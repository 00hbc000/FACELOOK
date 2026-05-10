import os, time
import win32serviceutil, win32service, win32event, servicemanager
import win32pipe, win32file
import face_recognition, cv2
from db_manager import init_db, get_all_users, decrypt_password

HODOR_PIPE = r'\\.\pipe\CredentialProviderPipe'
LOG_FILE = r'C:\FACELOOK\Logs\attendance.csv'
LAST_FACE_FILE = r'C:\FACELOOK\Logs\last_face.txt'
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

class FaceService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FACELOOKService"
    _svc_display_name_ = "FACELOOK Face Recognition Service"
    _svc_description_ = "Detects faces, updates presence timestamp, and unlocks via Hodor"

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.cap = None
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False
        if self.cap:
            self.cap.release()

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        init_db()
        self.main()

    def main(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            servicemanager.LogErrorMsg("Camera not found!")
            return

        known_users = get_all_users()
        servicemanager.LogInfoMsg(f"Loaded {len(known_users)} users")
        last_refresh = time.time()

        while self.running:
            if win32event.WaitForSingleObject(self.hWaitStop, 200) == win32event.WAIT_OBJECT_0:
                break

            if time.time() - last_refresh > 30:
                known_users = get_all_users()
                last_refresh = time.time()

            ret, frame = self.cap.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb, model="hog")
            if not boxes:
                continue

            encodings = face_recognition.face_encodings(rgb, boxes)
            if not encodings:
                continue

            for enc in encodings:
                distances = face_recognition.face_distance([u["embedding"] for u in known_users], enc)
                best_idx = distances.argmin()
                if distances[best_idx] < 0.5:
                    user = known_users[best_idx]
                    password = decrypt_password(user["enc_pw"], user["salt"])

                    # ── 1. Always update the presence timestamp ──
                    try:
                        with open(LAST_FACE_FILE, "w") as tf:
                            tf.write(str(time.time()))
                    except:
                        pass

                    # ── 2. If the lock screen is up, send the unlock command ──
                    try:
                        pipe = win32file.CreateFile(
                            HODOR_PIPE,
                            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                            0, None,
                            win32file.OPEN_EXISTING, 0, None)
                        unlock_cmd = f"UNLOCK:.\{user['username']}:{password}"
                        win32file.WriteFile(pipe, unlock_cmd.encode('utf-8') + b'\x00')
                        win32file.CloseHandle(pipe)

                        # Attendance log only when an actual unlock happens
                        with open(LOG_FILE, "a") as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{user['guid']}\n")
                        servicemanager.LogInfoMsg(f"Unlock sent for {user['username']}")
                    except:
                        # Pipe not available – that's fine, we already updated the timestamp
                        pass

                    break   # one unlock per loop

        if self.cap:
            self.cap.release()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FaceService)