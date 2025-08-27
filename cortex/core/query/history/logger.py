from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

import pytz
from pydantic import Field

from cortex.core.types.telescope import TSModel


class QueryCacheMode(str, Enum):
    """Enum for query cache execution modes"""
    UNCACHED = "UNCACHED"  # Executed directly against source; no cache involved
    CACHE_HIT = "CACHE_HIT"  # Served from cache; no DB execution
    CACHE_MISS_EXECUTED = "CACHE_MISS_EXECUTED"  # Not in cache; executed and written to cache
    CACHE_REFRESHED = "CACHE_REFRESHED"  # Stale entry refreshed by execution


class QueryLog(TSModel):
    """Represents a logged query execution with metadata"""
    
    id: UUID = Field(default_factory=uuid4)
    metric_id: UUID
    data_model_id: UUID
    query: str
    parameters: Optional[Dict[str, Any]] = Field(default=None)
    context_id: Optional[str] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)
    cache_mode: Optional[QueryCacheMode] = Field(default=QueryCacheMode.UNCACHED)
    query_hash: Optional[str] = Field(default=None)
    duration: float  # milliseconds
    row_count: Optional[int] = Field(default=None)
    success: bool
    error_message: Optional[str] = Field(default=None)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))


class QueryHistory(TSModel):
    """Manages query logging and history"""
    
    query_log: List[QueryLog] = Field(default_factory=list)
    
    def log_success(
        self,
        metric_id: UUID,
        data_model_id: UUID,
        query: str,
        duration: float,
        row_count: int,
        parameters: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        cache_mode: Optional[QueryCacheMode] = QueryCacheMode.UNCACHED,
        query_hash: Optional[str] = None
    ) -> QueryLog:
        """Log a successful query execution"""
        log_entry = QueryLog(
            metric_id=metric_id,
            data_model_id=data_model_id,
            query=query,
            parameters=parameters,
            context_id=context_id,
            meta=meta,
            cache_mode=cache_mode,
            query_hash=query_hash,
            duration=duration,
            row_count=row_count,
            success=True
        )
        
        self.query_log.append(log_entry)
        return log_entry
    
    def log_failure(
        self,
        metric_id: UUID,
        data_model_id: UUID,
        query: str,
        duration: float,
        error_message: str,
        parameters: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        cache_mode: Optional[QueryCacheMode] = QueryCacheMode.UNCACHED,
        query_hash: Optional[str] = None
    ) -> QueryLog:
        """Log a failed query execution"""
        log_entry = QueryLog(
            metric_id=metric_id,
            data_model_id=data_model_id,
            query=query,
            parameters=parameters,
            context_id=context_id,
            meta=meta,
            cache_mode=cache_mode,
            query_hash=query_hash,
            duration=duration,
            row_count=0,  # Set to 0 for failures
            success=False,
            error_message=error_message
        )
        
        self.query_log.append(log_entry)
        return log_entry
    
    def get_recent(self, limit: Optional[int] = None) -> List[QueryLog]:
        """Get recent query logs with optional limit"""
        if limit:
            return self.query_log[-limit:]
        return self.query_log
    
    def stats(self) -> Dict[str, Any]:
        """Get aggregated execution statistics"""
        if not self.query_log:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0
            }
        
        total_executions = len(self.query_log)
        successful_executions = sum(1 for entry in self.query_log if entry.success)
        failed_executions = total_executions - successful_executions
        success_rate = (successful_executions / total_executions) * 100
        
        total_duration = sum(entry.duration for entry in self.query_log)
        average_duration = total_duration / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": round(success_rate, 2),
            "average_duration_ms": round(average_duration, 2)
        }
    
    def clear(self) -> None:
        """Clear the query execution log"""
        self.query_log.clear()


__all__ = [
    "QueryCacheMode",
    "QueryLog", 
    "QueryHistory"
]
