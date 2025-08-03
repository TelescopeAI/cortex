from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4

import pytz
from pydantic import Field

from cortex.core.data.modelling.model import DataModel
from cortex.core.data.modelling.metric_service import MetricService
from cortex.core.query.engine.factory import QueryGeneratorFactory
from cortex.core.query.engine.processors.output_processor import OutputProcessor
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.databases import DataSourceTypes
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.utils.parsesql import convert_sqlalchemy_rows_to_dict
from cortex.core.types.telescope import TSModel
from cortex.core.query.context import MetricContext


class QueryLogEntry(TSModel):
    """
    Represents a logged query execution with metadata.
    """
    id: UUID = Field(default_factory=uuid4)
    metric_alias: str
    metric_id: UUID
    data_model_id: UUID
    query: str
    parameters: Optional[Dict[str, Any]] = None
    
    # Execution metadata
    execution_time_ms: float
    row_count: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    
    # Timestamps
    executed_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))


class QueryExecutor(TSModel):
    """
    Enhanced query executor with logging capabilities and metric execution.
    Handles query generation, execution, result processing, and audit logging.
    """
    
    # Define query_log as a model field
    query_log: List[QueryLogEntry] = Field(default_factory=list)
    
    def execute_metric(
        self, 
        metric: SemanticMetric,
        data_model: DataModel,
        parameters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
        context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific metric from a data model with comprehensive logging.
        
        Args:
            metric: SemanticMetric to execute
            data_model: DataModel containing the metric
            parameters: Optional runtime parameters
            source_type: Database source type for query generation
            
        Returns:
            Dict containing query results and execution metadata
        """
        start_time = datetime.now()
        log_entry = QueryLogEntry(
            metric_alias=metric.alias or metric.name,
            metric_id=metric.id,
            data_model_id=data_model.id,
            query="",  # Will be updated
            parameters=parameters,
            execution_time_ms=0.0,
            success=False
        )
        
        try:
            # Resolve metric extensions if needed
            resolved_metric = metric
            
            # Process context_id if provided and enhance parameters with consumer properties for $CORTEX_ substitution
            enhanced_parameters = self._enhance_parameters_with_context(parameters, context_id)
            
            # Generate the query
            query_generator = QueryGeneratorFactory.create_generator(resolved_metric, source_type)
            generated_query = query_generator.generate_query(enhanced_parameters, limit, offset)
            log_entry.query = generated_query
            
            # Execute the query (placeholder - would integrate with actual database execution)
            query_results = self._execute_database_query(generated_query, metric.data_source_id)
            
            # Apply output format transformations if defined
            if resolved_metric.output_formats:
                transformed_results = OutputProcessor.process_output_formats(
                    query_results, 
                    resolved_metric.output_formats
                )
            else:
                transformed_results = query_results
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update log entry with success
            log_entry.execution_time_ms = execution_time_ms
            log_entry.row_count = len(transformed_results) if transformed_results else 0
            log_entry.success = True
            
            # Add to query log
            self.query_log.append(log_entry)
            
            return {
                "success": True,
                "data": transformed_results,
                "metadata": {
                    "metric_alias": metric.alias or metric.name,
                    "metric_id": str(metric.id),
                    "execution_time_ms": execution_time_ms,
                    "row_count": log_entry.row_count,
                    "query": generated_query,
                    "parameters": parameters
                }
            }
            
        except Exception as e:
            # Calculate execution time even for failures
            end_time = datetime.now()
            execution_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Update log entry with failure
            log_entry.execution_time_ms = execution_time_ms
            log_entry.error_message = str(e)
            
            # Add to query log
            self.query_log.append(log_entry)
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "metric_alias": metric.alias or metric.name,
                    "metric_id": str(metric.id),
                    "execution_time_ms": execution_time_ms,
                    "query": log_entry.query,
                    "parameters": parameters
                }
            }
    
    def _execute_database_query(self, query: str, data_source_id: UUID) -> List[Dict[str, Any]]:
        """
        Execute the actual database query using the specified data source.

        Args:
            query: SQL query to execute.
            data_source_id: The ID of the data source to use for the query.

        Returns:
            A list of dictionaries representing the query results.
        """
        # 1. Fetch the data source details
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        # 2. Get the appropriate database client
        client = DBClientService.get_client(
            details=data_source.config,
            db_type=data_source.source_type
        )

        # 3. Connect, execute the query, and fetch results
        client.connect()
        results = client.query(query)

        # 4. Convert results to a list of dictionaries
        return convert_sqlalchemy_rows_to_dict(results)
    
    def _enhance_parameters_with_context(self, parameters: Optional[Dict[str, Any]], context_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Enhance parameters with context-based values from consumer properties.
        
        Args:
            parameters: Original parameters dictionary
            context_id: Context identifier in format <TYPE>_<UNIQUEID> or <TYPE>_<ID1>_<ID2>
            
        Returns:
            Enhanced parameters dictionary with context values substituted
        """
        if not context_id:
            return parameters
        
        try:
            # Parse the context_id
            context = MetricContext.parse(context_id)
            
            # Get consumer properties from context
            consumer_properties = context.get_consumer_properties()
            
            if not consumer_properties:
                return parameters
            
            # Create enhanced parameters by merging original parameters with consumer properties
            enhanced_parameters = parameters.copy() if parameters else {}
            
            # Merge consumer properties into enhanced parameters for $CORTEX_ substitution
            enhanced_parameters.update(consumer_properties)
            
            return enhanced_parameters
            
        except Exception as e:
            print(f"Error enhancing parameters with context {context_id}: {e}")
            return parameters
    

    
    def get_query_log(self, limit: Optional[int] = None) -> List[QueryLogEntry]:
        """
        Get the query execution log.
        
        Args:
            limit: Optional limit on number of entries to return
            
        Returns:
            List of QueryLogEntry objects
        """
        if limit:
            return self.query_log[-limit:]
        return self.query_log
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get aggregated execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        if not self.query_log:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0.0,
                "average_execution_time_ms": 0.0
            }
        
        total_executions = len(self.query_log)
        successful_executions = sum(1 for entry in self.query_log if entry.success)
        failed_executions = total_executions - successful_executions
        success_rate = (successful_executions / total_executions) * 100
        
        total_execution_time = sum(entry.execution_time_ms for entry in self.query_log)
        average_execution_time = total_execution_time / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": round(success_rate, 2),
            "average_execution_time_ms": round(average_execution_time, 2)
        }
    
    def clear_query_log(self) -> None:
        """Clear the query execution log."""
        self.query_log.clear() 