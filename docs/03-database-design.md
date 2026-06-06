# Database Design Document
# FRATELANZA REAL ESTATE PLATFORM

## 1. Design Principles

- **Multi-tenancy**: `company_id` on all tenant-scoped tables
- **Soft deletes**: `is_deleted`, `deleted_at` on core entities
- **Audit trail**: `created_at`, `updated_at` on all tables
- **Normalization**: 3NF with strategic denormalization for dashboards
- **Indexing**: Foreign keys, search fields, status columns indexed

## 2. Schema Domains

### 2.1 Tenant & Subscription
- `companies` — Developer companies
- `branches` — Company branches
- `subscription_plans` — SaaS pricing tiers
- `company_subscriptions` — Active subscriptions

### 2.2 Identity & Access
- `users` — All platform users
- `roles` — Custom roles per company
- `permissions` — Module.action permissions
- `user_roles` — User-role mapping
- `role_permissions` — Role-permission mapping

### 2.3 CRM & Customers
- `customers` — Customer profiles
- `customer_documents` — Uploaded documents
- `customer_activities` — Timeline events
- `leads` — Sales leads
- `lead_activities` — Lead interactions

### 2.4 Real Estate
- `projects` — Development projects
- `buildings` — Towers/buildings
- `floors` — Floor levels
- `units` — Sellable units

### 2.5 Sales
- `reservations` — Unit reservations
- `contracts` — Sales contracts
- `payment_plans` — Installment schedules
- `installments` — Individual dues
- `payments` — Payment records

### 2.6 Brokers
- `brokers` — Broker profiles
- `broker_commissions` — Commission tracking

### 2.7 Finance
- `chart_of_accounts` — COA
- `journal_entries` / `journal_lines` — GL entries
- `bank_accounts` — Bank management

### 2.8 Operations
- `employees`, `attendance`, `leave_requests` — HR
- `construction_phases`, `construction_tasks`, `construction_milestones` — Construction
- `vendors`, `rfqs`, `purchase_orders` — Procurement
- `warehouses`, `inventory_items`, `stock_movements` — Warehouse
- `maintenance_requests`, `handover_records` — Property Management
- `tickets`, `ticket_comments` — Customer Service

### 2.9 System
- `audit_logs` — Security audit
- `notifications` — Multi-channel notifications
- `documents` — Document management
- `system_settings` — Global configuration

## 3. Key Relationships

```
companies 1──N branches
companies 1──N users
companies 1──N customers
companies 1──N projects
projects 1──N buildings
buildings 1──N floors
floors 1──N units
customers 1──N reservations
units 1──N reservations
reservations 0..1──1 contracts
contracts 1──1 payment_plans
payment_plans 1──N installments
installments 1──N payments
```

## 4. Data Isolation

- Super Admin: No `company_id` filter
- Company users: All queries filtered by `company_id`
- Row-level security enforced at application layer

## 5. Storage Estimates

| Entity | Est. rows/company/year |
|--------|------------------------|
| Customers | 5,000 |
| Leads | 10,000 |
| Units | 2,000 |
| Payments | 20,000 |
| Audit logs | 50,000 |
