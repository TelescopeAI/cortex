"""
Metric execution service for shared metric execution logic.
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.data.modelling.model import DataModel
from cortex.core.query.executor import QueryExecutor
from cortex.core.types.databases import DataSourceTypes
from cortex.core.semantics.metrics.modifiers import MetricModifiers
from cortex.core.services.metrics.metrics_generation import MetricsGenerationService
from cortex.core.data.modelling.validation_service import ValidationService


class MetricExecutionService:
    """Service for executing metrics with proper data model resolution."""
    
    @staticmethod
    def execute_metric(
        metric_id: Optional[UUID] = None,
        metric: Optional[SemanticMetric] = None,
        context_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
        grouped: Optional[bool] = None,
        cache_preference: Optional[CachePreference] = None,
        modifiers: Optional[MetricModifiers] = None,
        preview: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        Execute a metric and return the result.
        
        Args:
            metric_id: UUID of the metric to execute (mutually exclusive with metric)
            metric: SemanticMetric object to execute directly (mutually exclusive with metric_id)
            context_id: Optional context ID for execution
            parameters: Optional parameters for metric execution
            limit: Optional limit for result rows
            offset: Optional offset for result pagination
            source_type: Data source type (defaults to PostgreSQL)
            grouped: Optional override for grouping
            cache_preference: Optional cache preferences
            modifiers: Optional metric modifiers
            preview: If True, generate query without executing or saving to DB
            
        Returns:
            Dict containing execution result with success, data, metadata, and errors
            
        Raises:
            ValueError: If neither metric_id nor metric provided, or both provided,
                       or if metric/data model not found
            Exception: For execution errors
        """
        # Validate that exactly one of metric_id or metric is provided
        if metric_id is not None and metric is not None:
            raise ValueError("Cannot provide both metric_id and metric; provide exactly one")
        if metric_id is None and metric is None:
            raise ValueError("Must provide either metric_id or metric")
        
        metric_service = MetricService()
        model_service = DataModelService()
        
        try:
            # Get or use provided metric
            if metric is not None:
                # Use the provided metric directly
                resolved_metric = metric
                effective_metric_id = metric.id
            else:
                # Fetch metric from database
                db_metric = metric_service.get_metric_by_id(metric_id)
                if db_metric:
                    resolved_metric = SemanticMetric.model_validate(db_metric)
                    effective_metric_id = metric_id
                else:
                    raise ValueError(f"Metric with ID {metric_id} not found")
            
            # Get data model for the metric
            data_model = model_service.get_data_model_by_id(resolved_metric.data_model_id)
            if not data_model:
                raise ValueError(f"Data model with ID {resolved_metric.data_model_id} not found")
            
            # Convert ORM to Pydantic using automatic conversion
            data_model = DataModel.model_validate(data_model)
            
            # Infer source_type from data_source_id if available
            effective_source_type = source_type
            if resolved_metric.data_source_id:
                try:
                    data_source = DataSourceCRUD.get_data_source(resolved_metric.data_source_id)
                    # Convert to DataSourceTypes enum (handles both string and enum values)
                    effective_source_type = DataSourceTypes(data_source.source_type)
                except Exception as e:
                    # If data source lookup fails, fall back to provided source_type
                    # Log the error but don't fail the execution
                    logging.warning(f"Failed to fetch data source {resolved_metric.data_source_id}: {e}. Using provided source_type: {source_type}")
            
            # Validate metric before execution
            validation_result = ValidationService.validate_metric_execution(resolved_metric, data_model)
            
            # If validation fails, return early with validation errors
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "data": None,
                    "metadata": {"metric_id": str(effective_metric_id)},
                    "error": "Metric validation failed",
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                }
            
            # Execute the metric using QueryExecutor
            executor = QueryExecutor()
            
            # Execute the metric with the new architecture
            result = executor.execute_metric(
                metric=resolved_metric,
                data_model=data_model,
                parameters=parameters or {},
                limit=limit,
                offset=offset,
                source_type=effective_source_type,
                context_id=context_id,
                grouped=grouped,
                cache_preference=cache_preference,
                modifiers=modifiers,
                preview=preview,
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
