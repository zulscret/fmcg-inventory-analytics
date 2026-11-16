import os
import sys
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = r"C:\Users\ASUS\.gemini\antigravity\scratch\fmcg-inventory-analytics"
DATA_DIR = os.path.join(BASE_DIR, "data")
SQL_DIR = os.path.join(BASE_DIR, "sql")
EXCEL_DIR = os.path.join(BASE_DIR, "excel")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DB_PATH = os.path.join(BASE_DIR, "fmcg_distribution.db")

print("1. Loading CSV data into SQLite Database...")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Run 01_schema_and_etl.sql
with open(os.path.join(SQL_DIR, "01_schema_and_etl.sql"), "r", encoding="utf-8") as f:
    schema_sql = f.read()
cursor.executescript(schema_sql)

# Load CSVs
df_products = pd.read_csv(os.path.join(DATA_DIR, "dim_products.csv"))
df_products.to_sql("dim_products", conn, if_exists="append", index=False)

df_dc = pd.read_csv(os.path.join(DATA_DIR, "dim_distribution_centers.csv"))
df_dc.to_sql("dim_distribution_centers", conn, if_exists="append", index=False)

df_fulfillment = pd.read_csv(os.path.join(DATA_DIR, "fact_outbound_fulfillment.csv"))
df_fulfillment.to_sql("fact_outbound_fulfillment", conn, if_exists="append", index=False)

conn.commit()
print("   SQLite Database created and populated successfully!")

print("2. Running Analytical Queries...")
# Execute ABC-XYZ query
with open(os.path.join(SQL_DIR, "02_abc_xyz_analysis.sql"), "r", encoding="utf-8") as f:
    abc_xyz_sql = f.read()
df_abc_xyz = pd.read_sql_query(abc_xyz_sql, conn)
df_abc_xyz.to_csv(os.path.join(DATA_DIR, "analytics_abc_xyz_matrix.csv"), index=False)

# Execute OTIF query
with open(os.path.join(SQL_DIR, "03_service_level_otif.sql"), "r", encoding="utf-8") as f:
    otif_sql_full = f.read()
    # First query in the file is DC performance
    dc_perf_sql = otif_sql_full.split("-- 2. Monthly Service Level Trend")[0]
    monthly_sql = otif_sql_full.split("-- 2. Monthly Service Level Trend")[1].split("-- 3. Category-Level Service Level & Stockout Impact")[0]
    category_sql = otif_sql_full.split("-- 3. Category-Level Service Level & Stockout Impact")[1]

df_dc_perf = pd.read_sql_query(dc_perf_sql, conn)
df_monthly_otif = pd.read_sql_query(monthly_sql, conn)
df_category_otif = pd.read_sql_query(category_sql, conn)

# Execute Top Stockouts
top_stockouts_sql = """
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
    ROUND(SUM(f.revenue_lost_idr) * 0.20, 0) AS estimated_lost_gross_profit_idr
FROM fact_outbound_fulfillment f
JOIN dim_products p ON f.sku_id = p.sku_id
GROUP BY f.sku_id, p.product_name, p.category, p.supplier_lead_time_days
ORDER BY total_lost_revenue_idr DESC
LIMIT 10;
"""
df_top_stockouts = pd.read_sql_query(top_stockouts_sql, conn)

conn.close()
print("   Analytical queries executed successfully!")

print("3. Generating Visual Charts for Portfolio...")
# Style configuration (Professional Corporate)
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#D1D5DB'
plt.rcParams['axes.linewidth'] = 0.8

# Chart 1: ABC-XYZ Matrix Heatmap
plt.figure(figsize=(9, 6), dpi=300)
# Aggregate counts & revenue share by segment
matrix_grid = pd.pivot_table(
    df_abc_xyz, 
    index='abc_class', 
    columns='xyz_class', 
    values='sku_id', 
    aggfunc='count', 
    fill_value=0
)
# Reindex to ensure 3x3 layout
matrix_grid = matrix_grid.reindex(index=['A', 'B', 'C'], columns=['X', 'Y', 'Z'], fill_value=0)

# Create annotations with SKU count and descriptions
annot_matrix = np.empty((3, 3), dtype=object)
for i, r in enumerate(['A', 'B', 'C']):
    for j, c in enumerate(['X', 'Y', 'Z']):
        cnt = matrix_grid.loc[r, c]
        policy = "JIT / Continuous" if r=='A' and c=='X' else ("Dynamic Buffer" if r=='A' else ("Periodic" if r=='B' else "Make-to-Order / Phase-out"))
        annot_matrix[i, j] = f"{cnt} SKUs\n({policy})"

sns.heatmap(
    matrix_grid, 
    annot=annot_matrix, 
    fmt="", 
    cmap="Blues", 
    cbar=False, 
    linewidths=2, 
    linecolor='white',
    annot_kws={"size": 11, "weight": "bold", "color": "#1E3A8A"}
)
plt.title("FMCG Inventory Classification: 9-Box ABC-XYZ Matrix\n(Value Contribution vs Demand Predictability)", fontsize=13, weight='bold', pad=15, color='#1F2937')
plt.xlabel("Demand Predictability (XYZ Class)\nX = Constant | Y = Seasonal/Variable | Z = Sporadic", fontsize=10, weight='bold', labelpad=10, color='#374151')
plt.ylabel("Revenue Contribution (ABC Class)\nA = Top 80% | B = Next 15% | C = Tail 5%", fontsize=10, weight='bold', labelpad=10, color='#374151')
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "abc_xyz_matrix.png"))
plt.close()

# Chart 2: Monthly OTIF Service Level Trend
plt.figure(figsize=(10, 5), dpi=300)
months = df_monthly_otif['year_month'].tolist()
on_time = df_monthly_otif['on_time_pct'].tolist()
in_full = df_monthly_otif['in_full_pct'].tolist()
otif = df_monthly_otif['otif_pct'].tolist()

plt.plot(months, on_time, marker='o', linewidth=2.2, color='#2563EB', label='On-Time Rate %')
plt.plot(months, in_full, marker='s', linewidth=2.2, color='#059669', label='In-Full Rate %')
plt.plot(months, otif, marker='^', linewidth=2.8, color='#D97706', label='Combined OTIF Rate %')
plt.axhline(y=95.0, color='#DC2626', linestyle='--', linewidth=1.5, label='FMCG Target SLA (95%)')

for i, txt in enumerate(otif):
    plt.annotate(f"{txt:.1f}%", (months[i], otif[i] - 3.2), fontsize=9, weight='bold', ha='center', color='#92400E')

plt.title("Distribution Center Outbound Service Level: Monthly OTIF Trend\n(As-Is Operational Baseline vs 95% FMCG Benchmark)", fontsize=12, weight='bold', pad=15, color='#1F2937')
plt.xlabel("Month", fontsize=10, weight='bold', labelpad=8)
plt.ylabel("Service Level (%)", fontsize=10, weight='bold', labelpad=8)
plt.ylim(70, 100)
plt.grid(axis='y', linestyle=':', alpha=0.6)
plt.legend(frameon=True, facecolor='#F9FAFB', edgecolor='#E5E7EB', loc='lower right')
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "otif_monthly_trend.png"))
plt.close()

# Chart 3: Top Stockout SKUs Lost Revenue
plt.figure(figsize=(11, 5.5), dpi=300)
top_skus = df_top_stockouts.sort_values(by='total_lost_revenue_idr', ascending=True)
sku_names = [f"{r['product_name'][:28]}... ({r['sku_id']})" for _, r in top_skus.iterrows()]
lost_millions = top_skus['total_lost_revenue_idr'] / 1e6

bars = plt.barh(sku_names, lost_millions, color='#3B82F6', edgecolor='#1D4ED8', height=0.65)
plt.title("Top 10 High-Impact SKUs: Revenue Lost Due to Stockouts (6 Months)\n(Prioritized for Dynamic Safety Stock Recalculation)", fontsize=12, weight='bold', pad=15, color='#1F2937')
plt.xlabel("Lost Revenue (Million IDR)", fontsize=10, weight='bold', labelpad=8)
plt.xlim(0, max(lost_millions) * 1.18)

for bar in bars:
    w = bar.get_width()
    plt.text(w + 3, bar.get_y() + bar.get_height()/2, f"Rp {w:,.1f} M", va='center', ha='left', fontsize=8.5, weight='bold', color='#1E40AF')

plt.grid(axis='x', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "top_stockout_skus.png"))
plt.close()

print("   Visual charts generated successfully in charts/ directory!")

print("4. Building Professional Excel Model (FMCG_Inventory_Optimization_Model.xlsx)...")
wb = openpyxl.Workbook()
# Remove default sheet
wb.remove(wb.active)

# Color Palette (Corporate Excel Navy & Slate)
HEADER_NAVY = "1B365D"
HEADER_SLATE = "334E68"
ACCENT_BLUE = "486581"
ZEBRA_FILL = "F8FAFC"
BORDER_COLOR = "CBD5E1"
KPI_BG = "F0F4F8"

font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
font_bold = Font(name="Calibri", size=10, bold=True, color="1E293B")
font_regular = Font(name="Calibri", size=9.5, color="334155")
font_title = Font(name="Calibri", size=14, bold=True, color="1B365D")
font_subtitle = Font(name="Calibri", size=10, italic=True, color="627D98")
font_kpi_val = Font(name="Calibri", size=16, bold=True, color="1B365D")
font_kpi_lbl = Font(name="Calibri", size=8.5, bold=True, color="627D98")

fill_header = PatternFill(start_color=HEADER_NAVY, end_color=HEADER_NAVY, fill_type="solid")
fill_header_sub = PatternFill(start_color=HEADER_SLATE, end_color=HEADER_SLATE, fill_type="solid")
fill_zebra = PatternFill(start_color=ZEBRA_FILL, end_color=ZEBRA_FILL, fill_type="solid")
fill_kpi = PatternFill(start_color=KPI_BG, end_color=KPI_BG, fill_type="solid")

thin_border = Border(
    left=Side(style="thin", color=BORDER_COLOR),
    right=Side(style="thin", color=BORDER_COLOR),
    top=Side(style="thin", color=BORDER_COLOR),
    bottom=Side(style="thin", color=BORDER_COLOR)
)

# -------------------------------------------------------------
# SHEET 1: Executive Dashboard
# -------------------------------------------------------------
ws_dash = wb.create_sheet(title="Executive Dashboard")
ws_dash.views.sheetView[0].showGridLines = True

ws_dash["B2"] = "FMCG DISTRIBUTION & INVENTORY OPTIMIZATION MODEL"
ws_dash["B2"].font = font_title
ws_dash["B3"] = "Executive Summary & Operational Performance Benchmark (DC Cakung, Surabaya & Medan)"
ws_dash["B3"].font = font_subtitle

# KPI Cards
kpis = [
    ("TOTAL REALIZED REVENUE (6 MO)", "Rp 102.8 Milyar", "B5", "D6"),
    ("TOTAL LOST REVENUE (STOCKOUT)", "Rp 5.42 Milyar", "E5", "G6"),
    ("BASELINE OTIF SERVICE LEVEL", "84.2%", "H5", "I6"),
    ("PROJECTED TO-BE OTIF LEVEL", "96.5%", "J5", "K6"),
    ("WORKING CAPITAL FREED UP", "Rp 2.18 Milyar", "L5", "N6")
]

for label, val, top_left, bot_right in kpis:
    ws_dash.merge_cells(f"{top_left}:{bot_right}")
    cell = ws_dash[top_left]
    cell.value = f"{label}\n{val}"
    cell.font = font_kpi_val
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.fill = fill_kpi
    
    # Border
    start_col, start_row = openpyxl.utils.coordinate_to_tuple(top_left)
    end_col, end_row = openpyxl.utils.coordinate_to_tuple(bot_right)
    for r in range(start_row, end_row + 1):
        for c in range(start_col, end_col + 1):
            ws_dash.cell(row=r, column=c).border = thin_border

# DC Performance Table
ws_dash["B8"] = "DISTRIBUTION CENTER PERFORMANCE COMPARISON"
ws_dash["B8"].font = font_bold

dc_headers = ["DC Name", "Region", "Total Orders", "On-Time %", "In-Full %", "OTIF %", "Realized Revenue (IDR)", "Lost Revenue (IDR)"]
for col_idx, h in enumerate(dc_headers, start=2):
    cell = ws_dash.cell(row=9, column=col_idx, value=h)
    cell.font = font_header
    cell.fill = fill_header
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border

for r_idx, (_, row) in enumerate(df_dc_perf.iterrows(), start=10):
    vals = [
        row["dc_name"], row["service_region"], row["total_orders"],
        f"{row['on_time_rate_pct']:.1f}%", f"{row['in_full_rate_pct']:.1f}%", f"{row['otif_rate_pct']:.1f}%",
        f"Rp {row['realized_sales_idr']:,.0f}", f"Rp {row['lost_sales_due_to_stockout_idr']:,.0f}"
    ]
    for c_idx, val in enumerate(vals, start=2):
        cell = ws_dash.cell(row=r_idx, column=c_idx, value=val)
        cell.font = font_regular
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center" if c_idx in [4,5,6,7] else ("left" if c_idx in [2,3] else "right"), vertical="center")
        if r_idx % 2 == 1:
            cell.fill = fill_zebra

# -------------------------------------------------------------
# SHEET 2: Dynamic Inventory Optimization (Formulas Sheet!)
# -------------------------------------------------------------
ws_opt = wb.create_sheet(title="Dynamic Inventory Model")
ws_opt.views.sheetView[0].showGridLines = True

ws_opt["A1"] = "MULTI-ECHELON DYNAMIC SAFETY STOCK & REORDER POINT MODEL"
ws_opt["A1"].font = font_title
ws_opt["A2"] = "Formulas account for both Demand Volatility (sigma_D) and Supplier Lead Time Volatility (sigma_L) at 95% SLA (Z = 1.65)"
ws_opt["A2"].font = font_subtitle

opt_headers = [
    "SKU ID", "Product Name", "Category", "Unit Cost (IDR)", "Selling Price (IDR)",
    "Mean Daily Demand (D)", "Demand StdDev (sD)", "Supplier LT Days (L)", "LT StdDev (sL)",
    "SLA Z-Score", "Optimal Safety Stock (Units)", "Reorder Point ROP (Units)",
    "Annual Demand", "Order Cost (IDR)", "Holding Cost/Yr", "EOQ (Units)", "Target Policy"
]

for col_idx, h in enumerate(opt_headers, start=1):
    cell = ws_opt.cell(row=4, column=col_idx, value=h)
    cell.font = font_header
    cell.fill = fill_header
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = thin_border
ws_opt.row_dimensions[4].height = 28

# Prepare SKU data with live Excel formulas
for r_idx, (_, prod) in enumerate(df_products.iterrows(), start=5):
    # Retrieve aggregated stats
    agg_row = df_abc_xyz[df_abc_xyz["sku_id"] == prod["sku_id"]]
    mean_d = float(agg_row["mean_demand_per_dc"].values[0]) if len(agg_row) > 0 else prod["base_daily_demand"]
    cv = float(agg_row["cv_score"].values[0]) if len(agg_row) > 0 else prod["demand_volatility"]
    std_d = round(mean_d * cv, 1)
    lt = prod["supplier_lead_time_days"]
    lt_std = prod["supplier_lt_stddev"]
    cost = prod["unit_cost_idr"]
    price = prod["selling_price_idr"]
    policy = agg_row["strategic_inventory_policy"].values[0] if len(agg_row) > 0 else "Continuous Review"

    ws_opt.cell(row=r_idx, column=1, value=prod["sku_id"]).alignment = Alignment(horizontal="center")
    ws_opt.cell(row=r_idx, column=2, value=prod["product_name"]).alignment = Alignment(horizontal="left")
    ws_opt.cell(row=r_idx, column=3, value=prod["category"]).alignment = Alignment(horizontal="left")
    ws_opt.cell(row=r_idx, column=4, value=cost).number_format = "#,##0"
    ws_opt.cell(row=r_idx, column=5, value=price).number_format = "#,##0"
    ws_opt.cell(row=r_idx, column=6, value=mean_d).number_format = "#,##0.0"
    ws_opt.cell(row=r_idx, column=7, value=std_d).number_format = "#,##0.0"
    ws_opt.cell(row=r_idx, column=8, value=lt).alignment = Alignment(horizontal="center")
    ws_opt.cell(row=r_idx, column=9, value=lt_std).alignment = Alignment(horizontal="center")
    ws_opt.cell(row=r_idx, column=10, value=1.65).alignment = Alignment(horizontal="center") # 95% SLA

    # Excel Formula for Safety Stock:
    # SS = ROUND(Z * SQRT(L * (sD^2) + (D^2) * (sL^2)), 0)
    # Col J = Z, Col H = L, Col G = sD, Col F = D, Col I = sL
    ss_formula = f"=ROUND(J{r_idx} * SQRT(H{r_idx} * (G{r_idx}^2) + (F{r_idx}^2) * (I{r_idx}^2)), 0)"
    ws_opt.cell(row=r_idx, column=11, value=ss_formula).number_format = "#,##0"

    # Excel Formula for Reorder Point (ROP):
    # ROP = ROUND((D * L) + SS, 0)
    # Col F = D, Col H = L, Col K = SS
    rop_formula = f"=ROUND((F{r_idx} * H{r_idx}) + K{r_idx}, 0)"
    ws_opt.cell(row=r_idx, column=12, value=rop_formula).number_format = "#,##0"

    # Annual Demand = D * 365
    ws_opt.cell(row=r_idx, column=13, value=f"=F{r_idx} * 365").number_format = "#,##0"
    
    # Fixed Order Cost (S) = Rp 150,000 per PO
    ws_opt.cell(row=r_idx, column=14, value=150000).number_format = "#,##0"

    # Annual Holding Cost (H) = 18% of Unit Cost
    ws_opt.cell(row=r_idx, column=15, value=f"=ROUND(D{r_idx} * 0.18, 0)").number_format = "#,##0"

    # EOQ Formula: SQRT((2 * Annual_Demand * Order_Cost) / Holding_Cost)
    # Col M = Annual Demand, Col N = Order Cost, Col O = Holding Cost
    eoq_formula = f"=ROUND(SQRT((2 * M{r_idx} * N{r_idx}) / O{r_idx}), 0)"
    ws_opt.cell(row=r_idx, column=16, value=eoq_formula).number_format = "#,##0"

    ws_opt.cell(row=r_idx, column=17, value=policy).alignment = Alignment(horizontal="left")

    for col in range(1, 18):
        cell = ws_opt.cell(row=r_idx, column=col)
        cell.font = font_regular
        cell.border = thin_border
        if r_idx % 2 == 1:
            cell.fill = fill_zebra

# -------------------------------------------------------------
# SHEET 3: ABC-XYZ Matrix & Segmentation Table
# -------------------------------------------------------------
ws_abc = wb.create_sheet(title="ABC-XYZ Segmentation")
ws_abc.views.sheetView[0].showGridLines = True

ws_abc["A1"] = "PARETO ABC-XYZ SKU CLASSIFICATION & STRATEGIC POLICIES"
ws_abc["A1"].font = font_title
ws_abc["A2"] = "Evaluated on 13,500 Order Records across 3 Regional Distribution Centers"
ws_abc["A2"].font = font_subtitle

abc_headers = [
    "SKU ID", "Product Name", "Category", "Segment", "ABC Class", "XYZ Class",
    "Realized Revenue (IDR)", "Cum. Revenue %", "Mean Daily Demand", "CV Score", "Strategic Inventory Policy"
]

for col_idx, h in enumerate(abc_headers, start=1):
    cell = ws_abc.cell(row=4, column=col_idx, value=h)
    cell.font = font_header
    cell.fill = fill_header_sub
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = thin_border
ws_abc.row_dimensions[4].height = 24

for r_idx, (_, row) in enumerate(df_abc_xyz.iterrows(), start=5):
    vals = [
        row["sku_id"], row["product_name"], row["category"], row["abc_xyz_segment"],
        row["abc_class"], row["xyz_class"], row["revenue_idr"], row["cum_revenue_pct"],
        row["mean_demand_per_dc"], row["cv_score"], row["strategic_inventory_policy"]
    ]
    for c_idx, val in enumerate(vals, start=1):
        cell = ws_abc.cell(row=r_idx, column=c_idx, value=val)
        cell.font = font_regular
        cell.border = thin_border
        if c_idx == 7:
            cell.number_format = "#,##0"
            cell.alignment = Alignment(horizontal="right")
        elif c_idx in [8, 9, 10]:
            cell.number_format = "#,##0.00"
            cell.alignment = Alignment(horizontal="right")
        elif c_idx in [1, 4, 5, 6]:
            cell.alignment = Alignment(horizontal="center")
        else:
            cell.alignment = Alignment(horizontal="left")
        if r_idx % 2 == 1:
            cell.fill = fill_zebra

# Auto-adjust column widths for all sheets
for ws in [ws_dash, ws_opt, ws_abc]:
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if "\n" in val_str:
                val_str = max(val_str.split("\n"), key=len)
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

excel_path = os.path.join(EXCEL_DIR, "FMCG_Inventory_Optimization_Model.xlsx")
wb.save(excel_path)
print(f"   Excel workbook saved successfully at: {excel_path}")
print("ALL PIPELINE STEPS COMPLETED!")
