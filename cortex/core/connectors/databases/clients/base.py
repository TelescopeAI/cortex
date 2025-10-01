from abc import abstractmethod
from typing import Any, Optional

from pydantic import ConfigDict

from cortex.core.types.telescope import TSModel


class DatabaseClient(TSModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    credentials: TSModel
    client: Optional[Any] = None

    @abstractmethod
    def connect(self):
        # Implement connection logic using self.credentials
        pass

    @abstractmethod
    def get_uri(self) -> str:
        # Get connection string logic using self.credentials
        pass

    @abstractmethod
    def query(self, **kwargs):
        # Query logic using self.credentials
        pass

    @abstractmethod
    def get_schema(self):
        # Get schema logic using self.credentials
        pass

    @abstractmethod
    def get_table_names(self, **kwargs):
        # Get table contents using self.credentials
        pass




