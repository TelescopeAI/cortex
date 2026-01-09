"""
Metrics generation service that recommends semantic metrics from data source schemas.

This module is intentionally SQL-dialect agnostic. It relies on schema metadata
only and avoids emitting dialect-specific expressions. It also introduces
controls to focus generation (tables/columns, metric types, time windows),
adds richer metric templates, and hardens naming/guardrails.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from uuid import UUID

from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.services.data_sources import DataSourceSchemaService
from cortex.core.semantics.conditions import ComparisonOperator, Condition, WhenClause
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.semantics.column_field import ColumnField
from cortex.core.types.semantics.filter import FilterOperator, FilterType, FilterValueType
from cortex.core.types.semantics.measure import SemanticMeasureType


class MetricsGenerationService:
    """
    Service for generating metric recommendations from database schemas.

    The service is designed to be safe-by-default (guardrails, filters) and
    adaptable across supported SQL databases by avoiding dialect-specific
    expressions.
    """

    # Column type classification constants
    NUMERIC_TYPES = {
        "REAL",
        "INTEGER",
        "INT",
        "NUMERIC",
        "DECIMAL",
        "FLOAT",
        "DOUBLE",
        "BIGINT",
        "SMALLINT",
        "TINYINT",
    }
    BOOLEAN_TYPES = {"BOOLEAN", "BOOL"}
    # Treat tinyint(1) as boolean for many warehouses
    BOOLEAN_LIKE_PREFIXES = {"TINYINT(1)", "BIT"}

    # Name pattern constants
    CATEGORICAL_KEYWORDS = [
        "type",
        "segment",
        "region",
        "country",
        "category",
        "status",
        "rating",
        "sector",
        "name",
        "channel",
        "state",
        "city",
    ]

    TECHNICAL_SUFFIXES = [
        "_usd",
        "_id",
        "_date",
        "_amount",
        "_count",
        "_number",
        "_percentage",
        "_year",
        "_month",
        "_ts",
    ]

    BOOLEAN_NAME_PREFIXES = ("is_", "has_", "can_", "should_", "flag_", "enabled_")

    DEFAULT_TIME_WINDOWS = [30]

    DEFAULT_METRIC_TYPES = {
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "count_distinct",
        "boolean",
    }
    MAX_METRICS_PER_TABLE = 200

    @staticmethod
    def _humanize_name(name: str) -> str:
        """
        Transform a database column/table name into a human-readable title.
        """
        humanized = name
        for suffix in MetricsGenerationService.TECHNICAL_SUFFIXES:
            if humanized.lower().endswith(suffix):
                humanized = humanized[: -len(suffix)]
                break

        words = humanized.split("_")
        return " ".join(word.capitalize() for word in words)

    @staticmethod
    def _slugify(table: str, name: str) -> str:
        base = f"{table}__{name}".lower().replace(" ", "_")
        return "".join(ch for ch in base if ch.isalnum() or ch == "_")

    @staticmethod
    def _is_numeric_column(column_type: str) -> bool:
        upper = column_type.upper()
        return any(t == upper or upper.startswith(t) for t in MetricsGenerationService.NUMERIC_TYPES)

    @staticmethod
    def _is_boolean_column(column_type: str, column_name: str) -> bool:
        upper = column_type.upper()
        if upper in MetricsGenerationService.BOOLEAN_TYPES:
            return True
        if any(upper.startswith(pref) for pref in MetricsGenerationService.BOOLEAN_LIKE_PREFIXES):
            return True
        lower_name = column_name.lower()
        return lower_name.startswith(MetricsGenerationService.BOOLEAN_NAME_PREFIXES) or lower_name.endswith(
            ("_flag", "_bool")
        )

    @staticmethod
    def _is_id_column(column_name: str) -> bool:
        return column_name.lower().endswith("_id")

    @staticmethod
    def _is_date_column(column_name: str) -> bool:
        lower_name = column_name.lower()
        return "date" in lower_name or "year" in lower_name or "month" in lower_name or "time" in lower_name

    @staticmethod
    def _is_categorical_column(column_type: str, column_name: str) -> bool:
        upper = column_type.upper()
        if upper in {"VARCHAR", "CHAR", "TEXT", "NVARCHAR"}:
            return True
        lower_name = column_name.lower()
        return any(keyword in lower_name for keyword in MetricsGenerationService.CATEGORICAL_KEYWORDS)

    @staticmethod
    def _classify_columns(
        table: Dict[str, Any],
        *,
        include_columns: Optional[Set[str]],
        exclude_columns: Optional[Set[str]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Classify columns in a table into different categories.
        """
        classified = {
            "numeric": [],
            "boolean": [],
            "id": [],
            "date": [],
            "categorical": [],
        }

        table_name = table.get("name")
        for column in table.get("columns", []):
            col_name = column.get("name")
            col_type = column.get("type")

            if not col_name or not col_type:
                continue

            fq = f"{table_name}.{col_name}".lower()
            if include_columns and fq not in include_columns and col_name.lower() not in include_columns:
                continue
            if exclude_columns and (fq in exclude_columns or col_name.lower() in exclude_columns):
                continue

            if MetricsGenerationService._is_numeric_column(col_type):
                classified["numeric"].append(column)
            elif MetricsGenerationService._is_boolean_column(col_type, col_name):
                classified["boolean"].append(column)

            if MetricsGenerationService._is_id_column(col_name):
                classified["id"].append(column)
            elif MetricsGenerationService._is_date_column(col_name):
                classified["date"].append(column)
            elif MetricsGenerationService._is_categorical_column(col_type, col_name):
                classified["categorical"].append(column)

        return classified

    @staticmethod
    def _create_boolean_measure(
        column_name: str,
        table_name: str,
        humanized_name: str,
        humanized_measure_name: Optional[str] = None,
        measure_type: SemanticMeasureType = SemanticMeasureType.SUM,
    ) -> SemanticMeasure:
        condition = Condition(
            when_clauses=[
                WhenClause(
                    field=ColumnField(column=column_name, table=table_name),
                    operator=ComparisonOperator.EQUALS,
                    compare_values=True,
                    then_return=1,
                )
            ],
            else_return=0,
        )

        measure_name = humanized_measure_name or MetricsGenerationService._humanize_name(
            f"count_{column_name}"
        )

        return SemanticMeasure(
            name=measure_name,
            description=f"Count of {humanized_name}",
            type=measure_type,
            conditional=True,
            conditions=condition,
            table=table_name,
        )

    @staticmethod
    def _create_time_filter(
        date_column: str,
        table_name: str,
        days: int = 30,
        *,
        tzinfo=timezone.utc,
    ) -> SemanticFilter:
        current_date = datetime.now(tz=tzinfo).date()
        past_date = current_date - timedelta(days=days)

        return SemanticFilter(
            name=f"last_{days}_days",
            description=f"Filter for records in the last {days} days",
            query=date_column,
            table=table_name,
            operator=FilterOperator.BETWEEN,
            filter_type=FilterType.WHERE,
            value_type=FilterValueType.DATE,
            min_value=past_date.isoformat(),
            max_value=current_date.isoformat(),
            is_active=True,
        )

    @staticmethod
    def _generate_time_dimensions(
        date_column: str,
        table_name: str,
        humanized_date: str,
        grains: Iterable[str],
    ) -> List[SemanticDimension]:
        dimensions: List[SemanticDimension] = []
        for grain in grains:
            name = f"{humanized_date} {grain.capitalize()}"
            dimensions.append(
                SemanticDimension(
                    name=name,
                    description=f"{humanized_date} at {grain} grain",
                    query=date_column,
                    table=table_name,
                )
            )
        return dimensions

    @staticmethod
    def _choose_count_column(table: Dict[str, Any], classified_columns: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
        id_columns = classified_columns.get("id", [])
        if id_columns:
            return id_columns[0]["name"]
        all_columns = table.get("columns", [])
        if all_columns:
            return all_columns[0].get("name")
        return None

    @staticmethod
    def _apply_table_filters(
        tables: List[Dict[str, Any]],
        include_tables: Optional[Set[str]],
        exclude_tables: Optional[Set[str]],
    ) -> List[Dict[str, Any]]:
        filtered = []
        for table in tables:
            name = table.get("name")
            if not name:
                continue
            lower = name.lower()
            if include_tables and lower not in include_tables:
                continue
            if exclude_tables and lower in exclude_tables:
                continue
            filtered.append(table)
        return filtered

    @staticmethod
    def _build_metric_name_and_title(table_name: str, base: str) -> Tuple[str, str]:
        slug = MetricsGenerationService._slugify(table_name, base)
        title = MetricsGenerationService._humanize_name(base)
        return slug, title

    @staticmethod
    def _should_create(metric_key: str, selected: Set[str]) -> bool:
        return metric_key in selected

    @staticmethod
    def _generate_single_value_metrics(
        table: Dict[str, Any],
        classified_columns: Dict[str, List[Dict[str, Any]]],
        environment_id: UUID,
        data_model_id: UUID,
        data_source_id: UUID,
        *,
        metric_types: Set[str],
        time_windows: List[int],
        grains: List[str],
        tzinfo,
    ) -> List[SemanticMetric]:
        metrics: List[SemanticMetric] = []
        table_name = table.get("name")
        humanized_table = MetricsGenerationService._humanize_name(table_name)

        count_column = MetricsGenerationService._choose_count_column(table, classified_columns)
        count_measure: Optional[SemanticMeasure] = None

        if count_column and MetricsGenerationService._should_create("count", metric_types):
            humanized_count = MetricsGenerationService._humanize_name("count")
            count_measure = SemanticMeasure(
                name=humanized_count,
                description=f"Count of {humanized_table}",
                type=SemanticMeasureType.COUNT,
                query=count_column,
                table=table_name,
            )
            metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                table_name, f"count_{table_name}"
            )
            metrics.append(
                SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_name,
                    title=metric_title,
                    description=f"Total number of records in the {humanized_table} table",
                    table_name=table_name,
                    measures=[count_measure],
                    grouped=False,
                )
            )

        for num_col in classified_columns.get("numeric", []):
            col_name = num_col["name"]
            humanized_col = MetricsGenerationService._humanize_name(col_name)

            if MetricsGenerationService._should_create("sum", metric_types):
                sum_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
                sum_measure = SemanticMeasure(
                    name=sum_name,
                    description=f"Total {humanized_col}",
                    type=SemanticMeasureType.SUM,
                    query=col_name,
                    table=table_name,
                )
                metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                    table_name, f"total_{col_name}"
                )
                metrics.append(
                    SemanticMetric(
                        environment_id=environment_id,
                        data_model_id=data_model_id,
                        data_source_id=data_source_id,
                        name=metric_name,
                        title=metric_title,
                        description=f"Sum of all {humanized_col} values from the {humanized_table} table",
                        table_name=table_name,
                        measures=[sum_measure],
                        grouped=False,
                    )
                )

            for agg_key, measure_type in [
                ("avg", SemanticMeasureType.AVG),
                ("min", SemanticMeasureType.MIN),
                ("max", SemanticMeasureType.MAX),
            ]:
                if MetricsGenerationService._should_create(agg_key, metric_types):
                    agg_name = MetricsGenerationService._humanize_name(f"{agg_key}_{col_name}")
                    agg_measure = SemanticMeasure(
                        name=agg_name,
                        description=f"{agg_key.upper()} of {humanized_col}",
                        type=measure_type,
                        query=col_name,
                        table=table_name,
                    )
                    metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                        table_name, f"{agg_key}_{col_name}"
                    )
                    metrics.append(
                        SemanticMetric(
                            environment_id=environment_id,
                            data_model_id=data_model_id,
                            data_source_id=data_source_id,
                            name=metric_name,
                            title=metric_title,
                            description=f"{agg_key.upper()} of {humanized_col} from the {humanized_table} table",
                            table_name=table_name,
                            measures=[agg_measure],
                            grouped=False,
                        )
                    )

        # Boolean metrics: count true, count false, percent true
        for bool_col in classified_columns.get("boolean", []):
            col_name = bool_col["name"]
            humanized_col = MetricsGenerationService._humanize_name(col_name)
            if MetricsGenerationService._should_create("boolean", metric_types):
                true_measure = MetricsGenerationService._create_boolean_measure(
                    col_name,
                    table_name,
                    humanized_col,
                    MetricsGenerationService._humanize_name(f"count_{col_name}_true"),
                    measure_type=SemanticMeasureType.SUM,
                )
                false_measure = MetricsGenerationService._create_boolean_measure(
                    col_name,
                    table_name,
                    humanized_col,
                    MetricsGenerationService._humanize_name(f"count_{col_name}_false"),
                    measure_type=SemanticMeasureType.SUM,
                )
                false_measure.conditions.when_clauses[0].then_return = 0  # type: ignore
                false_measure.conditions.else_return = 1  # type: ignore

                percent_true = MetricsGenerationService._create_boolean_measure(
                    col_name,
                    table_name,
                    humanized_col,
                    MetricsGenerationService._humanize_name(f"percent_{col_name}_true"),
                    measure_type=SemanticMeasureType.PERCENT,
                )

                base_name, base_title = MetricsGenerationService._build_metric_name_and_title(
                    table_name, f"{col_name}_boolean_metrics"
                )
                metrics.append(
                    SemanticMetric(
                        environment_id=environment_id,
                        data_model_id=data_model_id,
                        data_source_id=data_source_id,
                        name=base_name,
                        title=base_title,
                        description=f"Boolean metrics for {humanized_col} in {humanized_table}",
                        table_name=table_name,
                        measures=[true_measure, false_measure, percent_true],
                        grouped=False,
                    )
                )

        # Count distinct for id columns
        if MetricsGenerationService._should_create("count_distinct", metric_types):
            for id_col in classified_columns.get("id", []):
                col_name = id_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                distinct_name = MetricsGenerationService._humanize_name(f"distinct_{col_name}")
                distinct_measure = SemanticMeasure(
                    name=distinct_name,
                    description=f"Distinct count of {humanized_col}",
                    type=SemanticMeasureType.COUNT_DISTINCT,
                    query=col_name,
                    table=table_name,
                )
                metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                    table_name, f"distinct_{col_name}"
                )
                metrics.append(
                    SemanticMetric(
                        environment_id=environment_id,
                        data_model_id=data_model_id,
                        data_source_id=data_source_id,
                        name=metric_name,
                        title=metric_title,
                        description=f"Distinct count of {humanized_col} in the {humanized_table} table",
                        table_name=table_name,
                        measures=[distinct_measure],
                        grouped=False,
                    )
                )

        # Time-window variants
        date_columns = classified_columns.get("date", [])
        if date_columns:
            primary_date_col = date_columns[0]["name"]
            humanized_date_col = MetricsGenerationService._humanize_name(primary_date_col)
            for window_days in time_windows:
                time_filter = MetricsGenerationService._create_time_filter(
                    primary_date_col, table_name, window_days, tzinfo=tzinfo
                )

                if count_measure:
                    metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                        table_name, f"count_{window_days}d"
                    )
                    metrics.append(
                        SemanticMetric(
                            environment_id=environment_id,
                            data_model_id=data_model_id,
                            data_source_id=data_source_id,
                            name=metric_name,
                            title=metric_title,
                            description=(
                                f"Total number of {humanized_table} records from the last {window_days} days "
                                f"based on {humanized_date_col}"
                            ),
                            table_name=table_name,
                            measures=[count_measure],
                            filters=[time_filter],
                            grouped=False,
                        )
                    )

                for num_col in classified_columns.get("numeric", []):
                    col_name = num_col["name"]
                    humanized_col = MetricsGenerationService._humanize_name(col_name)
                    sum_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
                    sum_measure = SemanticMeasure(
                        name=sum_name,
                        description=f"Total {humanized_col}",
                        type=SemanticMeasureType.SUM,
                        query=col_name,
                        table=table_name,
                    )

                    metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                        table_name, f"total_{col_name}_{window_days}d"
                    )
                    metrics.append(
                        SemanticMetric(
                            environment_id=environment_id,
                            data_model_id=data_model_id,
                            data_source_id=data_source_id,
                            name=metric_name,
                            title=metric_title,
                            description=(
                                f"Sum of {humanized_col} from the last {window_days} days in the "
                                f"{humanized_table} table based on {humanized_date_col}"
                            ),
                            table_name=table_name,
                            measures=[sum_measure],
                            filters=[time_filter],
                            grouped=False,
                        )
                    )

            # Date dimensions by grain with numeric sums
            time_dimensions = MetricsGenerationService._generate_time_dimensions(
                primary_date_col, table_name, humanized_date_col, grains
            )
            for num_col in classified_columns.get("numeric", []):
                col_name = num_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                for dim in time_dimensions:
                    sum_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
                    sum_measure = SemanticMeasure(
                        name=sum_name,
                        description=f"Total {humanized_col}",
                        type=SemanticMeasureType.SUM,
                        query=col_name,
                        table=table_name,
                    )
                    metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                        table_name, f"total_{col_name}_by_{dim.name}"
                    )
                    metrics.append(
                        SemanticMetric(
                            environment_id=environment_id,
                            data_model_id=data_model_id,
                            data_source_id=data_source_id,
                            name=metric_name,
                            title=metric_title,
                            description=f"Sum of {humanized_col} grouped by {dim.name} from the {humanized_table} table",
                            table_name=table_name,
                            measures=[sum_measure],
                            dimensions=[dim],
                            grouped=True,
                        )
                    )

        return metrics

    @staticmethod
    def _generate_comparison_metrics(
        table: Dict[str, Any],
        classified_columns: Dict[str, List[Dict[str, Any]]],
        environment_id: UUID,
        data_model_id: UUID,
        data_source_id: UUID,
        *,
        metric_types: Set[str],
        grains: List[str],
    ) -> List[SemanticMetric]:
        metrics: List[SemanticMetric] = []
        table_name = table.get("name")
        humanized_table = MetricsGenerationService._humanize_name(table_name)

        count_column = MetricsGenerationService._choose_count_column(table, classified_columns)
        count_measure: Optional[SemanticMeasure] = None

        if count_column and MetricsGenerationService._should_create("count", metric_types):
            humanized_count = MetricsGenerationService._humanize_name("count")
            count_measure = SemanticMeasure(
                name=humanized_count,
                description=f"Count of {humanized_table}",
                type=SemanticMeasureType.COUNT,
                query=count_column,
                table=table_name,
            )

            for date_col in classified_columns.get("date", []):
                col_name = date_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)

                dimension = SemanticDimension(
                    name=humanized_col,
                    description=humanized_col,
                    query=col_name,
                    table=table_name,
                )

                metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                    table_name, f"count_by_{col_name}"
                )
                metrics.append(
                    SemanticMetric(
                        environment_id=environment_id,
                        data_model_id=data_model_id,
                        data_source_id=data_source_id,
                        name=metric_name,
                        title=metric_title,
                        description=f"Number of {humanized_table} records grouped by {humanized_col}",
                        table_name=table_name,
                        measures=[count_measure],
                        dimensions=[dimension],
                        grouped=True,
                    )
                )

            dimension_columns = classified_columns.get("id", []) + classified_columns.get("categorical", [])
            for dim_col in dimension_columns:
                col_name = dim_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)

                dimension = SemanticDimension(
                    name=humanized_col,
                    description=humanized_col,
                    query=col_name,
                    table=table_name,
                )

                metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                    table_name, f"count_per_{col_name}"
                )
                metrics.append(
                    SemanticMetric(
                        environment_id=environment_id,
                        data_model_id=data_model_id,
                        data_source_id=data_source_id,
                        name=metric_name,
                        title=metric_title,
                        description=f"Distribution of {humanized_table} records across different {humanized_col} values",
                        table_name=table_name,
                        measures=[count_measure],
                        dimensions=[dimension],
                        grouped=True,
                    )
                )

        date_columns = classified_columns.get("date", [])
        if date_columns:
            primary_date_col = date_columns[0]["name"]
            humanized_date = MetricsGenerationService._humanize_name(primary_date_col)

            date_dimensions = MetricsGenerationService._generate_time_dimensions(
                primary_date_col, table_name, humanized_date, grains
            )

            for num_col in classified_columns.get("numeric", []):
                col_name = num_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                sum_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
                sum_measure = SemanticMeasure(
                    name=sum_name,
                    description=f"Total {humanized_col}",
                    type=SemanticMeasureType.SUM,
                    query=col_name,
                    table=table_name,
                )
                for dim in date_dimensions:
                    metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                        table_name, f"total_{col_name}_by_{dim.name}"
                    )
                    metrics.append(
                        SemanticMetric(
                            environment_id=environment_id,
                            data_model_id=data_model_id,
                            data_source_id=data_source_id,
                            name=metric_name,
                            title=metric_title,
                            description=f"Sum of {humanized_col} grouped by {dim.name} from the {humanized_table} table",
                            table_name=table_name,
                            measures=[sum_measure],
                            dimensions=[dim],
                            grouped=True,
                        )
                    )

        categorical_columns = classified_columns.get("categorical", [])
        for bool_col in classified_columns.get("boolean", []):
            bool_name = bool_col["name"]
            humanized_bool = MetricsGenerationService._humanize_name(bool_name)
            bool_measure = MetricsGenerationService._create_boolean_measure(
                bool_name,
                table_name,
                humanized_bool,
                MetricsGenerationService._humanize_name(f"count_{bool_name}"),
                measure_type=SemanticMeasureType.SUM,
            )

            for cat_col in categorical_columns:
                cat_name = cat_col["name"]
                humanized_cat = MetricsGenerationService._humanize_name(cat_name)

                dimension = SemanticDimension(
                    name=humanized_cat,
                    description=humanized_cat,
                    query=cat_name,
                    table=table_name,
                )

                metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                    table_name, f"count_{bool_name}_per_{cat_name}"
                )
                metrics.append(
                    SemanticMetric(
                        environment_id=environment_id,
                        data_model_id=data_model_id,
                        data_source_id=data_source_id,
                        name=metric_name,
                        title=metric_title,
                        description=(
                            f"Count of records where {humanized_bool} is true, grouped by {humanized_cat} "
                            f"in the {humanized_table} table"
                        ),
                        table_name=table_name,
                        measures=[bool_measure],
                        dimensions=[dimension],
                        grouped=True,
                    )
                )

        # Relationship-aware (FK) metrics
        for fk in table.get("foreign_keys", []) or []:
            # Expected shape: {"column": "customer_id", "ref_table": "customers", "ref_column": "id"}
            fk_col = fk.get("column")
            ref_table = fk.get("ref_table")
            if not fk_col or not ref_table:
                continue
            if not count_measure:
                continue
            dim_name = MetricsGenerationService._humanize_name(ref_table)
            dimension = SemanticDimension(
                name=dim_name,
                description=f"Relationship to {ref_table}",
                query=fk_col,
                table=table_name,
            )
            metric_name, metric_title = MetricsGenerationService._build_metric_name_and_title(
                table_name, f"count_per_{ref_table}"
            )
            metrics.append(
                SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_name,
                    title=metric_title,
                    description=f"Count of {humanized_table} grouped by related {ref_table}",
                    table_name=table_name,
                    measures=[count_measure],
                    dimensions=[dimension],
                    grouped=True,
                )
            )

        return metrics

    @staticmethod
    def _normalize_set(values: Optional[List[str]]) -> Optional[Set[str]]:
        if values is None:
            return None
        return {v.lower() for v in values}

    @staticmethod
    def generate_metrics(
        environment_id: UUID,
        data_source_id: UUID,
        data_model_id: UUID,
        *,
        include_tables: Optional[List[str]] = None,
        exclude_tables: Optional[List[str]] = None,
        include_columns: Optional[List[str]] = None,
        exclude_columns: Optional[List[str]] = None,
        metric_types: Optional[List[str]] = None,
        time_windows: Optional[List[int]] = None,
        grains: Optional[List[str]] = None,
        tzinfo=timezone.utc,
    ) -> List[SemanticMetric]:
        """
        Generate metric recommendations from a data source schema.
        Supports optional scoping by tables/columns, metric types, time windows, and time grains.
        """
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        if not data_source:
            raise ValueError(f"Data source {data_source_id} not found")

        if data_source.environment_id != environment_id:
            raise ValueError(f"Data source {data_source_id} does not belong to environment {environment_id}")

        model_service = DataModelService()
        try:
            data_model = model_service.get_data_model_by_id(data_model_id)
            if not data_model:
                raise ValueError(f"Data model {data_model_id} not found")
            if data_model.environment_id != environment_id:
                raise ValueError(f"Data model {data_model_id} does not belong to environment {environment_id}")
        finally:
            model_service.close()

        schema_service = DataSourceSchemaService()
        schema_response = schema_service.get_schema(data_source_id)
        schema = schema_response.get("schema", {})
        tables = schema.get("tables", [])

        include_tables_set = MetricsGenerationService._normalize_set(include_tables)
        exclude_tables_set = MetricsGenerationService._normalize_set(exclude_tables)
        include_columns_set = MetricsGenerationService._normalize_set(include_columns)
        exclude_columns_set = MetricsGenerationService._normalize_set(exclude_columns)

        metric_types_set = set(metric_types) if metric_types else MetricsGenerationService.DEFAULT_METRIC_TYPES
        time_windows_list = time_windows or MetricsGenerationService.DEFAULT_TIME_WINDOWS
        grains_list = grains or ["day", "week", "month", "quarter", "year"]

        filtered_tables = MetricsGenerationService._apply_table_filters(
            tables, include_tables_set, exclude_tables_set
        )

        all_metrics: List[SemanticMetric] = []
        seen_names: Set[str] = set()

        for table in filtered_tables:
            classified = MetricsGenerationService._classify_columns(
                table,
                include_columns=include_columns_set,
                exclude_columns=exclude_columns_set,
            )

            single_value_metrics = MetricsGenerationService._generate_single_value_metrics(
                table,
                classified,
                environment_id,
                data_model_id,
                data_source_id,
                metric_types=metric_types_set,
                time_windows=time_windows_list,
                grains=grains_list,
                tzinfo=tzinfo,
            )
            comparison_metrics = MetricsGenerationService._generate_comparison_metrics(
                table,
                classified,
                environment_id,
                data_model_id,
                data_source_id,
                metric_types=metric_types_set,
                grains=grains_list,
            )

            capped = 0
            for metric in single_value_metrics + comparison_metrics:
                if metric.name in seen_names:
                    continue
                if capped >= MetricsGenerationService.MAX_METRICS_PER_TABLE:
                    break
                seen_names.add(metric.name)
                all_metrics.append(metric)
                capped += 1

        return all_metrics
