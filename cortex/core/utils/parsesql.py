from sqlalchemy.engine.result import Row
from sqlalchemy.engine.row import RowProxy
from sqlalchemy.orm.query import Query
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import List, Any, Union, Iterable


def convert_sqlalchemy_rows_to_dict(rows: Union[Iterable, Query]) -> List[dict]:
    """
    Convert SQLAlchemy query results to a list of dictionaries,
    ensuring proper JSON serialization.
    """

    def serialize_value(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    def row_to_dict(row: Any) -> dict:
        if isinstance(row, dict):
            return {key: serialize_value(value) for key, value in row.items()}
        elif isinstance(row, (RowProxy, Row)):
            return {key: serialize_value(row[i]) for i, key in enumerate(row._fields)}
        elif hasattr(row, '_asdict'):  # Named tuple-like results
            return {key: serialize_value(value) for key, value in row._asdict().items()}
        elif hasattr(row, '__dict__'):  # ORM objects
            return {key: serialize_value(value) for key, value in row.__dict__.items()
                    if not key.startswith('_')}
        elif isinstance(row, (tuple, list)):  # Tuple-like objects
            return {f"column_{i}": serialize_value(value) for i, value in enumerate(row)}
        else:
            raise TypeError(f"Unsupported row type: {type(row)}")

    result = []
    for row in rows:
        try:
            result.append(row_to_dict(row))
        except Exception as e:
            print(f"Error processing row: {row}")
            print(f"Error details: {str(e)}")
            raise

    return result
