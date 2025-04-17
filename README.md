# Vietnam Gross Net Income Calculator (vn_gross_net_calculator)

This project provides a tool to calculate Vietnamese Net income from Gross income based on regulations applicable around **April 2025** (current date: Thursday, April 17, 2025 at 8:33:03 PM +07).

It includes:

1. A core Python package (`core/`) for the calculation logic (Backend Logic).
2. A simple web UI built with Streamlit (`frontend/app.py`).
3. A web API built with FastAPI (`api/`) to access the calculations programmatically.

> **Disclaimer:**  
> Calculation logic is based on publicly available information (e.g., Decree 74/2024/ND-CP, Resolution 954/2020/UBTVQH14, standard insurance rates) and interpretations current as of April 2025.  
> The base salary for the BHXH/BHYT cap uses 2,340,000 VND based on UI hints/potential reforms.  
> This tool is for informational purposes only. Always consult official sources or a qualified professional for financial decisions.  
> **Location context: Hanoi, Vietnam.**

---

## Features

- Calculates Net Income, Personal Income Tax (PIT), and mandatory insurance contributions (BHXH, BHYT, BHTN).
- Accounts for personal and dependent allowances.
- Considers regional minimum wages for insurance caps.
- Provides both a Streamlit Web UI (Frontend) and a FastAPI Web API.

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

#### Using `uv` (recommended)

```bash
pip install uv
uv pip install "streamlit>=1.20.0" "fastapi>=0.90.0" "uvicorn[standard]>=0.20.0" "pydantic>=2.0.0"
# To include test dependencies:
uv pip install "pytest>=7.0.0" "requests>=2.20.0" "pandas>=1.5.0" "openpyxl>=3.0.0"
```

#### Or using `pip`

```bash
# Install from pyproject.toml
pip install .

# Or for testing:
pip install .[test]

# Or from requirements.txt
pip install -r requirements.txt
```

---

## Running the Application

### 1. Frontend (Streamlit UI)

Run the Streamlit application:

```bash
streamlit run frontend/app.py
```

Then open your browser to the provided URL (usually [http://localhost:8501](http://localhost:8501)).

---

### 2. API (FastAPI)

Run the FastAPI application using Uvicorn:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- `--reload`: Automatically restarts the server on code changes (for development).
- `--host 0.0.0.0`: Makes the API accessible on your network (use `127.0.0.1` for localhost only).
- `--port 8000`: Port to serve the API.

Visit the API docs (Swagger UI) at: [http://localhost:8000/docs](http://localhost:8000/docs)

#### Example API Call (using curl)

```bash
curl -X POST "http://localhost:8000/calculate/gross-to-net" \
-H "Content-Type: application/json" \
-d '{
  "gross_income": 30000000,
  "num_dependents": 1,
  "region": 1
}'
```

---

## Running Tests

To run automated tests (requires `pytest`, and optionally `pandas`, `openpyxl`):

```bash
pytest
```

---

## Project Structure

```
vn_gross_net_calculator/
├── api/             # FastAPI application code (API Layer)
├── core/            # Core calculation logic (Backend Logic)
├── frontend/        # Streamlit UI (Frontend Layer)
├── tests/           # Automated tests
├── .gitignore
├── LICENSE
├── pyproject.toml   # Project configuration and dependencies
├── README.md
└── requirements.txt # Alternative dependency list
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

