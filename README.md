# FMCG Multi-Echelon Inventory Optimization & Distribution Center Analytics
> **End-to-End Supply Chain Case Study: Dynamic Safety Stock, Reorder Point (ROP) Engineering, and Outbound Service Level (OTIF) Optimization Across 3 Regional Distribution Centers**

[![Author](https://img.shields.io/badge/Author-Muhammad%20Zulvan%20Yahya-1B365D?style=flat&logo=github)](https://github.com/zulscret)
[![Domain](https://img.shields.io/badge/Domain-FMCG%20Supply%20Chain%20%26%20Distribution-2563EB?style=flat)](#)
[![Tools](https://img.shields.io/badge/Stack-SQL%20%7C%20Python%20%7C%20Excel%20Modeling%20%7C%20Looker%20Studio-059669?style=flat)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

##  Executive Summary
In high-velocity Fast-Moving Consumer Goods (FMCG) distribution across Indonesia, balancing **customer service level (OTIF)** with **working capital efficiency** is a critical operational challenge. 

This repository contains an end-to-end analytical case study analyzing **180 days of order fulfillment and inventory replenishment (13,500 order transactions)** across 3 major distribution hubs:
* **DC Cakung** (Central Hub – Greater Jakarta & West Java)
* **DC Rungkut Surabaya** (Regional Hub – East Java, Bali & Nusa Tenggara)
* **DC KIM Medan** (Regional Hub – North Sumatra & Aceh)

across **25 high-velocity SKUs** spanning Food & Beverage (*Mie Sedaap, Floridina, Top Coffee*), Fabric Care (*SoKlin, Daia, Royale*), Personal Care (*Nuvo, Ciptadent, GIV*), and Home Care (*Ekonomi, WPC*).

---

##  Business Problem & As-Is Baseline
The legacy distribution network operated on static min/max replenishment rules. This led to severe operational vulnerabilities:
1. **Recurring Stockouts on High-Velocity SKUs:** Fast-moving products suffered intermittent stockouts during peak retail replenishment cycles, causing **Rp 5.42 Billion in lost gross revenue**.
2. **Subpar OTIF Delivery:** Network-wide On-Time In-Full (OTIF) service level languished at **84.2%**, falling short of the **95.0% FMCG industry standard**.
3. **Trapped Working Capital:** Slow-moving, erratic SKUs were over-buffered, tying up excess holding capital in regional warehouses and creating warehouse congestion.

---

##  Repository Architecture
```text
fmcg-inventory-analytics/
├── data/
│   ├── dim_products.csv                    # 25 SKU dimension table (Lead times, costs, volatilities)
│   ├── dim_distribution_centers.csv        # Regional DC capacities and multipliers
│   ├── fact_outbound_fulfillment.csv       # 13,500 granular outbound replenishment orders
│   └── analytics_abc_xyz_matrix.csv        # Processed ABC-XYZ segmentation output
├── sql/
│   ├── 01_schema_and_etl.sql               # DDL schema definition & index optimization
│   ├── 02_abc_xyz_analysis.sql             # Pareto ABC & Demand Volatility XYZ window queries
│   ├── 03_service_level_otif.sql           # DC, monthly & category OTIF service level calculations
│   └── 04_inventory_kpis_and_stockout.sql  # Root-cause stockout diagnostics & lost profit metrics
├── excel/
│   └── FMCG_Inventory_Optimization_Model.xlsx # Dynamic financial & inventory model with live formulas
├── charts/
│   ├── abc_xyz_matrix.png                  # 9-box classification heatmap
│   ├── otif_monthly_trend.png              # 6-month OTIF trend vs 95% SLA benchmark
│   └── top_stockout_skus.png               # Top 10 revenue-loss SKU diagnostics
├── reports/
│   ├── FMCG_Inventory_Optimization_Case_Study.pdf # Executive 2-page case study whitepaper
│   └── FMCG_Inventory_Case_Study_Report.html   # Source HTML report template
├── build_full_project.py                   # Automated ETL, analytics & report pipeline
└── README.md                               # Project documentation
```

---

##  Methodology & Analytical Framework

### 1. Multi-Dimensional ABC-XYZ Matrix
Rather than applying uniform stocking rules, SKUs were segmented using a combined **Pareto Value Contribution (ABC)** and **Coefficient of Variation (XYZ)** matrix:
* **Class A (Top 80% Revenue):** Vital revenue drivers.
* **Class B (Next 15% Revenue):** Secondary volume drivers.
* **Class C (Tail 5% Revenue):** Low-revenue long-tail items.
* **Class X ($CV < 0.20$):** Stable, highly predictable demand.
* **Class Y ($0.20 \le CV < 0.35$):** Variable demand with seasonality/promotional surges.
* **Class Z ($CV \ge 0.35$):** Sporadic, erratic demand.

| Segment | Representative SKU | Demand Behavior | Strategic Policy |
|---|---|---|---|
| **AX** | *Mie Sedaap Goreng, SoKlin Liquid* | High Volume, Steady | Continuous Review $(s, S)$, High Safety Buffer, Strict Supplier SLA |
| **AY** | *Mie Sedaap Korean Spicy, Floridina* | High Volume, Promotional | Dynamic Safety Stock, Collaborative Joint Forecasting |
| **BX/BY** | *Ciptadent, Top Coffee, Ekonomi* | Moderate Volume, Predictable | Periodic Weekly Review, Automated EOQ PO Trigger |
| **CZ** | *Fres & Natural, Klin Smart Karbol* | Low Volume, Erratic | Centralized Stocking at Hub Cakung; Rationalize MOQ / Phase Out |

---

### 2. Dual-Uncertainty Dynamic Safety Stock & ROP Formulas
The dynamic optimization model implemented in Excel replaces static heuristics with dual-variability statistical formulas accounting for **both demand fluctuations ($\sigma_D$)** and **supplier lead-time delays ($\sigma_L$)** at a 95% service level ($Z = 1.65$):

$$\text{Safety Stock (SS)} = Z \times \sqrt{\bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$

$$\text{Reorder Point (ROP)} = (\bar{D} \times \bar{L}) + \text{Safety Stock}$$

$$\text{Economic Order Quantity (EOQ)} = \sqrt{\frac{2 \times \text{Annual Demand} \times \text{Ordering Cost}}{\text{Holding Cost}}}$$

---

##  Key Results & Business Impact

| Metric | Baseline (As-Is) | Optimized (To-Be) | Operational Impact |
|---|---|---|---|
| **Network OTIF Rate** | **84.2%** | **96.5%** | **+12.3 pp** (Exceeds 95% SLA) |
| **Stockout Incidents** | 1,248 orders | 350 orders | **-72.0%** reduction in stockouts |
| **Lost Sales from Stockout** | Rp 5.42 Billion | Rp 1.47 Billion | **Rp 3.95 Billion** annual revenue recovered |
| **Tied-Up Working Capital** | Rp 18.6 Billion | Rp 16.42 Billion | **Rp 2.18 Billion** liquidity freed up |
| **Warehouse Space Utilization** | Congested (94%) | Balanced (78%) | Capacity expanded for fast-movers |

---

##  How to Run the Pipeline
```bash
# 1. Clone repository
git clone https://github.com/zulscret/fmcg-inventory-analytics.git
cd fmcg-inventory-analytics

# 2. Run the automated data generation and SQLite pipeline
python build_full_project.py

# 3. Generate the executive PDF report
python generate_report_pdf.py
```

---

##  Author
**Muhammad Zulvan Yahya**  
*S1 Information Systems — Universitas Pembangunan Nasional "Veteran" Jakarta*  
*Specialization: Supply Chain Analytics, Business Analysis, Process Optimization, SQL & Data Modeling*
