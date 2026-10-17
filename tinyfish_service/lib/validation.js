/**
 * Input validation utilities
 * Validates and sanitizes parameters before passing to TinyFish SDK
 */

/**
 * Validate search query
 * @param {string} query - Search query
 * @returns {{valid: boolean, error?: string, sanitized?: string}}
 */
export function validateQuery(query) {
  if (!query || typeof query !== 'string') {
    return { valid: false, error: 'Query must be a non-empty string' };
  }

  const trimmed = query.trim();

  if (trimmed.length === 0) {
    return { valid: false, error: 'Query cannot be empty' };
  }

  if (trimmed.length > 2000) {
    return { valid: false, error: 'Query exceeds maximum length of 2000 characters' };
  }

  return { valid: true, sanitized: trimmed };
}

/**
 * Validate URL
 * @param {string} url - URL to validate
 * @returns {{valid: boolean, error?: string}}
 */
export function validateUrl(url) {
  if (!url || typeof url !== 'string') {
    return { valid: false, error: 'URL must be a non-empty string' };
  }

  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return { valid: false, error: 'URL must use http or https protocol' };
    }
    return { valid: true };
  } catch (e) {
    return { valid: false, error: `Invalid URL: ${e.message}` };
  }
}

/**
 * Validate URLs array for fetch operation
 * @param {string[]} urls - Array of URLs
 * @returns {{valid: boolean, error?: string, sanitized?: string[]}}
 */
export function validateUrls(urls) {
  if (!Array.isArray(urls)) {
    return { valid: false, error: 'URLs must be an array' };
  }

  if (urls.length === 0) {
    return { valid: false, error: 'At least one URL is required' };
  }

  if (urls.length > 10) {
    return { valid: false, error: 'Maximum 10 URLs allowed per request' };
  }

  const sanitized = [];
  for (let i = 0; i < urls.length; i++) {
    const validation = validateUrl(urls[i]);
    if (!validation.valid) {
      return { valid: false, error: `URL ${i + 1}: ${validation.error}` };
    }
    sanitized.push(urls[i].trim());
  }

  return { valid: true, sanitized };
}

/**
 * Validate format parameter
 * @param {string} format - Format type
 * @returns {{valid: boolean, error?: string, sanitized?: string}}
 */
export function validateFormat(format) {
  const validFormats = ['markdown', 'html', 'json'];
  const lower = (format || 'markdown').toLowerCase();

  if (!validFormats.includes(lower)) {
    return {
      valid: false,
      error: `Format must be one of: ${validFormats.join(', ')}`
    };
  }

  return { valid: true, sanitized: lower };
}
