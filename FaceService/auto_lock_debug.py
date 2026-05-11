import os, time, ctypes

LOCK_DELAY = 10
GRACE_PERIOD = 15
TIMESTAMP_FILE = r"C:\FACELOOK\Logs\last_face.txt"

script_start = time.time()
print("=== DEBUG AUTO‑LOCK STARTED ===")
print(f"Grace period: {GRACE_PERIOD}s, Lock delay: {LOCK_DELAY}s")
print("Sit in front of the camera and watch the messages.\n")

while True:
    current_time = time.time()
    # read timestamp
    last_face_time = current_time
    try:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    last_face_time = float(content)
    except Exception as e:
        print(f"[ERROR] reading file: {e}")

    age = current_time - last_face_time
    grace_remaining = GRACE_PERIOD - (current_time - script_start)
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    locked = (hwnd == 0)

    # print status every second
    print(f"[{time.strftime('%H:%M:%S')}] age={age:.1f}s, file_time={last_face_time:.0f}, locked={locked}, hwnd={hwnd}")

    if grace_remaining > 0:
        print(f"  (grace period active, won't lock for {grace_remaining:.0f}s)")

    if grace_remaining <= 0 and age > LOCK_DELAY and not locked:
        print(">>> LOCKING NOW <<<")
        ctypes.windll.user32.LockWorkStation()
        time.sleep(5)
        try:
            if os.path.exists(TIMESTAMP_FILE):
                with open(TIMESTAMP_FILE, "r") as f:
                    val = f.read().strip()
                    if val:
                        last_face_time = float(val)
        except:
            last_face_time = time.time()

    time.sleep(1)