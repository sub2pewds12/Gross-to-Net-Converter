# Troubleshooting & Debugging Guide

Common problems and their fixes for the VN Gross-to-Net Calculator.

---

## 1. Local Docker Issues

### `docker compose: command not found`
* Docker Desktop/Engine not installed or not running.  
* On Linux install Compose plugin:  
  `sudo apt update && sudo apt install docker-compose-plugin`

### `failed to read dockerfile: open api.Dockerfile: no such file`
* Check `docker/docker-compose.yml` → correct `context:` and `dockerfile:` paths.  
* Filenames are case-sensitive on Linux.

### `ModuleNotFoundError` inside a container
* Missing dependency → add to `requirements.txt`, rebuild with  
  `docker compose -f docker/docker-compose.yml build <service>`  
* If error is `No module named 'core'` in **frontend**:  
  * Ensure `ENV PYTHONPATH=/app` and `COPY ./core /app/core` in `docker/frontend.Dockerfile`.

### Cannot reach `localhost:8000` or `:8501`
* Are containers running? `docker compose ps`  
* Ports mapped correctly in `docker-compose.yml`?  
* Check logs: `docker compose logs <service>`.

### API ↔ DB connection errors
* Verify `DATABASE_URL` uses host **`db`** (the service name).  
* Ensure DB health-check plus `condition: service_healthy` in `depends_on`.  
* Examine `db` logs for readiness.

### Code changes not reflected
* Confirm volume mounts, e.g.  
  ```yaml
  volumes:
    - ../:/app
  ```
* Using `--reload` (Uvicorn) or Streamlit should auto-reload in-container.

---

## 2. Render Deployment Issues

### Deploy/Build failed
* **Image pull:** wrong image name or private repo → adjust Render settings.  
* **Start-command:** must reference `$PORT`, e.g.  
  `uvicorn api.main:app --host 0.0.0.0 --port $PORT`  
* **Health-check:** path mismatch; app must answer before timeout.  
* **Env vars:** set `DATABASE_URL` (internal), `API_URL`, `PYTHONPATH=/app`.

### `ModuleNotFoundError: No module named 'core'` (Frontend)
* Add `ENV PYTHONPATH=/app` in Dockerfile **or** set in Render env.

### API cannot connect to PostgreSQL
* Use Render’s *internal* connection string for `DATABASE_URL` in API service.

---

## 3. Application-Specific Errors

### Excel batch upload fails
* File must be `.xlsx/.xls` with headers  
  `GrossIncome`, `Dependents`, `Region` (case-sensitive).  
* Check API logs for pandas / validation errors.

### HTTP 4xx / 5xx from API
* **400 / 422:** payload fails Pydantic validation – inspect `detail`.  
* **500:** unhandled server error – read API logs for stack-trace.

### Frontend cannot save / fetch calculations
* API down or `API_URL` incorrect.  
* Confirm API logs for matching error.

---

## 4. General Debugging Tips

1. **Read the logs first.**  
2. **Isolate** whether the issue is Frontend, API, or DB.  
3. **Verify env vars** in `.env`, `docker-compose.yml`, or Render.  
4. **Rebuild images** after dependency or Dockerfile changes.  
5. **Hard-refresh** browser (`Ctrl+Shift+R`) for UI glitches.  
6. **Test endpoints** directly with Swagger UI or `curl`.  
7. **IDE debugger** works when running services locally (Option 3 in README).

---
