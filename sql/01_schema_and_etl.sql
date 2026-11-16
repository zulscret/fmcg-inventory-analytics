-- ==============================================================================
-- PROJECT: FMCG Multi-Echelon Inventory Optimization & Distribution Center Analytics
-- AUTHOR: Muhammad Zulvan Yahya
-- MODULE: 01_schema_and_etl.sql
-- PURPOSE: DDL schema definition, table creation, and staging ETL for analytical queries
-- ==============================================================================

-- Drop existing tables if re-running
DROP TABLE IF EXISTS fact_outbound_fulfillment;
DROP TABLE IF EXISTS dim_distribution_centers;
DROP TABLE IF EXISTS dim_products;

-- 1. Dimension Table: Products (SKU Master)
CREATE TABLE dim_products (
    sku_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50) NOT NULL,
    unit_cost_idr NUMERIC(12, 2) NOT NULL,
    selling_price_idr NUMERIC(12, 2) NOT NULL,
    case_pack_qty INT NOT NULL,
    supplier_lead_time_days INT NOT NULL,
    supplier_lt_stddev NUMERIC(6, 2) NOT NULL,
    base_daily_demand INT NOT NULL,
    demand_volatility NUMERIC(6, 3) NOT NULL
);

-- 2. Dimension Table: Distribution Centers (DC Master)
CREATE TABLE dim_distribution_centers (
    dc_id VARCHAR(20) PRIMARY KEY,
    dc_name VARCHAR(100) NOT NULL,
    province VARCHAR(50) NOT NULL,
    service_region VARCHAR(100) NOT NULL,
    pallet_capacity INT NOT NULL,
    demand_multiplier NUMERIC(6, 2) NOT NULL
);

-- 3. Fact Table: Outbound Fulfillment & Service Level
CREATE TABLE fact_outbound_fulfillment (
    order_id VARCHAR(30) PRIMARY KEY,
    order_date DATE NOT NULL,
    dc_id VARCHAR(20) NOT NULL,
    sku_id VARCHAR(20) NOT NULL,
    ordered_qty INT NOT NULL,
    shipped_qty INT NOT NULL,
    lost_sales_qty INT NOT NULL,
    stockout_status VARCHAR(50) NOT NULL,
    is_on_time SMALLINT NOT NULL,
    is_in_full SMALLINT NOT NULL,
    is_otif SMALLINT NOT NULL,
    revenue_realized_idr NUMERIC(15, 2) NOT NULL,
    revenue_lost_idr NUMERIC(15, 2) NOT NULL,
    FOREIGN KEY (dc_id) REFERENCES dim_distribution_centers (dc_id),
    FOREIGN KEY (sku_id) REFERENCES dim_products (sku_id)
);

-- Indexing for optimized reporting performance
CREATE INDEX idx_fulfillment_order_date ON fact_outbound_fulfillment (order_date);
CREATE INDEX idx_fulfillment_dc_sku ON fact_outbound_fulfillment (dc_id, sku_id);
CREATE INDEX idx_fulfillment_otif ON fact_outbound_fulfillment (is_otif);
