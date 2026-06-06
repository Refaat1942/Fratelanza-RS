#!/bin/bash
set -e

echo "🚀 FRATELANZA Platform Setup"
echo "=============================="

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

echo "📦 Starting Docker services..."
docker compose up -d --build

echo "⏳ Waiting for services..."
sleep 10

echo "🔍 Health check..."
curl -sf http://localhost:8000/health && echo " ✅ Backend healthy" || echo " ❌ Backend not ready"
curl -sf http://localhost:5173 > /dev/null && echo " ✅ Frontend running" || echo " ❌ Frontend not ready"

echo ""
echo "=============================="
echo "🎉 Setup complete!"
echo ""
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Super Admin: admin@fratelanza.com / Admin@123456"
echo "Demo Admin:  admin@demo.fratelanza.com / Demo123456"
echo "=============================="
