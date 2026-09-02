from alembic import op
import sqlalchemy as sa

def upgrade():
    # The canonical schema is created from SQLAlchemy metadata for local bootstrapping.
    from app.db.session import Base
    from app.models import models
    bind=op.get_bind(); Base.metadata.create_all(bind=bind)

def downgrade():
    from app.db.session import Base
    from app.models import models
    bind=op.get_bind(); Base.metadata.drop_all(bind=bind)
