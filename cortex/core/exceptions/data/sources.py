from typing import List
from uuid import UUID


class DataSourceDoesNotExistError(Exception):
    def __init__(self, data_source_id: UUID):
        self.message = f"Data source with ID {data_source_id} does not exist"
        super().__init__(self.message)


class DataSourceAlreadyExistsError(Exception):
    def __init__(self, name: str, environment_id: UUID):
        self.message = f"Data source with name '{name}' already exists in environment {environment_id}"
        super().__init__(self.message)


class DataSourceHasDependenciesError(Exception):
    def __init__(
        self,
        data_source_id: UUID,
        metric_ids: List[UUID]
    ):
        self.data_source_id = data_source_id
        self.metric_ids = metric_ids
        self.message = (
            f"Cannot delete data source {data_source_id}: "
            f"{len(metric_ids)} metric(s) depend on it"
        )
        super().__init__(self.message)


class FileDoesNotExistError(Exception):
    def __init__(self, file_id: UUID):
        self.message = f"File with ID {file_id} does not exist"
        super().__init__(self.message)


class FileHasDependenciesError(Exception):
    def __init__(self, file_id: UUID, data_source_ids: List[UUID], metric_count: int):
        self.file_id = file_id
        self.data_source_ids = data_source_ids
        self.metric_count = metric_count
        self.message = (
            f"Cannot delete file {file_id}: "
            f"{len(data_source_ids)} data source(s) and {metric_count} metric(s) depend on it"
        )
        super().__init__(self.message)