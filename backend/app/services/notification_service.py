from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system import Notification


class NotificationService:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        title_ar: str,
        title_en: str,
        message_ar: str | None = None,
        message_en: str | None = None,
        company_id: int | None = None,
        channel: str = "in_app",
        reference_type: str | None = None,
        reference_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            company_id=company_id,
            title_ar=title_ar,
            title_en=title_en,
            message_ar=message_ar,
            message_en=message_en,
            channel=channel,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        db.add(notification)
        await db.flush()
        return notification
