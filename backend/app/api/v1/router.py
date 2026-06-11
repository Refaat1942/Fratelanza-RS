from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    auth,
    broker_portal,
    brokers,
    collections,
    companies,
    construction,
    contracts,
    customer_portal,
    customers,
    dashboard,
    exports,
    finance,
    hr,
    leads,
    modules,
    notifications,
    procurement,
    projects,
    property,
    reports,
    reminders,
    reservations,
    search,
    super_admin,
    tickets,
    treasury,
    users,
    warehouse,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(super_admin.router, prefix="/super-admin", tags=["Super Admin"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(leads.router, prefix="/leads", tags=["CRM & Leads"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects & Units"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(collections.router, prefix="/collections", tags=["Collections"])
api_router.include_router(brokers.router, prefix="/brokers", tags=["Brokers"])
api_router.include_router(broker_portal.router, prefix="/broker-portal", tags=["Broker Portal"])
api_router.include_router(customer_portal.router, prefix="/customer-portal", tags=["Customer Portal"])
api_router.include_router(construction.router, prefix="/construction", tags=["Construction"])
api_router.include_router(procurement.router, prefix="/procurement", tags=["Procurement"])
api_router.include_router(warehouse.router, prefix="/warehouse", tags=["Warehouse"])
api_router.include_router(property.router, prefix="/property", tags=["Property Management"])
api_router.include_router(finance.router, prefix="/finance", tags=["Finance"])
api_router.include_router(treasury.router, prefix="/treasury", tags=["Treasury"])
api_router.include_router(hr.router, prefix="/hr", tags=["HR"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Customer Service"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & BI"])
api_router.include_router(modules.router, prefix="/modules", tags=["Modules"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Features"])
