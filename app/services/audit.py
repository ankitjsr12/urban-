import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.models.base import utc_now

logger = logging.getLogger("security.audit")


class AuditService:
    """Security audit log recording service."""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        action: str,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )
        db.add(audit)
        try:
            await db.commit()
            await db.refresh(audit)
        except Exception as e:
            logger.error("Failed to commit audit log entry: %s", e)
        return audit
