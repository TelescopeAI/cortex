/**
 * ECharts theme matching Shadcn Vue design system (Dark Mode)
 * Based on default Shadcn Vue dark mode color palette
 */
export const shadcnDarkTheme = {
  // Color palette for data series (blue gradients from Tailwind - brighter for dark mode)
  color: [
    '#8fc5ff',   // Blue-400: Lightest
    '#2a7fff',   // Blue-500
    '#135dfc',   // Blue-600
    '#1247e6',   // Blue-700
    '#1a3cb8'    // Blue-800: Darkest
  ],

  // Dark background (transparent to blend with page)
  backgroundColor: 'transparent',

  // Global text styling for dark mode
  textStyle: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: 12,
    color: 'hsl(210, 40%, 98%)'  // --foreground in dark mode
  },

  // Title styling
  title: {
    textStyle: {
      color: 'hsl(210, 40%, 98%)',
      fontSize: 16,
      fontWeight: 600
    },
    subtextStyle: {
      color: 'hsl(215, 20.2%, 65.1%)'  // --muted-foreground in dark
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
    smooth: false
  },

  // Bar chart defaults
  bar: {
    itemStyle: {
      borderRadius: [4, 4, 0, 0]
    }
  },

  // Pie/Donut chart defaults
  pie: {
    itemStyle: {
      borderRadius: 4,
      borderColor: 'hsl(222.2, 84%, 4.9%)',
      borderWidth: 2
    }
  },

  // Category axis
  categoryAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: 'hsl(217.2, 32.6%, 17.5%)'  // --border in dark
      }
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: 'hsl(215, 20.2%, 65.1%)',  // --muted-foreground
      fontSize: 11
    },
    splitLine: {
      show: false
    }
  },

  // Value axis
  valueAxis: {
    axisLine: {
      show: false
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: 'hsl(215, 20.2%, 65.1%)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'hsl(217.2, 32.6%, 17.5%)',  // --border
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
        color: 'hsl(217.2, 32.6%, 17.5%)'
      }
    },
    axisTick: {
      show: false
    },
    axisLabel: {
      color: 'hsl(215, 20.2%, 65.1%)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'hsl(217.2, 32.6%, 17.5%)',
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
      color: 'hsl(215, 20.2%, 65.1%)',
      fontSize: 11
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: 'hsl(217.2, 32.6%, 17.5%)',
        opacity: 0.5
      }
    }
  },

  // Tooltip styling (matches Shadcn popover in dark mode)
  tooltip: {
    backgroundColor: 'hsl(222.2, 84%, 4.9%)',  // --popover in dark
    borderColor: 'hsl(217.2, 32.6%, 17.5%)',  // --border
    borderWidth: 1,
    textStyle: {
      color: 'hsl(210, 40%, 98%)',  // --popover-foreground
      fontSize: 12
    },
    padding: [8, 12],
    // Rounded rectangular markers instead of circular
    extraCssText: 'box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.3); border-radius: 0.5rem;'
  },

  // Legend styling
  legend: {
    textStyle: {
      color: 'hsl(215, 20.2%, 65.1%)',  // --muted-foreground
      fontSize: 12
    },
    inactiveColor: 'hsl(215, 20.2%, 45.1%)',
    inactiveBorderColor: 'hsl(217.2, 32.6%, 17.5%)',
    pageTextStyle: {
      color: 'hsl(215, 20.2%, 65.1%)'
    }
  },

  // DataZoom component styling
  dataZoom: {
    backgroundColor: 'hsl(222.2, 84%, 6%)',
    borderColor: 'hsl(217.2, 32.6%, 17.5%)',
    fillerColor: 'hsla(217, 91%, 60%, 0.15)',  // Blue-500 with opacity
    handleStyle: {
      color: 'hsl(222.2, 84%, 4.9%)',
      borderColor: 'hsl(217.2, 32.6%, 17.5%)'
    },
    moveHandleStyle: {
      color: 'hsl(215, 20.2%, 65.1%)',
      opacity: 0.3
    },
    selectedDataBackground: {
      lineStyle: {
        color: 'hsl(217, 91%, 60%)'  // Blue-500
      },
      areaStyle: {
        color: 'hsl(217, 91%, 60%)',
        opacity: 0.2
      }
    },
    dataBackground: {
      lineStyle: {
        color: 'hsl(215, 20.2%, 65.1%)',
        opacity: 0.3
      },
      areaStyle: {
        color: 'hsl(215, 20.2%, 65.1%)',
        opacity: 0.1
      }
    },
    textStyle: {
      color: 'hsl(215, 20.2%, 65.1%)'
    }
  },

  // Toolbox styling
  toolbox: {
    iconStyle: {
      borderColor: 'hsl(215, 20.2%, 65.1%)'
    },
    emphasis: {
      iconStyle: {
        borderColor: 'hsl(210, 40%, 98%)'
      }
    }
  }
}
