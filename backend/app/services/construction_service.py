from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.construction import ConstructionPhase, ConstructionTask
from app.models.real_estate import Project


class ConstructionService:
    @staticmethod
    async def get_phase_for_company(
        db: AsyncSession, phase_id: int, company_id: Optional[int]
    ) -> Optional[ConstructionPhase]:
        result = await db.execute(
            select(ConstructionPhase, Project)
            .join(Project, ConstructionPhase.project_id == Project.id)
            .where(ConstructionPhase.id == phase_id)
        )
        row = result.first()
        if not row:
            return None
        phase, project = row
        if company_id and project.company_id != company_id:
            return None
        return phase

    @staticmethod
    async def rollup_phase_progress(db: AsyncSession, phase_id: int) -> int:
        result = await db.execute(select(ConstructionTask).where(ConstructionTask.phase_id == phase_id))
        tasks = result.scalars().all()
        if not tasks:
            return 0
        avg = round(sum(t.progress_percent for t in tasks) / len(tasks))
        phase = (await db.execute(select(ConstructionPhase).where(ConstructionPhase.id == phase_id))).scalar_one_or_none()
        if phase:
            phase.progress_percent = min(max(avg, 0), 100)
            await db.flush()
            return phase.progress_percent
        return 0

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def _task_dates(task: ConstructionTask, phase: ConstructionPhase) -> tuple[str, str]:
        start = task.planned_start or phase.planned_start
        end = task.planned_end or phase.planned_end
        if start and end:
            return start, end
        today = date.today()
        fallback_start = (today - timedelta(days=7)).isoformat()
        fallback_end = (today + timedelta(days=21)).isoformat()
        return start or fallback_start, end or fallback_end

    @staticmethod
    async def build_schedule(db: AsyncSession, project_id: int, company_id: Optional[int]) -> dict:
        project = (
            await db.execute(select(Project).where(Project.id == project_id))
        ).scalar_one_or_none()
        if not project:
            return {"project_id": project_id, "range_start": None, "range_end": None, "rows": []}
        if company_id and project.company_id != company_id:
            return {"project_id": project_id, "range_start": None, "range_end": None, "rows": []}

        phases = (
            await db.execute(
                select(ConstructionPhase).where(ConstructionPhase.project_id == project_id).order_by(ConstructionPhase.id)
            )
        ).scalars().all()

        rows: list[dict] = []
        all_starts: list[date] = []
        all_ends: list[date] = []

        for phase in phases:
            p_start, p_end = ConstructionService._task_dates(
                ConstructionTask(phase_id=phase.id, name_ar="", name_en=""), phase
            )
            ps = ConstructionService._parse_date(p_start)
            pe = ConstructionService._parse_date(p_end)
            if ps:
                all_starts.append(ps)
            if pe:
                all_ends.append(pe)
            rows.append(
                {
                    "id": f"phase-{phase.id}",
                    "entity_id": phase.id,
                    "type": "phase",
                    "phase_id": phase.id,
                    "label_ar": phase.name_ar,
                    "label_en": phase.name_en,
                    "start": p_start,
                    "end": p_end,
                    "progress_percent": phase.progress_percent,
                    "depends_on_task_id": None,
                }
            )

            tasks = (
                await db.execute(
                    select(ConstructionTask).where(ConstructionTask.phase_id == phase.id).order_by(ConstructionTask.id)
                )
            ).scalars().all()
            for task in tasks:
                t_start, t_end = ConstructionService._task_dates(task, phase)
                ts = ConstructionService._parse_date(t_start)
                te = ConstructionService._parse_date(t_end)
                if ts:
                    all_starts.append(ts)
                if te:
                    all_ends.append(te)
                rows.append(
                    {
                        "id": f"task-{task.id}",
                        "entity_id": task.id,
                        "type": "task",
                        "phase_id": phase.id,
                        "label_ar": task.name_ar,
                        "label_en": task.name_en,
                        "start": t_start,
                        "end": t_end,
                        "progress_percent": task.progress_percent,
                        "depends_on_task_id": task.depends_on_task_id,
                        "status": task.status,
                        "contractor": task.contractor,
                    }
                )

        range_start = min(all_starts).isoformat() if all_starts else None
        range_end = max(all_ends).isoformat() if all_ends else None
        return {
            "project_id": project_id,
            "project_name_ar": project.name_ar,
            "project_name_en": project.name_en,
            "range_start": range_start,
            "range_end": range_end,
            "rows": rows,
        }
