# UI Design System
# FRATELANZA REAL ESTATE PLATFORM

## Brand Identity

| Element | Value |
|---------|-------|
| Primary Color | `#0159a1` (Deep Blue) |
| Accent Color | `#d4a853` (Gold) |
| Background | `#f8fafc` (Slate 50) |
| Arabic Font | Cairo |
| English Font | Inter |

## Color Palette

### Primary (Blue)
- 50: `#f0f7ff` — Backgrounds
- 500: `#0c8ce9` — Links
- 700: `#0159a1` — Buttons, sidebar active
- 900: `#0b3f6e` — Headers

### Semantic
- Success: Emerald (`#059669`)
- Warning: Amber (`#d97706`)
- Error: Red (`#dc2626`)
- Info: Blue (`#2563eb`)

## Typography

| Element | Arabic | English | Size |
|---------|--------|---------|------|
| H1 | Cairo Bold | Inter Bold | 24-32px |
| H2 | Cairo SemiBold | Inter SemiBold | 20-24px |
| Body | Cairo Regular | Inter Regular | 14-16px |
| Caption | Cairo Light | Inter Light | 12px |

## Components

### Buttons
- **Primary**: Blue background, white text, rounded-lg
- **Secondary**: White background, border, slate text
- **Ghost**: Transparent, hover background

### Cards
- White background, border `slate-200`, rounded-xl, shadow-sm
- Padding: 24px (p-6)

### Inputs
- Border `slate-300`, rounded-lg
- Focus: primary border + ring
- RTL: text-align right, icon positioning via logical properties

### Sidebar
- Width: 256px (w-64)
- Active link: `primary-50` background
- Icons: Lucide React, 20px

### Tables
- Header: slate-500 text, border-bottom
- Rows: hover highlight
- Status badges: rounded-full pills

## Layout

### Desktop (≥1024px)
- Sidebar + Header + Content
- 4-column KPI grid

### Tablet (768-1023px)
- Collapsible sidebar
- 2-column KPI grid

### Mobile (<768px)
- Bottom navigation (planned)
- Single column layout
- Stacked cards

## RTL Guidelines

- Use `start`/`end` instead of `left`/`right`
- Mirror sidebar to right side in RTL
- Chart axes remain LTR for numbers
- Icons that imply direction should flip

## Dashboard Widgets

1. **StatCard** — KPI with icon and trend
2. **SalesChart** — Bar chart (Recharts)
3. **PipelineChart** — Horizontal progress bars
4. **DataTable** — Sortable, paginated lists

## Dark Mode
- `darkMode: 'class'` configured in Tailwind
- Toggle via system settings (planned)
