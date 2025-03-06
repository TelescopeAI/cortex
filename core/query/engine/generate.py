from core.query.engine.factory import QueryGeneratorFactory
from core.semantics.measures import SemanticMeasure
from core.semantics.metrics.metric import SemanticMetric
from core.stores.connection import LocalSession
from core.types.databases import DataSourceTypes
from core.types.telescope import TSModel
import time


class QueryGenerator(TSModel):
    metric: SemanticMetric
    source_type: DataSourceTypes

    def generate_query(self) -> str:
        """
        Generate a database query for the given metric.

        Args:
            metric: The semantic metric to generate a query for
            source_type: The database source implementation that should be used to generate the query

        Returns:
            The generated query string (or query object for NoSQL)
        """
        generator = QueryGeneratorFactory.create_generator(self.metric, self.source_type)
        return generator.generate_query()


if __name__ == "__main__":
    measure_1 = SemanticMeasure(name="Workspaces Count", description="measure_1", type="count",
                                alias="workspace-count", query="id",
                                table="workspaces", primary_key="thread_id")

    metric_1 = SemanticMetric(name="Workspaces", description="Description for Workspaces",
                              measures=[measure_1], dimensions=[], table="workspaces")

    # Generate PostgreSQL query with timing
    start_time = time.time()
    query_gen = QueryGenerator(metric=metric_1, source_type=DataSourceTypes.POSTGRESQL)
    postgres_query = query_gen.generate_query()
    end_time = time.time()
    execution_time = end_time - start_time
    # local_session = LocalSession().get_session()
    # query_results = local_session.query(postgres_query)

    print(f"PostgreSQL Query: {postgres_query}")
    # print(f"Query Results: {query_results}")
    print(f"Execution time: {execution_time:.6f} seconds")
