/**
 * Shared validation logic for agent automation operations.
 *
 * This module provides validation that runs in BOTH dry-run and live modes,
 * ensuring consistent input checking regardless of execution path.
 *
 * IMPORTANT: These validators check request validity, NOT runtime behavior.
 * They cannot enforce read-only browser interactions or prevent the agent
 * from performing consequential actions once the SDK executes the goal.
 */

/**
 * Validate a URL for agent operations
 * @param {string} url - URL to validate
 * @returns {{valid: boolean, error?: string, normalized?: string}}
 */
export function validateAgentUrl(url) {
  if (!url || typeof url !== 'string' || url.trim().length === 0) {
    return { valid: false, error: 'URL must be a non-empty string' };
  }

  const trimmed = url.trim();

  // Parse URL
  let parsed;
  try {
    parsed = new URL(trimmed);
  } catch (e) {
    return { valid: false, error: `Invalid URL format: ${e.message}` };
  }

  // Enforce HTTP/HTTPS only
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return {
      valid: false,
      error: `URL must use HTTP or HTTPS protocol, got: ${parsed.protocol}`
    };
  }

  return { valid: true, normalized: parsed.href };
}

/**
 * Validate goal/task description for agent operations
 * @param {string} goal - Goal description
 * @param {number} maxLength - Maximum allowed length (default: 5000)
 * @returns {{valid: boolean, error?: string, trimmed?: string}}
 */
export function validateAgentGoal(goal, maxLength = 5000) {
  if (!goal || typeof goal !== 'string' || goal.trim().length === 0) {
    return { valid: false, error: 'Goal must be a non-empty string' };
  }

  const trimmed = goal.trim();

  if (trimmed.length > maxLength) {
    return {
      valid: false,
      error: `Goal exceeds maximum length of ${maxLength} characters (got ${trimmed.length})`
    };
  }

  return { valid: true, trimmed };
}

/**
 * Validate browser profile setting
 * @param {string} profile - Browser profile name
 * @returns {{valid: boolean, error?: string, normalized?: string}}
 */
export function validateBrowserProfile(profile) {
  const validProfiles = ['lite', 'stealth'];

  if (!profile || typeof profile !== 'string') {
    return { valid: false, error: 'Browser profile must be a string' };
  }

  const normalized = profile.toLowerCase().trim();

  if (!validProfiles.includes(normalized)) {
    return {
      valid: false,
      error: `Browser profile must be one of: ${validProfiles.join(', ')} (got: ${profile})`
    };
  }

  return { valid: true, normalized };
}

/**
 * Validate max_steps parameter
 * @param {number} maxSteps - Maximum steps
 * @returns {{valid: boolean, error?: string, clamped?: number}}
 */
export function validateMaxSteps(maxSteps) {
  if (typeof maxSteps !== 'number' || isNaN(maxSteps)) {
    return { valid: false, error: 'max_steps must be a number' };
  }

  if (maxSteps < 1) {
    return { valid: false, error: 'max_steps must be at least 1' };
  }

  if (maxSteps > 100) {
    return { valid: false, error: 'max_steps cannot exceed 100' };
  }

  return { valid: true, clamped: Math.floor(maxSteps) };
}

/**
 * Validate max_duration_seconds parameter
 * @param {number} maxDuration - Maximum duration in seconds
 * @returns {{valid: boolean, error?: string, clamped?: number}}
 */
export function validateMaxDuration(maxDuration) {
  if (typeof maxDuration !== 'number' || isNaN(maxDuration)) {
    return { valid: false, error: 'max_duration_seconds must be a number' };
  }

  if (maxDuration < 10) {
    return { valid: false, error: 'max_duration_seconds must be at least 10' };
  }

  if (maxDuration > 600) {
    return { valid: false, error: 'max_duration_seconds cannot exceed 600' };
  }

  return { valid: true, clamped: Math.floor(maxDuration) };
}

/**
 * Check if goal contains clearly prohibited actions.
 *
 * LIMITATION: This is basic pattern matching for request validation only.
 * It CANNOT prevent the agent from performing these actions if the SDK
 * receives the goal. The TinyFish SDK does not enforce interaction-level
 * restrictions. This check rejects obviously unsafe requests at the wrapper
 * level but does not guarantee read-only execution.
 *
 * @param {string} goal - Goal to check
 * @returns {{prohibited: boolean, reason?: string}}
 */
export function checkProhibitedActions(goal) {
  const trimmed = goal.trim().toLowerCase();

  const patterns = [
    { regex: /submit.*form/i, reason: 'form submission' },
    { regex: /fill.*form/i, reason: 'form filling' },
    { regex: /purchase/i, reason: 'purchases' },
    { regex: /buy/i, reason: 'purchases' },
    { regex: /checkout/i, reason: 'checkout/payment' },
    { regex: /payment/i, reason: 'payment processing' },
    { regex: /login/i, reason: 'authentication' },
    { regex: /sign\s*in/i, reason: 'authentication' },
    { regex: /authenticate/i, reason: 'authentication' },
    { regex: /create.*account/i, reason: 'account creation' },
    { regex: /register/i, reason: 'account registration' },
    { regex: /delete/i, reason: 'data deletion' },
    { regex: /remove/i, reason: 'data removal' },
    { regex: /upload/i, reason: 'file upload' },
    { regex: /send.*message/i, reason: 'message sending' },
    { regex: /post.*comment/i, reason: 'comment posting' }
  ];

  for (const { regex, reason } of patterns) {
    if (regex.test(trimmed)) {
      return {
        prohibited: true,
        reason: `Goal appears to request ${reason}, which is not supported in Phase 3`
      };
    }
  }

  return { prohibited: false };
}

/**
 * Validate all agent parameters and return normalized values or errors.
 * This is the main validation entry point used by both dry-run and live paths.
 *
 * @param {Object} params - Agent parameters
 * @param {string} params.url - Target URL
 * @param {string} params.goal - Task description
 * @param {number} [params.maxSteps] - Max steps
 * @param {number} [params.maxDurationSeconds] - Max duration
 * @param {string} [params.browserProfile] - Browser profile
 * @returns {{valid: boolean, errors: string[], normalized?: Object}}
 */
export function validateAgentParams(params) {
  const errors = [];
  const normalized = {};

  // Validate URL
  const urlResult = validateAgentUrl(params.url);
  if (!urlResult.valid) {
    errors.push(urlResult.error);
  } else {
    normalized.url = urlResult.normalized;
  }

  // Validate goal
  const goalResult = validateAgentGoal(params.goal);
  if (!goalResult.valid) {
    errors.push(goalResult.error);
  } else {
    normalized.goal = goalResult.trimmed;

    // Check for prohibited actions (only if goal is valid)
    const prohibitedCheck = checkProhibitedActions(normalized.goal);
    if (prohibitedCheck.prohibited) {
      errors.push(
        `Phase 3 restriction: ${prohibitedCheck.reason}. ` +
        `This phase supports browsing, navigation, and information extraction only.`
      );
    }
  }

  // Validate browser profile (optional, has default)
  if (params.browserProfile !== undefined) {
    const profileResult = validateBrowserProfile(params.browserProfile);
    if (!profileResult.valid) {
      errors.push(profileResult.error);
    } else {
      normalized.browserProfile = profileResult.normalized;
    }
  } else {
    normalized.browserProfile = 'lite';
  }

  // Validate max_steps (optional, has default)
  if (params.maxSteps !== undefined) {
    const stepsResult = validateMaxSteps(params.maxSteps);
    if (!stepsResult.valid) {
      errors.push(stepsResult.error);
    } else {
      normalized.maxSteps = stepsResult.clamped;
    }
  } else {
    normalized.maxSteps = 50;
  }

  // Validate max_duration_seconds (optional, has default)
  if (params.maxDurationSeconds !== undefined) {
    const durationResult = validateMaxDuration(params.maxDurationSeconds);
    if (!durationResult.valid) {
      errors.push(durationResult.error);
    } else {
      normalized.maxDurationSeconds = durationResult.clamped;
    }
  } else {
    normalized.maxDurationSeconds = 300;
  }

  return {
    valid: errors.length === 0,
    errors,
    normalized: errors.length === 0 ? normalized : undefined
  };
}
