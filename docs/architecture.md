
# Architecture

The system is organized as a data and serving pipeline. Raw CSV files are generated or supplied under `data/raw/`, validated by `backend.validation`, and cleaned by `backend.cleaning` into `data/processed/`. Weekly demand and leakage-safe features are produced by the preparation scripts. Forecasting modules provide baseline, Holt-Winters, and Random Forest models; `backend.pipeline` generates the configured four-week forecast. `backend.inventory_planning` and `backend.inventory_risk` convert forecasts and stock snapshots into reorder and risk decisions.

FastAPI exposes forecast, historical-demand, product, store, inventory, risk, and recommendation endpoints. PostgreSQL stores products, stores, sales, inventory, and forecasts using `sql/schema.sql`; `backend.forecast_persistence` performs forecast upserts. React/Vite consumes the API and renders forecast and inventory dashboards. `sql/powerbi_views.sql` provides reporting views for external BI tools.

Docker Compose runs PostgreSQL, FastAPI, and the React development server. PostgreSQL credentials come from `.env` variables, and the `postgres_data` named volume preserves database state across restarts. Airflow remains optional and isolated in `requirements-airflow.txt`.
