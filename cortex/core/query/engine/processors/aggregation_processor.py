from typing import List, Optional
from cortex.core.semantics.aggregations import SemanticAggregation, AggregationType
from cortex.core.types.telescope import TSModel


class AggregationProcessor(TSModel):
    """
    Processes aggregation definitions and generates SQL aggregation clauses.
    """
    
    @staticmethod
    def process_aggregations(aggregations: List[SemanticAggregation]) -> Optional[str]:
        """
        Process a list of aggregations and generate SQL aggregation clauses.
        
        Args:
            aggregations: List of SemanticAggregation objects
            
        Returns:
            SQL aggregation clause string or None if no aggregations
        """
        if not aggregations:
            return None
            
        aggregation_clauses = []
        
        for aggregation in aggregations:
            agg_clause = AggregationProcessor._build_single_aggregation(aggregation)
            if agg_clause:
                aggregation_clauses.append(agg_clause)
        
        return ", ".join(aggregation_clauses) if aggregation_clauses else None
    
    @staticmethod
    def _build_single_aggregation(aggregation: SemanticAggregation) -> str:
        """
        Build a single aggregation clause from a SemanticAggregation.
        
        Args:
            aggregation: SemanticAggregation object
            
        Returns:
            SQL aggregation clause string
        """
        if aggregation.type == AggregationType.CUSTOM:
            return f"{aggregation.custom_expression} AS {aggregation.target_column}"
        
        # Handle basic aggregations
        source_columns = ", ".join(aggregation.source_columns)
        
        if aggregation.type == AggregationType.COUNT:
            agg_sql = f"COUNT({source_columns})"
        elif aggregation.type == AggregationType.SUM:
            agg_sql = f"SUM({source_columns})"
        elif aggregation.type == AggregationType.AVG:
            agg_sql = f"AVG({source_columns})"
        elif aggregation.type == AggregationType.MIN:
            agg_sql = f"MIN({source_columns})"
        elif aggregation.type == AggregationType.MAX:
            agg_sql = f"MAX({source_columns})"
        elif aggregation.type == AggregationType.STDDEV:
            agg_sql = f"STDDEV({source_columns})"
        elif aggregation.type == AggregationType.VARIANCE:
            agg_sql = f"VARIANCE({source_columns})"
        elif aggregation.type == AggregationType.PERCENTILE:
            percentile = aggregation.percentile_value or 0.5
            agg_sql = f"PERCENTILE_CONT({percentile}) WITHIN GROUP (ORDER BY {source_columns})"
        elif aggregation.type == AggregationType.MEDIAN:
            agg_sql = f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {source_columns})"
        else:
            # Handle window functions
            agg_sql = AggregationProcessor._build_window_function(aggregation)
        
        # Add WHERE condition if present
        if aggregation.where_condition:
            agg_sql = f"{agg_sql} FILTER (WHERE {aggregation.where_condition})"
        
        return f"{agg_sql} AS {aggregation.target_column}"
    
    @staticmethod
    def _build_window_function(aggregation: SemanticAggregation) -> str:
        """
        Build window function SQL from aggregation definition.
        
        Args:
            aggregation: SemanticAggregation object with window function
            
        Returns:
            SQL window function string
        """
        source_columns = ", ".join(aggregation.source_columns)
        
        if aggregation.type == AggregationType.ROW_NUMBER:
            func_sql = "ROW_NUMBER()"
        elif aggregation.type == AggregationType.RANK:
            func_sql = "RANK()"
        elif aggregation.type == AggregationType.DENSE_RANK:
            func_sql = "DENSE_RANK()"
        elif aggregation.type == AggregationType.LAG:
            func_sql = f"LAG({source_columns})"
        elif aggregation.type == AggregationType.LEAD:
            func_sql = f"LEAD({source_columns})"
        else:
            func_sql = f"{aggregation.type.upper()}({source_columns})"
        
        # Build window specification
        window_parts = []
        
        if aggregation.window and aggregation.window.partition_by:
            partition_cols = ", ".join(aggregation.window.partition_by)
            window_parts.append(f"PARTITION BY {partition_cols}")
        
        if aggregation.window and aggregation.window.order_by:
            order_cols = ", ".join(aggregation.window.order_by)
            window_parts.append(f"ORDER BY {order_cols}")
        
        if aggregation.window and aggregation.window.frame_start and aggregation.window.frame_end:
            window_parts.append(f"ROWS BETWEEN {aggregation.window.frame_start} AND {aggregation.window.frame_end}")
        
        window_spec = " ".join(window_parts) if window_parts else ""
        
        return f"{func_sql} OVER ({window_spec})" 