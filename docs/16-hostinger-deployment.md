# Hostinger VPS Deployment Guide
# FRATELANZA on Port 9000 + Custom Domain

## Server Info

| Item | Value |
|------|-------|
| VPS IP | `187.124.15.14` |
| OS | Ubuntu 24.04 LTS |
| SSH | `ssh root@187.124.15.14` |
| App Port | **9000** (isolated from other projects) |

## Architecture

```
Internet
    │
    ├── Other projects (ports 80, 443, 3000, etc.)
    │
    └── FRATELANZA (port 9000) ← isolated Docker network
            │
            ├── nginx:9000 (frontend + API proxy)
            ├── backend:8000 (internal only)
            ├── postgres (internal only)
            └── redis (internal only)
```

**Domain option A** — Direct access: `http://187.124.15.14:9000`  
**Domain option B** — Custom domain: `https://erp.yourdomain.com` → proxies to port 9000

## Step 1: DNS Configuration

In your domain registrar (Hostinger DNS or external):

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | erp | 187.124.15.14 | 3600 |

Or for root domain:
| Type | Name | Value |
|------|------|-------|
| A | @ | 187.124.15.14 |

> Use a **subdomain** (e.g., `erp.yourdomain.com`) to keep FRATELANZA separate from other VPS projects.

## Step 2: Hostinger Firewall

In Hostinger Panel → VPS → **Security**:

1. Add inbound rule: **TCP port 9000** (FRATELANZA)
2. Keep existing rules for other projects unchanged

## Step 3: Deploy on VPS (verified working)

```bash
ssh root@187.124.15.14
cd /opt/fratelanza
git fetch origin && git reset --hard origin/main
bash DEPLOY-VPS.sh
```

**First-time install:**

```bash
ssh root@187.124.15.14
git clone https://github.com/Refaat1942/Fratelanza-RS.git /opt/fratelanza
cd /opt/fratelanza
cp .env.production.example .env
nano .env   # Set strong passwords!
bash DEPLOY-VPS.sh
```

**What `DEPLOY-VPS.sh` does:**

1. Syncs code to `origin/main` (`git reset --hard`)
2. Stops accidental dev compose (does **not** stop Hub)
3. Rebuilds production `nginx` + `backend` (`docker-compose.prod.yml`)
4. Starts stack on port **9000** only

**Verify:**

```bash
curl -s http://127.0.0.1:9000/health
# {"status":"healthy","git_commit":"...","release_features":[...]}

docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep fratelanza_
# fratelanza_nginx   0.0.0.0:9000->9000/tcp
```

**Do NOT use on VPS:**

```bash
docker compose up -d --build          # WRONG — dev file, port 5432 conflict
docker compose down --remove-orphans  # WRONG — can affect Hub
```

## Step 4: Configure .env

```env
APP_PORT=9000
DOMAIN=erp.yourdomain.com
POSTGRES_PASSWORD=<strong-password>
SECRET_KEY=<random-64-chars>
JWT_SECRET_KEY=<random-64-chars>
SUPER_ADMIN_PASSWORD=<strong-password>
CORS_ORIGINS=https://erp.yourdomain.com,http://187.124.15.14:9000
```

## Step 5: Connect Domain (Optional)

```bash
cd /opt/fratelanza
./scripts/setup-domain-proxy.sh erp.yourdomain.com
```

This creates an **isolated** nginx config that proxies only your FRATELANZA domain to port 9000, without affecting other projects.

## Step 6: Verify

```bash
# Health check
curl http://localhost:9000/health

# From your PC
curl http://187.124.15.14:9000/health

# Login
# http://187.124.15.14:9000
# admin@fratelanza.com / (your SUPER_ADMIN_PASSWORD)
```

## Management Commands

```bash
cd /opt/fratelanza

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Update
git pull && docker compose -f docker-compose.prod.yml up -d --build

# Backup database
docker exec fratelanza_postgres pg_dump -U fratelanza fratelanza_db > backup.sql
```

## Isolation from Other Projects

| Feature | How |
|---------|-----|
| Separate port | 9000 only |
| Separate Docker network | `fratelanza_isolated_net` |
| Separate volumes | `fratelanza_postgres`, etc. |
| Separate nginx config | `fratelanza-{domain}` site |
| No shared DB | Own PostgreSQL container |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 9000 blocked | Open in Hostinger firewall + `ufw allow 9000` |
| Can't connect | `docker compose -f docker-compose.prod.yml ps` |
| 502 Bad Gateway | Wait 30s for backend startup, check logs |
| CORS error | Add domain to `CORS_ORIGINS` in `.env` |
| `rs.fratelanza.com` or `rs-control.fratelanza.com` opens Fratelanza Hub | Run `bash scripts/fix-rs-domain.sh` on the VPS — fixes both domains to port 9000 (Hub stays at hub.fratelanza.com) |
