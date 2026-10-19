SELECT p.product_id, p.product_name, p.category,
       AVG(s.unit_price)::numeric(12,2) AS average_price,
       MIN(s.unit_price)::numeric(12,2) AS minimum_price,
       MAX(s.unit_price)::numeric(12,2) AS maximum_price,
       AVG(s.units_sold)::numeric(12,2) AS average_units_sold
FROM sales s JOIN products p USING (product_id)
GROUP BY p.product_id, p.product_name, p.category
ORDER BY p.product_id;
