/**
 * Unlock Credential Provider SDK for Node.js -- TypeScript declarations.
 */

export interface UnlockResult {
  success: boolean;
  response: string;
}

export interface ClientOptions {
  pipeName?: string;
  timeoutMs?: number;
}

export interface RetryOptions {
  maxRetries?: number;
  delayMs?: number;
}

export class CredentialProviderError extends Error {
  code: string;
  constructor(message: string, code?: string);
}

export class CredentialProviderClient {
  constructor(options?: ClientOptions);
  unlock(
    username: string,
    password: string,
    domain?: string
  ): Promise<UnlockResult>;
  unlockWithRetry(
    username: string,
    password: string,
    domain?: string,
    retryOptions?: RetryOptions
  ): Promise<UnlockResult>;
}
