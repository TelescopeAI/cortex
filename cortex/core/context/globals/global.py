from uuid import UUID

from cortex.core.types.telescope import TSModel


class GlobalContext(TSModel):
    workspace_id: UUID
    project_id: UUID


