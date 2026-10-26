# Agent instructions — Fratelanza Real Estate

## Cursor Cloud specific instructions

### VPS production deploy (verified working)

On Hostinger VPS `/opt/fratelanza`:

```bash
cd /opt/fratelanza
git fetch origin && git reset --hard origin/main
bash DEPLOY-VPS.sh
```

- Uses `docker-compose.prod.yml` (port 14136, project `fratelanza_rs`).
- Does **not** stop Hub or other VPS projects.
- Never tell users to run `docker compose up -d --build` on the VPS (dev compose, port 5432 conflict).

### Verify deploy

```bash
curl -s http://127.0.0.1:14136/health   # expect git_commit + release_features
docker ps | grep fratelanza_rs_nginx      # expect 0.0.0.0:14136->9000
```

### URLs

| Role | URL |
|------|-----|
| Company admin | https://rs.fratelanza.com/login |
| Super admin | https://rs-control.fratelanza.com/super-admin |
| Buyer portal | https://rs.fratelanza.com/portal/login |
| Installment calculator | Collections → Installment Calculator tab |

Full reference: [docs/VPS-DEPLOY.md](docs/VPS-DEPLOY.md)
