"""
generate_data.py
----------------
Creates the SYNTHETIC datasets used by the
"Performance ROI & Conversion Drop-off Analyzer" project.

Run:    python generate_data.py
Output: data/campaigns.csv  and  data/payments.csv

IMPORTANT: Every number here is randomly generated (with a fixed seed so the
results are reproducible). None of it is real company or market data.

Currency: all money values are in ONE reporting currency, USD. The values are
synthetic, so no real exchange rates are applied or implied.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DATA_DIR = Path(__file__).parent / "data"

# ----------------------------------------------------------------------------
# 1. Assumptions (all synthetic)
# ----------------------------------------------------------------------------

MARKETS = {
    # market: (code, cost multiplier, average order value in USD, conversion multiplier)
    "Bangladesh": ("BD", 0.50, 22.0, 0.90),
    "India": ("IN", 0.45, 20.0, 0.90),
    "United Arab Emirates": ("AE", 1.10, 55.0, 1.00),
    "United Kingdom": ("UK", 1.40, 62.0, 1.05),
    "United States": ("US", 1.60, 70.0, 1.10),
}

# Per channel funnel assumptions:
# ctr           = clicks / impressions
# cpc           = average cost per click in USD (before the market multiplier)
# land          = landing page visitors / clicks
# inter         = product interactions / landing page visitors
# cart          = add to cart / product interactions
# checkout      = checkout started / add to cart
# purchase      = purchases / checkout started
# impressions   = (min, max) impressions per campaign
CHANNELS = {
    "Facebook Ads": dict(ctr=0.011, cpc=0.35, land=0.82, inter=0.55, cart=0.22,
                         checkout=0.55, purchase=0.50, impressions=(300_000, 1_200_000)),
    "Instagram Ads": dict(ctr=0.009, cpc=0.45, land=0.80, inter=0.60, cart=0.20,
                          checkout=0.50, purchase=0.48, impressions=(250_000, 1_000_000)),
    "Google Search": dict(ctr=0.035, cpc=0.80, land=0.90, inter=0.62, cart=0.25,
                          checkout=0.62, purchase=0.58, impressions=(60_000, 300_000)),
    "Google Display": dict(ctr=0.004, cpc=0.20, land=0.75, inter=0.42, cart=0.15,
                           checkout=0.50, purchase=0.45, impressions=(600_000, 2_500_000)),
    "YouTube": dict(ctr=0.006, cpc=0.30, land=0.78, inter=0.48, cart=0.16,
                    checkout=0.52, purchase=0.47, impressions=(400_000, 1_800_000)),
    "TikTok Ads": dict(ctr=0.010, cpc=0.30, land=0.76, inter=0.52, cart=0.17,
                       checkout=0.45, purchase=0.42, impressions=(400_000, 1_600_000)),
    "Email": dict(ctr=0.025, cpc=0.90, land=0.93, inter=0.66, cart=0.28,
                  checkout=0.66, purchase=0.62, impressions=(20_000, 120_000)),
    "Influencer": dict(ctr=0.014, cpc=0.55, land=0.80, inter=0.58, cart=0.21,
                       checkout=0.54, purchase=0.50, impressions=(100_000, 700_000)),
}

OBJECTIVES = {
    "Facebook Ads": ["Conversions", "Traffic", "Retargeting"],
    "Instagram Ads": ["Conversions", "Awareness", "Retargeting"],
    "Google Search": ["Conversions", "Traffic"],
    "Google Display": ["Awareness", "Retargeting"],
    "YouTube": ["Awareness", "Traffic"],
    "TikTok Ads": ["Awareness", "Conversions", "Traffic"],
    "Email": ["Retargeting", "Conversions"],
    "Influencer": ["Awareness", "Conversions"],
}

THEMES = [
    "Eid Sale", "Winter Collection", "Flash Sale", "Back to School",
    "Free Shipping Week", "New Arrivals", "Cart Recovery", "Loyalty Rewards",
    "Black Friday Preview", "Festival Offers",
]

# Payment methods that exist in each market (synthetic assumption) and the
# assumed probability that an attempt succeeds.
# For "Cash on Delivery", "successful" means the order was confirmed and
# accepted; "failed" means it was not confirmed (e.g. customer unreachable or
# order rejected at confirmation).
PAYMENTS = {
    "Bangladesh": {"Cash on Delivery": (18000, 0.82), "bKash": (14000, 0.94),
                   "Nagad": (7000, 0.92), "Card": (6000, 0.84)},
    "India": {"Cash on Delivery": (20000, 0.80), "UPI": (22000, 0.96),
              "Card": (9000, 0.88), "Digital Wallet": (5000, 0.95)},
    "United Arab Emirates": {"Cash on Delivery": (6000, 0.88), "Card": (9000, 0.93),
                             "Digital Wallet": (4000, 0.96)},
    "United Kingdom": {"Card": (11000, 0.95), "Digital Wallet": (6000, 0.97)},
    "United States": {"Card": (16000, 0.96), "Digital Wallet": (8000, 0.97)},
}


# ----------------------------------------------------------------------------
# 2. Campaign data
# ----------------------------------------------------------------------------

def pick_campaign_slots(rng):
    """One campaign for every market x channel pair (40), plus 8 extras."""
    pairs = [(market, channel) for market in MARKETS for channel in CHANNELS]
    extra_idx = rng.choice(len(pairs), size=8, replace=False)
    return pairs + [pairs[i] for i in extra_idx]


def make_campaigns(rng):
    rows = []
    used_names = set()

    for number, (market, channel) in enumerate(pick_campaign_slots(rng), start=1):
        code, cost_mult, aov, conv_mult = MARKETS[market]
        ch = CHANNELS[channel]

        # Choose a theme so that each campaign name is unique.
        theme = THEMES[int(rng.integers(len(THEMES)))]
        name = f"{theme} - {channel} - {code}"
        while name in used_names:
            theme = THEMES[int(rng.integers(len(THEMES)))]
            name = f"{theme} - {channel} - {code}"
        used_names.add(name)

        objective = OBJECTIVES[channel][int(rng.integers(len(OBJECTIVES[channel])))]

        # A "quality" factor makes some campaigns clearly better or worse.
        quality = float(np.clip(rng.lognormal(mean=0.0, sigma=0.30), 0.45, 1.8))
        # Awareness campaigns convert less directly.
        if objective == "Awareness":
            quality *= 0.75
        # A few campaigns overspend relative to what they deliver.
        overspend = 1.0 + (float(rng.uniform(0.6, 1.2)) if rng.random() < 0.15 else 0.0)

        def noisy(rate, spread=0.08):
            return float(np.clip(rate * rng.normal(1.0, spread), 0.01, 0.99))

        impressions = int(rng.integers(*ch["impressions"]))
        clicks = int(rng.binomial(impressions, noisy(ch["ctr"], 0.15)))
        landing = int(rng.binomial(clicks, noisy(ch["land"])))
        interactions = int(rng.binomial(landing, noisy(ch["inter"])))
        add_to_cart = int(rng.binomial(interactions, noisy(ch["cart"] * conv_mult * quality)))
        checkout = int(rng.binomial(add_to_cart, noisy(ch["checkout"])))
        purchases = int(rng.binomial(checkout, noisy(ch["purchase"] * conv_mult)))

        cpc = ch["cpc"] * cost_mult * float(rng.normal(1.0, 0.12)) * overspend
        spend = round(clicks * max(cpc, 0.01), 2)
        revenue = round(purchases * aov * float(rng.lognormal(0.0, 0.10)), 2)

        rows.append({
            "campaign_id": f"C{number:03d}",
            "campaign_name": name,
            "market": market,
            "marketing_channel": channel,
            "campaign_objective": objective,
            "reporting_currency": "USD",
            "marketing_spend": spend,
            "impressions": impressions,
            "clicks": clicks,
            "landing_page_visitors": landing,
            "product_interactions": interactions,
            "add_to_cart": add_to_cart,
            "checkout_started": checkout,
            "purchases": purchases,
            "attributed_revenue": revenue,
        })

    df = pd.DataFrame(rows)

    # Deliberately create ONE campaign with spend but zero purchases, so the
    # project can show how zero denominators (CPA, ROI) are handled safely.
    idx = df.index[(df["marketing_channel"] == "Influencer") & (df["market"] == "United Kingdom")][0]
    df.loc[idx, ["purchases", "attributed_revenue"]] = [0, 0.0]
    return df


# ----------------------------------------------------------------------------
# 3. Payment data
# ----------------------------------------------------------------------------

def make_payments(rng):
    rows = []
    for market, methods in PAYMENTS.items():
        for method, (base_attempts, success_prob) in methods.items():
            attempts = int(base_attempts * rng.uniform(0.85, 1.15))
            success_prob = float(np.clip(success_prob + rng.normal(0, 0.01), 0.5, 0.995))
            successful = int(rng.binomial(attempts, success_prob))
            failed = attempts - successful          # reconciles exactly
            fulfil_prob = 0.93 if method == "Cash on Delivery" else 0.97
            completed = int(rng.binomial(successful, fulfil_prob))
            rows.append({
                "market": market,
                "payment_method": method,
                "checkout_attempts": attempts,
                "successful_payments": successful,
                "failed_payments": failed,
                "completed_orders": completed,
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 4. Main
# ----------------------------------------------------------------------------

def main():
    DATA_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    campaigns = make_campaigns(rng)
    payments = make_payments(rng)

    campaigns.to_csv(DATA_DIR / "campaigns.csv", index=False)
    payments.to_csv(DATA_DIR / "payments.csv", index=False)

    print(f"Created {DATA_DIR / 'campaigns.csv'}  ({len(campaigns)} campaigns)")
    print(f"Created {DATA_DIR / 'payments.csv'}  ({len(payments)} market/payment-method rows)")
    print("Reminder: all data is SYNTHETIC. Money values are in USD.")


if __name__ == "__main__":
    main()
