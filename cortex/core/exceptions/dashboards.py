from uuid import UUID


class DashboardDoesNotExistError(Exception):
    """Raised when a dashboard with the given ID does not exist."""
    
    def __init__(self, dashboard_id: UUID):
        self.message = f"Dashboard with ID {dashboard_id} does not exist in the database"
        super().__init__(self.message)


class DashboardViewDoesNotExistError(Exception):
    """Raised when a dashboard view with the given ID does not exist."""
    
    def __init__(self, view_id: UUID):
        self.message = f"Dashboard view with ID {view_id} does not exist in the database"
        super().__init__(self.message)


class DashboardSectionDoesNotExistError(Exception):
    """Raised when a dashboard section with the given ID does not exist."""
    
    def __init__(self, section_id: UUID):
        self.message = f"Dashboard section with ID {section_id} does not exist in the database"
        super().__init__(self.message)


class DashboardWidgetDoesNotExistError(Exception):
    """Raised when a dashboard widget with the given ID does not exist."""
    
    def __init__(self, widget_id: UUID):
        self.message = f"Dashboard widget with ID {widget_id} does not exist in the database"
        super().__init__(self.message)


class DashboardAlreadyExistsError(Exception):
    """Raised when attempting to create a dashboard that already exists."""
    
    def __init__(self, name: str, environment_id: UUID):
        self.message = f"Dashboard with name '{name}' already exists in environment {environment_id}"
        super().__init__(self.message)


class InvalidDefaultViewError(Exception):
    """Raised when trying to set a default view that doesn't belong to the dashboard."""
    
    def __init__(self, dashboard_id: UUID, view_id: UUID):
        self.message = f"View {view_id} does not belong to dashboard {dashboard_id} and cannot be set as default"
        super().__init__(self.message)


class DashboardExecutionError(Exception):
    """Raised when dashboard execution fails."""
    
    def __init__(self, dashboard_id: UUID, error_message: str):
        self.message = f"Failed to execute dashboard {dashboard_id}: {error_message}"
        super().__init__(self.message)


class WidgetExecutionError(Exception):
    """Raised when widget execution fails."""
    
    def __init__(self, widget_id: UUID, error_message: str):
        self.message = f"Failed to execute widget {widget_id}: {error_message}"
        super().__init__(self.message)


class InvalidVisualizationConfigError(Exception):
    """Raised when visualization configuration is invalid for the chosen type."""
    
    def __init__(self, visualization_type: str, error_message: str):
        self.message = f"Invalid configuration for {visualization_type}: {error_message}"
        super().__init__(self.message)