from datetime import datetime
from typing import List, Optional
from uuid import UUID

from cortex.core.types.databases import DataSourceTypes, DataSourceCatalog
from cortex.core.types.telescope import TSModel


class DataSourceResponse(TSModel):
    id: UUID
    environment_id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]
    source_catalog: DataSourceCatalog
    source_type: DataSourceTypes
    config: dict
    created_at: datetime
    updated_at: datetime


class DependentMetricInfo(TSModel):
    """Brief info about a dependent metric"""
    id: UUID
    name: str
    alias: Optional[str] = None
    version_count: int


class DataSourceDependencies(TSModel):
    """Details of entities depending on a data source"""
    metrics: List[DependentMetricInfo]


class DataSourceDependenciesResponse(TSModel):
    """Response when data source cannot be deleted due to dependencies"""
    error: str = "DataSourceHasDependencies"
    message: str
    data_source_id: UUID
    dependencies: DataSourceDependencies


class DependentDataSourceInfo(TSModel):
    """Brief info about a dependent data source with its metrics"""
    id: UUID
    name: str
    alias: Optional[str] = None
    metrics: List[DependentMetricInfo]


class FileDependencies(TSModel):
    """Details of entities depending on a file"""
    data_sources: List[DependentDataSourceInfo]


class FileDependenciesResponse(TSModel):
    """Response when file cannot be deleted due to dependencies"""
    error: str = "FileHasDependencies"
    message: str
    file_id: UUID
    dependencies: FileDependencies


class DataSourceRebuildResponse(TSModel):
    """Response from data source rebuild operation"""
    success: bool
    message: str
    rebuilt_tables: List[str]
    last_synced: Optional[str] = None
    sqlite_path: Optional[str] = None
