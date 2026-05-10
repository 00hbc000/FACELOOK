#include <windows.h>
#include <credentialprovider.h>
#include "facelook_provider.h"
#include <new>

STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppv) {
    if (rclsid == CLSID_FacelookProvider) {
        FacelookProvider* pProvider = new(std::nothrow) FacelookProvider();
        if (!pProvider) return E_OUTOFMEMORY;
        HRESULT hr = pProvider->QueryInterface(riid, ppv);
        pProvider->Release();
        return hr;
    }
    return CLASS_E_CLASSNOTAVAILABLE;
}
STDAPI DllCanUnloadNow() { return S_FALSE; }