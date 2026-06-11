# AGENTS.md

## Cursor Cloud specific instructions

Use **`sudo docker compose`** for all compose commands on Cloud Agent VMs.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |

Demo login: `admin@demo.fratelanza.com` / `Demo123456` (use **`username`** field in login API).

```bash
sudo docker compose up -d --build
sudo docker restart fratelanza_backend   # re-runs seed on startup
sudo docker exec fratelanza_frontend npm run build
```

### Document Management (`/documents`)

- API: `/api/v1/documents` — upload (multipart), list, download (auth-required), categories, summary
- Allowed types: PDF, JPEG, PNG, WebP, GIF (max 20 MB)
- Files stored under `uploads/documents/{company_id}/`; download via authenticated endpoint (not public static URLs)
- Module key: `documents` — included in Professional plan and above; seed syncs demo company modules from plan on startup
