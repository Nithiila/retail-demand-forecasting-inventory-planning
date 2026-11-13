-- Power BI reporting layer. Run after schema.sql; views are read-only projections.
CREATE OR REPLACE VIEW bi_weekly_actual_vs_forecast AS
WITH actuals AS (
    SELECT date_trunc('week', sale_date)::date AS week_start, store_id, product_id,
           SUM(units_sold)::numeric AS actual_demand,
           SUM(units_sold * unit_price)::numeric(14,2) AS actual_revenue
    FROM sales GROUP BY 1, 2, 3
), forecasts AS (
    SELECT target_week AS week_start, store_id, product_id, model_name,
           predicted_demand, lower_bound, upper_bound
    FROM forecasts
)
SELECT COALESCE(a.week_start, f.week_start) AS week_start,
       COALESCE(a.store_id, f.store_id) AS store_id,
       COALESCE(a.product_id, f.product_id) AS product_id,
       a.actual_demand, a.actual_revenue, f.predicted_demand,
       f.lower_bound, f.upper_bound, f.model_name,
       CASE WHEN f.predicted_demand IS NULL THEN 'historical' ELSE 'forecast' END AS period_type
FROM actuals a FULL OUTER JOIN forecasts f USING (week_start, store_id, product_id);

CREATE OR REPLACE VIEW bi_sales_weekly AS
SELECT date_trunc('week', s.sale_date)::date AS week_start,
       s.store_id, st.store_name, st.city, st.region,
       s.product_id, p.product_name, p.category,
       SUM(s.units_sold)::numeric AS units_sold,
       SUM(s.units_sold * s.unit_price)::numeric(14,2) AS revenue,
       AVG(s.unit_price)::numeric(12,2) AS average_price,
       BOOL_OR(s.promotion) AS had_promotion
FROM sales s JOIN products p USING (product_id) JOIN stores st USING (store_id)
GROUP BY 1,2,3,4,5,6,7,8;

CREATE OR REPLACE VIEW bi_inventory_risk AS
WITH latest AS (
    SELECT DISTINCT ON (store_id, product_id) *
    FROM inventory ORDER BY store_id, product_id, snapshot_date DESC
), demand AS (
    SELECT store_id, product_id, AVG(predicted_demand)::numeric AS average_weekly_demand
    FROM forecasts GROUP BY 1,2
)
SELECT i.snapshot_date, i.store_id, st.store_name, i.product_id, p.product_name, p.category,
       i.stock_quantity, i.reorder_point, i.lead_time_days, i.unit_cost,
       COALESCE(d.average_weekly_demand, 0) AS average_weekly_demand,
       CASE WHEN COALESCE(d.average_weekly_demand,0)=0 THEN NULL
            ELSE i.stock_quantity / d.average_weekly_demand END AS coverage_weeks,
       CASE WHEN i.stock_quantity <= 0 THEN 'stockout'
            WHEN COALESCE(d.average_weekly_demand,0)>0 AND i.stock_quantity / d.average_weekly_demand < 0.5 THEN 'critical'
            WHEN COALESCE(d.average_weekly_demand,0)>0 AND i.stock_quantity / d.average_weekly_demand < 1 THEN 'warning'
            WHEN COALESCE(d.average_weekly_demand,0)>0 AND i.stock_quantity / d.average_weekly_demand > 8 THEN 'excess'
            ELSE 'normal' END AS risk_level,
       CASE WHEN i.stock_quantity <= 0 THEN i.reorder_point
            WHEN i.stock_quantity < i.reorder_point THEN i.reorder_point - i.stock_quantity
            ELSE 0 END AS recommended_order_quantity
FROM latest i JOIN products p USING (product_id) JOIN stores st USING (store_id)
LEFT JOIN demand d USING (store_id, product_id);
