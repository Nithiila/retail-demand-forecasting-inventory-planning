
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE IF NOT EXISTS stores (
    store_id VARCHAR(32) PRIMARY KEY,
    store_name TEXT NOT NULL,
    city TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    sale_date DATE NOT NULL,
    store_id VARCHAR(32) NOT NULL REFERENCES stores(store_id),
    product_id VARCHAR(32) NOT NULL REFERENCES products(product_id),
    units_sold INTEGER NOT NULL CHECK (units_sold >= 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price > 0),
    promotion BOOLEAN NOT NULL DEFAULT FALSE,
    revenue NUMERIC(14, 2) GENERATED ALWAYS AS (units_sold * unit_price) STORED,
    PRIMARY KEY (sale_date, store_id, product_id)
);

CREATE TABLE IF NOT EXISTS inventory (
    snapshot_date DATE NOT NULL,
    store_id VARCHAR(32) NOT NULL REFERENCES stores(store_id),
    product_id VARCHAR(32) NOT NULL REFERENCES products(product_id),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
    unit_cost NUMERIC(12, 2) NOT NULL CHECK (unit_cost >= 0),
    PRIMARY KEY (snapshot_date, store_id, product_id)
);

CREATE TABLE IF NOT EXISTS forecasts (
    forecast_date DATE NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    store_id VARCHAR(32) NOT NULL REFERENCES stores(store_id),
    product_id VARCHAR(32) NOT NULL REFERENCES products(product_id),
    horizon_week SMALLINT NOT NULL CHECK (horizon_week BETWEEN 1 AND 52),
    predicted_units NUMERIC(14, 3) NOT NULL CHECK (predicted_units >= 0),
    lower_bound NUMERIC(14, 3) CHECK (lower_bound >= 0),
    upper_bound NUMERIC(14, 3) CHECK (upper_bound >= 0 AND (lower_bound IS NULL OR upper_bound >= lower_bound)),
    model_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (forecast_date, store_id, product_id, model_name)
);

CREATE INDEX IF NOT EXISTS idx_sales_product_date ON sales(product_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_store_date ON sales(store_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_date ON forecasts(forecast_date);
