import sys, cv2, face_recognition
from db_manager import init_db, add_user

if len(sys.argv) != 3:
    print("Usage: python enrollment.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

init_db()
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not found!")
    sys.exit(1)

print("Press SPACE to capture your face.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame – retrying...")
        continue
    cv2.imshow("Enrollment", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord(' '):
        break

cv2.destroyAllWindows()

# Convert BGR to RGB and ensure uint8
if frame is None or frame.size == 0:
    print("Invalid frame!")
    cap.release()
    sys.exit(1)

rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
# force a copy to make sure it's contiguous
rgb = rgb.copy(order='C')
rgb = rgb.astype('uint8')

print("Detecting face...")
boxes = face_recognition.face_locations(rgb, model="hog")
if not boxes:
    print("No face detected! Try again with better lighting.")
    cap.release()
    sys.exit(1)

encodings = face_recognition.face_encodings(rgb, boxes)
if not encodings:
    print("Encoding failed!")
    cap.release()
    sys.exit(1)

guid = add_user(username, password, encodings[0])
print(f"User enrolled successfully. GUID: {guid}")
cap.release()