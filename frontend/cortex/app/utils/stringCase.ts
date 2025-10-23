/**
 * String case conversion utilities for formatting column names and labels
 */

/**
 * Convert a string to snake_case
 * Example: "User Name" -> "user_name"
 */
export function toSnakeCase(str: string): string {
  if (!str) return '';
  return String(str)
    .replace(/^[^A-Za-z0-9]*|[^A-Za-z0-9]*$/g, '')
    .replace(/([a-z])([A-Z])/g, (m, a, b) => `${a}_${b.toLowerCase()}`)
    .replace(/[^A-Za-z0-9]+|_+/g, '_')
    .toLowerCase();
}

/**
 * Convert a string to Title Case
 * Example: "user_name" -> "User Name"
 */
export function toTitleCase(str: string): string {
  if (!str) return '';
  return String(str)
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Convert a string to camelCase
 * Example: "user_name" -> "userName"
 */
export function toCamelCase(str: string): string {
  if (!str) return '';
  const words = String(str).split(/[\s_-]+/);
  if (words.length === 0) return '';
  
  return words[0].toLowerCase() + 
    words.slice(1).map(word => 
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join('');
}

/**
 * Convert a string to PascalCase
 * Example: "user_name" -> "UserName"
 */
export function toPascalCase(str: string): string {
  if (!str) return '';
  return String(str)
    .split(/[\s_-]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('');
}

/**
 * Convert a string to kebab-case
 * Example: "userName" -> "user-name"
 */
export function toKebabCase(str: string): string {
  if (!str) return '';
  return String(str)
    .replace(/^[^A-Za-z0-9]*|[^A-Za-z0-9]*$/g, '')
    .replace(/([a-z])([A-Z])/g, (m, a, b) => `${a}_${b.toLowerCase()}`)
    .replace(/[^A-Za-z0-9]+|_+/g, '-')
    .toLowerCase();
}

/**
 * Humanize a string - convert snake_case or camelCase to readable format
 * Example: "user_first_name" -> "User First Name"
 */
export function humanize(str: string): string {
  if (!str) return '';
  
  // Remove common suffixes like _id, _name, etc.
  let cleaned = String(str);
  
  // Split by underscores, hyphens, or camelCase
  const words = cleaned
    .replace(/([a-z])([A-Z])/g, '$1 $2') // Add space before capital letters
    .split(/[\s_-]+/) // Split on spaces, underscores, hyphens
    .filter(word => word.length > 0);
  
  // Capitalize first letter of each word
  return words
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Create a descriptive label from a column name
 * Example: "user_id" -> "User ID", "email_address" -> "Email Address"
 */
export function labelFromColumn(columnName: string): string {
  if (!columnName) return '';
  
  const humanized = humanize(columnName);
  
  // Handle common abbreviations
  return humanized
    .replace(/\bId\b/g, 'ID')
    .replace(/\bUrl\b/g, 'URL')
    .replace(/\bApi\b/g, 'API')
    .replace(/\bUuid\b/g, 'UUID')
    .replace(/\bHttp\b/g, 'HTTP')
    .replace(/\bSql\b/g, 'SQL');
}

