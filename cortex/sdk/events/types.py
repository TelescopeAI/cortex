"""
Cortex Events - Centralized event types for SDK and future events system.

Path: cortex/sdk/events/types.py

Reusable across:
- Hooks system
- Future events/messaging system
- Audit logging
- Metrics collection
"""
from enum import Enum


class HookEventType(str, Enum):
    """
    Base event types for all operations.

    Attributes:
        BEFORE: Event fired before an operation
        AFTER: Event fired after successful operation
        ERROR: Event fired when an operation fails

    Examples:
        >>> event_type = HookEventType.BEFORE
        >>> print(event_type.value)
        'before'
    """

    BEFORE = "before"
    AFTER = "after"
    ERROR = "error"


class CortexEvents(str, Enum):
    """
    All events across Cortex SDK.

    Naming convention: {MANAGER}_{ACTION}
    Example: METRIC_CREATED, FILE_UPLOADED, DASHBOARD_EXECUTED

    These events are emitted by SDK operations and can be handled by hooks.
    Reusable for future events/messaging system.

    Examples:
        >>> event = CortexEvents.METRIC_CREATED
        >>> print(event.value)
        'metric_created'

        >>> # Use in hooks
        >>> if context.event_name == CortexEvents.METRIC_CREATED:
        ...     print("Metric was created")
    """

    # Metrics events
    METRIC_CREATED = "metric_created"
    METRIC_UPDATED = "metric_updated"
    METRIC_DELETED = "metric_deleted"
    METRIC_EXECUTED = "metric_executed"
    METRIC_CLONED = "metric_cloned"
    METRIC_VERSION_CREATED = "metric_version_created"
    METRIC_VERSION_LISTED = "metric_version_listed"
    METRIC_RECOMMENDATIONS_GENERATED = "metric_recommendations_generated"

    # Metric Variants events
    METRIC_VARIANT_CREATED = "metric_variant_created"
    METRIC_VARIANT_UPDATED = "metric_variant_updated"
    METRIC_VARIANT_DELETED = "metric_variant_deleted"
    METRIC_VARIANT_EXECUTED = "metric_variant_executed"
    METRIC_VARIANT_DETACHED = "metric_variant_detached"
    METRIC_VARIANT_RESET = "metric_variant_reset"
    METRIC_VARIANT_SOURCE_OVERRIDDEN = "metric_variant_source_overridden"

    # Data Source events
    DATA_SOURCE_CREATED = "data_source_created"
    DATA_SOURCE_UPDATED = "data_source_updated"
    DATA_SOURCE_DELETED = "data_source_deleted"
    DATA_SOURCE_LISTED = "data_source_listed"
    DATA_SOURCE_PINGED = "data_source_pinged"
    DATA_SOURCE_SCHEMA_FETCHED = "data_source_schema_fetched"
    DATA_SOURCE_REFRESHED = "data_source_refreshed"

    # File Storage events
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"
    FILE_LISTED = "file_listed"

    # Spreadsheet events
    SPREADSHEET_SHEETS_DISCOVERED = "spreadsheet_sheets_discovered"
    SPREADSHEET_SHEET_PREVIEWED = "spreadsheet_sheet_previewed"

    # Data Model events
    DATA_MODEL_CREATED = "data_model_created"
    DATA_MODEL_UPDATED = "data_model_updated"
    DATA_MODEL_DELETED = "data_model_deleted"
    DATA_MODEL_LISTED = "data_model_listed"
    DATA_MODEL_EXECUTED = "data_model_executed"

    # Dashboard events
    DASHBOARD_CREATED = "dashboard_created"
    DASHBOARD_UPDATED = "dashboard_updated"
    DASHBOARD_DELETED = "dashboard_deleted"
    DASHBOARD_LISTED = "dashboard_listed"
    DASHBOARD_EXECUTED = "dashboard_executed"
    DASHBOARD_WIDGET_EXECUTED = "dashboard_widget_executed"

    # Workspace events
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_UPDATED = "workspace_updated"
    WORKSPACE_DELETED = "workspace_deleted"
    WORKSPACE_LISTED = "workspace_listed"

    # Environment events
    ENVIRONMENT_CREATED = "environment_created"
    ENVIRONMENT_UPDATED = "environment_updated"
    ENVIRONMENT_DELETED = "environment_deleted"
    ENVIRONMENT_LISTED = "environment_listed"

    # Consumer events
    CONSUMER_CREATED = "consumer_created"
    CONSUMER_UPDATED = "consumer_updated"
    CONSUMER_DELETED = "consumer_deleted"
    CONSUMER_LISTED = "consumer_listed"

    # Consumer Group events
    CONSUMER_GROUP_CREATED = "consumer_group_created"
    CONSUMER_GROUP_UPDATED = "consumer_group_updated"
    CONSUMER_GROUP_DELETED = "consumer_group_deleted"
    CONSUMER_GROUP_LISTED = "consumer_group_listed"

    # Pre-aggregation events
    PREAGGREGATION_BUILT = "preaggregation_built"
    PREAGGREGATION_REFRESHED = "preaggregation_refreshed"
    PREAGGREGATION_DELETED = "preaggregation_deleted"
    PREAGGREGATION_LISTED = "preaggregation_listed"

    # Query History events
    QUERY_LOGGED = "query_logged"
    QUERY_HISTORY_FETCHED = "query_history_fetched"

    # Admin events
    CACHE_CLEARED = "cache_cleared"
