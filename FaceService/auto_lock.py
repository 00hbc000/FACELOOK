import os, time, ctypes

LOCK_DELAY = 10
TIMESTAMP_FILE = r"C:\FACELOOK\Logs\last_face.txt"

print("Debug Auto‑Lock started. Press Ctrl+C to stop.")
last_face_time = time.time()

while True:
    current_time = time.time()
    # Read latest timestamp
    try:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    last_face_time = float(content)
                    print(f"[DEBUG] Update from file: last_face_time = {last_face_time:.0f} (age: {current_time - last_face_time:.1f}s)")
    except Exception as e:
        print(f"[ERROR] reading file: {e}")

    age = current_time - last_face_time
    if age > LOCK_DELAY:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        locked = (hwnd == 0)
        print(f"[DEBUG] Age > {LOCK_DELAY}s. Locked? {locked}. hwnd={hwnd}")
        if not locked:
            print(">>> Locking workstation now <<<")
            ctypes.windll.user32.LockWorkStation()
            time.sleep(5)
            # after lock, reset timer to avoid immediate re‑lock
            try:
                with open(TIMESTAMP_FILE, "r") as f:
                    val = f.read().strip()
                    if val:
                        last_face_time = float(val)
                        print(f"[DEBUG] After lock, timestamp reset to {last_face_time:.0f}")
            except:
                last_face_time = time.time()
    time.sleep(1)