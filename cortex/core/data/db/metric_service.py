from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

import pytz
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc

from cortex.core.data.db.models import MetricORM, MetricVersionORM
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.storage.store import CortexStorage


class MetricService:
    """Service class for managing metrics in the database"""
    
    def __init__(self, session: Optional[Session] = None):
        if session:
            self.session = session
        else:
            self.local_session = CortexStorage()
            self.session = self.local_session.get_session()
    
    def create_metric(self, metric: SemanticMetric) -> MetricORM:
        """Create a new metric in the database"""
        try:
            db_metric = MetricORM(
                environment_id=metric.environment_id,
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

                parameters=metric.parameters,
                version=metric.version,
                extends=metric.extends,
                public=metric.public,
                refresh=metric.refresh,
                cache=metric.cache,
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
            
            # Create initial version snapshot aligned to current metric.version
            try:
                _ = self.create_metric_version(
                    db_metric.id,
                    description="Initial metric creation",
                    version_number=int(getattr(db_metric, 'version', 1) or 1)
                )
            except Exception:
                # Do not fail create on snapshot issues
                pass

            return db_metric
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create metric: {str(e)}")
    
    def get_metric_by_id(self, metric_id: UUID, environment_id: Optional[UUID] = None) -> Optional[MetricORM]:
        """Get a metric by its ID, optionally validating it belongs to an environment"""
        query = self.session.query(MetricORM).filter(MetricORM.id == metric_id)
        if environment_id is not None:
            query = query.filter(MetricORM.environment_id == environment_id)
        return query.first()
    
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
    
    def get_metrics_by_data_source(self, data_source_id: UUID, public_only: bool = False) -> List[MetricORM]:
        """Get all metrics for a specific data source"""
        query = self.session.query(MetricORM).filter(MetricORM.data_source_id == data_source_id)
        
        if public_only:
            query = query.filter(MetricORM.public == True)
            
        return query.order_by(desc(MetricORM.updated_at)).all()
    
    def get_all_metrics(self, 
                       environment_id: UUID,
                       skip: int = 0, 
                       limit: int = 100,
                       data_model_id: Optional[UUID] = None,
                       public_only: Optional[bool] = None,
                       valid_only: Optional[bool] = None) -> List[MetricORM]:
        """Get all metrics for a specific environment with optional filters"""
        query = self.session.query(MetricORM).filter(MetricORM.environment_id == environment_id)
        
        # Apply filters
        if data_model_id:
            query = query.filter(MetricORM.data_model_id == data_model_id)
        
        if public_only is not None:
            query = query.filter(MetricORM.public == public_only)
            
        if valid_only is not None:
            query = query.filter(MetricORM.is_valid == valid_only)
        
        return query.order_by(desc(MetricORM.updated_at)).offset(skip).limit(limit).all()
    
    def get_metrics_by_environment(self, environment_id: UUID) -> List[MetricORM]:
        """Get all metrics for a specific environment"""
        return (self.session.query(MetricORM)
                .filter(MetricORM.environment_id == environment_id)
                .order_by(desc(MetricORM.updated_at))
                .all())
    
    def update_metric(self, metric_id: UUID, updates: Dict[str, Any]) -> Optional[MetricORM]:
        """Update an existing metric"""
        try:
            db_metric = self.get_metric_by_id(metric_id)
            if not db_metric:
                return None
            
            # Detect changes to core fields to bump version for caching invalidation
            version_bump_fields = {
                'name', 'alias', 'description', 'title', 'query', 'table_name',
                'data_source_id', 'limit', 'grouped', 'measures', 'dimensions',
                'joins', 'aggregations', 'filters', 'parameters', 'refresh', 'cache', 'meta'
            }

            should_bump = any(k in version_bump_fields for k in updates.keys())

            # Update allowed fields - Pydantic handles serialization automatically
            for key, value in updates.items():
                if hasattr(db_metric, key):
                    setattr(db_metric, key, value)

            if should_bump:
                try:
                    current_version = int(getattr(db_metric, 'version', 0) or 0)
                except Exception:
                    current_version = 0
                setattr(db_metric, 'version', current_version + 1)
            
            # Always update the timestamp
            db_metric.updated_at = datetime.now(pytz.UTC)
            
            self.session.commit()
            self.session.refresh(db_metric)

            # Persist a version snapshot when bumped
            if should_bump:
                try:
                    changed_fields = ",".join(sorted(set(updates.keys()) & version_bump_fields))
                    _ = self.create_metric_version(
                        metric_id,
                        description=f"Auto snapshot on update: {changed_fields}",
                        version_number=int(getattr(db_metric, 'version', 1) or 1)
                    )
                except Exception:
                    # If snapshot fails, continue
                    pass
            
            return db_metric
            
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to update metric: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to update metric: {str(e)}")
    
    def delete_metric(self, metric_id: UUID) -> bool:
        """Delete a metric (hard delete) - cascades to delete all related versions first"""
        try:
            db_metric = self.get_metric_by_id(metric_id)
            if not db_metric:
                return False
            
            # First, delete all metric versions associated with this metric
            self.session.query(MetricVersionORM).filter(MetricVersionORM.metric_id == metric_id).delete()
            self.session.commit()
            
            # Then delete the metric itself
            self.session.delete(db_metric)
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Failed to delete metric: {str(e)}")
    
    def create_metric_version(self, metric_id: UUID, description: Optional[str] = None, version_number: Optional[int] = None) -> MetricVersionORM:
        """Create a version snapshot of a metric.

        If version_number is provided, it will be used. Otherwise, the method
        will bump the metric.version by 1 and use that value, keeping
        metric.version == metric_versions.version_number.
        """
        try:
            db_metric = self.get_metric_by_id(metric_id)
            if not db_metric:
                raise ValueError(f"Metric {metric_id} not found")
            
            # Resolve version to persist
            if version_number is None:
                current_version = int(getattr(db_metric, 'version', 0) or 0)
                next_version = current_version + 1
                setattr(db_metric, 'version', next_version)
                db_metric.updated_at = datetime.now(pytz.UTC)
                self.session.commit()
                self.session.refresh(db_metric)
                version_to_use = next_version
            else:
                version_to_use = int(version_number)

            # Create complete snapshot from ORM via Pydantic conversion
            pydantic_metric = SemanticMetric.model_validate(db_metric, from_attributes=True)
            snapshot = pydantic_metric.model_dump()
            
            db_version = MetricVersionORM(
                metric_id=metric_id,
                version_number=version_to_use,
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