from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.pricing import PricingRule
from app.models.real_estate import Project
from app.models.users import User
from app.schemas.pricing import PricingRuleCreate, PricingRuleResponse, PricingRuleUpdate
from app.services.dynamic_pricing_service import DynamicPricingService

router = APIRouter()


def _rule_dict(rule: PricingRule) -> dict:
    data = PricingRuleResponse.model_validate(rule).model_dump()
    data["trigger_type"] = rule.trigger_type.value
    return data


@router.get("/rules")
async def list_pricing_rules(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: Optional[int] = None,
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(PricingRule)
    if not current_user.is_super_admin:
        query = query.where(PricingRule.company_id == current_user.company_id)
    if project_id is not None:
        query = query.where(
            (PricingRule.project_id == project_id) | (PricingRule.project_id.is_(None))
        )
    rules = (await db.execute(query.order_by(PricingRule.sort_order, PricingRule.id))).scalars().all()
    return [_rule_dict(r) for r in rules]


@router.post("/rules", response_model=PricingRuleResponse)
async def create_pricing_rule(
    data: PricingRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    if data.project_id:
        project = (
            await db.execute(
                select(Project).where(
                    Project.id == data.project_id,
                    Project.company_id == current_user.company_id,
                    Project.is_deleted == False,
                )
            )
        ).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    rule = PricingRule(company_id=current_user.company_id, **data.model_dump())
    db.add(rule)
    await db.flush()
    return PricingRuleResponse.model_validate(rule)


@router.put("/rules/{rule_id}")
async def update_pricing_rule(
    rule_id: int,
    data: PricingRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    rule = (await db.execute(select(PricingRule).where(PricingRule.id == rule_id))).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    if not current_user.is_super_admin and rule.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.flush()
    return _rule_dict(rule)


@router.delete("/rules/{rule_id}")
async def delete_pricing_rule(
    rule_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    rule = (await db.execute(select(PricingRule).where(PricingRule.id == rule_id))).scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    if not current_user.is_super_admin and rule.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    await db.delete(rule)
    await db.flush()
    return {"success": True}


@router.get("/preview")
async def preview_pricing(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: int = Query(...),
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    project = (
        await db.execute(
            select(Project).where(Project.id == project_id, Project.is_deleted == False)
        )
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_super_admin and project.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await DynamicPricingService.compute_adjustment_percent(
        db, project.company_id, project_id
    )


@router.post("/recalculate")
async def recalculate_prices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    project_id: int = Query(...),
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    project = (
        await db.execute(
            select(Project).where(Project.id == project_id, Project.is_deleted == False)
        )
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not current_user.is_super_admin and project.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    result = await DynamicPricingService.recalculate_project_prices(
        db, project.company_id, project_id
    )
    return result
