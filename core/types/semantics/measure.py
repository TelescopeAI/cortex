from enum import Enum


class SemanticMeasureType(Enum):
    STRING = "string"
    NUMBER = "number"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    PERCENT = "percent"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    DURATION = "duration"


class SemanticMeasureOutputFormat(Enum):
    PERCENT = "percent"
    CURRENCY = "currency"

