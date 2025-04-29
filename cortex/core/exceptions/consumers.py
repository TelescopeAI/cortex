from uuid import UUID

from uuid import UUID


class ConsumerDoesNotExistError(Exception):
    def __init__(self, consumer_id: UUID):
        self.message = f"Consumer with ID {consumer_id} does not exist"
        super().__init__(self.message)


class ConsumerAlreadyExistsError(Exception):
    def __init__(self, email: str, environment_id: UUID):
        self.message = f"Consumer with email {email} already exists in environment {environment_id}"
        super().__init__(self.message)


class ConsumerGroupDoesNotExistError(Exception):
    def __init__(self, group_id: UUID):
        self.message = f"Consumer group with ID {group_id} does not exist"
        super().__init__(self.message)


class ConsumerGroupAlreadyExistsError(Exception):
    def __init__(self, name: str, environment_id: UUID):
        self.message = f"Consumer group with name '{name}' already exists in environment {environment_id}"
        super().__init__(self.message)
