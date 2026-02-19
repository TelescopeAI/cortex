"""
Exception mapper for Core → SDK exceptions.

Maps Core exceptions to SDK exceptions in Direct mode.
"""
from cortex.sdk.exceptions.base import (
    CortexSDKError,
    CortexNotFoundError,
    CortexValidationError,
)

# Import Core exceptions
from cortex.core.exceptions.data.sources import (
    DataSourceDoesNotExistError,
    DataSourceAlreadyExistsError,
    DataSourceHasDependenciesError,
    FileDoesNotExistError,
    FileHasDependenciesError,
)


class CoreExceptionMapper:
    """
    Maps Core exceptions to SDK exceptions.

    Used in Direct mode to provide consistent exception handling.

    Examples:
        >>> mapper = CoreExceptionMapper()
        >>> try:
        ...     # Core operation
        ...     pass
        ... except Exception as e:
        ...     sdk_exception = mapper.map(e)
        ...     raise sdk_exception
    """

    def map(self, exception: Exception) -> CortexSDKError:
        """
        Map a Core exception to an SDK exception.

        Args:
            exception: Core exception to map

        Returns:
            Corresponding SDK exception

        Examples:
            >>> mapper = CoreExceptionMapper()
            >>> core_exc = DataSourceDoesNotExistError(uuid4())
            >>> sdk_exc = mapper.map(core_exc)
            >>> isinstance(sdk_exc, CortexNotFoundError)
            True
        """
        # Not found errors
        if isinstance(exception, (DataSourceDoesNotExistError, FileDoesNotExistError)):
            return CortexNotFoundError(str(exception))

        # Validation errors (already exists, has dependencies)
        if isinstance(
            exception,
            (
                DataSourceAlreadyExistsError,
                DataSourceHasDependenciesError,
                FileHasDependenciesError,
            ),
        ):
            details = {}
            if hasattr(exception, "data_source_id"):
                details["data_source_id"] = str(exception.data_source_id)
            if hasattr(exception, "file_id"):
                details["file_id"] = str(exception.file_id)
            if hasattr(exception, "metric_ids"):
                details["metric_ids"] = [str(mid) for mid in exception.metric_ids]
            if hasattr(exception, "data_source_ids"):
                details["data_source_ids"] = [
                    str(did) for did in exception.data_source_ids
                ]

            return CortexValidationError(str(exception), details=details)

        # Default: wrap in generic SDK error
        return CortexSDKError(str(exception))
