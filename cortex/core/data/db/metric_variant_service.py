"""
Service for metric variant CRUD operations and versioning.

This module provides the MetricVariantService class for managing metric variants
in the database, including creation, retrieval, updates, deletion, and version tracking.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from cortex.core.data.db.metrics import MetricVariantORM, MetricVariantVersionORM
from cortex.core.storage.store import CortexStorage
from cortex.core.semantics.metrics.variant import SemanticMetricVariant


class MetricVariantService:
    """Service for metric variant CRUD operations and versioning."""

    def __init__(self, session: Optional[Session] = None):
        if session:
            self.session = session
            self.local_session = None
        else:
            self.local_session = CortexStorage()
            self.session = self.local_session.get_session()

    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close()

    def create_variant(self, variant: SemanticMetricVariant) -> MetricVariantORM:
        """
        Create a new metric variant.
        Auto-creates initial version snapshot.
        """
        try:
            # Create ORM instance from Pydantic model
            db_variant = MetricVariantORM(
                id=variant.id,
                environment_id=variant.environment_id,
                data_model_id=variant.data_model_id,
                data_source_id=variant.data_source_id,
                source_id=variant.source_id,  # For CASCADE DELETE
                name=variant.name,
                alias=variant.alias,
                description=variant.description,
                source=variant.source.model_dump() if variant.source else None,
                overrides=variant.overrides.model_dump() if variant.overrides else None,
                include=variant.include.model_dump() if variant.include else None,
                derivations=[d.model_dump() for d in variant.derivations] if variant.derivations else None,
                combine=[c.model_dump() for c in variant.combine] if variant.combine else None,
                composition=None,  # Populated by compiler
                version=variant.version,
                public=variant.public,
                cache=variant.cache.model_dump() if variant.cache else None,
                refresh=variant.refresh.model_dump() if variant.refresh else None,
                parameters={k: v.model_dump() for k, v in variant.parameters.items()} if variant.parameters else None,
                meta=variant.meta,
                is_valid=variant.is_valid,
                validation_errors=variant.validation_errors,
                compiled_query=variant.compiled_query,
                created_at=variant.created_at,
                updated_at=variant.updated_at
            )

            self.session.add(db_variant)
            self.session.flush()

            # Auto-create initial version snapshot
            self.create_variant_version(
                variant_id=db_variant.id,
                version_number=variant.version,
                description="Initial version"
            )

            self.session.commit()
            return db_variant

        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Failed to create variant: {str(e)}")

    def get_variant_by_id(
        self,
        variant_id: UUID,
        environment_id: Optional[UUID] = None
    ) -> Optional[MetricVariantORM]:
        """Get a single variant by ID with optional environment validation."""
        query = self.session.query(MetricVariantORM).filter(MetricVariantORM.id == variant_id)

        if environment_id:
            query = query.filter(MetricVariantORM.environment_id == environment_id)

        return query.first()

    def get_all_variants(
        self,
        environment_id: UUID,
        skip: int = 0,
        limit: int = 100,
        data_model_id: Optional[UUID] = None,
        source_metric_id: Optional[UUID] = None,
        public_only: bool = False
    ) -> List[MetricVariantORM]:
        """Get paginated list of variants with optional filtering."""
        query = self.session.query(MetricVariantORM).filter(
            MetricVariantORM.environment_id == environment_id
        )

        if data_model_id:
            query = query.filter(MetricVariantORM.data_model_id == data_model_id)

        if source_metric_id:
            query = query.filter(MetricVariantORM.source_id == source_metric_id)

        if public_only:
            query = query.filter(MetricVariantORM.public == True)

        return query.offset(skip).limit(limit).all()

    def get_variants_by_environment(self, environment_id: UUID) -> List[MetricVariantORM]:
        """Get all variants in an environment."""
        return self.session.query(MetricVariantORM).filter(
            MetricVariantORM.environment_id == environment_id
        ).all()

    def get_variants_by_data_model(
        self,
        data_model_id: UUID,
        public_only: bool = False
    ) -> List[MetricVariantORM]:
        """Get all variants for a data model."""
        query = self.session.query(MetricVariantORM).filter(
            MetricVariantORM.data_model_id == data_model_id
        )

        if public_only:
            query = query.filter(MetricVariantORM.public == True)

        return query.all()

    def get_variants_by_source_metric(
        self,
        source_metric_id: UUID,
        environment_id: UUID
    ) -> List[MetricVariantORM]:
        """Get all variants that reference a specific source metric."""
        return self.session.query(MetricVariantORM).filter(
            MetricVariantORM.source_id == source_metric_id,
            MetricVariantORM.environment_id == environment_id
        ).all()

    def update_variant(self, variant_id: UUID, updates: Dict[str, Any]) -> Optional[MetricVariantORM]:
        """
        Update a variant.
        Auto-increments version and creates snapshot if key fields changed.
        """
        db_variant = self.session.query(MetricVariantORM).filter(MetricVariantORM.id == variant_id).first()
        if not db_variant:
            return None

        # Version bump fields (core definition changes)
        version_bump_fields = {
            'name', 'alias', 'description', 'source', 'overrides', 'include',
            'derivations', 'combine', 'public', 'cache', 'refresh', 'parameters', 'meta'
        }

        should_bump_version = any(field in updates for field in version_bump_fields)

        # Apply updates
        for key, value in updates.items():
            setattr(db_variant, key, value)

        # Bump version and create snapshot if needed
        if should_bump_version:
            db_variant.version += 1
            # Invalidate compiled query on version bump (definition changed)
            db_variant.compiled_query = None
            db_variant.is_valid = False
            self.session.flush()
            self.create_variant_version(
                variant_id=variant_id,
                version_number=db_variant.version,
                description=f"Auto-saved version {db_variant.version}"
            )

        self.session.commit()
        return db_variant

    def delete_variant(self, variant_id: UUID) -> bool:
        """
        Delete a variant.
        Cascades to delete all version snapshots.
        """
        db_variant = self.session.query(MetricVariantORM).filter(MetricVariantORM.id == variant_id).first()
        if not db_variant:
            return False

        # Cascade delete versions (handled by relationship cascade)
        self.session.delete(db_variant)
        self.session.commit()
        return True

    def create_variant_version(
        self,
        variant_id: UUID,
        version_number: Optional[int] = None,
        description: Optional[str] = None
    ) -> MetricVariantVersionORM:
        """Create a new version snapshot of a variant."""
        db_variant = self.session.query(MetricVariantORM).filter(MetricVariantORM.id == variant_id).first()
        if not db_variant:
            raise ValueError(f"Variant {variant_id} not found")

        # Use provided version or increment current
        if version_number is None:
            version_number = db_variant.version + 1
            db_variant.version = version_number

        # Convert ORM to Pydantic
        pydantic_variant = SemanticMetricVariant.model_validate(db_variant, from_attributes=True)

        # Create version snapshot
        db_version = MetricVariantVersionORM(
            variant_id=variant_id,
            version_number=version_number,
            snapshot_data=pydantic_variant.model_dump(),
            description=description or f"Version {version_number}"
        )

        self.session.add(db_version)
        self.session.flush()
        return db_version

    def get_variant_versions(self, variant_id: UUID) -> List[MetricVariantVersionORM]:
        """Get all versions for a variant, ordered by version_number desc."""
        return (
            self.session.query(MetricVariantVersionORM)
            .filter(MetricVariantVersionORM.variant_id == variant_id)
            .order_by(MetricVariantVersionORM.version_number.desc())
            .all()
        )

    def get_variant_version_count(self, variant_id: UUID) -> int:
        """Count versions for a variant."""
        return self.session.query(MetricVariantVersionORM).filter(
            MetricVariantVersionORM.variant_id == variant_id
        ).count()
