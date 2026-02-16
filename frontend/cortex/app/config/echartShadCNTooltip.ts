/**
 * Shadcn-styled ECharts tooltip configuration
 * Provides formatters that match Shadcn Vue design system
 */

export interface ShadcnTooltipOptions {
  /** Custom value formatter function */
  valueFormatter?: (value: number | string) => string
  /** Number of categories/data points - if >= 100, show axis label in tooltip */
  categorySize?: number
  /** Maximum decimal places for numbers (default: 3) */
  maxDigits?: number
}

/**
 * Creates a Shadcn-styled tooltip formatter for ECharts
 * Returns HTML with muted labels, bold values, and right-aligned layout
 */
export function createShadcnTooltipFormatter(options: ShadcnTooltipOptions = {}) {
  return function (params: any) {
    // Handle single data point
    if (!Array.isArray(params)) {
      params = [params]
    }

    const formatValue = (value: number | string): string => {
      if (options.valueFormatter) {
        return options.valueFormatter(value)
      }

      // Handle number formatting with maxDigits
      if (typeof value === 'number') {
        const maxDigits = options.maxDigits ?? 3
        // Check if number has decimals
        if (value % 1 !== 0) {
          return value.toFixed(maxDigits).replace(/\.?0+$/, '')
        }
        return String(value)
      }

      return String(value)
    }

    // Build tooltip HTML with Shadcn styling
    // Only show axis label if categorySize >= 20
    const showAxisLabel = options.categorySize && options.categorySize >= 20
    const axisLabel = showAxisLabel ? (params[0].axisValueLabel || params[0].name) : ''

    let html = `
      <div style="min-width: 180px; font-family: 'Geist Mono', monospace;">
        ${axisLabel ? `<div style="font-weight: 600; margin-bottom: 8px; color: inherit;">
          ${axisLabel}
        </div>` : ''}
    `

    // Add each series with proper styling
    params.forEach((param: any) => {
      const value = formatValue(param.value)
      html += `
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; gap: 8px;">
          <div style="display: flex; align-items: center; gap: 8px; font-size: 12px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 2px; background-color: ${param.color};"></span>
            <span style="color: hsl(215, 16%, 47%);">${param.seriesName}</span>
          </div>
          <span style="font-weight: 600; font-size: 13px; color: inherit; white-space: nowrap;">
            ${value}
          </span>
        </div>
      `
    })

    html += '</div>'
    return html
  }
}

/**
 * Returns complete tooltip configuration object for ECharts
 * Automatically applies Shadcn styling matching reference design
 */
export function getShadcnTooltipConfig(options: ShadcnTooltipOptions = {}) {
  return {
    trigger: 'axis',
    formatter: createShadcnTooltipFormatter(options),
    // Use transparent to let CSS handle background
    backgroundColor: 'rgba(0, 0, 0, 0)',
    borderColor: 'transparent',
    borderWidth: 0,
    textStyle: {
      color: 'inherit',
      fontSize: 12
    },
    padding: [12, 16],
    // Apply background, shadow, and border via CSS for better theme support
    extraCssText: `
      background: rgba(255, 255, 255, 0.98) !important;
      box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1) !important;
      border-radius: 0.5rem !important;
      backdrop-filter: blur(8px) !important;
      color: #09090b !important;
    `.replace(/\s+/g, ' ').trim()
  }
}
