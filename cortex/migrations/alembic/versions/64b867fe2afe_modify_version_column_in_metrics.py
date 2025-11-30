"""modify version column in metrics

Revision ID: 64b867fe2afe
Revises: 621f2170d426
Create Date: 2025-08-30 03:15:52.104615

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64b867fe2afe'
down_revision: Union[str, None] = '621f2170d426'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column to preserve existing data and constraints
    op.alter_column('metrics', 'model_version', new_column_name='version', existing_type=sa.Integer())


def downgrade() -> None:
    # Revert the rename if needed
    op.alter_column('metrics', 'version', new_column_name='model_version', existing_type=sa.Integer())
