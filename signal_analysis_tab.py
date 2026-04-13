import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
from favorites_tab import render_save_button
from ui_helpers import insight_toggle


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────
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

    # ── CSS ──────────────────────────────────────────────────────────────────
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

    # ── Controls row ──────────────────────────────────────────────────────────
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

    # ── Run engines ───────────────────────────────────────────────────────────
    with st.spinner("Running signal analysis…"):
        signals_df = detect_signals(df)
        results, successful_signals, all_signal_details = evaluate_signal_success(
            df, signals_df, profit_target, holding_period, stop_loss
        )
        consensus_signals   = find_consensus_signals(signals_df)
        combo_results       = analyze_indicator_combinations(
            signals_df, df, profit_target, holding_period, stop_loss, max_combo_depth
        )
        monthly_performance = calculate_monthly_performance(all_signal_details)

    # ── Aggregate stats ───────────────────────────────────────────────────────
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
    
    # ── Wilson lower-bound helper ─────────────────────────────────────────────
    def _wilson(n, pct):
        if n == 0:
            return 0.0
        p = pct / 100
        z = 1.645
        denom  = 1 + z * z / n
        centre = p + z * z / (2 * n)
        spread = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
        return (centre - spread) / denom * 100

    # ══════════════════════════════════════════════════════════════════════════
    # 1. KPI ROW  (6 tiles)
    # ══════════════════════════════════════════════════════════════════════════
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

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TABS
    # ══════════════════════════════════════════════════════════════════════════
    tab_ind, tab_combo = st.tabs([
        "Indicator Leaderboard",
        "Indicator Combinations",
    ])

    # ── indicator map (key → name, category, chart_fn) ───────────────────────
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

    # ── build per-indicator stats ─────────────────────────────────────────────
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

    # Remove indicators with 100% win rate — statistically unreliable (too few signals or data artifact)
    indicator_performance = [x for x in indicator_performance if x["win_rate"] < 100]
    indicator_performance.sort(key=lambda x: (x["expectancy"], x["total"]), reverse=True)
    card_accents = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — INDICATOR LEADERBOARD
    # ══════════════════════════════════════════════════════════════════════════
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
                "Best Regime":    p["best_regime"] or "—",
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
                    + _sb("Best Regime", ind["best_regime"] or "—", br_color, _hex_rgba(br_color,.10))
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
                        f"Signal history — {ind['name']} ({len(sigs)} trades)",
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

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — DEEP COMBINATION EXPLORER
    # ══════════════════════════════════════════════════════════════════════════
    with tab_combo:
        _all_names = {p["key"]: p["name"] for p in indicator_performance}
        _all_accs  = {p["key"]: card_accents[i % len(card_accents)]
                      for i, p in enumerate(indicator_performance)}
        combo_accent_cycle = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

        # ── Filter / sort controls ────────────────────────────────────────────
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

        # ── Resolve size filter ───────────────────────────────────────────────
        _size_filter = None
        if _cc_size != "All sizes":
            _size_filter = int(_cc_size.split("-")[0])

        # ── Build all_combo_data ──────────────────────────────────────────────
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
                    "avg_hold":     cd.get("avg_hold", 0),
                    "regime_perf":  rp,
                    "best_regime":  best_r,
                    "wilson":       _wilson(n_c, wr),
                })
            all_combo_data.sort(key=lambda x: x[_sort_key], reverse=True)

        if not all_combo_data:
            st.info("No combinations found. Try increasing Combo Depth, a longer date range, or lower Min Signals.")
        else:
            total_combos = len(all_combo_data)

            # ── Helper: build indicator badge row HTML ────────────────────────
            def _badges(parts):
                html = ""
                for idx, p in enumerate(parts):
                    color = _all_accs.get(p, GOLD)
                    name  = _all_names.get(p, p)
                    html += (f"<span style='background:{color}22;color:{color};font-size:0.8rem;"
                             f"font-weight:800;padding:0.28rem 0.65rem;border-radius:20px;"
                             f"border:1px solid {color}55;white-space:nowrap;'>{name}</span>")
                    if idx < len(parts) - 1:
                        html += (f"<span style='color:{muted};font-weight:700;font-size:0.95rem;"
                                 f"padding:0 0.15rem;'>+</span>")
                return html

            # ── Champion banner ───────────────────────────────────────────────
            champ    = all_combo_data[0]
            champ_wr = champ["win_rate"]
            champ_ea = champ["expectancy"]
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(255,215,0,0.10),rgba(76,175,80,0.08));
                        border:2px solid rgba(255,215,0,0.50);border-radius:16px;
                        padding:1.5rem 1.8rem;margin-bottom:1.5rem;'>
              <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.7rem;'>
                <span style='font-size:1rem;'>&#127942;</span>
                <span style='font-size:0.63rem;font-weight:800;text-transform:uppercase;
                      letter-spacing:1px;color:{GOLD};'>BEST COMBINATION FOUND</span>
                <span style='margin-left:auto;font-size:0.65rem;color:{muted};font-weight:600;'>
                  {total_combos:,} valid combinations analysed</span>
              </div>
              <div style='display:flex;flex-wrap:wrap;align-items:center;
                          gap:0.35rem;margin-bottom:1rem;'>
                {_badges(champ["indicators"])}
              </div>
              <div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.6rem;'>
                <div style='text-align:center;'>
                  <div style='font-size:2rem;font-weight:900;color:{GOLD};line-height:1;'>{champ_wr:.1f}%</div>
                  <div style='font-size:0.6rem;color:{muted};text-transform:uppercase;'>Win Rate</div>
                </div>
                <div style='text-align:center;'>
                  <div style='font-size:2rem;font-weight:900;color:{BULL};line-height:1;'>{champ["wins"]}</div>
                  <div style='font-size:0.6rem;color:{muted};text-transform:uppercase;'>Winners</div>
                </div>
                <div style='text-align:center;'>
                  <div style='font-size:2rem;font-weight:900;color:{text_col};line-height:1;'>{champ["total"]}</div>
                  <div style='font-size:0.6rem;color:{muted};text-transform:uppercase;'>Signals</div>
                </div>
                <div style='text-align:center;'>
                  <div style='font-size:2rem;font-weight:900;color:{BULL if champ_ea > 0 else BEAR};line-height:1;'>{champ_ea:+.2f}%</div>
                  <div style='font-size:0.6rem;color:{muted};text-transform:uppercase;'>Expectancy</div>
                </div>
                <div style='text-align:center;'>
                  <div style='font-size:2rem;font-weight:900;color:{INFO};line-height:1;'>{champ["size"]}-Way</div>
                  <div style='font-size:0.6rem;color:{muted};text-transform:uppercase;'>Combo Size</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Quick top-6 strip across all sizes ───────────────────────────
            _top6  = all_combo_data[:6]
            _strip = (f"<div style='display:grid;grid-template-columns:repeat({len(_top6)},1fr);"
                      f"gap:0.5rem;margin-bottom:1.5rem;'>")
            for _si, _sr in enumerate(_top6):
                _ac = combo_accent_cycle[_si % len(combo_accent_cycle)]
                _strip += (
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-top:2px solid {_ac};border-radius:10px;"
                    f"padding:0.75rem 0.5rem;text-align:center;'>"
                    f"<div style='font-size:0.55rem;color:{muted};font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:0.6px;margin-bottom:0.2rem;'>"
                    f"#{_si+1} &middot; {_sr['size']}-Way</div>"
                    f"<div style='font-size:0.68rem;font-weight:800;color:{_ac};line-height:1.35;"
                    f"margin-bottom:0.25rem;'>"
                    + " + ".join(_all_names.get(p, p) for p in _sr["indicators"])
                    + f"</div>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{text_col};'>"
                    f"{_sr['win_rate']:.0f}%</div>"
                    f"<div style='font-size:0.6rem;color:{muted};'>{_sr['total']} signals</div>"
                    f"</div>"
                )
            _strip += "</div>"
            st.markdown(_strip, unsafe_allow_html=True)

            # ── Full sortable table ───────────────────────────────────────────
            _tbl_rows = []
            for _ti, _tr in enumerate(all_combo_data):
                _tbl_rows.append({
                    "Rank":          _ti + 1,
                    "Combination":   _tr["label"],
                    "Size":          f"{_tr['size']}-Way",
                    "Signals":       _tr["total"],
                    "Wins":          _tr["wins"],
                    "Losses":        _tr["losses"],
                    "Win %":         round(_tr["win_rate"], 1),
                    "Avg Gain %":    round(_tr["avg_gain"], 2),
                    "Avg Loss %":    round(_tr["avg_loss"], 2),
                    "Profit Factor": round(_tr["profit_factor"], 2),
                    "Expectancy %":  round(_tr["expectancy"], 2),
                    "Wilson Score":  round(_tr["wilson"], 1),
                    "Best Regime":   _tr["best_regime"] or "—",
                })
            _tbl_df = pd.DataFrame(_tbl_rows).set_index("Rank")
            with st.expander(
                f"Full Combination Table — {total_combos:,} valid combos (click to expand & sort)",
                expanded=False,
            ):
                st.dataframe(_tbl_df, use_container_width=True, height=460)

            # ── Combo card renderer ───────────────────────────────────────────
            def _make_combo_card(row, rank_label, accent):
                wr   = row["win_rate"]
                lp   = 100 - wr
                n_c  = row["total"]
                br_c = regime_color_map.get(row["best_regime"], accent)
                _br_label = (row["best_regime"] + f" ({row['regime_perf'].get(row['best_regime'], 0):.0f}%)"
                             if row["best_regime"] else "—")
                rp = row["regime_perf"]

                # Regime bars
                bars = ""
                for reg, pct in rp.items():
                    rc  = regime_color_map.get(reg, "#888")
                    bw  = min(100, max(0, pct))
                    bars += (
                        f"<div style='margin-bottom:0.55rem;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.2rem;'>"
                        f"<span style='font-size:0.72rem;color:{muted};font-weight:700;"
                        f"text-transform:uppercase;letter-spacing:0.5px;'>{reg}</span>"
                        f"<span style='font-size:0.78rem;font-weight:800;color:{rc};'>{pct:.0f}%</span>"
                        f"</div>"
                        f"<div style='background:{border};border-radius:4px;height:6px;'>"
                        f"<div style='background:{rc};border-radius:4px;height:6px;width:{bw:.0f}%;'></div>"
                        f"</div></div>"
                    )

                def _st3(lbl, val, col):
                    return (
                        f"<div style='background:{panel_alt};border:1px solid {border};"
                        f"border-radius:8px;padding:0.8rem 0.5rem;text-align:center;'>"
                        f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
                        f"letter-spacing:0.5px;margin-bottom:0.3rem;'>{lbl}</div>"
                        f"<div style='font-size:1.15rem;font-weight:800;color:{col};line-height:1;'>{val}</div>"
                        f"</div>"
                    )

                st.markdown((
                    f"<div style='background:{panel};border:1px solid {border};"
                    f"border-top:3px solid {accent};border-radius:14px;"
                    f"padding:1.4rem 1.5rem;margin-bottom:0.8rem;'>"
                    # header
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:flex-start;margin-bottom:1rem;'>"
                    f"<div style='flex:1;min-width:0;'>"
                    f"<div style='font-size:0.6rem;color:{muted};font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.5rem;'>"
                    f"{rank_label} &middot; {row['size']}-Indicator Combination</div>"
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.35rem;"
                    f"margin-bottom:0.4rem;'>{_badges(row['indicators'])}</div>"
                    f"<div style='font-size:0.72rem;color:{muted};'>Best regime: "
                    f"<span style='color:{br_c};font-weight:700;'>{_br_label}</span></div>"
                    f"</div>"
                    f"<div style='text-align:right;flex-shrink:0;margin-left:1rem;'>"
                    f"<div style='font-size:2.8rem;font-weight:900;color:{accent};line-height:1;'>"
                    f"{wr:.1f}<span style='font-size:1.2rem;'>%</span></div>"
                    f"<div style='font-size:0.7rem;color:{muted};text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-top:0.1rem;'>"
                    f"Win Rate &middot; {n_c} signals</div>"
                    f"</div></div>"
                    # win/loss bar
                    f"<div style='display:flex;border-radius:6px;overflow:hidden;"
                    f"height:7px;margin-bottom:0.35rem;'>"
                    f"<div style='width:{wr:.1f}%;background:{BULL};'></div>"
                    f"<div style='width:{lp:.1f}%;background:{BEAR};'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:1.2rem;'>"
                    f"<span style='font-size:0.72rem;color:{BULL};font-weight:700;'>"
                    f"&#10003; {row['wins']} wins ({wr:.1f}%)</span>"
                    f"<span style='font-size:0.72rem;color:{BEAR};font-weight:700;'>"
                    f"{row['losses']} losses ({lp:.1f}%) &#10005;</span></div>"
                    # stats + regime panel
                    f"<div style='display:grid;grid-template-columns:1fr 200px;gap:1.2rem;'>"
                    f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
                    f"gap:0.5rem;align-content:start;'>"
                    + _st3("Signals",      str(n_c),                          text_col)
                    + _st3("Winners",      str(row["wins"]),                   BULL)
                    + _st3("Losers",       str(row["losses"]),                 BEAR)
                    + _st3("Avg Gain",     f"+{row['avg_gain']:.2f}%",         BULL)
                    + _st3("Avg Loss",     f"{row['avg_loss']:.2f}%",          BEAR)
                    + _st3("Avg Hold",     f"{row['avg_hold']:.0f}d",          INFO)
                    + _st3("Profit Factor",f"{row['profit_factor']:.2f}",      BULL if row['profit_factor'] >= 1.5 else NEUT)
                    + _st3("Expectancy",   f"{row['expectancy']:+.2f}%",       BULL if row['expectancy'] > 0 else BEAR)
                    + _st3("Wilson",       f"{row['wilson']:.1f}",             INFO)
                    + "</div>"
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-radius:10px;padding:1rem 1.1rem;'>"
                    f"<div style='font-size:0.72rem;color:{accent};font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.8rem;'>"
                    f"Regime Win Rate</div>"
                    + bars
                    + "</div></div></div>"
                ), unsafe_allow_html=True)

                # Trade history expandable
                _sigs = combo_results.get(row["key"], {}).get("signals", [])
                if _sigs:
                    _cdf = pd.DataFrame(_sigs)
                    _ccols = [c for c in ["date", "entry_price", "exit_price",
                                          "gain", "days_held", "regime", "result"]
                              if c in _cdf.columns]
                    _cdf = _cdf[_ccols].sort_values("date", ascending=False).reset_index(drop=True)
                    _cdf.index += 1
                    if "result" in _cdf.columns:
                        _cdf["result"] = _cdf["result"].map({
                            "profit": "Profit", "stop_loss": "Stop Loss",
                            "timeout_profit": "Timeout ↑", "timeout_loss": "Timeout ↓",
                            "timeout": "Timeout",
                        }).fillna(_cdf["result"])
                    _cdf.columns = [c.replace("_", " ").title() for c in _cdf.columns]
                    with st.expander(
                        f"Trade history — {row['label']} ({len(_sigs)} trades)",
                        expanded=False,
                    ):
                        st.dataframe(_cdf, use_container_width=True)

                st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

            # ── Sections grouped by combo size ────────────────────────────────
            _size_name_map = {
                2: "2-Way Pairs",
                3: "3-Way Triples",
                4: "4-Way Quadruples",
                5: "5-Way Quintuples",
                6: "6-Way Combinations",
            }
            for _sv in sorted(set(x["size"] for x in all_combo_data)):
                _sc  = [x for x in all_combo_data if x["size"] == _sv]
                _sn  = _size_name_map.get(_sv, f"{_sv}-Way Combinations")
                _bwr = _sc[0]["win_rate"] if _sc else 0
                _bex = _sc[0]["expectancy"] if _sc else 0

                with st.expander(
                    f"{_sn}  —  {len(_sc)} combos  |  Best win rate: {_bwr:.0f}%  |  Best expectancy: {_bex:+.2f}%",
                    expanded=(_sv <= 3),
                ):
                    # Quick mini-strip for this group (top 6)
                    _ns = min(6, len(_sc))
                    _ss = (f"<div style='display:grid;grid-template-columns:repeat({_ns},1fr);"
                           f"gap:0.4rem;margin-bottom:1rem;'>")
                    for _xi, _xr in enumerate(_sc[:_ns]):
                        _xac = combo_accent_cycle[_xi % len(combo_accent_cycle)]
                        _ss += (
                            f"<div style='background:{panel_alt};border:1px solid {border};"
                            f"border-top:2px solid {_xac};border-radius:8px;"
                            f"padding:0.6rem 0.4rem;text-align:center;'>"
                            f"<div style='font-size:0.55rem;color:{muted};font-weight:700;"
                            f"margin-bottom:0.2rem;'>#{_xi+1}</div>"
                            f"<div style='font-size:0.65rem;font-weight:800;color:{_xac};"
                            f"line-height:1.3;'>"
                            + " + ".join(_all_names.get(p, p) for p in _xr["indicators"])
                            + f"</div>"
                            f"<div style='font-size:1rem;font-weight:900;color:{text_col};'>"
                            f"{_xr['win_rate']:.0f}%</div>"
                            f"<div style='font-size:0.58rem;color:{muted};'>{_xr['total']} sig</div>"
                            f"</div>"
                        )
                    _ss += "</div>"
                    st.markdown(_ss, unsafe_allow_html=True)

                    # Detail cards for top N in this group
                    _top_cards = _sc[:int(_cc_top_per_group)]
                    _rest      = _sc[int(_cc_top_per_group):]

                    for _ci, _cr in enumerate(_top_cards):
                        _cac = combo_accent_cycle[_ci % len(combo_accent_cycle)]
                        _make_combo_card(_cr, f"#{_ci + 1}", _cac)

                    # Remaining rows as a compact table
                    if _rest:
                        _rest_rows = [{
                            "Rank":           int(_cc_top_per_group) + _ri + 1,
                            "Combination":    _rr["label"],
                            "Signals":        _rr["total"],
                            "Win %":          round(_rr["win_rate"], 1),
                            "Avg Gain %":     round(_rr["avg_gain"], 2),
                            "Profit Factor":  round(_rr["profit_factor"], 2),
                            "Expectancy %":   round(_rr["expectancy"], 2),
                            "Wilson Score":   round(_rr["wilson"], 1),
                            "Best Regime":    _rr["best_regime"] or "—",
                        } for _ri, _rr in enumerate(_rest)]
                        _rest_df = pd.DataFrame(_rest_rows).set_index("Rank")
                        with st.expander(
                            f"Remaining {len(_rest)} {_sn} combinations",
                            expanded=False,
                        ):
                            st.dataframe(_rest_df, use_container_width=True)
