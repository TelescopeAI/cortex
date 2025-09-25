from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.data.sources.data_sources import DataSource
from cortex.core.exceptions.data.sources import DataSourceAlreadyExistsError, DataSourceDoesNotExistError
from cortex.api.schemas.requests.data_sources import DataSourceCreateRequest, DataSourceUpdateRequest
from cortex.api.schemas.responses.data_sources import DataSourceResponse
from cortex.core.exceptions.environments import EnvironmentDoesNotExistError
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.types.databases import DataSourceTypes
from cortex.core.connectors.databases.SQL.humanizer import SchemaHumanizer
from cortex.core.services import DataSourceSchemaService

DataSourcesRouter = APIRouter()


@DataSourcesRouter.post(
    "/data/sources",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Data Sources"]
)
async def create_data_source(data_source_data: DataSourceCreateRequest):
    """Create a new data source"""
    try:
        data_source = DataSource(
            environment_id=data_source_data.environment_id,
            name=data_source_data.name,
            alias=data_source_data.alias,
            description=data_source_data.description,
            source_catalog=data_source_data.source_catalog,
            source_type=data_source_data.source_type,
            config=data_source_data.config
        )
        created_source = DataSourceCRUD.add_data_source(data_source)
        return DataSourceResponse(**created_source.model_dump())
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DataSourceAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}",
    response_model=DataSourceResponse,
    tags=["Data Sources"]
)
async def get_data_source(data_source_id: UUID):
    """Get a data source by ID"""
    try:
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        return DataSourceResponse(**data_source.model_dump())
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.get(
    "/environments/{environment_id}/data/sources",
    response_model=List[DataSourceResponse],
    tags=["Environments"]
)
async def list_data_sources(environment_id: UUID):
    """List all data sources in an environment"""
    try:
        data_sources = DataSourceCRUD.get_data_sources_by_environment(environment_id)
        return [DataSourceResponse(**ds.model_dump()) for ds in data_sources]
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.put(
    "/data/sources/{data_source_id}",
    response_model=DataSourceResponse,
    tags=["Data Sources"]
)
async def update_data_source(data_source_id: UUID, data_source_data: DataSourceUpdateRequest):
    """Update a data source"""
    try:
        # Get existing data source
        existing_source = DataSourceCRUD.get_data_source(data_source_id)

        # Update only provided fields
        if data_source_data.name is not None:
            existing_source.name = data_source_data.name
        if data_source_data.alias is not None:
            existing_source.alias = data_source_data.alias
        if data_source_data.description is not None:
            existing_source.description = data_source_data.description
        if data_source_data.config is not None:
            existing_source.config = data_source_data.config

        updated_source = DataSourceCRUD.update_data_source(existing_source)
        return DataSourceResponse(**updated_source.model_dump())
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.post(
    "/data/sources/{data_source_id}/ping",
    tags=["Data Sources"]
)
async def ping_data_source(data_source_id: UUID):
    """Test connectivity to a data source"""
    try:
        # Get the data source configuration
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        
        # Extract connection details from config
        config = data_source.config
        
        # Add dialect for SQL databases if not present
        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE]:
            config["dialect"] = data_source.source_type
        
        # Create database client and test connection
        client = DBClientService.get_client(details=config, db_type=data_source.source_type)
        client.connect()
        
        return {
            "status": "success",
            "message": f"Successfully connected to data source {data_source.name}",
            "data_source_id": data_source_id,
            "data_source_name": data_source.name,
            "source_type": data_source.source_type
        }
        
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Connection failed or other error
        return {
            "status": "failed",
            "message": f"Failed to connect to data source: {str(e)}",
            "data_source_id": data_source_id,
            "error": str(e)
                 }


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/schema",
    tags=["Data Sources"]
)
async def get_data_source_schema(data_source_id: UUID):
    """Get the schema information for a data source"""
    try:
        service = DataSourceSchemaService()
        return service.get_schema(data_source_id)
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Schema retrieval failed or other error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve schema for data source: {str(e)}"
        )


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/schema/humanized",
    tags=["Data Sources"]
)
async def get_data_source_schema_humanized(data_source_id: UUID):
    """Get a human-readable description of the data source schema"""
    try:
        # Get the data source configuration
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        
        # Extract connection details from config
        config = data_source.config.copy()
        
        # Add dialect for SQL databases if not present
        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE]:
            config["dialect"] = data_source.source_type
        
        # Create database client and get schema
        client = DBClientService.get_client(details=config, db_type=data_source.source_type)
        client.connect()
        
        # Get schema information
        schema = client.get_schema()
        
        # Humanize the schema
        humanizer = SchemaHumanizer()
        human_readable_schema = humanizer.humanize_schema(schema)
        
        return {
            "status": "success",
            "message": f"Successfully retrieved humanized schema for data source {data_source.name}",
            "data_source_id": data_source_id,
            "data_source_name": data_source.name,
            "source_type": data_source.source_type,
            "humanized_schema": human_readable_schema
        }
        
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Schema retrieval failed or other error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve humanized schema for data source: {str(e)}"
        )


@DataSourcesRouter.delete(
    "/data/sources/{data_source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Data Sources"]
)
async def delete_data_source(data_source_id: UUID):
    """Delete a data source"""
    try:
        if DataSourceCRUD.delete_data_source(data_source_id):
            return None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete data source"
        )
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )