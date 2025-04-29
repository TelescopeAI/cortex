from uuid import UUID


class WorkspaceDoesNotExistError(Exception):
    def __init__(self, workspace_id: UUID):
        self.message = f"Workspace with ID {workspace_id} does not exist in the database"
        super().__init__(self.message)


class NoWorkspacesExistError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class WorkspaceAlreadyExistsError(Exception):
    def __init__(self, name: str):
        self.message = f"Workspace with name '{name}' already exists"
        super().__init__(self.message)
