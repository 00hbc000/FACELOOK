#pragma once
#include <windows.h>
#include <credentialprovider.h>

static const GUID CLSID_FacelookProvider = 
    { 0xFACE1000, 0x0001, 0x0001, { 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01 } };

class FacelookCredential;

class FacelookProvider : public ICredentialProvider {
public:
    FacelookProvider();
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    STDMETHODIMP_(ULONG) AddRef() override;
    STDMETHODIMP_(ULONG) Release() override;
    STDMETHODIMP SetUsageScenario(CREDENTIAL_PROVIDER_USAGE_SCENARIO cpus, DWORD dwFlags) override;
    STDMETHODIMP SetSerialization(const CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION* pcpcs) override;
    STDMETHODIMP Advise(ICredentialProviderEvents* pcpe, UINT_PTR upAdviseContext) override;
    STDMETHODIMP UnAdvise() override;
    STDMETHODIMP GetFieldDescriptorCount(DWORD* pdwCount) override;
    STDMETHODIMP GetFieldDescriptorAt(DWORD dwIndex, CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR** ppcpfd) override;
    STDMETHODIMP GetCredentialCount(DWORD* pdwCount, DWORD* pdwDefault, BOOL* pbAutoLogonWithDefault) override;
    STDMETHODIMP GetCredentialAt(DWORD dwIndex, ICredentialProviderCredential** ppcpc) override;

private:
    LONG _cRef = 1;
    CREDENTIAL_PROVIDER_USAGE_SCENARIO _cpus;
    FacelookCredential* _pCredential = nullptr;
};