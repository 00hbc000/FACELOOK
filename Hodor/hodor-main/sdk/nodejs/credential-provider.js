/**
 * Unlock Credential Provider SDK for Node.js.
 *
 * Communicates with UnlockProvider.dll via named pipe to unlock
 * the Windows lock screen or approve credential prompts.
 *
 * No third-party dependencies -- uses the built-in `net` module.
 *
 * @example
 * const { CredentialProviderClient } = require('./credential-provider');
 * const client = new CredentialProviderClient();
 * const result = await client.unlock('myuser', 'mypassword');
 * console.log(result); // { success: true, response: 'OK' }
 */

"use strict";

const net = require("net");

const PIPE_NAME = "\\\\.\\pipe\\CredentialProviderPipe";
const DEFAULT_TIMEOUT_MS = 5000;

/**
 * @typedef {Object} UnlockResult
 * @property {boolean} success - true when the provider accepted the command
 * @property {string}  response - raw response string ("OK" or "ERR:...")
 */

class CredentialProviderError extends Error {
  /**
   * @param {string} message
   * @param {string} [code]
   */
  constructor(message, code) {
    super(message);
    this.name = "CredentialProviderError";
    this.code = code || "UNKNOWN";
  }
}

class CredentialProviderClient {
  /**
   * @param {Object} [options]
   * @param {string} [options.pipeName] - Override the default pipe path.
   * @param {number} [options.timeoutMs] - I/O timeout in milliseconds.
   */
  constructor(options = {}) {
    this._pipeName = options.pipeName || PIPE_NAME;
    this._timeoutMs = options.timeoutMs || DEFAULT_TIMEOUT_MS;
  }

  /**
   * Send an UNLOCK command to the credential provider.
   *
   * @param {string} username - Windows username.
   * @param {string} password - Account password.
   * @param {string} [domain='.'] - NetBIOS domain or "." for local.
   * @returns {Promise<UnlockResult>}
   */
  unlock(username, password, domain = ".") {
    return new Promise((resolve, reject) => {
      const command = `UNLOCK:${domain}\\${username}:${password}`;
      let response = "";

      const client = net.connect(this._pipeName, () => {
        client.write(command, "utf-8");
      });

      client.on("data", (data) => {
        response += data.toString("utf-8");
      });

      client.on("end", () => {
        resolve({ success: response === "OK", response });
      });

      client.on("error", (err) => {
        reject(
          new CredentialProviderError(
            `Pipe connection failed: ${err.message}`,
            err.code
          )
        );
      });

      client.setTimeout(this._timeoutMs, () => {
        client.destroy();
        reject(
          new CredentialProviderError("Connection timed out", "TIMEOUT")
        );
      });
    });
  }

  /**
   * Send an UNLOCK command with retries.
   *
   * Useful right after LockWorkStation() when the credential provider
   * may still be loading.
   *
   * @param {string} username
   * @param {string} password
   * @param {string} [domain='.']
   * @param {Object} [retryOptions]
   * @param {number} [retryOptions.maxRetries=10]
   * @param {number} [retryOptions.delayMs=500]
   * @returns {Promise<UnlockResult>}
   */
  async unlockWithRetry(
    username,
    password,
    domain = ".",
    { maxRetries = 10, delayMs = 500 } = {}
  ) {
    let lastError;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await this.unlock(username, password, domain);
      } catch (err) {
        lastError = err;
        if (attempt < maxRetries - 1) {
          await new Promise((r) => setTimeout(r, delayMs));
        }
      }
    }
    throw lastError;
  }
}

module.exports = { CredentialProviderClient, CredentialProviderError };
