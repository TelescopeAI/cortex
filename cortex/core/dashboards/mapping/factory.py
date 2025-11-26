from typing import List, Type, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, FieldFormat
from cortex.core.dashboards.mapping.modules import (
    SingleValueMapping,
    ChartMapping, 
    TableMapping,
    GaugeMapping,
    BoxPlotMapping
)
from cortex.core.types.dashboards import VisualizationType
from cortex.core.dashboards.dashboard import SingleValueConfig, GaugeConfig, ChartConfig


class MappingFactory:
    """Factory for creating visualization-specific mapping instances."""
    
    # Registry of visualization types to mapping classes
    MAPPING_REGISTRY: Dict[VisualizationType, Type[VisualizationMapping]] = {
        VisualizationType.SINGLE_VALUE: SingleValueMapping,
        VisualizationType.BAR_CHART: ChartMapping,
        VisualizationType.LINE_CHART: ChartMapping,
        VisualizationType.AREA_CHART: ChartMapping,
        VisualizationType.PIE_CHART: ChartMapping,
        VisualizationType.DONUT_CHART: ChartMapping,
        VisualizationType.SCATTER_PLOT: ChartMapping,
        VisualizationType.BOX_PLOT: BoxPlotMapping,
        VisualizationType.TABLE: TableMapping,
        VisualizationType.GAUGE: GaugeMapping,
    }
    
    @classmethod
    def create_mapping(
        self,
        visualization_type: VisualizationType,
        data_mapping: DataMapping,
        visualization_config: Optional[Dict[str, Any]] = None
    ) -> VisualizationMapping:
        """Create a visualization-specific mapping instance."""
        
        if visualization_type not in self.MAPPING_REGISTRY:
            raise ValueError(f"Unsupported visualization type: {visualization_type}")
        
        mapping_class = self.MAPPING_REGISTRY[visualization_type]
        
        # Handle special cases that need additional configuration
        if visualization_type == VisualizationType.GAUGE:
            # Parse gauge config using Pydantic model for defaults
            gauge_config_data = (visualization_config or {}).get('gauge_config') or {}
            gauge_config = GaugeConfig.model_validate(gauge_config_data) if gauge_config_data else GaugeConfig()
            
            mapping = mapping_class(
                data_mapping=data_mapping,
                min_value=gauge_config.min_value,
                max_value=gauge_config.max_value,
                target_value=gauge_config.target_value
            )
            
            # Attach selection preferences from Pydantic model (has defaults)
            setattr(mapping, 'selection_mode', gauge_config.selection_mode)
            setattr(mapping, 'selection_config', gauge_config.selection_config)
            
            # Attach formatting preferences to x_axis if not present
            if hasattr(data_mapping, 'x_axis') and data_mapping.x_axis and getattr(data_mapping.x_axis, 'format', None) is None:
                fmt_kwargs: Dict[str, Any] = {}
                # Note: GaugeConfig doesn't have prefix/suffix/number_format by default
                # These would come from visualization_config directly if needed
                if fmt_kwargs:
                    try:
                        data_mapping.x_axis.format = FieldFormat(**fmt_kwargs)
                    except Exception:
                        pass
            return mapping
            
        if visualization_type == VisualizationType.SINGLE_VALUE:
            # Parse single value config using Pydantic model for defaults
            sv_config_data = (visualization_config or {}).get('single_value_config') or {}
            sv_config = SingleValueConfig.model_validate(sv_config_data)
            
            mapping = mapping_class(data_mapping=data_mapping)
            
            # Attach selection preferences from Pydantic model (has defaults)
            setattr(mapping, 'selection_mode', sv_config.selection_mode)
            setattr(mapping, 'selection_config', sv_config.selection_config)
            
            # Attach formatting preferences to x_axis if not present
            if hasattr(data_mapping, 'x_axis') and data_mapping.x_axis and getattr(data_mapping.x_axis, 'format', None) is None:
                fmt_kwargs: Dict[str, Any] = {}
                if sv_config.prefix:
                    fmt_kwargs['prefix'] = sv_config.prefix
                if sv_config.suffix:
                    fmt_kwargs['suffix'] = sv_config.suffix
                if sv_config.number_format:
                    fmt_kwargs['number_format'] = sv_config.number_format
                    try:
                        if isinstance(sv_config.number_format, str) and sv_config.number_format.lower() == 'integer':
                            fmt_kwargs['decimal_places'] = 0
                    except Exception:
                        pass
                if fmt_kwargs:
                    try:
                        data_mapping.x_axis.format = FieldFormat(**fmt_kwargs)
                    except Exception:
                        pass
            return mapping
        
        # Handle chart types with chart_config
        if visualization_type in [VisualizationType.BAR_CHART, VisualizationType.LINE_CHART, VisualizationType.AREA_CHART]:
            chart_config_data = (visualization_config or {}).get('chart_config') or {}
            chart_config = ChartConfig.model_validate(chart_config_data) if chart_config_data else ChartConfig()
            
            mapping = mapping_class(data_mapping=data_mapping)
            # Attach chart config for stacking and other chart-specific options
            setattr(mapping, 'chart_config', chart_config.model_dump())
            return mapping
        
        # Default creation for most visualization types
        return mapping_class(data_mapping=data_mapping)
    
    @classmethod
    def get_supported_types(cls) -> List[VisualizationType]:
        """Get list of supported visualization types."""
        return list(cls.MAPPING_REGISTRY.keys())
    
    @classmethod
    def register_mapping(cls, visualization_type: VisualizationType, mapping_class: Type[VisualizationMapping]):
        """Register a new mapping class for a visualization type."""
        cls.MAPPING_REGISTRY[visualization_type] = mapping_class
