# Vietnam Gross Net Income Calculator (vn_gross_net_calculator)

**Date:** Tuesday, May 13, 2025  
**Location Context:** Hanoi, Vietnam

This project provides a tool to calculate Vietnamese net income from gross income based on regulations applicable as of April 2025. It includes:

1. A core Python package (`core/`) for the calculation logic (Backend Logic).
2. A web UI built with Streamlit (`frontend/app.py`) supporting single calculations and batch processing via Excel upload.
3. A RESTful web API built with FastAPI (`api/`) to access the single calculation logic programmatically.
4. A CI/CD workflow using GitHub Actions to automate testing, building, and pushing Docker images to Docker Hub.

> **Disclaimer:**  
> Calculation logic is based on publicly available information (e.g., Decree 74/2024/ND-CP, Resolution 954/2020/UBTVQH14, standard insurance rates) and interpretations current as of April 2025.  
> The base salary for the BHXH/BHYT cap uses 2,340,000 VND based on UI hints/potential reforms.  
> This tool is for informational purposes only. Always consult official sources or a qualified professional for financial decisions.  
> **Location context: Hanoi, Vietnam.**

---

## Features

* Calculates Net Income, Personal Income Tax (PIT), and mandatory insurance contributions (BHXH, BHYT, BHTN).
* Accounts for personal and dependent allowances.
* Considers regional minimum wages for insurance caps.
* Provides a Streamlit Web UI (Frontend) with:
    * Single calculation input.
    * **Batch calculation via Excel file upload** (`.xlsx`, `.xls`).
    * Downloadable results (CSV, Excel).
* Provides a FastAPI Web API for single calculations (`POST /calculate/gross-to-net`).
* Includes Docker configuration (`Dockerfile`s and `docker-compose.yml`) for containerized development and deployment.
* Automated CI/CD pipeline using GitHub Actions for linting, testing, building, and pushing Docker images.

---

## Setup

### 1. Clone the repository (For Developers/Contributors)

If you intend to contribute to the code or run it from the source for development:

```bash
git clone https://github.com/sub2pewds12/Gross-to-Net-Calculator
cd vn_gross_net_calculator
````

### 2. Create a virtual environment (Recommended for local development without Docker)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

### 3. Install dependencies (Needed for manual running or local development outside Docker)

Ensure you have `pip` or `uv` available.

#### Using `uv` (Recommended)

```bash
pip install uv
# Install runtime dependencies including those for Excel feature and .env loading
uv pip install "streamlit>=1.20.0" "fastapi>=0.90.0" "uvicorn[standard]>=0.20.0" "pydantic>=2.0.0" "pandas>=1.5.0" "openpyxl>=3.0.0" "python-dotenv>=0.20.0"
# To include test and dev dependencies (like pytest, ruff):
# uv pip install "pytest>=7.0.0" "requests>=2.20.0" "ruff"
```

#### Or using `pip`

```bash
# Install runtime and test/dev dependencies from pyproject.toml
pip install .[test,dev]

# Or just runtime dependencies (ensure pandas, openpyxl, python-dotenv are listed in pyproject.toml's main deps):
# pip install .

# Or from requirements.txt (ensure it includes all necessary packages)
# pip install -r requirements.txt
```

---

## Running the Application

### Option 1: Using Docker Compose (For Development with Local Code)

Before testing any new feature, rebuild your containers locally by running:
```bash
docker compose -f docker/docker-compose.yml up --build -d
```
This ensures that all changes are picked up before you test the application.

This method runs both the API and the Web UI together in isolated containers using your **local source code** (changes to your code are reflected due to volume mounts). It's the recommended way for development if you have Docker installed and the source code cloned.

**Prerequisites:**

* Docker installed and running (e.g., Docker Desktop on Windows/Mac, or Docker Engine on Linux/WSL).
* Source code cloned (Step 1 in Setup).

**Steps:**

1. **Open a terminal** (like PowerShell, CMD, or your WSL terminal).
2. **Navigate to the project's main folder** (`vn_gross_net_calculator/`) where you cloned the repository. This folder contains the `docker/` subdirectory.
3. **(Optional, for local config) Create `.env` file:** If you want to use local environment variables (e.g., for `LOG_LEVEL`), copy `.env.example` to `.env` in the project root and modify it.
4. **Run the application:** Execute the following command:

   ```bash
   docker compose -f docker/docker-compose.yml up --build
   ```

   * This command tells Docker Compose to use the configuration file located at `docker/docker-compose.yml`.
   * It will build the necessary Docker images the first time you run it (or if Dockerfiles/dependencies change) using the `--build` flag.
   * It then starts both the API and the Frontend UI services, mounting your local code into the containers.
5. **Wait for Startup:** Wait a few moments until you see log messages indicating both servers (Uvicorn/Streamlit) are running, similar to:

   * `api-1     | INFO:     Uvicorn running on http://0.0.0.0:8000...`
   * `frontend-1|   URL: http://0.0.0.0:8501`
6. **Access the Applications:** Open your web browser:

   * **Web UI:** Go to `http://localhost:8501`
   * **API Docs (Optional):** Go to `http://localhost:8000/docs`
7. **Stop the Application:** When you are finished, go back to the terminal where the application is running and press `Ctrl+C`. Then, run the following command to clean up:

   ```bash
   docker compose -f docker/docker-compose.yml down
   ```

### Option 2: Running Pre-Built Images from Docker Hub (For End-Users or Simple Execution)

This option allows anyone with Docker installed to run the application using the pre-built images from Docker Hub (e.g., `leanhkhoi1010/vn-gross-net-api:latest`), without needing the source code.

**Prerequisites:**

* Docker installed and running.

**Steps:**

1. **Create `docker-compose-run.yml` file:** Create a *new file* in any directory on your computer (it doesn't need the project source code) and name it `docker-compose-run.yml`. Paste the following content into it:

   ```yaml
   # docker-compose-run.yml
   services:
     api:
       # Pulls the pre-built API image from Docker Hub
       image: leanhkhoi1010/vn-gross-net-api:latest # Replace leanhkhoi1010 with the actual Docker Hub username if different
       ports:
         - "8000:8000" # Maps host port 8000 to container port 8000
       environment: # Optional: Set environment variables for the deployed container
         - API_ENV=production
         - LOG_LEVEL=INFO
       restart: unless-stopped

     frontend:
       # Pulls the pre-built Frontend image from Docker Hub
       image: leanhkhoi1010/vn-gross-net-frontend:latest # Replace leanhkhoi1010 with the actual Docker Hub username if different
       ports:
         - "8501:8501" # Maps host port 8501 to container port 8501
       environment: # Optional: Set environment variables
         - API_ENV=production
         - LOG_LEVEL=INFO
         # - API_URL=https://<your-deployed-api-url>.onrender.com # Only if frontend calls the API
       depends_on:
         - api
       restart: unless-stopped
   ```

   *(Ensure the `image:` names exactly match your repositories on Docker Hub, using your username `leanhkhoi1010`).*

2. **Open a terminal** in the same directory where you saved `docker-compose-run.yml`.

3. **Pull Latest Images (Optional but good practice):** Download the latest images from Docker Hub:

   ```bash
   docker compose -f docker-compose-run.yml pull
   ```

4. **Run the Application:** Start the services using the images from Docker Hub:

   ```bash
   docker compose -f docker-compose-run.yml up -d
   ```

   *(Using `-d` runs the containers in the background).*

5. **Access Services:** Open your web browser:

   * Frontend UI: `http://localhost:8501`
   * API Docs: `http://localhost:8000/docs`

6. **Stop Services:** When finished, run the following command in the same directory where `docker-compose-run.yml` is located:

   ```bash
   docker compose -f docker-compose-run.yml down
   ```

### Option 3: Running Services Manually (Alternative - No Docker, Local Python Env)

Run the API and Frontend separately without Docker, directly using your local Python environment. Make sure you have completed Step 3 in the Setup section first (Install dependencies).

1. **Run API (FastAPI/Uvicorn):**

   * In one terminal (at project root, with virtual environment activated):

     ```bash
     uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
     ```
   * Access API docs at: `http://localhost:8000/docs`
2. **Run Frontend (Streamlit):**

   * In a *new* terminal (at project root, with virtual environment activated):

     ```bash
     streamlit run frontend/app.py
     ```
   * Access Frontend UI at: `http://localhost:8501`

---

## CI/CD with GitHub Actions

This project uses a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) to automate:

* **Linting & Formatting Checks:** Using Ruff.
* **Unit Testing:** Using Pytest.
* **Docker Image Building:** For both API and Frontend services.
* **Pushing to Docker Hub:** On pushes to the `main` branch, after successful tests and linting.

For the Docker Hub push to work, `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets must be configured in the GitHub repository settings.

---

## Running Tests

To run automated tests for the core logic (requires source code checkout and test dependencies installed):

```bash
pytest
```

---

## Project Structure

```
vn_gross_net_calculator/
├── api/            # FastAPI application code (API Layer)
│   ├── __init__.py
│   ├── main.py
│   └── routers/
│       ├── __init__.py
│       └── gross_net.py
│       └── saved_calculation_router.py
│
├── core/           # Core calculation logic package (Backend Logic)
│   ├── __init__.py
│   ├── calculator.py
│   ├── constants.py
│   ├── crud_saved_calculations.py
│   ├── database.py
│   ├── exceptions.py # Custom exceptions
│   └── models.py
│
├── docker/         # Docker configuration files
│   ├── api.Dockerfile
│   ├── frontend.Dockerfile
│   └── docker-compose.yml
│
├── frontend/       # Streamlit UI code (Frontend Layer)
│   └── app.py
│
├── tests/          # Automated tests
│   ├── __init__.py
│   ├── test_calculator.py
│   └── data/
│       └── data_test_gross_net.xlsx # Example test data file
│
├── .dockerignore   # Files to ignore for Docker builds
├── .gitignore      # Files to ignore for Git
├── LICENSE         # Project license
├── pyproject.toml  # Project configuration and dependencies (PEP 621)
├── README.md       # This file
├── requirements.txt # Alternative/generated dependency list
├── TROUBLESHOOTING.md

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

## Database Configuration

This project now uses a single PostgreSQL database container.  
Ensure that the environment variable is set accordingly. For example, the connection string should be:

```bash
postgresql://user:password@db:5432/dbname
```

Make sure to update your local `.env` file (or `.env.example`) with the above `DATABASE_URL` value.

