from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    companies,
    customers,
    dashboard,
    leads,
    projects,
    reservations,
    search,
    super_admin,
    users,
    ai,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(super_admin.router, prefix="/super-admin", tags=["Super Admin"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(leads.router, prefix="/leads", tags=["CRM & Leads"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects & Units"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & BI"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Features"])
