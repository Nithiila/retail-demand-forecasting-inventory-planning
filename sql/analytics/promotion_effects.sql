SELECT promotion,
       COUNT(*) AS observations,
       AVG(units_sold)::numeric(12,2) AS average_units,
       AVG(unit_price)::numeric(12,2) AS average_price,
       SUM(units_sold * unit_price)::numeric(14,2) AS revenue
FROM sales
GROUP BY promotion
ORDER BY promotion;
