"""
Response schemas for doctor diagnose endpoints.
"""

from typing import Optional

from cortex.core.types.doctor import Diagnosis
from cortex.core.types.telescope import TSModel


class DiagnoseResponse(TSModel):
    """Response from a diagnose operation."""

    healthy: bool
    diagnosis: Optional[Diagnosis] = None
