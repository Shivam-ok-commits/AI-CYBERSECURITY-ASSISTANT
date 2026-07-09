# Cloud Deployment Guide

## Quick Start (Any Cloud VM)

```bash
# On a fresh Ubuntu 22.04+ VM:
curl -fsSL https://get.docker.com | sh
git clone https://github.com/YOUR_USER/ai-cybersecurity-assistant.git
cd ai-cybersecurity-assistant
cp .env.example .env
# Edit .env — set JWT_SECRET_KEY
docker compose up -d --build
```

Your API is now live at `http://YOUR_VM_IP:8000`.

---

## Option 1: Railway (Easiest)

1. Push the repo to GitHub
2. Go to [railway.com](https://railway.com) → **New Project** → **Deploy from GitHub**
3. Select your repo
4. Add environment variables (see `.env.example`)
5. Set start command: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
6. Add a **Volume** mounted at `/data` for persistence
7. Deploy — Railway auto-detects the Dockerfile

## Option 2: Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Select your repo
4. Set **Runtime** to `Docker`
5. Set **Health Check Path** to `/api/v1/health`
6. Add env vars from `.env.example`
7. Add a **Disk** mount at `/app/data` (1 GB)
8. Deploy

Render will auto-build from the Dockerfile.

## Option 3: Fly.io

```bash
# Install flyctl
curl -fsSL https://fly.io/install.sh | sh

# Login and launch
fly auth login
fly launch --from Dockerfile --name cybersec-assistant

# Set secrets
fly secrets set JWT_SECRET_KEY=$(openssl rand -base64 32)

# Add persistent volume
fly volumes create app_data --size 1
# Update fly.toml mount path to /app/data

# Deploy
fly deploy
```

## Option 4: Google Cloud Run

```bash
# Build and push
gcloud builds submit --config deploy/cloudbuild.yaml

# Or deploy directly
gcloud run deploy cybersec-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --set-env-vars "DEBUG=false" \
  --set-secrets "JWT_SECRET_KEY=jwt-secret:latest"
```

## Option 5: AWS ECS

Deploy via the `deploy/docker-compose.cloud.yml` to Amazon ECS:

```bash
# Install ecs-cli or use CDK
docker context create ecs cybersec
docker compose -f deploy/docker-compose.cloud.yml up
```

## Environment Variables

See `.env.example` for all config options. Required in all environments:

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Random string for token signing (required) |
| `DATABASE_PATH` | Path to SQLite DB (default: `/app/data/assistant.db`) |

## Production Checklist

- [ ] Set a strong `JWT_SECRET_KEY`
- [ ] Enable HTTPS (Nginx + Let's Encrypt, or Cloudflare)
- [ ] Set up automated DB backups
- [ ] Configure monitoring (health endpoint at `/api/v1/health`)
- [ ] Set resource limits (memory/CPU) on the container
- [ ] Use a managed database (PostgreSQL) for high availability
