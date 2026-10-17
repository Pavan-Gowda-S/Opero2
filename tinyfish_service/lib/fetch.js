/**
 * TinyFish content fetching operations
 * Wraps client.fetch.getContents() with validation and error handling
 */

import { getClient } from './client.js';
import { validateUrls, validateFormat } from './validation.js';
import { FetchFormat } from '@tiny-fish/sdk';
import {
  SDKError,
  AuthenticationError,
  RateLimitError
} from '@tiny-fish/sdk';

/**
 * Fetch content from URLs using TinyFish
 * @param {Object} options - Fetch options
 * @param {string[]} options.urls - Array of URLs to fetch (1-10)
 * @param {string} [options.format='markdown'] - Output format: markdown, html, json
 * @param {boolean} [options.links=false] - Include links from pages
 * @param {boolean} [options.imageLinks=false] - Include image links
 * @param {number} [options.timeout=45000] - Per-URL timeout in milliseconds
 * @returns {Promise<Object>} Fetch results
 */
export async function fetchContent(options) {
  const {
    urls,
    format = 'markdown',
    links = false,
    imageLinks = false,
    timeout = 45000
  } = options;

  // Validate URLs
  const urlValidation = validateUrls(urls);
  if (!urlValidation.valid) {
    throw new Error(urlValidation.error);
  }

  // Validate format
  const formatValidation = validateFormat(format);
  if (!formatValidation.valid) {
    throw new Error(formatValidation.error);
  }

  try {
    const client = getClient();

    // Map format string to SDK enum
    const formatMap = {
      'markdown': FetchFormat.Markdown,
      'html': FetchFormat.Html,
      'json': FetchFormat.Json,
    };

    const params = {
      urls: urlValidation.sanitized,
      format: formatMap[formatValidation.sanitized],
      links: Boolean(links),
      image_links: Boolean(imageLinks),
      per_url_timeout_ms: Math.min(Math.max(timeout, 1000), 110000),
    };

    const response = await client.fetch.getContents(params);

    // Return sanitized response
    return {
      success: true,
      results: response.results.map(result => ({
        url: result.url,
        title: result.title || null,
        text: result.text || null,
        links: result.links || [],
        image_links: result.image_links || [],
        status: result.error ? 'error' : 'success',
        error: result.error || null,
      })),
      errors: response.errors || [],
    };

  } catch (error) {
    return handleFetchError(error);
  }
}

/**
 * Handle fetch errors with appropriate messages
 * @param {Error} error - Error object
 * @returns {Object} Error response
 */
function handleFetchError(error) {
  if (error instanceof AuthenticationError) {
    return {
      success: false,
      error: 'Authentication failed',
      code: 'AUTH_ERROR',
      message: 'Invalid or missing API key',
    };
  }

  if (error instanceof RateLimitError) {
    return {
      success: false,
      error: 'Rate limit exceeded',
      code: 'RATE_LIMIT',
      message: 'Too many requests. Please try again later.',
    };
  }

  if (error instanceof SDKError) {
    return {
      success: false,
      error: 'API error',
      code: 'SDK_ERROR',
      message: error.message,
      status: error.status,
    };
  }

  // Unknown error
  return {
    success: false,
    error: 'Unknown error',
    code: 'UNKNOWN',
    message: error.message || String(error),
  };
}
