from abc import ABC, abstractmethod

from core.types.telescope import TSModel


class DatabaseCredentialsFactory(ABC):
    @abstractmethod
    def get_creds(self, **kwargs) -> TSModel:
        pass
