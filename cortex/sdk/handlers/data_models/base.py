"""
Data models handler - routes to direct or remote based on mode.

Provides unified interface for data model operations with hook integration.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
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
from . import direct, remote


class DataModelsHandler:
    """
    Handler for data models operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = DataModelsHandler(mode=ConnectionMode.DIRECT)
        >>> models = handler.list(environment_id=env_id)

        API mode:
        >>> handler = DataModelsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> models = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize data models handler.

        Args:
            mode: Connection mode (DIRECT or API)
            http_client: HTTP client instance (required for API mode)
            hooks: Hook manager for event emission
            client_context: Client context (workspace_id, environment_id)
        """
        self.mode = mode
        self.http_client = http_client
        self._hooks = hooks or HookManager()
        self._context = client_context or {}

    def _execute_with_hooks(
        self, operation: str, event_name: CortexEvents, func, **context_kwargs
    ):
        """
        Execute operation with hook lifecycle.

        Emits BEFORE → operation → AFTER (or ERROR) events.

        Args:
            operation: Operation name (e.g., "data_models.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="data_models",
            action=operation.split(".")[-1],
            event_type=HookEventType.BEFORE,
            event_name=event_name,
            params=context_kwargs,
            **context_kwargs,
        )
        context = self._hooks.emit_event(context)

        try:
            # Execute operation
            result = func()

            # AFTER hook
            context.event_type = HookEventType.AFTER
            context.result = result
            self._hooks.emit_event(context)

            return result
        except Exception as e:
            # ERROR hook
            context.event_type = HookEventType.ERROR
            context.error = e
            self._hooks.emit_event(context)
            raise

    def create(self, request: DataModelCreateRequest) -> DataModelResponse:
        """
        Create a new data model.

        Args:
            request: Data model creation request

        Returns:
            Created data model response

        Examples:
            >>> from cortex.sdk.schemas.requests.data_models import DataModelCreateRequest
            >>> request = DataModelCreateRequest(
            ...     environment_id=env_id,
            ...     name="My Model",
            ...     alias="my_model"
            ... )
            >>> model = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="data_models.create",
            event_name=CortexEvents.DATA_MODEL_CREATED,
            func=lambda: (
                direct.create_data_model(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_data_model(self.http_client, request)
            ),
            environment_id=request.environment_id,
        )

    def get(self, model_id: UUID, environment_id: UUID) -> DataModelResponse:
        """
        Get a data model by ID.

        Args:
            model_id: Data model ID
            environment_id: Environment ID

        Returns:
            Data model response

        Examples:
            >>> model = handler.get(model_id, environment_id=env_id)
            >>> print(model.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_data_model(model_id, environment_id)
        else:
            return remote.get_data_model(self.http_client, model_id, environment_id)

    def list(
        self,
        environment_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> DataModelListResponse:
        """
        List data models with pagination.

        Args:
            environment_id: Environment ID
            page: Page number
            page_size: Page size
            is_active: Optional active status filter

        Returns:
            List of data model responses

        Examples:
            >>> models = handler.list(environment_id=env_id, page=1, page_size=20)
            >>> for model in models.models:
            ...     print(model.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_data_models(environment_id, page, page_size, is_active)
        else:
            return remote.list_data_models(
                    self.http_client, environment_id, page, page_size, is_active
                )

    def update(
        self, model_id: UUID, request: DataModelUpdateRequest
    ) -> DataModelResponse:
        """
        Update a data model.

        Args:
            model_id: Data model ID
            request: Update request

        Returns:
            Updated data model response

        Examples:
            >>> from cortex.sdk.schemas.requests.data_models import DataModelUpdateRequest
            >>> request = DataModelUpdateRequest(
            ...     environment_id=env_id,
            ...     name="Updated Model"
            ... )
            >>> model = handler.update(model_id, request)
        """
        return self._execute_with_hooks(
            operation="data_models.update",
            event_name=CortexEvents.DATA_MODEL_UPDATED,
            func=lambda: (
                direct.update_data_model(model_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_data_model(self.http_client, model_id, request)
            ),
            model_id=model_id,
            environment_id=request.environment_id,
        )

    def delete(self, model_id: UUID, environment_id: UUID) -> None:
        """
        Delete a data model (soft delete).

        Args:
            model_id: Data model ID
            environment_id: Environment ID

        Examples:
            >>> handler.delete(model_id, environment_id=env_id)
        """
        self._execute_with_hooks(
            operation="data_models.delete",
            event_name=CortexEvents.DATA_MODEL_DELETED,
            func=lambda: (
                direct.delete_data_model(model_id, environment_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_data_model(self.http_client, model_id, environment_id)
            ),
            model_id=model_id,
            environment_id=environment_id,
        )

    def execute(
        self, model_id: UUID, request: ModelExecutionRequest
    ) -> ModelExecutionResponse:
        """
        Execute a data model query.

        Args:
            model_id: Data model ID
            request: Execution request

        Returns:
            Execution response with results

        Examples:
            >>> from cortex.sdk.schemas.requests.data_models import ModelExecutionRequest
            >>> request = ModelExecutionRequest(
            ...     metric_alias="my_metric",
            ...     parameters={"limit": 100}
            ... )
            >>> result = handler.execute(model_id, request)
            >>> print(result.data)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.execute_data_model(model_id, request)
        else:
            return remote.execute_data_model(self.http_client, model_id, request)
