# Unlock Credential Provider -- Python SDK

## Quick Start

```python
from credential_provider import CredentialProviderClient

client = CredentialProviderClient()
result = client.unlock("myuser", "mypassword")
# result.success == True, result.response == "OK"
```

Source: [`sdk/python/credential_provider.py`](../sdk/python/credential_provider.py)

## Prerequisites

- Windows 11 (or 10) with `UnlockProvider.dll` registered
- Python 3.8+
- No third-party packages required (uses `ctypes`)

Optional for examples:
- `pip install SpeechRecognition pyaudio` -- voice activation
- `pip install opencv-python face-recognition` -- face recognition

## Pipe Protocol

| Item | Value |
|---|---|
| Pipe path | `\\.\pipe\CredentialProviderPipe` |
| Direction | Duplex (client writes command, reads response) |
| Encoding | UTF-8 |
| Command | `UNLOCK:<domain>\<username>:<password>` |
| Domain | `.` for local accounts, NetBIOS name for domain accounts |

### Responses

| Response | Meaning |
|---|---|
| `OK` | Credentials accepted; unlock/logon will be attempted by Windows |
| `ERR:INVALID_CMD` | Command could not be parsed |
| `ERR:NO_PROVIDER` | Provider is not in an active scenario |
| `ERR:PROVIDER_FAILED` | Internal provider error |

`OK` means the credentials were handed to Windows for validation.
The actual logon may still fail (wrong password, locked account, etc.) --
that outcome is shown on the lock screen, not returned on the pipe.

## API Reference

### `CredentialProviderClient`

```python
client = CredentialProviderClient(pipe_name=r"\\.\pipe\CredentialProviderPipe")
```

#### `client.unlock(username, password, domain=".") -> UnlockResult`

Connect to the pipe, send `UNLOCK`, read the response, disconnect.
Raises `CredentialProviderError` if the pipe is unreachable.

#### `client.unlock_with_retry(username, password, domain=".", max_retries=10, retry_delay=0.5) -> UnlockResult`

Same as `unlock()` but retries on connection failure.
Use this after `LockWorkStation()` -- the credential provider needs
a few seconds to load before the pipe is available.

### `UnlockResult`

```python
@dataclass
class UnlockResult:
    success: bool   # True when response == "OK"
    response: str   # Raw response string
```

### `CredentialProviderError`

Raised on pipe I/O failures (pipe not found, broken connection, etc.).

## Examples

### Lock and Unlock

```python
import ctypes, time
from credential_provider import CredentialProviderClient

client = CredentialProviderClient()

ctypes.windll.user32.LockWorkStation()
time.sleep(5)

result = client.unlock_with_retry("myuser", "mypassword")
print(result)  # UnlockResult(success=True, response='OK')
```

### Voice Activation

Source: [`sdk/python/example_voice.py`](../sdk/python/example_voice.py)

```bash
pip install SpeechRecognition pyaudio
python sdk/python/example_voice.py myuser mypassword
```

Listens on the microphone. When it hears a phrase containing "unlock",
it sends the UNLOCK command.

```python
import speech_recognition as sr
from credential_provider import CredentialProviderClient

client = CredentialProviderClient()
recognizer = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    recognizer.adjust_for_ambient_noise(source)
    audio = recognizer.listen(source)

text = recognizer.recognize_google(audio).lower()
if "unlock" in text:
    result = client.unlock_with_retry("myuser", "mypassword")
    print(result.response)
```

### Face Recognition

Source: [`sdk/python/example_face.py`](../sdk/python/example_face.py)

```bash
pip install opencv-python face-recognition
python sdk/python/example_face.py photo.jpg myuser mypassword
```

Captures webcam frames, compares against a reference photo,
and unlocks when a match is found.

```python
import cv2, face_recognition
from credential_provider import CredentialProviderClient

client = CredentialProviderClient()
known_image = face_recognition.load_image_file("photo.jpg")
known_encoding = face_recognition.face_encodings(known_image)[0]

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        continue
    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    for enc in face_recognition.face_encodings(rgb):
        if face_recognition.compare_faces([known_encoding], enc, tolerance=0.5)[0]:
            client.unlock_with_retry("myuser", "mypassword")
            cap.release()
            break
```

## Security Notes

- Never hardcode credentials. Use Windows Credential Manager, environment
  variables, or a secrets vault.
- The pipe is local-only. Remote connections are blocked by the DACL.
- Credentials travel in plaintext over the local pipe. This is standard
  for local IPC (an attacker with local admin can already read process
  memory) but must not be extended to network transports.
- Call `del password` or overwrite the variable after use.
