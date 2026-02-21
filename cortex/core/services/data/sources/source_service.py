"""Data source query service for running direct queries against data sources."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.utils.parsesql import convert_sqlalchemy_rows_to_dict


class DataSourceQueryService:
    """Service for executing direct queries against data sources."""

    @staticmethod
    def execute(
        data_source_id: UUID,
        environment_id: UUID,
        table: Optional[str] = None,
        statement: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = 0,
    ) -> Dict[str, Any]:
        """
        Execute a query against a data source.

        Args:
            data_source_id: The ID of the data source to query.
            environment_id: Environment ID for multi-tenancy validation.
            table: Table name for a SELECT * query. Mutually exclusive with statement.
            statement: Raw SQL statement to execute. Mutually exclusive with table.
            limit: Row limit for table queries. None returns all rows. Ignored for statement.
            offset: Row offset for table queries. Ignored for statement.

        Returns:
            Dictionary with success, data, row_count, query, duration, and error fields.
        """
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        if data_source.environment_id != environment_id:
            raise ValueError(
                f"Data source {data_source_id} does not belong to environment {environment_id}"
            )

        client = DBClientService.get_client(
            details=data_source.config,
            db_type=data_source.source_type,
        )
        client.connect()

        if table:
            available_tables = client.get_table_names()
            if table not in available_tables:
                raise ValueError(
                    f"Table '{table}' not found. Available tables: {available_tables}"
                )
            sql = f"SELECT * FROM {table}"
            if limit is not None:
                sql += f" LIMIT {limit}"
            if offset:
                sql += f" OFFSET {offset}"
        else:
            sql = statement

        start_time = time.time()
        try:
            results = client.query(sql)
            data = convert_sqlalchemy_rows_to_dict(results)
            duration = (time.time() - start_time) * 1000
            return {
                "success": True,
                "data": data,
                "row_count": len(data),
                "query": sql,
                "duration": round(duration, 2),
            }
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "query": sql,
                "duration": round(duration, 2),
            }
