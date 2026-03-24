import streamlit as st
import plotly.graph_objects as go

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
        f"<div style='font-size:1rem;color:#ffffff;font-weight:700;"
        f"margin:2rem 0 1rem 0;border-bottom:2px solid {color}33;"
        f"padding-bottom:0.5rem;'>{title}</div>"
    )


def _glowbar(pct, color=BULL, height="8px"):
    pct = max(0, min(100, float(pct)))
    return (
        f"<div style='background:{BDR};border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:linear-gradient(90deg,{color}99,{color});border-radius:999px;'></div></div>"
    )

REGIME_COLOR = {"TREND": "#26A69A", "RANGE": "#4A9EFF", "VOLATILE": "#FF6B6B"}

REGIME_DESC = {
    "TREND":    "Market is making directional moves — momentum strategies work best.",
    "RANGE":    "Price is oscillating between support and resistance — mean-reversion setups favoured.",
    "VOLATILE": "Choppy and unpredictable action — reduce size, widen stops, avoid breakouts.",
}

REGIME_STRATEGY = {
    "TREND": [
        ("✅ Ride the trend",       "Follow the direction with trailing stops."),
        ("✅ Breakout entries",     "Buy pullbacks to EMA, not parabolic tops."),
        ("⚠️ Avoid counter-trend", "Mean-reversion has poor odds in strong trends."),
    ],
    "RANGE": [
        ("✅ Buy at support",          "Enter near the lower bound of the range."),
        ("✅ Sell at resistance",       "Take profit near the upper bound of the range."),
        ("⚠️ Avoid breakout trades",  "False breakouts are common in ranging markets."),
    ],
    "VOLATILE": [
        ("⚠️ Reduce position size", "Wider swings mean larger drawdowns."),
        ("✅ Wait for clarity",      "Let volatility settle before entering new positions."),
        ("⚠️ Avoid tight stops",    "Price will whipsaw through normal stop levels."),
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
            f"<div style='margin-top:0.55rem;height:4px;background:rgba(255,255,255,0.06);"
            f"border-radius:2px;overflow:hidden;'>"
            f"<div style='width:{bar_pct:.0f}%;height:100%;background:{bar_color or val_color};"
            f"border-radius:2px;'></div></div>"
        )
    return (
        f"<div style='background:{bg};border:1px solid {border};"
        f"border-radius:12px;padding:1.1rem 1.3rem;'>"
        f"<div style='font-size:0.67rem;color:{muted};text-transform:uppercase;"
        f"letter-spacing:0.8px;margin-bottom:0.45rem;font-weight:600;'>{label}</div>"
        f"<div style='font-size:1.25rem;font-weight:800;color:{val_color};line-height:1;'>{value}</div>"
        f"<div style='font-size:0.73rem;color:{muted};margin-top:0.3rem;'>{sub}</div>"
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
    <div style="background:{bg_card};border:1px solid {border};border-left:5px solid {rc};
                border-radius:16px;padding:1.8rem 2rem 1.5rem;margin-bottom:1.2rem;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;
                    gap:1rem;flex-wrap:wrap;">
            <div>
                <div style="font-size:0.70rem;color:{muted};text-transform:uppercase;
                            letter-spacing:1.1px;margin-bottom:0.5rem;font-weight:600;">
                    Current Market Regime</div>
                <div style="font-size:2.8rem;font-weight:900;color:{rc};line-height:1;
                            letter-spacing:-0.5px;">{current_regime}</div>
                <div style="font-size:0.88rem;color:{muted};margin-top:0.55rem;
                            max-width:460px;line-height:1.5;">{desc}</div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="font-size:0.70rem;color:{muted};text-transform:uppercase;
                            letter-spacing:1px;margin-bottom:0.35rem;font-weight:600;">
                    Current Price</div>
                <div style="font-size:2.0rem;font-weight:800;color:{text};line-height:1;">
                    {current_price:.2f} SAR</div>
                <div style="font-size:0.75rem;color:{muted};margin-top:0.3rem;">
                    Active for <span style="color:{rc};font-weight:700;">{streak} days</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DISTRIBUTION ──────────────────────────────────────────────────────────
    st.markdown(_sec(f"Regime Distribution — {total_days} Days", rc), unsafe_allow_html=True)
    for label, days, pct, color in [
        ("Trend",    trend_days, trend_pct,    "#26A69A"),
        ("Range",    range_days, range_pct,    "#4A9EFF"),
        ("Volatile", vol_days,   volatile_pct, "#FF6B6B"),
    ]:
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {BDR};"
            f"border-top:3px solid {color};border-radius:12px;"
            f"padding:1rem 1.3rem;margin-bottom:0.6rem;'>"
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:baseline;margin-bottom:0.6rem;'>"
            f"<span style='font-size:0.90rem;font-weight:700;color:{color};'>{label}</span>"
            f"<span style='font-size:0.80rem;color:#9e9e9e;'>{days} days &nbsp;·&nbsp;"
            f"<span style='color:{color};font-weight:700;'>{pct}%</span></span>"
            f"</div>"
            + _glowbar(pct, color, "6px") +
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── TIMELINE ─────────────────────────────────────────────────────────────
    st.markdown(_sec("Regime Timeline — Last 120 Days", INFO), unsafe_allow_html=True)
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
        plot_bgcolor=bg_plot,
        paper_bgcolor=bg_plot,
        font=dict(color=muted, family="Inter, Arial, sans-serif", size=11),
        xaxis=dict(gridcolor=border, showline=False, zeroline=False,
                   tickfont=dict(color=muted), tickformat="%b %y"),
        yaxis=dict(visible=False),
        margin=dict(t=8, b=28, l=6, r=6),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(color=muted),
                    bgcolor="rgba(0,0,0,0)"),
        bargap=0,
    )
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": False})
