"""Username login (e-mail optional) and password-less demo links.

Revision ID: 20261027_01
Revises: 20261026_01
Create Date: 2026-10-27
"""

import sqlalchemy as sa
from alembic import op

revision = "20261027_01"
down_revision = "20261026_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN email DROP NOT NULL"))
    op.execute(sa.text("ALTER TABLE demo_environments ADD COLUMN IF NOT EXISTS access_token VARCHAR(64)"))
    op.execute(sa.text("ALTER TABLE demo_environments ADD COLUMN IF NOT EXISTS link_user_id INTEGER REFERENCES users(id)"))
    op.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_demo_environments_access_token ON demo_environments (access_token)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_demo_environments_access_token"))
    op.execute(sa.text("ALTER TABLE demo_environments DROP COLUMN IF EXISTS link_user_id"))
    op.execute(sa.text("ALTER TABLE demo_environments DROP COLUMN IF EXISTS access_token"))
    # Only possible while every user still has an e-mail
    op.execute(sa.text("ALTER TABLE users ALTER COLUMN email SET NOT NULL"))
