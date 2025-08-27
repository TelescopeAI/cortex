from typing import List, Optional, Dict, Any
from uuid import UUID

from cortex.core.query.db.service import QueryHistoryCRUD
from cortex.core.query.history.logger import QueryLog


class QueryHistoryService:
    """Service for querying historical data."""
    
    @staticmethod
    def get_metric_query_history(
        metric_id: UUID,
        limit: Optional[int] = 100,
        include_failed: bool = True
    ) -> List[QueryLog]:
        """
        Get query execution history for a specific metric.
        
        Args:
            metric_id: The metric ID to get history for
            limit: Maximum number of entries to return
            include_failed: Whether to include failed executions
            
        Returns:
            List of QueryLog entries for the metric
        """
        # Build filter parameters
        filters = {
            "metric_id": metric_id,
            "limit": limit
        }
        
        # Optionally filter by success status
        if not include_failed:
            filters["success"] = True
        
        return QueryHistoryCRUD.get_recent_query_logs(**filters)
    
    @staticmethod
    def get_metric_execution_stats(
        metric_id: UUID,
        time_range: Optional[str] = "7d"
    ) -> Dict[str, Any]:
        """
        Get execution statistics for a specific metric.
        
        Args:
            metric_id: The metric ID to get stats for
            time_range: Time range for stats (1h, 24h, 7d, 30d)
            
        Returns:
            Dictionary with execution statistics
        """
        return QueryHistoryCRUD.get_execution_stats(
            metric_id=metric_id,
            time_range=time_range
        )
    
    @staticmethod
    def get_metric_slow_queries(
        metric_id: UUID,
        limit: Optional[int] = 10,
        threshold_ms: Optional[float] = 1000.0
    ) -> List[QueryLog]:
        """
        Get slow query executions for a specific metric.
        
        Args:
            metric_id: The metric ID to get slow queries for
            limit: Maximum number of entries to return
            threshold_ms: Duration threshold in milliseconds
            
        Returns:
            List of slow QueryLog entries for the metric
        """
        # Get all queries for the metric and filter by duration
        all_queries = QueryHistoryCRUD.get_recent_query_logs(
            metric_id=metric_id,
            limit=1000  # Get more to filter by duration
        )
        
        # Filter by duration threshold and sort by duration (slowest first)
        slow_queries = [
            query for query in all_queries 
            if query.duration >= threshold_ms
        ]
        
        # Sort by duration (slowest first) and limit results
        slow_queries.sort(key=lambda x: x.duration, reverse=True)
        return slow_queries[:limit]
    
    @staticmethod
    def get_metric_recent_executions(
        metric_id: UUID,
        limit: Optional[int] = 20
    ) -> List[QueryLog]:
        """
        Get recent successful executions for a specific metric.
        
        Args:
            metric_id: The metric ID to get recent executions for
            limit: Maximum number of entries to return
            
        Returns:
            List of recent successful QueryLog entries
        """
        return QueryHistoryCRUD.get_recent_query_logs(
            metric_id=metric_id,
            limit=limit,
            success=True
        )
