from typing import List, Type, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, FieldFormat
from cortex.core.dashboards.mapping.modules import (
    SingleValueMapping,
    ChartMapping, 
    TableMapping,
    GaugeMapping
)
from cortex.core.types.dashboards import VisualizationType, ValueSelectionMode


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
        if visualization_type == VisualizationType.GAUGE and visualization_config:
            gauge_config = visualization_config.get('gauge_config', {})
            mapping = mapping_class(
                data_mapping=data_mapping,
                min_value=gauge_config.get('min_value', 0),
                max_value=gauge_config.get('max_value', 100),
                target_value=gauge_config.get('target_value')
            )
            sel_mode = gauge_config.get('selection_mode')
            if sel_mode is not None:
                try:
                    sel_mode = ValueSelectionMode(sel_mode) if isinstance(sel_mode, str) else sel_mode
                except Exception:
                    sel_mode = None
            if sel_mode is not None:
                setattr(mapping, 'selection_mode', sel_mode)
            if 'selection_config' in gauge_config:
                setattr(mapping, 'selection_config', gauge_config.get('selection_config'))
            # Attach formatting preferences (prefix/suffix/number_format) to x_axis if not present
            if hasattr(data_mapping, 'x_axis') and data_mapping.x_axis and getattr(data_mapping.x_axis, 'format', None) is None:
                fmt_kwargs: Dict[str, Any] = {}
                if 'prefix' in gauge_config:
                    fmt_kwargs['prefix'] = gauge_config.get('prefix')
                if 'suffix' in gauge_config:
                    fmt_kwargs['suffix'] = gauge_config.get('suffix')
                if 'number_format' in gauge_config:
                    fmt_kwargs['number_format'] = gauge_config.get('number_format')
                    # interpret integer as 0 decimals for backend formatting
                    try:
                        nf = gauge_config.get('number_format')
                        if isinstance(nf, str) and nf.lower() == 'integer':
                            fmt_kwargs['decimal_places'] = 0
                    except Exception:
                        pass
                if fmt_kwargs:
                    try:
                        data_mapping.x_axis.format = FieldFormat(**fmt_kwargs)
                    except Exception:
                        pass
            return mapping
        if visualization_type == VisualizationType.SINGLE_VALUE and visualization_config:
            sv = visualization_config.get('single_value_config', {})
            mapping = mapping_class(data_mapping=data_mapping)
            # attach selection preferences on instance (lightweight)
            sel_mode = sv.get('selection_mode')
            if sel_mode is not None:
                try:
                    sel_mode = ValueSelectionMode(sel_mode) if isinstance(sel_mode, str) else sel_mode
                except Exception:
                    sel_mode = None
            if sel_mode is not None:
                setattr(mapping, 'selection_mode', sel_mode)
            setattr(mapping, 'selection_config', sv.get('selection_config'))
            # Attach formatting preferences to x_axis if not present
            if hasattr(data_mapping, 'x_axis') and data_mapping.x_axis and getattr(data_mapping.x_axis, 'format', None) is None:
                fmt_kwargs: Dict[str, Any] = {}
                if 'prefix' in sv:
                    fmt_kwargs['prefix'] = sv.get('prefix')
                if 'suffix' in sv:
                    fmt_kwargs['suffix'] = sv.get('suffix')
                if 'number_format' in sv:
                    fmt_kwargs['number_format'] = sv.get('number_format')
                    try:
                        nf = sv.get('number_format')
                        if isinstance(nf, str) and nf.lower() == 'integer':
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
        if visualization_type in [VisualizationType.BAR_CHART, VisualizationType.LINE_CHART, VisualizationType.AREA_CHART] and visualization_config:
            chart_config = visualization_config.get('chart_config', {})
            mapping = mapping_class(data_mapping=data_mapping)
            # Attach chart config for stacking and other chart-specific options
            if chart_config:
                setattr(mapping, 'chart_config', chart_config)
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
