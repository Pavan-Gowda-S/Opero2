#!/usr/bin/env node

/**
 * TinyFish Service CLI - Entry point for subprocess calls from Python
 *
 * Usage:
 *   node index.js search --query "search term" [--location US] [--language en]
 *   node index.js fetch --urls "url1,url2" [--format markdown] [--links] [--image-links]
 *
 * Environment: Requires TINYFISH_API_KEY in environment or .env file
 */

import { search } from './lib/search.js';
import { fetchContent } from './lib/fetch.js';
import { runAgent } from './lib/agent.js';
import { validateAgentParams } from './lib/agent-validation.js';

/**
 * Parse command line arguments
 */
function parseArgs(args) {
  const parsed = {
    operation: args[2],
    options: {}
  };

  for (let i = 3; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].substring(2);
      const value = args[i + 1];

      // Handle boolean flags
      if (key === 'links' || key === 'image-links' || key === 'dry-run' || key === 'image_links') {
        parsed.options[key.replace(/-/g, '_')] = true;
      } else if (value && !value.startsWith('--')) {
        parsed.options[key.replace('-', '_')] = value;
        i++;
      }
    }
  }

  return parsed;
}

/**
 * Main execution function
 */
async function main() {
  try {
    const { operation, options } = parseArgs(process.argv);

    // Validate operation
    if (!operation) {
      console.error(JSON.stringify({
        success: false,
        error: 'No operation specified',
        usage: 'node index.js <search|fetch|agent> [options]'
      }));
      process.exit(1);
    }

    let result;

    switch (operation) {
      case 'search':
        if (!options.query) {
          throw new Error('--query is required for search operation');
        }

        // Dry run mode (for testing without API calls)
        if (options.dry_run) {
          result = {
            success: true,
            dry_run: true,
            operation: 'search',
            query: options.query,
            message: 'Dry run - no API call made'
          };
        } else {
          result = await search({
            query: options.query,
            maxResults: parseInt(options.max_results || '10'),
            location: options.location,
            language: options.language,
          });
        }
        break;

      case 'fetch':
        if (!options.urls) {
          throw new Error('--urls is required for fetch operation');
        }

        const urls = options.urls.split(',').map(u => u.trim());

        // Dry run mode
        if (options.dry_run) {
          result = {
            success: true,
            dry_run: true,
            operation: 'fetch',
            urls: urls,
            message: 'Dry run - no API call made'
          };
        } else {
          result = await fetchContent({
            urls: urls,
            format: options.format || 'markdown',
            links: options.links || false,
            imageLinks: options.image_links || false,
            timeout: parseInt(options.timeout || '45000'),
          });
        }
        break;

      case 'agent':
        // Parse and prepare parameters
        const agentParams = {
          url: options.url,
          goal: options.goal || options.task,
          maxSteps: options.max_steps ? parseInt(options.max_steps) : undefined,
          maxDurationSeconds: options.max_duration_seconds ? parseInt(options.max_duration_seconds) : undefined,
          browserProfile: options.browser_profile
        };

        // CRITICAL: Run validation in BOTH dry-run and live modes
        // This ensures consistent input checking regardless of execution path
        const validation = validateAgentParams(agentParams);

        if (!validation.valid) {
          // Return validation errors immediately
          throw new Error(validation.errors.join('; '));
        }

        // Dry run mode - validation passed, return success without making API call
        if (options.dry_run) {
          result = {
            success: true,
            dry_run: true,
            operation: 'agent',
            validated: validation.normalized,
            message: 'Dry run - validation passed, no API call made (agent automation would be billable)'
          };
        } else {
          // Live mode - validation passed, proceed with SDK call
          result = await runAgent(validation.normalized);
        }
        break;

      default:
        throw new Error(`Unknown operation: ${operation}. Use 'search', 'fetch', or 'agent'`);
    }

    // Output result as JSON
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);

  } catch (error) {
    // Output error as JSON
    console.error(JSON.stringify({
      success: false,
      error: error.message || String(error),
      code: error.code || 'UNKNOWN_ERROR',
    }, null, 2));
    process.exit(1);
  }
}

// Run main function
main();
