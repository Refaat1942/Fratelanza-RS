# START HERE — Deploy FRATELANZA (3 steps only)

I cannot log into your server without your password.  
You only need to do **3 simple things** below.

---

## STEP 1 — Open port 9000 (in Hostinger website)

1. Go to https://hpanel.hostinger.com
2. Click **VPS**
3. Click your server
4. Click **Security** (left menu)
5. Click **Add rule** or **Firewall**
6. Add:
   - Port: **9000**
   - Protocol: **TCP**
7. Save

---

## STEP 2 — Open Terminal on your computer

**Windows:** Press `Win + R`, type `cmd`, press Enter

**Mac:** Press `Cmd + Space`, type `Terminal`, press Enter

Type this and press Enter:

```
ssh root@187.124.15.14
```

When it asks for password, type your **VPS root password** (you won't see letters while typing — that's normal). Press Enter.

---

## STEP 3 — Copy and paste this ONE block

After you are logged in to the server, copy **ALL** of this and paste it into the terminal, then press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/Refaat1942/Fratelanza-RS/cursor/hostinger-deploy-all-phases-8cb9/scripts/easy-install.sh | bash
```

Wait 3–5 minutes. When finished, it will show your login password.

---

## STEP 4 — Open the website

Go to: **http://187.124.15.14:9000**

| Email | Password |
|-------|----------|
| admin@fratelanza.com | Shown at end of install (also in `/opt/fratelanza/LOGIN_PASSWORD.txt` on server) |

---

## Need help?

Send me:
1. A screenshot of what you see after Step 2 or Step 3
2. Or your VPS root password (if you trust sharing it) and I can try again

---

## Don't have VPS password?

1. Hostinger → VPS → your server
2. Click **Settings** or **Reset root password**
3. Set a new password
4. Try Step 2 again
