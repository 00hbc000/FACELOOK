import os, time, ctypes

LOCK_DELAY = 10            # seconds without a face before lock
GRACE_PERIOD = 15          # first 15 seconds after login/startup: no lock
TIMESTAMP_FILE = r"C:\FACELOOK\Logs\last_face.txt"

script_start = time.time()
print("Auto‑lock watcher started. Grace period active...")

while True:
    current_time = time.time()
    # Read latest timestamp
    last_face_time = current_time
    try:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    last_face_time = float(content)
    except:
        pass

    age = current_time - last_face_time
    if (current_time - script_start) > GRACE_PERIOD and age > LOCK_DELAY:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd != 0:   # not locked
            print("No face detected for 10 seconds – locking workstation.")
            ctypes.windll.user32.LockWorkStation()
            time.sleep(5)
            # Reset timer after lock
            try:
                with open(TIMESTAMP_FILE, "r") as f:
                    val = f.read().strip()
                    if val:
                        last_face_time = float(val)
            except:
                last_face_time = time.time()
    time.sleep(1)