import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
from favorites_tab import render_save_button
from ui_helpers import insight_toggle


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DESIGN TOKENS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BULL = "#4caf50"
BEAR = "#f44336"
NEUT = "#ff9800"
INFO = "#2196f3"
PURP = "#9c27b0"
GOLD = "#FFD700"
BG   = "#181818"
BG2  = "#212121"
BDR  = "#303030"


def _hex_rgba(hex_color, alpha=0.12):
    hc = str(hex_color).strip().lstrip("#")
    if len(hc) != 6:
        return f"rgba(127,127,127,{alpha})"
    r, g, b = int(hc[:2], 16), int(hc[2:4], 16), int(hc[4:], 16)
    return f"rgba({r},{g},{b},{alpha})"


def signal_analysis_tab(df, info_icon):

    from signal_engine import (
        detect_signals, evaluate_signal_success,
        find_consensus_signals, analyze_indicator_combinations,
        calculate_monthly_performance,
    )
    from charts import (
        create_ema_chart, create_adx_chart, create_rsi_chart,
        create_macd_chart, create_bollinger_bands_chart,
        create_stochastic_chart,
    )

    theme_palette = st.session_state.get("theme_palette", {})
    panel     = theme_palette.get("panel",     BG)
    panel_alt = theme_palette.get("panel_alt", BG2)
    border    = theme_palette.get("border",    BDR)
    text_col  = theme_palette.get("text",      "#ffffff")
    muted     = theme_palette.get("muted",     "#9e9e9e")

    # â”€â”€ CSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown(f"""
    <style>
    .sa-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 0.65rem;
        margin-bottom: 1.2rem;
    }}
    .sa-kpi-card {{
        background: {panel_alt};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 0.8rem 0.85rem;
    }}
    .sa-kpi-label {{
        font-size: 0.62rem;
        color: {muted};
        text-transform: uppercase;
        letter-spacing: 0.7px;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }}
    .sa-kpi-value {{
        font-size: 1.55rem;
        font-weight: 900;
        line-height: 1;
    }}
    .sa-kpi-sub {{
        font-size: 0.68rem;
        color: {muted};
        margin-top: 0.25rem;
        font-weight: 600;
    }}
    </style>
    """, unsafe_allow_html=True)

    # â”€â”€ Controls row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        st.markdown(
            f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
            f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Risk</div>",
            unsafe_allow_html=True,
        )
        risk_val = st.number_input(
            "Risk", min_value=1, max_value=100, value=1, step=1,
            label_visibility="collapsed", key="sa_risk_val",
        )
    with c2:
        st.markdown(
            f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
            f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Reward</div>",
            unsafe_allow_html=True,
        )
        reward_val = st.number_input(
            "Reward", min_value=1, max_value=100, value=2, step=1,
            label_visibility="collapsed", key="sa_reward_val",
        )
    with c3:
        st.markdown(
            f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
            f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Holding Period</div>",
            unsafe_allow_html=True,
        )
        _period_map   = {"Short (5d)": 5, "Medium (63d)": 63, "Long (252d)": 252}
        _period_label = st.selectbox(
            "Period", list(_period_map.keys()), index=1,
            label_visibility="collapsed", key="sa_period_val",
        )
        holding_period = _period_map[_period_label]
    with c4:
        st.markdown(
            f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
            f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Combo Depth</div>",
            unsafe_allow_html=True,
        )
        _depth_opts = {"Pairs only (2)": 2, "Up to Triples (3)": 3,
                       "Up to Quads (4)": 4, "Up to 5-Way (5)": 5, "Up to 6-Way (6)": 6}
        _depth_label = st.selectbox(
            "Depth", list(_depth_opts.keys()), index=2,
            label_visibility="collapsed", key="sa_combo_depth",
        )
        max_combo_depth = _depth_opts[_depth_label]

    stop_loss     = 0.02
    rr_ratio      = reward_val / risk_val
    profit_target = stop_loss * rr_ratio

    # â”€â”€ Run engines â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with st.spinner("Running signal analysisâ€¦"):
        signals_df = detect_signals(df)
        results, successful_signals, all_signal_details = evaluate_signal_success(
            df, signals_df, profit_target, holding_period, stop_loss
        )
        consensus_signals   = find_consensus_signals(signals_df)
        combo_results       = analyze_indicator_combinations(
            signals_df, df, profit_target, holding_period, stop_loss, max_combo_depth
        )
        monthly_performance = calculate_monthly_performance(all_signal_details)

    # â”€â”€ Aggregate stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    total_signals    = sum(d["total_signals"] for d in results.values())
    total_successful = len(successful_signals)
    overall_success  = (total_successful / total_signals * 100) if total_signals > 0 else 0.0
    total_failed     = total_signals - total_successful

    all_gains  = [s["gain"] for s in all_signal_details if s["gain"] > 0]
    all_losses = [abs(s["gain"]) for s in all_signal_details if s["gain"] < 0]
    actual_avg_gain = float(np.mean(all_gains))  if all_gains  else 0.0
    actual_avg_loss = float(np.mean(all_losses)) if all_losses else 0.0
    actual_rr       = round(actual_avg_gain / actual_avg_loss, 2) if actual_avg_loss > 0 else 0.0
    pf_overall      = round(sum(all_gains) / sum(all_losses), 2) \
                      if all_losses and sum(all_losses) > 0 else 0.0
    expectancy_all  = round(
        (overall_success / 100) * actual_avg_gain -
        (1 - overall_success / 100) * actual_avg_loss, 2
    )
    insight_toggle(
        "kpi_metrics",
        "What do these 6 performance numbers mean?",
        "<p><strong>Win Rate</strong> &mdash; Percentage of signals where price hit the profit target before hitting the stop loss. "
        "Above 50% means the indicator was right more than wrong.</p>"
        "<p><strong>Total Signals</strong> &mdash; How many times this indicator fired during the backtested period.</p>"
        "<p><strong>Successful Signals</strong> &mdash; Signals that resulted in a win (target reached first).</p>"
        "<p><strong>Failed Signals</strong> &mdash; Signals that were stopped out (stop loss hit first).</p>"
        "<p><strong>Profit Factor</strong> &mdash; Total winning gain &divide; total losses. "
        "A value above 1.5 means the strategy generates 1.5x more profit than it loses &mdash; a solid edge. Below 1.0 = net loser.</p>"
        "<p><strong>Expectancy</strong> &mdash; Average return per signal = (Win Rate &times; Avg Gain) &minus; (Loss Rate &times; Avg Loss). "
        "A positive expectancy means the strategy has a mathematical edge over time.</p>"
    )
    
    # â”€â”€ Wilson lower-bound helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _wilson(n, pct):
        if n == 0:
            return 0.0
        p = pct / 100
        z = 1.645
        denom  = 1 + z * z / n
        centre = p + z * z / (2 * n)
        spread = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
        return (centre - spread) / denom * 100

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # 1. KPI ROW  (6 tiles)
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    sc      = BULL if overall_success >= 50 else BEAR
    pf_col  = BULL if pf_overall >= 1.5 else NEUT if pf_overall >= 1.0 else BEAR
    exp_col = BULL if expectancy_all > 0 else BEAR

    st.markdown(f"""
    <div class='sa-kpi-grid'>
        <div class='sa-kpi-card' style='border-top:3px solid {INFO};'>
            <div class='sa-kpi-label'>Total Signals</div>
            <div class='sa-kpi-value' style='color:{INFO};'>{total_signals}</div>
            <div class='sa-kpi-sub'>All indicators</div>
        </div>
        <div class='sa-kpi-card' style='border-top:3px solid {BULL};'>
            <div class='sa-kpi-label'>Successful</div>
            <div class='sa-kpi-value' style='color:{BULL};'>{total_successful}</div>
            <div class='sa-kpi-sub'>Hit {risk_val}:{reward_val} target</div>
        </div>
        <div class='sa-kpi-card' style='border-top:3px solid {BEAR};'>
            <div class='sa-kpi-label'>Failures</div>
            <div class='sa-kpi-value' style='color:{BEAR};'>{total_failed}</div>
            <div class='sa-kpi-sub'>Missed target</div>
        </div>
        <div class='sa-kpi-card' style='border-top:3px solid {sc};'>
            <div class='sa-kpi-label'>Win Rate</div>
            <div class='sa-kpi-value' style='color:{sc};'>{overall_success:.1f}%</div>
            <div class='sa-kpi-sub'>Overall hit rate</div>
        </div>
        <div class='sa-kpi-card' style='border-top:3px solid {pf_col};'>
            <div class='sa-kpi-label'>Profit Factor</div>
            <div class='sa-kpi-value' style='color:{pf_col};'>{pf_overall:.2f}</div>
            <div class='sa-kpi-sub'>Gross W / Gross L</div>
        </div>
        <div class='sa-kpi-card' style='border-top:3px solid {exp_col};'>
            <div class='sa-kpi-label'>Expectancy</div>
            <div class='sa-kpi-value' style='color:{exp_col};'>{expectancy_all:+.2f}%</div>
            <div class='sa-kpi-sub'>Per-trade edge</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # SUB-TABS
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    tab_ind, tab_combo = st.tabs([
        "Indicator Leaderboard",
        "Indicator Combinations",
    ])

    # â”€â”€ indicator map (key â†’ name, category, chart_fn) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    indicator_map = {
        "EMA":   ("EMA (20/50/200)",       "Trend Following",     create_ema_chart),
        "SMA":   ("SMA (50/200)",           "Trend Following",     None),
        "PSAR":  ("Parabolic SAR",          "Trend Reversal",      None),
        "ICHI":  ("Ichimoku Cloud",         "Trend & S/R",         None),
        "WMA":   ("WMA (20)",               "Trend Following",     None),
        "RSI":   ("RSI (14)",               "Momentum",            create_rsi_chart),
        "MACD":  ("MACD (12/26/9)",         "Momentum",            create_macd_chart),
        "STOCH": ("Stochastic (14,3,3)",    "Reversal",            create_stochastic_chart),
        "ROC":   ("ROC (12)",               "Momentum",            None),
        "CCI":   ("CCI (20)",               "Oscillator",          None),
        "WILLR": ("Williams %R (14)",       "Oscillator",          None),
        "BB":    ("Bollinger Bands (20,2)", "Volatility",          create_bollinger_bands_chart),
        "KC":    ("Keltner Channel",        "Volatility Breakout", None),
        "DC":    ("Donchian (20)",          "Breakout",            None),
        "MFI":   ("MFI (14)",              "Volume Momentum",     None),
        "CMF":   ("CMF (20)",              "Volume Flow",         None),
        "VWAP":  ("VWAP",                  "Volume Anchor",       None),
        "OBV":   ("OBV",                   "Volume Trend",        None),
        "ADX":   ("ADX (14) +DI/-DI",      "Trend Strength",      create_adx_chart),
    }

    # â”€â”€ build per-indicator stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    succ_by_ind = {}
    for s in successful_signals:
        succ_by_ind.setdefault(s["indicator"], []).append(s["gain"])

    indicator_performance = []
    regime_color_map = {"TREND": INFO, "RANGE": NEUT, "VOLATILE": BEAR}

    for key, (name, category, chart_fn) in indicator_map.items():
        if key not in results:
            continue
        data  = results[key]
        total = data.get("total_signals", 0)
        if total <= 0:
            continue

        succ_gains  = succ_by_ind.get(key, [])
        win_count   = len(succ_gains)
        win_rate    = win_count / total * 100
        avg_gain    = float(np.mean(succ_gains)) if succ_gains else 0.0
        loss_gains  = [abs(s["gain"]) for s in all_signal_details
                       if s["indicator"] == key and s["gain"] < 0]
        avg_loss    = -float(np.mean(loss_gains)) if loss_gains else 0.0
        pf          = round(sum(succ_gains) / sum(loss_gains), 2) \
                      if loss_gains and sum(loss_gains) > 0 else 0.0
        exp         = (win_rate / 100) * avg_gain + (1 - win_rate / 100) * avg_loss

        ind_sigs    = sorted(
            [s for s in all_signal_details if s["indicator"] == key],
            key=lambda x: pd.to_datetime(x["date"]),
        )
        regime_perf = data.get("regime_performance", {})
        best_regime = max(regime_perf, key=regime_perf.get) if regime_perf else ""

        indicator_performance.append({
            "key": key, "name": name, "category": category,
            "total": total, "win_count": win_count,
            "win_rate": win_rate, "avg_gain": round(avg_gain, 2),
            "avg_loss": round(avg_loss, 2), "profit_factor": pf,
            "expectancy": round(exp, 2),
            "best_regime": best_regime, "regime_performance": regime_perf,
            "chart_fn": chart_fn, "signals": ind_sigs,
            "max_gain": data.get("max_gain", 0),
            "max_loss": data.get("max_loss", 0),
            "wilson": _wilson(total, win_rate),
        })

    # Remove indicators with 100% win rate â€” statistically unreliable (too few signals or data artifact)
    indicator_performance = [x for x in indicator_performance if x["win_rate"] < 100]
    indicator_performance.sort(key=lambda x: (x["expectancy"], x["total"]), reverse=True)
    card_accents = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # TAB 1 â€” INDICATOR LEADERBOARD
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    with tab_ind:
        if not indicator_performance:
            st.info("No indicator data available for the selected period.")
        else:
            # full leaderboard table
            _lb_df = pd.DataFrame([{
                "Rank":           i + 1,
                "Indicator":      p["name"],
                "Category":       p["category"],
                "Signals":        p["total"],
                "Win %":          round(p["win_rate"], 1),
                "Avg Gain %":     round(p["avg_gain"], 2),
                "Avg Loss %":     round(p["avg_loss"], 2),
                "Profit Factor":  p["profit_factor"],
                "Expectancy %":   p["expectancy"],
                "Best Regime":    p["best_regime"] or "â€”",
            } for i, p in enumerate(indicator_performance)])
            with st.expander("Full Leaderboard Table", expanded=False):
                st.dataframe(_lb_df.set_index("Rank"), use_container_width=True)

            # top-4 detail cards
            for idx, ind in enumerate(indicator_performance[:4]):
                accent   = card_accents[idx % len(card_accents)]
                br_color = regime_color_map.get(ind["best_regime"], accent)
                win_pct  = ind["win_rate"]
                loss_pct = 100 - win_pct
                total    = ind["total"]
                wins     = ind["win_count"]
                losses   = total - wins
                gain_col = BULL if ind["avg_gain"] >= 1 else NEUT if ind["avg_gain"] > 0 else BEAR
                loss_col = BEAR if ind["avg_loss"] < -1 else NEUT

                def _sb(label, value, color, bg=None, sub=None, _border=border,
                        _panel_alt=panel_alt, _muted=muted):
                    _bg = bg or _panel_alt
                    _sh = (
                        f"<div style='font-size:0.68rem;font-weight:700;color:{color};"
                        f"opacity:0.8;margin-top:0.2rem;'>{sub}</div>"
                    ) if sub else ""
                    return (
                        f"<div style='background:{_bg};border:1px solid {_border};"
                        f"border-radius:10px;padding:0.85rem 0.7rem;text-align:center;'>"
                        f"<div style='font-size:0.6rem;color:{_muted};text-transform:uppercase;"
                        f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.35rem;'>{label}</div>"
                        f"<div style='font-size:1.2rem;font-weight:900;color:{color};line-height:1;'>{value}</div>"
                        f"{_sh}</div>"
                    )

                st.markdown((
                    f"<div style='background:{panel};border:1px solid {border};"
                    f"border-left:4px solid {accent};border-radius:14px;"
                    f"padding:1.6rem 1.8rem;margin-bottom:0.8rem;'>"

                    # header row
                    f"<div style='display:flex;align-items:center;gap:1.2rem;margin-bottom:1.2rem;'>"
                    f"<div style='width:3rem;height:3rem;border-radius:50%;"
                    f"background:{accent}18;border:2px solid {accent};"
                    f"display:flex;align-items:center;justify-content:center;flex-shrink:0;'>"
                    f"<span style='font-size:1.1rem;font-weight:900;color:{accent};'>#{idx+1}</span></div>"
                    f"<div style='flex:1;'>"
                    f"<div style='font-size:1.15rem;font-weight:900;color:{text_col};'>{ind['name']}</div>"
                    f"<div style='font-size:0.75rem;color:{accent};font-weight:600;"
                    f"text-transform:uppercase;letter-spacing:0.5px;margin-top:0.15rem;'>{ind['category']}</div>"
                    f"</div>"
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-size:2.6rem;font-weight:900;color:{accent};line-height:1;'>"
                    f"{win_pct:.0f}%</div>"
                    f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-top:0.1rem;'>Win Rate</div>"
                    f"</div></div>"

                    # win/loss bar
                    f"<div style='margin-bottom:1.2rem;'>"
                    f"<div style='display:flex;border-radius:6px;overflow:hidden;"
                    f"height:7px;margin-bottom:0.4rem;'>"
                    f"<div style='width:{win_pct:.1f}%;background:{accent};'></div>"
                    f"<div style='width:{loss_pct:.1f}%;background:{_hex_rgba(BEAR,.35)};'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span style='font-size:0.72rem;color:{accent};font-weight:700;'>"
                    f"&#10003; {total} signals &middot; {win_pct:.0f}% winners</span>"
                    f"<span style='font-size:0.72rem;color:{BEAR};font-weight:700;'>"
                    f"{loss_pct:.0f}% losers</span>"
                    f"</div></div>"

                    # stats grid
                    f"<div style='display:grid;grid-template-columns:repeat(6,1fr);gap:0.5rem;"
                    f"margin-bottom:0.8rem;'>"
                    + _sb("Signals",    str(total),               text_col)
                    + _sb("Wins",       str(wins),                BULL, _hex_rgba(BULL,.08), f"{win_pct:.0f}%")
                    + _sb("Losses",     str(losses),              BEAR, _hex_rgba(BEAR,.08), f"{loss_pct:.0f}%")
                    + _sb("Avg Gain",   f"+{ind['avg_gain']:.2f}%", gain_col, _hex_rgba(BULL,.06))
                    + _sb("Avg Loss",   f"{ind['avg_loss']:.2f}%",  loss_col, _hex_rgba(BEAR,.06))
                    + _sb("Best Regime", ind["best_regime"] or "â€”", br_color, _hex_rgba(br_color,.10))
                    + "</div></div>"
                ), unsafe_allow_html=True)

                # signal history table
                sigs = ind.get("signals", [])
                if sigs:
                    _sdf = pd.DataFrame(sigs)
                    _keep = [c for c in ["date","entry_price","exit_price",
                                         "gain","days_held","regime","exit_reason"]
                             if c in _sdf.columns]
                    _sdf = _sdf[_keep].copy()
                    _sdf["date"] = pd.to_datetime(_sdf["date"]).dt.strftime("%Y-%m-%d")
                    _sdf = _sdf.sort_values("date", ascending=False).reset_index(drop=True)
                    _sdf.index += 1
                    _sdf.rename(columns={
                        "date": "Date", "entry_price": "Entry", "exit_price": "Exit",
                        "gain": "Gain %", "days_held": "Days",
                        "regime": "Regime", "exit_reason": "Result",
                    }, inplace=True)
                    for col in ("Entry", "Exit"):
                        if col in _sdf.columns:
                            _sdf[col] = _sdf[col].round(2)
                    if "Gain %" in _sdf.columns:
                        _sdf["Gain %"] = _sdf["Gain %"].round(2)
                    with st.expander(
                        f"Signal history â€” {ind['name']} ({len(sigs)} trades)",
                        expanded=False,
                    ):
                        st.dataframe(_sdf, use_container_width=True)

                # indicator chart
                if ind["chart_fn"] is not None:
                    try:
                        _fig = ind["chart_fn"](df)
                        if _fig is not None:
                            _fig.update_layout(
                                height=220,
                                margin=dict(l=0, r=0, t=24, b=0),
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#ffffff", size=11),
                            )
                            with st.expander(f"{ind['name']} chart", expanded=False):
                                st.plotly_chart(
                                    _fig, use_container_width=True,
                                    config={"displayModeBar": False},
                                )
                    except Exception:
                        pass

                st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    # TAB 2 â€” DEEP COMBINATION EXPLORER
    # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
    with tab_combo:
        _all_names = {p["key"]: p["name"] for p in indicator_performance}
        _all_accs  = {p["key"]: card_accents[i % len(card_accents)]
                      for i, p in enumerate(indicator_performance)}
        combo_accent_cycle = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

        # â”€â”€ Filter / sort controls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        fc1, fc2, fc3, fc4 = st.columns([1.5, 1.5, 2, 2])
        with fc1:
            st.markdown(
                f"<div style='font-size:0.62rem;color:{muted};text-transform:uppercase;"
                f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Combo Size Filter</div>",
                unsafe_allow_html=True)
            _size_opts = ["All sizes", "2-Way only", "3-Way only", "4-Way only", "5-Way only", "6-Way only"]
            _cc_size = st.selectbox("Size filter", _size_opts, index=0, key="cc_size_filt",
                                    label_visibility="collapsed")
        with fc2:
            st.markdown(
                f"<div style='font-size:0.62rem;color:{muted};text-transform:uppercase;"
                f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Min Signals</div>",
                unsafe_allow_html=True)
            _cc_minsig = st.number_input("Min signals", min_value=1, value=3, step=1,
                                          key="cc_minsig", label_visibility="collapsed")
        with fc3:
            st.markdown(
                f"<div style='font-size:0.62rem;color:{muted};text-transform:uppercase;"
                f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Sort By</div>",
                unsafe_allow_html=True)
            _sort_opts = {"Wilson Score": "wilson", "Win Rate": "win_rate",
                          "Expectancy": "expectancy", "Profit Factor": "profit_factor",
                          "Total Signals": "total"}
            _cc_sort_label = st.selectbox("Sort by", list(_sort_opts.keys()), index=0,
                                           key="cc_sortby", label_visibility="collapsed")
            _sort_key = _sort_opts[_cc_sort_label]
        with fc4:
            st.markdown(
                f"<div style='font-size:0.62rem;color:{muted};text-transform:uppercase;"
                f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Detail Cards per Group</div>",
                unsafe_allow_html=True)
            _cc_top_per_group = st.number_input("Cards per group", min_value=1, max_value=50,
                                                  value=5, step=1, key="cc_topgroup",
                                                  label_visibility="collapsed")

        # â”€â”€ Resolve size filter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _size_filter = None
        if _cc_size != "All sizes":
            _size_filter = int(_cc_size.split("-")[0])

        # â”€â”€ Build all_combo_data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        all_combo_data = []
        if combo_results:
            for combo_key, cd in combo_results.items():
                parts = [p.strip() for p in combo_key.split(" + ")]
                size = len(parts)
                if _size_filter is not None and size != _size_filter:
                    continue
                n_c = cd["total"]
                wr  = cd["success_rate"]
                if n_c < _cc_minsig or wr >= 100:
                    continue
                rp = {r: v for r, v in cd.get("regime_performance", {}).items() if v > 0}
                best_r = max(rp, key=rp.get) if rp else ""
                all_combo_data.append({
                    "key":          combo_key,
                    "indicators":   parts,
                    "size":         size,
                    "label":        " + ".join(_all_names.get(p, p) for p in parts),
                    "total":        n_c,
                    "wins":         cd["successful"],
                    "losses":       cd["failed"],
                    "win_rate":     wr,
                    "avg_gain":     cd["avg_gain"],
                    "avg_loss":     cd["avg_loss"],
                    "profit_factor": cd["profit_factor"],
                    "expectancy":   cd["expectancy"],
                    "avg_hold":          cd.get("avg_hold", 0),
                    "regime_perf":       rp,
                    "best_regime":       best_r,
                    "wilson":            _wilson(n_c, wr),
                    "max_consec_wins":   cd.get("max_consecutive_wins", 0),
                    "max_consec_losses": cd.get("max_consecutive_losses", 0),
                    "signal_freq":       cd.get("signal_frequency", 0),
                    "consistency":       cd.get("monthly_consistency", 0),
                    "monthly_win_rates": cd.get("monthly_win_rates", {}),
                })
            all_combo_data.sort(key=lambda x: x[_sort_key], reverse=True)

        if not all_combo_data:
            st.info("No combinations found. Try increasing Combo Depth, a longer date range, or lower Min Signals.")
        else:
            total_combos = len(all_combo_data)

            # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            def _badges(parts):
                html = ""
                for idx, p in enumerate(parts):
                    color = _all_accs.get(p, GOLD)
                    name  = _all_names.get(p, p)
                    html += (f"<span style='background:{color}22;color:{color};font-size:0.76rem;"
                             f"font-weight:800;padding:0.22rem 0.55rem;border-radius:20px;"
                             f"border:1px solid {color}55;white-space:nowrap;'>{name}</span>")
                    if idx < len(parts) - 1:
                        html += f"<span style='color:{muted};font-weight:700;font-size:0.88rem;padding:0 0.1rem;'>+</span>"
                return html

            def _wr_color(wr):
                if wr >= 65: return ("#1b5e20", "#81c784")
                if wr >= 55: return ("#2e7d32", "#a5d6a7")
                if wr >= 45: return ("#0d47a1", "#90caf9")
                if wr >= 35: return ("#b71c1c", "#ef9a9a")
                return ("#212121", "#757575")

            # Broad category grouping
            _broad_cat = {
                "Trend Following": "Trend", "Trend Reversal": "Trend",
                "Trend & S/R": "Trend", "Trend Strength": "Trend",
                "Momentum": "Momentum", "Oscillator": "Momentum", "Reversal": "Momentum",
                "Volatility": "Volatility", "Volatility Breakout": "Volatility", "Breakout": "Volatility",
                "Volume Momentum": "Volume", "Volume Flow": "Volume",
                "Volume Anchor": "Volume", "Volume Trend": "Volume",
            }
            _cat_col = {"Trend": INFO, "Momentum": BULL, "Volatility": NEUT, "Volume": PURP, "Other": GOLD}
            def _ind_cat(key):
                raw = indicator_map.get(key, ("", "", None))[1]
                return _broad_cat.get(raw, "Other")

            # â”€â”€ Deep combo card renderer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            def _make_combo_card(row, rank_label, accent):
                wr   = row["win_rate"]
                lp   = 100 - wr
                n_c  = row["total"]
                br_c = regime_color_map.get(row["best_regime"], accent)
                _br_label = (row["best_regime"] + f" ({row['regime_perf'].get(row['best_regime'], 0):.0f}%)"
                             if row["best_regime"] else "â€”")
                rp   = row["regime_perf"]
                mc_w = row.get("max_consec_wins", 0)
                mc_l = row.get("max_consec_losses", 0)
                sf   = row.get("signal_freq", 0)
                con  = row.get("consistency", 0)
                mwr  = row.get("monthly_win_rates", {})
                con_color = "#81c784" if con < 15 else "#ffb74d" if con < 28 else "#ef9a9a"
                con_label = "High" if con < 15 else "Medium" if con < 28 else "Low"

                bars = ""
                for reg, pct in rp.items():
                    rc = regime_color_map.get(reg, "#888")
                    bw = min(100, max(0, pct))
                    bars += (
                        f"<div style='margin-bottom:0.45rem;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.18rem;'>"
                        f"<span style='font-size:0.68rem;color:{muted};font-weight:700;text-transform:uppercase;'>{reg}</span>"
                        f"<span style='font-size:0.75rem;font-weight:800;color:{rc};'>{pct:.0f}%</span></div>"
                        f"<div style='background:{border};border-radius:4px;height:5px;'>"
                        f"<div style='background:{rc};border-radius:4px;height:5px;width:{bw:.0f}%;'></div>"
                        f"</div></div>"
                    )

                mwr_bars = ""
                if mwr:
                    _sorted_mwr = sorted(mwr.items())[-18:]
                    mwr_bars = (
                        f"<div style='background:{BG2};border:1px solid {border};border-radius:7px;"
                        f"padding:0.6rem 0.7rem;margin-top:0.35rem;'>"
                        f"<div style='font-size:0.58rem;color:{muted};font-weight:700;text-transform:uppercase;"
                        f"letter-spacing:0.7px;margin-bottom:0.45rem;'>Monthly Win Rate (last 18 months)</div>"
                        f"<div style='display:flex;align-items:flex-end;gap:2px;height:26px;'>"
                    )
                    for _mo, _mwr in _sorted_mwr:
                        _bg2, _fg2 = _wr_color(_mwr)
                        _h2 = max(3, int(_mwr / 100 * 22))
                        mwr_bars += (
                            f"<div title='{_mo}: {_mwr:.0f}%' style='flex:1;min-width:2px;"
                            f"height:{_h2}px;background:{_fg2};border-radius:2px 2px 0 0;'></div>"
                        )
                    mwr_bars += "</div></div>"

                def _st(lbl, val, col):
                    return (
                        f"<div style='background:{BG2};border:1px solid {border};"
                        f"border-radius:7px;padding:0.65rem 0.3rem;text-align:center;'>"
                        f"<div style='font-size:0.57rem;color:{muted};text-transform:uppercase;"
                        f"letter-spacing:0.45px;margin-bottom:0.2rem;'>{lbl}</div>"
                        f"<div style='font-size:0.98rem;font-weight:800;color:{col};line-height:1;'>{val}</div>"
                        f"</div>"
                    )

                st.markdown((
                    f"<div style='background:{panel};border:1px solid {border};"
                    f"border-top:3px solid {accent};border-radius:14px;"
                    f"padding:1.2rem 1.35rem;margin-bottom:0.75rem;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.8rem;'>"
                    f"<div style='flex:1;min-width:0;'>"
                    f"<div style='font-size:0.57rem;color:{muted};font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:0.8px;margin-bottom:0.38rem;'>{rank_label} آ· {row['size']}-Way Combination</div>"
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.28rem;margin-bottom:0.32rem;'>"
                    f"{_badges(row['indicators'])}</div>"
                    f"<div style='font-size:0.68rem;color:{muted};'>Best regime: "
                    f"<span style='color:{br_c};font-weight:700;'>{_br_label}</span></div></div>"
                    f"<div style='text-align:right;flex-shrink:0;margin-left:0.8rem;'>"
                    f"<div style='font-size:2.5rem;font-weight:900;color:{accent};line-height:1;'>"
                    f"{wr:.1f}<span style='font-size:1.05rem;'>%</span></div>"
                    f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;letter-spacing:0.5px;'>"
                    f"Win Rate آ· {n_c} signals</div></div></div>"
                    f"<div style='display:flex;border-radius:5px;overflow:hidden;height:6px;margin-bottom:0.28rem;'>"
                    f"<div style='width:{wr:.1f}%;background:{BULL};'></div>"
                    f"<div style='width:{lp:.1f}%;background:{BEAR};'></div></div>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:0.85rem;'>"
                    f"<span style='font-size:0.68rem;color:{BULL};font-weight:700;'>âœ“ {row['wins']} wins ({wr:.1f}%)</span>"
                    f"<span style='font-size:0.68rem;color:{BEAR};font-weight:700;'>{row['losses']} losses ({lp:.1f}%) âœ—</span></div>"
                    f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.32rem;margin-bottom:0.75rem;'>"
                    + _st("Signals",       str(n_c),                               text_col)
                    + _st("Winners",       str(row["wins"]),                        BULL)
                    + _st("Losers",        str(row["losses"]),                      BEAR)
                    + _st("Avg Gain",      f"+{row['avg_gain']:.2f}%",             BULL)
                    + _st("Avg Loss",      f"{row['avg_loss']:.2f}%",              BEAR)
                    + _st("Avg Hold",      f"{row['avg_hold']:.0f}d",              INFO)
                    + _st("Profit Factor", f"{row['profit_factor']:.2f}",          BULL if row['profit_factor'] >= 1.5 else NEUT)
                    + _st("Expectancy",    f"{row['expectancy']:+.2f}%",           BULL if row['expectancy'] > 0 else BEAR)
                    + _st("Wilson Score",  f"{row['wilson']:.1f}",                 INFO)
                    + _st("Max W-Streak",  str(mc_w),                              BULL)
                    + _st("Max L-Streak",  str(mc_l),                              BEAR)
                    + _st("Sig/100 Bars",  f"{sf:.1f}",                            PURP)
                    + "</div>"
                    f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.65rem;'>"
                    f"<div style='background:{BG2};border:1px solid {border};border-radius:9px;padding:0.75rem 0.85rem;'>"
                    f"<div style='font-size:0.6rem;color:{accent};font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:0.8px;margin-bottom:0.5rem;'>Regime Win Rate</div>"
                    + bars
                    + "</div>"
                    f"<div style='background:{BG2};border:1px solid {border};border-radius:9px;padding:0.75rem 0.85rem;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem;'>"
                    f"<span style='font-size:0.6rem;color:{accent};font-weight:700;text-transform:uppercase;letter-spacing:0.8px;'>Consistency</span>"
                    f"<span style='font-size:0.7rem;font-weight:800;color:{con_color};'>{con_label}</span></div>"
                    f"<div style='font-size:0.65rem;color:{muted};margin-bottom:0.28rem;'>"
                    f"Std dev: <strong style='color:{text_col};'>{con:.1f}%</strong> â€” lower = more reliable</div>"
                    + mwr_bars
                    + "</div></div></div>"
                ), unsafe_allow_html=True)

                _sigs = combo_results.get(row["key"], {}).get("signals", [])
                if _sigs:
                    _cdf = pd.DataFrame(_sigs)
                    _ccols = [c for c in ["date","entry_price","exit_price","gain","days_held","regime","result"] if c in _cdf.columns]
                    _cdf = _cdf[_ccols].sort_values("date", ascending=False).reset_index(drop=True)
                    _cdf.index += 1
                    if "result" in _cdf.columns:
                        _cdf["result"] = _cdf["result"].map({
                            "profit":"Profit","stop_loss":"Stop Loss",
                            "timeout_profit":"Timeout â†‘","timeout_loss":"Timeout â†“","timeout":"Timeout",
                        }).fillna(_cdf["result"])
                    _cdf.columns = [c.replace("_"," ").title() for c in _cdf.columns]
                    with st.expander(f"Trade history â€” {row['label']} ({len(_sigs)} trades)", expanded=False):
                        st.dataframe(_cdf, use_container_width=True)
                st.markdown("<div style='margin-bottom:0.35rem;'></div>", unsafe_allow_html=True)

            # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
            # 5 DEEP ANALYSIS SUB-TABS
            # â•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گâ•گ
            ctab1, ctab2, ctab3, ctab4, ctab5 = st.tabs([
                "Leaderboard",
                "Regime Champions",
                "Pair Heatmap",
                "Category Mix",
                "Deep Cards",
            ])

            # â”€â”€ Sub-tab 1: Leaderboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with ctab1:
                champ    = all_combo_data[0]
                champ_wr = champ["win_rate"]
                champ_ea = champ["expectancy"]
                champ_con = champ.get("consistency", 0)
                st.markdown(
                    f"<div style='background:linear-gradient(135deg,rgba(255,215,0,0.10),rgba(76,175,80,0.07));"
                    f"border:2px solid rgba(255,215,0,0.45);border-radius:15px;"
                    f"padding:1.2rem 1.5rem;margin-bottom:1.1rem;'>"
                    f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;'>"
                    f"<span style='font-size:0.88rem;'>ًںڈ†</span>"
                    f"<span style='font-size:0.58rem;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:{GOLD};'>BEST COMBINATION OVERALL</span>"
                    f"<span style='margin-left:auto;font-size:0.58rem;color:{muted};font-weight:600;'>{total_combos:,} combinations analysed</span>"
                    f"</div>"
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.28rem;margin-bottom:0.75rem;'>{_badges(champ['indicators'])}</div>"
                    f"<div style='display:grid;grid-template-columns:repeat(6,1fr);gap:0.4rem;'>"
                    f"<div style='text-align:center;'><div style='font-size:1.6rem;font-weight:900;color:{GOLD};line-height:1;'>{champ_wr:.1f}%</div><div style='font-size:0.52rem;color:{muted};text-transform:uppercase;'>Win Rate</div></div>"
                    f"<div style='text-align:center;'><div style='font-size:1.6rem;font-weight:900;color:{BULL};line-height:1;'>{champ['wins']}</div><div style='font-size:0.52rem;color:{muted};text-transform:uppercase;'>Winners</div></div>"
                    f"<div style='text-align:center;'><div style='font-size:1.6rem;font-weight:900;color:{text_col};line-height:1;'>{champ['total']}</div><div style='font-size:0.52rem;color:{muted};text-transform:uppercase;'>Signals</div></div>"
                    f"<div style='text-align:center;'><div style='font-size:1.6rem;font-weight:900;color:{'#81c784' if champ_ea>0 else BEAR};line-height:1;'>{champ_ea:+.2f}%</div><div style='font-size:0.52rem;color:{muted};text-transform:uppercase;'>Expectancy</div></div>"
                    f"<div style='text-align:center;'><div style='font-size:1.6rem;font-weight:900;color:{INFO};line-height:1;'>{champ['size']}-Way</div><div style='font-size:0.52rem;color:{muted};text-transform:uppercase;'>Combo Size</div></div>"
                    f"<div style='text-align:center;'><div style='font-size:1.6rem;font-weight:900;color:{'#81c784' if champ_con<15 else '#ffb74d'};line-height:1;'>{champ_con:.1f}%</div><div style='font-size:0.52rem;color:{muted};text-transform:uppercase;'>Variability دƒ</div></div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                # Top-10 strip (2 rows أ— 5)
                for _row_start in [0, 5]:
                    _strip_items = all_combo_data[_row_start:_row_start + 5]
                    if not _strip_items:
                        break
                    _sh = (f"<div style='display:grid;grid-template-columns:repeat({len(_strip_items)},1fr);"
                           f"gap:0.38rem;margin-bottom:0.38rem;'>")
                    for _sti, _str in enumerate(_strip_items):
                        _stac = combo_accent_cycle[(_row_start + _sti) % len(combo_accent_cycle)]
                        _sh += (
                            f"<div style='background:{BG2};border:1px solid {border};"
                            f"border-top:2px solid {_stac};border-radius:9px;padding:0.6rem 0.35rem;text-align:center;'>"
                            f"<div style='font-size:0.5rem;color:{muted};font-weight:700;margin-bottom:0.12rem;'>#{_row_start+_sti+1} آ· {_str['size']}-Way</div>"
                            f"<div style='font-size:0.58rem;font-weight:800;color:{_stac};line-height:1.3;'>"
                            + " + ".join(_all_names.get(p, p) for p in _str["indicators"])
                            + f"</div><div style='font-size:0.95rem;font-weight:900;color:{text_col};'>{_str['win_rate']:.0f}%</div>"
                            f"<div style='font-size:0.55rem;color:{muted};'>{_str['total']} sig آ· exp {_str['expectancy']:+.1f}%</div>"
                            f"</div>"
                        )
                    _sh += "</div>"
                    st.markdown(_sh, unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)
                # Full sortable table (always visible)
                _tbl_rows = []
                for _ti, _tr in enumerate(all_combo_data):
                    _tbl_rows.append({
                        "Rank":           _ti + 1,
                        "Combination":    _tr["label"],
                        "Size":           f"{_tr['size']}-Way",
                        "Signals":        _tr["total"],
                        "Wins":           _tr["wins"],
                        "Losses":         _tr["losses"],
                        "Win %":          round(_tr["win_rate"], 1),
                        "Avg Gain %":     round(_tr["avg_gain"], 2),
                        "Avg Loss %":     round(_tr["avg_loss"], 2),
                        "Profit Factor":  round(_tr["profit_factor"], 2),
                        "Expectancy %":   round(_tr["expectancy"], 2),
                        "Wilson Score":   round(_tr["wilson"], 1),
                        "Consistency دƒ":  round(_tr.get("consistency", 0), 1),
                        "Max W-Streak":   _tr.get("max_consec_wins", 0),
                        "Max L-Streak":   _tr.get("max_consec_losses", 0),
                        "Sig/100 Bars":   round(_tr.get("signal_freq", 0), 1),
                        "Best Regime":    _tr["best_regime"] or "â€”",
                    })
                _tbl_df = pd.DataFrame(_tbl_rows).set_index("Rank")
                st.markdown(
                    f"<div style='font-size:0.62rem;color:{muted};margin-bottom:0.35rem;font-weight:600;'>"
                    f"Click any column to sort آ· {total_combos:,} valid combinations:</div>",
                    unsafe_allow_html=True,
                )
                st.dataframe(_tbl_df, use_container_width=True, height=520)

            # â”€â”€ Sub-tab 2: Regime Champions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with ctab2:
                st.markdown(
                    f"<div style='font-size:0.72rem;color:{muted};margin-bottom:0.75rem;'>"
                    f"Each section ranks combinations by their win rate <em>specifically inside that market regime</em>, "
                    f"not overall. Use this to deploy the right combination when the market is trending, ranging, or volatile.</div>",
                    unsafe_allow_html=True,
                )
                for _rgn, _rgc in [("TREND", INFO), ("RANGE", NEUT), ("VOLATILE", BEAR)]:
                    _reg_combos = sorted(
                        [x for x in all_combo_data if x["regime_perf"].get(_rgn, 0) > 0],
                        key=lambda x: x["regime_perf"].get(_rgn, 0), reverse=True,
                    )
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.6rem 0;'>"
                        f"<span style='width:4px;height:1.35rem;background:{_rgc};border-radius:2px;flex-shrink:0;display:inline-block;'></span>"
                        f"<span style='font-size:0.86rem;font-weight:800;color:{_rgc};text-transform:uppercase;letter-spacing:0.5px;'>{_rgn} Regime</span>"
                        f"<span style='font-size:0.65rem;color:{muted};'>{len(_reg_combos)} combos with data</span></div>",
                        unsafe_allow_html=True,
                    )
                    if not _reg_combos:
                        st.markdown(f"<div style='color:{muted};font-size:0.76rem;padding:0.35rem 0;'>No regime data yet â€” try a longer date range.</div>", unsafe_allow_html=True)
                    else:
                        _rcs = _reg_combos[:5]
                        _rhtml = f"<div style='display:grid;grid-template-columns:repeat({len(_rcs)},1fr);gap:0.38rem;margin-bottom:0.55rem;'>"
                        for _ri, _rr in enumerate(_rcs):
                            _rwr = _rr["regime_perf"].get(_rgn, 0)
                            _rhtml += (
                                f"<div style='background:{BG2};border:1px solid {border};"
                                f"border-top:2px solid {_rgc};border-radius:9px;padding:0.55rem 0.38rem;text-align:center;'>"
                                f"<div style='font-size:0.5rem;color:{muted};font-weight:700;margin-bottom:0.12rem;'>#{_ri+1}</div>"
                                f"<div style='font-size:0.58rem;font-weight:800;color:{_rgc};line-height:1.3;'>"
                                + " + ".join(_all_names.get(p, p) for p in _rr["indicators"])
                                + f"</div><div style='font-size:0.9rem;font-weight:900;color:{text_col};'>{_rwr:.0f}%</div>"
                                f"<div style='font-size:0.52rem;color:{muted};'>in {_rgn} آ· {_rr['total']} total sig</div></div>"
                            )
                        _rhtml += "</div>"
                        st.markdown(_rhtml, unsafe_allow_html=True)
                        _rtbl = []
                        for _rti, _rtr in enumerate(_reg_combos[:30]):
                            _rtbl.append({
                                "Rank":              _rti + 1,
                                "Combination":       _rtr["label"],
                                "Size":              f"{_rtr['size']}-Way",
                                f"{_rgn} Win %":     round(_rtr["regime_perf"].get(_rgn, 0), 1),
                                "Overall Win %":     round(_rtr["win_rate"], 1),
                                "Signals":           _rtr["total"],
                                "Profit Factor":     round(_rtr["profit_factor"], 2),
                                "Expectancy %":      round(_rtr["expectancy"], 2),
                                "Wilson Score":      round(_rtr["wilson"], 1),
                                "Consistency دƒ":     round(_rtr.get("consistency", 0), 1),
                            })
                        with st.expander(f"Top {len(_rtbl)} combos for {_rgn} (sortable)", expanded=False):
                            st.dataframe(pd.DataFrame(_rtbl).set_index("Rank"), use_container_width=True)
                    st.markdown(f"<hr style='border:none;border-top:1px solid {border};margin:0.6rem 0;'>", unsafe_allow_html=True)

            # â”€â”€ Sub-tab 3: Pair Heatmap â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with ctab3:
                _pairs = [x for x in all_combo_data if x["size"] == 2]
                if not _pairs:
                    st.info("No 2-way pair data. Ensure Combo Depth â‰¥ 2 and Min Signals is low enough.")
                else:
                    st.markdown(
                        f"<div style='font-size:0.72rem;color:{muted};margin-bottom:0.65rem;'>"
                        f"Win rate when <strong style='color:{text_col};'>both</strong> indicators fire on the <strong style='color:{text_col};'>same bar</strong>. "
                        f"<span style='color:#81c784;'>â– </span> â‰¥65% "
                        f"<span style='color:#a5d6a7;'>â– </span> â‰¥55% "
                        f"<span style='color:#90caf9;'>â– </span> â‰¥45% "
                        f"<span style='color:#ef9a9a;'>â– </span> &lt;45% "
                        f"<span style='color:#444;'>â– </span> no data &nbsp;آ· "
                        f"Hover a cell to see exact figures.</div>",
                        unsafe_allow_html=True,
                    )
                    _plu = {}
                    for _p in _pairs:
                        a2, b2 = _p["indicators"][0], _p["indicators"][1]
                        _plu[(a2, b2)] = (_p["win_rate"], _p["total"], _p["expectancy"])
                        _plu[(b2, a2)] = (_p["win_rate"], _p["total"], _p["expectancy"])
                    _hm_inds = sorted(set(v for _p in _pairs for v in _p["indicators"]))
                    _N = len(_hm_inds)
                    _cw2 = max(46, min(88, 780 // (_N + 1)))
                    _hm = (
                        f"<div style='overflow-x:auto;-webkit-overflow-scrolling:touch;'>"
                        f"<table style='border-collapse:collapse;font-size:0.59rem;'><thead><tr>"
                        f"<th style='min-width:{_cw2}px;padding:0.28rem 0.18rem;color:{muted};"
                        f"background:{BG2};border:1px solid {border};'>â†“ / â†’</th>"
                    )
                    for _hb in _hm_inds:
                        _hm += (
                            f"<th style='min-width:{_cw2}px;padding:0.26rem 0.15rem;text-align:center;"
                            f"color:{_all_accs.get(_hb,GOLD)};background:{BG2};"
                            f"border:1px solid {border};font-weight:800;'>"
                            + _all_names.get(_hb, _hb)[:9] + "</th>"
                        )
                    _hm += "</tr></thead><tbody>"
                    for _ha in _hm_inds:
                        _hm += (
                            f"<tr><td style='padding:0.26rem 0.38rem;font-weight:800;"
                            f"color:{_all_accs.get(_ha,GOLD)};background:{BG2};"
                            f"border:1px solid {border};white-space:nowrap;'>"
                            + _all_names.get(_ha, _ha)[:11] + "</td>"
                        )
                        for _hb in _hm_inds:
                            if _ha == _hb:
                                _hm += f"<td style='background:#282828;border:1px solid {border};text-align:center;color:#555;'>â€”</td>"
                            elif (_ha, _hb) in _plu:
                                _wr3, _ns3, _ex3 = _plu[(_ha, _hb)]
                                _bg3, _fg3 = _wr_color(_wr3)
                                _hm += (
                                    f"<td style='background:{_bg3};border:1px solid {border};"
                                    f"text-align:center;color:{_fg3};font-weight:700;cursor:default;'"
                                    f" title='{_ha}+{_hb}: {_wr3:.1f}% WR | {_ns3} sig | exp {_ex3:+.2f}%'>"
                                    f"{_wr3:.0f}%</td>"
                                )
                            else:
                                _hm += f"<td style='background:#181818;border:1px solid {border};text-align:center;color:#2e2e2e;'>آ·</td>"
                        _hm += "</tr>"
                    _hm += "</tbody></table></div>"
                    st.markdown(_hm, unsafe_allow_html=True)
                    st.markdown("<div style='margin-top:0.9rem;'></div>", unsafe_allow_html=True)
                    _pr = []
                    for _pi2, _pp2 in enumerate(sorted(_pairs, key=lambda x: x["win_rate"], reverse=True)):
                        _pr.append({
                            "Rank":          _pi2 + 1,
                            "Pair":          _pp2["label"],
                            "Win %":         round(_pp2["win_rate"], 1),
                            "Signals":       _pp2["total"],
                            "Wins":          _pp2["wins"],
                            "Avg Gain %":    round(_pp2["avg_gain"], 2),
                            "Avg Loss %":    round(_pp2["avg_loss"], 2),
                            "Profit Factor": round(_pp2["profit_factor"], 2),
                            "Expectancy %":  round(_pp2["expectancy"], 2),
                            "Wilson Score":  round(_pp2["wilson"], 1),
                            "Consistency دƒ": round(_pp2.get("consistency", 0), 1),
                            "Max W-Streak":  _pp2.get("max_consec_wins", 0),
                            "Max L-Streak":  _pp2.get("max_consec_losses", 0),
                        })
                    with st.expander(f"All {len(_pr)} valid pairs ranked by Win Rate", expanded=False):
                        st.dataframe(pd.DataFrame(_pr).set_index("Rank"), use_container_width=True, height=400)

            # â”€â”€ Sub-tab 4: Category Mix â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with ctab4:
                st.markdown(
                    f"<div style='font-size:0.72rem;color:{muted};margin-bottom:0.75rem;'>"
                    f"All indicators are bucketed into 4 broad families: "
                    f"<strong style='color:{INFO};'>Trend</strong> (EMA/SMA/PSAR/Ichimoku/WMA/ADX), "
                    f"<strong style='color:{BULL};'>Momentum</strong> (RSI/MACD/Stoch/ROC/CCI/WillR), "
                    f"<strong style='color:{NEUT};'>Volatility</strong> (BB/Keltner/Donchian), "
                    f"<strong style='color:{PURP};'>Volume</strong> (MFI/CMF/VWAP/OBV). "
                    f"This reveals which type-of-indicator mixes create the strongest edge.</div>",
                    unsafe_allow_html=True,
                )
                for _row in all_combo_data:
                    _cats = sorted(set(_ind_cat(p) for p in _row["indicators"]))
                    _row["_cat_mix"] = " + ".join(_cats)
                _mix_grps = {}
                for _row in all_combo_data:
                    _mx = _row["_cat_mix"]
                    if _mx not in _mix_grps:
                        _mix_grps[_mx] = []
                    _mix_grps[_mx].append(_row)
                _mix_summ = sorted([{
                    "mix":    _mx,
                    "count":  len(_grp),
                    "avg_wr": float(np.mean([x["win_rate"] for x in _grp])),
                    "avg_pf": float(np.mean([x["profit_factor"] for x in _grp])),
                    "avg_exp": float(np.mean([x["expectancy"] for x in _grp])),
                    "best":   max(_grp, key=lambda x: x["wilson"]),
                    "combos": _grp,
                } for _mx, _grp in _mix_grps.items()], key=lambda x: x["avg_wr"], reverse=True)
                _max_awr = max(x["avg_wr"] for x in _mix_summ) if _mix_summ else 100
                # Ranked bar chart
                _cmh = "<div style='margin-bottom:0.9rem;'>"
                for _ms in _mix_summ:
                    _mx_cats = _ms["mix"].split(" + ")
                    _dots = "".join(
                        f"<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
                        f"background:{_cat_col.get(c,GOLD)};margin-right:2px;vertical-align:middle;'></span>"
                        for c in _mx_cats
                    )
                    _bw2 = int(_ms["avg_wr"] / max(_max_awr, 1) * 100)
                    _bc2 = BULL if _ms["avg_wr"] >= 55 else NEUT if _ms["avg_wr"] >= 45 else BEAR
                    _cmh += (
                        f"<div style='margin-bottom:0.8rem;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.25rem;'>"
                        f"<div style='display:flex;align-items:center;gap:0.32rem;'>{_dots}"
                        f"<span style='font-size:0.72rem;font-weight:700;color:{text_col};'>{_ms['mix']}</span>"
                        f"<span style='font-size:0.58rem;color:{muted};'>({_ms['count']} combos)</span></div>"
                        f"<div style='display:flex;gap:0.75rem;'>"
                        f"<span style='font-size:0.68rem;font-weight:800;color:{_bc2};'>Avg WR: {_ms['avg_wr']:.1f}%</span>"
                        f"<span style='font-size:0.68rem;color:{muted};'>PF: {_ms['avg_pf']:.2f}</span>"
                        f"<span style='font-size:0.68rem;color:{BULL if _ms['avg_exp']>0 else BEAR};'>Exp: {_ms['avg_exp']:+.2f}%</span>"
                        f"</div></div>"
                        f"<div style='background:{border};border-radius:4px;height:7px;'>"
                        f"<div style='background:{_bc2};border-radius:4px;height:7px;width:{_bw2}%;'></div></div>"
                        f"<div style='font-size:0.61rem;color:{muted};margin-top:0.15rem;'>"
                        f"Best: <strong style='color:{text_col};'>{_ms['best']['label']}</strong>"
                        f" â€” {_ms['best']['win_rate']:.1f}% WR آ· {_ms['best']['total']} sig</div></div>"
                    )
                _cmh += "</div>"
                st.markdown(_cmh, unsafe_allow_html=True)
                for _msi, _ms in enumerate(_mix_summ):
                    _cac3 = combo_accent_cycle[_msi % len(combo_accent_cycle)]
                    with st.expander(
                        f"{_ms['mix']}  â€”  {_ms['count']} combos  |  Avg WR {_ms['avg_wr']:.1f}%  |  Best {_ms['best']['win_rate']:.1f}%",
                        expanded=(_msi < 2),
                    ):
                        _make_combo_card(_ms["best"], "#1 in mix", _cac3)
                        _mix_tbl = [{
                            "Rank":          _mi4 + 1,
                            "Combination":   _mr4["label"],
                            "Size":          f"{_mr4['size']}-Way",
                            "Win %":         round(_mr4["win_rate"], 1),
                            "Signals":       _mr4["total"],
                            "Profit Factor": round(_mr4["profit_factor"], 2),
                            "Expectancy %":  round(_mr4["expectancy"], 2),
                            "Wilson Score":  round(_mr4["wilson"], 1),
                            "Consistency دƒ": round(_mr4.get("consistency", 0), 1),
                            "Max W-Streak":  _mr4.get("max_consec_wins", 0),
                        } for _mi4, _mr4 in enumerate(
                            sorted(_ms["combos"], key=lambda x: x["win_rate"], reverse=True)
                        )]
                        st.dataframe(pd.DataFrame(_mix_tbl).set_index("Rank"), use_container_width=True)

            # â”€â”€ Sub-tab 5: Deep Cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            with ctab5:
                _sz_names = {
                    2: "2-Way Pairs", 3: "3-Way Triples", 4: "4-Way Quadruples",
                    5: "5-Way Quintuples", 6: "6-Way Combinations",
                }
                for _sv in sorted(set(x["size"] for x in all_combo_data)):
                    _sc  = [x for x in all_combo_data if x["size"] == _sv]
                    _sn  = _sz_names.get(_sv, f"{_sv}-Way")
                    _bwr = _sc[0]["win_rate"] if _sc else 0
                    _bex = _sc[0]["expectancy"] if _sc else 0
                    with st.expander(
                        f"{_sn}  â€”  {len(_sc)} combos  |  Best WR {_bwr:.0f}%  |  Best Exp {_bex:+.2f}%",
                        expanded=(_sv == 2),
                    ):
                        _ns3 = min(5, len(_sc))
                        _ss3 = (f"<div style='display:grid;grid-template-columns:repeat({_ns3},1fr);"
                                f"gap:0.32rem;margin-bottom:0.75rem;'>")
                        for _xi, _xr in enumerate(_sc[:_ns3]):
                            _xac = combo_accent_cycle[_xi % len(combo_accent_cycle)]
                            _ss3 += (
                                f"<div style='background:{BG2};border:1px solid {border};"
                                f"border-top:2px solid {_xac};border-radius:8px;padding:0.5rem 0.32rem;text-align:center;'>"
                                f"<div style='font-size:0.5rem;color:{muted};font-weight:700;margin-bottom:0.12rem;'>#{_xi+1}</div>"
                                f"<div style='font-size:0.58rem;font-weight:800;color:{_xac};line-height:1.3;'>"
                                + " + ".join(_all_names.get(p, p) for p in _xr["indicators"])
                                + f"</div><div style='font-size:0.92rem;font-weight:900;color:{text_col};'>{_xr['win_rate']:.0f}%</div>"
                                f"<div style='font-size:0.53rem;color:{muted};'>{_xr['total']} sig</div></div>"
                            )
                        _ss3 += "</div>"
                        st.markdown(_ss3, unsafe_allow_html=True)
                        _top_n = _sc[:int(_cc_top_per_group)]
                        _rest2 = _sc[int(_cc_top_per_group):]
                        for _ci, _cr in enumerate(_top_n):
                            _cac4 = combo_accent_cycle[_ci % len(combo_accent_cycle)]
                            _make_combo_card(_cr, f"#{_ci + 1}", _cac4)
                        if _rest2:
                            _rest_rows2 = [{
                                "Rank":           int(_cc_top_per_group) + _ri + 1,
                                "Combination":    _rr["label"],
                                "Signals":        _rr["total"],
                                "Win %":          round(_rr["win_rate"], 1),
                                "Avg Gain %":     round(_rr["avg_gain"], 2),
                                "Profit Factor":  round(_rr["profit_factor"], 2),
                                "Expectancy %":   round(_rr["expectancy"], 2),
                                "Wilson Score":   round(_rr["wilson"], 1),
                                "Consistency دƒ":  round(_rr.get("consistency", 0), 1),
                                "Max W-Streak":   _rr.get("max_consec_wins", 0),
                                "Max L-Streak":   _rr.get("max_consec_losses", 0),
                                "Sig/100 Bars":   round(_rr.get("signal_freq", 0), 1),
                                "Best Regime":    _rr["best_regime"] or "â€”",
                            } for _ri, _rr in enumerate(_rest2)]
                            with st.expander(f"Remaining {len(_rest2)} {_sn} combinations", expanded=False):
                                st.dataframe(pd.DataFrame(_rest_rows2).set_index("Rank"), use_container_width=True)

