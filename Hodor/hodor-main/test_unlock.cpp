//
// test_unlock.exe - Test application for the Unlock Credential Provider
//
// Usage: test_unlock.exe <username> <password> [domain]
//
// This program:
// 1. Locks the workstation
// 2. Waits 3 seconds for the lock screen to load
// 3. Connects to the credential provider's named pipe
// 4. Sends an UNLOCK command to auto-unlock the screen
//

#include <windows.h>
#include <stdio.h>

#define PIPE_NAME "\\\\.\\pipe\\CredentialProviderPipe"

static BOOL SendUnlockCommand(const char* pszDomain, const char* pszUsername, const char* pszPassword)
{
    // Build command string
    char szCommand[512];
    if (pszDomain && pszDomain[0]) {
        _snprintf_s(szCommand, sizeof(szCommand), _TRUNCATE,
            "UNLOCK:%s\\%s:%s", pszDomain, pszUsername, pszPassword);
    } else {
        _snprintf_s(szCommand, sizeof(szCommand), _TRUNCATE,
            "UNLOCK:%s:%s", pszUsername, pszPassword);
    }

    // Try connecting with retries (the pipe may not be ready immediately)
    HANDLE hPipe = INVALID_HANDLE_VALUE;
    for (int attempt = 0; attempt < 10; attempt++) {
        hPipe = CreateFileA(
            PIPE_NAME,
            GENERIC_READ | GENERIC_WRITE,
            0,
            NULL,
            OPEN_EXISTING,
            0,
            NULL);

        if (hPipe != INVALID_HANDLE_VALUE) break;

        DWORD dwErr = GetLastError();
        if (dwErr == ERROR_PIPE_BUSY) {
            if (!WaitNamedPipeA(PIPE_NAME, 2000)) {
                printf("[RETRY] Pipe busy, waiting... (attempt %d)\n", attempt + 1);
                continue;
            }
        } else {
            printf("[RETRY] Pipe not available (error %lu), retrying in 500ms... (attempt %d)\n",
                dwErr, attempt + 1);
            Sleep(500);
        }
    }

    if (hPipe == INVALID_HANDLE_VALUE) {
        printf("[ERROR] Failed to connect to pipe after retries. Error: %lu\n", GetLastError());
        return FALSE;
    }

    // Set pipe to message mode
    DWORD dwMode = PIPE_READMODE_MESSAGE;
    SetNamedPipeHandleState(hPipe, &dwMode, NULL, NULL);

    // Send the command
    DWORD cbWritten = 0;
    BOOL bSuccess = WriteFile(hPipe, szCommand, (DWORD)strlen(szCommand), &cbWritten, NULL);
    if (!bSuccess) {
        printf("[ERROR] WriteFile failed. Error: %lu\n", GetLastError());
        CloseHandle(hPipe);
        return FALSE;
    }
    printf("[INFO] Sent: %s\n", "UNLOCK:<credentials>");  // Don't log actual credentials

    // Read response
    char szResponse[512] = {};
    DWORD cbRead = 0;
    bSuccess = ReadFile(hPipe, szResponse, sizeof(szResponse) - 1, &cbRead, NULL);
    if (bSuccess && cbRead > 0) {
        szResponse[cbRead] = '\0';
        printf("[INFO] Response: %s\n", szResponse);
    } else {
        printf("[WARN] No response from pipe. Error: %lu\n", GetLastError());
    }

    // Securely clear the command buffer (contains password)
    SecureZeroMemory(szCommand, sizeof(szCommand));
    CloseHandle(hPipe);

    return (cbRead > 0 && strcmp(szResponse, "OK") == 0);
}

int main(int argc, char* argv[])
{
    printf("=== Unlock Credential Provider Test ===\n\n");

    if (argc < 3) {
        printf("Usage: test_unlock.exe <username> <password> [domain]\n\n");
        printf("Examples:\n");
        printf("  test_unlock.exe MyUser MyPassword\n");
        printf("  test_unlock.exe MyUser MyPassword MYDOMAIN\n");
        printf("  test_unlock.exe MyUser MyPassword .\n");
        printf("\nThis will lock the screen, wait 3 seconds, then unlock.\n");
        return 1;
    }

    const char* pszUsername = argv[1];
    const char* pszPassword = argv[2];
    const char* pszDomain = (argc >= 4) ? argv[3] : ".";

    printf("[INFO] Username: %s\n", pszUsername);
    printf("[INFO] Domain:   %s\n", pszDomain);
    printf("[INFO] Locking workstation in 2 seconds...\n");
    Sleep(2000);

    // Lock the workstation
    if (!LockWorkStation()) {
        printf("[ERROR] LockWorkStation failed. Error: %lu\n", GetLastError());
        printf("[INFO] You may need to run this from an interactive session.\n");
        return 1;
    }
    printf("[INFO] Workstation locked.\n");

    // Wait for the lock screen to fully load and credential providers to initialize.
    // Windows 11 can take several seconds to load the lock screen and instantiate providers.
    printf("[INFO] Waiting 5 seconds for lock screen to initialize...\n");
    Sleep(5000);

    // Send unlock command
    printf("[INFO] Sending unlock command...\n");
    if (SendUnlockCommand(pszDomain, pszUsername, pszPassword)) {
        printf("[OK] Unlock command sent successfully.\n");
    } else {
        printf("[FAIL] Unlock command failed.\n");
        return 1;
    }

    return 0;
}
