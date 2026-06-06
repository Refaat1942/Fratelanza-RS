# Software Requirements Specification (SRS)
# FRATELANZA REAL ESTATE PLATFORM

## 1. Introduction

### 1.1 Purpose
This document specifies functional and non-functional requirements for the FRATELANZA platform.

### 1.2 Scope
Cloud SaaS application covering real estate development lifecycle from lead acquisition to post-sales property management.

## 2. Functional Requirements

### 2.1 Super Admin Module (FR-SA)
| ID | Requirement |
|----|-------------|
| FR-SA-01 | Create, update, suspend companies |
| FR-SA-02 | Manage subscription plans and storage limits |
| FR-SA-03 | Create users across all companies |
| FR-SA-04 | View global dashboards and audit logs |
| FR-SA-05 | Export any data (Excel, PDF, CSV) |
| FR-SA-06 | Database backup and restore |
| FR-SA-07 | Manage system themes and languages |

### 2.2 CRM & Sales (FR-CRM)
| ID | Requirement |
|----|-------------|
| FR-CRM-01 | Lead capture from 9+ sources |
| FR-CRM-02 | Pipeline stages: New → Contract Signed / Lost |
| FR-CRM-03 | Lead assignment and scoring |
| FR-CRM-04 | AI lead qualification |
| FR-CRM-05 | Activity tracking and follow-up reminders |

### 2.3 Real Estate Structure (FR-RE)
| ID | Requirement |
|----|-------------|
| FR-RE-01 | Hierarchy: Company → Project → Building → Floor → Unit |
| FR-RE-02 | 11 unit types supported |
| FR-RE-03 | 6 unit statuses with locking mechanism |
| FR-RE-04 | Unit images and attachments |

### 2.4 Reservations (FR-RES)
| ID | Requirement |
|----|-------------|
| FR-RES-01 | Prevent double reservation |
| FR-RES-02 | Automatic unit locking |
| FR-RES-03 | Expiry-based auto-release |
| FR-RES-04 | Approval workflow |

### 2.5 Contracts & Collections (FR-CON)
| ID | Requirement |
|----|-------------|
| FR-CON-01 | Auto-generate Arabic/English contracts |
| FR-CON-02 | Electronic signature support |
| FR-CON-03 | Payment plan types: Monthly to Custom |
| FR-CON-04 | Installment status tracking |
| FR-CON-05 | Multi-channel notifications |

### 2.6 Additional Modules
- Broker Portal (FR-BRK)
- Customer Portal (FR-CUS)
- Property Management (FR-PM)
- Construction Management (FR-CM)
- Procurement & Warehouse (FR-PR, FR-WH)
- Finance & Accounting (FR-FIN)
- HR System (FR-HR)
- Customer Service (FR-CS)
- AI Features (FR-AI)
- Business Intelligence (FR-BI)

## 3. Non-Functional Requirements

### 3.1 Performance
- API response < 200ms for 95th percentile
- Support 1000 concurrent users per deployment

### 3.2 Security
- JWT authentication with refresh tokens
- RBAC with 17 predefined roles
- 2FA (TOTP)
- Audit and activity logs
- IP restrictions (configurable)

### 3.3 Localization
- Arabic RTL (primary)
- English LTR (secondary)
- Dynamic language switching
- Bilingual reports and contracts

### 3.4 Scalability
- Multi-tenant data isolation
- Redis caching
- S3-compatible file storage
- Horizontal scaling via Docker

### 3.5 Availability
- Docker-based deployment
- Health check endpoints
- Automated backup system

## 4. User Roles

Super Admin, Company Admin, CEO, Managing Director, Sales Director, Sales Manager, Sales Agent, Customer Service, Collection Officer, Accountant, Finance Manager, Procurement Officer, Project Manager, Engineer, HR Manager, Broker, Customer

## 5. External Interfaces

- Email (SMTP)
- SMS API
- WhatsApp Business API
- AWS S3 / compatible storage
- Payment gateways (future)

## 6. Constraints

- Tech stack: React, TypeScript, Tailwind, FastAPI, PostgreSQL, Redis
- Deployment: Docker, Nginx, Linux VPS
