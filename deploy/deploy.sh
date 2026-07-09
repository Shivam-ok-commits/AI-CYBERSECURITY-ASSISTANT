#!/usr/bin/env bash
set -euo pipefail

# AI Cybersecurity Assistant — Cloud Deploy Script
# Usage:  ./deploy/deploy.sh [target]
# Targets: vm | railway | render | fly
# Default: vm (sets up a Linux VM with Docker + Compose)

TARGET="${1:-vm}"

case "$TARGET" in
  vm)
    echo "==> Deploying to VM..."
    echo "    Run this ON your VM (Ubuntu 22.04+):"

    cat <<'VMSCRIPT'
# === VM Setup Script ===
set -euo pipefail

# 1. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"

# 2. Clone repo
git clone https://github.com/YOUR_USER/ai-cybersecurity-assistant.git
cd ai-cybersecurity-assistant

# 3. Configure env
cp .env.example .env
nano .env  # Set JWT_SECRET_KEY and any API keys

# 4. Start with Docker Compose
sudo docker compose up -d --build

# 5. Verify
curl -f http://localhost/api/v1/health
echo "Deploy complete! Open http://YOUR_VM_IP/docs"
VMSCRIPT
    ;;

  railway)
    echo "==> Deploying to Railway..."
    echo "
    1. Push repo to GitHub
    2. Go to https://railway.com -> New Project -> Deploy from GitHub
    3. Select your repo
    4. Add these environment variables:
       - JWT_SECRET_KEY: <random string>
       - DATABASE_PATH: /data/assistant.db
    5. Set Start Command: uvicorn src.api:app --host 0.0.0.0 --port \$PORT
    6. Add a volume mount: /data
    7. Deploy!
    "
    ;;

  render)
    echo "==> Deploying to Render..."
    echo "
    1. Push repo to GitHub
    2. Go to https://render.com -> New Web Service
    3. Connect your repo
    4. Set:
       - Runtime: Docker
       - Build Command: (leave empty)
       - Start Command: (leave empty)
       - Health Check Path: /api/v1/health
    5. Add env vars:
       - JWT_SECRET_KEY: <random string>
    6. Add a Disk mount at /app/data (1 GB)
    7. Create Web Service
    "
    ;;

  fly)
    echo "==> Deploying to Fly.io..."
    echo "
    1. Install flyctl: curl -fsSL https://fly.io/install.sh | sh
    2. fly auth login
    3. fly launch --from Dockerfile
    4. fly secrets set JWT_SECRET_KEY=<random>
    5. fly volumes create app_data --size 1
    6. fly deploy
    "
    ;;

  *)
    echo "Usage: $0 [vm|railway|render|fly]"
    exit 1
    ;;
esac
