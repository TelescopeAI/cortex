"""
Metric execution service for shared metric execution logic.
"""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.conditions import Condition, WhenClause, ComparisonOperator
from cortex.core.types.semantics.column_field import ColumnField
from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.types.semantics.filter import FilterOperator, FilterType, FilterValueType
from cortex.core.data.modelling.model import DataModel
from cortex.core.query.executor import QueryExecutor
from cortex.core.types.databases import DataSourceTypes
from cortex.core.semantics.metrics.modifiers import MetricModifiers
from cortex.core.services.data_sources import DataSourceSchemaService
from cortex.core.data.modelling.validation_service import ValidationService


class MetricExecutionService:
    """Service for executing metrics with proper data model resolution."""
    
    @staticmethod
    def execute_metric(
        metric_id: Optional[UUID] = None,
        metric: Optional[SemanticMetric] = None,
        context_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
        grouped: Optional[bool] = None,
        cache_preference: Optional[CachePreference] = None,
        modifiers: Optional[MetricModifiers] = None,
        preview: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        Execute a metric and return the result.
        
        Args:
            metric_id: UUID of the metric to execute (mutually exclusive with metric)
            metric: SemanticMetric object to execute directly (mutually exclusive with metric_id)
            context_id: Optional context ID for execution
            parameters: Optional parameters for metric execution
            limit: Optional limit for result rows
            offset: Optional offset for result pagination
            source_type: Data source type (defaults to PostgreSQL)
            grouped: Optional override for grouping
            cache_preference: Optional cache preferences
            modifiers: Optional metric modifiers
            preview: If True, generate query without executing or saving to DB
            
        Returns:
            Dict containing execution result with success, data, metadata, and errors
            
        Raises:
            ValueError: If neither metric_id nor metric provided, or both provided,
                       or if metric/data model not found
            Exception: For execution errors
        """
        # Validate that exactly one of metric_id or metric is provided
        if metric_id is not None and metric is not None:
            raise ValueError("Cannot provide both metric_id and metric; provide exactly one")
        if metric_id is None and metric is None:
            raise ValueError("Must provide either metric_id or metric")
        
        metric_service = MetricService()
        model_service = DataModelService()
        
        try:
            # Get or use provided metric
            if metric is not None:
                # Use the provided metric directly
                resolved_metric = metric
                effective_metric_id = metric.id
            else:
                # Fetch metric from database
                db_metric = metric_service.get_metric_by_id(metric_id)
                if db_metric:
                    resolved_metric = SemanticMetric.model_validate(db_metric)
                    effective_metric_id = metric_id
                else:
                    raise ValueError(f"Metric with ID {metric_id} not found")
            
            # Get data model for the metric
            data_model = model_service.get_data_model_by_id(resolved_metric.data_model_id)
            if not data_model:
                raise ValueError(f"Data model with ID {resolved_metric.data_model_id} not found")
            
            # Convert ORM to Pydantic using automatic conversion
            data_model = DataModel.model_validate(data_model)
            
            # Infer source_type from data_source_id if available
            effective_source_type = source_type
            if resolved_metric.data_source_id:
                try:
                    data_source = DataSourceCRUD.get_data_source(resolved_metric.data_source_id)
                    # Convert to DataSourceTypes enum (handles both string and enum values)
                    effective_source_type = DataSourceTypes(data_source.source_type)
                except Exception as e:
                    # If data source lookup fails, fall back to provided source_type
                    # Log the error but don't fail the execution
                    logging.warning(f"Failed to fetch data source {resolved_metric.data_source_id}: {e}. Using provided source_type: {source_type}")
            
            # Validate metric before execution
            validation_result = ValidationService.validate_metric_execution(resolved_metric, data_model)
            
            # If validation fails, return early with validation errors
            if not validation_result.is_valid:
                return {
                    "success": False,
                    "data": None,
                    "metadata": {"metric_id": str(effective_metric_id)},
                    "error": "Metric validation failed",
                    "validation_errors": validation_result.errors,
                    "validation_warnings": validation_result.warnings,
                }
            
            # Execute the metric using QueryExecutor
            executor = QueryExecutor()
            
            # Execute the metric with the new architecture
            result = executor.execute_metric(
                metric=resolved_metric,
                data_model=data_model,
                parameters=parameters or {},
                limit=limit,
                offset=offset,
                source_type=effective_source_type,
                context_id=context_id,
                grouped=grouped,
                cache_preference=cache_preference,
                modifiers=modifiers,
                preview=preview,
            )
            
            return result
            
        finally:
            metric_service.close()
            model_service.close()
    
    @staticmethod
    def get_metric_details(metric_id: UUID) -> Dict[str, Any]:
        """
        Get metric details including data model information.
        
        Args:
            metric_id: UUID of the metric
            
        Returns:
            Dict containing metric and data model details
            
        Raises:
            ValueError: If metric or data model not found
        """
        metric_service = MetricService()
        model_service = DataModelService()
        
        try:
            # Get metric
            db_metric = metric_service.get_metric_by_id(metric_id)
            if not db_metric:
                raise ValueError(f"Metric with ID {metric_id} not found")
            
            # Convert ORM to Pydantic
            metric = SemanticMetric.model_validate(db_metric)
            
            # Get data model
            data_model = model_service.get_data_model_by_id(metric.data_model_id)
            if not data_model:
                raise ValueError(f"Data model with ID {metric.data_model_id} not found")
            
            # Convert ORM to Pydantic
            pydantic_model = DataModel.model_validate(data_model)
            
            return {
                "metric": metric,
                "data_model": pydantic_model
            }
            
        finally:
            metric_service.close()
            model_service.close()


class MetricsGenerationService:
    """Service for generating metric recommendations from database schemas."""
    
    # Column type classification constants
    NUMERIC_TYPES = {"REAL", "INTEGER", "NUMERIC", "DECIMAL", "FLOAT", "DOUBLE"}
    BOOLEAN_TYPES = {"BOOLEAN", "BOOL"}
    
    # Name pattern constants
    CATEGORICAL_KEYWORDS = [
        "type", "segment", "region", "country", "category",
        "status", "rating", "sector", "name", "channel"
    ]
    
    TECHNICAL_SUFFIXES = [
        "_usd", "_id", "_date", "_amount", "_count",
        "_number", "_percentage", "_year", "_month"
    ]
    
    @staticmethod
    def _humanize_name(name: str) -> str:
        """
        Transform a database column/table name into a human-readable title.
        
        Examples:
            total_revenue_usd -> Total Revenue
            client_id -> Client
            is_key_client -> Is Key Client
        """
        # Remove technical suffixes
        humanized = name
        for suffix in MetricsGenerationService.TECHNICAL_SUFFIXES:
            if humanized.lower().endswith(suffix):
                humanized = humanized[:-len(suffix)]
                break
        
        # Split by underscores and capitalize each word
        words = humanized.split("_")
        return " ".join(word.capitalize() for word in words)
    
    @staticmethod
    def _is_numeric_column(column_type: str) -> bool:
        """Check if column type is numeric."""
        return column_type.upper() in MetricsGenerationService.NUMERIC_TYPES
    
    @staticmethod
    def _is_boolean_column(column_type: str) -> bool:
        """Check if column type is boolean."""
        return column_type.upper() in MetricsGenerationService.BOOLEAN_TYPES
    
    @staticmethod
    def _is_id_column(column_name: str) -> bool:
        """Check if column name indicates it's an ID column."""
        return column_name.lower().endswith("_id")
    
    @staticmethod
    def _is_date_column(column_name: str) -> bool:
        """Check if column name indicates it's a date column."""
        lower_name = column_name.lower()
        return "date" in lower_name or "year" in lower_name or "month" in lower_name
    
    @staticmethod
    def _is_categorical_column(column_type: str, column_name: str) -> bool:
        """Check if column is a categorical dimension."""
        if column_type.upper() != "VARCHAR":
            return False
        
        lower_name = column_name.lower()
        return any(keyword in lower_name for keyword in MetricsGenerationService.CATEGORICAL_KEYWORDS)
    
    @staticmethod
    def _classify_columns(table: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Classify columns in a table into different categories.
        
        Returns:
            Dict with keys: numeric, boolean, id, date, categorical
        """
        classified = {
            "numeric": [],
            "boolean": [],
            "id": [],
            "date": [],
            "categorical": []
        }
        
        for column in table.get("columns", []):
            col_name = column.get("name")
            col_type = column.get("type")
            
            if not col_name or not col_type:
                continue
            
            # Classify column
            if MetricsGenerationService._is_numeric_column(col_type):
                classified["numeric"].append(column)
            elif MetricsGenerationService._is_boolean_column(col_type):
                classified["boolean"].append(column)
            
            # Check dimension types (column can be multiple types)
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
        humanized_measure_name: Optional[str] = None
    ) -> SemanticMeasure:
        """
        Create a measure for a boolean column using native Condition objects.
        
        Instead of raw SQL like: SUM(CASE WHEN col = TRUE THEN 1 ELSE 0 END)
        Use conditional measure with Condition object.
        """
        # Create condition for boolean check
        condition = Condition(
            when_clauses=[
                WhenClause(
                    field=ColumnField(column=column_name, table=table_name),
                    operator=ComparisonOperator.EQUALS,
                    compare_values=True,
                    then_return=1
                )
            ],
            else_return=0
        )
        
        # Use humanized measure name if provided, otherwise generate default
        measure_name = humanized_measure_name or MetricsGenerationService._humanize_name(f"count_{column_name}")
        
        return SemanticMeasure(
            name=measure_name,
            description=f"Count of {humanized_name}",
            type=SemanticMeasureType.SUM,
            conditional=True,
            conditions=condition,
            table=table_name
        )
    
    @staticmethod
    def _create_time_filter(
        date_column: str,
        table_name: str,
        days: int = 30
    ) -> SemanticFilter:
        """
        Create a time-based filter using SemanticFilter with BETWEEN operator.
        
        Filter for last N days using native filter objects with calculated date values.
        """
        # Calculate current date and past date
        current_date = datetime.now().date()
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
            is_active=True
        )
    
    @staticmethod
    def _generate_single_value_metrics(
        table: Dict[str, Any],
        classified_columns: Dict[str, List[Dict[str, Any]]],
        environment_id: UUID,
        data_model_id: UUID,
        data_source_id: UUID
    ) -> List[SemanticMetric]:
        """Generate single value metrics for a table."""
        metrics = []
        table_name = table.get("name")
        humanized_table = MetricsGenerationService._humanize_name(table_name)
        
        # 1. Count metric
        # Find primary ID column or use first available column (avoid '*' which causes issues)
        id_columns = classified_columns.get("id", [])
        count_column = id_columns[0]["name"] if id_columns else None
        
        # If no ID column, use the first column from any category
        if not count_column:
            all_columns = table.get("columns", [])
            if all_columns:
                count_column = all_columns[0].get("name")
        
        # Only create count metric if we have a valid column
        if count_column:
            humanized_count = MetricsGenerationService._humanize_name("count")
            count_measure = SemanticMeasure(
                name=humanized_count,
                description=f"Count of {humanized_table}",
                type=SemanticMeasureType.COUNT,
                query=count_column,
                table=table_name
            )
            
            metric_title = f"Count of {humanized_table}"
            metrics.append(SemanticMetric(
                environment_id=environment_id,
                data_model_id=data_model_id,
                data_source_id=data_source_id,
                name=metric_title,
                title=metric_title,
                description=f"Total number of records in the {humanized_table} table",
                table_name=table_name,
                measures=[count_measure],
                grouped=False
            ))
        
        # 2. Sum metrics for numeric columns
        for num_col in classified_columns.get("numeric", []):
            col_name = num_col["name"]
            humanized_col = MetricsGenerationService._humanize_name(col_name)
            humanized_measure_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
            
            sum_measure = SemanticMeasure(
                name=humanized_measure_name,
                description=f"Total {humanized_col}",
                type=SemanticMeasureType.SUM,
                query=col_name,
                table=table_name
            )
            
            metric_title = f"Total {humanized_col}"
            metrics.append(SemanticMetric(
                environment_id=environment_id,
                data_model_id=data_model_id,
                data_source_id=data_source_id,
                name=metric_title,
                title=metric_title,
                description=f"Sum of all {humanized_col} values from the {humanized_table} table",
                table_name=table_name,
                measures=[sum_measure],
                grouped=False
            ))
        
        # 3. Boolean count metrics
        for bool_col in classified_columns.get("boolean", []):
            col_name = bool_col["name"]
            humanized_col = MetricsGenerationService._humanize_name(col_name)
            humanized_bool_measure_name = MetricsGenerationService._humanize_name(f"count_{col_name}")
            
            bool_measure = MetricsGenerationService._create_boolean_measure(
                col_name, table_name, humanized_col, humanized_bool_measure_name
            )
            
            metric_title = f"Count of {humanized_col}"
            metrics.append(SemanticMetric(
                environment_id=environment_id,
                data_model_id=data_model_id,
                data_source_id=data_source_id,
                name=metric_title,
                title=metric_title,
                description=f"Count of records where {humanized_col} is true in the {humanized_table} table",
                table_name=table_name,
                measures=[bool_measure],
                grouped=False
            ))
        
        # 4. Last 30 days metrics (if date columns exist)
        date_columns = classified_columns.get("date", [])
        if date_columns:
            primary_date_col = date_columns[0]["name"]
            humanized_date_col = MetricsGenerationService._humanize_name(primary_date_col)
            time_filter = MetricsGenerationService._create_time_filter(
                primary_date_col, table_name, 30
            )
            
            # Count in last 30 days
            metric_title = f"Count of {humanized_table} in Last 30 Days"
            metrics.append(SemanticMetric(
                environment_id=environment_id,
                data_model_id=data_model_id,
                data_source_id=data_source_id,
                name=metric_title,
                title=metric_title,
                description=f"Total number of {humanized_table} records from the last 30 days based on {humanized_date_col}",
                table_name=table_name,
                measures=[count_measure],
                filters=[time_filter],
                grouped=False
            ))
            
            # Sum in last 30 days for each numeric column
            for num_col in classified_columns.get("numeric", []):
                col_name = num_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                humanized_measure_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
                
                sum_measure = SemanticMeasure(
                    name=humanized_measure_name,
                    description=f"Total {humanized_col}",
                    type=SemanticMeasureType.SUM,
                    query=col_name,
                    table=table_name
                )
                
                metric_title = f"Total {humanized_col} in Last 30 Days"
                metrics.append(SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_title,
                    title=metric_title,
                    description=f"Sum of {humanized_col} from the last 30 days in the {humanized_table} table based on {humanized_date_col}",
                    table_name=table_name,
                    measures=[sum_measure],
                    filters=[time_filter],
                    grouped=False
                ))
        
        return metrics
    
    @staticmethod
    def _generate_comparison_metrics(
        table: Dict[str, Any],
        classified_columns: Dict[str, List[Dict[str, Any]]],
        environment_id: UUID,
        data_model_id: UUID,
        data_source_id: UUID
    ) -> List[SemanticMetric]:
        """Generate comparison metrics for a table."""
        metrics = []
        table_name = table.get("name")
        humanized_table = MetricsGenerationService._humanize_name(table_name)
        
        # Find primary ID column for count measure or use first available column (avoid '*' which causes issues)
        id_columns = classified_columns.get("id", [])
        count_column = id_columns[0]["name"] if id_columns else None
        
        # If no ID column, use the first column from any category
        if not count_column:
            all_columns = table.get("columns", [])
            if all_columns:
                count_column = all_columns[0].get("name")
        
        # Only generate count-based comparison metrics if we have a valid column
        if count_column:
            humanized_count = MetricsGenerationService._humanize_name("count")
            count_measure = SemanticMeasure(
                name=humanized_count,
                description=f"Count of {humanized_table}",
                type=SemanticMeasureType.COUNT,
                query=count_column,
                table=table_name
            )
            
            # 1. Count by date columns
            for date_col in classified_columns.get("date", []):
                col_name = date_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                
                dimension = SemanticDimension(
                    name=humanized_col,
                    description=humanized_col,
                    query=col_name,
                    table=table_name
                )
                
                metric_title = f"Count of {humanized_table} by {humanized_col}"
                metrics.append(SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_title,
                    title=metric_title,
                    description=f"Number of {humanized_table} records grouped by {humanized_col}",
                    table_name=table_name,
                    measures=[count_measure],
                    dimensions=[dimension],
                    grouped=True
                ))
            
            # 2. Count by ID and categorical dimensions
            dimension_columns = classified_columns.get("id", []) + classified_columns.get("categorical", [])
            for dim_col in dimension_columns:
                col_name = dim_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                
                dimension = SemanticDimension(
                    name=humanized_col,
                    description=humanized_col,
                    query=col_name,
                    table=table_name
                )
                
                metric_title = f"Count of {humanized_table} per {humanized_col}"
                metrics.append(SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_title,
                    title=metric_title,
                    description=f"Distribution of {humanized_table} records across different {humanized_col} values",
                    table_name=table_name,
                    measures=[count_measure],
                    dimensions=[dimension],
                    grouped=True
                ))
        
        # 3. Numeric measures by primary date dimension
        date_columns = classified_columns.get("date", [])
        if date_columns:
            primary_date_col = date_columns[0]["name"]
            humanized_date = MetricsGenerationService._humanize_name(primary_date_col)
            
            date_dimension = SemanticDimension(
                name=humanized_date,
                description=humanized_date,
                query=primary_date_col,
                table=table_name
            )
            
            for num_col in classified_columns.get("numeric", []):
                col_name = num_col["name"]
                humanized_col = MetricsGenerationService._humanize_name(col_name)
                humanized_measure_name = MetricsGenerationService._humanize_name(f"total_{col_name}")
                
                sum_measure = SemanticMeasure(
                    name=humanized_measure_name,
                    description=f"Total {humanized_col}",
                    type=SemanticMeasureType.SUM,
                    query=col_name,
                    table=table_name
                )
                
                metric_title = f"Total {humanized_col} by {humanized_date}"
                metrics.append(SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_title,
                    title=metric_title,
                    description=f"Sum of {humanized_col} grouped by {humanized_date} from the {humanized_table} table",
                    table_name=table_name,
                    measures=[sum_measure],
                    dimensions=[date_dimension],
                    grouped=True
                ))
        
        # 4. Boolean metrics by categorical dimension
        categorical_columns = classified_columns.get("categorical", [])
        for bool_col in classified_columns.get("boolean", []):
            bool_name = bool_col["name"]
            humanized_bool = MetricsGenerationService._humanize_name(bool_name)
            humanized_bool_measure_name = MetricsGenerationService._humanize_name(f"count_{bool_name}")
            
            bool_measure = MetricsGenerationService._create_boolean_measure(
                bool_name, table_name, humanized_bool, humanized_bool_measure_name
            )
            
            for cat_col in categorical_columns:
                cat_name = cat_col["name"]
                humanized_cat = MetricsGenerationService._humanize_name(cat_name)
                
                dimension = SemanticDimension(
                    name=humanized_cat,
                    description=humanized_cat,
                    query=cat_name,
                    table=table_name
                )
                
                metric_title = f"Count of {humanized_bool} per {humanized_cat}"
                metrics.append(SemanticMetric(
                    environment_id=environment_id,
                    data_model_id=data_model_id,
                    data_source_id=data_source_id,
                    name=metric_title,
                    title=metric_title,
                    description=f"Count of records where {humanized_bool} is true, grouped by {humanized_cat} in the {humanized_table} table",
                    table_name=table_name,
                    measures=[bool_measure],
                    dimensions=[dimension],
                    grouped=True
                ))
        
        return metrics
    
    @staticmethod
    def generate_metrics(
        environment_id: UUID,
        data_source_id: UUID,
        data_model_id: UUID
    ) -> List[SemanticMetric]:
        """
        Generate metric recommendations from a data source schema.
        
        Args:
            environment_id: Environment ID for scoping
            data_source_id: Data source to analyze
            data_model_id: Data model to associate metrics with
            
        Returns:
            List of generated SemanticMetric instances
            
        Raises:
            ValueError: If data_source or data_model don't belong to environment
        """
        # Validate data source belongs to environment
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        if not data_source:
            raise ValueError(f"Data source {data_source_id} not found")
        
        if data_source.environment_id != environment_id:
            raise ValueError(
                f"Data source {data_source_id} does not belong to environment {environment_id}"
            )
        
        # Validate data model belongs to environment
        model_service = DataModelService()
        try:
            data_model = model_service.get_data_model_by_id(data_model_id)
            if not data_model:
                raise ValueError(f"Data model {data_model_id} not found")
            
            if data_model.environment_id != environment_id:
                raise ValueError(
                    f"Data model {data_model_id} does not belong to environment {environment_id}"
                )
        finally:
            model_service.close()
        
        # Fetch schema
        schema_service = DataSourceSchemaService()
        schema_response = schema_service.get_schema(data_source_id)
        schema = schema_response.get("schema", {})
        tables = schema.get("tables", [])
        
        # Generate metrics for each table
        all_metrics = []
        for table in tables:
            # Classify columns
            classified = MetricsGenerationService._classify_columns(table)
            
            # Generate single value metrics
            single_value_metrics = MetricsGenerationService._generate_single_value_metrics(
                table, classified, environment_id, data_model_id, data_source_id
            )
            all_metrics.extend(single_value_metrics)
            
            # Generate comparison metrics
            comparison_metrics = MetricsGenerationService._generate_comparison_metrics(
                table, classified, environment_id, data_model_id, data_source_id
            )
            all_metrics.extend(comparison_metrics)
        
        return all_metrics
