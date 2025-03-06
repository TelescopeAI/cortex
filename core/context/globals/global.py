from uuid import UUID

from core.types.telescope import TSModel


class GlobalContext(TSModel):
    workspace_id: UUID
    project_id: UUID


