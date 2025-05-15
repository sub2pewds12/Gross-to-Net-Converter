# Vietnam Gross-to-Net Income Calculator (vn_gross_net_calculator)

**Date:** Thursday, May 15 2025  
**Location context:** Hanoi, Vietnam  

This project provides a complete toolkit for converting Vietnamese gross
income to net income under regulations current as of **April 2025**.  
It includes:

* **Core Python package** for calculation logic  
* **FastAPI** REST API  
* **Streamlit** web UI (with Excel batch support)  
* **PostgreSQL** persistence layer  
* **Docker + Docker Compose** for local/production parity  
* **GitHub Actions** CI/CD pipeline (tests → build → publish → deploy)

> **Disclaimer**  
> Figures are based on publicly available legislation (e.g. Decree 74/2024/ND-CP,  
> Resolution 954/2020/UBTVQH14) and common interpretations as of April 2025.  
> Always verify with official sources or a qualified professional.

---

## Features

| Layer | Highlights |
|-------|------------|
| **Core (`core/`)** | • Computes net income, PIT, BHXH, BHYT, BHTN<br>• Handles allowances & regional wage caps |
| **API (`api/`)**   | • `POST /calculate/gross-to-net` (single)<br>• `POST /calculate/batch-excel-upload` (batch)<br>• Full CRUD for saved calculations |
| **Frontend (`frontend/`)** | • Streamlit UI for single & batch runs<br>• Download CSV/XLSX<br>• Manage saved calculations |
| **Database** | PostgreSQL via SQLAlchemy ORM |
| **CI/CD** | Pytest, flake8/ruff, docker build & push, Render deploy |
| **Containers** | One-command spin-up with `docker compose` |

---

## Project Structure

```text
vn_gross_net_calculator/
├─ .github/workflows/ci-cd.yml
├─ api/
│  ├─ routers/
│  ├─ main.py
│  └─ wait_for_db.py
├─ core/
├─ docker/
│  ├─ api.Dockerfile
│  ├─ db.Dockerfile
│  ├─ frontend.Dockerfile
│  └─ docker-compose.yml
├─ frontend/app.py
├─ tests/
├─ README.md
└─ TROUBLESHOOTING.md
```

---

## Quick Start — Docker Compose (recommended)

```bash
# 1 clone
git clone https://github.com/sub2pewds12/gross-to-net-converter.git
cd gross-to-net-converter

# 2 spin everything up
docker compose -f docker/docker-compose.yml up --build

# 3 open
#   Frontend : http://localhost:8501
#   API docs : http://localhost:8000/docs
```

Stop with `Ctrl-C`, then `docker compose -f docker/docker-compose.yml down`.

---

## Local Python Run

```bash
# prerequisites: Python ≥3.10, PostgreSQL running separately

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# start API
uvicorn api.main:app --reload --port 8000

# new terminal → start Streamlit UI
streamlit run frontend/app.py
```

---

## CI/CD Pipeline (GitHub Actions)

1. **Test** → `pytest`  
2. **Lint/format** → ruff & black  
3. **Build** Docker images (`api`, `frontend`, `db`)  
4. **Push** to Docker Hub on `main`  
5. **Deploy** to Render via deploy-hook URLs  

Secrets required: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`,  
`RENDER_API_DEPLOY_HOOK_URL`, `RENDER_FRONTEND_DEPLOY_HOOK_URL`,  
`RENDER_DATABASE_DEPLOY_HOOK_URL`.

---

## Environment Variables (key ones)

| Variable      | Purpose                                 |
|---------------|-----------------------------------------|
| `DATABASE_URL`| PostgreSQL connection string            |
| `API_URL`     | Base URL used by Streamlit to reach API |
| `LOG_LEVEL`   | `DEBUG` / `INFO` / `WARNING` …          |
| *Render only* | See required secrets above              |

---

## Contributing

Fork → feature branch → pull request.  
Please include tests and pass linting before opening a PR.

---

## License

MIT License – see `LICENSE` for full text.
