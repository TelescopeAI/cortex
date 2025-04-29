from enum import Enum

from cortex.core.types.telescope import TSModel


class SemanticJoinRelationship(Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class SemanticJoin(TSModel):
    name: str
    relationship: SemanticJoinRelationship
    query: str
