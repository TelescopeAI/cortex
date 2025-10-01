from typing import Dict, Optional, Protocol

from cortex.core.types.time import TimeGrain


class QuerySourceBinding(Protocol):
    """Binding that tells a QueryGenerator how to read from a specific source.

    Implementations typically adapt a build-time RollupBindingModel or a base-table binding.
    """

    @property
    def qualified_table(self) -> str:  # schema-qualified, quoted
        ...

    @property
    def column_mapping(self) -> Dict[str, str]:  # logical name -> physical sql/column
        ...

    @property
    def rollup_grain(self) -> Optional[TimeGrain]:
        ...

    @property
    def pre_aggregation_spec_id(self) -> Optional[str]:
        ...


