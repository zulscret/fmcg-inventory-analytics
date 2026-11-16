-- ==============================================================================
-- PROJECT: FMCG Multi-Echelon Inventory Optimization & Distribution Center Analytics
-- AUTHOR: Muhammad Zulvan Yahya
-- MODULE: 02_abc_xyz_analysis.sql
-- PURPOSE: Multi-dimensional ABC-XYZ Matrix segmentation for targeted inventory policy
-- ==============================================================================

WITH sku_sales_agg AS (
    SELECT 
        f.sku_id,
        p.product_name,
        p.category,
        p.unit_cost_idr,
        p.selling_price_idr,
        p.supplier_lead_time_days,
        p.supplier_lt_stddev,
        SUM(f.ordered_qty) AS total_units_demanded,
        SUM(f.shipped_qty) AS total_units_shipped,
        SUM(f.revenue_realized_idr) AS total_revenue_idr,
        AVG(f.ordered_qty) AS avg_daily_demand,
        -- Sample standard deviation calculation: sqrt(avg(x^2) - avg(x)^2)
        SQRT(AVG(f.ordered_qty * f.ordered_qty) - (AVG(f.ordered_qty) * AVG(f.ordered_qty))) AS stddev_daily_demand
    FROM fact_outbound_fulfillment f
    JOIN dim_products p ON f.sku_id = p.sku_id
    GROUP BY f.sku_id, p.product_name, p.category, p.unit_cost_idr, p.selling_price_idr, p.supplier_lead_time_days, p.supplier_lt_stddev
),

abc_ranked AS (
    SELECT 
        *,
        -- Cumulative revenue over total revenue across all SKUs
        SUM(total_revenue_idr) OVER (ORDER BY total_revenue_idr DESC) AS cum_revenue_idr,
        SUM(total_revenue_idr) OVER () AS grand_total_revenue_idr,
        ROUND(
            (SUM(total_revenue_idr) OVER (ORDER BY total_revenue_idr DESC) * 100.0) / 
            SUM(total_revenue_idr) OVER (), 2
        ) AS cum_revenue_pct,
        -- Coefficient of Variation (CV) = StdDev / Mean
        ROUND(stddev_daily_demand / avg_daily_demand, 3) AS coefficient_of_variation
    FROM sku_sales_agg
),

matrix_segmented AS (
    SELECT 
        sku_id,
        product_name,
        category,
        total_revenue_idr,
        cum_revenue_pct,
        avg_daily_demand,
        stddev_daily_demand,
        supplier_lead_time_days,
        supplier_lt_stddev,
        coefficient_of_variation,
        -- ABC Classification based on 80/15/5 Pareto rule
        CASE 
            WHEN cum_revenue_pct <= 80.0 THEN 'A'
            WHEN cum_revenue_pct <= 95.0 THEN 'B'
            ELSE 'C'
        END AS abc_class,
        -- XYZ Classification based on demand predictability
        CASE 
            WHEN coefficient_of_variation < 0.20 THEN 'X'
            WHEN coefficient_of_variation < 0.35 THEN 'Y'
            ELSE 'Z'
        END AS xyz_class
    FROM abc_ranked
)

SELECT 
    sku_id,
    product_name,
    category,
    abc_class || xyz_class AS abc_xyz_segment,
    abc_class,
    xyz_class,
    ROUND(total_revenue_idr, 0) AS revenue_idr,
    cum_revenue_pct,
    ROUND(avg_daily_demand, 1) AS mean_demand_per_dc,
    coefficient_of_variation AS cv_score,
    -- Inventory Policy Recommendation based on Segment
    CASE 
        WHEN abc_class = 'A' AND xyz_class = 'X' THEN 'Continuous Review (s, S); High Safety Buffer; Strict Supplier SLA'
        WHEN abc_class = 'A' AND xyz_class = 'Y' THEN 'Dynamic ROP; Frequent Collaborative Forecasting; Joint Promotions'
        WHEN abc_class = 'A' AND xyz_class = 'Z' THEN 'Strategic Safety Stock; Direct Plant Replenishment; Order Smoothing'
        WHEN abc_class = 'B' AND xyz_class = 'X' THEN 'Periodic Weekly Review; Automated PO Trigger; Standard Buffer'
        WHEN abc_class = 'B' AND xyz_class = 'Y' THEN 'Bi-weekly Review; Seasonal Safety Stock Buffering'
        WHEN abc_class = 'B' AND xyz_class = 'Z' THEN 'Centralized Hub Stocking; Pull Replenishment from DC Cakung'
        WHEN abc_class = 'C' AND xyz_class = 'X' THEN 'Two-Bin System / Large Batch EOQ; Low Operational Attention'
        WHEN abc_class = 'C' AND xyz_class = 'Y' THEN 'Minimum Order Quantity (MOQ); Periodic Monthly Replenishment'
        WHEN abc_class = 'C' AND xyz_class = 'Z' THEN 'Make-to-Order / Direct Vendor Ship; Rationalize or Phase Out'
    END AS strategic_inventory_policy
FROM matrix_segmented
ORDER BY total_revenue_idr DESC;
