/**
 * ECharts theme matching Shadcn Vue design system (Light Mode)
 * Based on default Shadcn Vue color palette
 */
export const shadcnLightTheme = {
  // Color palette for data series (blue gradients from Tailwind)
  color: [
    '#1a3cb8',    // Blue-800: Darkest
    '#8fc5ff',   // Blue-400: Lightest
    '#1247e6',   // Blue-700
    '#2a7fff',   // Blue-500
    '#135dfc'   // Blue-600
  ],

  // Transparent background to blend with page
  backgroundColor: 'transparent',

  // Global text styling
  textStyle: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: 12,
    color: 'hsl(222.2, 84%, 4.9%)'  // --foreground
  },

  // Title styling
  title: {
    textStyle: {
      color: 'hsl(222.2, 84%, 4.9%)',
      fontSize: 16,
      fontWeight: 600
    },
    subtextStyle: {
      color: 'hsl(215.4, 16.3%, 46.9%)'  // --muted-foreground
    }
  },

  // Line chart defaults
  line: {
    itemStyle: {
      borderWidth: 2
    },
    lineStyle: {
      width: 2
    },
    symbolSize: 6,
    symbol: 'circle',
    smooth: false  // Straight lines by default, matches Shadcn style
  },

  // Bar chart defaults
  bar: {
    itemStyle: {
      borderRadius: [4, 4, 0, 0]  // Rounded top corners
    }
  },

  // Pie/Donut chart defaults
  pie: {
    itemStyle: {
      borderRadius: 4,
      borderColor: 'hsl(0, 0%, 100%)',
      borderWidth: 2
    }
  },

  // Category axis (X-axis typically)
  categoryAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: 'hsl(214.3, 31.8%, 91.4%)'  // --border
      }
    },
    axisTick: {
      show: false  // Hide ticks for cleaner look
    },
    axisLabel: {
      color: 'hsl(215.4, 16.3%, 46.9%)',  // --muted-foreground
      fontSize: 11
    },
    splitLine: {
      show: false
    }
  },

  // Value axis (Y-axis typically)
  valueAxis: {
    axisLine: {
      show: false
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: 'hsl(215.4, 16.3%, 46.9%)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'hsl(214.3, 31.8%, 91.4%)',  // --border
        type: 'solid',
        opacity: 0.5
      }
    }
  },

  // Time axis
  timeAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: 'hsl(214.3, 31.8%, 91.4%)'
      }
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: 'hsl(215.4, 16.3%, 46.9%)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'hsl(214.3, 31.8%, 91.4%)',
        opacity: 0.5
      }
    }
  },

  // Log axis
  logAxis: {
    axisLine: {
      show: false
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: 'hsl(215.4, 16.3%, 46.9%)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'hsl(214.3, 31.8%, 91.4%)',
        opacity: 0.5
      }
    }
  },

  // Tooltip styling (matches Shadcn popover)
  tooltip: {
    backgroundColor: 'hsl(0, 0%, 100%)',  // --popover
    borderColor: 'hsl(214.3, 31.8%, 91.4%)',  // --border
    borderWidth: 1,
    textStyle: {
      color: 'hsl(222.2, 84%, 4.9%)',  // --popover-foreground
      fontSize: 12
    },
    padding: [8, 12],
    // Rounded rectangular markers instead of circular
    extraCssText: 'box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); border-radius: 0.5rem;'
  },

  // Legend styling
  legend: {
    textStyle: {
      color: 'hsl(215.4, 16.3%, 46.9%)',  // --muted-foreground
      fontSize: 12
    },
    inactiveColor: 'hsl(215.4, 16.3%, 56.9%)',
    inactiveBorderColor: 'hsl(214.3, 31.8%, 91.4%)',
    pageTextStyle: {
      color: 'hsl(215.4, 16.3%, 46.9%)'
    }
  },

  // DataZoom component styling
  dataZoom: {
    backgroundColor: 'hsl(0, 0%, 98%)',
    borderColor: 'hsl(214.3, 31.8%, 91.4%)',
    fillerColor: 'hsla(12, 76%, 61%, 0.15)',  // --chart-1 with opacity
    handleStyle: {
      color: 'hsl(0, 0%, 100%)',
      borderColor: 'hsl(214.3, 31.8%, 91.4%)'
    },
    moveHandleStyle: {
      color: 'hsl(215.4, 16.3%, 46.9%)',
      opacity: 0.3
    },
    selectedDataBackground: {
      lineStyle: {
        color: 'hsl(12, 76%, 61%)'  // --chart-1
      },
      areaStyle: {
        color: 'hsl(12, 76%, 61%)',
        opacity: 0.2
      }
    },
    dataBackground: {
      lineStyle: {
        color: 'hsl(215.4, 16.3%, 46.9%)',
        opacity: 0.3
      },
      areaStyle: {
        color: 'hsl(215.4, 16.3%, 46.9%)',
        opacity: 0.1
      }
    },
    textStyle: {
      color: 'hsl(215.4, 16.3%, 46.9%)'
    }
  },

  // Toolbox styling
  toolbox: {
    iconStyle: {
      borderColor: 'hsl(215.4, 16.3%, 46.9%)'
    },
    emphasis: {
      iconStyle: {
        borderColor: 'hsl(222.2, 84%, 4.9%)'
      }
    }
  }
}
