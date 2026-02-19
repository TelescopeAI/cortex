"""
Data models direct handler - Core service calls.

Handles data model operations in Direct mode.
"""
from typing import Optional
from uuid import UUID

from cortex.core.data.modelling.model import DataModel
from cortex.core.data.db.model_service import DataModelService
from cortex.core.query.executor import QueryExecutor
from cortex.sdk.schemas.requests.data_models import (
    DataModelCreateRequest,
    DataModelUpdateRequest,
    ModelExecutionRequest
)
from cortex.sdk.schemas.responses.data_models import (
    DataModelResponse,
    DataModelListResponse,
    ModelExecutionResponse
)
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


# Global query executor instance
query_executor = QueryExecutor()


def create_data_model(request: DataModelCreateRequest) -> DataModelResponse:
    """
    Create a new data model - direct Core service call.

    Args:
        request: Data model creation request

    Returns:
        Created data model response
    """
    db_service = DataModelService()

    try:
        # Create the data model
        data_model = DataModel(
            environment_id=request.environment_id,
            name=request.name,
            alias=request.alias,
            description=request.description,
            config=request.config or {}
        )

        # Save to database
        db_model = db_service.create_data_model(data_model)

        # Convert ORM to Pydantic
        saved_model = DataModel.model_validate(db_model)
        metrics_count = db_service.get_model_metrics_count(saved_model.id)

        response_data = saved_model.model_dump()
        response_data['metrics_count'] = metrics_count
        return DataModelResponse(**response_data)

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        db_service.close()


def get_data_model(model_id: UUID, environment_id: UUID) -> DataModelResponse:
    """
    Get a data model by ID - direct Core service call.

    Args:
        model_id: Data model ID
        environment_id: Environment ID

    Returns:
        Data model response
    """
    db_service = DataModelService()

    try:
        db_model = db_service.get_data_model_by_id(model_id, environment_id=environment_id)
        if not db_model:
            raise CortexNotFoundError(
                f"Data model with ID {model_id} not found in environment {environment_id}"
            )

        # Convert ORM to Pydantic
        saved_model = DataModel.model_validate(db_model)
        metrics_count = db_service.get_model_metrics_count(saved_model.id)

        response_data = saved_model.model_dump()
        response_data['metrics_count'] = metrics_count
        return DataModelResponse(**response_data)

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        db_service.close()


def list_data_models(
    environment_id: UUID,
    page: int = 1,
    page_size: int = 20,
    is_active: Optional[bool] = None
) -> DataModelListResponse:
    """
    List data models - direct Core service call.

    Args:
        environment_id: Environment ID
        page: Page number
        page_size: Page size
        is_active: Optional active status filter

    Returns:
        List of data model responses
    """
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
            pydantic_model = DataModel.model_validate(db_model)
            metrics_count = db_service.get_model_metrics_count(pydantic_model.id)

            response_data = pydantic_model.model_dump()
            response_data['metrics_count'] = metrics_count
            models.append(DataModelResponse(**response_data))

        total_count = len(models)

        return DataModelListResponse(
            models=models,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        db_service.close()


def update_data_model(
    model_id: UUID,
    request: DataModelUpdateRequest
) -> DataModelResponse:
    """
    Update a data model - direct Core service call.

    Args:
        model_id: Data model ID
        request: Update request

    Returns:
        Updated data model response
    """
    db_service = DataModelService()

    try:
        # Fetch existing model
        existing_db_model = db_service.get_data_model_by_id(
            model_id,
            environment_id=request.environment_id
        )
        if not existing_db_model:
            raise CortexNotFoundError(
                f"Data model with ID {model_id} not found in environment {request.environment_id}"
            )

        # Prepare update data (only include provided fields)
        update_data = {}

        if request.name is not None:
            update_data['name'] = request.name
        if request.alias is not None:
            update_data['alias'] = request.alias
        if request.description is not None:
            update_data['description'] = request.description
        if request.config is not None:
            update_data['config'] = request.config
        if request.is_active is not None:
            update_data['is_active'] = request.is_active

        # Update the model
        updated_db_model = db_service.update_data_model(model_id, update_data)
        if not updated_db_model:
            raise CortexNotFoundError(f"Data model with ID {model_id} not found")

        # Convert ORM to Pydantic
        updated_model = DataModel.model_validate(updated_db_model)
        metrics_count = db_service.get_model_metrics_count(updated_model.id)

        response_data = updated_model.model_dump()
        response_data['metrics_count'] = metrics_count
        return DataModelResponse(**response_data)

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        db_service.close()


def delete_data_model(model_id: UUID, environment_id: UUID) -> None:
    """
    Delete a data model (soft delete) - direct Core service call.

    Args:
        model_id: Data model ID
        environment_id: Environment ID
    """
    db_service = DataModelService()

    try:
        # Validate model exists in this environment
        existing_model = db_service.get_data_model_by_id(model_id, environment_id=environment_id)
        if not existing_model:
            raise CortexNotFoundError(
                f"Data model with ID {model_id} not found in environment {environment_id}"
            )

        success = db_service.delete_data_model(model_id)
        if not success:
            raise CortexNotFoundError(f"Data model with ID {model_id} not found")

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        db_service.close()


def execute_data_model(
    model_id: UUID,
    request: ModelExecutionRequest
) -> ModelExecutionResponse:
    """
    Execute a data model query - direct Core service call.

    Args:
        model_id: Data model ID
        request: Execution request

    Returns:
        Execution response with results
    """
    db_service = DataModelService()

    try:
        # Fetch the model
        db_model = db_service.get_data_model_by_id(model_id)
        if not db_model:
            raise CortexNotFoundError(f"Data model with ID {model_id} not found")

        # Convert to Pydantic model
        data_model = DataModel.model_validate(db_model)

        # Check if model is valid
        if not data_model.is_valid:
            raise ValueError(
                "Cannot execute invalid data model. Please validate and fix errors first."
            )

        # Execute the model
        execution_result = query_executor.execute_model(
            data_model=data_model,
            query_params=request.parameters or {},
            limit=getattr(request, 'limit', None),
            dry_run=getattr(request, 'dry_run', False)
        )

        return ModelExecutionResponse(
            success=execution_result.get("success", False),
            data=execution_result.get("results"),
            error=execution_result.get("error_message"),
            metadata={
                "execution_id": execution_result.get("execution_id"),
                "row_count": execution_result.get("row_count"),
                "execution_time_ms": execution_result.get("execution_time_ms"),
                "query": execution_result.get("query")
            }
        )

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        db_service.close()
