#include "facelook_credential.h"
#include "facelook_provider.h"
#include <strsafe.h>
#include <NTSecAPI.h>

FacelookCredential::FacelookCredential() : _cRef(1) {}

STDMETHODIMP FacelookCredential::QueryInterface(REFIID riid, void** ppv)
{
    if (riid == IID_IUnknown || riid == IID_ICredentialProviderCredential || riid == IID_ICredentialProviderCredential2)
        *ppv = static_cast<ICredentialProviderCredential2*>(this);
    else { *ppv = nullptr; return E_NOINTERFACE; }
    AddRef();
    return S_OK;
}
STDMETHODIMP_(ULONG) FacelookCredential::AddRef() { return InterlockedIncrement(&_cRef); }
STDMETHODIMP_(ULONG) FacelookCredential::Release()
{
    LONG cRef = InterlockedDecrement(&_cRef);
    if (cRef == 0) delete this;
    return cRef;
}

STDMETHODIMP FacelookCredential::Advise(ICredentialProviderCredentialEvents*) { return S_OK; }
STDMETHODIMP FacelookCredential::UnAdvise() { return S_OK; }

STDMETHODIMP FacelookCredential::SetSelected(BOOL* pbAutoLogon)
{
    *pbAutoLogon = FALSE;
    _authenticated = PerformAuth();
    return S_OK;
}
STDMETHODIMP FacelookCredential::SetDeselected() { return S_OK; }

STDMETHODIMP FacelookCredential::GetFieldState(DWORD, CREDENTIAL_PROVIDER_FIELD_STATE* pcpfs, CREDENTIAL_PROVIDER_FIELD_INTERACTIVE_STATE* pcpfis)
{
    *pcpfs = CPFS_DISPLAY_IN_SELECTED_TILE;
    *pcpfis = CPFIS_NONE;
    return S_OK;
}

STDMETHODIMP FacelookCredential::GetStringValue(DWORD, PWSTR* ppwz)
{
    return SHStrDupW(L"Face Recognition", ppwz);
}

STDMETHODIMP FacelookCredential::GetBitmapValue(DWORD, HBITMAP*) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::GetCheckboxValue(DWORD, BOOL*, PWSTR*) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::GetComboBoxValueCount(DWORD, DWORD*, DWORD*) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::GetComboBoxValueAt(DWORD, DWORD, PWSTR*) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::GetSubmitButtonValue(DWORD, DWORD*) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::SetStringValue(DWORD, LPCWSTR) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::SetCheckboxValue(DWORD, BOOL) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::SetComboBoxSelectedValue(DWORD, DWORD) { return E_NOTIMPL; }
STDMETHODIMP FacelookCredential::CommandLinkClicked(DWORD) { return E_NOTIMPL; }

STDMETHODIMP FacelookCredential::GetSerialization(CREDENTIAL_PROVIDER_GET_SERIALIZATION_RESPONSE* pcpgsr,
    CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs,
    PWSTR*, CREDENTIAL_PROVIDER_STATUS_ICON*)
{
    if (!_authenticated)
    {
        *pcpgsr = CPGSR_NO_CREDENTIAL_NOT_FINISHED;
        return S_OK;
    }

    size_t userLen = _username.length();
    size_t passLen = _password.length();
    size_t userByte = (userLen + 1) * sizeof(WCHAR);
    size_t passByte = (passLen + 1) * sizeof(WCHAR);
    size_t totalSize = sizeof(KERB_INTERACTIVE_LOGON) + userByte + passByte;

    BYTE* pBuffer = (BYTE*)CoTaskMemAlloc(totalSize);
    if (!pBuffer) return E_OUTOFMEMORY;

    KERB_INTERACTIVE_LOGON* pkil = (KERB_INTERACTIVE_LOGON*)pBuffer;
    ZeroMemory(pkil, sizeof(KERB_INTERACTIVE_LOGON));
    pkil->MessageType = KerbInteractiveLogon;
    pkil->LogonDomainName.Length = 0;
    pkil->LogonDomainName.MaximumLength = 0;
    pkil->LogonDomainName.Buffer = NULL;

    PWSTR pUser = (PWSTR)(pBuffer + sizeof(KERB_INTERACTIVE_LOGON));
    pkil->UserName.Length = (USHORT)(userLen * sizeof(WCHAR));
    pkil->UserName.MaximumLength = (USHORT)userByte;
    pkil->UserName.Buffer = pUser;
    memcpy(pUser, _username.c_str(), userByte);

    PWSTR pPass = (PWSTR)(pBuffer + sizeof(KERB_INTERACTIVE_LOGON) + userByte);
    pkil->Password.Length = (USHORT)(passLen * sizeof(WCHAR));
    pkil->Password.MaximumLength = (USHORT)passByte;
    pkil->Password.Buffer = pPass;
    memcpy(pPass, _password.c_str(), passByte);

    pcpcs->ulAuthenticationPackage = 0;
    pcpcs->clsidCredentialProvider = CLSID_FacelookProvider;
    pcpcs->cbSerialization = (ULONG)totalSize;
    pcpcs->rgbSerialization = pBuffer;
    *pcpgsr = CPGSR_RETURN_CREDENTIAL_FINISHED;
    return S_OK;
}

STDMETHODIMP FacelookCredential::ReportResult(NTSTATUS, NTSTATUS, PWSTR*, CREDENTIAL_PROVIDER_STATUS_ICON*)
{
    return S_OK;
}

bool FacelookCredential::PerformAuth()
{
    // Try opening the pipe for up to 5 seconds
    HANDLE hPipe = nullptr;
    for (int i = 0; i < 5; ++i)
    {
        hPipe = CreateFileW(L"\\\\.\\pipe\\FacelookBiometric", GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
        if (hPipe != INVALID_HANDLE_VALUE)
            break;
        Sleep(1000);  // wait 1 second before retry
    }
    if (hPipe == INVALID_HANDLE_VALUE)
        return false;

    const char cmd[] = "AUTH";
    DWORD written;
    WriteFile(hPipe, cmd, (DWORD)strlen(cmd), &written, NULL);

    char buffer[256];
    DWORD read;
    if (!ReadFile(hPipe, buffer, sizeof(buffer) - 1, &read, NULL))
    {
        CloseHandle(hPipe);
        return false;
    }
    buffer[read] = '\0';
    CloseHandle(hPipe);

    std::string response(buffer, read);
    if (response.compare(0, 5, "FAIL") == 0) return false;

    size_t colon = response.find(':');
    if (colon == std::string::npos) return false;

    std::string user = response.substr(0, colon);
    std::string pass = response.substr(colon + 1);
    _username.assign(user.begin(), user.end());
    _password.assign(pass.begin(), pass.end());
    return true;
}