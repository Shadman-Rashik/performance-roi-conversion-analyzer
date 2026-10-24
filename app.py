"""
app.py  -  Performance ROI & Conversion Drop-off Analyzer (Streamlit dashboard)

Run:  python -m streamlit run app.py

How the pieces fit together:
  * SQLite database (data/analytics.db) = where the data is stored (a single file)
  * This Python script (app.py)         = reads the data, calculates metrics, builds charts
  * Your web browser                    = shows the interactive page that Streamlit serves locally

All data is SYNTHETIC. Money is in USD.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import metrics as m
import recommendations as rec
import validate_data as vd

APP_TITLE = "Performance ROI & Conversion Drop-off Analyzer"
DB_PATH = Path(__file__).parent / "data" / "analytics.db"

st.set_page_config(page_title=APP_TITLE, layout="wide")


# -----------------------------------------------------------------------------
# Loading data
# -----------------------------------------------------------------------------

@st.cache_data
def load_data(db_path):
    return vd.load_tables(db_path)


if not DB_PATH.exists():
    st.title(APP_TITLE)
    st.error("The database file was not found.")
    st.markdown(
        "Open a terminal in the project folder and run these two commands, "
        "then refresh this page:\n\n"
        "```\npython generate_data.py\npython build_database.py\n```")
    st.stop()

campaigns_all, payments_all = load_data(str(DB_PATH))
quality_problems = vd.validate_campaigns(campaigns_all) + vd.validate_payments(payments_all)


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------

st.title(APP_TITLE)
st.info(
    "**Synthetic data.** Every number in this dashboard is randomly generated for a "
    "portfolio project. It is not real company or market data. All money values are in USD."
)


# -----------------------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------------------

st.sidebar.header("Filters")

market_options = sorted(campaigns_all["market"].unique())
selected_markets = st.sidebar.multiselect("Market", market_options, default=market_options)

channel_options = sorted(
    campaigns_all.loc[campaigns_all["market"].isin(selected_markets), "marketing_channel"].unique())
selected_channels = st.sidebar.multiselect(
    "Marketing channel", channel_options, default=channel_options)

campaign_pool = campaigns_all[
    campaigns_all["market"].isin(selected_markets)
    & campaigns_all["marketing_channel"].isin(selected_channels)
]
campaign_options = sorted(campaign_pool["campaign_name"].unique())
selected_campaigns = st.sidebar.multiselect(
    "Campaign", campaign_options, default=campaign_options)

st.sidebar.caption(
    "Market filters both marketing and payment data. Channel and Campaign filters apply to "
    "marketing data only, because the payment table is summarised by market and payment "
    "method and is not linked to individual campaigns.")

campaigns = campaign_pool[campaign_pool["campaign_name"].isin(selected_campaigns)]
payments = payments_all[payments_all["market"].isin(selected_markets)]

if campaigns.empty:
    st.warning("No campaigns match the current filters. Select at least one value in each filter.")
    st.stop()

st.sidebar.markdown(f"**{len(campaigns)}** campaign(s) selected")


# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------

tab_overview, tab_marketing, tab_funnel, tab_payments, tab_reco, tab_about = st.tabs([
    "Executive Overview", "Marketing Performance", "Conversion Funnel",
    "Checkout & Payments", "Recommendations", "About & Methodology",
])


# ---------------------------- A. Executive overview ---------------------------
with tab_overview:
    st.subheader("Executive Overview")
    k = m.campaign_kpis(campaigns)

    row1 = st.columns(3)
    row1[0].metric("Marketing Spend", m.fmt_money(k["marketing_spend"]))
    row1[1].metric("Attributed Revenue", m.fmt_money(k["attributed_revenue"]))
    row1[2].metric("Revenue-Based ROI", m.fmt_pct(k["roi_pct"]),
                   help="(Attributed Revenue - Marketing Spend) / Marketing Spend x 100. "
                        "This is NOT net-profit ROI: product, operating and other costs are not included.")
    row2 = st.columns(3)
    row2[0].metric("Purchases", m.fmt_int(k["purchases"]))
    row2[1].metric("Cost per Acquisition (CPA)", m.fmt_money(k["cpa"], 2),
                   help="Marketing Spend / Purchases")
    row2[2].metric("Purchase Conversion Rate", m.fmt_pct(k["conversion_rate_pct"], 2),
                   help="Purchases / Landing Page Visitors x 100")

    st.caption("Revenue-based ROI ignores product costs and other expenses, so it is not the same as net-profit ROI.")

    by_market = m.summarize_campaigns(campaigns, "market")
    long = by_market.melt(id_vars="market", value_vars=["marketing_spend", "attributed_revenue"],
                          var_name="Measure", value_name="USD")
    long["Measure"] = long["Measure"].map(
        {"marketing_spend": "Marketing spend", "attributed_revenue": "Attributed revenue"})
    fig = px.bar(long, x="market", y="USD", color="Measure", barmode="group",
                 title="Marketing spend vs attributed revenue by market")
    fig.update_layout(xaxis_title=None)
    st.plotly_chart(fig, key="overview_market")

    with st.expander("Data quality checks"):
        if quality_problems:
            st.error("Problems found in the data:")
            for p in quality_problems:
                st.write("- " + p)
        else:
            st.success("All validation checks passed (funnel order, payment totals, no missing values).")


# ---------------------------- B. Marketing performance ------------------------
with tab_marketing:
    st.subheader("Marketing Performance")
    by_channel = m.summarize_campaigns(campaigns, "marketing_channel")

    col1, col2 = st.columns(2)
    with col1:
        d = by_channel.sort_values("roi_pct")
        fig = px.bar(d, x="roi_pct", y="marketing_channel", orientation="h", text_auto=".0f",
                     title="Revenue-based ROI (%) by marketing channel",
                     labels={"roi_pct": "ROI (%)", "marketing_channel": "Channel"})
        fig.add_vline(x=0, line_dash="dash")
        st.plotly_chart(fig, key="roi_by_channel")
    with col2:
        d = by_channel.dropna(subset=["cpa"]).sort_values("cpa")
        fig = px.bar(d, x="marketing_channel", y="cpa", text_auto=".2f",
                     title="Cost per acquisition (CPA, USD) by channel - lower is cheaper",
                     labels={"cpa": "CPA (USD)", "marketing_channel": "Channel"})
        st.plotly_chart(fig, key="cpa_by_channel")

    long = by_channel.melt(id_vars="marketing_channel",
                           value_vars=["marketing_spend", "attributed_revenue"],
                           var_name="Measure", value_name="USD")
    long["Measure"] = long["Measure"].map(
        {"marketing_spend": "Marketing spend", "attributed_revenue": "Attributed revenue"})
    fig = px.bar(long, x="marketing_channel", y="USD", color="Measure", barmode="group",
                 title="Marketing spend vs attributed revenue by channel")
    fig.update_layout(xaxis_title=None)
    st.plotly_chart(fig, key="spend_vs_revenue_channel")

    per_campaign = m.summarize_campaigns(
        campaigns, ["campaign_id", "campaign_name", "market", "marketing_channel"])

    fig = px.scatter(per_campaign, x="marketing_spend", y="attributed_revenue",
                     color="marketing_channel", hover_name="campaign_name",
                     hover_data={"market": True, "roi_pct": ":.0f", "marketing_spend": ":,.0f",
                                 "attributed_revenue": ":,.0f"},
                     title="Each campaign: spend vs attributed revenue (points below the dashed line returned less than they cost)",
                     labels={"marketing_spend": "Marketing spend (USD)",
                             "attributed_revenue": "Attributed revenue (USD)"})
    axis_max = float(max(per_campaign["marketing_spend"].max(),
                         per_campaign["attributed_revenue"].max()))
    fig.add_trace(go.Scatter(x=[0, axis_max], y=[0, axis_max], mode="lines",
                             line=dict(dash="dash"), name="Break-even (revenue = spend)"))
    st.plotly_chart(fig, key="campaign_scatter")

    st.markdown("#### Campaign performance ranking")
    sort_options = {
        "Revenue-based ROI (%)": ("roi_pct", False),
        "Attributed revenue": ("attributed_revenue", False),
        "Purchase conversion rate (%)": ("conversion_rate_pct", False),
        "CPA (lowest first)": ("cpa", True),
        "Marketing spend": ("marketing_spend", False),
    }
    c1, c2 = st.columns([2, 1])
    sort_label = c1.selectbox("Rank campaigns by", list(sort_options.keys()))
    top_n = c2.slider("Rows to show", min_value=5, max_value=30, value=10)
    sort_col, ascending = sort_options[sort_label]

    ranking = per_campaign.sort_values(sort_col, ascending=ascending, na_position="last").head(top_n)
    ranking = ranking[["campaign_name", "market", "marketing_channel", "marketing_spend",
                       "attributed_revenue", "roi_pct", "cpa", "conversion_rate_pct", "purchases"]].copy()
    ranking.columns = ["Campaign", "Market", "Channel", "Spend (USD)", "Revenue (USD)",
                       "ROI (%)", "CPA (USD)", "Conv. rate (%)", "Purchases"]
    ranking = ranking.round({"Spend (USD)": 0, "Revenue (USD)": 0, "ROI (%)": 1,
                             "CPA (USD)": 2, "Conv. rate (%)": 2})
    st.dataframe(ranking, hide_index=True)
    st.caption("CPA shows as empty where a campaign had no purchases (division by zero is avoided).")


# ---------------------------- C. Conversion funnel -----------------------------
with tab_funnel:
    st.subheader("Conversion Funnel")
    funnel = m.funnel_table(campaigns)
    biggest = m.largest_dropoff(funnel)

    fig = go.Figure(go.Funnel(
        y=funnel["stage"], x=funnel["count"], textinfo="value+percent initial"))
    fig.update_layout(title="Landing Page Visitors to Purchases (selected campaigns)")
    st.plotly_chart(fig, key="funnel_chart")

    if biggest is not None:
        st.warning(
            f"Largest observed drop-off: **{biggest['step']}** - "
            f"{m.fmt_pct(biggest['step_dropoff_pct'])} of people did not continue "
            f"({m.fmt_int(biggest['lost_from_previous'])} lost).")

    steps = funnel.iloc[1:].copy()
    colors = ["#d62728" if (biggest is not None and s == biggest["step"]) else "#1f77b4"
              for s in steps["step"]]
    fig = go.Figure(go.Bar(x=steps["step"], y=steps["step_dropoff_pct"], marker_color=colors,
                           text=steps["step_dropoff_pct"].round(1).astype(str) + "%"))
    fig.update_layout(title="Drop-off rate between funnel steps (largest in red)",
                      yaxis_title="Drop-off (%)", xaxis_title=None)
    st.plotly_chart(fig, key="dropoff_chart")

    table = funnel[["stage", "count", "step_conversion_pct", "step_dropoff_pct",
                    "lost_from_previous", "pct_of_first_stage"]].copy()
    table.columns = ["Stage", "People", "Continued from previous (%)", "Drop-off from previous (%)",
                     "Lost from previous", "Share of first stage (%)"]
    st.dataframe(table.round(1), hide_index=True)

    st.markdown("#### Compare drop-off across segments")
    compare_by = st.radio("Group by", ["market", "marketing_channel"], horizontal=True,
                          format_func=lambda x: "Market" if x == "market" else "Marketing channel")
    heat = m.dropoff_by_group(campaigns, compare_by)
    if len(heat) >= 1:
        fig = px.imshow(heat.round(1), text_auto=".1f", aspect="auto", color_continuous_scale="Reds",
                        labels={"color": "Drop-off (%)"},
                        title="Drop-off (%) at each step - darker means a bigger drop")
        st.plotly_chart(fig, key="dropoff_heatmap")
    st.caption("Each step's drop-off = people who did not reach the next stage as a share of the previous stage. "
               "Some drop-off at every step is normal; compare segments to find where to look.")


# ---------------------------- D. Checkout and payments -------------------------
with tab_payments:
    st.subheader("Checkout & Payment Analysis")
    st.caption("Filtered by Market only. This table is aggregated by market and payment method and "
               "has no link to campaigns, so Channel and Campaign filters do not apply here.")

    if payments.empty:
        st.warning("No payment data for the selected markets.")
    else:
        overall = m.summarize_payments(payments).iloc[0]
        c = st.columns(3)
        c[0].metric("Checkout attempts", m.fmt_int(overall["checkout_attempts"]))
        c[1].metric("Checkout completion rate", m.fmt_pct(overall["checkout_completion_rate_pct"]),
                    help="Successful payments / checkout attempts x 100")
        c[2].metric("Payment failure rate", m.fmt_pct(overall["payment_failure_rate_pct"]),
                    help="Failed payments / checkout attempts x 100")

        by_method = m.summarize_payments(payments, "payment_method").sort_values(
            "payment_failure_rate_pct", ascending=False)
        by_market_pay = m.summarize_payments(payments, "market").sort_values(
            "checkout_completion_rate_pct")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(by_method, x="payment_method", y="payment_failure_rate_pct", text_auto=".1f",
                         hover_data={"checkout_attempts": ":,"},
                         title="Payment failure rate (%) by payment method",
                         labels={"payment_failure_rate_pct": "Failure rate (%)",
                                 "payment_method": "Payment method"})
            st.plotly_chart(fig, key="fail_by_method")
        with col2:
            fig = px.bar(by_market_pay, x="market", y="checkout_completion_rate_pct", text_auto=".1f",
                         hover_data={"checkout_attempts": ":,"},
                         title="Checkout completion rate (%) by market",
                         labels={"checkout_completion_rate_pct": "Completion rate (%)", "market": "Market"})
            fig.update_yaxes(range=[0, 100])
            st.plotly_chart(fig, key="completion_by_market")

        combo = m.summarize_payments(payments, ["market", "payment_method"])
        pivot = combo.pivot(index="market", columns="payment_method",
                            values="payment_failure_rate_pct")
        fig = px.imshow(pivot.round(1), text_auto=".1f", aspect="auto", color_continuous_scale="Reds",
                        labels={"color": "Failure rate (%)"},
                        title="Payment failure rate (%) by market and payment method (blank = method not offered)")
        st.plotly_chart(fig, key="fail_heatmap")

        detail = combo.sort_values("payment_failure_rate_pct", ascending=False)[
            ["market", "payment_method", "checkout_attempts", "successful_payments",
             "failed_payments", "completed_orders", "checkout_completion_rate_pct",
             "payment_failure_rate_pct"]].copy()
        detail.columns = ["Market", "Payment method", "Attempts", "Successful", "Failed",
                          "Completed orders", "Completion rate (%)", "Failure rate (%)"]
        st.dataframe(detail.round(1), hide_index=True)
        st.caption("For Cash on Delivery, 'failed' means the order was not confirmed (a synthetic definition). "
                   "Compare attempts as well as rates: a high rate on few attempts is less reliable.")


# ---------------------------- F. Recommendations --------------------------------
with tab_reco:
    st.subheader("Data-Supported Recommendations")
    st.caption("Rule-based and recalculated from your current filters.")
    for item in rec.build_recommendations(campaigns, payments):
        st.markdown(f"**{item['area']}**")
        st.write(item["observation"])
        st.write("*Worth investigating:* " + item["suggestion"])
        st.divider()
    st.info(rec.CAVEAT)


# ---------------------------- About ---------------------------------------------
with tab_about:
    st.subheader("About & Methodology")
    st.markdown(
        """
**Purpose.** A portfolio project that shows how marketing spend, attributed revenue, funnel
drop-off and payment outcomes can be analysed with SQL, Python (Pandas) and an interactive dashboard.

**Data.** Fully synthetic and randomly generated (fixed seed, so it is reproducible). It is
*inspired by* Bangladesh and international markets but it is **not** real data, and nothing here
should be read as a real market finding.

**Currency.** All money values are in one reporting currency, **USD**. No exchange-rate conversion
is applied. The USD amounts are synthetic.

**Metric definitions**
- Revenue-Based ROI (%) = (Attributed Revenue - Marketing Spend) / Marketing Spend x 100
- CPA = Marketing Spend / Purchases
- CTR (%) = Clicks / Impressions x 100
- Purchase Conversion Rate (%) = Purchases / Landing Page Visitors x 100
- Funnel step drop-off (%) = 100 - (people at this stage / people at the previous stage x 100)
- Checkout Completion Rate (%) = Successful Payments / Checkout Attempts x 100
- Payment Failure Rate (%) = Failed Payments / Checkout Attempts x 100

Totals are calculated by adding up raw counts first and dividing afterwards. A zero or missing
denominator gives "N/A" instead of an error.

**Limitations**
- Revenue-based ROI is **not** net-profit ROI. Product costs, operating costs and other expenses are not included.
- Attribution is simplified: each purchase is credited to one campaign.
- Payment data is aggregated by market and payment method and is **not linked** to campaigns.
- Patterns shown here are observations to investigate; they do not prove cause and effect.
- Small groups can produce noisy rates.
        """
    )
