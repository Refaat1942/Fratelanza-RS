# Production Deployment Guide
# FRATELANZA REAL ESTATE PLATFORM

## Prerequisites

- Linux VPS (Ubuntu 22.04+ recommended)
- Docker & Docker Compose
- Domain name with DNS configured
- SSL certificate (Let's Encrypt)

## 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y
```

## 2. Clone & Configure

```bash
git clone https://github.com/Refaat1942/Fratelanza-RS.git
cd Fratelanza-RS
cp .env.example .env
```

### Edit `.env` for production:
```env
APP_ENV=production
DEBUG=false
SECRET_KEY=<generate-64-char-random>
JWT_SECRET_KEY=<generate-64-char-random>
DATABASE_URL=postgresql+asyncpg://fratelanza:<strong-password>@postgres:5432/fratelanza_db
SUPER_ADMIN_EMAIL=admin@yourdomain.com
SUPER_ADMIN_PASSWORD=<strong-password>
CORS_ORIGINS=https://yourdomain.com
STORAGE_TYPE=s3
AWS_S3_BUCKET=fratelanza-uploads
```

## 3. SSL Configuration

```bash
# Install certbot
sudo apt install certbot -y
sudo certbot certonly --standalone -d yourdomain.com

# Copy certs to nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
```

Update `nginx/nginx.conf` to listen on 443 with SSL.

## 4. Deploy

```bash
docker compose up -d --build
```

### Verify:
```bash
curl http://localhost/health
curl http://localhost/api/v1/auth/me  # Should return 401
```

## 5. Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80, 443 | Reverse proxy |
| backend | 8000 | FastAPI API |
| frontend | 5173 | React dev (use build for prod) |
| postgres | 5432 | Database |
| redis | 6379 | Cache |

## 6. Production Frontend Build

For production, update `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

## 7. Database Backup

```bash
# Manual backup
docker exec fratelanza_postgres pg_dump -U fratelanza fratelanza_db > backup.sql

# Restore
docker exec -i fratelanza_postgres psql -U fratelanza fratelanza_db < backup.sql
```

### Automated (cron):
```bash
0 2 * * * docker exec fratelanza_postgres pg_dump -U fratelanza fratelanza_db | gzip > /backups/fratelanza_$(date +\%Y\%m\%d).sql.gz
```

## 8. Monitoring

- Health check: `GET /health`
- Docker logs: `docker compose logs -f backend`
- PostgreSQL: `docker exec fratelanza_postgres pg_isready`

## 9. Scaling

- **Horizontal**: Multiple backend containers behind Nginx load balancer
- **Database**: PostgreSQL read replicas
- **Cache**: Redis cluster
- **Storage**: AWS S3 or MinIO

## 10. Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall (ufw: 80, 443, 22 only)
- [ ] Disable PostgreSQL/Redis external ports
- [ ] Enable 2FA for Super Admin
- [ ] Configure automated backups
- [ ] Set up log rotation
- [ ] Enable HTTPS only
- [ ] Review CORS origins

## 11. Default Credentials (CHANGE IMMEDIATELY)

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@fratelanza.com | Admin@123456 |
| Demo Company Admin | admin@demo.fratelanza.com | Demo123456 |
