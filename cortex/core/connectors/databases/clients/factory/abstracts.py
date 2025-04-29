from abc import abstractmethod, ABC

from cortex.core.types.telescope import TSModel


class DatabaseClientFactory(ABC):
    @abstractmethod
    def create_client(self, credentials: TSModel) -> TSModel:
        pass

