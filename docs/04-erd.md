# Entity Relationship Diagram (ERD)
# FRATELANZA REAL ESTATE PLATFORM

```mermaid
erDiagram
    COMPANIES ||--o{ BRANCHES : has
    COMPANIES ||--o{ USERS : employs
    COMPANIES ||--o{ CUSTOMERS : owns
    COMPANIES ||--o{ PROJECTS : develops
    COMPANIES ||--o| COMPANY_SUBSCRIPTIONS : subscribes
    SUBSCRIPTION_PLANS ||--o{ COMPANY_SUBSCRIPTIONS : defines

    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned
    ROLES ||--o{ ROLE_PERMISSIONS : has
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : granted

    PROJECTS ||--o{ BUILDINGS : contains
    BUILDINGS ||--o{ FLOORS : has
    FLOORS ||--o{ UNITS : contains

    CUSTOMERS ||--o{ LEADS : generates
    CUSTOMERS ||--o{ CUSTOMER_DOCUMENTS : uploads
    CUSTOMERS ||--o{ CUSTOMER_ACTIVITIES : timeline
    CUSTOMERS ||--o{ RESERVATIONS : makes
    CUSTOMERS ||--o{ CONTRACTS : signs

    UNITS ||--o{ RESERVATIONS : reserved
    RESERVATIONS ||--o| CONTRACTS : converts

    CONTRACTS ||--|| PAYMENT_PLANS : schedules
    PAYMENT_PLANS ||--o{ INSTALLMENTS : contains
    INSTALLMENTS ||--o{ PAYMENTS : receives

    BROKERS ||--o{ LEADS : refers
    BROKERS ||--o{ BROKER_COMMISSIONS : earns
    CONTRACTS ||--o{ BROKER_COMMISSIONS : generates

    COMPANIES ||--o{ CHART_OF_ACCOUNTS : maintains
    COMPANIES ||--o{ JOURNAL_ENTRIES : records
    JOURNAL_ENTRIES ||--o{ JOURNAL_LINES : details

    PROJECTS ||--o{ CONSTRUCTION_PHASES : phases
    CONSTRUCTION_PHASES ||--o{ CONSTRUCTION_TASKS : tasks
    PROJECTS ||--o{ CONSTRUCTION_MILESTONES : milestones

    COMPANIES ||--o{ VENDORS : manages
    VENDORS ||--o{ PURCHASE_ORDERS : fulfills
    COMPANIES ||--o{ WAREHOUSES : operates
    WAREHOUSES ||--o{ INVENTORY_ITEMS : stocks

    UNITS ||--o{ MAINTENANCE_REQUESTS : requires
    UNITS ||--o{ HANDOVER_RECORDS : delivered

    COMPANIES ||--o{ TICKETS : supports
    TICKETS ||--o{ TICKET_COMMENTS : discusses

    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ NOTIFICATIONS : receives
```

## Core Entity Attributes

### companies
`id, name_ar, name_en, code, status, storage_limit_mb, country`

### users
`id, company_id, email, system_role, is_super_admin, status`

### units
`id, floor_id, unit_code, unit_type, area_sqm, price, status, is_locked`

### contracts
`id, company_id, contract_number, customer_id, unit_id, total_price, status`

### installments
`id, payment_plan_id, due_date, due_amount, paid_amount, status`
