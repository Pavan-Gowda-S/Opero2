/**
 * TinyFish search operations
 * Wraps client.search.query() with validation and error handling
 */

import { getClient } from './client.js';
import { validateQuery } from './validation.js';
import {
  SDKError,
  AuthenticationError,
  RateLimitError,
  NotFoundError
} from '@tiny-fish/sdk';

/**
 * Perform web search using TinyFish
 * @param {Object} options - Search options
 * @param {string} options.query - Search query
 * @param {number} [options.maxResults=10] - Maximum results to return
 * @param {string} [options.location] - Country code for geo-targeting (e.g., "US")
 * @param {string} [options.language] - Language code (e.g., "en")
 * @returns {Promise<Object>} Search results
 */
export async function search(options) {
  const { query, maxResults = 10, location, language } = options;

  // Validate query
  const validation = validateQuery(query);
  if (!validation.valid) {
    throw new Error(validation.error);
  }

  try {
    const client = getClient();

    const params = {
      query: validation.sanitized,
    };

    if (location && typeof location === 'string') {
      params.location = location.trim().toUpperCase();
    }

    if (language && typeof language === 'string') {
      params.language = language.trim().toLowerCase();
    }

    const response = await client.search.query(params);

    // Return sanitized response (remove any sensitive data)
    return {
      success: true,
      query: response.query,
      total_results: response.total_results,
      results: response.results.slice(0, maxResults).map(result => ({
        title: result.title || '',
        snippet: result.snippet || '',
        url: result.url || '',
        // Do not include any internal metadata
      })),
    };

  } catch (error) {
    return handleSearchError(error);
  }
}

/**
 * Handle search errors with appropriate messages
 * @param {Error} error - Error object
 * @returns {Object} Error response
 */
function handleSearchError(error) {
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

  if (error instanceof NotFoundError) {
    return {
      success: false,
      error: 'Resource not found',
      code: 'NOT_FOUND',
      message: error.message,
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
