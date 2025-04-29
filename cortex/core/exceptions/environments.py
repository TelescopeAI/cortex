from uuid import UUID


class EnvironmentDoesNotExistError(Exception):
    def __init__(self, environment_id: UUID):
        self.message = f"Environment with ID {environment_id} does not exist in the database"
        super().__init__(self.message)


class NoEnvironmentsExistError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class EnvironmentAlreadyExistsError(Exception):
    def __init__(self, name: str, workspace_id: UUID):
        self.message = f"Environment with name '{name}' already exists in workspace {workspace_id}"
        super().__init__(self.message)