# Windows EXE Build and Operation

This document explains how to run the Fratelanza Admin Console on your laptop
and how to build customer EXEs that do not require SQL Server on customer
devices.

## 1. Pull latest code on your laptop

Open CMD inside the project folder:

```bat
git pull origin cursor/fratelanza-business-suite-becb
```

If Git blocks because of local `.env.example` changes:

```bat
git stash push -m "local env example" .env.example
git pull origin cursor/fratelanza-business-suite-becb
```

## 2. Run admin console without building EXE

Use this first for testing:

```bat
.venv\Scripts\activate
pip install -e ".[exe]"
set FRATELANZA_ADMIN_API_BASE_URL=https://your-vps-domain.com
set FRATELANZA_ADMIN_KEY=your-private-admin-key
fratelanza-admin
```

If your VPS API is not deployed yet, the admin console will open but requests
will fail until the backend is running.

## 3. Build admin EXE on your laptop

```bat
scripts\build_admin_exe.bat
```

Output:

```text
dist\FratelanzaAdminConsole\FratelanzaAdminConsole.exe
```

Create/edit this file:

```text
dist\FratelanzaAdminConsole\.env
```

Content:

```env
FRATELANZA_ADMIN_API_BASE_URL=https://your-vps-domain.com
FRATELANZA_ADMIN_KEY=your-private-admin-key
```

Then run:

```bat
dist\FratelanzaAdminConsole\FratelanzaAdminConsole.exe
```

## 4. Build customer EXE

```bat
scripts\build_customer_exe.bat
```

Output:

```text
dist\FratelanzaBusinessSuite\FratelanzaBusinessSuite.exe
```

For each customer, create/edit:

```text
dist\FratelanzaBusinessSuite\.env
```

Example customer:

```env
FRATELANZA_DATA_MODE=hybrid_offline
FRATELANZA_REMOTE_ENABLED=true
FRATELANZA_REMOTE_API_BASE_URL=https://your-vps-domain.com
FRATELANZA_REMOTE_API_KEY=customer-secret-key-from-admin-console
FRATELANZA_REMOTE_CLIENT_ID=CUST-001
FRATELANZA_REMOTE_INSTALLATION_ID=CUST-001-PC-001
FRATELANZA_REMOTE_DISABLE=true
FRATELANZA_REMOTE_OFFLINE_GRACE_HOURS=72
FRATELANZA_CURRENCY=EGP
```

Customer runs:

```bat
dist\FratelanzaBusinessSuite\FratelanzaBusinessSuite.exe
```

The customer does not install SQL Server. The EXE talks to your VPS API.

## 5. VPS backend quick start

On your VPS:

```bash
curl -fsSL https://raw.githubusercontent.com/Refaat1942/Fratelanza-LMP/cursor/fratelanza-business-suite-becb/scripts/deploy_vps_api.sh | bash
```

The script deploys the API on internal port `1058`, configures Nginx on port
`80`, prints the admin key, and prints the exact `.env` lines for the Admin EXE.

Then put it behind HTTPS with your VPS domain before selling to customers.
