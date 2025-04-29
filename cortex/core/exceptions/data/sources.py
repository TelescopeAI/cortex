from uuid import UUID


class DataSourceDoesNotExistError(Exception):
    def __init__(self, data_source_id: UUID):
        self.message = f"Data source with ID {data_source_id} does not exist"
        super().__init__(self.message)


class DataSourceAlreadyExistsError(Exception):
    def __init__(self, name: str, environment_id: UUID):
        self.message = f"Data source with name '{name}' already exists in environment {environment_id}"
        super().__init__(self.message)