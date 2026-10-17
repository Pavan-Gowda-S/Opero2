/**
 * TinyFish SDK client wrapper
 * Loads API key from environment and provides singleton instance
 */

import { TinyFish } from '@tiny-fish/sdk';

let clientInstance = null;

/**
 * Get or create TinyFish client instance
 * @returns {TinyFish} Configured TinyFish client
 * @throws {Error} If TINYFISH_API_KEY is not set
 */
export function getClient() {
  if (clientInstance) {
    return clientInstance;
  }

  const apiKey = process.env.TINYFISH_API_KEY;

  if (!apiKey || apiKey.trim() === '') {
    throw new Error('TINYFISH_API_KEY environment variable is not set or empty');
  }

  clientInstance = new TinyFish({
    apiKey: apiKey,
    timeout: 60_000,  // 60 second timeout for operations
    maxRetries: 2,
  });

  return clientInstance;
}

/**
 * Reset client instance (useful for testing)
 */
export function resetClient() {
  clientInstance = null;
}
