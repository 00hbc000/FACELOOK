{*******************************************************************************
  Unlock Credential Provider SDK for Delphi / Free Pascal.

  Communicates with UnlockProvider.dll via named pipe to unlock
  the Windows lock screen or approve credential prompts.

  No third-party dependencies. Works with Delphi 7+ and Free Pascal.

  Usage:
    var
      Client: TCredentialPipeClient;
      Res: TUnlockResult;
    begin
      Client := TCredentialPipeClient.Create;
      try
        Res := Client.Unlock('myuser', 'mypassword');
        if Res.Success then
          ShowMessage('Unlocked!');
      finally
        Client.Free;
      end;
    end;
*******************************************************************************}

unit CredentialPipe;

interface

uses
  Windows, SysUtils;

const
  CREDENTIAL_PIPE_NAME = '\\.\pipe\CredentialProviderPipe';
  CREDENTIAL_PIPE_BUFSIZE = 512;

type
  ECredentialPipeError = class(Exception);

  TUnlockResult = record
    Success: Boolean;
    Response: string;
  end;

  TCredentialPipeClient = class
  private
    FPipeName: string;
    FTimeoutMs: DWORD;
    function InternalConnect: THandle;
  public
    constructor Create; overload;
    constructor Create(const APipeName: string); overload;
    destructor Destroy; override;

    /// <summary>
    /// Send an UNLOCK command to the credential provider.
    /// </summary>
    /// <param name="AUsername">Windows username</param>
    /// <param name="APassword">Account password</param>
    /// <param name="ADomain">NetBIOS domain or "." for local</param>
    /// <returns>TUnlockResult with Success flag and raw Response</returns>
    /// <exception cref="ECredentialPipeError">On pipe I/O failure</exception>
    function Unlock(const AUsername, APassword: string;
      const ADomain: string = '.'): TUnlockResult;

    /// <summary>
    /// Send an UNLOCK command with automatic retries.
    /// Useful after LockWorkStation when the provider may still be loading.
    /// </summary>
    function UnlockWithRetry(const AUsername, APassword: string;
      const ADomain: string = '.';
      AMaxRetries: Integer = 10;
      ARetryDelayMs: Integer = 500): TUnlockResult;

    property PipeName: string read FPipeName write FPipeName;
    property TimeoutMs: DWORD read FTimeoutMs write FTimeoutMs;
  end;

implementation

{ TCredentialPipeClient }

constructor TCredentialPipeClient.Create;
begin
  Create(CREDENTIAL_PIPE_NAME);
end;

constructor TCredentialPipeClient.Create(const APipeName: string);
begin
  inherited Create;
  FPipeName := APipeName;
  FTimeoutMs := 5000;
end;

destructor TCredentialPipeClient.Destroy;
begin
  inherited;
end;

function TCredentialPipeClient.InternalConnect: THandle;
begin
  Result := CreateFileW(
    PWideChar(WideString(FPipeName)),
    GENERIC_READ or GENERIC_WRITE,
    0,
    nil,
    OPEN_EXISTING,
    0,
    0);
  if Result = INVALID_HANDLE_VALUE then
    raise ECredentialPipeError.CreateFmt(
      'Cannot connect to pipe "%s". Win32 error %d',
      [FPipeName, GetLastError]);
end;

function TCredentialPipeClient.Unlock(const AUsername, APassword: string;
  const ADomain: string): TUnlockResult;
var
  hPipe: THandle;
  Command: UTF8String;
  Buffer: array[0..CREDENTIAL_PIPE_BUFSIZE - 1] of AnsiChar;
  BytesWritten, BytesRead: DWORD;
  dwMode: DWORD;
begin
  Result.Success := False;
  Result.Response := '';

  hPipe := InternalConnect;
  try
    // Switch to message-read mode
    dwMode := PIPE_READMODE_MESSAGE;
    if not SetNamedPipeHandleState(hPipe, dwMode, nil, nil) then
      raise ECredentialPipeError.CreateFmt(
        'SetNamedPipeHandleState failed. Win32 error %d', [GetLastError]);

    // Build and send the UNLOCK command (UTF-8)
    Command := UTF8Encode(Format('UNLOCK:%s\%s:%s',
      [ADomain, AUsername, APassword]));

    if not WriteFile(hPipe, PAnsiChar(Command)^, Length(Command),
      BytesWritten, nil) then
      raise ECredentialPipeError.CreateFmt(
        'WriteFile failed. Win32 error %d', [GetLastError]);

    // Read response
    FillChar(Buffer, SizeOf(Buffer), 0);
    if not ReadFile(hPipe, Buffer, SizeOf(Buffer) - 1, BytesRead, nil) then
      raise ECredentialPipeError.CreateFmt(
        'ReadFile failed. Win32 error %d', [GetLastError]);

    Buffer[BytesRead] := #0;
    Result.Response := string(UTF8Decode(Buffer));
    Result.Success := (Result.Response = 'OK');
  finally
    CloseHandle(hPipe);
    // Securely wipe the command buffer (it contains the password)
    FillChar(Pointer(Command)^, Length(Command), 0);
  end;
end;

function TCredentialPipeClient.UnlockWithRetry(const AUsername, APassword: string;
  const ADomain: string; AMaxRetries, ARetryDelayMs: Integer): TUnlockResult;
var
  I: Integer;
  LastError: string;
begin
  Result.Success := False;
  Result.Response := '';
  LastError := '';
  for I := 0 to AMaxRetries - 1 do
  begin
    try
      Result := Unlock(AUsername, APassword, ADomain);
      Exit; // Connected and got a response (OK or ERR)
    except
      on E: ECredentialPipeError do
      begin
        LastError := E.Message;
        if I < AMaxRetries - 1 then
          Sleep(ARetryDelayMs)
        else
          raise; // Last attempt -- propagate
      end;
    end;
  end;
end;

end.
