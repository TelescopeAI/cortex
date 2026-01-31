from abc import ABC, abstractmethod
from typing import Any, Dict
from cortex.core.types.telescope import TSModel


class CortexSpreadsheetCredentials(TSModel, ABC):
    """Abstract base class for spreadsheet credentials"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert credentials to dictionary for storage"""
        pass
