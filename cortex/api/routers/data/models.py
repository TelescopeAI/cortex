from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from cortex.api.schemas.requests.data_models import (
    DataModelCreateRequest,
    DataModelUpdateRequest,
    ModelExecutionRequest
)
from cortex.api.schemas.responses.data_models import (
    DataModelResponse,
    DataModelListResponse,
    ModelExecutionResponse
)
from cortex.core.data.modelling.model import DataModel
from cortex.core.data.db.model_service import DataModelService
from cortex.core.query.executor import QueryExecutor

# Create router instance
DataModelsRouter = APIRouter()

# Global query executor instance (in production, this might be dependency injected)
query_executor = QueryExecutor()


@DataModelsRouter.post("/data/models", response_model=DataModelResponse,
                       status_code=status.HTTP_201_CREATED,
                       tags=["Data Models"]
)
async def create_data_model(model_data: DataModelCreateRequest):
    """Create a new data model with semantic definitions."""
    try:
        # Create the data model
        data_model = DataModel(
            environment_id=model_data.environment_id,
            name=model_data.name,
            alias=model_data.alias,
            description=model_data.description,
            config=model_data.config or {}
        )
        
        # Save to database
        db_service = DataModelService()
        try:
            db_model = db_service.create_data_model(data_model)
            
            # Convert ORM to Pydantic using automatic conversion
            saved_model = DataModel.model_validate(db_model)
            metrics_count = db_service.get_model_metrics_count(saved_model.id)
            
            response_data = saved_model.model_dump()
            response_data['metrics_count'] = metrics_count
            return DataModelResponse(**response_data)
        finally:
            db_service.close()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create data model: {str(e)}"
        )


@DataModelsRouter.get("/data/models/{model_id}", response_model=DataModelResponse,
                      tags=["Data Models"]
)
async def get_data_model(model_id: UUID, environment_id: UUID = Query(..., description="Environment ID")):
    """Get a specific data model by ID, validating it belongs to the environment."""
    try:
        # Fetch from database
        db_service = DataModelService()
        try:
            db_model = db_service.get_data_model_by_id(model_id, environment_id=environment_id)
            if not db_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {model_id} not found in environment {environment_id}"
                )
            
            # Convert ORM to Pydantic using automatic conversion
            saved_model = DataModel.model_validate(db_model)
            metrics_count = db_service.get_model_metrics_count(saved_model.id)
            
            response_data = saved_model.model_dump()
            response_data['metrics_count'] = metrics_count
            return DataModelResponse(**response_data)
        finally:
            db_service.close()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data model: {str(e)}"
        )


@DataModelsRouter.get("/data/models", response_model=DataModelListResponse,
                      tags=["Data Models"]
)
async def list_data_models(
    environment_id: UUID = Query(..., description="Environment ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """List data models for a specific environment with optional filtering and pagination."""
    try:
        # Fetch from database with filters
        db_service = DataModelService()
        try:
            skip = (page - 1) * page_size
            db_models = db_service.get_all_data_models(
                environment_id=environment_id,
                skip=skip,
                limit=page_size,
                active_only=is_active
            )
            
            # Convert to Pydantic models and then to response models
            models = []
            for db_model in db_models:
                # Convert ORM to Pydantic using automatic conversion
                pydantic_model = DataModel.model_validate(db_model)
                metrics_count = db_service.get_model_metrics_count(pydantic_model.id)
                
                response_data = pydantic_model.model_dump()
                response_data['metrics_count'] = metrics_count
                models.append(DataModelResponse(**response_data))
            
            # For now, use length of results as total count (in production, do separate count query)
            total_count = len(models)
            
            return DataModelListResponse(
                models=models,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
        finally:
            db_service.close()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list data models: {str(e)}"
        )


@DataModelsRouter.put("/data/models/{model_id}", response_model=DataModelResponse,
                      tags=["Data Models"]
)
async def update_data_model(model_id: UUID, model_data: DataModelUpdateRequest):
    """Update an existing data model, validating it belongs to the environment."""
    try:
        # Fetch existing model from database
        db_service = DataModelService()
        try:
            existing_db_model = db_service.get_data_model_by_id(model_id, environment_id=model_data.environment_id)
            if not existing_db_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {model_id} not found in environment {model_data.environment_id}"
                )
            
            # Prepare update data (only include fields that are provided and not None)
            update_data = {}
            
            # Check each field explicitly to avoid attribute errors
            if hasattr(model_data, 'name') and model_data.name is not None:
                update_data['name'] = model_data.name
            if hasattr(model_data, 'alias') and model_data.alias is not None:
                update_data['alias'] = model_data.alias
            if hasattr(model_data, 'description') and model_data.description is not None:
                update_data['description'] = model_data.description
            if hasattr(model_data, 'config') and model_data.config is not None:
                update_data['config'] = model_data.config
            if hasattr(model_data, 'is_active') and model_data.is_active is not None:
                update_data['is_active'] = model_data.is_active
            
            # Update the model in database
            updated_db_model = db_service.update_data_model(model_id, update_data)
            if not updated_db_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {model_id} not found"
                )
            
            # Convert ORM to Pydantic using automatic conversion
            updated_model = DataModel.model_validate(updated_db_model)
            metrics_count = db_service.get_model_metrics_count(updated_model.id)
            
            response_data = updated_model.model_dump()
            response_data['metrics_count'] = metrics_count
            return DataModelResponse(**response_data)
            
        finally:
            db_service.close()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update data model: {str(e)}"
        )


@DataModelsRouter.delete("/data/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT,
                         tags=["Data Models"]
)
async def delete_data_model(model_id: UUID, environment_id: UUID = Query(..., description="Environment ID")):
    """Delete a data model (soft delete), validating it belongs to the environment."""
    try:
        db_service = DataModelService()
        try:
            # Validate model exists in this environment before deleting
            existing_model = db_service.get_data_model_by_id(model_id, environment_id=environment_id)
            if not existing_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {model_id} not found in environment {environment_id}"
                )
            success = db_service.delete_data_model(model_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {model_id} not found"
                )
        finally:
            db_service.close()
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete data model: {str(e)}"
        )


@DataModelsRouter.post("/data/models/{model_id}/execute", response_model=ModelExecutionResponse,
                       tags=["Data Models"]
)
async def execute_data_model(model_id: UUID, execution_request: ModelExecutionRequest):
    """Execute a data model query."""
    try:
        # Fetch the model from database
        db_service = DataModelService()
        try:
            db_model = db_service.get_data_model_by_id(model_id)
            if not db_model:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Data model with ID {model_id} not found"
                )
            
            # Convert to Pydantic model
            data_model = DataModel.model_validate(db_model)
            
            # Check if model is valid before execution
            if not data_model.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot execute invalid data model. Please validate and fix errors first."
                )
        finally:
            db_service.close()
        
        # Execute the model using the query executor
        execution_result = query_executor.execute_model(
            data_model=data_model,
            query_params=execution_request.parameters or {},
            limit=execution_request.limit,
            dry_run=execution_request.dry_run
        )
        
        return ModelExecutionResponse(
            model_id=model_id,
            execution_id=execution_result.execution_id,
            status=execution_result.status,
            query=execution_result.query,
            results=execution_result.results,
            row_count=execution_result.row_count,
            execution_time_ms=execution_result.execution_time_ms,
            executed_at=execution_result.executed_at,
            error_message=execution_result.error_message
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute data model: {str(e)}"
        ) 