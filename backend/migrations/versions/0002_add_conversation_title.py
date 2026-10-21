"""Add title and title_status to conversations. Existing rows keep NULL title and pending status.

No runtime model imports: future model changes cannot affect this migration.
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_conversation_title"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("conversations", sa.Column("title", sa.String(80), nullable=True))
    op.add_column(
        "conversations",
        sa.Column("title_status", sa.String(20), nullable=False, server_default="pending"),
    )


def downgrade():
    op.drop_column("conversations", "title_status")
    op.drop_column("conversations", "title")
