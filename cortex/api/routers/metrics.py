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
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.services.metrics import MetricExecutionService
from cortex.core.data.modelling.model import DataModel
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.types.databases import DataSourceTypes
from cortex.core.utils.schema_inference import auto_infer_semantic_types

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
        
        # Auto-infer source_type and source_meta for measures, dimensions, and filters
        measures = metric_data.measures
        dimensions = metric_data.dimensions  
        filters = metric_data.filters
        
        if metric_data.data_source_id and (measures or dimensions or filters):
            try:
                # Get data source schema for auto-inference
                data_source = DataSourceCRUD.get_data_source(metric_data.data_source_id)
                config = data_source.config
                
                # Add dialect for SQL databases if not present
                if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE]:
                    config["dialect"] = data_source.source_type
                
                # Create database client and get schema
                client = DBClientService.get_client(details=config, db_type=data_source.source_type)
                client.connect()
                schema = client.get_schema()
                
                # Auto-infer source types and metadata
                inferred_measures, inferred_dimensions, inferred_filters = auto_infer_semantic_types(
                    measures, dimensions, filters, schema
                )
                
                # Use inferred values if available, otherwise keep original
                measures = inferred_measures if inferred_measures is not None else measures
                dimensions = inferred_dimensions if inferred_dimensions is not None else dimensions
                filters = inferred_filters if inferred_filters is not None else filters
                
            except Exception as e:
                # Schema inference failed, but continue with metric creation
                # This ensures backward compatibility if schema inference has issues
                print(f"Warning: Schema inference failed for metric {metric_data.name}: {str(e)}")
        
        # Create metric with potentially updated measures/dimensions/filters
        metric = SemanticMetric(
            data_model_id=metric_data.data_model_id,
            name=metric_data.name,
            alias=metric_data.alias,
            description=metric_data.description,
            title=metric_data.title,
            query=metric_data.query,
            table_name=metric_data.table_name,
            data_source_id=metric_data.data_source_id,
            limit=metric_data.limit,
            measures=measures,
            dimensions=dimensions,
            joins=metric_data.joins,
            aggregations=metric_data.aggregations,
            filters=filters,

            parameters=metric_data.parameters,
            public=metric_data.public,
            refresh=metric_data.refresh,
            cache=metric_data.cache,
            meta=metric_data.meta,
            version=pydantic_model.version
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
            
            # Auto-infer source_type and source_meta for updated measures, dimensions, and filters
            metric_data_dict = metric_data.model_dump()
            
            # Only perform schema inference if measures, dimensions, or filters are being updated
            if any(key in metric_data_dict and metric_data_dict[key] is not None 
                   for key in ['measures', 'dimensions', 'filters']):
                
                # Get the data_source_id (either from update or existing metric)
                data_source_id = metric_data_dict.get('data_source_id') or db_metric.data_source_id
                
                if data_source_id:
                    try:
                        # Get data source schema for auto-inference
                        data_source = DataSourceCRUD.get_data_source(data_source_id)
                        config = data_source.config
                        
                        # Add dialect for SQL databases if not present
                        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE]:
                            config["dialect"] = data_source.source_type
                        
                        # Create database client and get schema
                        client = DBClientService.get_client(details=config, db_type=data_source.source_type)
                        client.connect()
                        schema = client.get_schema()
                        
                        # Get current or updated values
                        measures_data = metric_data_dict.get('measures') or db_metric.measures
                        dimensions_data = metric_data_dict.get('dimensions') or db_metric.dimensions
                        filters_data = metric_data_dict.get('filters') or db_metric.filters
                        
                        # Convert dicts to Pydantic models for inference
                        measures = None
                        dimensions = None
                        filters = None
                        
                        if measures_data:
                            measures = [SemanticMeasure.model_validate(m) if isinstance(m, dict) else m for m in measures_data]
                        if dimensions_data:
                            dimensions = [SemanticDimension.model_validate(d) if isinstance(d, dict) else d for d in dimensions_data]
                        if filters_data:
                            filters = [SemanticFilter.model_validate(f) if isinstance(f, dict) else f for f in filters_data]
                        
                        # Auto-infer source types and metadata
                        inferred_measures, inferred_dimensions, inferred_filters = auto_infer_semantic_types(
                            measures, dimensions, filters, schema
                        )
                        
                        # Update the metric_data_dict with inferred values (convert back to dicts for JSONB)
                        if 'measures' in metric_data_dict and metric_data_dict['measures'] is not None:
                            metric_data_dict['measures'] = [m.model_dump() if hasattr(m, 'model_dump') else m for m in inferred_measures] if inferred_measures else None
                        if 'dimensions' in metric_data_dict and metric_data_dict['dimensions'] is not None:
                            metric_data_dict['dimensions'] = [d.model_dump() if hasattr(d, 'model_dump') else d for d in inferred_dimensions] if inferred_dimensions else None
                        if 'filters' in metric_data_dict and metric_data_dict['filters'] is not None:
                            metric_data_dict['filters'] = [f.model_dump() if hasattr(f, 'model_dump') else f for f in inferred_filters] if inferred_filters else None
                        
                    except Exception as e:
                        # Schema inference failed, but continue with metric update
                        print(f"Warning: Schema inference failed for metric update {metric_id}: {str(e)}")
            
            # Update metric
            # Handle explicit None values for fields that can be cleared (like limit)
            updates = {}
            for k, v in metric_data_dict.items():
                if v is not None or k in ['limit', 'filters']:  # Allow None for limit and filters
                    updates[k] = v
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
        # Use the shared metric execution service
        result = MetricExecutionService.execute_metric(
            metric_id=metric_id,
            context_id=execution_request.context_id,
            parameters=execution_request.parameters,
            limit=execution_request.limit,
            offset=execution_request.offset,
            grouped=execution_request.grouped,
            cache_preference=getattr(execution_request, 'cache', None)
        )
        
        return MetricExecutionResponse(
            success=result["success"],
            data=result.get("data"),
            metadata=result.get("metadata", {}),
            errors=[result.get("error")] if not result["success"] else None
        )
        
    except ValueError as e:
        # Handle metric/model not found errors
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute metric: {str(e)}"
        )


@MetricsRouter.post("/metrics/{metric_id}/validate", response_model=MetricValidationResponse,
                   tags=["Metrics"])
async def validate_metric(metric_id: UUID):
    """Validate a metric configuration and save compiled query if valid."""
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
                compiled_query = generator.generate_query(grouped=metric.grouped if metric.grouped is not None else True)
                
                # If validation is successful and query compiled, save the compiled query to the database
                if validation_result.is_valid and compiled_query:
                    metric_service.update_metric(metric_id, {
                        "compiled_query": compiled_query,
                        "is_valid": True,
                        "validation_errors": None  # Clear any previous validation errors
                    })
                    
            except Exception as e:
                validation_result.errors.append(f"Query compilation failed: {str(e)}")
                validation_result.is_valid = False
                
                # Mark as invalid if compilation fails
                metric_service.update_metric(metric_id, {
                    "is_valid": False,
                    "validation_errors": [f"Compilation failed: {str(e)}"]
                })
            
            # If validation failed for other reasons, update the database accordingly
            if not validation_result.is_valid:
                metric_service.update_metric(metric_id, {
                    "is_valid": False,
                    "validation_errors": validation_result.errors
                })
            
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