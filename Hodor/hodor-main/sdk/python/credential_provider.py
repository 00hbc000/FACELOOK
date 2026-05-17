"""
Unlock Credential Provider SDK for Python.

Communicates with the UnlockProvider.dll via named pipe to unlock
the Windows lock screen or approve credential prompts.

Requirements: Windows only. No third-party dependencies (uses ctypes).

Usage:
    from credential_provider import CredentialProviderClient

    client = CredentialProviderClient()
    result = client.unlock("myuser", "mypassword")
    print(result)  # UnlockResult(success=True, response='OK')
"""

import ctypes
import ctypes.wintypes as wt
import time
from dataclasses import dataclass
from typing import Optional

kernel32 = ctypes.windll.kernel32

# Win32 constants
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = wt.HANDLE(-1).value
PIPE_READMODE_MESSAGE = 0x00000002
ERROR_PIPE_BUSY = 231

PIPE_NAME = r"\\.\pipe\CredentialProviderPipe"


class CredentialProviderError(Exception):
    """Raised when the named pipe connection or I/O fails."""
    pass


@dataclass
class UnlockResult:
    """Result of an unlock command."""
    success: bool
    response: str


class CredentialProviderClient:
    """
    Client for the Unlock Credential Provider named pipe.

    Example:
        client = CredentialProviderClient()
        result = client.unlock("username", "password", domain=".")
        if result.success:
            print("Workstation unlocked")
    """

    def __init__(self, pipe_name: str = PIPE_NAME):
        self._pipe_name = pipe_name

    def unlock(
        self,
        username: str,
        password: str,
        domain: str = ".",
    ) -> UnlockResult:
        """
        Send an UNLOCK command to the credential provider.

        Args:
            username: Windows username.
            password: Password for the account.
            domain:   NetBIOS domain name, or "." for a local account.

        Returns:
            UnlockResult with success flag and raw response string.

        Raises:
            CredentialProviderError: If the pipe cannot be opened or I/O fails.
        """
        handle = self._connect()
        try:
            self._set_message_mode(handle)
            command = f"UNLOCK:{domain}\\{username}:{password}".encode("utf-8")
            self._write(handle, command)
            response = self._read(handle)
            return UnlockResult(
                success=(response == "OK"),
                response=response,
            )
        finally:
            kernel32.CloseHandle(handle)

    def unlock_with_retry(
        self,
        username: str,
        password: str,
        domain: str = ".",
        max_retries: int = 10,
        retry_delay: float = 0.5,
    ) -> UnlockResult:
        """
        Send an UNLOCK command with connection retries.

        Useful when calling right after LockWorkStation(), since the
        credential provider DLL may not have finished loading yet.

        Args:
            username:    Windows username.
            password:    Password for the account.
            domain:      NetBIOS domain name, or "." for a local account.
            max_retries: Maximum number of connection attempts.
            retry_delay: Seconds to wait between retries.

        Returns:
            UnlockResult with success flag and raw response string.

        Raises:
            CredentialProviderError: After all retries are exhausted.
        """
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                return self.unlock(username, password, domain)
            except CredentialProviderError as exc:
                last_error = exc
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        raise last_error  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _connect(self) -> int:
        handle = kernel32.CreateFileW(
            self._pipe_name,
            GENERIC_READ | GENERIC_WRITE,
            0,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        if handle == INVALID_HANDLE_VALUE:
            err = kernel32.GetLastError()
            if err == ERROR_PIPE_BUSY:
                raise CredentialProviderError(
                    "Pipe is busy (another client is connected)"
                )
            raise CredentialProviderError(
                f"Cannot connect to pipe. Win32 error {err}"
            )
        return handle

    @staticmethod
    def _set_message_mode(handle: int) -> None:
        mode = wt.DWORD(PIPE_READMODE_MESSAGE)
        ok = kernel32.SetNamedPipeHandleState(
            handle, ctypes.byref(mode), None, None
        )
        if not ok:
            raise CredentialProviderError(
                f"SetNamedPipeHandleState failed. Win32 error {kernel32.GetLastError()}"
            )

    @staticmethod
    def _write(handle: int, data: bytes) -> None:
        written = wt.DWORD()
        ok = kernel32.WriteFile(
            handle, data, len(data), ctypes.byref(written), None
        )
        if not ok:
            raise CredentialProviderError(
                f"WriteFile failed. Win32 error {kernel32.GetLastError()}"
            )

    @staticmethod
    def _read(handle: int, bufsize: int = 512) -> str:
        buf = ctypes.create_string_buffer(bufsize)
        read = wt.DWORD()
        ok = kernel32.ReadFile(handle, buf, bufsize, ctypes.byref(read), None)
        if not ok:
            raise CredentialProviderError(
                f"ReadFile failed. Win32 error {kernel32.GetLastError()}"
            )
        return buf.raw[: read.value].decode("utf-8")
