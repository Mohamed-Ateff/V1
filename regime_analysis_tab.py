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


def _normalize_regime_df(df):
    clean = df.copy()
    regimes = clean["REGIME"].astype("string").str.strip().str.upper()
    regimes = regimes.replace({
        "TRENDING": "TREND",
        "SIDEWAYS": "RANGE",
        "VOLATILITY": "VOLATILE",
    })
    regimes = regimes.where(regimes.isin(REGIME_COLOR.keys()))
    regimes = regimes.ffill().bfill().fillna("RANGE")
    clean["REGIME"] = regimes
    return clean


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
        f"<div style='font-size:0.75rem;color:#999;text-transform:uppercase;"
        f"letter-spacing:0.8px;margin-bottom:0.45rem;font-weight:700;'>{label}</div>"
        f"<div style='font-size:1.3rem;font-weight:800;color:{val_color};line-height:1;'>{value}</div>"
        f"<div style='font-size:0.72rem;color:#666;margin-top:0.3rem;'>{sub}</div>"
        f"{bar_html}"
        f"</div>"
    )


def get_regime_signal(df, cp):
    """Return a signal dict for the Decision Tab aggregator, or None if no trade."""
    if df is None or len(df) < 20:
        return None
    try:
        df = _normalize_regime_df(df)
        latest = df.iloc[-1]
        current_regime = str(latest["REGIME"])
        mom_5d  = _momentum(df, 5)
        mom_20d = _momentum(df, 20)
        adx_val = float(latest.get("ADX_14", 0) or 0)
        ema20   = float(latest.get("EMA_20", float(cp)) or float(cp))
        ema50   = float(latest.get("EMA_50", float(cp)) or float(cp))
        atr_val = float(latest.get("ATR_14", float(cp) * 0.02) or float(cp) * 0.02)
        stability = _stability(df, 20)
        streak    = _streak(df)

        # Score regime favorability for a long trade
        score = 50
        if current_regime == "TREND":
            score += 20 if mom_5d >= 0 else -10
            score += 10 if float(cp) > ema20 else -8
            score += 8  if adx_val >= 25 else (-5 if adx_val < 18 else 0)
        elif current_regime == "RANGE":
            score += 5 if float(cp) > ema20 else -5
            score -= 5 if float(cp) < ema50 else 0
        elif current_regime == "VOLATILE":
            score -= 20

        score += 5 if stability >= 60 else (-5 if stability < 35 else 0)
        score = max(0, min(100, score))

        # Only surface bullish regime setups
        if score < 52:
            return None

        is_buy  = current_regime == "TREND" and mom_5d >= 0 and float(cp) > ema20
        verdict = "▲ BUY" if is_buy else "▶ HOLD"
        reasons = [
            f"Regime: {current_regime} ({streak}d streak, {stability:.0f}% stability)",
            f"5D momentum {'+' if mom_5d >= 0 else ''}{mom_5d:.1f}%, ADX {adx_val:.0f}",
        ]

        _stop = round(float(cp) - 2 * atr_val, 2)
        _risk = max(float(cp) - _stop, 0.001)
        return dict(
            color="#26A69A",
            verdict_text=verdict,
            sublabel=f"Regime Analysis — {current_regime}",
            conf=score,
            reasons=reasons,
            entry=float(cp),
            stop=_stop,
            t1=round(float(cp) + _risk * 2.0, 2),
            t2=round(float(cp) + _risk * 3.5, 2),
            t3=round(float(cp) + _risk * 5.5, 2),
        )
    except Exception:
        return None


def render_regime_analysis_tab(df, info_icon, create_regime_distribution_chart):
    df = _normalize_regime_df(df)

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

    # ── DECISION BOX ─────────────────────────────────────────────────────────
    _atr_val = float(latest.get("ATR_14", current_price * 0.02) or current_price * 0.02)
    _ema20   = float(latest.get("EMA_20", current_price) or current_price)
    _ema50   = float(latest.get("EMA_50", current_price) or current_price)

    if current_regime == "TREND" and mom_5d >= 0 and current_price > _ema20:
        _dec_v    = "BUY"
        _dec_col  = BULL
        _dec_sub  = f"Regime is trending up — momentum and structure are aligned. Enter on dips to EMA20."
        _dec_entry = current_price
        _dec_stop  = round(current_price - 2 * _atr_val, 2)
        _dec_t1    = round(current_price + 2 * _atr_val, 2)
        _dec_t2    = round(current_price + 3.5 * _atr_val, 2)
        _dec_t3    = round(current_price + 5.5 * _atr_val, 2)
    elif current_regime == "VOLATILE" or (current_regime == "TREND" and mom_5d < 0):
        _dec_v    = "WAIT"
        _dec_col  = NEUT
        _dec_sub  = f"Volatile or trend reversing — risk is elevated. No new entries until regime stabilises."
        _dec_entry = _dec_stop = _dec_t1 = _dec_t2 = _dec_t3 = None
    else:
        _dec_v    = "HOLD"
        _dec_col  = "#4A9EFF"
        _dec_sub  = f"Range-bound regime with {stability:.0f}% stability. Wait for a breakout before entering."
        _dec_entry = _dec_stop = _dec_t1 = _dec_t2 = _dec_t3 = None

    _dec_rgb = {"BUY": "76,175,80", "WAIT": "255,152,0", "HOLD": "74,158,255"}.get(_dec_v, "74,158,255")

    _ladder_html = ""
    if _dec_v == "BUY" and _dec_entry:
        try:
            from _levels import price_ladder_html as _reg_plh
            _ladder_html = _reg_plh(_dec_entry, _dec_stop, _dec_t1, _dec_t2, _dec_t3, True)
        except Exception:
            pass

    # ── Tooltip CSS + helper ──────────────────────────────────────────────────
    st.markdown("""<style>
    .reg-tip-wrap{position:relative;display:inline-flex;align-items:center;cursor:help;margin-left:0.3rem}
    .reg-tip-wrap .reg-tt{
        visibility:hidden;opacity:0;position:absolute;bottom:130%;left:50%;
        transform:translateX(-50%);background:#1e1e1e;color:#ccc;border:1px solid #333;
        border-radius:6px;padding:0.45rem 0.6rem;font-size:0.7rem;font-weight:500;
        line-height:1.5;white-space:normal;width:220px;text-align:left;z-index:200;
        pointer-events:none;transition:opacity .15s;box-shadow:0 4px 14px rgba(0,0,0,.5);
        text-transform:none;letter-spacing:0}
    .reg-tip-wrap .reg-tt::after{content:'';position:absolute;top:100%;left:50%;
        transform:translateX(-50%);border:5px solid transparent;border-top-color:#333}
    .reg-tip-wrap:hover .reg-tt{visibility:visible;opacity:1}
    </style>""", unsafe_allow_html=True)

    def _rtip(text):
        return (
            f"<span class='reg-tip-wrap'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:13px;height:13px;border-radius:50%;border:1px solid #3a3a3a;"
            f"font-size:0.48rem;color:#666;font-weight:700;'>?</span>"
            f"<span class='reg-tt'>{text}</span></span>"
        )

    def _rlbl(text, tooltip=""):
        return (
            f"<div style='display:flex;align-items:center;margin-bottom:0.25rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>{text}</div>"
            + (_rtip(tooltip) if tooltip else "")
            + f"</div>"
        )

    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;"
        f"border-top:3px solid {_dec_col};border-radius:14px;overflow:hidden;margin-bottom:1.4rem;'>"
        f"<div style='padding:1.6rem 2rem 1.3rem;border-bottom:1px solid #222;"
        f"display:flex;align-items:flex-start;justify-content:space-between;gap:1.5rem;'>"
        f"<div>"
        f"<div style='font-size:0.72rem;color:#bbb;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.45rem;'>Decision</div>"
        f"<div style='font-size:3rem;font-weight:900;color:{_dec_col};"
        f"letter-spacing:-1.5px;line-height:1;'>{_dec_v}</div>"
        f"<div style='font-size:0.85rem;color:#bbb;margin-top:0.55rem;"
        f"font-weight:500;line-height:1.6;max-width:420px;'>{_dec_sub}</div>"
        f"</div>"
        f"<div style='text-align:right;flex-shrink:0;'>"
        f"<div style='display:flex;align-items:center;justify-content:flex-end;gap:0.3rem;margin-bottom:0.3rem;'>"
        f"<div style='font-size:0.72rem;color:#bbb;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;'>Regime</div>"
        + _rtip("Market condition detected by combining ADX, EMA direction, and ATR volatility. "
                "TREND = price moving strongly in one direction (ADX above 20, EMA sloping). "
                "RANGE = price bouncing between support and resistance. "
                "VOLATILE = large unpredictable swings — reduce size, wait for clarity.")
        + f"</div>"
        f"<div style='font-size:2rem;font-weight:900;color:{rc};line-height:1;"
        f"letter-spacing:-0.5px;'>{current_regime}</div>"
        f"<div style='font-size:0.7rem;color:#aaa;margin-top:0.25rem;'>{streak}d streak</div>"
        f"<div style='font-size:0.72rem;color:#777;line-height:1.5;margin-top:0.4rem;"
        f"max-width:200px;text-align:right;'>{desc}</div>"
        f"</div>"
        f"</div>"
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);"
        f"border-bottom:1px solid #222;'>"
        f"<div style='padding:0.85rem 1.2rem;border-right:1px solid #222;'>"
        + _rlbl("5D Momentum",
            "Price change over the last 5 trading days. "
            "Positive = short-term upward momentum. Negative = price is falling. "
            "20D momentum is shown as a secondary reference for the medium-term trend.")
        + f"<div style='font-size:1rem;font-weight:800;color:{mom_col_5};'>"
        f"{'+' if mom_5d >= 0 else ''}{mom_5d:.1f}%</div>"
        f"<div style='font-size:0.72rem;color:#aaa;margin-top:0.1rem;'>20D: {'+' if mom_20d >= 0 else ''}{mom_20d:.1f}%</div>"
        f"</div>"
        f"<div style='padding:0.85rem 1.2rem;border-right:1px solid #222;'>"
        + _rlbl("ADX",
            "Average Directional Index — measures trend strength, not direction. "
            "Above 30 = strong trend in whichever direction. "
            "20–30 = moderate trend. Below 20 = weak or no trend (choppy). "
            "High ADX in TREND regime = strong tailwind for momentum trades.")
        + f"<div style='font-size:1rem;font-weight:800;color:{adx_col};'>{adx_val:.0f}</div>"
        f"<div style='font-size:0.72rem;color:#aaa;margin-top:0.1rem;'>{adx_label}</div>"
        f"</div>"
        f"<div style='padding:0.85rem 1.2rem;border-right:1px solid #222;'>"
        + _rlbl("Volume",
            "Today's volume compared to the 20-day average. "
            "High (1.5×+) = strong market participation — confirms the move. "
            "Low (below 0.7×) = thin trading — moves are less reliable and easier to fake. "
            "Normal = average interest.")
        + f"<div style='font-size:1rem;font-weight:800;color:{vol_col};'>{vol_label}</div>"
        f"<div style='font-size:0.72rem;color:#aaa;margin-top:0.1rem;'>{vol_ratio:.1f}x avg</div>"
        f"</div>"
        f"<div style='padding:0.85rem 1.2rem;'>"
        + _rlbl("Stability",
            "How consistently the stock has been in its current regime over the last 20 sessions. "
            "70%+ = very stable — the regime is well-established. "
            "Below 35% = regime is flickering — mixed signals, be cautious. "
            "A stable TREND regime with high ADX is the ideal setup for momentum trades.")
        + f"<div style='font-size:1rem;font-weight:800;color:{stability_col};'>{stability:.0f}%</div>"
        f"<div style='font-size:0.72rem;color:#aaa;margin-top:0.1rem;'>last 20 sessions</div>"
        f"</div>"
        f"</div>"
        + (_ladder_html if _ladder_html else "")
        + f"</div>",
        unsafe_allow_html=True,
    )

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
