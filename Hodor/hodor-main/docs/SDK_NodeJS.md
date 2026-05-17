# Unlock Credential Provider -- Node.js SDK

## Quick Start

```javascript
const { CredentialProviderClient } = require("./credential-provider");

const client = new CredentialProviderClient();
const result = await client.unlock("myuser", "mypassword");
// { success: true, response: "OK" }
```

Source: [`sdk/nodejs/credential-provider.js`](../sdk/nodejs/credential-provider.js)
Types: [`sdk/nodejs/credential-provider.d.ts`](../sdk/nodejs/credential-provider.d.ts)

## Prerequisites

- Windows 11 (or 10) with `UnlockProvider.dll` registered
- Node.js 14+
- No third-party packages required (uses built-in `net` module)

Optional for examples:
- `npm install vosk mic` -- voice activation
- `npm install @vladmandic/face-api canvas` -- face recognition

## Pipe Protocol

| Item | Value |
|---|---|
| Pipe path | `\\.\pipe\CredentialProviderPipe` |
| Direction | Duplex (client writes command, reads response) |
| Encoding | UTF-8 |
| Command | `UNLOCK:<domain>\<username>:<password>` |
| Domain | `.` for local accounts, NetBIOS name for domain accounts |

### Responses

| Response | Meaning |
|---|---|
| `OK` | Credentials accepted; unlock/logon will be attempted by Windows |
| `ERR:INVALID_CMD` | Command could not be parsed |
| `ERR:NO_PROVIDER` | Provider is not in an active scenario |
| `ERR:PROVIDER_FAILED` | Internal provider error |

`OK` means the credentials were handed to Windows for validation.
The actual logon may still fail (wrong password, locked account, etc.) --
that outcome is shown on the lock screen, not returned on the pipe.

## API Reference

### `new CredentialProviderClient([options])`

| Option | Type | Default | Description |
|---|---|---|---|
| `pipeName` | `string` | `\\.\pipe\CredentialProviderPipe` | Pipe path |
| `timeoutMs` | `number` | `5000` | I/O timeout (ms) |

### `client.unlock(username, password[, domain]) -> Promise<UnlockResult>`

Connect, send `UNLOCK`, read response, disconnect.
Rejects with `CredentialProviderError` on connection or I/O failure.

### `client.unlockWithRetry(username, password[, domain[, retryOptions]]) -> Promise<UnlockResult>`

Same as `unlock()` but retries on connection failure.

| retryOptions | Type | Default |
|---|---|---|
| `maxRetries` | `number` | `10` |
| `delayMs` | `number` | `500` |

### `UnlockResult`

```typescript
interface UnlockResult {
  success: boolean; // true when response === "OK"
  response: string; // raw response string
}
```

### `CredentialProviderError`

Extends `Error`. Has a `code` property with the underlying error code.

## Examples

### Lock and Unlock

```javascript
const { execSync } = require("child_process");
const { CredentialProviderClient } = require("./credential-provider");

const client = new CredentialProviderClient();

// Lock (alternative: use ffi to call LockWorkStation)
execSync("rundll32.exe user32.dll,LockWorkStation");

// Wait for lock screen
await new Promise((r) => setTimeout(r, 5000));

const result = await client.unlockWithRetry("myuser", "mypassword");
console.log(result); // { success: true, response: 'OK' }
```

### Voice Activation (Vosk)

Source: [`sdk/nodejs/example-voice.js`](../sdk/nodejs/example-voice.js)

```bash
npm install vosk mic
# Download a model from https://alphacephei.com/vosk/models
node sdk/nodejs/example-voice.js myuser mypassword
```

Listens on the microphone using offline speech recognition.
When it hears "unlock" or "unlock computer", it sends the command.

```javascript
const vosk = require("vosk");
const mic = require("mic");
const { CredentialProviderClient } = require("./credential-provider");

const client = new CredentialProviderClient();
const model = new vosk.Model("./vosk-model-small-en-us");
const rec = new vosk.Recognizer({ model, sampleRate: 16000 });

const m = mic({ rate: "16000", channels: "1", encoding: "signed-integer", bitwidth: "16" });
m.getAudioStream().on("data", async (data) => {
  if (rec.acceptWaveform(data)) {
    const { text } = rec.result();
    if (text.includes("unlock")) {
      m.stop();
      await client.unlockWithRetry("myuser", "mypassword");
    }
  }
});
m.start();
```

### Face Recognition (face-api.js)

Source: [`sdk/nodejs/example-face.js`](../sdk/nodejs/example-face.js)

```bash
npm install @vladmandic/face-api canvas
node sdk/nodejs/example-face.js photo.jpg myuser mypassword
```

Loads a reference face image, then compares captured frames against it.
See the example file for the full implementation with notes on webcam
capture in Node.js.

### Electron Integration

```javascript
// main.js
const { ipcMain } = require("electron");
const { CredentialProviderClient } = require("./credential-provider");

const client = new CredentialProviderClient();

ipcMain.handle("unlock", async (_event, { username, password, domain }) => {
  return client.unlock(username, password, domain || ".");
});

// preload.js
const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("credentialProvider", {
  unlock: (args) => ipcRenderer.invoke("unlock", args),
});

// renderer.js
const result = await window.credentialProvider.unlock({
  username: "myuser",
  password: "mypassword",
});
```

## Security Notes

- Never hardcode credentials. Use environment variables, Windows Credential
  Manager (via `keytar`), or a secrets vault.
- The pipe is local-only. Remote connections are blocked by the DACL.
- Credentials travel in plaintext over the local pipe. This is standard
  for local IPC but must not be extended to network transports.
- In Electron, use `contextIsolation: true` and expose only the
  high-level `unlock` function via the preload bridge.
