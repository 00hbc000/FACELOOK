# Unlock Credential Provider -- Delphi SDK

## Quick Start

```pascal
uses CredentialPipe;

var
  Client: TCredentialPipeClient;
  Res: TUnlockResult;
begin
  Client := TCredentialPipeClient.Create;
  try
    Res := Client.Unlock('myuser', 'mypassword');
    // Res.Success = True, Res.Response = 'OK'
  finally
    Client.Free;
  end;
end;
```

Source: [`sdk/delphi/CredentialPipe.pas`](../sdk/delphi/CredentialPipe.pas)

## Prerequisites

- Windows 11 (or 10) with `UnlockProvider.dll` registered
- Delphi 7+ or Free Pascal / Lazarus
- No third-party packages required (uses `Windows` and `SysUtils` only)

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

### `TCredentialPipeClient`

```pascal
constructor Create;                          // uses default pipe name
constructor Create(const APipeName: string); // custom pipe name
```

| Property | Type | Default | Description |
|---|---|---|---|
| `PipeName` | `string` | `\\.\pipe\CredentialProviderPipe` | Pipe path |
| `TimeoutMs` | `DWORD` | `5000` | Reserved for future use |

#### `function Unlock(AUsername, APassword: string; ADomain: string = '.'): TUnlockResult`

Connect, send `UNLOCK`, read response, disconnect.
Raises `ECredentialPipeError` on pipe I/O failure.

#### `function UnlockWithRetry(AUsername, APassword: string; ADomain: string = '.'; AMaxRetries: Integer = 10; ARetryDelayMs: Integer = 500): TUnlockResult`

Same as `Unlock` but retries on connection failure.
Use this after `LockWorkStation` -- the credential provider needs
a few seconds to load before the pipe is available.

### `TUnlockResult`

```pascal
TUnlockResult = record
  Success: Boolean;  // True when Response = 'OK'
  Response: string;  // Raw response string
end;
```

### `ECredentialPipeError`

Raised on pipe connection or I/O failures. Message includes the
Win32 error code.

## Examples

### Console: Lock and Unlock

Source: [`sdk/delphi/ExampleConsole.dpr`](../sdk/delphi/ExampleConsole.dpr)

```pascal
program ExampleConsole;
{$APPTYPE CONSOLE}
uses
  Windows, SysUtils, CredentialPipe;
var
  Client: TCredentialPipeClient;
  Res: TUnlockResult;
begin
  Client := TCredentialPipeClient.Create;
  try
    LockWorkStation;
    Sleep(5000);
    Res := Client.UnlockWithRetry(ParamStr(1), ParamStr(2));
    if Res.Success then
      WriteLn('Unlocked!')
    else
      WriteLn('Failed: ', Res.Response);
  finally
    Client.Free;
  end;
end.
```

### VCL Form

Source: [`sdk/delphi/ExampleVCL.pas`](../sdk/delphi/ExampleVCL.pas)

```pascal
procedure TMainForm.btnUnlockClick(Sender: TObject);
var
  Client: TCredentialPipeClient;
  Res: TUnlockResult;
begin
  Client := TCredentialPipeClient.Create;
  try
    try
      Res := Client.Unlock(edtUsername.Text, edtPassword.Text, edtDomain.Text);
      if Res.Success then
        lblStatus.Caption := 'Unlock command sent.'
      else
        lblStatus.Caption := 'Provider returned: ' + Res.Response;
    except
      on E: ECredentialPipeError do
        lblStatus.Caption := 'Error: ' + E.Message;
    end;
  finally
    Client.Free;
  end;
end;
```

### Voice Activation (Windows SAPI)

```pascal
uses
  ComObj, ActiveX, CredentialPipe;

procedure VoiceUnlock(const AUsername, APassword, ADomain: string);
var
  SpVoice: OleVariant;
  RecoContext: OleVariant;
  Grammar: OleVariant;
  Client: TCredentialPipeClient;
begin
  CoInitialize(nil);
  try
    // Create a shared recognition context (uses the default audio input)
    RecoContext := CreateOleObject('SAPI.SpSharedRecoContext');

    // Build a command grammar with the trigger phrase
    Grammar := RecoContext.CreateGrammar(0);
    Grammar.DictationSetState(0); // disable free dictation
    Grammar.CmdSetRuleState('unlock',
      1 {SGDSActive} );

    // In production, hook the Recognition event via IConnectionPoint
    // and call Unlock when the "unlock computer" rule fires:
    //
    //   Client := TCredentialPipeClient.Create;
    //   Res := Client.UnlockWithRetry(AUsername, APassword, ADomain);
    //   Client.Free;

    WriteLn('Say "unlock computer" to unlock the workstation.');
    WriteLn('(Full SAPI event wiring omitted for brevity.)');
  finally
    CoUninitialize;
  end;
end;
```

### Face Recognition (OpenCV via DLL)

```pascal
uses
  Windows, CredentialPipe;

// Import the core OpenCV functions you need (or use a Delphi OpenCV binding).
// Pseudocode flow:

procedure FaceUnlock(const ARefImage, AUsername, APassword, ADomain: string);
var
  Client: TCredentialPipeClient;
  StopEvent: THandle;
begin
  Client := TCredentialPipeClient.Create;
  StopEvent := CreateEvent(nil, True, False, nil);
  try
    // 1. Load reference image and compute face encoding
    //    refEncoding := ComputeEncoding(LoadImage(ARefImage));

    // 2. Open webcam
    //    cap := cvCaptureFromCAM(0);

    // 3. Loop until match or stop
    //    while WaitForSingleObject(StopEvent, 100) = WAIT_TIMEOUT do
    //    begin
    //      frame := cvQueryFrame(cap);
    //      faces := DetectFaces(frame);
    //      for each face do
    //        if CompareEncodings(face, refEncoding) < 0.5 then
    //        begin
    //          Client.UnlockWithRetry(AUsername, APassword, ADomain);
    //          Exit;
    //        end;
    //    end;

    WriteLn('Face unlock requires an OpenCV binding for Delphi.');
    WriteLn('See github.com/Laex/Delphi-OpenCV');
  finally
    CloseHandle(StopEvent);
    Client.Free;
  end;
end;
```

### Exporting as a DLL for Other Languages

```pascal
library UnlockSDK;
uses Windows, SysUtils, CredentialPipe;

function UnlockWorkstation(
  AUsername, APassword, ADomain: PAnsiChar): Integer; stdcall;
var
  Client: TCredentialPipeClient;
  Res: TUnlockResult;
begin
  Result := -1; // connection error
  Client := TCredentialPipeClient.Create;
  try
    try
      Res := Client.Unlock(
        string(AnsiString(AUsername)),
        string(AnsiString(APassword)),
        string(AnsiString(ADomain)));
      if Res.Success then Result := 0 else Result := 1;
    except
      Result := -1;
    end;
  finally
    Client.Free;
  end;
end;

exports UnlockWorkstation;
begin
end.
```

Calling from C/C++:

```c
typedef int (__stdcall *PUnlockWorkstation)(const char*, const char*, const char*);
HMODULE hDll = LoadLibraryA("UnlockSDK.dll");
PUnlockWorkstation fn = (PUnlockWorkstation)GetProcAddress(hDll, "UnlockWorkstation");
int rc = fn("myuser", "mypassword", ".");  // 0 = OK, 1 = server error, -1 = no connection
```

## Security Notes

- Never hardcode credentials. Use `CredReadW` / `CredWriteW` (Windows
  Credential Manager) or a secure storage mechanism.
- The pipe is local-only. Remote connections are blocked by the DACL.
- Credentials travel in plaintext over the local pipe. This is standard
  for local IPC but must not be extended to network transports.
- Use `FillChar` or `SecureZeroMemory` to wipe password buffers after use.
  The SDK does this internally for the pipe command buffer.
- In Windows service applications, ensure the service account is a member
  of Authenticated Users (the default) to access the pipe.
