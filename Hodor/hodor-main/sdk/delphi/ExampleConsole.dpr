{*******************************************************************************
  Console example: lock the workstation, wait, then unlock via pipe.

  Usage:
    ExampleConsole.exe <username> <password> [domain]
*******************************************************************************}

program ExampleConsole;

{$APPTYPE CONSOLE}

uses
  Windows, SysUtils, CredentialPipe;

var
  Client: TCredentialPipeClient;
  Res: TUnlockResult;
  Domain: string;
begin
  if ParamCount < 2 then
  begin
    WriteLn('Usage: ExampleConsole.exe <username> <password> [domain]');
    WriteLn;
    WriteLn('Examples:');
    WriteLn('  ExampleConsole.exe MyUser MyPassword');
    WriteLn('  ExampleConsole.exe MyUser MyPassword MYDOMAIN');
    ExitCode := 1;
    Exit;
  end;

  if ParamCount >= 3 then
    Domain := ParamStr(3)
  else
    Domain := '.';

  Client := TCredentialPipeClient.Create;
  try
    WriteLn('[INFO] Locking workstation in 2 seconds...');
    Sleep(2000);

    if not LockWorkStation then
    begin
      WriteLn('[ERROR] LockWorkStation failed. Error: ', GetLastError);
      ExitCode := 1;
      Exit;
    end;
    WriteLn('[INFO] Workstation locked.');
    WriteLn('[INFO] Waiting 5 seconds for lock screen...');
    Sleep(5000);

    WriteLn('[INFO] Sending unlock command...');
    try
      Res := Client.UnlockWithRetry(ParamStr(1), ParamStr(2), Domain);
      if Res.Success then
        WriteLn('[OK] Unlock command accepted.')
      else
        WriteLn('[FAIL] Provider returned: ', Res.Response);
    except
      on E: ECredentialPipeError do
        WriteLn('[ERROR] ', E.Message);
    end;
  finally
    Client.Free;
  end;
end.
