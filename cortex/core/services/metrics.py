"""
Metric execution service for shared metric execution logic.
"""
from typing import Dict, Any, Optional
from uuid import UUID

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.data.modelling.model import DataModel
from cortex.core.query.executor import QueryExecutor
from cortex.core.types.databases import DataSourceTypes


class MetricExecutionService:
    """Service for executing metrics with proper data model resolution."""
    
    @staticmethod
    def execute_metric(
        metric_id: UUID,
        context_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL
    ) -> Dict[str, Any]:
        """
        Execute a metric and return the result.
        
        Args:
            metric_id: UUID of the metric to execute
            context_id: Optional context ID for execution
            parameters: Optional parameters for metric execution
            limit: Optional limit for result rows
            offset: Optional offset for result pagination
            source_type: Data source type (defaults to PostgreSQL)
            
        Returns:
            Dict containing execution result with success, data, metadata, and errors
            
        Raises:
            ValueError: If metric or data model not found
            Exception: For execution errors
        """
        metric_service = MetricService()
        model_service = DataModelService()
        
        try:
            # Get metric
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise ValueError(f"Metric with ID {metric_id} not found")
            
            # Convert ORM to Pydantic using automatic conversion
            metric = SemanticMetric.model_validate(db_metric)
            
            # Get data model for the metric
            data_model = model_service.get_data_model_by_id(metric.data_model_id)
            if not data_model:
                raise ValueError(f"Data model with ID {metric.data_model_id} not found")
            
            # Convert ORM to Pydantic using automatic conversion
            pydantic_model = DataModel.model_validate(data_model)
            
            # Execute the metric using QueryExecutor
            executor = QueryExecutor()
            
            # Execute the metric with the new architecture
            result = executor.execute_metric(
                metric=metric,
                data_model=pydantic_model,
                parameters=parameters or {},
                limit=limit,
                offset=offset,
                source_type=source_type,
                context_id=context_id
            )
            
            return result
            
        finally:
            metric_service.close()
            model_service.close()
    
    @staticmethod
    def get_metric_details(metric_id: UUID) -> Dict[str, Any]:
        """
        Get metric details including data model information.
        
        Args:
            metric_id: UUID of the metric
            
        Returns:
            Dict containing metric and data model details
            
        Raises:
            ValueError: If metric or data model not found
        """
        metric_service = MetricService()
        model_service = DataModelService()
        
        try:
            # Get metric
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise ValueError(f"Metric with ID {metric_id} not found")
            
            # Convert ORM to Pydantic
            metric = SemanticMetric.model_validate(db_metric)
            
            # Get data model
            data_model = model_service.get_data_model_by_id(metric.data_model_id)
            if not data_model:
                raise ValueError(f"Data model with ID {metric.data_model_id} not found")
            
            # Convert ORM to Pydantic
            pydantic_model = DataModel.model_validate(data_model)
            
            return {
                "metric": metric,
                "data_model": pydantic_model
            }
            
        finally:
            metric_service.close()
            model_service.close()
