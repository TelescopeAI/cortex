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
    def get_consumer_group_by_name_and_environment(name: str, environment_id: UUID) -> Optional[ConsumerGroup]:
        db_session = CortexStorage().get_session()
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
    def add_consumer_group(group: ConsumerGroup) -> ConsumerGroup:
        db_session = CortexStorage().get_session()
        try:
            # Check if environment exists
            EnvironmentCRUD.get_environment(group.environment_id)

            # Check if group with same name exists in the environment
            existing_group = ConsumerGroupCRUD.get_consumer_group_by_name_and_environment(
                group.name,
                group.environment_id
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
    def get_consumer_group(group_id: UUID) -> ConsumerGroup:
        db_session = CortexStorage().get_session()
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
    def get_consumer_group_with_consumers(group_id: UUID) -> tuple[ConsumerGroup, List[Consumer]]:
        db_session = CortexStorage().get_session()
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
    def get_consumer_groups_by_environment(environment_id: UUID) -> List[ConsumerGroup]:
        db_session = CortexStorage().get_session()
        try:
            # Verify environment exists
            EnvironmentCRUD.get_environment(environment_id)

            db_groups = db_session.query(ConsumerGroupORM).filter(
                ConsumerGroupORM.environment_id == environment_id
            ).all()
            return [ConsumerGroup.model_validate(g, from_attributes=True) for g in db_groups]
        finally:
            db_session.close()

    @staticmethod
    def get_groups_for_consumer(consumer_id: UUID) -> List[ConsumerGroup]:
        db_session = CortexStorage().get_session()
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
    def update_consumer_group(group: ConsumerGroup) -> ConsumerGroup:
        db_session = CortexStorage().get_session()
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
    def delete_consumer_group(group_id: UUID) -> bool:
        db_session = CortexStorage().get_session()
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
    def add_consumer_to_group(group_id: UUID, consumer_id: UUID) -> bool:
        db_session = CortexStorage().get_session()
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
    def remove_consumer_from_group(group_id: UUID, consumer_id: UUID) -> bool:
        db_session = CortexStorage().get_session()
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
    def is_consumer_in_group(group_id: UUID, consumer_id: UUID) -> bool:
        db_session = CortexStorage().get_session()
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