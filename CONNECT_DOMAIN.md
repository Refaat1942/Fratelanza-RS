# Connect Your Domain to FRATELANZA

Your app runs on port **14136**. Your domain will point to it **without affecting other projects**.

**VPS IP:** `187.124.15.14`

---

## STEP 1 — DNS (Hostinger website)

1. Go to **https://hpanel.hostinger.com**
2. Click **Domains** → select your domain
3. Click **DNS / DNS Zone**
4. Add a new record:

| Type | Name | Points to | TTL |
|------|------|-----------|-----|
| **A** | `erp` | `187.124.15.14` | 3600 |

This creates: **erp.yourdomain.com** → your server

> Use any name you like instead of `erp` (e.g. `app`, `platform`, `rs`)

5. **Save** and wait **10–30 minutes**

---

## STEP 2 — Run on VPS (Hostinger Terminal)

Replace `erp.yourdomain.com` with your real domain:

```bash
cd /opt/fratelanza
git pull origin main
bash scripts/connect-domain.sh erp.yourdomain.com your@email.com
```

Example:
```bash
bash scripts/connect-domain.sh erp.fratelanza.com admin@fratelanza.com
```

---

## STEP 3 — Open your site

Go to: **https://erp.yourdomain.com**

Login same as before:
- Super Admin: `admin@fratelanza.com`
- Demo company: `admin@demo.fratelanza.com` / `Demo123456`

---

## Will this break my other projects?

**No.**

| Your other projects | FRATELANZA |
|---------------------|------------|
| Keep their domains  | Gets its own domain only |
| Keep port 80/443 sharing | Nginx routes by domain name |
| Unchanged files     | Only adds `fratelanza-*` nginx config |

---

## If SSL fails

DNS may not be ready. Wait 30 minutes, then run:

```bash
certbot --nginx -d erp.yourdomain.com
```

---

## Check DNS is working

```bash
ping erp.yourdomain.com
```

Should show IP: `187.124.15.14`
