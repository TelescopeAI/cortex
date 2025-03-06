from core.types.databases import DataSourceTypes
from core.types.telescope import TSModel


class SemanticSchema(TSModel):
    name: str
    type: DataSourceTypes
    

