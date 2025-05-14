# Troubleshooting & Debugging Guide

This guide provides solutions to common issues you might encounter while setting up, running, or deploying the VN Gross-to-Net Calculator application.

## 1. Local Development Issues (Docker Compose)

### Error: `docker compose` command not found (or `docker-compose` not found)
* **Symptom:** Terminal says `docker compose: command not found` or `docker-compose: command not found`.
* **Cause:**
    * Docker Desktop might not be running or its WSL integration is not enabled.
    * You might be using the wrong command (`docker-compose` vs `docker compose`). Modern Docker uses `docker compose` (with a space).
    * If using Docker Engine directly in WSL, the Docker Compose plugin might not be installed.
* **Solution:**
    * Ensure Docker Desktop is running and WSL Integration is enabled for your distro (Settings > Resources > WSL Integration).
    * Try `docker compose` (with a space).
    * If using Docker Engine in WSL directly, install the plugin: `sudo apt update && sudo apt install docker-compose-plugin`.

### Error: `failed to read dockerfile: open api.Dockerfile: no such file or directory`
* **Symptom:** Docker Compose fails during the build step with this error.
* **Cause:** Case sensitivity mismatch. The filename in your `docker-compose.yml` (e.g., `docker/api.Dockerfile`) does not exactly match the actual filename on your disk (e.g., it might be `docker/api.dockerfile`). Linux filesystems (used by WSL and Docker build runners) are case-sensitive.
* **Solution:**
    * Run `ls -l docker/` in your WSL terminal to see the exact filenames.
    * Ensure the `dockerfile:` entries in `docker/docker-compose.yml` precisely match these filenames, including capitalization. It's conventional to use `Dockerfile` (capital D).

### Error: `ModuleNotFoundError: No module named 'some_package'` inside container logs
* **Symptom:** API or Frontend container starts but then crashes, and logs show a `ModuleNotFoundError`.
* **Cause:**
    * The required Python package (e.g., `sqlalchemy`, `pandas`, `python-multipart`) is missing from your `requirements.txt` file.
    * The Docker image was not rebuilt after updating `requirements.txt`.
    * For `ModuleNotFoundError: No module named 'core'` specifically in the frontend: `ENV PYTHONPATH=/app` might be missing or incorrect in `frontend.Dockerfile`, or the `core` directory wasn't copied correctly.
* **Solution:**
    * Ensure all necessary dependencies are listed in `pyproject.toml` and accurately reflected in `requirements.txt`.
    * Rebuild the relevant image: `docker compose -f docker/docker-compose.yml build <service_name>` (e.g., `api` or `frontend`).
    * Then run `docker compose -f docker/docker-compose.yml up`.
    * For the `core` module error in frontend, verify `ENV PYTHONPATH=/app` and `COPY ["core", "/app/core"]` in `docker/frontend.Dockerfile`.

### Error: API or Frontend UI not accessible on `localhost`
* **Symptom:** `localhost:8000` or `localhost:8501` shows "This site can’t be reached."
* **Cause:**
    * Containers are not running: Check `docker compose -f docker/docker-compose.yml ps`.
    * Port mapping issue: Verify `ports:` section in `docker/docker-compose.yml`.
    * Application crash inside container: Check logs: `docker compose -f docker/docker-compose.yml logs <service_name>`.
    * Firewall blocking the port on your host machine.
    * Using `0.0.0.0` in the browser instead of `localhost` or `127.0.0.1`.
* **Solution:**
    * Ensure containers are up.
    * Check logs for errors.
    * Use `localhost:<port>` in your browser.
    * Temporarily disable firewall to test.

### Error: Database connection issues for API (e.g., `could not connect to server: Connection refused`)
* **Symptom:** API logs show errors related to connecting to PostgreSQL.
* **Cause:**
    * PostgreSQL container (`db` service in `docker-compose.yml`) is not running or hasn't started properly.
    * `DATABASE_URL` environment variable for the `api` service in `docker-compose.yml` is incorrect (e.g., wrong hostname, port, credentials). It should use the service name `db` as the host (e.g., `postgresql://user:pass@db:5432/dbname`).
    * `depends_on: - db` is missing for the `api` service in `docker-compose.yml`.
* **Solution:**
    * Check `db` container logs: `docker compose -f docker/docker-compose.yml logs db`.
    * Verify `DATABASE_URL` in `docker-compose.yml` for the `api` service.
    * Ensure `depends_on: - db` is present.

## 2. Render Deployment Issues

### Error: Deployment Failed (Check Render "Events" and "Logs")
* **Symptom:** Render dashboard shows "Deploy failed" or "Build failed".
* **Cause & Solution:**
    * **Image Pull Error:** Render couldn't pull your image from Docker Hub.
        * Verify the "Image Path" in Render service settings *exactly* matches your Docker Hub image name (e.g., `leanhkhoi1010/vn-gross-net-api:latest`).
        * Ensure the image is public on Docker Hub, or configure Render with credentials for private repositories.
    * **Start Command Error:** Your application failed to start inside the container on Render.
        * Check Render "Logs" for your service. Look for Python tracebacks or server startup errors.
        * Ensure your "Start Command" in Render settings is correct and uses the `$PORT` environment variable provided by Render (e.g., `uvicorn api.main:app --host 0.0.0.0 --port $PORT` or `streamlit run frontend/app.py --server.port $PORT --server.address=0.0.0.0 --server.headless=true`).
    * **Health Check Failures:** Render's health checks to `/health` (for API) or `/` (for Frontend) are failing.
        * Ensure these paths are correct in Render settings.
        * Check application logs on Render to see why it might not be responding successfully on those paths.
        * The application might be crashing before the health check can succeed.
    * **Resource Limits:** Free tier on Render has resource limits. If your app is too resource-intensive, it might fail to start or run stably. Check Render "Metrics".
    * **Missing Environment Variables:** If your app relies on environment variables (e.g., `PYTHONPATH=/app` for frontend, `DATABASE_URL` for API connecting to Render's managed DB), ensure they are correctly set in the "Environment" section of your service on Render.

### Error: `ModuleNotFoundError: No module named 'core'` (Frontend on Render)
* **Symptom:** Frontend service logs on Render show this error.
* **Cause:** Python inside the container cannot find your `core` package.
* **Solution:**
    * Ensure `ENV PYTHONPATH=/app` is in your `docker/frontend.Dockerfile`.
    * As a fallback or override, explicitly set the `PYTHONPATH` environment variable to `/app` in your Frontend service settings on Render.

### Error: Cannot connect to PostgreSQL on Render
* **Symptom:** API logs on Render show errors connecting to the database.
* **Cause:** The `DATABASE_URL` environment variable for your API service on Render is incorrect or not set.
* **Solution:**
    * When you create a managed PostgreSQL database on Render, it provides an "Internal Connection String" or "Database URL".
    * Copy this exact URL and set it as the value for the `DATABASE_URL` environment variable in your API service settings on Render.

## 3. Application Specific Errors

### Frontend: Excel Upload Errors
* **Symptom:** "File is not a zip file", "Missing required columns", errors during processing.
* **Cause:** The uploaded Excel file does not match the required format.
* **Solution:**
    * Refer to the detailed instructions within the Streamlit app's "Batch Upload (Excel)" tab.
    * Ensure the file is a valid `.xlsx` or `.xls` file (not a CSV renamed).
    * Verify column headers exactly match: `GrossIncome`, `Dependents`, `Region` (case-sensitive).
    * Check data types in each cell (numeric for GrossIncome, integer for Dependents and Region).
    * Check Render logs for the frontend service; it might show more specific errors from `pandas` or the calculation logic.

### API: 4xx or 5xx Errors
* **400 Bad Request / 422 Unprocessable Entity:** Usually means the data sent to the API endpoint (e.g., in a POST request) is malformed or fails Pydantic validation. Check the `detail` field in the API's JSON error response. Check API logs on Render for more info.
* **500 Internal Server Error:** Indicates an unhandled error occurred within the API's code. Check API logs on Render for Python stack traces to pinpoint the issue. This could be due to `CoreCalculationError`, `MissingConfigurationError`, or other unexpected exceptions.

## 4. General Debugging Tips

* **Check Logs First:** Whether local (via `docker compose logs`) or on Render, logs are your primary source of information. Look for error messages and Python tracebacks.
* **Isolate the Problem:** If both API and Frontend are failing, try to determine which one is the root cause. Can you access the API's `/docs` or `/health` endpoint directly?
* **Simplify:** If a complex feature isn't working, try a simpler version or test individual components.
* **Verify Environment Variables:** Ensure environment variables are correctly set and accessible in both local Docker environments (via `.env` and `docker-compose.yml`) and on Render.
* **Rebuild Images:** After code changes (especially dependencies or Dockerfile changes), always rebuild your Docker images (`docker compose -f docker/docker-compose.yml up --build`).
* **Hard Refresh Browser:** When testing UI changes, always do a hard refresh (`Ctrl+Shift+R` or `Cmd+Shift+R`) to avoid cached content.

This guide should help you diagnose and resolve common issues. Remember to consult the specific error messages and logs for the most direct clues.
