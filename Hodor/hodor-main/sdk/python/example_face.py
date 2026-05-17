"""
Face-recognition unlock example.

Captures frames from the default webcam, compares detected faces
against a known reference image, and unlocks when a match is found.

Requirements:
    pip install opencv-python face-recognition

Usage:
    python example_face.py <reference_image> <username> <password> [domain]
"""

import sys
import cv2
import face_recognition
from credential_provider import CredentialProviderClient


def face_unlock(
    known_face_path: str,
    username: str,
    password: str,
    domain: str = ".",
    tolerance: float = 0.5,
) -> None:
    client = CredentialProviderClient()

    # Load and encode the reference face
    print(f"Loading reference face from {known_face_path}...")
    known_image = face_recognition.load_image_file(known_face_path)
    known_encodings = face_recognition.face_encodings(known_image)
    if not known_encodings:
        print("ERROR: No face found in the reference image.")
        sys.exit(1)
    known_encoding = known_encodings[0]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open webcam.")
        sys.exit(1)

    print("Watching for face... Press Ctrl+C to stop.")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            # Downscale for speed
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb)
            encodings = face_recognition.face_encodings(rgb, locations)

            for encoding in encodings:
                matches = face_recognition.compare_faces(
                    [known_encoding], encoding, tolerance=tolerance
                )
                if matches[0]:
                    distance = face_recognition.face_distance(
                        [known_encoding], encoding
                    )[0]
                    print(f"Face matched (distance={distance:.3f}). Unlocking...")
                    result = client.unlock_with_retry(username, password, domain)
                    print(f"Result: {result.response}")
                    return
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cap.release()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            "Usage: python example_face.py <reference_image> "
            "<username> <password> [domain]"
        )
        sys.exit(1)
    face_unlock(
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        sys.argv[4] if len(sys.argv) > 4 else ".",
    )
