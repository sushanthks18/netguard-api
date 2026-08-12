# NetGuard — Network Endpoint Health Monitor & CI/CD Pipeline

A containerized Flask API that tracks the health of network
endpoints (uptime + latency), raises incident alerts on degradation
or outage, and is deployed through a fully automated CI/CD pipeline.

## Architecture

```
Push to GitHub
      |
      v
+----------------+     +----------------+     +------------------+     +-------------+
|  CI: Lint +    | --> |  Build Docker  | --> | Push to GitHub   | --> | Deploy to   |
|  Pytest tests  |     |  image         |     | Container Reg.   |     | Render      |
+----------------+     +----------------+     +------------------+     +-------------+
```

This mirrors a real-world Sandbox -> Integration -> Pre-production ->
Production promotion flow: code only reaches the deployable image
after tests pass, and only reaches production after the image builds
cleanly.

## Stack

| Layer          | Tech                        |
|----------------|-----------------------------|
| App            | Python 3.11 + Flask         |
| Testing        | pytest                      |
| Container      | Docker                      |
| CI/CD          | GitHub Actions              |
| Registry       | GitHub Container Registry (ghcr.io) |
| Deploy target  | Render (free tier)          |

## Endpoints

| Method | Path                          | Purpose                                  |
|--------|--------------------------------|--------------------------------------------|
| GET    | `/health`                      | Liveness check                           |
| POST   | `/endpoints`                   | Register a network endpoint to monitor   |
| GET    | `/endpoints`                   | List all monitored endpoints             |
| POST   | `/endpoints/<id>/report`       | Report a health-check result (ping)      |
| GET    | `/endpoints/<id>/status`       | Current status + latency history         |
| GET    | `/incidents`                   | Active/triggered incidents               |

## Run locally

```bash
pip install -r requirements.txt
python app.py
# API now live at http://localhost:5000
```

## Run with Docker

```bash
docker build -t netguard-api .
docker run -p 5000:5000 netguard-api
```

## Run tests

```bash
pytest -v
```

## CI/CD Pipeline Stages

1. **Lint + Test** — every push/PR runs flake8 and pytest. A failing
   test blocks the pipeline from proceeding.
2. **Build + Push image** — on merge to `main`, a Docker image is
   built and pushed to GitHub Container Registry.
3. **Deploy** — a deploy hook triggers Render to pull and redeploy
   the latest image automatically.

## Why this project

Built to demonstrate incident-response monitoring logic plus
end-to-end CI/CD, containerization, and cloud deployment — directly
relevant to production network-function lifecycle management
(Sandbox -> Integration -> Pre-production -> Production) and
service-assurance metrics.
