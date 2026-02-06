/**
 * Normalizes URLs to ensure they have a protocol (https://) and are valid.
 * Handles common patterns like:
 * - "example.com" -> "https://example.com"
 * - "www.example.com" -> "https://www.example.com"
 * - "example.com/path" -> "https://example.com/path"
 * - "http://example.com" -> "https://example.com"
 * - "https://example.com" -> "https://example.com" (unchanged)
 */
export function normalizeUrl(input) {
  if (!input || typeof input !== 'string') {
    return input
  }

  // Trim whitespace
  let url = input.trim()

  // Remove trailing slashes (except after protocol)
  url = url.replace(/\/+$/, '')

  // If already has protocol, just upgrade http to https
  if (url.match(/^https?:\/\//i)) {
    // Upgrade http to https
    if (url.match(/^http:\/\//i)) {
      url = url.replace(/^http:\/\//i, 'https://')
    }
    return url
  }

  // If starts with //, add https:
  if (url.startsWith('//')) {
    return 'https:' + url
  }

  // Check if it looks like a domain (contains at least one dot, or is a valid domain)
  // Pattern: domain with optional subdomain, optional port, optional path
  const domainPattern = /^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}(\/.*)?$/
  const simpleDomainPattern = /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}(\/.*)?$/
  
  // Check for localhost or IP addresses
  const localhostPattern = /^(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?(\/.*)?$/
  const ipPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?(\/.*)?$/

  if (
    domainPattern.test(url) ||
    simpleDomainPattern.test(url) ||
    localhostPattern.test(url) ||
    ipPattern.test(url)
  ) {
    // Add https:// protocol
    return 'https://' + url
  }

  // If it doesn't match any pattern, return as-is (let backend handle validation)
  return url
}

/**
 * Validates if a string looks like a valid URL or domain
 */
export function isValidUrlOrDomain(input) {
  if (!input || typeof input !== 'string') {
    return false
  }

  const normalized = normalizeUrl(input.trim())
  
  try {
    // Try to create a URL object to validate
    new URL(normalized)
    return true
  } catch {
    return false
  }
}
