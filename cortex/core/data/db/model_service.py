from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

import pytz
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc

from cortex.core.data.db.models import DataModelORM, ModelVersionORM, MetricORM
from cortex.core.data.modelling.model import DataModel
from cortex.core.data.modelling.model_version import ModelVersion
from cortex.core.storage.store import CortexStorage


class DataModelService:
    """Service class for managing data models in the database"""
    
    def __init__(self, storage: Optional[CortexStorage] = None):
        """
        Initialize DataModelService.
        
        Args:
            storage: Optional CortexStorage instance. If not provided, uses singleton.
        """
        self.storage = storage or CortexStorage()
        self.session = self.storage.get_session()
    
    def create_data_model(self, data_model: DataModel) -> DataModelORM:
        """Create a new data model in the database"""
        try:
            db_model = DataModelORM(
                id=data_model.id,
                environment_id=data_model.environment_id,
                name=data_model.name,
                alias=data_model.alias,
                description=data_model.description,
                version=data_model.version,
                is_active=data_model.is_active,
                parent_version_id=data_model.parent_version_id,
                config=data_model.config,
                is_valid=data_model.is_valid,
                validation_errors=data_model.validation_errors,
                created_at=data_model.created_at,
                updated_at=data_model.updated_at
            )
            
            self.session.add(db_model)
            self.session.commit()
            self.session.refresh(db_model)
            
            return db_model
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create data model: {str(e)}")
    
    def get_data_model_by_id(self, model_id: UUID, environment_id: Optional[UUID] = None) -> Optional[DataModelORM]:
        """Get a data model by its ID, optionally validating it belongs to an environment"""
        query = self.session.query(DataModelORM).filter(DataModelORM.id == model_id)
        if environment_id is not None:
            query = query.filter(DataModelORM.environment_id == environment_id)
        return query.first()
    
    
    def get_all_data_models(self, 
                           environment_id: UUID,
                           skip: int = 0, 
                           limit: int = 100,
                           active_only: Optional[bool] = None,
                           valid_only: Optional[bool] = None) -> List[DataModelORM]:
        """Get all data models for a specific environment with optional filters"""
        query = self.session.query(DataModelORM).filter(DataModelORM.environment_id == environment_id)
        
        # Apply filters
        if active_only is not None:
            query = query.filter(DataModelORM.is_active == active_only)
            
        if valid_only is not None:
            query = query.filter(DataModelORM.is_valid == valid_only)
        
        return query.order_by(desc(DataModelORM.updated_at)).offset(skip).limit(limit).all()
    
    def update_data_model(self, model_id: UUID, updates: Dict[str, Any]) -> Optional[DataModelORM]:
        """Update an existing data model"""
        try:
            db_model = self.get_data_model_by_id(model_id)
            if not db_model:
                return None
            
            # Update allowed fields
            for key, value in updates.items():
                if hasattr(db_model, key):
                    setattr(db_model, key, value)
            
            # Always update the timestamp
            db_model.updated_at = datetime.now(pytz.UTC)
            
            self.session.commit()
            self.session.refresh(db_model)
            
            return db_model
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to update data model: {str(e)}")
    
    def delete_data_model(self, model_id: UUID) -> bool:
        """Delete a data model (soft delete by setting is_active to False)"""
        try:
            db_model = self.get_data_model_by_id(model_id)
            if not db_model:
                return False
            
            # Soft delete
            db_model.is_active = False
            db_model.updated_at = datetime.now(pytz.UTC)
            
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to delete data model: {str(e)}")
    
    def create_model_version(self, model_version: ModelVersion) -> ModelVersionORM:
        """Create a new version snapshot of a data model"""
        try:
            db_version = ModelVersionORM(
                id=model_version.id,
                data_model_id=model_version.data_model_id,
                version_number=model_version.version_number,
                semantic_model=model_version.semantic_model,
                is_valid=model_version.is_valid,
                validation_errors=model_version.validation_errors,
                compiled_queries=model_version.compiled_queries,
                description=model_version.description,
                created_by=model_version.created_by,
                tags=model_version.tags,
                config=model_version.config,
                created_at=model_version.created_at
            )
            
            self.session.add(db_version)
            self.session.commit()
            self.session.refresh(db_version)
            
            return db_version
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create model version: {str(e)}")
    
    def get_model_versions(self, model_id: UUID) -> List[ModelVersionORM]:
        """Get all versions for a specific data model"""
        return (self.session.query(ModelVersionORM)
                .filter(ModelVersionORM.data_model_id == model_id)
                .order_by(desc(ModelVersionORM.version_number))
                .all())
    
    def get_model_version(self, model_id: UUID, version_number: int) -> Optional[ModelVersionORM]:
        """Get a specific version of a data model"""
        return (self.session.query(ModelVersionORM)
                .filter(and_(
                    ModelVersionORM.data_model_id == model_id,
                    ModelVersionORM.version_number == version_number
                ))
                .first())
    
    def to_pydantic_version(self, db_version: ModelVersionORM) -> ModelVersion:
        """Convert SQLAlchemy ORM version to Pydantic model"""
        return ModelVersion(
            id=db_version.id,
            data_model_id=db_version.data_model_id,
            version_number=db_version.version_number,
            semantic_model=db_version.semantic_model,
            is_valid=db_version.is_valid,
            validation_errors=db_version.validation_errors,
            compiled_queries=db_version.compiled_queries,
            description=db_version.description,
            created_by=db_version.created_by,
            tags=db_version.tags,
            config=db_version.config,
            created_at=db_version.created_at
        )
    
    def get_model_metrics(self, model_id: UUID) -> List[MetricORM]:
        """Get all metrics for a specific data model"""
        return (self.session.query(MetricORM)
                .filter(MetricORM.data_model_id == model_id)
                .order_by(desc(MetricORM.updated_at))
                .all())
    
    def get_model_metrics_count(self, model_id: UUID) -> int:
        """Get count of metrics for a specific data model"""
        return (self.session.query(MetricORM)
                .filter(MetricORM.data_model_id == model_id)
                .count())
    
    def close(self):
        """Close the database session"""
        if self.session:
            self.session.close()