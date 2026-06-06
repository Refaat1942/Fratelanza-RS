from fastapi import APIRouter

from app.api.v1.endpoints import auth, companies, customers, dashboard, real_estate, sales

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(real_estate.router, tags=["real-estate"])
api_router.include_router(sales.router, tags=["sales"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
