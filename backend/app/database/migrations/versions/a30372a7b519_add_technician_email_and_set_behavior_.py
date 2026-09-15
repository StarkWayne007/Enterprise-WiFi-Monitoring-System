"""add technician email and set behavior window to 24 hours

Revision ID: a30372a7b519
Revises: f0f20d39cdb6
Create Date: 2026-09-11 07:46:09.299249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a30372a7b519"
down_revision: Union[str, Sequence[str], None] = "f0f20d39cdb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column(
            "technician_email",
            sa.String(length=320),
            nullable=False,
            server_default="",
        ),
    )

    op.execute(
        sa.text(
            "UPDATE system_settings "
            "SET behavior_window_minutes = 1440 "
            "WHERE id = 1"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE system_settings "
            "SET behavior_window_minutes = 5 "
            "WHERE id = 1"
        )
    )

    op.drop_column("system_settings", "technician_email")

