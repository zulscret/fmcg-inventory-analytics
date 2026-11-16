-- ==============================================================================
-- PROJECT: FMCG Multi-Echelon Inventory Optimization & Distribution Center Analytics
-- AUTHOR: Muhammad Zulvan Yahya
-- MODULE: 03_service_level_otif.sql
-- PURPOSE: Operational Service Level (On-Time, In-Full, OTIF) and Lost Revenue analysis
-- ==============================================================================

-- 1. Distribution Center (DC) Performance Benchmark
SELECT 
    d.dc_name,
    d.province,
    d.service_region,
    COUNT(f.order_id) AS total_orders,
    SUM(f.is_on_time) AS on_time_orders,
    SUM(f.is_in_full) AS in_full_orders,
    SUM(f.is_otif) AS otif_orders,
    ROUND(SUM(f.is_on_time) * 100.0 / COUNT(f.order_id), 2) AS on_time_rate_pct,
    ROUND(SUM(f.is_in_full) * 100.0 / COUNT(f.order_id), 2) AS in_full_rate_pct,
    ROUND(SUM(f.is_otif) * 100.0 / COUNT(f.order_id), 2) AS otif_rate_pct,
    ROUND(SUM(f.revenue_realized_idr), 0) AS realized_sales_idr,
    ROUND(SUM(f.revenue_lost_idr), 0) AS lost_sales_due_to_stockout_idr,
    ROUND((SUM(f.revenue_lost_idr) * 100.0) / (SUM(f.revenue_realized_idr) + SUM(f.revenue_lost_idr)), 2) AS lost_revenue_pct
FROM fact_outbound_fulfillment f
JOIN dim_distribution_centers d ON f.dc_id = d.dc_id
GROUP BY d.dc_name, d.province, d.service_region
ORDER BY otif_rate_pct DESC;

-- 2. Monthly Service Level Trend
SELECT 
    SUBSTR(f.order_date, 1, 7) AS year_month,
    COUNT(f.order_id) AS total_orders,
    ROUND(SUM(f.is_on_time) * 100.0 / COUNT(f.order_id), 2) AS on_time_pct,
    ROUND(SUM(f.is_in_full) * 100.0 / COUNT(f.order_id), 2) AS in_full_pct,
    ROUND(SUM(f.is_otif) * 100.0 / COUNT(f.order_id), 2) AS otif_pct,
    ROUND(SUM(f.revenue_lost_idr), 0) AS total_lost_sales_idr
FROM fact_outbound_fulfillment f
GROUP BY SUBSTR(f.order_date, 1, 7)
ORDER BY year_month ASC;

-- 3. Category-Level Service Level & Stockout Impact
SELECT 
    p.category,
    COUNT(f.order_id) AS total_orders,
    ROUND(SUM(f.is_in_full) * 100.0 / COUNT(f.order_id), 2) AS in_full_pct,
    ROUND(SUM(f.is_otif) * 100.0 / COUNT(f.order_id), 2) AS otif_pct,
    ROUND(SUM(f.revenue_realized_idr), 0) AS realized_revenue_idr,
    ROUND(SUM(f.revenue_lost_idr), 0) AS lost_revenue_idr,
    SUM(f.lost_sales_qty) AS total_units_lost
FROM fact_outbound_fulfillment f
JOIN dim_products p ON f.sku_id = p.sku_id
GROUP BY p.category
ORDER BY lost_revenue_idr DESC;
