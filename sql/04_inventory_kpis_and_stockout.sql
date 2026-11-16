-- ==============================================================================
-- PROJECT: FMCG Multi-Echelon Inventory Optimization & Distribution Center Analytics
-- AUTHOR: Muhammad Zulvan Yahya
-- MODULE: 04_inventory_kpis_and_stockout.sql
-- PURPOSE: Root-cause identification of top stockout SKUs and lost margin analysis
-- ==============================================================================

-- 1. Top 10 SKUs with Highest Revenue Loss from Stockouts
SELECT 
    f.sku_id,
    p.product_name,
    p.category,
    p.supplier_lead_time_days,
    COUNT(CASE WHEN f.lost_sales_qty > 0 THEN 1 END) AS stockout_incidents,
    SUM(f.ordered_qty) AS total_units_ordered,
    SUM(f.lost_sales_qty) AS total_units_unfulfilled,
    ROUND(SUM(f.lost_sales_qty) * 100.0 / SUM(f.ordered_qty), 2) AS unfulfilled_rate_pct,
    ROUND(SUM(f.revenue_lost_idr), 0) AS total_lost_revenue_idr,
    -- Estimated Gross Margin Lost (Assuming 20% average gross margin)
    ROUND(SUM(f.revenue_lost_idr) * 0.20, 0) AS estimated_lost_gross_profit_idr
FROM fact_outbound_fulfillment f
JOIN dim_products p ON f.sku_id = p.sku_id
GROUP BY f.sku_id, p.product_name, p.category, p.supplier_lead_time_days
ORDER BY total_lost_revenue_idr DESC
LIMIT 10;

-- 2. Distribution Center vs Category Stockout Heatmap Data
SELECT 
    d.dc_name,
    p.category,
    COUNT(f.order_id) AS total_shipments,
    SUM(CASE WHEN f.lost_sales_qty > 0 THEN 1 ELSE 0 END) AS stockout_count,
    ROUND(SUM(CASE WHEN f.lost_sales_qty > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(f.order_id), 2) AS stockout_frequency_pct,
    ROUND(SUM(f.revenue_lost_idr), 0) AS lost_sales_idr
FROM fact_outbound_fulfillment f
JOIN dim_distribution_centers d ON f.dc_id = d.dc_id
JOIN dim_products p ON f.sku_id = p.sku_id
GROUP BY d.dc_name, p.category
ORDER BY d.dc_name, lost_sales_idr DESC;
