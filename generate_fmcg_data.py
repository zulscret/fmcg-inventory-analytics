import os
import sys
import math
import random
import datetime
import sqlite3
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Set seed for exact reproducibility
np.random.seed(42)
random.seed(42)

BASE_DIR = r"C:\Users\ASUS\.gemini\antigravity\scratch\fmcg-inventory-analytics"
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")
EXCEL_DIR = os.path.join(BASE_DIR, "excel")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

for d in [DATA_DIR, SQL_DIR, EXCEL_DIR, CHARTS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# 1. Product Master (25 SKUs)
products_data = [
    # SKU, Name, Category, Subcategory, Unit_Cost, Selling_Price, Case_Pack_Qty, Supplier_Lead_Time_Days, Supplier_LT_StdDev, Base_Daily_Demand, Demand_Volatility
    ("SKU-001", "Mie Sedaap Goreng Original 85g (Karton 40s)", "Food & Beverage", "Instant Noodle", 102000, 118000, 40, 4, 0.8, 450, 0.12),
    ("SKU-002", "Mie Sedaap Soto 75g (Karton 40s)", "Food & Beverage", "Instant Noodle", 98000, 114000, 40, 4, 0.9, 380, 0.15),
    ("SKU-003", "Mie Sedaap Selection Korean Spicy 87g (Karton 40s)", "Food & Beverage", "Instant Noodle", 112000, 130000, 40, 5, 1.2, 280, 0.28),
    ("SKU-004", "SoKlin Liquid Detergent Softergent 720ml Pouch", "Fabric Care", "Liquid Detergent", 14500, 17500, 12, 6, 1.0, 520, 0.14),
    ("SKU-005", "Daia Detergent Bubuk Bunga 1.8kg Bag", "Fabric Care", "Powder Detergent", 26000, 31000, 6, 5, 0.8, 320, 0.16),
    ("SKU-006", "Royale Parfum Collection Pelembut 720ml Pouch", "Fabric Care", "Fabric Softener", 19500, 24000, 12, 7, 1.5, 210, 0.24),
    ("SKU-007", "SoKlin Pemutih Regular Botol 500ml", "Fabric Care", "Bleach", 6500, 8200, 24, 7, 1.1, 140, 0.18),
    ("SKU-008", "Nuvo Family Antibacterial Bodywash Mild 450ml Pouch", "Personal Care", "Body Wash", 15000, 19000, 12, 6, 1.0, 390, 0.15),
    ("SKU-009", "GIV White Beauty Bodywash Damask Rose 450ml Pouch", "Personal Care", "Body Wash", 14000, 17800, 12, 6, 1.2, 260, 0.22),
    ("SKU-010", "Ciptadent Maxi Complete Toothpaste 190g", "Personal Care", "Oral Care", 8500, 11000, 36, 5, 0.7, 410, 0.13),
    ("SKU-011", "Zinc Anti-Dandruff Shampoo Refreshing Cool 340ml", "Personal Care", "Hair Care", 28000, 34500, 12, 8, 1.6, 170, 0.26),
    ("SKU-012", "Emeron Nutritive Shampoo Black Shine 170ml", "Personal Care", "Hair Care", 12500, 16000, 24, 7, 1.3, 130, 0.29),
    ("SKU-013", "Kodomo Baby Hair & Body Wash Pump 200ml", "Personal Care", "Baby Care", 21000, 27000, 12, 9, 2.0, 85, 0.35),
    ("SKU-014", "Top Coffee Gula Aren Bag 9x25g", "Food & Beverage", "Ready to Mix Coffee", 8800, 11200, 20, 5, 0.9, 360, 0.17),
    ("SKU-015", "Floridina Orange Real Pulp 350ml (Karton 24s)", "Food & Beverage", "Beverage", 58000, 70000, 24, 5, 1.1, 310, 0.25),
    ("SKU-016", "ISOPLUS Isotonic Drink 350ml (Karton 24s)", "Food & Beverage", "Beverage", 62000, 75000, 24, 6, 1.2, 220, 0.27),
    ("SKU-017", "JasJus Jeruk Segar Serbuk (Karton 10 Renceng)", "Food & Beverage", "Beverage Serbuk", 42000, 52000, 10, 5, 0.8, 290, 0.19),
    ("SKU-018", "Ekonomi Pencuci Piring Jeruk Nipis 650ml Pouch", "Home Care", "Dishwashing", 7800, 9900, 12, 5, 0.8, 480, 0.13),
    ("SKU-019", "Mama Lemon Jeruk Nipis 680ml Pouch", "Home Care", "Dishwashing", 8200, 10500, 12, 5, 0.7, 440, 0.14),
    ("SKU-020", "WPC Pembersih Porselen & Kloset Classic 780ml", "Home Care", "Surface Cleaner", 13000, 16500, 12, 7, 1.4, 180, 0.23),
    ("SKU-021", "Super Sol Karbol Wangi Pinus 800ml Pouch", "Home Care", "Surface Cleaner", 11500, 14800, 12, 7, 1.2, 160, 0.21),
    ("SKU-022", "Proclin Penghilang Noda Pakaian 400ml Pouch", "Fabric Care", "Bleach / Stain", 10500, 13800, 12, 9, 2.2, 60, 0.42),
    ("SKU-023", "Fres & Natural Cologne Green Miracle 100ml Botol", "Personal Care", "Fragrance", 12000, 16000, 24, 10, 2.5, 45, 0.48),
    ("SKU-024", "Olala Jelly Drink Strawberry 150ml (Karton 24s)", "Food & Beverage", "Confectionery Drink", 41000, 51000, 24, 8, 2.0, 75, 0.38),
    ("SKU-025", "Klin Smart Karbol Sereh Refill 450ml", "Home Care", "Surface Cleaner", 8000, 10500, 12, 12, 3.0, 35, 0.55),
]

df_products = pd.DataFrame(products_data, columns=[
    "sku_id", "product_name", "category", "subcategory", "unit_cost_idr",
    "selling_price_idr", "case_pack_qty", "supplier_lead_time_days",
    "supplier_lt_stddev", "base_daily_demand", "demand_volatility"
])
df_products.to_csv(os.path.join(DATA_DIR, "dim_products.csv"), index=False)

# 2. Distribution Centers Master
dc_data = [
    ("DC-CKG01", "DC Cakung Central Hub", "DKI Jakarta", "Greater Jakarta & West Java", 180000, 1.35),
    ("DC-SBY01", "DC Rungkut Regional Hub", "Jawa Timur", "East Java, Bali & Nusa Tenggara", 120000, 0.95),
    ("DC-MDN01", "DC KIM Medan Regional Hub", "Sumatera Utara", "North Sumatra & Aceh", 75000, 0.65),
]
df_dc = pd.DataFrame(dc_data, columns=["dc_id", "dc_name", "province", "service_region", "pallet_capacity", "demand_multiplier"])
df_dc.to_csv(os.path.join(DATA_DIR, "dim_distribution_centers.csv"), index=False)

# 3. Generate 180 Days of Daily Demand & Fulfillment (June 1, 2026 - Nov 27, 2026)
start_date = datetime.date(2026, 6, 1)
days_count = 180

daily_records = []
fulfillment_records = []
po_records = []

po_counter = 10001
order_counter = 50001

for d_idx in range(days_count):
    current_date = start_date + datetime.timedelta(days=d_idx)
    dow = current_date.weekday() # 0 = Mon, 6 = Sun
    # FMCG retail restock peak on Mon/Tue and Thu/Fri
    dow_factor = 1.15 if dow in [0, 1, 3, 4] else (0.80 if dow == 6 else 1.0)
    
    # Payday / Paycheck boost on days 25 to 2
    day_of_month = current_date.day
    payday_factor = 1.25 if (day_of_month >= 25 or day_of_month <= 3) else 1.0

    for _, prod in df_products.iterrows():
        for _, dc in df_dc.iterrows():
            mean_demand = prod["base_daily_demand"] * dc["demand_multiplier"] * dow_factor * payday_factor
            std_demand = mean_demand * prod["demand_volatility"]
            
            # Simulated actual store orders received
            actual_demand = max(0, int(np.random.normal(mean_demand, std_demand)))
            
            # Service Level Simulation: As-Is system suffers from stockout in fast moving / erratic items
            # Fast-moving items with high demand and longer lead time suffer stockout if not properly buffered
            stockout_risk_score = (prod["demand_volatility"] * 1.5) + (prod["supplier_lead_time_days"] / 10.0)
            
            # Baseline As-Is stockout rate is around 8-10% overall
            is_stockout_event = (np.random.random() < (0.05 * stockout_risk_score))
            
            if is_stockout_event:
                fulfillment_rate = np.random.uniform(0.50, 0.85)
                shipped_qty = int(actual_demand * fulfillment_rate)
                lost_sales_qty = actual_demand - shipped_qty
                stockout_status = "Partial Fill / Stockout"
            else:
                shipped_qty = actual_demand
                lost_sales_qty = 0
                stockout_status = "Fully Filled"

            order_id = f"ORD-{order_counter}"
            order_counter += 1
            
            # On-time delivery simulation (Target: within 24h for CKG, 48h for regional)
            lead_time_actual_hours = 24 if dc["dc_id"] == "DC-CKG01" else 48
            is_delayed = (np.random.random() < (0.06 if dc["dc_id"] == "DC-CKG01" else 0.12))
            actual_delivery_hours = lead_time_actual_hours + (int(np.random.exponential(18)) if is_delayed else 0)
            
            is_on_time = (actual_delivery_hours <= (30 if dc["dc_id"] == "DC-CKG01" else 54))
            is_in_full = (lost_sales_qty == 0)
            is_otif = (is_on_time and is_in_full)
            
            revenue_lost_idr = lost_sales_qty * prod["selling_price_idr"]
            revenue_realized_idr = shipped_qty * prod["selling_price_idr"]

            fulfillment_records.append({
                "order_id": order_id,
                "order_date": current_date.strftime("%Y-%m-%d"),
                "dc_id": dc["dc_id"],
                "sku_id": prod["sku_id"],
                "ordered_qty": actual_demand,
                "shipped_qty": shipped_qty,
                "lost_sales_qty": lost_sales_qty,
                "stockout_status": stockout_status,
                "is_on_time": 1 if is_on_time else 0,
                "is_in_full": 1 if is_in_full else 0,
                "is_otif": 1 if is_otif else 0,
                "revenue_realized_idr": revenue_realized_idr,
                "revenue_lost_idr": revenue_lost_idr
            })

df_fulfillment = pd.DataFrame(fulfillment_records)
df_fulfillment.to_csv(os.path.join(DATA_DIR, "fact_outbound_fulfillment.csv"), index=False)

print(f"Generated {len(df_fulfillment)} outbound fulfillment records.")
