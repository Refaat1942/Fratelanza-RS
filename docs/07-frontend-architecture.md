# Frontend Architecture
# FRATELANZA REAL ESTATE PLATFORM

## Tech Stack
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router v7** for routing
- **TanStack Query** for server state
- **Zustand** for client state (auth)
- **i18next** for internationalization
- **Recharts** for data visualization
- **Axios** for HTTP client

## Architecture Pattern

```
Pages → Components → Hooks/Stores → API Client → Backend
```

## Key Design Decisions

### 1. RTL/LTR Support
- `dir` attribute on `<html>` toggled dynamically
- Cairo font for Arabic, Inter for English
- Tailwind logical properties (`start`/`end`)

### 2. Authentication Flow
1. Login → JWT tokens stored in Zustand (persisted)
2. Axios interceptor attaches Bearer token
3. 401 responses trigger logout redirect

### 3. Route Structure
- `/login` — Public
- `/super-admin/*` — Super Admin only
- `/dashboard`, `/customers`, etc. — Company users

### 4. State Management
- **Server state**: TanStack Query (caching, refetch)
- **Auth state**: Zustand with localStorage persistence
- **UI state**: Local component state

### 5. Component Hierarchy
```
DashboardLayout
├── Sidebar (role-based navigation)
├── Header (search, language, notifications)
└── Page Content
    ├── StatCards
    ├── Charts (Recharts)
    └── Data Tables
```

## Module Pages

| Module | Route | Status |
|--------|-------|--------|
| Dashboard | /dashboard | ✅ Implemented |
| Customers | /customers | ✅ Implemented |
| Leads | /leads | ✅ Implemented |
| Super Admin | /super-admin | ✅ Implemented |
| AI Assistant | /ai-assistant | ✅ Implemented |
| Other modules | /finance, etc. | 🔲 Placeholder (API ready) |

## Build & Deploy
```bash
npm run build  # Production build to dist/
```
