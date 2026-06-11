from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crm import Lead, LeadActivity, LeadStage
from app.models.users import SystemRole, User, UserStatus

# Roles eligible to receive auto-assigned leads (least-loaded round-robin).
SALES_POOL_ROLES = (
    SystemRole.SALES_AGENT,
    SystemRole.SALES_MANAGER,
)

CLOSED_STAGES = (LeadStage.CONTRACT_SIGNED, LeadStage.LOST)


class LeadAssignmentService:
    @staticmethod
    async def get_sales_agents(db: AsyncSession, company_id: int) -> list[User]:
        result = await db.execute(
            select(User)
            .where(
                User.company_id == company_id,
                User.is_deleted == False,
                User.status == UserStatus.ACTIVE,
                User.system_role.in_(SALES_POOL_ROLES),
            )
            .order_by(User.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def pick_least_loaded_agent(db: AsyncSession, company_id: int) -> Optional[int]:
        agents = await LeadAssignmentService.get_sales_agents(db, company_id)
        if not agents:
            return None

        best_id: Optional[int] = None
        best_count = -1
        for agent in agents:
            count = (
                await db.execute(
                    select(func.count())
                    .select_from(Lead)
                    .where(
                        Lead.company_id == company_id,
                        Lead.is_deleted == False,
                        Lead.assigned_to_id == agent.id,
                        Lead.stage.notin_(CLOSED_STAGES),
                    )
                )
            ).scalar() or 0
            if best_id is None or count < best_count or (count == best_count and agent.id < best_id):
                best_id = agent.id
                best_count = count
        return best_id

    @staticmethod
    async def is_valid_assignee(db: AsyncSession, company_id: int, user_id: int) -> bool:
        result = await db.execute(
            select(User.id).where(
                User.id == user_id,
                User.company_id == company_id,
                User.is_deleted == False,
                User.status == UserStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def resolve_assignee(
        db: AsyncSession,
        company_id: int,
        assigned_to_id: Optional[int],
        fallback_user_id: Optional[int] = None,
    ) -> Optional[int]:
        """Use explicit assignee when valid; otherwise least-loaded sales agent; else fallback."""
        if assigned_to_id and await LeadAssignmentService.is_valid_assignee(db, company_id, assigned_to_id):
            return assigned_to_id
        auto = await LeadAssignmentService.pick_least_loaded_agent(db, company_id)
        if auto:
            return auto
        if fallback_user_id and await LeadAssignmentService.is_valid_assignee(db, company_id, fallback_user_id):
            return fallback_user_id
        return None

    @staticmethod
    async def log_assignment(
        db: AsyncSession,
        lead_id: int,
        agent_id: int,
        created_by_id: Optional[int] = None,
    ) -> None:
        db.add(
            LeadActivity(
                lead_id=lead_id,
                activity_type="assignment",
                description=f"Lead assigned to user #{agent_id}",
                created_by_id=created_by_id,
            )
        )
