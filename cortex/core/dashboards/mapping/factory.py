from typing import List, Type, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping
from cortex.core.dashboards.mapping.modules import (
    SingleValueMapping,
    ChartMapping, 
    TableMapping,
    GaugeMapping
)
from cortex.core.types.dashboards import VisualizationType


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
            return mapping_class(
                data_mapping=data_mapping,
                min_value=gauge_config.get('min_value', 0),
                max_value=gauge_config.get('max_value', 100),
                target_value=gauge_config.get('target_value')
            )
        
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
