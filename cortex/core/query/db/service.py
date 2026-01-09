from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

import pytz

from cortex.core.storage.store import CortexStorage
from cortex.core.types.telescope import TSModel
from cortex.core.query.history.logger import QueryLog, QueryCacheMode
from cortex.core.query.db.models import QueryHistoryORM


class QueryHistoryCRUD(TSModel):
    
    @staticmethod
    def get_query_log_by_id(query_id: UUID, storage: Optional[CortexStorage] = None) -> Optional[QueryLog]:
        """
        Get query log entry by ID.
        
        Args:
            query_id: Query ID to retrieve
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            QueryLog object or None if not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_query_log = db_session.query(QueryHistoryORM).filter(
                QueryHistoryORM.id == query_id
            ).first()
            if db_query_log is None:
                return None
            
            return QueryLog.model_validate(db_query_log, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_recent_query_logs(
        limit: Optional[int] = None,
        metric_id: Optional[UUID] = None,
        data_model_id: Optional[UUID] = None,
        success: Optional[bool] = None,
        cache_mode: Optional[QueryCacheMode] = None,
        executed_after: Optional[datetime] = None,
        executed_before: Optional[datetime] = None,
        storage: Optional[CortexStorage] = None
    ) -> List[QueryLog]:
        """
        Get recent query logs with optional filtering.
        
        Args:
            limit: Maximum number of results to return
            metric_id: Filter by metric ID
            data_model_id: Filter by data model ID
            success: Filter by success status
            cache_mode: Filter by cache mode
            executed_after: Filter by execution time (after)
            executed_before: Filter by execution time (before)
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of QueryLog objects
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            query = db_session.query(QueryHistoryORM)
            
            # Apply filters
            if metric_id:
                query = query.filter(QueryHistoryORM.metric_id == metric_id)
            if data_model_id:
                query = query.filter(QueryHistoryORM.data_model_id == data_model_id)
            if success is not None:
                query = query.filter(QueryHistoryORM.success == success)
            if cache_mode:
                query = query.filter(QueryHistoryORM.cache_mode == cache_mode.value)
            if executed_after:
                query = query.filter(QueryHistoryORM.executed_at >= executed_after)
            if executed_before:
                query = query.filter(QueryHistoryORM.executed_at <= executed_before)
            
            # Order by execution time (newest first)
            query = query.order_by(QueryHistoryORM.executed_at.desc())
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            db_query_logs = query.all()
            
            query_logs = []
            for db_query_log in db_query_logs:
                query_logs.append(QueryLog.model_validate(db_query_log, from_attributes=True))
            
            return query_logs
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def add_query_log(query_log: QueryLog, storage: Optional[CortexStorage] = None) -> QueryLog:
        """
        Create a new query log entry.
        
        Args:
            query_log: QueryLog object to create
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Created QueryLog object
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_query_log = QueryHistoryORM(
                id=query_log.id,
                metric_id=query_log.metric_id,
                data_model_id=query_log.data_model_id,
                query=query_log.query,
                parameters=query_log.parameters,
                context_id=query_log.context_id,
                meta=query_log.meta,
                cache_mode=query_log.cache_mode.value if query_log.cache_mode else None,
                query_hash=query_log.query_hash,
                duration=query_log.duration,
                row_count=query_log.row_count,
                success=query_log.success,
                error_message=query_log.error_message,
                executed_at=query_log.executed_at
            )
            
            db_session.add(db_query_log)
            db_session.commit()
            db_session.refresh(db_query_log)
            
            return QueryLog.model_validate(db_query_log, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_execution_stats(
        metric_id: Optional[UUID] = None,
        data_model_id: Optional[UUID] = None,
        time_range: Optional[str] = None,
        storage: Optional[CortexStorage] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated execution statistics.
        
        Args:
            metric_id: Filter by metric ID
            data_model_id: Filter by data model ID
            time_range: Time range for filtering (1h, 24h, 7d, 30d)
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Dictionary of execution statistics
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            query = db_session.query(QueryHistoryORM)
            
            # Apply filters
            if metric_id:
                query = query.filter(QueryHistoryORM.metric_id == metric_id)
            if data_model_id:
                query = query.filter(QueryHistoryORM.data_model_id == data_model_id)
            
            # Apply time range filter
            if time_range:
                now = datetime.now(pytz.UTC)
                if time_range == "1h":
                    start_time = now.replace(minute=0, second=0, microsecond=0)
                elif time_range == "24h":
                    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif time_range == "7d":
                    start_time = now.replace(day=now.day - 7, hour=0, minute=0, second=0, microsecond=0)
                elif time_range == "30d":
                    start_time = now.replace(day=now.day - 30, hour=0, minute=0, second=0, microsecond=0)
                else:
                    start_time = None
                
                if start_time:
                    query = query.filter(QueryHistoryORM.executed_at >= start_time)
            
            db_query_logs = query.all()
            
            if not db_query_logs:
                return {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "success_rate": 0.0,
                    "average_duration_ms": 0.0,
                    "cache_hit_rate": 0.0
                }
            
            total_executions = len(db_query_logs)
            successful_executions = sum(1 for entry in db_query_logs if entry.success)
            failed_executions = total_executions - successful_executions
            success_rate = (successful_executions / total_executions) * 100
            
            total_duration = sum(entry.duration for entry in db_query_logs)
            average_duration = total_duration / total_executions
            
            # Calculate cache hit rate
            cache_hits = sum(1 for entry in db_query_logs if entry.cache_mode == QueryCacheMode.CACHE_HIT.value)
            cache_hit_rate = (cache_hits / total_executions) * 100 if total_executions > 0 else 0.0
            
            return {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": round(success_rate, 2),
                "average_duration_ms": round(average_duration, 2),
                "cache_hit_rate": round(cache_hit_rate, 2)
            }
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_slow_queries(
        limit: Optional[int] = 10,
        time_range: Optional[str] = None,
        threshold_ms: Optional[float] = 1000.0,
        storage: Optional[CortexStorage] = None
    ) -> List[QueryLog]:
        """
        Get slowest queries for performance analysis.
        
        Args:
            limit: Maximum number of results to return
            time_range: Time range for filtering (1h, 24h, 7d, 30d)
            threshold_ms: Minimum duration in milliseconds
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of slow QueryLog objects
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            query = db_session.query(QueryHistoryORM).filter(
                QueryHistoryORM.duration >= threshold_ms
            )
            
            # Apply time range filter
            if time_range:
                now = datetime.now(pytz.UTC)
                if time_range == "1h":
                    start_time = now.replace(minute=0, second=0, microsecond=0)
                elif time_range == "24h":
                    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif time_range == "7d":
                    start_time = now.replace(day=now.day - 7, hour=0, minute=0, second=0, microsecond=0)
                elif time_range == "30d":
                    start_time = now.replace(day=now.day - 30, hour=0, minute=0, second=0, microsecond=0)
                else:
                    start_time = None
                
                if start_time:
                    query = query.filter(QueryHistoryORM.executed_at >= start_time)
            
            # Order by duration (slowest first)
            query = query.order_by(QueryHistoryORM.duration.desc())
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            db_query_logs = query.all()
            
            slow_queries = []
            for db_query_log in db_query_logs:
                slow_queries.append(QueryLog.model_validate(db_query_log, from_attributes=True))
            
            return slow_queries
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def clear_query_history(older_than: Optional[datetime] = None, storage: Optional[CortexStorage] = None) -> int:
        """
        Clear query history with optional time-based filtering.
        
        Args:
            older_than: Delete only entries older than this datetime
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Number of entries deleted
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            query = db_session.query(QueryHistoryORM)
            
            if older_than:
                query = query.filter(QueryHistoryORM.executed_at < older_than)
            
            # Count entries to be deleted
            count = query.count()
            
            # Delete entries
            query.delete()
            db_session.commit()
            
            return count
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()
