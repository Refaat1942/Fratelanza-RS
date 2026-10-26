from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_expenses,
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
    demos,
    exports,
    finance,
    hr,
    leads,
    modules,
    notifications,
    owners,
    pricing,
    procurement,
    projects,
    property,
    property_expenses,
    re_reports,
    re_requests,
    rentals,
    reports,
    reminders,
    reservations,
    roles,
    search,
    super_admin,
    tickets,
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
api_router.include_router(pricing.router, prefix="/pricing", tags=["Dynamic Pricing"])
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
api_router.include_router(hr.router, prefix="/hr", tags=["HR"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Customer Service"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & BI"])
api_router.include_router(modules.router, prefix="/modules", tags=["Modules"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(exports.router, prefix="/exports", tags=["Exports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Features"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & Permissions"])
api_router.include_router(demos.router, prefix="/demos", tags=["Demo Management"])
api_router.include_router(rentals.router, prefix="/rentals", tags=["Rental Contracts & Collections"])
api_router.include_router(owners.router, prefix="/owners", tags=["Owners & Settlements"])
api_router.include_router(property_expenses.router, prefix="/property-expenses", tags=["Property Expenses"])
api_router.include_router(admin_expenses.router, prefix="/admin-expenses", tags=["Administrative Expenses"])
api_router.include_router(re_requests.router, prefix="/re-requests", tags=["Property Requests & Matching"])
api_router.include_router(re_reports.router, prefix="/re-reports", tags=["Property Management Reports"])
api_router.include_router(re_reports.dashboard_router, prefix="/re-dashboard", tags=["Dashboard & BI"])
