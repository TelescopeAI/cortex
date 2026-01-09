from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from cortex.core import ConsumerGroupORM
from cortex.core.consumers.db.groups import consumer_group_members
from cortex.core.consumers.groups import ConsumerGroup
from cortex.core.consumers.consumer import Consumer
from cortex.core.consumers.db.consumer import ConsumerORM
from cortex.core.exceptions.consumers import ConsumerDoesNotExistError, ConsumerGroupDoesNotExistError, \
    ConsumerGroupAlreadyExistsError
from cortex.core.storage.store import CortexStorage
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD


class ConsumerGroupCRUD:

    @staticmethod
    def get_consumer_group_by_name_and_environment(
        name: str,
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> Optional[ConsumerGroup]:
        """
        Get consumer group by name and environment ID.
        
        Args:
            name: Consumer group name to search for
            environment_id: Environment ID to filter by
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            ConsumerGroup object or None if not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_group = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.name == name,
                ConsumerGroupORM.environment_id == environment_id
            ).first()
            if db_group is None:
                return None
            return ConsumerGroup.model_validate(db_group, from_attributes=True)
        finally:
            db_session.close()

    @staticmethod
    def add_consumer_group(group: ConsumerGroup, storage: Optional[CortexStorage] = None) -> ConsumerGroup:
        """
        Add a new consumer group to an environment.
        
        Args:
            group: ConsumerGroup object to create
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Created consumer group object
            
        Raises:
            ConsumerGroupAlreadyExistsError: If group already exists
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if environment exists
            EnvironmentCRUD.get_environment(group.environment_id, storage=storage)

            # Check if group with same name exists in the environment
            existing_group = ConsumerGroupCRUD.get_consumer_group_by_name_and_environment(
                group.name,
                group.environment_id,
                storage=storage
            )
            if existing_group:
                raise ConsumerGroupAlreadyExistsError(group.name, group.environment_id)

            while True:
                try:
                    group_id = uuid4()
                    db_group = ConsumerGroupORM(
                        id=group_id,
                        environment_id=group.environment_id,
                        name=group.name,
                        description=group.description,
                        alias=group.alias,
                        properties=group.properties,
                        created_at=datetime.now(pytz.UTC),
                        updated_at=datetime.now(pytz.UTC)
                    )
                    db_session.add(db_group)
                    db_session.commit()
                    db_session.refresh(db_group)
                    return ConsumerGroup.model_validate(db_group, from_attributes=True)
                except IntegrityError:
                    db_session.rollback()
                    continue
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_consumer_group(group_id: UUID, storage: Optional[CortexStorage] = None) -> ConsumerGroup:
        """
        Get consumer group by ID.
        
        Args:
            group_id: Consumer group ID to retrieve
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            ConsumerGroup object
            
        Raises:
            ConsumerGroupDoesNotExistError: If group not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_group = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.id == group_id
            ).first()
            if db_group is None:
                raise ConsumerGroupDoesNotExistError(group_id)
            return ConsumerGroup.model_validate(db_group, from_attributes=True)
        finally:
            db_session.close()

    @staticmethod
    def get_consumer_group_with_consumers(
        group_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> tuple[ConsumerGroup, List[Consumer]]:
        """
        Get consumer group with all its members.
        
        Args:
            group_id: Consumer group ID to retrieve
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Tuple of (ConsumerGroup, list of Consumer objects)
            
        Raises:
            ConsumerGroupDoesNotExistError: If group not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_group = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.id == group_id
            ).first()
            if db_group is None:
                raise ConsumerGroupDoesNotExistError(group_id)

            group = ConsumerGroup.model_validate(db_group, from_attributes=True)
            consumers = [Consumer.model_validate(c, from_attributes=True) for c in db_group.consumers]
            return group, consumers
        finally:
            db_session.close()

    @staticmethod
    def get_consumer_groups_by_environment(
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> List[ConsumerGroup]:
        """
        Get all consumer groups for an environment.
        
        Args:
            environment_id: Environment ID to get groups for
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of consumer group objects
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Verify environment exists
            EnvironmentCRUD.get_environment(environment_id, storage=storage)

            db_groups = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.environment_id == environment_id
            ).all()
            return [ConsumerGroup.model_validate(g, from_attributes=True) for g in db_groups]
        finally:
            db_session.close()

    @staticmethod
    def get_groups_for_consumer(consumer_id: UUID, storage: Optional[CortexStorage] = None) -> List[ConsumerGroup]:
        """
        Get all groups that a consumer belongs to.
        
        Args:
            consumer_id: Consumer ID to get groups for
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of consumer group objects
            
        Raises:
            ConsumerDoesNotExistError: If consumer not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if consumer exists
            db_consumer = db_session.query(ConsumerORM).filter(
                ConsumerORM.id == consumer_id
            ).first()
            if db_consumer is None:
                raise ConsumerDoesNotExistError(consumer_id)

            # Get groups that contain this consumer
            db_groups = db_session.query(ConsumerGroupORM).join(
                ConsumerGroupORM.consumers
            ).filter(
                ConsumerORM.id == consumer_id
            ).all()
            
            return [ConsumerGroup.model_validate(g, from_attributes=True) for g in db_groups]
        finally:
            db_session.close()

    @staticmethod
    def update_consumer_group(
        group: ConsumerGroup,
        storage: Optional[CortexStorage] = None
    ) -> ConsumerGroup:
        """
        Update an existing consumer group.
        
        Args:
            group: ConsumerGroup object with updated values
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Updated consumer group object
            
        Raises:
            ConsumerGroupDoesNotExistError: If group not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_group = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.id == group.id
            ).first()
            if db_group is None:
                raise ConsumerGroupDoesNotExistError(group.id)

            # Track if any changes were made
            changes_made = False

            # Check and update only allowed fields if they've changed
            if group.name != db_group.name:
                db_group.name = group.name
                changes_made = True

            if group.description != db_group.description:
                db_group.description = group.description
                changes_made = True

            if group.alias != db_group.alias:
                db_group.alias = group.alias
                changes_made = True

            if group.properties != db_group.properties:
                db_group.properties = group.properties
                changes_made = True

            # Only update if changes were made
            if changes_made:
                db_group.updated_at = datetime.now(pytz.UTC)
                db_session.commit()
                db_session.refresh(db_group)

            return ConsumerGroup.model_validate(db_group, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def delete_consumer_group(group_id: UUID, storage: Optional[CortexStorage] = None) -> bool:
        """
        Delete a consumer group.
        
        Args:
            group_id: Consumer group ID to delete
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if group was deleted, False otherwise
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            result = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.id == group_id
            ).delete()
            db_session.commit()
            return result > 0
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def add_consumer_to_group(
        group_id: UUID,
        consumer_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Add a consumer to a group.
        
        Args:
            group_id: Consumer group ID
            consumer_id: Consumer ID to add
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if consumer was added to group
            
        Raises:
            ConsumerGroupDoesNotExistError: If group not found
            ConsumerDoesNotExistError: If consumer not found
            ValueError: If consumer and group are in different environments
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if group exists
            db_group = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.id == group_id
            ).first()
            if db_group is None:
                raise ConsumerGroupDoesNotExistError(group_id)

            # Check if consumer exists
            db_consumer = db_session.query(ConsumerORM).filter(
                ConsumerORM.id == consumer_id
            ).first()
            if db_consumer is None:
                raise ConsumerDoesNotExistError(consumer_id)

            # Check if they're in the same environment
            if db_group.environment_id != db_consumer.environment_id:
                raise ValueError("Consumer and group must be in the same environment")

            # Check if already a member
            is_member = db_session.query(consumer_group_members).filter(
                consumer_group_members.c.consumer_id == consumer_id,
                consumer_group_members.c.group_id == group_id
            ).first() is not None

            if not is_member:
                # Insert into association table
                db_session.execute(
                    consumer_group_members.insert().values(
                        consumer_id=consumer_id,
                        group_id=group_id
                    )
                )
                db_session.commit()

            return True
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def remove_consumer_from_group(
        group_id: UUID,
        consumer_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Remove a consumer from a group.
        
        Args:
            group_id: Consumer group ID
            consumer_id: Consumer ID to remove
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if consumer was removed from group
            
        Raises:
            ConsumerGroupDoesNotExistError: If group not found
            ConsumerDoesNotExistError: If consumer not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if group exists
            if not db_session.query(ConsumerGroupORM).filter(ConsumerGroupORM.id == group_id).first():
                raise ConsumerGroupDoesNotExistError(group_id)

            # Check if consumer exists
            if not db_session.query(ConsumerORM).filter(ConsumerORM.id == consumer_id).first():
                raise ConsumerDoesNotExistError(consumer_id)

            # Delete from association table
            result = db_session.execute(
                consumer_group_members.delete().where(
                    consumer_group_members.c.consumer_id == consumer_id,
                    consumer_group_members.c.group_id == group_id
                )
            )
            db_session.commit()

            return result.rowcount > 0
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def is_consumer_in_group(
        group_id: UUID,
        consumer_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Check if a consumer is a member of a group.
        
        Args:
            group_id: Consumer group ID
            consumer_id: Consumer ID to check
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if consumer is in group, False otherwise
            
        Raises:
            ConsumerGroupDoesNotExistError: If group not found
            ConsumerDoesNotExistError: If consumer not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if group exists
            if not db_session.query(ConsumerGroupORM).filter(ConsumerGroupORM.id == group_id).first():
                raise ConsumerGroupDoesNotExistError(group_id)

            # Check if consumer exists
            if not db_session.query(ConsumerORM).filter(ConsumerORM.id == consumer_id).first():
                raise ConsumerDoesNotExistError(consumer_id)

            # Check membership
            is_member = db_session.query(consumer_group_members).filter(
                consumer_group_members.c.consumer_id == consumer_id,
                consumer_group_members.c.group_id == group_id
            ).first() is not None

            return is_member
        finally:
            db_session.close()