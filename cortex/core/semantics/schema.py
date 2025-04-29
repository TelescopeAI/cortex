from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.telescope import TSModel


class SemanticSchema(TSModel):
    name: str
    type: DataSourceTypes
    

