from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel


class KPICard(BaseModel):
    label_ar: str
    label_en: str
    value: str
    change_percent: Optional[float] = None
    trend: Optional[str] = None


class DashboardStats(BaseModel):
    total_companies: Optional[int] = None
    total_users: Optional[int] = None
    total_projects: Optional[int] = None
    total_customers: Optional[int] = None
    total_leads: Optional[int] = None
    total_units: Optional[int] = None
    available_units: Optional[int] = None
    reserved_units: Optional[int] = None
    sold_units: Optional[int] = None
    total_sales: Optional[Decimal] = None
    total_collections: Optional[Decimal] = None
    overdue_amount: Optional[Decimal] = None
    active_contracts: Optional[int] = None
    open_tickets: Optional[int] = None


class ChartDataPoint(BaseModel):
    label: str
    value: float


class DashboardResponse(BaseModel):
    stats: DashboardStats
    kpis: List[KPICard]
    sales_chart: List[ChartDataPoint] = []
    collections_chart: List[ChartDataPoint] = []
    leads_pipeline: Dict[str, int] = {}
