from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple

from pydantic import Field

from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.databases import DataSourceTypes
from cortex.core.semantics.output_formats import FormattingMap
from cortex.core.types.telescope import TSModel


class BaseQueryGenerator(TSModel, ABC):
    metric: SemanticMetric
    source_type: DataSourceTypes = Field(description="Database Source Type (Postgres, MySQL, BigQuery, etc.)")
    generated_query: Optional[str] = Field(None, description="The generated query string")
    formatting_map: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Mapping of semantic object names to their formatting lists")

    @abstractmethod
    def generate_query(self, parameters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None, grouped: Optional[bool] = None) -> str:
        """Generate the complete query based on the metric with optional parameters, limit/offset, and grouping control"""
        pass

    @abstractmethod
    def _build_select_clause(self) -> str:
        """Build the SELECT clause for the query"""
        pass

    @abstractmethod
    def _build_from_clause(self) -> str:
        """Build the FROM clause for the query"""
        pass

    @abstractmethod
    def _build_where_clause(self) -> Optional[str]:
        """Build the WHERE clause for the query if applicable"""
        pass

    @abstractmethod
    def _build_group_by_clause(self, grouped: bool) -> Optional[str]:
        """Build the GROUP BY clause for the query if applicable"""
        pass

    @abstractmethod
    def _build_join_clause(self) -> Optional[str]:
        """Build the JOIN clause for the query if applicable"""
        pass

    @abstractmethod
    def _build_having_clause(self) -> Optional[str]:
        """Build the HAVING clause for the query if applicable"""
        pass

    @abstractmethod
    def _build_order_by_clause(self) -> Optional[str]:
        """Build the ORDER BY clause for the query if applicable"""
        pass
    
    @abstractmethod
    def _build_combine_expression(self, parts: List[Tuple[str, Optional[str]]]) -> str:
        """
        Build database-specific column concatenation expression.
        
        Args:
            parts: List of (column_expression, delimiter_before_column) tuples
                   First tuple has None as delimiter
                   
        Returns:
            SQL expression that concatenates the columns with delimiters
        """
        pass

    @abstractmethod
    def _build_limit_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Optional[str]:
        """Build the LIMIT clause for the query if applicable"""
        pass

    @abstractmethod
    def _substitute_parameters(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Substitute parameters in the query string"""
        pass

    @abstractmethod
    def _apply_database_formatting(self, column_expression: str, object_name: str, formatting_map: FormattingMap) -> str:
        """Apply database-specific formatting to a column expression"""
        pass
