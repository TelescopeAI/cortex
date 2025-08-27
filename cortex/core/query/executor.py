from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from pydantic import Field

from cortex.core.data.modelling.model import DataModel
from cortex.core.query.engine.factory import QueryGeneratorFactory
from cortex.core.query.engine.processors.output_processor import OutputProcessor
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.databases import DataSourceTypes
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.utils.parsesql import convert_sqlalchemy_rows_to_dict
from cortex.core.types.telescope import TSModel
from cortex.core.query.context import MetricContext
from cortex.core.query.history.logger import QueryHistory, QueryCacheMode
from cortex.core.query.db.service import QueryHistoryCRUD


class QueryExecutor(TSModel):
    """
    Enhanced query executor with logging capabilities and metric execution.
    Handles query generation, execution, result processing, and audit logging.
    """
    
    # Use QueryHistory for logging
    query_history: QueryHistory = Field(default_factory=QueryHistory)
    
    def execute_metric(
        self, 
        metric: SemanticMetric,
        data_model: DataModel,
        parameters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
        context_id: Optional[str] = None,
        grouped: Optional[bool] = None
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
        
        # Prepare meta information
        meta = {
            "source_type": source_type.value,
            "limit": limit,
            "offset": offset,
            "grouped": grouped
        }
        
        try:
            # Resolve metric extensions if needed
            resolved_metric = metric
            
            # Process context_id if provided and enhance parameters with consumer properties for $CORTEX_ substitution
            enhanced_parameters = self._enhance_parameters_with_context(parameters, context_id)
            
            # Generate the query
            query_generator = QueryGeneratorFactory.create_generator(resolved_metric, source_type)
            generated_query = query_generator.generate_query(enhanced_parameters, limit, offset, grouped)
            
            # Execute the query (placeholder - would integrate with actual database execution)
            query_results = self._execute_database_query(generated_query, metric.data_source_id)
            
            # Collect all formatting from semantic objects
            all_formats = OutputProcessor.collect_semantic_formatting(
                measures=resolved_metric.measures,
                dimensions=resolved_metric.dimensions,
                filters=resolved_metric.filters
            )
            
            # Flatten all formats into a single list for processing
            flat_formats = []
            for format_list in all_formats.values():
                if format_list:
                    flat_formats.extend(format_list)
            
            # Apply output format transformations if defined
            if flat_formats:
                transformed_results = OutputProcessor.process_output_formats(
                    query_results, 
                    flat_formats
                )
            else:
                transformed_results = query_results
            
            # Calculate execution time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            # Log successful execution (in-memory)
            log_entry = self.query_history.log_success(
                metric_id=metric.id,
                data_model_id=data_model.id,
                query=generated_query,
                duration=duration,
                row_count=len(transformed_results) if transformed_results else 0,
                parameters=parameters,
                context_id=context_id,
                meta=meta,
                cache_mode=QueryCacheMode.UNCACHED
            )
            
            # Persist to database
            try:
                QueryHistoryCRUD.add_query_log(log_entry)
            except Exception as db_error:
                print(f"Failed to persist query log to database: {db_error}")
                # Continue execution even if database logging fails
            
            return {
                "success": True,
                "data": transformed_results,
                "metadata": {
                    "metric_id": str(metric.id),
                    "duration": duration,
                    "row_count": len(transformed_results) if transformed_results else 0,
                    "query": generated_query,
                    "parameters": parameters
                }
            }
            
        except Exception as e:
            # Calculate execution time even for failures
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            # Log failed execution (in-memory)
            log_entry = self.query_history.log_failure(
                metric_id=metric.id,
                data_model_id=data_model.id,
                query=generated_query if 'generated_query' in locals() else "",
                duration=duration,
                error_message=str(e),
                parameters=parameters,
                context_id=context_id,
                meta=meta,
                cache_mode=QueryCacheMode.UNCACHED
            )
            
            # Persist to database
            try:
                QueryHistoryCRUD.add_query_log(log_entry)
            except Exception as db_error:
                print(f"Failed to persist failed query log to database: {db_error}")
                # Continue execution even if database logging fails
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "metric_id": str(metric.id),
                    "duration": duration,
                    "query": generated_query if 'generated_query' in locals() else "",
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
    

    
    def get_query_log(self, limit: Optional[int] = None):
        """
        Get the query execution log.
        
        Args:
            limit: Optional limit on number of entries to return
            
        Returns:
            List of QueryLog objects
        """
        return self.query_history.get_recent(limit)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get aggregated execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        return self.query_history.stats()
    
    def clear_query_log(self) -> None:
        """Clear the query execution log."""
        self.query_history.clear() 