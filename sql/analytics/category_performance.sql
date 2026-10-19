SELECT date_trunc('week', s.sale_date)::date AS week_start,
       p.category,
       SUM(s.units_sold)::integer AS units_sold,
       SUM(s.units_sold * s.unit_price)::numeric(14,2) AS revenue,
       COUNT(DISTINCT s.product_id) AS products_sold
FROM sales s JOIN products p USING (product_id)
GROUP BY 1, p.category
ORDER BY 1, p.category;
