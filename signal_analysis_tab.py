import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
from favorites_tab import render_save_button, render_save_indicator_button, render_save_combo_button
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

                render_save_indicator_button(idx, ind, risk_val, reward_val, _period_label)
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
        fc1, = st.columns([1])
        with fc1:
            st.markdown(
                f"<div style='font-size:0.62rem;color:{muted};text-transform:uppercase;"
                f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.3rem;'>Combo Size Filter</div>",
                unsafe_allow_html=True)
            _size_opts = ["All sizes", "2-Way only", "3-Way only", "4-Way only", "5-Way only", "6-Way only"]
            _cc_size = st.selectbox("Size filter", _size_opts, index=0, key="cc_size_filt",
                                    label_visibility="collapsed")
        _sort_key = "win_rate"
        _cc_top_per_group = 5

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
                if wr >= 100:
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
            st.info("No combinations found. Try increasing Combo Depth or using a longer date range.")
        else:
            total_combos = len(all_combo_data)

            # ── Helpers ────────────────────────────────────────────────────────
            def _badges(parts):
                html = ""
                for idx, p in enumerate(parts):
                    name  = _all_names.get(p, p)
                    html += (
                        f"<span style='background:#252525;color:#e0e0e0;font-size:0.95rem;"
                        f"font-weight:600;padding:0.25rem 0.75rem;border-radius:6px;"
                        f"border:1px solid #383838;white-space:nowrap;'>{name}</span>"
                    )
                    if idx < len(parts) - 1:
                        html += "<span style='color:#555;padding:0 0.2rem;font-size:0.9rem;'>&middot;</span>"
                return html

            def _wr_color(wr):
                if wr >= 65: return ("#1b5e20", "#81c784")
                if wr >= 55: return ("#2e7d32", "#a5d6a7")
                if wr >= 45: return ("#0d47a1", "#90caf9")
                if wr >= 35: return ("#b71c1c", "#ef9a9a")
                return ("#282828", "#757575")

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

            # ── Stat mini-cell used inside combo cards ─────────────────────────
            def _st(lbl, val, col):
                return (
                    f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;"
                    f"border-radius:8px;padding:0.8rem 0.4rem;text-align:center;'>"
                    f"<div style='font-size:0.75rem;color:#757575;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.35rem;font-weight:500;'>{lbl}</div>"
                    f"<div style='font-size:1.15rem;font-weight:700;color:{col};line-height:1;'>{val}</div>"
                    f"</div>"
                )

            # ── Full combo card ────────────────────────────────────────────────
            def _make_combo_card(row, rank_label, accent):
                wr   = row["win_rate"]
                lp   = 100 - wr
                _, _wr_col = _wr_color(wr)
                n_c  = row["total"]
                br_c = regime_color_map.get(row["best_regime"], "#9e9e9e")
                _br_label = (
                    row["best_regime"] + f" ({row['regime_perf'].get(row['best_regime'], 0):.0f}%)"
                    if row["best_regime"] else "None"
                )
                rp   = row["regime_perf"]
                mc_w = row.get("max_consec_wins", 0)
                mc_l = row.get("max_consec_losses", 0)
                sf   = row.get("signal_freq", 0)
                con  = row.get("consistency", 0)
                mwr  = row.get("monthly_win_rates", {})
                con_color = "#81c784" if con < 15 else "#ffb74d" if con < 28 else "#ef9a9a"
                con_label = "High" if con < 15 else "Medium" if con < 28 else "Low"

                # Regime bars HTML
                bars = ""
                for reg, pct in rp.items():
                    rc = regime_color_map.get(reg, "#888")
                    bw = min(100, max(0, pct))
                    bars += (
                        f"<div style='margin-bottom:0.4rem;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.15rem;'>"
                        f"<span style='font-size:0.65rem;color:{muted};font-weight:700;text-transform:uppercase;'>{reg}</span>"
                        f"<span style='font-size:0.72rem;font-weight:800;color:{rc};'>{pct:.0f}%</span></div>"
                        f"<div style='background:{border};border-radius:3px;height:4px;'>"
                        f"<div style='background:{rc};border-radius:3px;height:4px;width:{bw:.0f}%;'></div>"
                        f"</div></div>"
                    )

                # Monthly win rate mini-bars
                mwr_bars = ""
                if mwr:
                    _sorted_mwr = sorted(mwr.items())[-18:]
                    mwr_bars = (
                        f"<div style='background:#141414;border:1px solid #252525;border-radius:6px;"
                        f"padding:0.5rem 0.6rem;margin-top:0.3rem;'>"
                        f"<div style='font-size:0.65rem;color:#757575;font-weight:500;text-transform:uppercase;"
                        f"letter-spacing:0.6px;margin-bottom:0.4rem;'>Monthly Win Rate (last 18 mo.)</div>"
                        f"<div style='display:flex;align-items:flex-end;gap:2px;height:24px;'>"
                    )
                    for _mo, _mwr_v in _sorted_mwr:
                        _bg2, _fg2 = _wr_color(_mwr_v)
                        _h2 = max(3, int(_mwr_v / 100 * 20))
                        mwr_bars += (
                            f"<div title='{_mo}: {_mwr_v:.0f}%' style='flex:1;min-width:2px;"
                            f"height:{_h2}px;background:{_fg2};border-radius:2px 2px 0 0;'></div>"
                        )
                    mwr_bars += "</div></div>"

                st.markdown((
                    f"<div style='background:#1e1e1e;border:1px solid #2d2d2d;"
                    f"border-left:3px solid {_wr_col};border-radius:12px;"
                    f"padding:1.1rem 1.25rem;margin-bottom:0.65rem;'>"

                    # Header row
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.7rem;'>"
                    f"<div style='flex:1;min-width:0;'>"
                    f"<div style='font-size:0.75rem;color:#757575;font-weight:500;text-transform:uppercase;"
                    f"letter-spacing:0.8px;margin-bottom:0.35rem;'>{rank_label} &middot; {row['size']}-Way Combination</div>"
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.25rem;margin-bottom:0.28rem;'>"
                    f"{_badges(row['indicators'])}</div>"
                    f"<div style='font-size:0.75rem;color:{muted};'>Best in: "
                    f"<span style='color:{br_c};font-weight:700;'>{_br_label}</span></div>"
                    f"</div>"
                    f"<div style='text-align:right;flex-shrink:0;margin-left:0.8rem;'>"
                    f"<div style='font-size:2.4rem;font-weight:800;color:{_wr_col};line-height:1;'>"
                    f"{wr:.1f}<span style='font-size:1rem;'>%</span></div>"
                    f"<div style='font-size:0.75rem;color:#757575;letter-spacing:0.3px;'>"
                    f"win rate &middot; {n_c} signals</div>"
                    f"</div></div>"

                    # Win/loss bar
                    f"<div style='display:flex;border-radius:4px;overflow:hidden;height:5px;margin-bottom:0.22rem;'>"
                    f"<div style='width:{wr:.1f}%;background:{BULL};'></div>"
                    f"<div style='width:{lp:.1f}%;background:{BEAR};'></div></div>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:0.8rem;'>"
                    f"<span style='font-size:0.75rem;color:{BULL};font-weight:700;'>{row['wins']} wins ({wr:.1f}%)</span>"
                    f"<span style='font-size:0.75rem;color:{BEAR};font-weight:700;'>{row['losses']} losses ({lp:.1f}%)</span></div>"

                    # Stats grid
                    f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.28rem;margin-bottom:0.65rem;'>"
                    + _st("Signals",       str(n_c),                                 text_col)
                    + _st("Winners",       str(row["wins"]),                          BULL)
                    + _st("Losers",        str(row["losses"]),                        BEAR)
                    + _st("Avg Gain",      f"+{row['avg_gain']:.2f}%",               BULL)
                    + _st("Avg Loss",      f"{row['avg_loss']:.2f}%",                BEAR)
                    + _st("Avg Hold",      f"{row['avg_hold']:.0f}d",                INFO)
                    + _st("Profit Factor", f"{row['profit_factor']:.2f}",             BULL if row['profit_factor'] >= 1.5 else NEUT)
                    + _st("Expectancy",    f"{row['expectancy']:+.2f}%",              BULL if row['expectancy'] > 0 else BEAR)
                    + _st("Wilson Score",  f"{row['wilson']:.1f}",                   INFO)
                    + _st("Max W-Streak",  str(mc_w),                                BULL)
                    + _st("Max L-Streak",  str(mc_l),                                BEAR)
                    + _st("Signals/100",   f"{sf:.1f}",                              INFO)
                    + "</div>"

                    # Bottom 2-col: regime bars | consistency + monthly chart
                    f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.55rem;'>"
                    f"<div style='background:#141414;border:1px solid #252525;border-radius:8px;padding:0.65rem 0.75rem;'>"
                    f"<div style='font-size:0.75rem;color:#9e9e9e;font-weight:600;text-transform:uppercase;"
                    f"letter-spacing:0.7px;margin-bottom:0.45rem;'>Win Rate by Regime</div>"
                    + bars +
                    "</div>"
                    f"<div style='background:#141414;border:1px solid #252525;border-radius:8px;padding:0.65rem 0.75rem;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.28rem;'>"
                    f"<span style='font-size:0.75rem;color:#9e9e9e;font-weight:600;text-transform:uppercase;letter-spacing:0.7px;'>Consistency</span>"
                    f"<span style='font-size:0.78rem;font-weight:800;color:{con_color};'>{con_label}</span></div>"
                    f"<div style='font-size:0.72rem;color:{muted};margin-bottom:0.22rem;'>"
                    f"Std dev <strong style='color:{text_col};'>{con:.1f}%</strong> - lower is more reliable</div>"
                    + mwr_bars +
                    "</div></div></div>"
                ), unsafe_allow_html=True)

                # Trade history expander
                _sigs = combo_results.get(row["key"], {}).get("signals", [])
                if _sigs:
                    _cdf = pd.DataFrame(_sigs)
                    _ccols = [c for c in ["date","entry_price","exit_price","gain","days_held","regime","result"] if c in _cdf.columns]
                    _cdf = _cdf[_ccols].sort_values("date", ascending=False).reset_index(drop=True)
                    _cdf.index += 1
                    if "result" in _cdf.columns:
                        _cdf["result"] = _cdf["result"].map({
                            "profit": "Profit", "stop_loss": "Stop Loss",
                            "timeout_profit": "Timeout+", "timeout_loss": "Timeout-", "timeout": "Timeout",
                        }).fillna(_cdf["result"])
                    _cdf.columns = [c.replace("_", " ").title() for c in _cdf.columns]
                    with st.expander(f"Trade history -- {row['label']} ({len(_sigs)} trades)", expanded=False):
                        st.dataframe(_cdf, use_container_width=True)
                st.markdown("<div style='margin-bottom:0.3rem;'></div>", unsafe_allow_html=True)

            # ─────────────────────────────────────────────────────────────────
            # 4 ANALYSIS SUB-TABS
            # ─────────────────────────────────────────────────────────────────
            ctab1, ctab2 = st.tabs([
                "Combinations",
                "Regime Champions",
            ])

            # ── Leaderboard ───────────────────────────────────────────────────
            with ctab1:
                # Build dynamic combo math explanation
                from math import comb as _comb
                _n_inds = len(indicator_performance)
                _sz_names_math = {2: "pairs", 3: "triples", 4: "quads", 5: "5-way", 6: "6-way"}
                _combo_breakdown_parts = []
                _theory_total = 0
                for _sz in range(2, max_combo_depth + 1):
                    _cnt = _comb(_n_inds, _sz)
                    _theory_total += _cnt
                    _nm = _sz_names_math.get(_sz, f"{_sz}-way")
                    _combo_breakdown_parts.append(f"<strong style='color:#fff;'>{_cnt:,}</strong> {_nm}")
                _breakdown_str = " + ".join(_combo_breakdown_parts)
                _combo_math_html = (
                    f"<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.25);"
                    f"border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.85rem;'>"
                    f"<div style='font-size:0.6rem;font-weight:800;color:#90caf9;text-transform:uppercase;"
                    f"letter-spacing:0.7px;margin-bottom:0.4rem;'>How the math works -- your current settings</div>"
                    f"<div style='font-size:0.78rem;color:#e0e0e0;margin-bottom:0.3rem;line-height:1.5;'>"
                    f"You have <strong style='color:#fff;'>{_n_inds} indicators</strong> active and "
                    f"Combo Depth set to <strong style='color:#fff;'>{max_combo_depth}</strong>. "
                    f"The engine exhaustively tests every possible combination:</div>"
                    f"<div style='font-size:0.74rem;color:#90caf9;font-weight:600;margin-bottom:0.4rem;line-height:1.8;'>"
                    f"{_breakdown_str}</div>"
                    f"<div style='font-size:0.72rem;color:#9e9e9e;margin-bottom:0.25rem;'>"
                    f"Total theoretical: <strong style='color:#fff;'>{_theory_total:,} combinations</strong> tested.</div>"
                    f"<div style='font-size:0.72rem;color:#9e9e9e;'>"
                    f"Shown below: <strong style='color:#4caf50;'>{total_combos:,} combinations</strong> that had "
                    f"enough signals to pass your minimum threshold. Combos with zero co-occurrences are excluded.</div>"
                    f"</div>"
                )
                insight_toggle(
                    "combo_leaderboard",
                    "What is the Leaderboard? (click to see the math)",
                    _combo_math_html +
                    "<p><strong>Wilson Score</strong> is the default sort -- it penalises combinations with very few signals "
                    "so you only see combinations with a real statistical edge, not just lucky flukes.</p>"
                    "<p><strong>Win %</strong> -- how often both indicators fired at the same time and the trade was profitable.</p>"
                    "<p><strong>Expectancy</strong> -- average profit per trade = (Win% x Avg Gain) minus (Loss% x Avg Loss). "
                    "Positive means the combination has a mathematical edge over time.</p>"
                    "<p><strong>Profit Factor</strong> -- total gains divided by total losses. Above 1.5 is strong.</p>"
                    "<p><strong>Consistency (Std Dev)</strong> -- how stable the win rate is month to month. "
                    "Lower number = more reliable across different market conditions.</p>"
                    "<p>Click any column header in the table to re-sort instantly.</p>"
                )

                # Champion banner
                champ     = all_combo_data[0]
                champ_wr  = champ["win_rate"]
                champ_ea  = champ["expectancy"]
                champ_con = champ.get("consistency", 0)
                champ_pf  = champ.get("profit_factor", 0)
                champ_lp  = 100 - champ_wr
                ea_col    = "#81c784" if champ_ea > 0 else BEAR
                con_col   = "#81c784" if champ_con < 8 else ("#ffb74d" if champ_con < 15 else "#ef5350")
                pf_col    = "#81c784" if champ_pf >= 1.5 else "#ffb74d"
                _pf_tag   = "Very Strong" if champ_pf >= 2 else ("Strong" if champ_pf >= 1.5 else ("Decent" if champ_pf >= 1 else "Losing"))
                _ea_tag   = "Positive edge" if champ_ea > 0 else "Negative edge"
                _con_tag  = "Stable" if champ_con < 8 else ("Moderate" if champ_con < 15 else "Variable")
                _, _champ_wr_col = _wr_color(champ_wr)

                st.markdown(
                    # champion banner
                    f"<div style='background:#1a1a1a;border:1px solid #2d2d2d;"
                    f"border-radius:14px;padding:1.5rem 1.6rem 1.3rem 1.6rem;"
                    f"margin-bottom:1.2rem;'>"

                    # top row: crown badge + label + count
                    f"<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;'>"
                    f"<div style='font-size:1.5rem;line-height:1;'>&#127942;</div>"
                    f"<div>"
                    f"<div style='font-size:0.72rem;color:#9e9e9e;font-weight:600;margin-bottom:0.35rem;'>Best Combination Overall</div>"
                    f"<div style='font-size:0.7rem;color:#9e9e9e;margin-top:0.1rem;'>"
                    f"#{1} of {total_combos:,} &nbsp;&middot;&nbsp; {champ['size']}-Way</div>"
                    f"</div>"
                    f"</div>"

                    # indicator badges row
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.3rem;margin-bottom:1.1rem;'>"
                    f"{_badges(champ['indicators'])}</div>"

                    # big win rate + win/loss bar + secondary stats split
                    f"<div style='display:grid;grid-template-columns:auto 1fr;gap:1.5rem;align-items:center;margin-bottom:1rem;'>"

                    # left: giant win rate
                    f"<div style='text-align:center;padding:0.9rem 1.2rem;"
                    f"background:#212121;border:1px solid #2a2a2a;"
                    f"border-radius:10px;min-width:120px;'>"
                    f"<div style='font-size:0.62rem;font-weight:500;text-transform:uppercase;"
                    f"letter-spacing:0.8px;color:#757575;margin-bottom:0.3rem;'>Win Rate</div>"
                    f"<div style='font-size:3rem;font-weight:900;color:{_champ_wr_col};line-height:1;"
                    f"letter-spacing:-2px;'>{champ_wr:.1f}<span style='font-size:1.4rem;'>%</span></div>"
                    f"<div style='font-size:0.62rem;color:#757575;margin-top:0.25rem;'>"
                    f"{champ['wins']}W / {champ['losses']}L</div>"
                    f"</div>"

                    # right: win/loss bar + 5 stat pills
                    f"<div>"
                    f"<div style='display:flex;border-radius:5px;overflow:hidden;height:8px;margin-bottom:0.35rem;'>"
                    f"<div style='width:{champ_wr:.1f}%;background:linear-gradient(90deg,#43a047,#66bb6a);'></div>"
                    f"<div style='width:{champ_lp:.1f}%;background:linear-gradient(90deg,#e53935,#ef5350);'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:0.85rem;'>"
                    f"<span style='font-size:0.78rem;color:{BULL};font-weight:700;'>{champ['wins']} wins ({champ_wr:.1f}%)</span>"
                    f"<span style='font-size:0.78rem;color:{BEAR};font-weight:700;'>{champ['losses']} losses ({champ_lp:.1f}%)</span>"
                    f"</div>"
                    f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.4rem;'>"

                    # ── Box 1: Signals ──
                    f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;"
                    f"padding:0.6rem 0.35rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.3rem;'>Signals</div>"
                    f"<div style='font-size:1.4rem;font-weight:800;color:#90caf9;line-height:1;'>{champ['total']}</div>"
                    f"<div style='font-size:0.68rem;color:#616161;margin-top:0.25rem;'>"
                    f"{champ['wins']}W / {champ['losses']}L</div>"
                    f"</div>"

                    # ── Box 2: Expectancy ──
                    f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;"
                    f"padding:0.6rem 0.35rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.3rem;'>Expectancy</div>"
                    f"<div style='font-size:1.4rem;font-weight:800;color:{ea_col};line-height:1;'>{champ_ea:+.2f}%</div>"
                    f"<div style='font-size:0.68rem;color:{ea_col};margin-top:0.25rem;'>"
                    f"{_ea_tag}</div>"
                    f"</div>"

                    # ── Box 3: Profit Factor ──
                    f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;"
                    f"padding:0.6rem 0.35rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.3rem;'>Profit Factor</div>"
                    f"<div style='font-size:1.4rem;font-weight:800;color:{pf_col};line-height:1;'>{champ_pf:.2f}</div>"
                    f"<div style='font-size:0.68rem;color:{pf_col};margin-top:0.25rem;'>"
                    f"{_pf_tag}</div>"
                    f"</div>"

                    # ── Box 4: Combo Size ──
                    f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;"
                    f"padding:0.6rem 0.35rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.3rem;'>Combo Size</div>"
                    f"<div style='font-size:1.4rem;font-weight:800;color:#e0e0e0;line-height:1;'>{champ['size']}-Way</div>"
                    f"<div style='font-size:0.68rem;color:#616161;margin-top:0.25rem;'>indicators</div>"
                    f"</div>"

                    # ── Box 5: Consistency ──
                    f"<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;"
                    f"padding:0.6rem 0.35rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.3rem;'>Consistency</div>"
                    f"<div style='font-size:1.4rem;font-weight:800;color:{con_col};line-height:1;'>{champ_con:.1f}%</div>"
                    f"<div style='font-size:0.68rem;color:{con_col};margin-top:0.25rem;'>"
                    f"{_con_tag}</div>"
                    f"</div>"

                    f"</div></div></div>"  # end stats grid, right col, 2-col grid
                    f"</div>",
                    unsafe_allow_html=True,
                )
                # best regime badge (built separately to avoid quote nesting)
                _champ_br      = champ["best_regime"] or "N/A"
                _champ_br_col  = regime_color_map.get(champ["best_regime"], GOLD)
                _champ_br_pct  = champ["regime_perf"].get(champ["best_regime"], 0)
                st.markdown(
                    f"<div style='margin-top:-0.6rem;margin-bottom:1.2rem;font-size:0.75rem;color:{muted};"
                    f"padding:0.5rem 1.8rem;'>"
                    f"Best regime: <strong style='color:{_champ_br_col};font-size:0.8rem;'>"
                    f"{_champ_br} &mdash; {_champ_br_pct:.0f}% win rate in that regime</strong>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                render_save_combo_button(0, champ, _all_names, risk_val, reward_val, _period_label)
                for _row_start in [0, 5]:
                    _strip_items = all_combo_data[_row_start:_row_start + 5]
                    if not _strip_items:
                        break
                    _sh = (
                        f"<div style='display:grid;grid-template-columns:repeat({len(_strip_items)},1fr);"
                        f"gap:0.4rem;margin-bottom:0.4rem;'>"
                    )
                    for _sti, _str in enumerate(_strip_items):
                        _idx  = _row_start + _sti
                        _stac = combo_accent_cycle[_idx % len(combo_accent_cycle)]
                        _, _swr_col = _wr_color(_str['win_rate'])
                        _sh += (
                            f"<div style='background:#1e1e1e;border:1px solid #2d2d2d;"
                            f"border-radius:8px;padding:0.6rem 0.4rem;text-align:center;'>"
                            f"<div style='font-size:0.7rem;color:#757575;margin-bottom:0.2rem;'>#{_idx+1} &nbsp;&middot;&nbsp; {_str['size']}-Way</div>"
                            f"<div style='font-size:0.9rem;font-weight:700;color:#c8c8c8;line-height:1.4;margin-bottom:0.3rem;'>"
                            + " + ".join(_all_names.get(p, p) for p in _str["indicators"])
                            + f"</div>"
                            f"<div style='font-size:1.3rem;font-weight:800;color:{_swr_col};line-height:1;'>{_str['win_rate']:.0f}%</div>"
                            f"<div style='font-size:0.72rem;color:#757575;margin-top:0.2rem;'>{_str['total']} signals &nbsp;&middot;&nbsp; exp {_str['expectancy']:+.1f}%</div>"
                            f"</div>"
                        )
                    _sh += "</div>"
                    st.markdown(_sh, unsafe_allow_html=True)

                st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

                # Full sortable table
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
                        "Std Dev":        round(_tr.get("consistency", 0), 1),
                        "Max W-Streak":   _tr.get("max_consec_wins", 0),
                        "Max L-Streak":   _tr.get("max_consec_losses", 0),
                        "Sig/100 Bars":   round(_tr.get("signal_freq", 0), 1),
                        "Best Regime":    _tr["best_regime"] or "--",
                    })
                _tbl_df = pd.DataFrame(_tbl_rows).set_index("Rank")
                st.markdown(
                    f"<div style='font-size:0.7rem;color:{muted};margin-bottom:0.35rem;font-weight:600;'>"
                    f"Click any column header to sort &nbsp;&bull;&nbsp; {total_combos:,} combinations:</div>",
                    unsafe_allow_html=True,
                )
                st.dataframe(_tbl_df, use_container_width=True, height=500)

            # ── Regime Champions ──────────────────────────────────────────────
            with ctab2:
                insight_toggle(
                    "combo_regime",
                    "What is Regime Champions?",
                    "<p>The market alternates between three conditions. Each tab shows which indicator combinations "
                    "performed best <strong>specifically inside that regime</strong>, not overall.</p>"
                    "<p><strong>TREND</strong> -- price is making clear directional moves (ADX above 25). "
                    "Trend-following combinations shine here.</p>"
                    "<p><strong>RANGE</strong> -- price moves sideways between support and resistance. "
                    "Mean-reversion and oscillator combos work better.</p>"
                    "<p><strong>VOLATILE</strong> -- large rapid moves, often around news or earnings. "
                    "Breakout and volatility combos may catch big moves.</p>"
                    "<p>Use this to switch which combination you watch depending on what the market is doing today.</p>"
                )
                for _rgn, _rgc in [("TREND", INFO), ("RANGE", NEUT), ("VOLATILE", BEAR)]:
                    _reg_combos = sorted(
                        [x for x in all_combo_data if x["regime_perf"].get(_rgn, 0) > 0],
                        key=lambda x: x["regime_perf"].get(_rgn, 0), reverse=True,
                    )
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.45rem;margin:0.9rem 0 0.5rem 0;'>"
                        f"<span style='width:3px;height:1.1rem;background:{_rgc};border-radius:2px;"
                        f"flex-shrink:0;display:inline-block;'></span>"
                        f"<span style='font-size:0.82rem;font-weight:800;color:{_rgc};"
                        f"text-transform:uppercase;letter-spacing:0.5px;'>{_rgn} Regime</span>"
                        f"<span style='font-size:0.62rem;color:{muted};'>({len(_reg_combos)} combos)</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if not _reg_combos:
                        st.markdown(
                            f"<div style='color:{muted};font-size:0.74rem;padding:0.3rem 0;'>"
                            f"No regime data yet. Try a longer date range.</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        _rcs = _reg_combos[:5]
                        _rhtml = (
                            f"<div style='display:grid;grid-template-columns:repeat({len(_rcs)},1fr);"
                            f"gap:0.35rem;margin-bottom:0.5rem;'>"
                        )
                        for _ri, _rr in enumerate(_rcs):
                            _rwr = _rr["regime_perf"].get(_rgn, 0)
                            _, _rc_wr_col = _wr_color(_rwr)
                            _rhtml += (
                                f"<div style='background:#1e1e1e;border:1px solid #2d2d2d;"
                                f"border-left:3px solid {_rgc};border-radius:8px;"
                                f"padding:0.65rem 0.45rem;text-align:center;'>"
                                f"<div style='font-size:0.7rem;color:#757575;margin-bottom:0.2rem;'>#{_ri+1}</div>"
                                f"<div style='font-size:0.9rem;font-weight:700;color:#c8c8c8;line-height:1.4;margin-bottom:0.25rem;'>"
                                + " + ".join(_all_names.get(p, p) for p in _rr["indicators"])
                                + f"</div>"
                                f"<div style='font-size:1.2rem;font-weight:800;color:{_rc_wr_col};line-height:1;'>{_rwr:.0f}%</div>"
                                f"<div style='font-size:0.7rem;color:#757575;margin-top:0.15rem;'>{_rgn} &middot; {_rr['total']} signals</div>"
                                f"</div>"
                            )
                        _rhtml += "</div>"
                        st.markdown(_rhtml, unsafe_allow_html=True)

                        _rtbl = []
                        for _rti, _rtr in enumerate(_reg_combos[:30]):
                            _rtbl.append({
                                "Rank":            _rti + 1,
                                "Combination":     _rtr["label"],
                                "Size":            f"{_rtr['size']}-Way",
                                f"{_rgn} Win %":   round(_rtr["regime_perf"].get(_rgn, 0), 1),
                                "Overall Win %":   round(_rtr["win_rate"], 1),
                                "Signals":         _rtr["total"],
                                "Profit Factor":   round(_rtr["profit_factor"], 2),
                                "Expectancy %":    round(_rtr["expectancy"], 2),
                                "Wilson Score":    round(_rtr["wilson"], 1),
                                "Std Dev":         round(_rtr.get("consistency", 0), 1),
                            })
                        with st.expander(f"Top {len(_rtbl)} combos for {_rgn}", expanded=False):
                            st.dataframe(pd.DataFrame(_rtbl).set_index("Rank"), use_container_width=True)
                    st.markdown(
                        f"<hr style='border:none;border-top:1px solid {border};margin:0.55rem 0;'>",
                        unsafe_allow_html=True,
                    )

            # ── Deep Cards (continues in same Combinations tab) ────────────────────────────
            with ctab1:
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:0.6rem;"
                    f"margin:1.8rem 0 1rem 0;'>"
                    f"<div style='flex:1;height:1px;background:{border};'></div>"
                    f"<span style='font-size:0.65rem;font-weight:800;text-transform:uppercase;"
                    f"letter-spacing:1.2px;color:{muted};padding:0 0.6rem;'>Deep Analysis by Combo Size</span>"
                    f"<div style='flex:1;height:1px;background:{border};'></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                insight_toggle(
                    "combo_deepcards",
                    "What does 2-Way / 3-Way / 4-Way mean? (click to understand)",
                    "<h4 style='margin:0 0 0.6rem 0;color:#fff;font-size:0.9rem;'>What is a N-Way Combination?</h4>"
                    "<p>A <strong>combination</strong> means: multiple indicators all agreed at the same moment and a trade signal fired. "
                    "The number tells you how many indicators had to agree together:</p>"
                    "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem;margin:0.6rem 0;'>"
                    "<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#90caf9;'>2-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "Two indicators fired at the same bar. Example: RSI went oversold <strong>AND</strong> MACD crossed bullish at the same candle. "
                    "More signals, easier to trigger.</div></div>"
                    "<div style='background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#81c784;'>3-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "Three indicators all agreed. Example: RSI oversold <strong>AND</strong> MACD bullish cross <strong>AND</strong> price above EMA. "
                    "Rarer signal but higher conviction.</div></div>"
                    "<div style='background:rgba(255,215,0,0.06);border:1px solid rgba(255,215,0,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#FFD700;'>4-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "Four indicators in agreement simultaneously. Very rare but extremely high confidence when it happens. "
                    "Fewer total trades but often a better win rate.</div></div>"
                    "<div style='background:rgba(156,39,176,0.08);border:1px solid rgba(156,39,176,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#ce93d8;'>5 / 6-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "Five or six indicators must all align. Extremely rare signals -- only appears a handful of times per year. "
                    "Use these as ultra-high-confidence confirmation only.</div></div>"
                    "</div>"
                    "<p style='margin-top:0.5rem;'><strong style='color:#FFD700;'>The trade-off:</strong> more indicators = fewer signals but higher quality. "
                    "Fewer indicators = more signals but more noise. Compare the win rates across sizes in the Leaderboard tab to find your sweet spot.</p>"
                    "<hr style='border:none;border-top:1px solid #303030;margin:0.8rem 0;'>"
                    "<p style='font-weight:700;color:#fff;margin-bottom:0.4rem;'>Each card below shows the full picture for one combination:</p>"
                    "<ul>"
                    "<li><strong>Win % bar</strong> -- green = wins, red = losses, split proportionally.</li>"
                    "<li><strong>Avg Gain / Avg Loss</strong> -- average size of winning vs losing trades.</li>"
                    "<li><strong>Avg Hold</strong> -- average number of days the trade was open before closing.</li>"
                    "<li><strong>Profit Factor</strong> -- total profit divided by total loss. Above 1.5 is strong.</li>"
                    "<li><strong>Expectancy</strong> -- average money made per trade. Positive = edge exists.</li>"
                    "<li><strong>Wilson Score</strong> -- confidence-adjusted win rate that penalises small sample sizes.</li>"
                    "<li><strong>Max W-Streak / L-Streak</strong> -- longest consecutive winning or losing run.</li>"
                    "<li><strong>Signals/100</strong> -- how frequently this combination fires (per 100 price bars).</li>"
                    "<li><strong>Consistency (Std Dev)</strong> -- how stable the monthly win rate is. Lower = more reliable all year.</li>"
                    "<li><strong>Monthly bars</strong> -- each bar = one month. Taller green = high win rate that month.</li>"
                    "<li><strong>Trade history</strong> -- expand to see every individual trade with entry, exit, gain, and regime.</li>"
                    "</ul>"
                )
                _sz_names = {
                    2: "2-Way Pairs", 3: "3-Way Triples", 4: "4-Way Quadruples",
                    5: "5-Way Quintuples", 6: "6-Way Combinations",
                }
                for _sv in sorted(set(x["size"] for x in all_combo_data)):
                    _sc   = [x for x in all_combo_data if x["size"] == _sv]
                    _sn   = _sz_names.get(_sv, f"{_sv}-Way")
                    _bwr  = _sc[0]["win_rate"] if _sc else 0
                    _bex  = _sc[0]["expectancy"] if _sc else 0
                    with st.expander(
                        f"{_sn}  --  {len(_sc)} combos  |  Best WR {_bwr:.0f}%  |  Best Exp {_bex:+.2f}%",
                        expanded=(_sv == 2),
                    ):
                        # Top-5 mini strip
                        _ns3 = min(5, len(_sc))
                        _ss3 = (
                            f"<div style='display:grid;grid-template-columns:repeat({_ns3},1fr);"
                            f"gap:0.28rem;margin-bottom:0.65rem;'>"
                        )
                        for _xi, _xr in enumerate(_sc[:_ns3]):
                            _, _xs_wr_col = _wr_color(_xr['win_rate'])
                            _ss3 += (
                                f"<div style='background:#1e1e1e;border:1px solid #2d2d2d;"
                                f"border-radius:7px;padding:0.65rem 0.4rem;text-align:center;'>"
                                f"<div style='font-size:0.7rem;color:#757575;margin-bottom:0.2rem;'>#{_xi+1}</div>"
                                f"<div style='font-size:0.9rem;font-weight:700;color:#c8c8c8;line-height:1.35;margin-bottom:0.25rem;'>"
                                + " + ".join(_all_names.get(p, p) for p in _xr["indicators"])
                                + f"</div>"
                                f"<div style='font-size:1.15rem;font-weight:800;color:{_xs_wr_col};'>{_xr['win_rate']:.0f}%</div>"
                                f"<div style='font-size:0.7rem;color:#757575;'>{_xr['total']} signals</div>"
                                f"</div>"
                            )
                        _ss3 += "</div>"
                        st.markdown(_ss3, unsafe_allow_html=True)

                        # Detail cards
                        _top_n = _sc[:int(_cc_top_per_group)]
                        _rest2 = _sc[int(_cc_top_per_group):]
                        for _ci, _cr in enumerate(_top_n):
                            _cac4 = combo_accent_cycle[_ci % len(combo_accent_cycle)]
                            _make_combo_card(_cr, f"#{_ci + 1}", _cac4)
                            render_save_combo_button(
                                _ci + _sv * 100, _cr, _all_names, risk_val, reward_val, _period_label
                            )

                        # Remaining in table
                        if _rest2:
                            _rest_rows2 = [{
                                "Rank":          int(_cc_top_per_group) + _ri + 1,
                                "Combination":   _rr["label"],
                                "Signals":       _rr["total"],
                                "Win %":         round(_rr["win_rate"], 1),
                                "Avg Gain %":    round(_rr["avg_gain"], 2),
                                "Profit Factor": round(_rr["profit_factor"], 2),
                                "Expectancy %":  round(_rr["expectancy"], 2),
                                "Wilson Score":  round(_rr["wilson"], 1),
                                "Std Dev":       round(_rr.get("consistency", 0), 1),
                                "Max W-Streak":  _rr.get("max_consec_wins", 0),
                                "Max L-Streak":  _rr.get("max_consec_losses", 0),
                                "Signals/100":   round(_rr.get("signal_freq", 0), 1),
                                "Best Regime":   _rr["best_regime"] or "--",
                            } for _ri, _rr in enumerate(_rest2)]
                            with st.expander(f"Remaining {len(_rest2)} {_sn} combinations", expanded=False):
                                st.dataframe(pd.DataFrame(_rest_rows2).set_index("Rank"), use_container_width=True)
