"""
Join inference service for detecting and generating missing joins.

Ported from the frontend auto-join detection logic in MetricSchemaBuilder.vue,
enhanced with backend-only capabilities like actual foreign key metadata.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from cortex.core.semantics.joins import JoinCondition, JoinType, SemanticJoin
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.sql_schema import DatabaseSchema, TableSchema

logger = logging.getLogger(__name__)


class JoinInferenceService:
    """
    Detects missing joins in a metric and generates them from schema metadata.

    Uses three strategies in priority order:
    1. Foreign key relationships from the database schema
    2. Exact column name matches between tables
    3. Foreign key naming patterns (e.g., id ↔ {table}_id)
    """

    @staticmethod
    def collect_referenced_tables(metric: SemanticMetric) -> Set[str]:
        """Collect all table names referenced by measures, dimensions, and filters."""
        tables: Set[str] = set()

        if metric.table_name:
            tables.add(metric.table_name)

        for measure in metric.measures or []:
            if measure.table:
                tables.add(measure.table)

        for dimension in metric.dimensions or []:
            if dimension.table:
                tables.add(dimension.table)

        for filt in metric.filters or []:
            if filt.table:
                tables.add(filt.table)

        return tables

    @staticmethod
    def find_missing_join_tables(metric: SemanticMetric) -> Set[str]:
        """
        Find tables that are referenced but have no join defined.

        Returns set of table names that need joins to the base table.
        """
        if not metric.table_name:
            return set()

        referenced = JoinInferenceService.collect_referenced_tables(metric)
        base_table = metric.table_name

        # Build set of table pairs that already have joins
        joined_tables: Set[str] = {base_table}
        for join in metric.joins or []:
            joined_tables.add(join.left_table)
            joined_tables.add(join.right_table)

        return referenced - joined_tables

    @staticmethod
    def _singularize(name: str) -> str:
        """Simple singularization: remove trailing 's' (handles common cases)."""
        if name.endswith("ies"):
            return name[:-3] + "y"
        if name.endswith("ses") or name.endswith("xes") or name.endswith("zes"):
            return name[:-2]
        if name.endswith("s") and not name.endswith("ss"):
            return name[:-1]
        return name

    @staticmethod
    def _find_common_columns(
        table1: TableSchema,
        table2: TableSchema,
    ) -> List[Tuple[str, str]]:
        """
        Find joinable column pairs between two tables.

        Returns list of (table1_column, table2_column) pairs.
        Uses three strategies:
        1. Foreign key relationships
        2. Exact column name match
        3. FK naming pattern (id ↔ {table}_id)
        """
        pairs: List[Tuple[str, str]] = []
        t1_name = table1.name
        t2_name = table2.name
        t1_cols = {col.name for col in table1.columns}
        t2_cols = {col.name for col in table2.columns}

        # Strategy 1: Foreign key relationships
        for fk_schema in table1.foreign_keys:
            for rel in fk_schema.relations:
                if rel.referenced_table == t2_name and rel.column in t1_cols:
                    if rel.referenced_column in t2_cols:
                        pairs.append((rel.column, rel.referenced_column))

        for fk_schema in table2.foreign_keys:
            for rel in fk_schema.relations:
                if rel.referenced_table == t1_name and rel.column in t2_cols:
                    if rel.referenced_column in t1_cols:
                        pairs.append((rel.referenced_column, rel.column))

        if pairs:
            return pairs

        # Strategy 2: Exact column name match (prioritize 'id' columns)
        common = t1_cols & t2_cols
        for col_name in sorted(common, key=lambda c: (0 if "id" in c.lower() else 1, c)):
            pairs.append((col_name, col_name))

        if pairs:
            return pairs

        # Strategy 3: FK naming patterns
        t1_singular = JoinInferenceService._singularize(t1_name)
        t2_singular = JoinInferenceService._singularize(t2_name)

        # Check if table1 has 'id' and table2 has '{table1}_id'
        fk_name_for_t1 = f"{t1_singular}_id"
        if "id" in t1_cols and fk_name_for_t1 in t2_cols:
            pairs.append(("id", fk_name_for_t1))

        # Check if table2 has 'id' and table1 has '{table2}_id'
        fk_name_for_t2 = f"{t2_singular}_id"
        if "id" in t2_cols and fk_name_for_t2 in t1_cols:
            pairs.append((fk_name_for_t2, "id"))

        return pairs

    @staticmethod
    def infer_missing_joins(
        metric: SemanticMetric,
        schema: DatabaseSchema,
    ) -> List[SemanticJoin]:
        """
        Infer missing joins for a metric based on the data source schema.

        Only generates simple star-schema joins from the base table to
        referenced tables. Complex multi-hop joins are not generated.

        Args:
            metric: The metric to analyze
            schema: Database schema with table/column/FK metadata

        Returns:
            List of inferred SemanticJoin objects for missing joins
        """
        if not metric.table_name:
            return []

        missing_tables = JoinInferenceService.find_missing_join_tables(metric)
        if not missing_tables:
            return []

        base_table = metric.table_name

        # Build table lookup from schema
        table_lookup: Dict[str, TableSchema] = {t.name: t for t in schema.tables}

        base_schema = table_lookup.get(base_table)
        if not base_schema:
            return []

        inferred_joins: List[SemanticJoin] = []

        for target_table in sorted(missing_tables):
            target_schema = table_lookup.get(target_table)
            if not target_schema:
                continue

            column_pairs = JoinInferenceService._find_common_columns(
                base_schema, target_schema
            )
            if not column_pairs:
                continue

            # Use the first (best) match
            left_col, right_col = column_pairs[0]

            join = SemanticJoin(
                name=f"{base_table}_{target_table}_join",
                description=f"Auto-generated join from {base_table} to {target_table}",
                join_type=JoinType.LEFT,
                left_table=base_table,
                right_table=target_table,
                conditions=[
                    JoinCondition(
                        left_table=base_table,
                        left_column=left_col,
                        right_table=target_table,
                        right_column=right_col,
                        operator="=",
                    )
                ],
            )
            inferred_joins.append(join)

        return inferred_joins
