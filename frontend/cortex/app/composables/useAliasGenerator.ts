import { ref } from 'vue'

/**
 * Composable for generating and managing aliases from names
 * Provides auto-generation, validation, and manual edit tracking
 */
export function useAliasGenerator() {
  // Track if alias was manually edited
  const aliasManuallyEdited = ref(false)

  /**
   * Generate an alias from a name
   * Converts to lowercase, replaces spaces with underscores, removes special characters
   * @param name - The input name to convert to an alias
   * @returns The generated alias
   */
  const generateAlias = (name: string): string => {
    return name
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
      .replace(/_{2,}/g, '_')
      .replace(/^_+|_+$/g, '')
  }

  /**
   * Validate alias format
   * Checks if alias contains only lowercase letters, numbers, and underscores
   * @param alias - The alias to validate
   * @returns True if valid, false otherwise
   */
  const validateAlias = (alias: string): boolean => {
    // Allow only lowercase letters, numbers, and underscores
    // No spaces, no special characters except underscore
    const aliasRegex = /^[a-z0-9_]+$/
    return aliasRegex.test(alias) && alias.length > 0
  }

  /**
   * Get validation error message for an alias
   * @param alias - The alias to validate
   * @returns Error message if invalid, empty string if valid
   */
  const getAliasError = (alias: string): string => {
    if (!alias) return ''
    if (!validateAlias(alias)) {
      return 'Alias can only contain lowercase letters, numbers, and underscores'
    }
    return ''
  }

  /**
   * Reset the manual edit flag
   */
  const resetManualEditFlag = () => {
    aliasManuallyEdited.value = false
  }

  /**
   * Mark alias as manually edited
   */
  const markAsManuallyEdited = () => {
    aliasManuallyEdited.value = true
  }

  return {
    // State
    aliasManuallyEdited,
    
    // Functions
    generateAlias,
    validateAlias,
    getAliasError,
    resetManualEditFlag,
    markAsManuallyEdited
  }
} 