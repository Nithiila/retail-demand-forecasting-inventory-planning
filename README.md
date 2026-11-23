
# Retail Demand Forecasting and Inventory Planning

This project provides a FastAPI backend, React/Vite dashboard, PostgreSQL storage, weekly demand forecasting, inventory planning, risk classification, and Power BI-ready reporting views.

## Technologies and structure

- `backend/`: FastAPI routes, validation, cleaning, feature engineering, forecasting, inventory calculations, and PostgreSQL persistence.
- `frontend/`: React/Vite dashboard for forecasts, inventory, and risk actions.
- `data/raw/`: source CSV datasets; generated/cleaned outputs are written separately.
- `sql/`: PostgreSQL schema, analytics queries, and Power BI views.
- `scripts/`: data preparation, feature generation, model evaluation, and pipeline entry points.
- `airflow/`: optional Airflow orchestration; dependencies stay in `requirements-airflow.txt`.
- `tests/`: pure-logic tests and PostgreSQL-marked integration tests.

## Docker setup

Copy `.env.example` to `.env` and set a non-empty `POSTGRES_PASSWORD`. Then start all services:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

With the default local port mapping, services are available at `http://localhost:5174` (frontend), `http://localhost:8001/health` (backend), and PostgreSQL on port `5433`. PostgreSQL data persists in the `postgres_data` Docker volume. Do not use `docker compose down -v`.

The backend API is available under `/api/v1`:

- `GET /products` and `GET /stores` support paginated catalog lookups.
- `GET /forecasts` and `GET /demand-history` provide filtered weekly demand data.
- `GET /inventory`, `GET /inventory/risks`, and `GET /inventory/recommendations` provide inventory planning outputs.
- `POST /forecasts` persists a validated forecast batch using an upsert.

The React dashboard uses `VITE_API_BASE` to select the API base URL; it defaults to `http://localhost:8000/api/v1` for local development.

## Local setup and tests

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q -m "not db"
cd frontend
npm ci
npm test -- --run
npm run build
```

Start the backend locally with `uvicorn backend.main:app --reload --port 8000` and the frontend with `cd frontend; npm run dev`.

## Data regeneration sequence

Run the stages in this order:

```powershell
python scripts/generate_raw_data.py
python -c "from backend.validation import validate_raw_datasets; print(validate_raw_datasets('data/raw'))"
python -c "from backend.cleaning import clean_raw_datasets; print(clean_raw_datasets('data/raw','data/processed'))"
python -m backend.load_database
python scripts/train_random_forest.py
python scripts/run_forecast_pipeline.py
```

The sequence is: **Generate data → Validate → Clean → Load database → Train → Forecast**. Airflow users can run the equivalent dependency-ordered DAG after installing `requirements-airflow.txt` separately.
