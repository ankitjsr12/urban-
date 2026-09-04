"""Initial database schema with PostGIS and UUID extensions.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure PostGIS and UUID extensions are enabled in PostgreSQL
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

    from app.models.base import Base
    import app.models

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from app.models.base import Base
    import app.models

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
