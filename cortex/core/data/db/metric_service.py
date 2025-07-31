from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

import pytz
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc

from cortex.core.data.db.models import MetricORM, MetricVersionORM
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.stores.connection import LocalSession


class MetricService:
    """Service class for managing metrics in the database"""
    
    def __init__(self, session: Optional[Session] = None):
        if session:
            self.session = session
        else:
            self.local_session = LocalSession()
            self.session = self.local_session.get_session()
    
    def create_metric(self, metric: SemanticMetric) -> MetricORM:
        """Create a new metric in the database"""
        try:
            db_metric = MetricORM(
                data_model_id=metric.data_model_id,
                name=metric.name,
                alias=metric.alias,
                description=metric.description,
                title=metric.title,
                query=metric.query,
                table_name=metric.table_name,
                data_source_id=metric.data_source_id,
                limit=metric.limit,
                measures=metric.measures,
                dimensions=metric.dimensions,
                joins=metric.joins,
                aggregations=metric.aggregations,
                filters=metric.filters,
                output_formats=metric.output_formats,
                parameters=metric.parameters,
                model_version=metric.model_version,
                extends=metric.extends,
                public=metric.public,
                refresh_key=metric.refresh_key,
                meta=metric.meta,
                is_valid=metric.is_valid,
                validation_errors=metric.validation_errors,
                compiled_query=metric.compiled_query,
                created_at=metric.created_at,
                updated_at=metric.updated_at
            )
            
            self.session.add(db_metric)
            self.session.commit()
            self.session.refresh(db_metric)
            
            return db_metric
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create metric: {str(e)}")
    
    def get_metric_by_id(self, metric_id: UUID) -> Optional[MetricORM]:
        """Get a metric by its ID"""
        return self.session.query(MetricORM).filter(MetricORM.id == metric_id).first()
    
    def get_metric_by_alias(self, data_model_id: UUID, alias: str) -> Optional[MetricORM]:
        """Get a metric by its alias within a specific data model"""
        return (self.session.query(MetricORM)
                .filter(and_(
                    MetricORM.data_model_id == data_model_id,
                    MetricORM.alias == alias
                ))
                .first())
    
    def get_metrics_by_model(self, data_model_id: UUID, public_only: bool = False) -> List[MetricORM]:
        """Get all metrics for a specific data model"""
        query = self.session.query(MetricORM).filter(MetricORM.data_model_id == data_model_id)
        
        if public_only:
            query = query.filter(MetricORM.public == True)
            
        return query.order_by(desc(MetricORM.updated_at)).all()
    
    def get_all_metrics(self, 
                       skip: int = 0, 
                       limit: int = 100,
                       data_model_id: Optional[UUID] = None,
                       public_only: Optional[bool] = None,
                       valid_only: Optional[bool] = None) -> List[MetricORM]:
        """Get all metrics with optional filters"""
        query = self.session.query(MetricORM)
        
        # Apply filters
        if data_model_id:
            query = query.filter(MetricORM.data_model_id == data_model_id)
        
        if public_only is not None:
            query = query.filter(MetricORM.public == public_only)
            
        if valid_only is not None:
            query = query.filter(MetricORM.is_valid == valid_only)
        
        return query.order_by(desc(MetricORM.updated_at)).offset(skip).limit(limit).all()
    
    def update_metric(self, metric_id: UUID, updates: Dict[str, Any]) -> Optional[MetricORM]:
        """Update an existing metric"""
        try:
            db_metric = self.get_metric_by_id(metric_id)
            if not db_metric:
                return None
            
            # Update allowed fields - Pydantic handles serialization automatically
            for key, value in updates.items():
                if hasattr(db_metric, key):
                    setattr(db_metric, key, value)
            
            # Always update the timestamp
            db_metric.updated_at = datetime.now(pytz.UTC)
            
            self.session.commit()
            self.session.refresh(db_metric)
            
            return db_metric
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to update metric: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to update metric: {str(e)}")
    
    def delete_metric(self, metric_id: UUID) -> bool:
        """Delete a metric (hard delete)"""
        try:
            db_metric = self.get_metric_by_id(metric_id)
            if not db_metric:
                return False
            
            self.session.delete(db_metric)
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to delete metric: {str(e)}")
    
    def create_metric_version(self, metric_id: UUID, description: Optional[str] = None) -> MetricVersionORM:
        """Create a version snapshot of a metric"""
        try:
            db_metric = self.get_metric_by_id(metric_id)
            if not db_metric:
                raise ValueError(f"Metric {metric_id} not found")
            
            # Get the current version number
            latest_version = (self.session.query(MetricVersionORM)
                            .filter(MetricVersionORM.metric_id == metric_id)
                            .order_by(desc(MetricVersionORM.version_number))
                            .first())
            
            version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create complete snapshot
            snapshot = db_metric.model_dump()
            
            db_version = MetricVersionORM(
                metric_id=metric_id,
                version_number=version_number,
                snapshot_data=snapshot,
                description=description,
                created_at=datetime.now(pytz.UTC)
            )
            
            self.session.add(db_version)
            self.session.commit()
            self.session.refresh(db_version)
            
            return db_version
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create metric version: {str(e)}")
    
    def get_metric_versions(self, metric_id: UUID) -> List[MetricVersionORM]:
        """Get all versions for a specific metric"""
        return (self.session.query(MetricVersionORM)
                .filter(MetricVersionORM.metric_id == metric_id)
                .order_by(desc(MetricVersionORM.version_number))
                .all())
    
    def clone_metric(self, metric_id: UUID, new_data_model_id: UUID, new_name: Optional[str] = None) -> MetricORM:
        """Clone a metric to another data model"""
        try:
            original_metric = self.get_metric_by_id(metric_id)
            if not original_metric:
                raise ValueError(f"Metric {metric_id} not found")
            
            # Convert to Pydantic and modify
            metric_data = original_metric.model_dump()
            metric_data['data_model_id'] = new_data_model_id
            metric_data['name'] = new_name or f"{metric_data['name']}_copy"
            metric_data['alias'] = None  # Clear alias to avoid conflicts
            
            # Create new metric
            return self.create_metric(SemanticMetric(**metric_data))
            
        except Exception as e:
            raise ValueError(f"Failed to clone metric: {str(e)}")
    
    def close(self):
        """Close the database session"""
        if self.session:
            self.session.close() 