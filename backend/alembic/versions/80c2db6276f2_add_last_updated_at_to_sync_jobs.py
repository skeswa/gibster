"""add_last_updated_at_to_sync_jobs

Revision ID: 80c2db6276f2
Revises: 03fd6815538f
Create Date: 2025-07-01 16:29:13.947652

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "80c2db6276f2"
down_revision: Union[str, Sequence[str], None] = "03fd6815538f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add last_updated_at column to sync_jobs table
    with op.batch_alter_table("sync_jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("last_updated_at", sa.DateTime(), nullable=True))

    # Update existing rows to have a value for last_updated_at
    # Use the completed_at or started_at as a fallback
    op.execute(
        """
        UPDATE sync_jobs 
        SET last_updated_at = COALESCE(completed_at, started_at, CURRENT_TIMESTAMP)
        WHERE last_updated_at IS NULL
    """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove last_updated_at column from sync_jobs table
    with op.batch_alter_table("sync_jobs", schema=None) as batch_op:
        batch_op.drop_column("last_updated_at")
