/**
 * TinyFish agent automation operations
 * Wraps client.agent.run() with validation and error handling
 *
 * SECURITY NOTE: This wrapper validates requests before submission but CANNOT
 * enforce browser-level interaction restrictions. The TinyFish SDK does not
 * provide controls to prevent specific interactions (clicks, form fills, etc.)
 * once a goal is submitted. Pattern matching on goal text is not a reliable
 * enforcement mechanism.
 *
 * Phase 3 safety boundaries are enforced through:
 * 1. Request validation (this wrapper) - rejects obviously unsafe goals
 * 2. User education - clear documentation of permitted vs prohibited operations
 * 3. Future UI controls - will gate agent features behind explicit user consent
 *
 * The agent CAN perform consequential actions if the goal requests them in
 * ways that bypass basic pattern matching.
 */

import { getClient } from './client.js';
import { validateAgentParams } from './agent-validation.js';
import {
  RunStatus,
  SDKError,
  AuthenticationError,
  RateLimitError,
  BadRequestError,
  InternalServerError
} from '@tiny-fish/sdk';

/**
 * Run browser agent automation
 * @param {Object} options - Agent options
 * @param {string} options.url - Target URL to automate
 * @param {string} options.goal - Natural language description of the task
 * @param {number} [options.maxSteps] - Maximum steps the agent can take
 * @param {number} [options.maxDurationSeconds] - Maximum duration in seconds
 * @param {string} [options.browserProfile='lite'] - Browser profile: 'lite' or 'stealth'
 * @returns {Promise<Object>} Agent run result
 */
export async function runAgent(options) {
  // Use shared validation module
  const validation = validateAgentParams({
    url: options.url,
    goal: options.goal,
    maxSteps: options.maxSteps,
    maxDurationSeconds: options.maxDurationSeconds,
    browserProfile: options.browserProfile
  });

  if (!validation.valid) {
    // Return validation errors as a single error message
    throw new Error(validation.errors.join('; '));
  }

  const { url, goal, maxSteps, maxDurationSeconds, browserProfile } = validation.normalized;

  try {
    const client = getClient();

    // Build params - only include agent_config if values differ from defaults
    // The API may reject custom max_steps if the account is not in the beta program
    const params = {
      url: url,
      goal: goal,
      browser_profile: browserProfile,
    };

    // Only include agent_config if explicitly set and differs from defaults
    // Omitting agent_config allows API to use server-side defaults
    if (maxSteps !== 50 || maxDurationSeconds !== 300) {
      params.agent_config = {
        max_steps: maxSteps,
        max_duration_seconds: maxDurationSeconds,
      };
    }

    // agent.run() is a blocking HTTP request that waits for the agent to complete.
    //
    // TIMEOUT BEHAVIOR (verified from SDK source):
    // - The SDK's `timeout` option (60s in client.js) controls the HTTP request timeout
    // - This timeout applies to the ENTIRE blocking call, not just network latency
    // - If the agent takes longer than the HTTP timeout, the local request is aborted
    // - CRITICAL: Aborting the local request does NOT cancel the remote agent execution
    // - The agent continues running on TinyFish servers even after local timeout
    // - There is no SDK method to cancel an in-progress agent.run() after starting
    //
    // IMPLICATIONS:
    // - max_duration_seconds up to 600s cannot be fully utilized with 60s HTTP timeout
    // - Agent runs exceeding 60s will appear to fail locally but continue remotely
    // - Retrying after timeout will start a DUPLICATE agent run, not resume the first
    // - This is a known limitation of using agent.run() with current SDK timeout
    //
    // SAFE ALTERNATIVES FOR LONG RUNS (not implemented in Phase 3):
    // 1. Use agent.queue() + polling instead of agent.run()
    // 2. Increase SDK client timeout (requires testing impact on search/fetch)
    // 3. Use agent.stream() with progress events (requires architecture changes)
    const response = await client.agent.run(params);

    // Return sanitized response
    return formatAgentResponse(response);

  } catch (error) {
    return handleAgentError(error);
  }
}

/**
 * Format agent response into consistent structure
 * @param {Object} response - SDK response object
 * @returns {Object} Formatted response
 */
function formatAgentResponse(response) {
  const status = response.status;

  if (status === RunStatus.COMPLETED) {
    return {
      success: true,
      status: 'COMPLETED',
      result: response.result || null,
      run_id: response.run_id || null,
      // Do not include streaming_url or other internal fields
    };
  }

  if (status === RunStatus.FAILED) {
    return {
      success: false,
      status: 'FAILED',
      error: response.error?.message || 'Agent run failed',
      error_category: response.error?.category || 'UNKNOWN',
      run_id: response.run_id || null,
    };
  }

  // PENDING, RUNNING, CANCELLED should not occur with blocking agent.run()
  // but handle them defensively
  return {
    success: false,
    status: status,
    error: `Unexpected status: ${status}`,
    run_id: response.run_id || null,
  };
}

/**
 * Handle agent errors with appropriate messages
 * @param {Error} error - Error object
 * @returns {Object} Error response
 */
function handleAgentError(error) {
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

  if (error instanceof BadRequestError) {
    return {
      success: false,
      error: 'Invalid request',
      code: 'BAD_REQUEST',
      message: error.message || 'Invalid parameters provided',
    };
  }

  if (error instanceof InternalServerError) {
    return {
      success: false,
      error: 'TinyFish service error',
      code: 'SERVICE_ERROR',
      message: 'The automation service encountered an error. Please try again.',
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

  // Unknown error (including validation errors from this wrapper)
  return {
    success: false,
    error: 'Operation failed',
    code: 'UNKNOWN',
    message: error.message || String(error),
  };
}
