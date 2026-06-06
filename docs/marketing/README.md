# FRATELANZA Subscription Plans — Customer Brochure

## Customer demo screenshots (recommended — bilingual AR + EN)

**Folder:** `docs/demo-screenshots/` (26 PNG files)  
**Guides:** [DEMO-SCREENSHOTS-GUIDE.md](../DEMO-SCREENSHOTS-GUIDE.md) · [DEMO-SCREENSHOTS-GUIDE-AR.md](../DEMO-SCREENSHOTS-GUIDE-AR.md)

Every screenshot covers **one company module** (no Super Admin) with a **bilingual overlay** explaining all features in English and Arabic.

**Regenerate:**

```bash
./scripts/build-demo-screenshots.sh
# or: DEMO_URL=https://rs.fratelanza.com npm run demo-screenshots
```

**Login for capture:** `admin@demo.fratelanza.com` or `demo_admin` · password `Demo123456`

---

## Customer demo video (optional)

**File:** `fratelanza-customer-demo.mp4` (~3 min, Arabic UI)

```bash
./scripts/build-customer-demo-video.sh
```

Output: `/opt/cursor/artifacts/fratelanza-customer-demo.mp4`

---

## PDF for customer service

**File:** `fratelanza-subscription-plans.pdf`

Bilingual (English + Arabic) brochure with:

- All subscription plans (Basic, Professional, Enterprise)
- Monthly & yearly pricing in EGP
- User, project, and storage limits
- Full feature comparison matrix
- Payment terms (Net 30, trial, reminders)
- Customer service contact details

## How to get the latest PDF

### Option 1 — Super Admin UI

1. Log in as Super Admin
2. Go to **Subscription Plans**
3. Click **Download customer brochure (PDF)**

This pulls **live plan data** from the database (current prices and features).

### Option 2 — Regenerate locally (full design brochure)

```bash
./scripts/build-subscription-plans-pdf.sh
```

Output:

- `/opt/cursor/artifacts/fratelanza-subscription-plans.pdf` (rich HTML layout)
- `docs/marketing/fratelanza-subscription-plans.pdf` (copy for the repo)

Uses Playwright and optionally fetches live plans from the API.

### Option 3 — API

```
GET /api/v1/super-admin/subscription-plans/brochure.pdf
Authorization: Bearer <super_admin_token>
```

## Sharing with customers

Customer service can email the PDF or print it for meetings. Update plans in Super Admin first, then download a fresh brochure.
