from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from cortex.api.schemas.requests.metrics import (
    MetricCreateRequest,
    MetricUpdateRequest,
    MetricExecutionRequest,
    MetricCloneRequest,
    MetricVersionCreateRequest
)
from cortex.api.schemas.responses.metrics import (
    MetricResponse,
    MetricListResponse,
    MetricExecutionResponse,
    MetricValidationResponse,
    MetricVersionResponse,
    MetricVersionListResponse
)
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.modelling.model import DataModel

# Create router instance
MetricsRouter = APIRouter()


@MetricsRouter.post("/metrics", response_model=MetricResponse,
                   status_code=status.HTTP_201_CREATED,
                   tags=["Metrics"])
async def create_metric(metric_data: MetricCreateRequest):
    """Create a new metric."""
    try:
        # Verify data model exists
        model_service = DataModelService()
        try:
            data_model = model_service.get_data_model_by_id(metric_data.data_model_id)
            if not data_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {metric_data.data_model_id} not found"
                )
            
            # Convert ORM to Pydantic using automatic conversion
            pydantic_model = DataModel.model_validate(data_model)
            
        finally:
            model_service.close()
        
        # Create metric
        metric = SemanticMetric(
            data_model_id=metric_data.data_model_id,
            name=metric_data.name,
            alias=metric_data.alias,
            description=metric_data.description,
            title=metric_data.title,
            query=metric_data.query,
            table_name=metric_data.table_name,
            data_source=metric_data.data_source,
            measures=metric_data.measures,
            dimensions=metric_data.dimensions,
            joins=metric_data.joins,
            aggregations=metric_data.aggregations,
            output_formats=metric_data.output_formats,
            parameters=metric_data.parameters,
            public=metric_data.public,
            refresh_key=metric_data.refresh_key,
            meta=metric_data.meta,
            model_version=pydantic_model.version
        )
        
        # Save to database
        metric_service = MetricService()
        try:
            db_metric = metric_service.create_metric(metric)
            
            # Convert ORM to Pydantic using automatic conversion
            saved_metric = SemanticMetric.model_validate(db_metric)
            
            # Convert to response
            return MetricResponse(
                **saved_metric.model_dump(),
                data_model_name=pydantic_model.name
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create metric: {str(e)}"
        )


@MetricsRouter.get("/metrics/{metric_id}", response_model=MetricResponse,
                  tags=["Metrics"])
async def get_metric(metric_id: UUID):
    """Get a specific metric by ID."""
    try:
        metric_service = MetricService()
        try:
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            # Convert ORM to Pydantic using automatic conversion
            saved_metric = SemanticMetric.model_validate(db_metric)
            
            # Get data model name
            model_service = DataModelService()
            try:
                data_model = model_service.get_data_model_by_id(saved_metric.data_model_id)
                data_model_name = data_model.name if data_model else "Unknown"
            finally:
                model_service.close()
            
            return MetricResponse(
                **saved_metric.model_dump(),
                data_model_name=data_model_name
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metric: {str(e)}"
        )


@MetricsRouter.get("/metrics", response_model=MetricListResponse,
                  tags=["Metrics"])
async def list_metrics(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    data_model_id: Optional[UUID] = Query(None, description="Filter by data model ID"),
    public_only: Optional[bool] = Query(None, description="Filter by public status"),
    valid_only: Optional[bool] = Query(None, description="Filter by valid status")
):
    """List metrics with optional filtering and pagination."""
    try:
        metric_service = MetricService()
        try:
            skip = (page - 1) * page_size
            db_metrics = metric_service.get_all_metrics(
                skip=skip,
                limit=page_size,
                data_model_id=data_model_id,
                public_only=public_only,
                valid_only=valid_only
            )
            
            # Convert to response format with data model names
            metrics = []
            model_service = DataModelService()
            try:
                for db_metric in db_metrics:
                    # Convert ORM to Pydantic using automatic conversion
                    pydantic_metric = SemanticMetric.model_validate(db_metric)
                    data_model = model_service.get_data_model_by_id(pydantic_metric.data_model_id)
                    data_model_name = data_model.name if data_model else "Unknown"
                    
                    metrics.append(MetricResponse(
                        **pydantic_metric.model_dump(),
                        data_model_name=data_model_name
                    ))
            finally:
                model_service.close()
            
            total_count = len(metrics)  # In production, do separate count query
            
            return MetricListResponse(
                metrics=metrics,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
        finally:
            metric_service.close()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list metrics: {str(e)}"
        )


@MetricsRouter.put("/metrics/{metric_id}", response_model=MetricResponse,
                  tags=["Metrics"])
async def update_metric(metric_id: UUID, metric_data: MetricUpdateRequest):
    """Update an existing metric."""
    try:
        metric_service = MetricService()
        try:
            # Check if metric exists
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            # Update metric
            updates = {k: v for k, v in metric_data.model_dump().items() if v is not None}
            updated_metric = metric_service.update_metric(metric_id, updates)
            
            if not updated_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            saved_metric = SemanticMetric.model_validate(updated_metric)
            
            # Get data model name
            model_service = DataModelService()
            try:
                data_model = model_service.get_data_model_by_id(saved_metric.data_model_id)
                data_model_name = data_model.name if data_model else "Unknown"
            finally:
                model_service.close()
            
            return MetricResponse(
                **saved_metric.model_dump(),
                data_model_name=data_model_name
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update metric: {str(e)}"
        )


@MetricsRouter.delete("/metrics/{metric_id}",
                     status_code=status.HTTP_204_NO_CONTENT,
                     tags=["Metrics"])
async def delete_metric(metric_id: UUID):
    """Delete a metric."""
    try:
        metric_service = MetricService()
        try:
            success = metric_service.delete_metric(metric_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete metric: {str(e)}"
        )


@MetricsRouter.post("/metrics/{metric_id}/execute", response_model=MetricExecutionResponse,
                   tags=["Metrics"])
async def execute_metric(metric_id: UUID, execution_request: MetricExecutionRequest):
    """Execute a metric with parameters."""
    try:
        # Get metric
        metric_service = MetricService()
        try:
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            # Convert ORM to Pydantic using automatic conversion
            metric = SemanticMetric.model_validate(db_metric)
            
            # Get data model for the metric
            model_service = DataModelService()
            try:
                data_model = model_service.get_data_model_by_id(metric.data_model_id)
                if not data_model:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Data model with ID {metric.data_model_id} not found"
                    )
                
                # Convert ORM to Pydantic using automatic conversion
                pydantic_model = DataModel.model_validate(data_model)
                
            finally:
                model_service.close()
            
            # Execute the metric using QueryExecutor
            from cortex.core.query.executor import QueryExecutor
            from cortex.core.types.databases import DataSourceTypes
            
            executor = QueryExecutor()
            
            # Execute the metric with the new architecture
            result = executor.execute_metric(
                metric=metric,
                data_model=pydantic_model,
                parameters=execution_request.parameters,
                source_type=DataSourceTypes.POSTGRESQL
            )
            
            return MetricExecutionResponse(
                success=result["success"],
                data=result.get("data"),
                metadata=result.get("metadata", {}),
                errors=[result.get("error")] if not result["success"] else None
            )
            
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute metric: {str(e)}"
        )


@MetricsRouter.post("/metrics/{metric_id}/validate", response_model=MetricValidationResponse,
                   tags=["Metrics"])
async def validate_metric(metric_id: UUID):
    """Validate a metric configuration."""
    try:
        metric_service = MetricService()
        try:
            # Get metric
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            # Convert ORM to Pydantic using automatic conversion
            metric = SemanticMetric.model_validate(db_metric)
            
            # Get data model for the metric
            model_service = DataModelService()
            try:
                data_model = model_service.get_data_model_by_id(metric.data_model_id)
                if not data_model:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Data model with ID {metric.data_model_id} not found"
                    )
                
                # Convert ORM to Pydantic using automatic conversion
                pydantic_model = DataModel.model_validate(data_model)
                
            finally:
                model_service.close()
            
            # Use ValidationService for comprehensive validation
            from cortex.core.data.modelling.validation_service import ValidationService
            
            validation_result = ValidationService.validate_metric_execution(
                metric, 
                pydantic_model
            )
            
            # Try to generate a query to check compilation
            compiled_query = None
            try:
                from cortex.core.query.engine.factory import QueryGeneratorFactory
                from cortex.core.types.databases import DataSourceTypes
                
                generator = QueryGeneratorFactory.create_generator(metric, DataSourceTypes.POSTGRESQL)
                compiled_query = generator.generate_query()
            except Exception as e:
                validation_result.errors.append(f"Query compilation failed: {str(e)}")
                validation_result.is_valid = False
            
            return MetricValidationResponse(
                is_valid=validation_result.is_valid,
                errors=validation_result.errors if validation_result.errors else None,
                warnings=validation_result.warnings if validation_result.warnings else None,
                compiled_query=compiled_query
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate metric: {str(e)}"
        )


@MetricsRouter.post("/metrics/{metric_id}/compile", response_model=MetricResponse,
                   tags=["Metrics"])
async def compile_metric(metric_id: UUID):
    """Compile a metric to generate SQL query."""
    try:
        metric_service = MetricService()
        try:
            # Get metric
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            metric = SemanticMetric.model_validate(db_metric)
            
            # Generate SQL query using QueryGeneratorFactory
            from cortex.core.query.engine.factory import QueryGeneratorFactory
            from cortex.core.types.databases import DataSourceTypes
            
            try:
                generator = QueryGeneratorFactory.create_generator(metric, DataSourceTypes.POSTGRESQL)
                compiled_query = generator.generate_query()
                
                # Update the metric with the compiled query
                updated_metric = metric_service.update_metric(metric_id, {
                    "compiled_query": compiled_query,
                    "is_valid": True
                })
                
                if not updated_metric:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Metric with ID {metric_id} not found"
                    )
                
                saved_metric = SemanticMetric.model_validate(updated_metric)
                
                # Get data model name
                model_service = DataModelService()
                try:
                    data_model = model_service.get_data_model_by_id(saved_metric.data_model_id)
                    data_model_name = data_model.name if data_model else "Unknown"
                finally:
                    model_service.close()
                
                return MetricResponse(
                    **saved_metric.model_dump(),
                    data_model_name=data_model_name
                )
                
            except Exception as e:
                # Mark as invalid if compilation fails
                metric_service.update_metric(metric_id, {
                    "is_valid": False,
                    "validation_errors": [f"Compilation failed: {str(e)}"]
                })
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to compile metric: {str(e)}"
                )
            
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile metric: {str(e)}"
        )


@MetricsRouter.post("/metrics/{metric_id}/clone", response_model=MetricResponse,
                   tags=["Metrics"])
async def clone_metric(metric_id: UUID, clone_request: MetricCloneRequest):
    """Clone a metric to another data model."""
    try:
        # Verify target data model exists
        model_service = DataModelService()
        try:
            target_model = model_service.get_data_model_by_id(clone_request.target_data_model_id)
            if not target_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target data model with ID {clone_request.target_data_model_id} not found"
                )
        finally:
            model_service.close()
        
        metric_service = MetricService()
        try:
            # Clone metric
            cloned_metric = metric_service.clone_metric(
                metric_id, 
                clone_request.target_data_model_id,
                clone_request.new_name
            )
            
            saved_metric = SemanticMetric.model_validate(cloned_metric)
            
            return MetricResponse(
                **saved_metric.model_dump(),
                data_model_name=target_model.name
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clone metric: {str(e)}"
        )


@MetricsRouter.get("/metrics/{metric_id}/versions", response_model=MetricVersionListResponse,
                  tags=["Metrics"])
async def list_metric_versions(metric_id: UUID):
    """List all versions of a metric."""
    try:
        metric_service = MetricService()
        try:
            # Check if metric exists
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Metric with ID {metric_id} not found"
                )
            
            # Get versions
            db_versions = metric_service.get_metric_versions(metric_id)
            
            versions = []
            for db_version in db_versions:
                versions.append(MetricVersionResponse(
                    id=db_version.id,
                    metric_id=db_version.metric_id,
                    version_number=db_version.version_number,
                    snapshot_data=db_version.snapshot_data,
                    description=db_version.description,
                    created_by=db_version.created_by,
                    tags=db_version.tags,
                    created_at=db_version.created_at
                ))
            
            return MetricVersionListResponse(
                versions=versions,
                total_count=len(versions)
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list metric versions: {str(e)}"
        )


@MetricsRouter.post("/metrics/{metric_id}/versions", response_model=MetricVersionResponse,
                   status_code=status.HTTP_201_CREATED,
                   tags=["Metrics"])
async def create_metric_version(metric_id: UUID, version_request: MetricVersionCreateRequest):
    """Create a new version of a metric."""
    try:
        metric_service = MetricService()
        try:
            # Create version
            db_version = metric_service.create_metric_version(
                metric_id, 
                version_request.description
            )
            
            return MetricVersionResponse(
                id=db_version.id,
                metric_id=db_version.metric_id,
                version_number=db_version.version_number,
                snapshot_data=db_version.snapshot_data,
                description=db_version.description,
                created_by=db_version.created_by,
                tags=db_version.tags,
                created_at=db_version.created_at
            )
        finally:
            metric_service.close()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create metric version: {str(e)}"
        ) 