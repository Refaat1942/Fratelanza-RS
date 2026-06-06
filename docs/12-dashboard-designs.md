# Dashboard Designs
# FRATELANZA REAL ESTATE PLATFORM

## 1. Super Admin Dashboard

### Layout
```
┌─────────────────────────────────────────────────┐
│  Header: Search | Language | Notifications      │
├──────────┬──────────────────────────────────────┤
│ Sidebar  │  KPI Cards (3 columns)               │
│          │  ┌────────┐ ┌────────┐ ┌────────┐    │
│ Companies│  │Companies│ │ Users  │ │Customers│   │
│ Users    │  └────────┘ └────────┘ └────────┘    │
│ Plans    │                                      │
│ Audit    │  Recent Activity Table               │
│ Settings │                                      │
└──────────┴──────────────────────────────────────┘
```

### KPIs
- Total Companies (active/suspended)
- Total Users across platform
- Total Customers across platform
- Revenue from subscriptions

## 2. Company Executive Dashboard

### Layout
```
┌─────────────────────────────────────────────────┐
│  KPI Row: Sales | Collections | Units | Leads │
├───────────────────────┬─────────────────────────┤
│  Sales Chart (Bar)    │  Lead Pipeline (Bars)   │
├───────────────────────┴─────────────────────────┤
│  Recent Reservations | Overdue Installments      │
└─────────────────────────────────────────────────┘
```

### KPIs
- Total Sales (EGP/SAR/AED)
- Total Collections
- Available Units
- Active Leads
- Overdue Amount
- Open Tickets

## 3. Sales Dashboard

- Pipeline funnel chart
- Lead source breakdown (pie)
- Agent performance ranking
- Conversion rate trend
- Upcoming follow-ups list

## 4. Collection Dashboard

- Due vs Paid chart
- Aging report (30/60/90 days)
- Collection forecast
- Top overdue customers
- Payment method breakdown

## 5. Finance Dashboard

- P&L summary
- Cash flow chart
- Receivables vs Payables
- Bank account balances
- Project profitability

## 6. Construction Dashboard

- Gantt chart overview
- Budget vs Actual
- Phase progress bars
- Delay alerts
- Risk indicators

## 7. Broker Dashboard

- Personal sales ranking
- Commission pipeline (pending/approved/paid)
- Lead conversion rate
- Active referrals

## 8. HR Dashboard

- Headcount by department
- Attendance summary
- Leave requests pending
- Payroll overview

## Chart Types Used

| Chart | Library | Use Case |
|-------|---------|----------|
| Bar | Recharts | Sales trends |
| Line | Recharts | Collection forecast |
| Pie | Recharts | Lead sources |
| Progress bars | Custom | Pipeline stages |
| Gantt | Planned | Construction timeline |

## Color Coding

- 🟢 Green: Positive trends, paid, active
- 🟡 Amber: Warning, due soon, pending
- 🔴 Red: Overdue, lost, suspended
- 🔵 Blue: Informational, new items
