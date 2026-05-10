#include "facelook_provider.h"
#include "facelook_credential.h"
#include <new>

FacelookProvider::FacelookProvider() : _cRef(1) {}
STDMETHODIMP FacelookProvider::QueryInterface(REFIID riid, void** ppv) {
    if (riid == IID_IUnknown || riid == IID_ICredentialProvider)
        *ppv = static_cast<ICredentialProvider*>(this);
    else { *ppv = nullptr; return E_NOINTERFACE; }
    AddRef(); return S_OK;
}
STDMETHODIMP_(ULONG) FacelookProvider::AddRef() { return InterlockedIncrement(&_cRef); }
STDMETHODIMP_(ULONG) FacelookProvider::Release() {
    LONG cRef = InterlockedDecrement(&_cRef);
    if (cRef == 0) delete this;
    return cRef;
}
STDMETHODIMP FacelookProvider::SetUsageScenario(CREDENTIAL_PROVIDER_USAGE_SCENARIO cpus, DWORD) { _cpus = cpus; return S_OK; }
STDMETHODIMP FacelookProvider::SetSerialization(const CREDENTIAL_PROVIDER_CREDENTIAL_SERIALIZATION*) { return S_OK; }
STDMETHODIMP FacelookProvider::Advise(ICredentialProviderEvents*, UINT_PTR) { return S_OK; }
STDMETHODIMP FacelookProvider::UnAdvise() { return S_OK; }
STDMETHODIMP FacelookProvider::GetFieldDescriptorCount(DWORD* pdwCount) { *pdwCount = 1; return S_OK; }
STDMETHODIMP FacelookProvider::GetFieldDescriptorAt(DWORD, CREDENTIAL_PROVIDER_FIELD_DESCRIPTOR** ppcpfd) { *ppcpfd = nullptr; return E_INVALIDARG; }
STDMETHODIMP FacelookProvider::GetCredentialCount(DWORD* pdwCount, DWORD* pdwDefault, BOOL* pbAutoLogonWithDefault) {
    *pdwCount = 1; *pdwDefault = 0; *pbAutoLogonWithDefault = FALSE; return S_OK;
}
STDMETHODIMP FacelookProvider::GetCredentialAt(DWORD dwIndex, ICredentialProviderCredential** ppcpc) {
    if (dwIndex != 0) return E_INVALIDARG;
    if (!_pCredential) {
        _pCredential = new(std::nothrow) FacelookCredential();
        if (!_pCredential) return E_OUTOFMEMORY;
    }
    return _pCredential->QueryInterface(IID_ICredentialProviderCredential, (void**)ppcpc);
}