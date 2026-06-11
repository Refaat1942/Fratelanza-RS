# VPS Deploy — Quick Reference

**Server:** `187.124.15.14` (srv1443693)  
**App folder:** `/opt/fratelanza`  
**URL:** https://rs.fratelanza.com  
**Port:** 9000 (production only)

---

## Update after code changes (use every time)

```bash
cd /opt/fratelanza
git fetch origin && git reset --hard origin/main
bash DEPLOY-VPS.sh
```

Wait 5–10 minutes. Hard-refresh browser: `Ctrl+Shift+R`.

---

## Verify deploy succeeded

```bash
curl -s http://127.0.0.1:9000/health
```

Good response includes `"git_commit":"..."` and `"release_features"`.

```bash
docker ps | grep fratelanza_
```

Must show:

| Container | Port |
|-----------|------|
| `fratelanza_nginx` | `0.0.0.0:9000->9000` |
| `fratelanza_backend` | internal |
| `fratelanza_postgres` | internal (no host 5432) |
| `fratelanza_redis` | internal |

---

## First-time install

```bash
git clone https://github.com/Refaat1942/Fratelanza-RS.git /opt/fratelanza
cd /opt/fratelanza
cp .env.production.example .env
nano .env
bash DEPLOY-VPS.sh
```

---

## Do not use on VPS

| Command | Why |
|---------|-----|
| `docker compose up -d --build` | Dev compose — binds port 5432, build fails |
| `docker compose down --remove-orphans` | Can remove Hub containers |

Hub and other projects stay running. Only the `fratelanza` compose project (port 9000) is updated.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `git pull` fails (diverged) | `git fetch origin && git reset --hard origin/main` |
| Build TypeScript error | Pull latest `main`, run `DEPLOY-VPS.sh` again |
| Old UI after deploy | `Ctrl+Shift+R` in browser |
| No `fratelanza_nginx` in `docker ps` | Deploy failed — read build output, re-run `DEPLOY-VPS.sh` |
