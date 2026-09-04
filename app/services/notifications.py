import uuid
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification, NotificationType
from app.models.base import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    """Multi-channel notification dispatcher supporting database logging, Push, Email, and SMS."""

    @staticmethod
    async def send_notification(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.ALERT,
        metadata: dict | None = None,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {},
        )
        db.add(notif)
        await db.commit()
        await db.refresh(notif)

        # Mock dispatch hook for external FCM / Email / SMS providers
        logger.info(
            "Dispatched %s notification to user %s: %s",
            notification_type.value,
            user_id,
            title,
        )
        return notif
