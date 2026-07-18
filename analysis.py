"""
Credit Risk & Collections Analytics -- Python analysis layer.
Reads from the SQLite DB, reproduces the SQL findings in pandas,
and produces chart images + KPI JSON for the dashboard.
"""
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import json

conn = sqlite3.connect("/home/claude/fintech_project/data/loans.db")
df = pd.read_sql_query("SELECT * FROM loans", conn)

OUT = "/home/claude/fintech_project/dashboard/assets"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#1a1a1a",
    "text.color": "#1a1a1a",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
})

NAVY = "#1F3864"
TEAL = "#0F6E56"
CORAL = "#993C1D"

# ---- 1. NPA rate by loan type ----
type_stats = df.groupby("loan_type").agg(
    total=("loan_id", "count"),
    npa=("dpd_bucket", lambda x: (x == "90+ DPD (NPA)").sum())
)
type_stats["npa_rate"] = 100 * type_stats["npa"] / type_stats["total"]
type_stats = type_stats.sort_values("npa_rate", ascending=False)

fig, ax = plt.subplots(figsize=(7, 4.2))
bars = ax.barh(type_stats.index, type_stats["npa_rate"], color=CORAL)
ax.set_xlabel("NPA Rate (%)")
ax.set_title("NPA Rate by Loan Type", fontsize=13, weight="bold", color=NAVY)
ax.invert_yaxis()
for bar, val in zip(bars, type_stats["npa_rate"]):
    ax.text(val + 0.05, bar.get_y() + bar.get_height()/2, f"{val:.2f}%", va="center", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{OUT}/npa_by_loan_type.png", dpi=150)
plt.close()

# ---- 2. NPA rate by credit score band ----
def band(score):
    if score >= 800: return "800+"
    if score >= 750: return "750-799"
    if score >= 700: return "700-749"
    if score >= 650: return "650-699"
    if score >= 600: return "600-649"
    return "Below 600"

df["score_band"] = df["credit_score"].apply(band)
band_order = ["800+", "750-799", "700-749", "650-699", "600-649", "Below 600"]
score_stats = df.groupby("score_band").agg(
    total=("loan_id", "count"),
    npa=("dpd_bucket", lambda x: (x == "90+ DPD (NPA)").sum())
).reindex(band_order)
score_stats["npa_rate"] = 100 * score_stats["npa"] / score_stats["total"]

fig, ax = plt.subplots(figsize=(7, 4.2))
bars = ax.bar(score_stats.index, score_stats["npa_rate"], color=NAVY)
ax.set_ylabel("NPA Rate (%)")
ax.set_title("NPA Rate by Credit Score Band", fontsize=13, weight="bold", color=NAVY)
for bar, val in zip(bars, score_stats["npa_rate"]):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.1, f"{val:.2f}%", ha="center", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig(f"{OUT}/npa_by_score_band.png", dpi=150)
plt.close()

# ---- 3. Monthly vintage NPA trend ----
df["vintage_month"] = pd.to_datetime(df["disbursal_date"]).dt.to_period("M").astype(str)
vintage = df.groupby("vintage_month").agg(
    total=("loan_id", "count"),
    npa=("dpd_bucket", lambda x: (x == "90+ DPD (NPA)").sum())
)
vintage["npa_rate"] = 100 * vintage["npa"] / vintage["total"]

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(vintage.index, vintage["npa_rate"], color=NAVY, marker="o", markersize=4, linewidth=2)
ax.fill_between(vintage.index, vintage["npa_rate"], color=NAVY, alpha=0.08)
ax.set_title("Monthly Disbursal Vintage NPA Trend", fontsize=13, weight="bold", color=NAVY)
ax.set_ylabel("NPA Rate (%)")
ax.set_xticks(range(0, len(vintage.index), 3))
ax.set_xticklabels(vintage.index[::3], rotation=45, ha="right")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{OUT}/vintage_trend.png", dpi=150)
plt.close()

# ---- 4. Collection efficiency by region ----
region = df.groupby("region").agg(
    outstanding=("outstanding_principal", "sum"),
    collected=("collections_amount", "sum")
)
region["efficiency"] = 100 * region["collected"] / region["outstanding"]
region = region.sort_values("efficiency")

fig, ax = plt.subplots(figsize=(7, 4.2))
bars = ax.barh(region.index, region["efficiency"], color=TEAL)
ax.set_xlabel("Collection Efficiency (%)")
ax.set_title("Collection Efficiency by Region", fontsize=13, weight="bold", color=NAVY)
ax.set_xlim(85, 96)
for bar, val in zip(bars, region["efficiency"]):
    ax.text(val + 0.1, bar.get_y() + bar.get_height()/2, f"{val:.1f}%", va="center", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(f"{OUT}/collection_by_region.png", dpi=150)
plt.close()

# ---- Summary + KPI JSON ----
total_disbursed = df["loan_amount"].sum() / 1e7
total_outstanding = df["outstanding_principal"].sum() / 1e7
npa_rate = 100 * (df["dpd_bucket"] == "90+ DPD (NPA)").mean()
npa_exposure = df.loc[df["dpd_bucket"] == "90+ DPD (NPA)", "outstanding_principal"].sum() / 1e7
overall_efficiency = 100 * df["collections_amount"].sum() / df["outstanding_principal"].sum()

summary = f"""
KEY METRICS
-----------
Total Loan Accounts:      {len(df):,}
Total Disbursed:          Rs. {total_disbursed:.2f} Cr
Total Outstanding:        Rs. {total_outstanding:.2f} Cr
NPA Rate:                 {npa_rate:.2f}%
NPA Exposure:              Rs. {npa_exposure:.2f} Cr
Overall Collection Eff.:  {overall_efficiency:.1f}%
Riskiest Loan Type:       {type_stats['npa_rate'].idxmax()} ({type_stats['npa_rate'].max():.2f}% NPA)
Highest-Risk Score Band:  Below 600 ({score_stats.loc['Below 600','npa_rate']:.2f}% NPA)
"""
print(summary)

kpi = {
    "total_loans": int(len(df)),
    "total_disbursed_cr": round(total_disbursed, 2),
    "total_outstanding_cr": round(total_outstanding, 2),
    "npa_rate": round(npa_rate, 2),
    "npa_exposure_cr": round(npa_exposure, 2),
    "collection_efficiency": round(overall_efficiency, 1),
    "npa_by_type": type_stats["npa_rate"].round(2).to_dict(),
    "npa_by_score_band": score_stats["npa_rate"].round(2).to_dict(),
    "vintage_npa": vintage["npa_rate"].round(2).to_dict(),
    "region_efficiency": region["efficiency"].round(1).to_dict(),
}
with open(f"{OUT}/kpi_data.json", "w") as f:
    json.dump(kpi, f, indent=2)

print("Charts + KPI data written.")
