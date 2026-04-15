import streamlit as st
import plotly.graph_objects as go
from ui_helpers import insight_toggle

BULL = "#4caf50"
BEAR = "#f44336"
NEUT = "#ff9800"
INFO = "#2196f3"
PURP = "#9c27b0"
BG   = "#181818"
BG2  = "#212121"
BDR  = "#303030"


def _sec(title, color=INFO):
    return (
        f"<div style='display:flex;align-items:center;gap:0.6rem;"
        f"margin:2.2rem 0 1rem;padding:0;'>"
        f"<div style='width:3px;height:18px;border-radius:2px;background:{color};"
        f"box-shadow:0 0 8px {color}44;'></div>"
        f"<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
        f"text-transform:uppercase;letter-spacing:0.8px;'>{title}</span></div>"
    )


def _glowbar(pct, color=BULL, height="5px"):
    pct = max(0, min(100, float(pct)))
    return (
        f"<div style='background:#1a1a1a;border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:linear-gradient(90deg,{color}cc,{color});border-radius:999px;"
        f"box-shadow:0 0 8px {color}55;'></div></div>"
    )

REGIME_COLOR = {"TREND": "#26A69A", "RANGE": "#4A9EFF", "VOLATILE": "#FF6B6B"}

REGIME_DESC = {
    "TREND":    "Market is making clear directional moves — momentum and trend-following strategies work best. Ride the direction.",
    "RANGE":    "Price is bouncing between a support floor and resistance ceiling — buy the dips, take profit at the top.",
    "VOLATILE": "Price is moving fast and unpredictably — high ATR with no clear direction. Reduce size, widen stops, wait for a clearer setup.",
}

REGIME_STRATEGY = {
    "TREND": [
        ("✅ Follow the trend",       "Enter in the trend direction. Use trailing stops to lock in profits."),
        ("✅ Buy pullbacks to EMA",   "Don’t chase the top. Wait for a dip to the 20 or 50 EMA then buy."),
        ("⚠️ Avoid counter-trades",  "Going against a strong trend has low odds. Wait for reversal confirmation first."),
    ],
    "RANGE": [
        ("✅ Buy at support",          "Enter near the lower bound where price has bounced before."),
        ("✅ Take profit at resistance", "Don’t be greedy — the upper bound is where sellers show up."),
        ("⚠️ Watch out for breakouts", "If price closes strongly above resistance, the range may be ending — that’s a new opportunity."),
    ],
    "VOLATILE": [
        ("⚠️ Cut your position size",  "In volatile markets, losses can be bigger than expected. Trade smaller."),
        ("✅ Widen your stop loss",    "Tight stops will get hit by noise. Give the trade more room, or skip it."),
        ("✅ Wait for a clear setup",  "Volatile regimes often transition to TREND or RANGE. Patience pays."),
        ("⚠️ Avoid breakout entries",  "Breakouts in volatile markets fail often. Wait for a confirmed close above/below the level."),
    ],
}


def _streak(df):
    regime = df["REGIME"].iloc[-1]
    count = 0
    for r in reversed(df["REGIME"].tolist()):
        if r == regime:
            count += 1
        else:
            break
    return count


def _stability(df, window=20):
    regime = df["REGIME"].iloc[-1]
    tail = df["REGIME"].tail(window)
    return round((tail == regime).sum() / len(tail) * 100, 1)


def _momentum(df, days=5):
    if len(df) < days + 1:
        return 0.0
    return (df["Close"].iloc[-1] / df["Close"].iloc[-(days + 1)] - 1) * 100


def _stat_tile(label, value, sub, val_color, bg, border, muted, bar_pct=None, bar_color=None):
    bar_html = ""
    if bar_pct is not None:
        bar_html = (
            f"<div style='margin-top:0.55rem;height:4px;background:#1a1a1a;"
            f"border-radius:2px;overflow:hidden;'>"
            f"<div style='width:{bar_pct:.0f}%;height:100%;background:{bar_color or val_color};"
            f"border-radius:2px;box-shadow:0 0 6px {bar_color or val_color}44;'></div></div>"
        )
    return (
        f"<div style='background:#1b1b1b;border:1px solid #272727;"
        f"border-radius:10px;padding:1rem 1.2rem;'>"
        f"<div style='font-size:0.62rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:0.8px;margin-bottom:0.45rem;font-weight:700;'>{label}</div>"
        f"<div style='font-size:1.3rem;font-weight:800;color:{val_color};line-height:1;'>{value}</div>"
        f"<div style='font-size:0.72rem;color:#666;margin-top:0.3rem;'>{sub}</div>"
        f"{bar_html}"
        f"</div>"
    )


def render_regime_analysis_tab(df, info_icon, create_regime_distribution_chart):
    theme_palette  = st.session_state.get('theme_palette', {})
    bg_card = theme_palette.get('panel_alt', BG2)
    bg_plot = theme_palette.get('panel', BG)
    border  = theme_palette.get('border', BDR)
    text    = theme_palette.get('text', '#ffffff')
    muted   = theme_palette.get('muted', '#9e9e9e')

    latest         = df.iloc[-1]
    current_price  = latest["Close"]
    current_regime = latest["REGIME"]
    rc             = REGIME_COLOR.get(current_regime, "#888")
    desc           = REGIME_DESC.get(current_regime, "")

    # ── computed metrics ──────────────────────────────────────────────────────
    streak       = _streak(df)
    stability    = _stability(df, 20)
    mom_5d       = _momentum(df, 5)
    mom_20d      = _momentum(df, 20)
    adx_val      = float(latest.get("ADX_14", 0) or 0)
    avg_vol_20   = df.tail(20)["Volume"].mean()
    vol_ratio    = (latest.get("Volume", 0) / avg_vol_20) if avg_vol_20 > 0 else 1.0
    vol_label    = "High" if vol_ratio >= 1.5 else "Low" if vol_ratio < 0.7 else "Normal"
    vol_col      = BULL if vol_ratio >= 1.5 else "#757575" if vol_ratio < 0.7 else NEUT
    adx_label    = "Strong" if adx_val >= 30 else "Weak" if adx_val < 20 else "Moderate"
    adx_col      = BULL if adx_val >= 30 else BEAR if adx_val < 20 else NEUT
    stability_col= BULL if stability >= 70 else NEUT if stability >= 45 else BEAR
    mom_col_5    = BULL if mom_5d  >= 0 else BEAR
    mom_col_20   = BULL if mom_20d >= 0 else BEAR
    mom_sign_5   = "+" if mom_5d  >= 0 else ""
    mom_sign_20  = "+" if mom_20d >= 0 else ""

    regime_counts = df["REGIME"].value_counts()
    total_days    = len(df)
    trend_days    = regime_counts.get("TREND",    0)
    range_days    = regime_counts.get("RANGE",    0)
    vol_days      = regime_counts.get("VOLATILE", 0)
    trend_pct     = round(trend_days / total_days * 100, 1) if total_days else 0
    range_pct     = round(range_days / total_days * 100, 1) if total_days else 0
    volatile_pct  = round(vol_days   / total_days * 100, 1) if total_days else 0

    # ── HERO CARD ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:#1b1b1b;border:1px solid #272727;
                border-radius:14px;overflow:hidden;margin-bottom:1.4rem;
                box-shadow:0 4px 24px rgba(0,0,0,0.3);">
        <div style="padding:1.6rem 2rem 1.4rem;
                    background:linear-gradient(135deg,rgba({','.join(str(int(rc[i:i+2],16)) for i in (1,3,5))},0.08),transparent);">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;
                        gap:1.2rem;flex-wrap:wrap;">
                <div>
                    <div style="font-size:0.62rem;color:#606060;text-transform:uppercase;
                                letter-spacing:1.2px;margin-bottom:0.55rem;font-weight:700;">
                        Current Market Regime</div>
                    <div style="display:flex;align-items:center;gap:0.9rem;">
                        <div style="width:48px;height:48px;border-radius:12px;
                                    background:rgba({','.join(str(int(rc[i:i+2],16)) for i in (1,3,5))},0.12);
                                    display:flex;align-items:center;justify-content:center;
                                    font-size:1.3rem;color:{rc};font-weight:900;">&#9673;</div>
                        <div style="font-size:2.4rem;font-weight:900;color:{rc};line-height:1;
                                    letter-spacing:-1px;text-shadow:0 0 20px {rc}33;">{current_regime}</div>
                    </div>
                    <div style="font-size:0.82rem;color:#888;margin-top:0.6rem;
                                max-width:460px;line-height:1.6;">{desc}</div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:0.62rem;color:#606060;text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:0.4rem;font-weight:700;">
                        Current Price</div>
                    <div style="font-size:2rem;font-weight:800;color:#e0e0e0;line-height:1;">
                        {current_price:.2f} SAR</div>
                    <div style="font-size:0.75rem;color:#666;margin-top:0.35rem;">
                        Active for <span style="color:{rc};font-weight:700;">{streak} days</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DISTRIBUTION ──────────────────────────────────────────────────────────
    st.markdown(_sec(f"Regime Distribution — {total_days} Days", rc), unsafe_allow_html=True)
    insight_toggle(
        "regime_dist",
        "What are TREND, RANGE, and VOLATILE regimes?",
        "<p><strong>TREND</strong> &mdash; The market is moving strongly in one direction. "
        "Price is above (bullish) or below (bearish) its moving averages, and ADX is above 25. "
        "Trend-following indicators (EMA, MACD) are most reliable in this regime.</p>"
        "<p><strong>RANGE</strong> &mdash; The market is moving sideways between support and resistance. "
        "ADX is below 20, price oscillates without a clear direction. "
        "Mean-reversion indicators (RSI, Stochastic, Bollinger Bands) perform best here.</p>"
        "<p><strong>VOLATILE</strong> &mdash; The market is making large, unpredictable swings in both directions. "
        "High ATR relative to recent history. All trade signals carry higher risk "
        "and tighter risk management (smaller positions, wider stops) is recommended.</p>"
        "<p>The <strong>Regime Distribution</strong> bar shows how the stock spent time in each state over the past period. "
        "A stock that was in TREND 70% of the time is a reliable trend-follower.</p>"
    )
    for label, days, pct, color in [
        ("Trend",    trend_days, trend_pct,    "#26A69A"),
        ("Range",    range_days, range_pct,    "#4A9EFF"),
        ("Volatile", vol_days,   volatile_pct, "#FF6B6B"),
    ]:
        st.markdown(
            f"<div style='background:#1b1b1b;border:1px solid #272727;"
            f"border-radius:12px;overflow:hidden;"
            f"margin-bottom:0.7rem;box-shadow:0 2px 12px rgba(0,0,0,0.15);'>"

            # header strip
            f"<div style='padding:0.85rem 1.3rem;border-bottom:1px solid #272727;"
            f"background:linear-gradient(135deg,rgba({','.join(str(int(color[i:i+2],16)) for i in (1,3,5))},0.07),transparent);"
            f"display:flex;justify-content:space-between;align-items:center;'>"
            f"<span style='font-size:0.88rem;font-weight:700;color:{color};'>{label}</span>"
            f"<div style='display:flex;align-items:center;gap:0.5rem;'>"
            f"<span style='font-size:0.75rem;color:#666;'>{days} days</span>"
            f"<span style='font-size:1rem;font-weight:800;color:{color};'>{pct}%</span>"
            f"</div>"
            f"</div>"

            # progress bar body
            f"<div style='padding:0.75rem 1.3rem;'>"
            + _glowbar(pct, color, "5px") +
            f"</div>"

            f"</div>",
            unsafe_allow_html=True,
        )

    # ── TIMELINE ─────────────────────────────────────────────────────────────
    st.markdown(_sec("Regime Timeline — Last 120 Days", INFO), unsafe_allow_html=True)
    insight_toggle(
        "regime_timeline",
        "How to read the Regime Timeline?",
        "<p>Each colored block on the timeline represents consecutive days the stock spent in the same regime. "
        "<strong style='color:#4caf50'>Green = TREND (bullish)</strong>, "
        "<strong style='color:#f44336'>Red = TREND (bearish)</strong>, "
        "<strong style='color:#ff9800'>Orange = RANGE</strong>, "
        "<strong style='color:#9e9e9e'>Grey = VOLATILE</strong>.</p>"
        "<p>Look for transitions: a shift from RANGE to TREND is often the start of a breakout. "
        "A shift from TREND to VOLATILE may signal exhaustion. "
        "Long runs of a single color indicate a persistent, reliable market condition.</p>"
    )
    timeline_df = df.tail(120).copy()
    fig = go.Figure()
    for regime, color in REGIME_COLOR.items():
        mask = timeline_df["REGIME"] == regime
        fig.add_trace(go.Bar(
            x=timeline_df.loc[mask, "Date"],
            y=[1] * mask.sum(),
            name=regime,
            marker_color=color,
            marker_line_width=0,
            width=86400000,
            hovertemplate=f"<b>{regime}</b><br>%{{x|%b %d %Y}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        height=110,
        plot_bgcolor="#1b1b1b",
        paper_bgcolor="#1b1b1b",
        font=dict(color="#666", family="Inter, Arial, sans-serif", size=11),
        xaxis=dict(gridcolor="#272727", showline=False, zeroline=False,
                   tickfont=dict(color="#666"), tickformat="%b %y"),
        yaxis=dict(visible=False),
        margin=dict(t=8, b=28, l=6, r=6),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color="#888"),
                    bgcolor="rgba(0,0,0,0)"),
        bargap=0,
    )
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": False})
