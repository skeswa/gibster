"""add_booking_indexes_for_performance

Revision ID: 46c87f424281
Revises: 80c2db6276f2
Create Date: 2025-07-08 12:03:08.792683

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "46c87f424281"
down_revision: Union[str, Sequence[str], None] = "80c2db6276f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create index on user_id for faster filtering
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])

    # Create composite index on (user_id, id) for faster existence checks
    op.create_index("ix_bookings_user_id_id", "bookings", ["user_id", "id"])

    # Create index on last_seen for potential cleanup operations
    op.create_index("ix_bookings_last_seen", "bookings", ["last_seen"])

    # Create index on start_time for calendar queries
    op.create_index("ix_bookings_start_time", "bookings", ["start_time"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_bookings_start_time", "bookings")
    op.drop_index("ix_bookings_last_seen", "bookings")
    op.drop_index("ix_bookings_user_id_id", "bookings")
    op.drop_index("ix_bookings_user_id", "bookings")
