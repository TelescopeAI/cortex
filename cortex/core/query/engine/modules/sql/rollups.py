from typing import Optional

from cortex.core.query.engine.modules.sql.base_sql import SQLQueryGenerator
from cortex.core.query.engine.bindings.base import QuerySourceBinding


class RollupSQLQueryGenerator(SQLQueryGenerator):
    """Generates the SELECT used to build a rollup (MV/CTAS) from a binding.

    This class relies on the standard SQLQueryGenerator processors and semantics,
    but swaps the metric context using a QuerySourceBinding when present.
    """

    def __init__(self, *args, binding: Optional[QuerySourceBinding] = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.binding = binding

    def _build_from_clause(self) -> str:
        # When building a rollup, we always source from the base table described by the metric
        # The binding is primarily for column alias mapping and engine-aware formatting at serve time.
        return super()._build_from_clause()


