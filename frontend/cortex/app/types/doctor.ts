/**
 * Type definitions for the Doctor (Diagnose) API.
 *
 * Mirrors backend types from cortex/core/types/doctor.py and
 * cortex/sdk/schemas/requests/doctor.py / responses/doctor.py
 */

// ============================================================================
// Response Types
// ============================================================================

export interface Suggestion {
  /** Why the error occurred */
  description: string
  /** Corrected entity JSON that resolves the issue */
  fixed: Record<string, any>
}

export interface Diagnosis {
  /** Human-readable summary of ALL detected issues */
  explanation: string
  /** Concrete fix suggestions (only for issues where a fix could be generated) */
  suggestions: Suggestion[]
}

export interface DiagnoseResponse {
  /** Whether the entity is healthy (no issues detected) */
  healthy: boolean
  /** Full diagnosis result (null when healthy is true) */
  diagnosis: Diagnosis | null
}

// ============================================================================
// Request Types
// ============================================================================

export interface MetricDiagnoseRequest {
  metric_id?: string
  metric?: Record<string, any>
  environment_id: string
}

export interface VariantDiagnoseRequest {
  variant_id?: string
  variant?: Record<string, any>
  environment_id: string
}
