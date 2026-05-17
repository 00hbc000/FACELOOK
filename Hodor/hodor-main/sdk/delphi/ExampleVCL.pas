{*******************************************************************************
  VCL form example: unlock button + status label.

  Drop a TEdit (edtUsername), TEdit (edtPassword), TEdit (edtDomain),
  TButton (btnUnlock), and TLabel (lblStatus) on a form,
  then wire btnUnlockClick to the button's OnClick event.
*******************************************************************************}

unit ExampleVCL;

interface

uses
  Windows, SysUtils, Classes, Controls, Forms, StdCtrls, CredentialPipe;

type
  TMainForm = class(TForm)
    edtUsername: TEdit;
    edtPassword: TEdit;
    edtDomain: TEdit;
    btnUnlock: TButton;
    lblStatus: TLabel;
    procedure btnUnlockClick(Sender: TObject);
  end;

var
  MainForm: TMainForm;

implementation

{$R *.dfm}

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
        lblStatus.Caption := 'Unlock command sent successfully.'
      else
        lblStatus.Caption := 'Provider returned: ' + Res.Response;
    except
      on E: ECredentialPipeError do
        lblStatus.Caption := 'Connection error: ' + E.Message;
    end;
  finally
    Client.Free;
  end;
end;

end.
