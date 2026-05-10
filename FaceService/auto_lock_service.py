import os, time, ctypes
import win32serviceutil, win32service, win32event, servicemanager

TIMESTAMP_FILE = r"C:\FACELOOK\Logs\last_face.txt"
LOCK_DELAY = 10

class AutoLockService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FACELOOKAutoLock"
    _svc_display_name_ = "FACELOOK Auto‑Lock Service"
    _svc_description_ = "Locks the workstation when no face has been seen for 10 seconds"

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        # ----- Read the timestamp file first, else fall back to now -----
        last_face_time = time.time()
        try:
            if os.path.exists(TIMESTAMP_FILE):
                with open(TIMESTAMP_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        last_face_time = float(content)
        except:
            pass

        while self.running:
            if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                break

            current_time = time.time()
            # Re‑read the timestamp file every loop
            try:
                if os.path.exists(TIMESTAMP_FILE):
                    with open(TIMESTAMP_FILE, "r") as f:
                        content = f.read().strip()
                        if content:
                            last_face_time = float(content)
            except:
                pass

            age = current_time - last_face_time
            print(f"[DEBUG] age={age:.1f}s, last_face_time={last_face_time:.0f}, locked={ctypes.windll.user32.GetForegroundWindow()==0}")
            if age > LOCK_DELAY:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd != 0:   # unlocked
                    servicemanager.LogInfoMsg("No face detected – locking workstation")
                    ctypes.windll.user32.LockWorkStation()
                    time.sleep(5)
                    # After locking, reset timer from file to avoid immediate re‑lock
                    try:
                        if os.path.exists(TIMESTAMP_FILE):
                            with open(TIMESTAMP_FILE, "r") as f:
                                val = f.read().strip()
                                if val:
                                    last_face_time = float(val)
                    except:
                        last_face_time = time.time()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AutoLockService)