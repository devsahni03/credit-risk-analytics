-- =====================================================================
-- Credit Risk & Collections Analytics
-- Dataset: 60,000 synthetic loan accounts (disbursals, DPD, credit score, recoveries)
-- Author: Dev Sahni
-- =====================================================================

-- 1. PORTFOLIO SUMMARY
-- Total disbursed vs outstanding vs NPA exposure
SELECT
    ROUND(SUM(loan_amount) / 1e7, 2)                                   AS total_disbursed_cr,
    ROUND(SUM(outstanding_principal) / 1e7, 2)                         AS total_outstanding_cr,
    ROUND(SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN outstanding_principal ELSE 0 END) / 1e7, 2) AS npa_exposure_cr,
    ROUND(
        100.0 * SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN 1 ELSE 0 END) / COUNT(*), 2
    ) AS npa_rate_pct
FROM loans;


-- 2. NPA RATE BY LOAN TYPE
-- Which products are driving the most risk -- actionable for underwriting policy
SELECT
    loan_type,
    COUNT(*)                                                            AS total_loans,
    SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN 1 ELSE 0 END)       AS npa_loans,
    ROUND(100.0 * SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN 1 ELSE 0 END) / COUNT(*), 2) AS npa_rate_pct,
    ROUND(SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN outstanding_principal ELSE 0 END) / 1e7, 2) AS npa_exposure_cr
FROM loans
GROUP BY loan_type
ORDER BY npa_rate_pct DESC;


-- 3. DEFAULT RATE BY CREDIT SCORE BAND (ROOT CAUSE / RISK SEGMENTATION)
-- Buckets scores into bands using a CASE expression, then aggregates -- shows the
-- direct relationship between creditworthiness and default risk
SELECT
    CASE
        WHEN credit_score >= 800 THEN '800+ (Excellent)'
        WHEN credit_score >= 750 THEN '750-799 (Very Good)'
        WHEN credit_score >= 700 THEN '700-749 (Good)'
        WHEN credit_score >= 650 THEN '650-699 (Fair)'
        WHEN credit_score >= 600 THEN '600-649 (Poor)'
        ELSE 'Below 600 (High Risk)'
    END AS credit_score_band,
    COUNT(*) AS total_loans,
    ROUND(100.0 * SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN 1 ELSE 0 END) / COUNT(*), 2) AS npa_rate_pct
FROM loans
GROUP BY credit_score_band
ORDER BY MIN(credit_score) DESC;


-- 4. REGIONAL COLLECTIONS EFFICIENCY
-- Collections as a % of outstanding, by region -- joined against a regional NPA
-- subquery to give both efficiency and risk in one view
SELECT
    l.region,
    COUNT(*)                                                            AS total_loans,
    ROUND(SUM(l.outstanding_principal) / 1e7, 2)                        AS outstanding_cr,
    ROUND(SUM(l.collections_amount) / 1e7, 2)                           AS collected_cr,
    ROUND(100.0 * SUM(l.collections_amount) / SUM(l.outstanding_principal), 1) AS collection_efficiency_pct,
    r.npa_rate_pct
FROM loans l
JOIN (
    SELECT region,
           ROUND(100.0 * SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN 1 ELSE 0 END) / COUNT(*), 2) AS npa_rate_pct
    FROM loans
    GROUP BY region
) r ON l.region = r.region
GROUP BY l.region
ORDER BY collection_efficiency_pct ASC;


-- 5. MONTHLY DISBURSAL VINTAGE & NPA TREND
-- Tracks whether more recently disbursed loans are performing better or worse
-- than older vintages -- a standard credit-risk monitoring view
SELECT
    strftime('%Y-%m', disbursal_date)                                  AS vintage_month,
    COUNT(*)                                                            AS loans_disbursed,
    ROUND(SUM(loan_amount) / 1e7, 2)                                    AS disbursed_cr,
    ROUND(100.0 * SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN 1 ELSE 0 END) / COUNT(*), 2) AS npa_rate_pct
FROM loans
GROUP BY vintage_month
ORDER BY vintage_month;


-- 6. RECOVERY OPPORTUNITY SIZING
-- If every loan type's NPA rate matched the best-performing type's rate,
-- how much NPA exposure could be avoided? (subquery pulls the benchmark rate)
SELECT
    loan_type,
    ROUND(SUM(outstanding_principal) / 1e7, 2) AS total_outstanding_cr,
    ROUND(
        (SUM(CASE WHEN dpd_bucket = '90+ DPD (NPA)' THEN outstanding_principal ELSE 0 END)
         - (SELECT MIN(best.npa_rate) FROM (
                SELECT loan_type,
                       1.0 * SUM(CASE WHEN dpd_bucket='90+ DPD (NPA)' THEN 1 ELSE 0 END) / COUNT(*) AS npa_rate
                FROM loans GROUP BY loan_type
            ) best) * SUM(outstanding_principal)
        ) / 1e7, 2
    ) AS estimated_avoidable_npa_cr
FROM loans
GROUP BY loan_type
ORDER BY estimated_avoidable_npa_cr DESC;
