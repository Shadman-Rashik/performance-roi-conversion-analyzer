-- schema.sql
-- Defines the two tables of the "Performance ROI & Conversion Drop-off Analyzer".
-- The CHECK rules make the database itself reject impossible data
-- (for example: more purchases than checkouts started).

DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS payments;

-- One row per marketing campaign. All money is in the reporting currency (USD).
CREATE TABLE campaigns (
    campaign_id           TEXT PRIMARY KEY,
    campaign_name         TEXT NOT NULL UNIQUE,
    market                TEXT NOT NULL,
    marketing_channel     TEXT NOT NULL,
    campaign_objective    TEXT NOT NULL,
    reporting_currency    TEXT NOT NULL,
    marketing_spend       REAL NOT NULL CHECK (marketing_spend >= 0),
    impressions           INTEGER NOT NULL CHECK (impressions >= 0),
    clicks                INTEGER NOT NULL CHECK (clicks >= 0),
    landing_page_visitors INTEGER NOT NULL CHECK (landing_page_visitors >= 0),
    product_interactions  INTEGER NOT NULL CHECK (product_interactions >= 0),
    add_to_cart           INTEGER NOT NULL CHECK (add_to_cart >= 0),
    checkout_started      INTEGER NOT NULL CHECK (checkout_started >= 0),
    purchases             INTEGER NOT NULL CHECK (purchases >= 0),
    attributed_revenue    REAL NOT NULL CHECK (attributed_revenue >= 0),
    -- the funnel can only shrink as customers move forward
    CHECK (clicks <= impressions),
    CHECK (landing_page_visitors <= clicks),
    CHECK (product_interactions <= landing_page_visitors),
    CHECK (add_to_cart <= product_interactions),
    CHECK (checkout_started <= add_to_cart),
    CHECK (purchases <= checkout_started)
);

-- One row per market + payment method (aggregated, NOT linked to campaigns).
CREATE TABLE payments (
    market              TEXT NOT NULL,
    payment_method      TEXT NOT NULL,
    checkout_attempts   INTEGER NOT NULL CHECK (checkout_attempts >= 0),
    successful_payments INTEGER NOT NULL CHECK (successful_payments >= 0),
    failed_payments     INTEGER NOT NULL CHECK (failed_payments >= 0),
    completed_orders    INTEGER NOT NULL CHECK (completed_orders >= 0),
    PRIMARY KEY (market, payment_method),
    -- successful + failed must add up to attempts
    CHECK (successful_payments + failed_payments = checkout_attempts),
    CHECK (completed_orders <= successful_payments)
);
