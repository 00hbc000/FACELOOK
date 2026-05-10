import os, time, ctypes

LOCK_DELAY = 10          # seconds
TIMESTAMP_FILE = r"C:\FACELOOK\Logs\last_face.txt"

print("Auto‑lock watcher started. Watching for face activity...")

while True:
    current_time = time.time()
    last_face_time = current_time      # fallback if file is missing/empty

    try:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    last_face_time = float(content)
    except:
        pass

    # Only lock if enough time has passed AND the workstation is not already locked
    if current_time - last_face_time > LOCK_DELAY:
        # Is the workstation locked? GetForegroundWindow returns NULL on secure desktop
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd != 0:   # unlocked
            print("No face detected for 10 seconds – locking workstation.")
            ctypes.windll.user32.LockWorkStation()
            time.sleep(5)            # prevent immediate re‑lock after unlock
            # Reset fallback so we don't lock again immediately after coming back
            try:
                with open(TIMESTAMP_FILE, "r") as f:
                    val = f.read().strip()
                    if val:
                        last_face_time = float(val)
            except:
                last_face_time = time.time()
        else:
            pass   # already locked, do nothing

    time.sleep(1)