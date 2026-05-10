#pragma once
#include <windows.h>
#include <credentialprovider.h>
#include <string>
#include <shlwapi.h>            // for SHStrDupW

class FacelookCredential : public ICredentialProviderCredential2
{
public:
    FacelookCredential();

    // IUnknown
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    STDMETHODIMP_(ULONG) AddRef() override;
    STDMETHODIMP_(ULONG) Release() override;

    // ICredentialProviderCredential
    STDMETHODIMP Advise(ICredentialProviderCredentialEvents* pcpce) override;
    STDMETHODIMP UnAdvise() override;
    STDMETHODIMP SetSelected(BOOL* pbAutoLogon) override;
    STDMETHODIMP SetDeselected() override;
    STDMETHODIMP GetFieldState(DWORD dwFieldID, CREDENTIAL_PROVIDER_FIELD_STATE* pcpfs, CREDENTIAL_PROVIDER_FIELD_INTERACTIVE_STATE* pcpfis) override;
    STDMETHODIMP GetStringValue(DWORD dwFieldID, PWSTR* ppwz) override;
    STDMETHODIMP GetBitmapValue(DWORD dwFieldID, HBITMAP* phbmp) override;
    STDMETHODIMP GetCheckboxValue(DWORD dwFieldID, BOOL* pbChecked, PWSTR* ppwzLabel) override;
    STDMETHODIMP GetComboBoxValueCount(DWORD dwFieldID, DWORD* pcItems, DWORD* pdwSelectedItem) override;
    STDMETHODIMP GetComboBoxValueAt(DWORD dwFieldID, DWORD dwItem, PWSTR* ppwzItem) override;
    STDMETHODIMP GetSubmitButtonValue(DWORD dwFieldID, DWORD* pdwAdjacentTo) override;

    // Required Set methods (we don’t use them, return E_NOTIMPL)
    STDMETHODIMP SetStringValue(DWORD dwFieldID, LPCWSTR pwz) override;
    STDMETHODIMP SetCheckboxValue(DWORD dwFieldID, BOOL bChecked) override;
    STDMETHODIMP SetComboBoxSelectedValue(DWORD dwFieldID, DWORD dwSelectedItem) override;

    STDMETHODIMP CommandLinkClicked(DWORD dwFieldID) override;
    STDMETHODIMP GetSerialization(CREDENTIAL_PROVIDER_GET_SERIALIZATION_RESPONSE* pcpgsr,
        CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs,
        PWSTR* ppwzOptionalStatusText,
        CREDENTIAL_PROVIDER_STATUS_ICON* pcpsiOptionalStatusIcon) override;

    // Correct signature matching the SDK
    STDMETHODIMP ReportResult(NTSTATUS ntsStatus, NTSTATUS ntsSubstatus,
        PWSTR* ppwzOptionalStatusText,
        CREDENTIAL_PROVIDER_STATUS_ICON* pcpsiOptionalStatusIcon) override;

    // ICredentialProviderCredential2
    STDMETHODIMP GetUserSid(PWSTR* ppszSid) override { return E_NOTIMPL; }

private:
    LONG _cRef = 1;
    bool _authenticated = false;
    std::wstring _username;
    std::wstring _password;
    bool PerformAuth();
};