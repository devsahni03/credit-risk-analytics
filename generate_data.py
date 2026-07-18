"""
Generates a realistic synthetic loan portfolio dataset for credit risk &
collections analytics: disbursals, DPD buckets, credit scores, recoveries.
Scale: ~60,000 loan accounts, mirroring the healthcare project's scope.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(7)
random.seed(7)

N = 60000

loan_types = ["Personal Loan", "Auto Loan", "Home Loan", "Business Loan", "Gold Loan", "Consumer Durable"]
loan_type_weights = [0.28, 0.18, 0.12, 0.14, 0.16, 0.12]

regions = ["North", "South", "East", "West", "Central"]
region_weights = [0.26, 0.24, 0.14, 0.24, 0.12]

dpd_buckets = ["Current", "1-30 DPD", "31-60 DPD", "61-90 DPD", "90+ DPD (NPA)"]

start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 12, 31)
date_range_days = (end_date - start_date).days

loan_base = {
    "Personal Loan": 180000, "Auto Loan": 550000, "Home Loan": 2800000,
    "Business Loan": 950000, "Gold Loan": 120000, "Consumer Durable": 45000
}

rows = []
for i in range(N):
    ltype = np.random.choice(loan_types, p=loan_type_weights)
    region = np.random.choice(regions, p=region_weights)
    disbursal_date = start_date + timedelta(days=random.randint(0, date_range_days))

    loan_amount = max(15000, np.random.normal(loan_base[ltype], loan_base[ltype] * 0.4))
    tenure_months = {"Personal Loan": 36, "Auto Loan": 60, "Home Loan": 180,
                      "Business Loan": 48, "Gold Loan": 12, "Consumer Durable": 18}[ltype]

    # credit score: normal distribution centered at 720, range 300-900
    credit_score = int(np.clip(np.random.normal(720, 85), 300, 900))

    # default probability driven primarily by credit score, with loan-type and region modifiers
    score_risk = max(0.01, (750 - credit_score) / 1000)
    type_modifier = {"Personal Loan": 1.3, "Auto Loan": 0.9, "Home Loan": 0.5,
                      "Business Loan": 1.4, "Gold Loan": 0.6, "Consumer Durable": 1.5}[ltype]
    region_modifier = {"North": 1.0, "South": 0.85, "East": 1.15, "West": 0.9, "Central": 1.1}[region]
    default_prob = min(0.55, score_risk * type_modifier * region_modifier)

    roll = random.random()
    outstanding_principal = loan_amount * np.random.uniform(0.3, 0.95)

    if roll < default_prob * 0.4:
        dpd_bucket = "90+ DPD (NPA)"
        collections_amount = outstanding_principal * np.random.uniform(0.05, 0.25)
        written_off = random.random() < 0.3
    elif roll < default_prob * 0.6:
        dpd_bucket = "61-90 DPD"
        collections_amount = outstanding_principal * np.random.uniform(0.2, 0.5)
        written_off = False
    elif roll < default_prob * 0.8:
        dpd_bucket = "31-60 DPD"
        collections_amount = outstanding_principal * np.random.uniform(0.4, 0.7)
        written_off = False
    elif roll < default_prob:
        dpd_bucket = "1-30 DPD"
        collections_amount = outstanding_principal * np.random.uniform(0.6, 0.9)
        written_off = False
    else:
        dpd_bucket = "Current"
        collections_amount = outstanding_principal * np.random.uniform(0.9, 1.0)
        written_off = False

    rows.append({
        "loan_id": f"LN{200000+i}",
        "borrower_id": f"BOR{random.randint(10000, 42000)}",
        "loan_type": ltype,
        "region": region,
        "disbursal_date": disbursal_date.strftime("%Y-%m-%d"),
        "loan_amount": round(loan_amount, 2),
        "tenure_months": tenure_months,
        "credit_score": credit_score,
        "outstanding_principal": round(outstanding_principal, 2),
        "collections_amount": round(collections_amount, 2),
        "dpd_bucket": dpd_bucket,
        "written_off": written_off,
    })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/fintech_project/data/loan_portfolio.csv", index=False)
print(df.shape)
print(df["dpd_bucket"].value_counts(normalize=True))
print("Total disbursed (Cr):", round(df["loan_amount"].sum() / 1e7, 2))
print("Total outstanding (Cr):", round(df["outstanding_principal"].sum() / 1e7, 2))
npa_rate = (df["dpd_bucket"] == "90+ DPD (NPA)").mean() * 100
print(f"NPA rate: {npa_rate:.1f}%")
