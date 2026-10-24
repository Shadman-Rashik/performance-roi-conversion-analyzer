-- queries.sql
-- Business questions answered with SQL (SQLite) for the
-- "Performance ROI & Conversion Drop-off Analyzer".
-- All data is SYNTHETIC. Money is in USD.
--
-- Run them all:  python run_queries.py
-- Or open data/analytics.db in "DB Browser for SQLite" and paste one at a time.
--
-- Tip: "* 1.0" or "* 100.0" forces decimal division. Plain integer / integer
-- would round down in SQLite. NULLIF(x, 0) turns a zero into NULL so we never
-- divide by zero.


-- name: Q1 Which campaigns generate the highest attributed revenue?
-- What it does: sorts campaigns by attributed_revenue, biggest first, top 10.
-- Why a business cares: shows where most attributed revenue comes from, but
-- also compare it with spend (ROI) before moving budget.
SELECT
    campaign_id,
    campaign_name,
    market,
    marketing_channel,
    marketing_spend,
    attributed_revenue,
    ROUND((attributed_revenue - marketing_spend) * 100.0 / NULLIF(marketing_spend, 0), 1) AS roi_pct
FROM campaigns
ORDER BY attributed_revenue DESC
LIMIT 10;


-- name: Q2 Which channels have the lowest cost per acquisition (CPA)?
-- What it does: adds up spend and purchases per channel, then divides.
-- Why a business cares: CPA = how much it costs to win one customer order.
-- Lower CPA means cheaper orders (it says nothing about order value).
-- HAVING removes channels with zero purchases, where CPA cannot be calculated.
SELECT
    marketing_channel,
    ROUND(SUM(marketing_spend), 2)  AS total_spend,
    SUM(purchases)                  AS total_purchases,
    ROUND(SUM(marketing_spend) * 1.0 / SUM(purchases), 2) AS cpa
FROM campaigns
GROUP BY marketing_channel
HAVING SUM(purchases) > 0
ORDER BY cpa ASC;


-- name: Q3 Which campaigns have high spend but comparatively low attributed revenue?
-- What it does: keeps campaigns that spent MORE than the average campaign AND
-- earned LESS revenue per dollar than the overall portfolio.
-- Why a business cares: these are candidates to investigate (creative,
-- targeting, landing page, tracking) before deciding to cut or fix them.
SELECT
    campaign_id,
    campaign_name,
    market,
    marketing_channel,
    marketing_spend,
    attributed_revenue,
    ROUND(attributed_revenue * 1.0 / marketing_spend, 2) AS revenue_per_dollar_spent
FROM campaigns
WHERE marketing_spend > (SELECT AVG(marketing_spend) FROM campaigns)
  AND attributed_revenue * 1.0 / marketing_spend
      < (SELECT SUM(attributed_revenue) * 1.0 / SUM(marketing_spend) FROM campaigns)
ORDER BY revenue_per_dollar_spent ASC
LIMIT 10;


-- name: Q4 Which markets show the largest conversion drop-off?
-- What it does: per market, shows what share of landing-page visitors end up
-- purchasing, and the loss at each funnel step. Lowest conversion is listed first.
-- Why a business cares: points to markets where the journey may be leaking most.
SELECT
    market,
    SUM(landing_page_visitors) AS visitors,
    SUM(purchases)             AS purchases,
    ROUND(SUM(purchases) * 100.0 / NULLIF(SUM(landing_page_visitors), 0), 2) AS visitor_to_purchase_pct,
    ROUND(100 - SUM(product_interactions) * 100.0 / NULLIF(SUM(landing_page_visitors), 0), 1) AS dropoff_visit_to_interaction_pct,
    ROUND(100 - SUM(add_to_cart)          * 100.0 / NULLIF(SUM(product_interactions), 0), 1)  AS dropoff_interaction_to_cart_pct,
    ROUND(100 - SUM(checkout_started)     * 100.0 / NULLIF(SUM(add_to_cart), 0), 1)           AS dropoff_cart_to_checkout_pct,
    ROUND(100 - SUM(purchases)            * 100.0 / NULLIF(SUM(checkout_started), 0), 1)      AS dropoff_checkout_to_purchase_pct
FROM campaigns
GROUP BY market
ORDER BY visitor_to_purchase_pct ASC;


-- name: Q5 Which payment methods have the highest observed failure rates?
-- What it does: totals attempts and failures per payment method (all markets
-- together) and calculates failed / attempts.
-- Why a business cares: failed payments are lost sales. Note: for Cash on
-- Delivery, "failed" means the order was not confirmed.
SELECT
    payment_method,
    SUM(checkout_attempts) AS attempts,
    SUM(failed_payments)   AS failed,
    ROUND(SUM(failed_payments) * 100.0 / NULLIF(SUM(checkout_attempts), 0), 2) AS failure_rate_pct
FROM payments
GROUP BY payment_method
ORDER BY failure_rate_pct DESC;


-- name: Q6 Which market + payment method combinations fail most often?
-- What it does: same as Q5 but keeps market and method together.
-- Why a business cares: the same method can behave differently by market
-- (for example card payments), so a combined view shows where to look first.
SELECT
    market,
    payment_method,
    checkout_attempts,
    failed_payments,
    ROUND(failed_payments * 100.0 / NULLIF(checkout_attempts, 0), 2) AS failure_rate_pct
FROM payments
ORDER BY failure_rate_pct DESC
LIMIT 8;


-- name: Q7 What is the best campaign in each market by revenue-based ROI?
-- What it does: ranks campaigns inside each market with a window function
-- (ROW_NUMBER ... PARTITION BY market) and keeps rank 1.
-- Why a business cares: each market gets its own top performer, so a big
-- market does not hide a good campaign in a small one.
SELECT market, campaign_name, marketing_channel, marketing_spend, attributed_revenue, roi_pct
FROM (
    SELECT
        market,
        campaign_name,
        marketing_channel,
        marketing_spend,
        attributed_revenue,
        ROUND((attributed_revenue - marketing_spend) * 100.0 / NULLIF(marketing_spend, 0), 1) AS roi_pct,
        ROW_NUMBER() OVER (
            PARTITION BY market
            ORDER BY (attributed_revenue - marketing_spend) * 1.0 / NULLIF(marketing_spend, 0) DESC
        ) AS rank_in_market
    FROM campaigns
) AS ranked
WHERE rank_in_market = 1
ORDER BY market;
