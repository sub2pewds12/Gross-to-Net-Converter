# Vietnam Gross Net Income Calculator (`vn_gross_net_calculator`)

This project provides a tool to calculate Vietnamese Net income from Gross income based on regulations applicable around **April 2025** (current date: Saturday, April 19, 2025 at 12:12 AM +07).

It includes:

1.  A core Python package (`core/`) for the calculation logic (Backend Logic).
2.  A web UI built with Streamlit (`frontend/app.py`) supporting single calculations and batch processing via Excel upload.
3.  A RESTful web API built with FastAPI (`api/`) to access the single calculation logic programmatically.

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
  * Batch calculation via **Excel file upload** (`.xlsx`, `.xls`).
  * Downloadable results (CSV, Excel).
* Provides a FastAPI Web API for single calculations (`POST /calculate/gross-to-net`).
* Includes Docker configuration (`Dockerfile`s and `docker-compose.yml`) for containerized development and deployment.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/sub2pewds12/Gross-to-Net-Converter
cd vn_gross_net_calculator
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

### 3. Install dependencies

#### Using uv (recommended)

```bash
pip install uv
uv pip install \
  "streamlit>=1.20.0" \
  "fastapi>=0.90.0" \
  "uvicorn[standard]>=0.20.0" \
  "pydantic>=2.0.0" \
  "pandas>=1.5.0" \
  "openpyxl>=3.0.0"
# Optional: For testing
uv pip install "pytest>=7.0.0" "requests>=2.20.0"
```

#### Using pip

```bash
# Install runtime and test dependencies from pyproject.toml
pip install .[test]

# Or just runtime dependencies
pip install .

# Or from requirements.txt
pip install -r requirements.txt
```

---

## Running the Application

### Option 1: Using Docker Compose (Recommended)

Ensure Docker is installed. In the project root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

- Web UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

To stop and clean up:

```bash
docker compose -f docker/docker-compose.yml down
```

### Option 2: Manually without Docker

#### Run API:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
Visit: http://localhost:8000/docs

#### Run Frontend:
```bash
streamlit run frontend/app.py
```
Visit: http://localhost:8501

### Option 3: Using Pre-Built Docker Images

Create a `docker-compose-run.yml`:

```yaml
services:
  api:
    image: leanhkhoi1010/vn-gross-net-api:latest
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    image: leanhkhoi1010/vn-gross-net-frontend:latest
    ports:
      - "8501:8501"
    depends_on:
      - api
    restart: unless-stopped
```

Run:
```bash
docker compose -f docker-compose-run.yml pull
docker compose -f docker-compose-run.yml up -d
```

To stop:
```bash
docker compose -f docker-compose-run.yml down
```

---

## Running Tests

Ensure dependencies are installed:

```bash
pytest
```

---

## Project Structure

```
vn_gross_net_calculator/
├── api/            # FastAPI application code
│   └── routers/
│       └── gross_net.py
├── core/           # Calculation logic
│   ├── calculator.py
│   ├── constants.py
│   └── models.py
├── docker/         # Docker config
├── frontend/       # Streamlit UI
│   └── app.py
├── tests/          # Automated tests
│   └── data/data_test_gross_net.xlsx
├── .gitignore
├── .dockerignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

@CCN-HUST
Computation & Communication Networking


