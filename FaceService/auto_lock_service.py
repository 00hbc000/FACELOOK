import os, time, ctypes
import win32serviceutil, win32service, win32event, servicemanager

TIMESTAMP_FILE = r"C:\FACELOOK\Logs\last_face.txt"
LOCK_DELAY = 10
LOG_FILE = r"C:\FACELOOK\Logs\auto_lock.log"

def write_log(msg):
    try:
        with open(LOG_FILE, "a") as logf:
            logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except:
        pass

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
        write_log("Service started.")
        self.main()

    def main(self):
        # Initialise last_face_time from the file, or use current time
        last_face_time = time.time()
        try:
            if os.path.exists(TIMESTAMP_FILE):
                with open(TIMESTAMP_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        last_face_time = float(content)
        except Exception as e:
            write_log(f"Error reading initial timestamp: {e}")

        write_log(f"Initial last_face_time = {last_face_time:.0f}")

        while self.running:
            if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                write_log("Stop event received.")
                break

            current_time = time.time()
            # Re‑read the timestamp file
            try:
                if os.path.exists(TIMESTAMP_FILE):
                    with open(TIMESTAMP_FILE, "r") as f:
                        content = f.read().strip()
                        if content:
                            last_face_time = float(content)
            except Exception as e:
                write_log(f"Error reading timestamp: {e}")

            age = current_time - last_face_time
            if age > LOCK_DELAY:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                locked = (hwnd == 0)
                write_log(f"Age={age:.1f}s, Locked={locked}")
                if not locked:
                    write_log("Locking workstation now.")
                    ctypes.windll.user32.LockWorkStation()
                    time.sleep(5)
                    # Reset timer after lock
                    try:
                        if os.path.exists(TIMESTAMP_FILE):
                            with open(TIMESTAMP_FILE, "r") as f:
                                val = f.read().strip()
                                if val:
                                    last_face_time = float(val)
                    except:
                        last_face_time = time.time()
                # else: already locked, do nothing
            # else: not yet expired

        write_log("Service stopped.")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AutoLockService)