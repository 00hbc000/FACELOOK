# Windows Credential Provider -- Pipe-Controlled Unlock

A Windows 11 credential provider DLL that accepts unlock commands over a named pipe.
Any application that can write to a pipe can unlock the lock screen or approve a credential prompt -- no Windows Hello enrollment, no built-in biometric hardware required.

## How It Works

```
Your App  ──UNLOCK:.\user:pass──>  \\.\pipe\CredentialProviderPipe  ──>  UnlockProvider.dll  ──>  Windows LSA  ──>  Unlock
```

The DLL runs inside LogonUI.exe on the lock screen. When your app sends a command, the DLL packages the credentials and hands them to Windows for validation. If valid, the workstation unlocks.

## Build

Requires VS2022 with C++ desktop workload.

```batch
build.bat
```

Produces `UnlockProvider.dll` and `test_unlock.exe`.

## Install

```batch
register.bat        &:: Run as Administrator
```

## Test

```batch
test_unlock.exe myuser mypassword
test_unlock.exe myuser mypassword MYDOMAIN
```

Locks the screen, waits 5 seconds, sends the unlock command.

## Uninstall

```batch
unregister.bat      &:: Run as Administrator
```

## Usage Scenarios

### Face Recognition

A camera service runs in the background. When the lock screen appears, it captures a frame, runs face detection, and if the face matches the enrolled user, sends the unlock command. The user walks up to the PC and it unlocks.

```
Camera  ->  Face Detection Model  ->  Match?  ->  UNLOCK:.\user:pass  ->  Pipe  ->  Unlocked
```

Works with any face recognition stack: OpenCV + dlib, MediaPipe, Azure Face API, AWS Rekognition, a custom ONNX model -- anything that can produce a match/no-match result.

### Voice Activation

A microphone listener runs in the user session. It performs speech-to-text (locally with Vosk/Whisper or via a cloud API). When a trigger phrase is recognized ("unlock my computer", a custom passphrase, or a voice biometric match), it sends the unlock command.

```
Microphone  ->  Speech-to-Text  ->  Trigger Phrase?  ->  UNLOCK:.\user:pass  ->  Pipe  ->  Unlocked
```

Can also be combined with speaker verification: only unlock when the right voice says the right phrase.

### Fingerprint / Biometric Hardware

A USB fingerprint reader, palm scanner, or iris camera has its own SDK that fires an event when a known print/pattern is matched. The event handler sends the unlock command.

```
Fingerprint Reader SDK  ->  Match Event  ->  UNLOCK:.\user:pass  ->  Pipe  ->  Unlocked
```

This lets you use biometric hardware that Windows Hello does not natively support.

### Proximity / Bluetooth

A companion app on the user's phone advertises a BLE beacon. A background service on the PC monitors RSSI. When the phone is within range and the screen is locked, it unlocks. When the phone leaves range, it locks.

```
Phone BLE Beacon  ->  PC BLE Scanner  ->  In Range?  ->  UNLOCK:.\user:pass  ->  Pipe  ->  Unlocked
Phone out of range  ->  LockWorkStation()
```

### Smart Card / NFC

An NFC reader detects a known badge or smart card. The reader's SDK fires a card-read event containing a card UID. The handler maps the UID to stored credentials and sends the unlock command.

```
NFC Reader  ->  Card UID  ->  Lookup Credentials  ->  UNLOCK:.\user:pass  ->  Pipe  ->  Unlocked
```

### Kiosk / Shared Terminal

A kiosk application manages user sessions. When a customer authenticates through the kiosk UI (PIN, QR code scan, membership card), the kiosk app unlocks the workstation to their profile and locks it again when the session ends.

```
Kiosk UI  ->  Customer Authenticated  ->  UNLOCK:.\kiosk_user:pass  ->  Pipe  ->  Unlocked
Session End  ->  LockWorkStation()
```

### Remote Administration

A management tool on the network needs to unlock a workstation for remote maintenance. An agent running on the target machine receives the command over a secure channel and relays it to the local pipe.

```
Admin Console  ->  TLS/SSH to Agent  ->  Agent  ->  UNLOCK:.\admin:pass  ->  Pipe  ->  Unlocked
```

### Multi-Factor Combination

Combine any of the above. A service requires both face match AND voice passphrase before sending the unlock command.

```
Face Match = true  AND  Voice Match = true  ->  UNLOCK:.\user:pass  ->  Pipe  ->  Unlocked
```

## Pipe Protocol

| Item | Value |
|---|---|
| Pipe path | `\\.\pipe\CredentialProviderPipe` |
| Command | `UNLOCK:domain\username:password` |
| Domain | `.` for local, NetBIOS name for domain |
| Response | `OK` or `ERR:INVALID_CMD` / `ERR:NO_PROVIDER` / `ERR:PROVIDER_FAILED` |

`OK` = credentials handed to Windows. Logon result (success/wrong password/locked account) appears on the lock screen.

## SDKs

| Language | Source | Docs |
|---|---|---|
| Python | [`sdk/python/credential_provider.py`](sdk/python/credential_provider.py) | [`docs/SDK_Python.md`](docs/SDK_Python.md) |
| Node.js | [`sdk/nodejs/credential-provider.js`](sdk/nodejs/credential-provider.js) | [`docs/SDK_NodeJS.md`](docs/SDK_NodeJS.md) |
| Delphi | [`sdk/delphi/CredentialPipe.pas`](sdk/delphi/CredentialPipe.pas) | [`docs/SDK_Delphi.md`](docs/SDK_Delphi.md) |

All SDKs have zero third-party dependencies. Any language that can open a named pipe works -- the protocol is 1 write + 1 read of a UTF-8 string.

## Debugging

Run [Sysinternals DebugView](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview) as Administrator with "Capture Global Win32" enabled. The DLL logs every step with `[UnlockProvider]`, `[Credential]`, and `[PipeListener]` prefixes.

## Security

- Pipe DACL: SYSTEM and Administrators get full access, Authenticated Users get read/write, Anonymous and Network are denied.
- Remote pipe connections are blocked (`PIPE_REJECT_REMOTE_CLIENTS`).
- Pipe squatting is prevented (`FILE_FLAG_FIRST_PIPE_INSTANCE`).
- Passwords are wiped with `SecureZeroMemory` after use.
- DLL installs to `C:\Windows\System32` (admin-writable only).
