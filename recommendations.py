"""
recommendations.py
------------------
Simple RULE-BASED recommendations built from the numbers in the selected data.

Nothing here is hardcoded to a particular campaign, channel or market:
every name in the text comes from the currently filtered data.
The rules describe patterns to INVESTIGATE; they do not prove cause and effect.
"""

import numpy as np
import pandas as pd

import metrics as m

# Rule thresholds (change them to make the rules stricter or looser)
MIN_CAMPAIGNS_FOR_RANKING = 4     # need at least this many campaigns to rank/compare
CPA_GAP_RATIO = 1.5               # highest CPA is 1.5x the lowest -> flag
PAYMENT_GAP_POINTS = 2.0          # failure rate this many points above the overall rate -> flag
MIN_PAYMENT_ATTEMPTS = 1000       # ignore payment groups with fewer attempts

# Ideas to investigate for each funnel step (generic; the step itself comes from the data)
STEP_IDEAS = {
    "Product Interactions": "landing-page relevance to the ad, page load speed, and mobile layout",
    "Add to Cart": "product pages, pricing clarity, delivery cost and time information, and trust signals",
    "Checkout Started": "unexpected shipping costs, forced account creation, and cart-page friction",
    "Purchases": "payment options, form length, payment errors, and order confirmation steps",
}

CAVEAT = (
    "These are rule-based observations from synthetic data. They show patterns worth "
    "investigating, not proven causes. Revenue-based ROI ignores product, operating and "
    "other costs, so it is not net-profit ROI."
)


def _item(area, observation, suggestion):
    return {"area": area, "observation": observation, "suggestion": suggestion}


def campaign_recommendations(campaigns):
    items = []
    if campaigns.empty:
        return items

    # --- Channel ROI ----------------------------------------------------------
    by_channel = m.summarize_campaigns(campaigns, "marketing_channel")
    ranked = by_channel.dropna(subset=["roi_pct"])
    if len(ranked) >= 2:
        best = ranked.loc[ranked["roi_pct"].idxmax()]
        worst = ranked.loc[ranked["roi_pct"].idxmin()]
        text = (f"Among the selected data, {best['marketing_channel']} has the highest "
                f"revenue-based ROI ({m.fmt_pct(best['roi_pct'], 0)}) and "
                f"{worst['marketing_channel']} the lowest ({m.fmt_pct(worst['roi_pct'], 0)}).")
        idea = ("Check whether the gap comes from audience, creative, landing pages or how "
                "revenue is attributed, before changing budgets.")
        if worst["roi_pct"] < 0:
            idea = (f"{worst['marketing_channel']} attributed less revenue than it spent. " + idea)
        items.append(_item("Channel ROI", text, idea))
    elif len(ranked) == 1:
        only = ranked.iloc[0]
        items.append(_item(
            "Channel ROI",
            f"Only {only['marketing_channel']} is selected "
            f"(revenue-based ROI {m.fmt_pct(only['roi_pct'], 0)}).",
            "Select more channels to compare them."))

    # --- CPA gap ---------------------------------------------------------------
    cpa_rows = by_channel.dropna(subset=["cpa"])
    if len(cpa_rows) >= 2:
        low = cpa_rows.loc[cpa_rows["cpa"].idxmin()]
        high = cpa_rows.loc[cpa_rows["cpa"].idxmax()]
        if low["cpa"] > 0 and high["cpa"] / low["cpa"] >= CPA_GAP_RATIO:
            items.append(_item(
                "Cost per acquisition",
                f"{high['marketing_channel']} has a CPA of {m.fmt_money(high['cpa'], 2)}, about "
                f"{high['cpa'] / low['cpa']:.1f}x that of {low['marketing_channel']} "
                f"({m.fmt_money(low['cpa'], 2)}).",
                "Compare order values too: a higher CPA can still be fine if those customers "
                "spend more. Look at targeting and conversion steps for the higher-CPA channel."))

    # --- High spend, below-average return ---------------------------------------
    if len(campaigns) >= MIN_CAMPAIGNS_FOR_RANKING:
        overall = m.summarize_campaigns(campaigns).iloc[0]
        per_campaign = m.summarize_campaigns(
            campaigns, ["campaign_id", "campaign_name"])
        median_spend = per_campaign["marketing_spend"].median()
        flagged = per_campaign[
            (per_campaign["marketing_spend"] >= median_spend)
            & (per_campaign["roi_pct"] < overall["roi_pct"])
        ].sort_values("roi_pct").head(3)
        if not flagged.empty:
            names = "; ".join(
                f"{r.campaign_name} (ROI {m.fmt_pct(r.roi_pct, 0)}, spend {m.fmt_money(r.marketing_spend)})"
                for r in flagged.itertuples())
            items.append(_item(
                "High spend, lower return",
                f"These campaigns spent at or above the median but returned less than the "
                f"overall ROI of {m.fmt_pct(overall['roi_pct'], 0)}: {names}.",
                "Review creative, audience, landing page and tracking for these campaigns "
                "before deciding whether to adjust or pause them."))

    # --- Spend but zero purchases ------------------------------------------------
    zero = campaigns[(campaigns["marketing_spend"] > 0) & (campaigns["purchases"] == 0)]
    if not zero.empty:
        names = "; ".join(zero["campaign_name"].tolist()[:3])
        items.append(_item(
            "Spend with no purchases",
            f"{len(zero)} campaign(s) recorded spend but no purchases: {names}. "
            "CPA cannot be calculated for them.",
            "Confirm that purchase tracking and attribution are set up correctly for these campaigns."))

    # --- Funnel -------------------------------------------------------------------
    funnel = m.funnel_table(campaigns)
    biggest = m.largest_dropoff(funnel)
    if biggest is not None:
        idea = STEP_IDEAS.get(biggest["stage"], "the customer experience at this step")
        items.append(_item(
            "Conversion funnel",
            f"The largest drop-off is {biggest['step']}: {m.fmt_pct(biggest['step_dropoff_pct'])} "
            f"of people did not continue ({m.fmt_int(biggest['lost_from_previous'])} lost).",
            f"Worth investigating: {idea}. Some drop-off at this step is normal, so compare "
            "it with your own benchmarks."))
    return items


def payment_recommendations(payments):
    items = []
    if payments.empty:
        return items

    overall = m.summarize_payments(payments).iloc[0]
    overall_fail = overall["payment_failure_rate_pct"]
    if pd.isna(overall_fail):
        return items

    # --- Payment method ---------------------------------------------------------
    by_method = m.summarize_payments(payments, "payment_method")
    by_method = by_method[by_method["checkout_attempts"] >= MIN_PAYMENT_ATTEMPTS]
    if len(by_method) >= 2:
        worst = by_method.loc[by_method["payment_failure_rate_pct"].idxmax()]
        gap = worst["payment_failure_rate_pct"] - overall_fail
        if gap >= PAYMENT_GAP_POINTS:
            extra = ""
            if worst["payment_method"] == "Cash on Delivery":
                extra = (" For Cash on Delivery, 'failed' means the order was not confirmed, "
                         "so review confirmation calls/messages and address quality.")
            items.append(_item(
                "Payment method",
                f"{worst['payment_method']} has a failure rate of "
                f"{m.fmt_pct(worst['payment_failure_rate_pct'])}, {gap:.1f} points above the "
                f"overall rate of {m.fmt_pct(overall_fail)}.",
                "Look at error reasons and the checkout steps for this method." + extra))

    # --- Market + method combination ---------------------------------------------
    combo = m.summarize_payments(payments, ["market", "payment_method"])
    combo = combo[combo["checkout_attempts"] >= MIN_PAYMENT_ATTEMPTS]
    if len(combo) >= 2:
        worst = combo.loc[combo["payment_failure_rate_pct"].idxmax()]
        if worst["payment_failure_rate_pct"] - overall_fail >= PAYMENT_GAP_POINTS:
            items.append(_item(
                "Market + payment method",
                f"The highest observed failure rate is {worst['payment_method']} in "
                f"{worst['market']}: {m.fmt_pct(worst['payment_failure_rate_pct'])} "
                f"across {m.fmt_int(worst['checkout_attempts'])} attempts.",
                "Compare this combination with the same method in other markets to see "
                "whether the issue is market-specific (banks, networks, local rules) or method-wide."))

    # --- Market completion ----------------------------------------------------------
    by_market = m.summarize_payments(payments, "market")
    by_market = by_market[by_market["checkout_attempts"] >= MIN_PAYMENT_ATTEMPTS]
    if len(by_market) >= 2:
        worst = by_market.loc[by_market["checkout_completion_rate_pct"].idxmin()]
        gap = overall["checkout_completion_rate_pct"] - worst["checkout_completion_rate_pct"]
        if gap >= PAYMENT_GAP_POINTS:
            items.append(_item(
                "Market checkout completion",
                f"{worst['market']} has the lowest checkout completion rate "
                f"({m.fmt_pct(worst['checkout_completion_rate_pct'])}), {gap:.1f} points below "
                f"the overall rate.",
                "Check which payment methods are offered there and how their failure rates compare."))
    return items


def build_recommendations(campaigns, payments):
    """Combine marketing and payment recommendations. Always returns a list of dicts."""
    items = campaign_recommendations(campaigns) + payment_recommendations(payments)
    if not items:
        items.append(_item(
            "No clear flags",
            "No rule was triggered for the current selection, or there is too little data.",
            "Try selecting more markets, channels or campaigns."))
    return items
