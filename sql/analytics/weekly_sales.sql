-- Weekly demand by product and store. ISO weeks start on Monday.
SELECT date_trunc('week', sale_date)::date AS week_start,
       s.store_id, s.store_name, p.product_id, p.product_name, p.category,
       SUM(x.units_sold)::integer AS units_sold,
       SUM(x.units_sold * x.unit_price)::numeric(14,2) AS revenue,
       AVG(x.unit_price)::numeric(12,2) AS average_price,
       BOOL_OR(x.promotion) AS had_promotion
FROM sales x
JOIN stores s USING (store_id)
JOIN products p USING (product_id)
GROUP BY 1, s.store_id, s.store_name, p.product_id, p.product_name, p.category
ORDER BY 1, s.store_id, p.product_id;
