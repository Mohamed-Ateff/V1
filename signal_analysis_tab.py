import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
from favorites_tab import render_save_button, render_save_indicator_button, render_save_combo_button
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
    st.markdown(
        """
        <style>
        .sa-kpi-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.65rem;
            margin-bottom: 1.2rem;
        }
        .sa-kpi-card {
            background: #1b1b1b;
            border: 1px solid #272727;
            border-radius: 10px;
            padding: 0.8rem 0.85rem;
        }
        .sa-kpi-label {
            font-size: 0.62rem;
            color: #606060;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .sa-kpi-value {
            font-size: 1.55rem;
            font-weight: 900;
            line-height: 1;
        }
        .sa-kpi-sub {
            font-size: 0.68rem;
            color: #808080;
            margin-top: 0.25rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        st.markdown(
            "<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:1px;font-weight:700;margin-bottom:0.3rem;'>Risk</div>",
            unsafe_allow_html=True,
        )
        risk_val = st.number_input(
            "Risk",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            label_visibility="collapsed",
            key="sa_risk_val",
        )
    with c2:
        st.markdown(
            "<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:1px;font-weight:700;margin-bottom:0.3rem;'>Reward</div>",
            unsafe_allow_html=True,
        )
        reward_val = st.number_input(
            "Reward",
            min_value=1,
            max_value=100,
            value=2,
            step=1,
            label_visibility="collapsed",
            key="sa_reward_val",
        )
    with c3:
        st.markdown(
            "<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:1px;font-weight:700;margin-bottom:0.3rem;'>Holding Period</div>",
            unsafe_allow_html=True,
        )
        _period_map = {"Short (5d)": 5, "Medium (63d)": 63, "Long (252d)": 252}
        _period_label = st.selectbox(
            "Period",
            list(_period_map.keys()),
            index=1,
            label_visibility="collapsed",
            key="sa_period_val",
        )
        holding_period = _period_map[_period_label]
    with c4:
        st.markdown(
            "<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:1px;font-weight:700;margin-bottom:0.3rem;'>Combo Depth</div>",
            unsafe_allow_html=True,
        )
        _depth_opts = {
            "Pairs only (2)": 2,
            "Up to Triples (3)": 3,
            "Up to Quads (4)": 4,
            "Up to 5-Way (5)": 5,
            "Up to 6-Way (6)": 6,
        }
        _depth_label = st.selectbox(
            "Depth",
            list(_depth_opts.keys()),
            index=2,
            label_visibility="collapsed",
            key="sa_combo_depth",
        )
        max_combo_depth = _depth_opts[_depth_label]
    combo_signal_window = 3

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
            signals_df, df, profit_target, holding_period, stop_loss, max_combo_depth,
            combo_signal_window,
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
        "What do these numbers mean? (tap to read)",
        "<p><strong>Win Rate</strong> — Out of all the signals, how many actually made money? Above 50% means it's right more often than wrong.</p>"
        "<p><strong>Total Signals</strong> — How many times this indicator said 'buy' during the time period you're testing.</p>"
        "<p><strong>Successful</strong> — Trades that hit your profit target before getting stopped out.</p>"
        "<p><strong>Failed</strong> — Trades that hit the stop loss or ran out of time.</p>"
        "<p><strong>Profit Factor</strong> — Total money made ÷ total money lost. Above 1.0 = making money. Above 2.0 = very good.</p>"
        "<p><strong>Expectancy</strong> — On average, how much do you make (or lose) per trade? Positive = you're making money over time.</p>"
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
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Total Signals</div>
            <div class='sa-kpi-value' style='color:{INFO};text-shadow:0 0 18px {INFO}33;'>{total_signals}</div>
            <div class='sa-kpi-sub'>All indicators</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Successful</div>
            <div class='sa-kpi-value' style='color:{BULL};text-shadow:0 0 18px {BULL}33;'>{total_successful}</div>
            <div class='sa-kpi-sub'>Hit {risk_val}:{reward_val} target</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Failures</div>
            <div class='sa-kpi-value' style='color:{BEAR};text-shadow:0 0 18px {BEAR}33;'>{total_failed}</div>
            <div class='sa-kpi-sub'>Missed target</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Win Rate</div>
            <div class='sa-kpi-value' style='color:{sc};text-shadow:0 0 18px {sc}33;'>{overall_success:.1f}%</div>
            <div class='sa-kpi-sub'>Overall hit rate</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Profit Factor</div>
            <div class='sa-kpi-value' style='color:{pf_col};text-shadow:0 0 18px {pf_col}33;'>{pf_overall:.2f}</div>
            <div class='sa-kpi-sub'>Gross W / Gross L</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Expectancy</div>
            <div class='sa-kpi-value' style='color:{exp_col};text-shadow:0 0 18px {exp_col}33;'>{expectancy_all:+.2f}%</div>
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
        "RSI":   ("RSI (14)",               "Momentum",            None),
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
            # All indicator cards
            for idx, ind in enumerate(indicator_performance):
                accent   = card_accents[idx % len(card_accents)]
                br_color = regime_color_map.get(ind["best_regime"], accent)
                win_pct  = ind["win_rate"]
                loss_pct = 100 - win_pct
                total    = ind["total"]
                wins     = ind["win_count"]
                losses   = total - wins
                gain_col = BULL if ind["avg_gain"] >= 1 else NEUT if ind["avg_gain"] > 0 else BEAR
                loss_col = BEAR if ind["avg_loss"] < -1 else NEUT

                # Tooltip hints for individual indicator stat cells
                _ind_tips = {
                    "Signals":     "Total number of times this indicator triggered a signal",
                    "Wins":        "Number of signals that ended in a profitable trade",
                    "Losses":      "Number of signals that resulted in a loss",
                    "Avg Gain":    "Average profit on winning trades — higher means bigger wins",
                    "Avg Loss":    "Average loss on losing trades — closer to 0 means better risk control",
                    "Best Regime": "Market condition where this indicator performed best (Trend/Range/Volatile)",
                }
                def _sb(label, value, color, bg=None, sub=None):
                    _bg = bg or "#161616"
                    _sh = (
                        f"<div style='font-size:0.68rem;font-weight:700;color:{color};"
                        f"opacity:0.8;margin-top:0.2rem;'>{sub}</div>"
                    ) if sub else ""
                    _tip = _ind_tips.get(label, "")
                    _tip_html = (
                        f"<span title='{_tip}' style='display:inline-flex;align-items:center;justify-content:center;"
                        f"width:13px;height:13px;border-radius:50%;border:1px solid #444;"
                        f"font-size:0.45rem;color:#666;font-weight:700;margin-left:0.25rem;"
                        f"cursor:help;vertical-align:middle;'>?</span>"
                    ) if _tip else ""
                    return (
                        f"<div style='background:{_bg};border:1px solid #272727;"
                        f"border-radius:10px;padding:0.85rem 0.7rem;text-align:center;'>"
                        f"<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;"
                        f"letter-spacing:1px;font-weight:700;margin-bottom:0.35rem;'>{label}{_tip_html}</div>"
                        f"<div style='font-size:1.2rem;font-weight:900;color:{color};line-height:1;"
                        f"text-shadow:0 0 18px {color}33;'>{value}</div>"
                        f"{_sh}</div>"
                    )

                st.markdown((
                    f"<div style='background:#1b1b1b;border:1px solid #272727;"
                    f"border-radius:14px 14px 0 0;overflow:hidden;margin-bottom:0;'>"
                    f"<div style='padding:1.6rem 1.8rem;"
                    f"background:linear-gradient(135deg,{_hex_rgba(accent,.07)},transparent);'>"

                    # header row
                    f"<div style='display:flex;align-items:center;gap:1.2rem;margin-bottom:1.2rem;'>"
                    f"<div style='width:3rem;height:3rem;border-radius:50%;"
                    f"background:{accent}18;border:2px solid {accent};"
                    f"display:flex;align-items:center;justify-content:center;flex-shrink:0;'>"
                    f"<span style='font-size:1.1rem;font-weight:900;color:{accent};'>#{idx+1}</span></div>"
                    f"<div style='flex:1;'>"
                    f"<div style='font-size:1.15rem;font-weight:900;color:#e0e0e0;'>{ind['name']}</div>"
                    f"<div style='font-size:0.75rem;color:{accent};font-weight:600;"
                    f"text-transform:uppercase;letter-spacing:0.5px;margin-top:0.15rem;'>{ind['category']}</div>"
                    f"</div>"
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-size:2.6rem;font-weight:900;color:{accent};line-height:1;"
                    f"text-shadow:0 0 20px {accent}33;'>"
                    f"{win_pct:.0f}%</div>"
                    f"<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-top:0.1rem;'>Win Rate</div>"
                    f"</div></div>"

                    # win/loss bar
                    f"<div style='margin-bottom:1.2rem;'>"
                    f"<div style='display:flex;border-radius:6px;overflow:hidden;"
                    f"height:7px;background:#1a1a1a;margin-bottom:0.4rem;'>"
                    f"<div style='width:{win_pct:.1f}%;background:{accent};"
                    f"box-shadow:0 0 8px {accent}55;'></div>"
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
                    + _sb("Signals",    str(total),               "#e0e0e0")
                    + _sb("Wins",       str(wins),                BULL, _hex_rgba(BULL,.08), f"{win_pct:.0f}%")
                    + _sb("Losses",     str(losses),              BEAR, _hex_rgba(BEAR,.08), f"{loss_pct:.0f}%")
                    + _sb("Avg Gain",   f"+{ind['avg_gain']:.2f}%", gain_col, _hex_rgba(BULL,.06))
                    + _sb("Avg Loss",   f"{ind['avg_loss']:.2f}%",  loss_col, _hex_rgba(BEAR,.06))
                    + _sb("Best Regime", ind["best_regime"] or "\u2014", br_color, _hex_rgba(br_color,.10))
                    + "</div></div></div>"
                ), unsafe_allow_html=True)


                with st.container(key=f"ind_save_wrap_{idx}_{ind['key']}"):
                    render_save_indicator_button(idx, ind, risk_val, reward_val, _period_label)

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
        fc1, = st.columns([1])
        with fc1:
            st.markdown(
                "<div style='font-size:0.62rem;color:#606060;text-transform:uppercase;"
                "letter-spacing:1px;font-weight:700;margin-bottom:0.3rem;'>Combo Size Filter</div>",
                unsafe_allow_html=True)
            _size_opts = ["All sizes", "2-Way only", "3-Way only", "4-Way only", "5-Way only", "6-Way only"]
            _cc_size = st.selectbox("Size filter", _size_opts, index=0, key="cc_size_filt",
                                    label_visibility="collapsed")
        _sort_key = "win_rate"
        _cc_top_per_group = 5

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
                if wr >= 100:
                    continue
                regime_perf_raw = cd.get("regime_performance", {})
                regime_totals = cd.get("regime_totals", {})
                rp = {r: regime_perf_raw.get(r, 0) for r in regime_perf_raw if regime_totals.get(r, 0) > 0}
                best_r = max(rp, key=rp.get) if rp else ""
                all_combo_data.append({
                    "key":          combo_key,
                    "indicators":   parts,
                    "size":         size,
                    "label":        " + ".join(_all_names.get(p, p) for p in parts),
                    "total":        n_c,
                    "active_bars":  cd.get("active_bars", n_c),
                    "regime_totals": regime_totals,
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
                    "signal_window":     cd.get("signal_window", combo_signal_window),
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
                        f"<span style='background:#1b1b1b;color:#e0e0e0;font-size:0.95rem;"
                        f"font-weight:600;padding:0.25rem 0.75rem;border-radius:6px;"
                        f"border:1px solid #272727;white-space:nowrap;'>{name}</span>"
                    )
                    if idx < len(parts) - 1:
                        html += "<span style='color:#555;padding:0 0.2rem;font-size:0.9rem;'>&middot;</span>"
                return html

            def _wr_color(wr):
                if wr >= 65: return ("#1b5e20", "#81c784")
                if wr >= 55: return ("#2e7d32", "#a5d6a7")
                if wr >= 45: return ("#0d47a1", "#90caf9")
                if wr >= 35: return ("#b71c1c", "#ef9a9a")
                return ("#282828", "#606060")

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

            _regime_meta = {
                "TREND": {
                    "accent": INFO,
                    "label": "Trend",
                    "summary": "Use these combinations when price is moving cleanly in one direction and confirmation stays aligned.",
                },
                "RANGE": {
                    "accent": NEUT,
                    "label": "Range",
                    "summary": "Use these combinations when price is rotating between support and resistance instead of trending.",
                },
                "VOLATILE": {
                    "accent": BEAR,
                    "label": "Volatile",
                    "summary": "Use these combinations when price is expanding quickly and clean signals need faster confirmation.",
                },
            }

            def _count_by(values):
                counts = {}
                for value in values:
                    counts[value] = counts.get(value, 0) + 1
                return counts

            def _combo_synergy(parts):
                cats = [_ind_cat(part) for part in parts]
                counts = _count_by(cats)
                ordered = [name for name, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
                primary = ordered[0] if ordered else "Other"
                secondary = ordered[1] if len(ordered) > 1 else ""
                pair_story = {
                    ("Trend", "Momentum"): "Trend direction is reinforced by momentum timing.",
                    ("Trend", "Volume"): "Trend direction is backed by volume confirmation.",
                    ("Trend", "Volatility"): "Directional bias is paired with breakout confirmation.",
                    ("Momentum", "Volatility"): "Momentum entries are filtered by expansion moves.",
                    ("Momentum", "Volume"): "Timing signals are supported by volume flow.",
                    ("Volatility", "Volume"): "Breakout pressure is confirmed by participation.",
                }
                if secondary:
                    return (
                        pair_story.get((primary, secondary))
                        or pair_story.get((secondary, primary))
                        or f"{primary} signals are reinforced by {secondary.lower()} confirmation."
                    )
                return f"{primary} signals carry most of the edge in this setup."

            def _regime_reasons(row, regime):
                regime_wr = row["regime_perf"].get(regime, 0)
                overall_wr = row["win_rate"]
                edge = regime_wr - overall_wr
                signal_count = row["total"]
                active_bars = row.get("active_bars", signal_count)
                expectancy = row["expectancy"]
                profit_factor = row["profit_factor"]
                monthly_points = len(row.get("monthly_win_rates", {}))
                consistency = row.get("consistency", 0)
                reasons = []

                if edge >= 8:
                    reasons.append(
                        f"{regime} win rate is {edge:.1f} pts above the {overall_wr:.1f}% overall baseline."
                    )
                elif edge >= 3:
                    reasons.append(
                        f"It improves from {overall_wr:.1f}% overall to {regime_wr:.1f}% in {regime.lower()} conditions."
                    )
                else:
                    reasons.append(
                        f"It still holds {regime_wr:.1f}% in {regime.lower()} conditions with {overall_wr:.1f}% overall win."
                    )

                if signal_count >= 20:
                    reasons.append(f"{signal_count} entries gives it a deeper sample than most niche combinations.")
                elif signal_count >= 10:
                    reasons.append(f"{signal_count} entries keeps it actionable without being too sparse.")
                else:
                    reasons.append(f"Only {signal_count} entries, so this is a selective setup rather than a frequent one.")

                if active_bars > signal_count:
                    reasons.append(
                        f"The combo stayed aligned for {active_bars} bars, but continuous overlap is compressed into {signal_count} distinct trade entries."
                    )

                if profit_factor >= 1.5 and expectancy > 0:
                    reasons.append(
                        f"Profit factor {profit_factor:.2f} and expectancy {expectancy:+.2f}% show the winners are carrying the edge."
                    )
                elif expectancy > 0:
                    reasons.append(f"Positive expectancy {expectancy:+.2f}% keeps the edge net positive over time.")
                else:
                    reasons.append(f"Expectancy is {expectancy:+.2f}%, so it needs tighter confirmation despite the hit rate.")

                if monthly_points > 1 and consistency <= 12:
                    reasons.append("Its monthly results have been relatively stable instead of depending on one hot streak.")

                return reasons[:3]

            def _regime_story(row, regime):
                regime_wr = row["regime_perf"].get(regime, 0)
                return (
                    f"{_combo_synergy(row['indicators'])} "
                    f"In {regime.lower()} conditions it wins {regime_wr:.1f}% "
                    f"across {row['total']} entries and {row.get('active_bars', row['total'])} active bars."
                )

            def _regime_sort_key(row, regime, rank_mode):
                regime_wr = row["regime_perf"].get(regime, 0)
                if rank_mode == "Highest overall win":
                    return (row["win_rate"], regime_wr, row["total"], row["profit_factor"], row["expectancy"])
                if rank_mode == "Most signals":
                    return (row["total"], regime_wr, row["win_rate"], row["profit_factor"], row["expectancy"])
                return (regime_wr, row["win_rate"], row["total"], row["profit_factor"], row["expectancy"])

            def _rc_metric(label, value, color, sub=""):
                sub_html = (
                    f"<div style='font-size:0.62rem;color:{muted};margin-top:0.2rem;font-weight:600;'>{sub}</div>"
                    if sub else ""
                )
                return (
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-radius:10px;padding:0.75rem 0.7rem;text-align:center;'>"
                    f"<div style='font-size:0.58rem;color:{muted};text-transform:uppercase;"
                    f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.35rem;'>{label}</div>"
                    f"<div style='font-size:1.2rem;font-weight:900;color:{color};line-height:1;'>{value}</div>"
                    f"{sub_html}</div>"
                )

            def _regime_reason_html(row, regime):
                accent = _regime_meta[regime]["accent"]
                items = []
                for reason in _regime_reasons(row, regime):
                    items.append(
                        f"<div style='display:flex;align-items:flex-start;gap:0.45rem;margin-bottom:0.4rem;'>"
                        f"<span style='display:inline-block;width:7px;height:7px;border-radius:50%;"
                        f"background:{accent};margin-top:0.35rem;flex-shrink:0;'></span>"
                        f"<span style='font-size:0.74rem;color:{text_col};line-height:1.55;'>{reason}</span>"
                        f"</div>"
                    )
                return "".join(items)

            def _regime_bars_html(row, selected_regime):
                bars = []
                for regime_key in ("TREND", "RANGE", "VOLATILE"):
                    value = row["regime_perf"].get(regime_key, 0)
                    accent = _regime_meta[regime_key]["accent"]
                    label_color = accent if regime_key == selected_regime else muted
                    bars.append(
                        f"<div style='margin-bottom:0.48rem;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.16rem;'>"
                        f"<span style='font-size:0.62rem;color:{label_color};font-weight:800;"
                        f"letter-spacing:0.5px;text-transform:uppercase;'>{regime_key}</span>"
                        f"<span style='font-size:0.72rem;font-weight:800;color:{accent};'>{value:.1f}%</span>"
                        f"</div>"
                        f"<div style='height:6px;background:{panel};border-radius:999px;overflow:hidden;'>"
                        f"<div style='height:6px;width:{min(100, max(value, 0)):.1f}%;background:{accent};"
                        f"box-shadow:0 0 10px {accent}44;'></div>"
                        f"</div></div>"
                    )
                return "".join(bars)

            # ── Stat mini-cell used inside combo cards ─────────────────────────
            # Tooltip descriptions for every stat label
            _stat_tips = {
                "Signals":       "Total number of times this combination triggered in the backtest period",
                "Winners":       "Trades that hit your profit target — more is better",
                "Losers":        "Trades that got stopped out or ran out of time",
                "Avg Gain":      "When you win, how much you make on average",
                "Avg Loss":      "When you lose, how much you lose on average",
                "Avg Hold":      "How many days a trade is usually held before closing",
                "Profit Factor": "Total money made ÷ total money lost. Above 1 = profitable. Above 2 = very good",
                "Expectancy":    "Average profit per trade. Positive = making money over time",
                "Signals/100":   "How often this combo gives a signal per 100 trading days",
            }
            def _st(lbl, val, col):
                _tip = _stat_tips.get(lbl, "")
                _tip_html = (
                    f"<span title='{_tip}' style='display:inline-flex;align-items:center;justify-content:center;"
                    f"width:13px;height:13px;border-radius:50%;border:1px solid #444;"
                    f"font-size:0.45rem;color:#666;font-weight:700;margin-left:0.25rem;"
                    f"cursor:help;vertical-align:middle;'>?</span>"
                ) if _tip else ""
                return (
                    f"<div style='background:#161616;border:1px solid #272727;"
                    f"border-radius:8px;padding:0.8rem 0.4rem;text-align:center;'>"
                    f"<div style='font-size:0.75rem;color:#606060;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.35rem;font-weight:600;'>{lbl}{_tip_html}</div>"
                    f"<div style='font-size:1.15rem;font-weight:800;color:{col};line-height:1;"
                    f"text-shadow:0 0 18px {col}33;'>{val}</div>"
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
                sf   = row.get("signal_freq", 0)

                # Regime bars HTML
                bars = ""
                for reg, pct in rp.items():
                    rc = regime_color_map.get(reg, "#888")
                    bw = min(100, max(0, pct))
                    bars += (
                        f"<div style='margin-bottom:0.4rem;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.15rem;'>"
                        f"<span style='font-size:0.65rem;color:#606060;font-weight:700;text-transform:uppercase;'>{reg}</span>"
                        f"<span style='font-size:0.72rem;font-weight:800;color:{rc};'>{pct:.0f}%</span></div>"
                        f"<div style='background:#272727;border-radius:3px;height:4px;'>"
                        f"<div style='background:{rc};border-radius:3px;height:4px;width:{bw:.0f}%;'></div>"
                        f"</div></div>"
                    )

                st.markdown((
                    f"<div style='background:#1b1b1b;border:1px solid #272727;"
                    f"border-radius:12px 12px 0 0;overflow:hidden;margin-bottom:0;'>"
                    f"<div style='padding:1.1rem 1.25rem;"
                    f"background:linear-gradient(135deg,{_hex_rgba(_wr_col,.06)},transparent);'>"

                    # Header row
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.7rem;'>"
                    f"<div style='flex:1;min-width:0;'>"
                    f"<div style='font-size:0.75rem;color:#606060;font-weight:600;text-transform:uppercase;"
                    f"letter-spacing:0.8px;margin-bottom:0.35rem;'>{rank_label} &middot; {row['size']}-Way Combination</div>"
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.25rem;margin-bottom:0.28rem;'>"
                    f"{_badges(row['indicators'])}</div>"
                    f"<div style='font-size:0.75rem;color:#606060;'>Best in: "
                    f"<span style='color:{br_c};font-weight:700;'>{_br_label}</span></div>"
                    f"</div>"
                    f"<div style='text-align:right;flex-shrink:0;margin-left:0.8rem;'>"
                    f"<div style='font-size:2.4rem;font-weight:800;color:{_wr_col};line-height:1;'>"
                    f"{wr:.1f}<span style='font-size:1rem;'>%</span></div>"
                    f"<div style='font-size:0.75rem;color:#606060;letter-spacing:0.3px;'>"
                    f"win rate &middot; {n_c} signals</div>"
                    f"</div></div>"

                    # Win/loss bar
                    f"<div style='display:flex;border-radius:4px;overflow:hidden;height:5px;background:#1a1a1a;margin-bottom:0.22rem;'>"
                    f"<div style='width:{wr:.1f}%;background:{BULL};box-shadow:0 0 6px {BULL}44;'></div>"
                    f"<div style='width:{lp:.1f}%;background:{BEAR};'></div></div>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:0.8rem;'>"
                    f"<span style='font-size:0.75rem;color:{BULL};font-weight:700;'>{row['wins']} wins ({wr:.1f}%)</span>"
                    f"<span style='font-size:0.75rem;color:{BEAR};font-weight:700;'>{row['losses']} losses ({lp:.1f}%)</span></div>"

                    # Stats grid
                    f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:0.28rem;margin-bottom:0.65rem;'>"
                    + _st("Signals",       str(n_c),                                 "#e0e0e0")
                    + _st("Winners",       str(row["wins"]),                          BULL)
                    + _st("Losers",        str(row["losses"]),                        BEAR)
                    + _st("Avg Gain",      f"+{row['avg_gain']:.2f}%",               BULL)
                    + _st("Avg Loss",      f"{row['avg_loss']:.2f}%",                BEAR)
                    + _st("Avg Hold",      f"{row['avg_hold']:.0f}d",                INFO)
                    + _st("Profit Factor", f"{row['profit_factor']:.2f}",             BULL if row['profit_factor'] >= 1.5 else NEUT)
                    + _st("Expectancy",    f"{row['expectancy']:+.2f}%",              BULL if row['expectancy'] > 0 else BEAR)
                    + _st("Signals/100",   f"{sf:.1f}",                              INFO)
                    + "</div>"

                    # Bottom: regime bars
                    f"<div style='background:#161616;border:1px solid #272727;border-radius:8px;padding:0.65rem 0.75rem;'>"
                    f"<div style='font-size:0.75rem;color:#606060;font-weight:600;text-transform:uppercase;"
                    f"letter-spacing:0.7px;margin-bottom:0.45rem;'>Win Rate by Regime"
                    f"<span title='How well this combo performed in each market condition — Trending, Sideways, or Volatile. "
                    f"Higher bar = better performance in that condition.' "
                    f"style='display:inline-flex;align-items:center;justify-content:center;"
                    f"width:13px;height:13px;border-radius:50%;border:1px solid #444;"
                    f"font-size:0.45rem;color:#666;font-weight:700;margin-left:0.25rem;"
                    f"cursor:help;vertical-align:middle;'>?</span></div>"
                    + bars +
                    "</div></div></div>"
                ), unsafe_allow_html=True)
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
                    f"letter-spacing:0.7px;margin-bottom:0.4rem;'>How it works</div>"
                    f"<div style='font-size:0.78rem;color:#e0e0e0;margin-bottom:0.3rem;line-height:1.5;'>"
                    f"You have <strong style='color:#fff;'>{_n_inds} indicators</strong> turned on with "
                    f"Combo Depth set to <strong style='color:#fff;'>{max_combo_depth}</strong>. "
                    f"We tested every possible combination of those indicators to see which ones work best together.</div>"
                    f"<div style='font-size:0.72rem;color:#90caf9;margin-bottom:0.35rem;line-height:1.55;'>"
                    "A combo starts when the indicators are bullish together in the same overlap stretch, instead of forcing every indicator to flip on the exact same day.</div>"
                    f"<div style='font-size:0.74rem;color:#90caf9;font-weight:600;margin-bottom:0.4rem;line-height:1.8;'>"
                    f"{_breakdown_str}</div>"
                    f"<div style='font-size:0.72rem;color:#606060;margin-bottom:0.25rem;'>"
                    f"That's <strong style='color:#fff;'>{_theory_total:,} combinations</strong> tested in total.</div>"
                    f"<div style='font-size:0.72rem;color:#606060;margin-bottom:0.65rem;'>"
                    f"Out of those, <strong style='color:#4caf50;'>{total_combos:,} combinations</strong> actually "
                    f"had enough trades to be meaningful. The rest had too few signals to be useful.</div>"
                    f"<div style='border-top:1px solid rgba(33,150,243,0.18);padding-top:0.6rem;'>"
                    f"<div style='font-size:0.6rem;font-weight:800;color:#90caf9;text-transform:uppercase;"
                    f"letter-spacing:0.7px;margin-bottom:0.45rem;'>How trades are simulated</div>"
                    f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:0.5rem;margin-bottom:0.5rem;'>"
                    f"<div style='background:rgba(239,83,80,0.08);border:1px solid rgba(239,83,80,0.2);"
                    f"border-radius:7px;padding:0.45rem 0.5rem;text-align:center;'>"
                    f"<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;letter-spacing:0.5px;"
                    f"margin-bottom:0.2rem;'>Stop Loss</div>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:#ef5350;line-height:1;'>2%</div>"
                    f"<div style='font-size:0.62rem;color:#606060;margin-top:0.15rem;'>if price drops 2%, sell</div>"
                    f"</div>"
                    f"<div style='background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);"
                    f"border-radius:7px;padding:0.45rem 0.5rem;text-align:center;'>"
                    f"<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;letter-spacing:0.5px;"
                    f"margin-bottom:0.2rem;'>Profit Target</div>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:#4caf50;line-height:1;'>{profit_target*100:.0f}%</div>"
                    f"<div style='font-size:0.62rem;color:#606060;margin-top:0.15rem;'>if price goes up {profit_target*100:.0f}%, sell</div>"
                    f"</div>"
                    f"<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.2);"
                    f"border-radius:7px;padding:0.45rem 0.5rem;text-align:center;'>"
                    f"<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;letter-spacing:0.5px;"
                    f"margin-bottom:0.2rem;'>Max Hold</div>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:#2196f3;line-height:1;'>{holding_period}d</div>"
                    f"<div style='font-size:0.62rem;color:#606060;margin-top:0.15rem;'>sell after {holding_period} days max</div>"
                    f"</div>"
                    f"</div>"
                    f"<div style='font-size:0.71rem;color:#606060;line-height:1.6;'>"
                    f"When indicators say 'buy', we pretend to buy the next day. "
                    f"<span style='color:#4caf50;font-weight:700;'>WIN</span> = price went up {profit_target*100:.0f}% before anything bad happened. "
                    f"<span style='color:#ef5350;font-weight:700;'>LOSS</span> = price dropped 2% first, "
                    f"or {holding_period} days passed and nothing happened so we just sold.</div>"
                    f"</div>"
                    f"</div>"
                )
                insight_toggle(
                    "combo_leaderboard",
                    "What is the Leaderboard? (tap to learn)",
                    _combo_math_html
                )

                # Champion banner
                champ     = all_combo_data[0]
                champ_wr  = champ["win_rate"]
                champ_ea  = champ["expectancy"]
                champ_pf  = champ.get("profit_factor", 0)
                champ_lp  = 100 - champ_wr
                ea_col    = "#81c784" if champ_ea > 0 else BEAR
                pf_col    = "#81c784" if champ_pf >= 1.5 else "#ffb74d"
                _pf_tag   = "Very Strong" if champ_pf >= 2 else ("Strong" if champ_pf >= 1.5 else ("Decent" if champ_pf >= 1 else "Losing"))
                _ea_tag   = "Positive edge" if champ_ea > 0 else "Negative edge"
                _, _champ_wr_col = _wr_color(champ_wr)
                _champ_br      = champ["best_regime"] or "N/A"
                _champ_br_col  = regime_color_map.get(champ["best_regime"], GOLD)
                _champ_br_pct  = champ["regime_perf"].get(champ["best_regime"], 0)

                st.markdown(
                    # champion banner
                    f"<div style='background:#1b1b1b;border:1px solid #272727;"
                    f"border-radius:14px 14px 0 0;overflow:hidden;margin-bottom:0;'>"
                    f"<div style='padding:1.5rem 1.6rem 1.3rem 1.6rem;"
                    f"background:linear-gradient(135deg,rgba(255,215,0,0.04),transparent);'>"

                    # top row: crown badge + label + best regime pill
                    f"<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:1rem;'>"
                    f"<div style='font-size:1.5rem;line-height:1;'>&#127942;</div>"
                    f"<div style='flex:1;'>"
                    f"<div style='font-size:0.72rem;color:#606060;font-weight:700;margin-bottom:0.35rem;'>Best Combination Overall</div>"
                    f"<div style='font-size:0.7rem;color:#606060;margin-top:0.1rem;'>"
                    f"#{1} of {total_combos:,} &nbsp;&middot;&nbsp; {champ['size']}-Way</div>"
                    f"</div>"
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.22rem;'>Best Regime</div>"
                    f"<div style='display:inline-flex;align-items:center;gap:0.4rem;"
                    f"background:{_champ_br_col}18;border:1px solid {_champ_br_col}44;"
                    f"border-radius:7px;padding:0.3rem 0.9rem;'>"
                    f"<span style='font-size:0.82rem;font-weight:800;color:{_champ_br_col};'>{_champ_br}</span>"
                    f"<span style='font-size:0.75rem;font-weight:600;color:{_champ_br_col};'>&mdash;&nbsp;{_champ_br_pct:.0f}%</span>"
                    f"</div></div>"
                    f"</div>"

                    # indicator badges row
                    f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.3rem;margin-bottom:1.1rem;'>"
                    f"{_badges(champ['indicators'])}</div>"

                    # big win rate + win/loss bar + secondary stats split
                    f"<div style='display:grid;grid-template-columns:auto 1fr;gap:1.5rem;align-items:center;margin-bottom:1rem;'>"

                    # left: giant win rate
                    f"<div style='text-align:center;padding:0.9rem 1.2rem;"
                    f"background:#161616;border:1px solid #272727;"
                    f"border-radius:10px;min-width:120px;'>"
                    f"<div style='font-size:0.62rem;font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:1px;color:#606060;margin-bottom:0.3rem;'>Win Rate</div>"
                    f"<div style='font-size:3rem;font-weight:900;color:{_champ_wr_col};line-height:1;"
                    f"letter-spacing:-2px;text-shadow:0 0 20px {_champ_wr_col}33;'>{champ_wr:.1f}<span style='font-size:1.4rem;'>%</span></div>"
                    f"<div style='font-size:0.62rem;color:#606060;margin-top:0.25rem;'>"
                    f"{champ['wins']}W / {champ['losses']}L</div>"
                    f"</div>"

                    # right: win/loss bar + 5 stat pills
                    f"<div>"
                    f"<div style='display:flex;border-radius:5px;overflow:hidden;height:8px;background:#1a1a1a;margin-bottom:0.35rem;'>"
                    f"<div style='width:{champ_wr:.1f}%;background:linear-gradient(90deg,#43a047,#66bb6a);"
                    f"box-shadow:0 0 8px {BULL}55;'></div>"
                    f"<div style='width:{champ_lp:.1f}%;background:linear-gradient(90deg,#e53935,#ef5350);'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;margin-bottom:0.2rem;'>"
                    f"<span style='font-size:0.78rem;color:{BULL};font-weight:700;'>{champ['wins']} wins ({champ_wr:.1f}%)</span>"
                    f"<span style='font-size:0.78rem;color:{BEAR};font-weight:700;'>{champ['losses']} losses ({champ_lp:.1f}%)</span>"
                    f"</div>"

                    # inline stat row (replaces 5 boxes)
                    f"<div style='display:flex;align-items:center;justify-content:space-between;"
                    f"margin-top:0.6rem;padding:0.55rem 0.8rem;"
                    f"background:#161616;border:1px solid #272727;border-radius:10px;'>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:0.95rem;font-weight:800;color:#90caf9;'>{champ['total']}</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;'>Signals</div></div>"
                    f"<div style='width:1px;height:24px;background:#272727;'></div>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:0.95rem;font-weight:800;color:{ea_col};'>{champ_ea:+.2f}%</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;'>Expectancy</div></div>"
                    f"<div style='width:1px;height:24px;background:#272727;'></div>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:0.95rem;font-weight:800;color:{pf_col};'>{champ_pf:.2f}</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;'>Profit Factor</div></div>"
                    f"<div style='width:1px;height:24px;background:#272727;'></div>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:0.95rem;font-weight:800;color:#e0e0e0;'>{champ['size']}-Way</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;'>Size</div></div>"
                    f"</div>"

                    f"</div></div></div>"  # end right col, 2-col grid
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                with st.container(key="combo_save_wrap_champ"):
                    render_save_combo_button(
                        0, champ, _all_names, risk_val, reward_val, _period_label,
                        combo_signal_window,
                    )

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
                        "Sig/100 Bars":   round(_tr.get("signal_freq", 0), 1),
                        "Best Regime":    _tr["best_regime"] or "--",
                    })
                _tbl_df = pd.DataFrame(_tbl_rows).set_index("Rank")

                # Column glossary — explains every metric in the table
                insight_toggle(
                    "combo_table_glossary",
                    "What does each column mean? (tap to read)",
                    "<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 1.5rem;'>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Combination</strong> — Which indicators were all saying 'buy' at the same time.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Size</strong> — How many indicators agreed together. 2-Way = 2 agreed, 3-Way = 3 agreed, etc.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Signals</strong> — How many times this combo triggered a buy signal during the test period.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Wins / Losses</strong> — How many trades made money vs lost money.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Win %</strong> — What percentage of trades made money. Above 50% = winning more than losing.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Avg Gain %</strong> — When a trade wins, how much does it make on average.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Avg Loss %</strong> — When a trade loses, how much does it lose on average.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Profit Factor</strong> — Total money made ÷ total money lost. Above 1 = profitable. Above 2 = very good.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Expectancy %</strong> — On average, how much you make or lose per trade. Positive = making money.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Sig/100 Bars</strong> — How often this combo gives a signal per 100 trading days. Higher = more trade chances.</div></div>"

                    "<div class='itog-row'><div class='itog-dot'></div>"
                    "<div><strong>Best Regime</strong> — Which market condition (Trending, Sideways, or Volatile) this combo works best in.</div></div>"

                    "</div>"
                )

                st.markdown(
                    f"<div style='font-size:0.75rem;color:#606060;margin-bottom:0.35rem;font-weight:600;'>"
                    f"Click any column header to sort &nbsp;&bull;&nbsp; {total_combos:,} combinations:</div>",
                    unsafe_allow_html=True,
                )
                st.dataframe(_tbl_df, use_container_width=True, height=500)

            # ── Regime Champions ──────────────────────────────────────────────
            with ctab2:
                def _tip_icon(text):
                    _safe = str(text).replace("'", "&#39;").replace('"', '&quot;')
                    return (
                        f"<span title='{_safe}' style='display:inline-flex;align-items:center;justify-content:center;"
                        f"width:13px;height:13px;border-radius:50%;border:1px solid #444;"
                        f"font-size:0.45rem;color:#666;font-weight:700;margin-left:0.25rem;"
                        f"cursor:help;vertical-align:middle;'>?</span>"
                    )

                def _focus_metric(label, value, color, sub="", tip=""):
                    _tip_html = _tip_icon(tip) if tip else ""
                    _sub_html = (
                        f"<div style='font-size:0.62rem;color:{muted};margin-top:0.22rem;font-weight:600;'>{sub}</div>"
                        if sub else ""
                    )
                    return (
                        f"<div style='background:{panel_alt};border:1px solid {border};"
                        f"border-radius:10px;padding:0.75rem 0.7rem;text-align:center;'>"
                        f"<div style='font-size:0.58rem;color:{muted};text-transform:uppercase;"
                        f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.35rem;'>{label}{_tip_html}</div>"
                        f"<div style='font-size:1.16rem;font-weight:900;color:{color};line-height:1;'>{value}</div>"
                        f"{_sub_html}</div>"
                    )

                def _sample_band(row):
                    _total = row["total"]
                    if _total >= 25:
                        return ("Deep sample", INFO)
                    if _total >= 15:
                        return ("Strong sample", BULL)
                    if _total >= 8:
                        return ("Usable sample", NEUT)
                    return ("Thin sample", BEAR)

                def _quality_allows(row, lens):
                    if lens == "All setups":
                        return True
                    if lens == "Balanced":
                        return row["total"] >= 8 and row["expectancy"] >= 0
                    if lens == "Higher sample":
                        return row["total"] >= 15
                    return row["signal_freq"] >= 2.0 and row["total"] >= 6

                def _focus_sort_key(row, sort_mode):
                    if sort_mode == "Most Signals":
                        return (row["total"], row["signal_freq"], row["win_rate"], row["profit_factor"])
                    if sort_mode == "Profit Factor":
                        return (row["profit_factor"], row["win_rate"], row["total"], row["expectancy"])
                    return (row["win_rate"], row["total"], row["profit_factor"], row["expectancy"])

                def _render_focus_card(row, rank, focus_regime, hero=False, save_idx=None):
                    _meta = _regime_meta[focus_regime]
                    _accent = _meta["accent"]
                    _label = _meta["label"]
                    _sample_label, _sample_color = _sample_band(row)
                    _wr_col = BULL if row["win_rate"] >= 55 else NEUT if row["win_rate"] >= 45 else BEAR
                    _pf_col = BULL if row["profit_factor"] >= 1.3 else NEUT if row["profit_factor"] >= 1 else BEAR
                    _exp_col = BULL if row["expectancy"] > 0 else BEAR
                    _card_radius = "16px" if hero else "14px"
                    _card_pad = "1.25rem 1.35rem" if hero else "0.95rem 1.1rem"
                    _title = f"Top {_label} setup" if hero else f"#{rank}"
                    st.markdown(
                        (
                            f"<div style='background:{panel};border:1px solid {border};border-radius:{_card_radius};"
                            f"overflow:hidden;margin-bottom:0;'>"
                            f"<div style='padding:{_card_pad};"
                            f"background:linear-gradient(135deg,{_hex_rgba(_accent, .09 if hero else .05)},transparent);'>"
                            f"<div style='display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;margin-bottom:0.8rem;'>"
                            f"<div style='flex:1;min-width:280px;'>"
                            f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.35rem;margin-bottom:0.45rem;'>"
                            f"<span style='font-size:0.66rem;color:{_accent};font-weight:800;text-transform:uppercase;"
                            f"letter-spacing:0.8px;padding:0.18rem 0.55rem;border-radius:999px;"
                            f"background:{_accent}14;border:1px solid {_accent}33;'>{_title}</span>"
                            f"<span style='font-size:0.64rem;color:{_sample_color};font-weight:800;text-transform:uppercase;"
                            f"letter-spacing:0.7px;padding:0.18rem 0.55rem;border-radius:999px;"
                            f"background:{_sample_color}14;border:1px solid {_sample_color}33;'>{_sample_label}</span>"
                            f"<span style='font-size:0.64rem;color:{INFO};font-weight:800;text-transform:uppercase;"
                            f"letter-spacing:0.7px;padding:0.18rem 0.55rem;border-radius:999px;"
                            f"background:{INFO}14;border:1px solid {INFO}33;'>{row['size']}-Way</span>"
                            f"<span style='font-size:0.64rem;color:{_accent};font-weight:800;text-transform:uppercase;"
                            f"letter-spacing:0.7px;padding:0.18rem 0.55rem;border-radius:999px;"
                            f"background:{_accent}14;border:1px solid {_accent}33;'>Best in {_label}</span>"
                            f"</div>"
                            f"<div style='font-size:{'1.16rem' if hero else '1.0rem'};font-weight:900;color:{text_col};margin-bottom:0.42rem;'>"
                            f"{row['label']}</div>"
                            f"</div>"
                            f"<div style='text-align:right;min-width:150px;'>"
                            f"<div style='font-size:0.58rem;color:{muted};text-transform:uppercase;letter-spacing:0.7px;'>"
                            f"Overall Win{_tip_icon('How often this setup wins across the full test, not only inside one regime.')}</div>"
                            f"<div style='font-size:{'3rem' if hero else '2.2rem'};font-weight:900;color:{_wr_col};line-height:1;"
                            f"text-shadow:0 0 18px {_wr_col}33;'>{row['win_rate']:.1f}%</div>"
                            f"<div style='font-size:0.72rem;color:{muted};margin-top:0.18rem;font-weight:600;'>"
                            f"{row['wins']} winners · {row['losses']} losers</div>"
                            f"</div></div>"
                            f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.4rem;margin-bottom:0.65rem;'>"
                            f"{_focus_metric('Entries', str(row['total']), INFO, f'{row['signal_freq']:.1f}/100 bars', 'How many distinct trade entries this setup produced in the full test.') }"
                            f"{_focus_metric('Winners', str(row['wins']), BULL, tip='How many of those entries finished positive.') }"
                            f"{_focus_metric('Losers', str(row['losses']), BEAR, tip='How many of those entries finished negative.') }"
                            f"{_focus_metric('Profit Factor', f'{row['profit_factor']:.2f}', _pf_col, tip='Total gains divided by total losses. Above 1.0 means the setup made more than it lost.') }"
                            f"{_focus_metric('Expectancy', f'{row['expectancy']:+.2f}%', _exp_col, tip='Average edge per trade after wins and losses are blended together.') }"
                            f"</div>"
                            f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:0.4rem;'>"
                            f"{_focus_metric('Avg Hold', f'{row['avg_hold']:.0f}d', INFO, tip='How long trades stayed open on average before they closed.') }"
                            f"{_focus_metric('Avg Gain', f'+{row['avg_gain']:.2f}%', BULL, tip='Average size of the winning trades.') }"
                            f"{_focus_metric('Avg Loss', f'{row['avg_loss']:.2f}%', BEAR, tip='Average size of the losing trades.') }"
                            f"</div>"
                            + "</div></div>"
                        ),
                        unsafe_allow_html=True,
                    )
                    render_save_combo_button(
                        8800 + (save_idx if save_idx is not None else rank),
                        dict(row, best_regime=focus_regime),
                        _all_names,
                        risk_val,
                        reward_val,
                        _period_label,
                        combo_signal_window,
                        regime_tag=focus_regime,
                        button_label=f"☆  Save  {_label} setup",
                    )

                insight_toggle(
                    "combo_regime",
                    "What is Regime Champions? (tap to learn)",
                    "<p>Regime Focus groups setups by the market condition where they fit best.</p>"
                    "<p>Use the tabs to jump between <strong>Trend</strong>, <strong>Range</strong>, and <strong>Volatile</strong> champions. Each tab shows the top 10 setups for that market state, ranked by overall win.</p>"
                    "<p><strong>Entries</strong> are built from active bullish overlap, not from forcing every indicator to flip on the same day.</p>"
                )

                def _render_regime_champion_section(_section_name, _regime_key, _save_offset):
                    _section_meta = _regime_meta[_regime_key]
                    _regime_combos_all = [row for row in all_combo_data if row["best_regime"] == _regime_key]
                    if not _regime_combos_all:
                        _regime_combos_all = [
                            row for row in all_combo_data if row.get("regime_totals", {}).get(_regime_key, 0) > 0
                        ]
                    _regime_combos = sorted(
                        _regime_combos_all,
                        key=lambda row: (row["win_rate"], row["total"], row["profit_factor"], row["expectancy"]),
                        reverse=True,
                    )[:10]

                    st.markdown(
                        (
                            f"<div style='display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;"
                            f"margin:0.45rem 0 0.65rem 0;flex-wrap:wrap;'>"
                            f"<div>"
                            f"<div style='font-size:0.76rem;color:{_section_meta['accent']};font-weight:900;text-transform:uppercase;letter-spacing:0.8px;'>"
                            f"{_section_name} Champions</div>"
                            f"<div style='font-size:0.76rem;color:{muted};margin-top:0.18rem;'>"
                            f"Best 10 setups in {_section_name.lower()} conditions, ranked by overall win rate</div>"
                            f"</div>"
                            f"<div style='font-size:0.72rem;color:{muted};font-weight:700;'>"
                            f"Showing {min(10, len(_regime_combos_all))} of {len(_regime_combos_all)}</div>"
                            f"</div>"
                        ),
                        unsafe_allow_html=True,
                    )

                    if not _regime_combos:
                        _regime_trade_count = sum(row.get("regime_totals", {}).get(_regime_key, 0) for row in all_combo_data)
                        _empty_msg = (
                            f"No {_section_name.lower()} entries were found in the current combo set."
                            if _regime_trade_count == 0
                            else f"No {_section_name.lower()} champion qualified on win rate, but the tab no longer hides setups just because they went 0-for-N in that regime."
                        )
                        st.markdown(
                            f"<div style='background:{panel};border:1px solid {border};border-radius:14px;padding:0.95rem 1rem;"
                            f"color:{muted};font-size:0.78rem;'>{_empty_msg}</div>",
                            unsafe_allow_html=True,
                        )
                        return

                    _champion = _regime_combos[0]
                    _render_focus_card(_champion, 1, _regime_key, hero=True, save_idx=_save_offset + 1)

                    if len(_regime_combos) > 1:
                        st.markdown(
                            f"<div style='display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.45rem 0;'>"
                            f"<span style='width:3px;height:1rem;background:{_section_meta['accent']};border-radius:2px;display:inline-block;'></span>"
                            f"<span style='font-size:0.8rem;font-weight:800;color:{_section_meta['accent']};text-transform:uppercase;letter-spacing:0.5px;'>"
                            f"More {_section_name.lower()} setups</span>"
                            f"<span style='font-size:0.62rem;color:{muted};'>Top {len(_regime_combos)} only</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption(f"Only one {_section_name.lower()} setup matched the current combo set.")

                    for _rank, _row in enumerate(_regime_combos[1:], start=2):
                        _render_focus_card(_row, _rank, _regime_key, hero=False, save_idx=_save_offset + _rank)

                _regime_sections = [
                    ("Trend", "TREND", 0),
                    ("Range", "RANGE", 100),
                    ("Volatile", "VOLATILE", 200),
                ]

                _champion_tabs = st.tabs([f"{_name} Champions" for _name, _, _ in _regime_sections])
                for _tab, (_section_name, _regime_key, _save_offset) in zip(_champion_tabs, _regime_sections):
                    with _tab:
                        _render_regime_champion_section(_section_name, _regime_key, _save_offset)

            # ── Deep Cards (continues in same Combinations tab) ────────────────────────────
            with ctab1:
                # Section header — premium
                _all_sizes = sorted(set(x["size"] for x in all_combo_data))
                _total_deep = len(all_combo_data)
                _avg_deep_wr = sum(x['win_rate'] for x in all_combo_data) / _total_deep if _total_deep else 0
                _, _adwr_col = _wr_color(_avg_deep_wr)
                st.markdown(
                    f"<div style='margin:1.5rem 0 0.5rem;padding:1rem 1.4rem;"
                    f"background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(99,102,241,0.02),transparent);"
                    f"border:1px solid rgba(99,102,241,0.18);border-radius:14px;'>"
                    f"<div style='display:flex;align-items:center;justify-content:space-between;gap:1rem;'>"
                    # left: icon + title
                    f"<div style='display:flex;align-items:center;gap:0.7rem;'>"
                    f"<div style='width:34px;height:34px;border-radius:9px;"
                    f"background:rgba(99,102,241,0.15);display:flex;align-items:center;"
                    f"justify-content:center;font-size:1rem;'>&#128269;</div>"
                    f"<div>"
                    f"<div style='font-size:0.95rem;font-weight:900;color:#e0e0e0;"
                    f"letter-spacing:0.5px;'>Deep Analysis by Combo Size</div>"
                    f"<div style='font-size:0.62rem;color:#555;margin-top:0.15rem;'>"
                    f"{_total_deep} combinations across {len(_all_sizes)} size groups</div>"
                    f"</div></div>"
                    # right: summary pills
                    f"<div style='display:flex;gap:1.2rem;align-items:center;'>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:1.05rem;font-weight:900;color:{_adwr_col};line-height:1.1;'>{_avg_deep_wr:.0f}%</div>"
                    f"<div style='font-size:0.45rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;'>Avg WR</div></div>"
                    f"<div style='width:1px;height:22px;background:#272727;'></div>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:1.05rem;font-weight:900;color:#e0e0e0;line-height:1.1;'>{len(_all_sizes)}</div>"
                    f"<div style='font-size:0.45rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;'>Sizes</div></div>"
                    f"</div></div></div>",
                    unsafe_allow_html=True,
                )
                insight_toggle(
                    "combo_deepcards",
                    "What does 2-Way / 3-Way / 4-Way mean? (tap to learn)",
                    "<h4 style='margin:0 0 0.6rem 0;color:#fff;font-size:0.9rem;'>What do these numbers mean?</h4>"
                    "<p>When we say '2-Way' or '3-Way', we mean how many indicators had to agree at the same time before we count it as a signal. "
                    "More indicators agreeing = rarer signal but usually more reliable:</p>"
                    "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem;margin:0.6rem 0;'>"
                    "<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#90caf9;'>2-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "2 indicators agreed at the same time. Happens often, gives you more trade signals.</div></div>"
                    "<div style='background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#81c784;'>3-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "3 indicators all agreed. Doesn't happen as often, but when it does it's usually a stronger signal.</div></div>"
                    "<div style='background:rgba(255,215,0,0.06);border:1px solid rgba(255,215,0,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#FFD700;'>4-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "4 indicators all said 'buy' at the same time. Pretty rare, but usually very reliable.</div></div>"
                    "<div style='background:rgba(156,39,176,0.08);border:1px solid rgba(156,39,176,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
                    "<div style='font-size:1.1rem;font-weight:900;color:#ce93d8;'>5 / 6-Way</div>"
                    "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
                    "5 or 6 indicators all agreed. Extremely rare — but when it happens, it's a very strong signal.</div></div>"
                    "</div>"
                    "<p style='margin-top:0.5rem;'><strong style='color:#FFD700;'>Simple rule:</strong> the more indicators that agree, the fewer signals you get — but each one is usually better quality.</p>"
                )

                # Size color mapping
                _sz_colors = {2: "#2196f3", 3: "#4caf50", 4: "#FFD700", 5: "#9c27b0", 6: "#f44336"}
                _sz_names = {
                    2: "2-Way Pairs", 3: "3-Way Triples", 4: "4-Way Quads",
                    5: "5-Way Quints", 6: "6-Way Combos",
                }

                # ── Premium size selector (full-width pills) ──
                _sz_emojis = {2: "🔷", 3: "🔶", 4: "💎", 5: "⭐", 6: "🏆"}
                _sz_short  = {2: "Pairs", 3: "Triples", 4: "Quads", 5: "Quints", 6: "Sextets"}

                # Precompute per-size stats
                _sz_stats = {}
                for _sv_tmp in _all_sizes:
                    _sc_tmp = [x for x in all_combo_data if x["size"] == _sv_tmp]
                    _sz_stats[_sv_tmp] = {
                        "count": len(_sc_tmp),
                        "best_wr":  _sc_tmp[0]["win_rate"]    if _sc_tmp else 0,
                        "best_exp": _sc_tmp[0]["expectancy"]  if _sc_tmp else 0,
                        "avg_wr":   sum(x["win_rate"]    for x in _sc_tmp) / len(_sc_tmp) if _sc_tmp else 0,
                        "avg_exp":  sum(x["expectancy"]  for x in _sc_tmp) / len(_sc_tmp) if _sc_tmp else 0,
                    }

                # CSS to stretch pills full-width
                st.markdown(
                    "<style>"
                    "div[data-testid='stPills'] {width:100%;}"
                    "div[data-testid='stPills'] > div {width:100%;}"
                    "div[data-testid='stPills'] > div > div {width:100%;display:flex !important;}"
                    "div[data-testid='stPills'] > div > div > button {flex:1;}"
                    "</style>",
                    unsafe_allow_html=True,
                )

                # Build pill labels
                _pill_map = {}
                for _sv_tmp in _all_sizes:
                    _lbl = f"{_sz_emojis.get(_sv_tmp, '📊')} {_sz_short.get(_sv_tmp, str(_sv_tmp))}  ({_sz_stats[_sv_tmp]['count']})"
                    _pill_map[_lbl] = _sv_tmp
                _pill_labels = list(_pill_map.keys())

                _selected_pill = st.pills(
                    "Size", _pill_labels, default=_pill_labels[0],
                    label_visibility="collapsed",
                )
                _sv = _pill_map.get(_selected_pill, _all_sizes[0])

                _sc   = [x for x in all_combo_data if x["size"] == _sv]
                _sn   = _sz_names.get(_sv, f"{_sv}-Way")
                _scol = _sz_colors.get(_sv, "#888")
                _sst  = _sz_stats[_sv]

                # Stats banner — compact row with dividers
                _, _bwr_col = _wr_color(_sst["best_wr"])
                _exp_col     = "#4caf50" if _sst["best_exp"] > 0 else "#f44336"
                _avg_exp_col = "#4caf50" if _sst["avg_exp"]  > 0 else "#f44336"
                _avg_wr_col2 = "#4caf50" if _sst["avg_wr"] >= 50 else "#f44336"
                st.markdown(
                    f"<div style='display:flex;align-items:center;justify-content:space-between;"
                    f"margin:0.3rem 0 0.9rem;padding:0.7rem 1.2rem;"
                    f"background:#161616;border:1px solid {_scol}22;border-radius:12px;"
                    f"border-top:2px solid {_scol};'>"
                    # left: emoji + name
                    f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
                    f"<span style='font-size:1.4rem;'>{_sz_emojis.get(_sv, '📊')}</span>"
                    f"<div>"
                    f"<div style='font-size:0.88rem;font-weight:900;color:{_scol};'>{_sn}</div>"
                    f"<div style='font-size:0.55rem;color:#555;'>{len(_sc)} combos analyzed</div>"
                    f"</div></div>"
                    # stats row
                    f"<div style='display:flex;align-items:center;gap:0;'>"
                    # Best WR
                    f"<div style='text-align:center;padding:0 1rem;'>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{_bwr_col};line-height:1.1;'>{_sst['best_wr']:.0f}%</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.6px;'>Best WR</div></div>"
                    f"<div style='width:1px;height:28px;background:#272727;'></div>"
                    # Avg WR
                    f"<div style='text-align:center;padding:0 1rem;'>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{_avg_wr_col2};line-height:1.1;'>{_sst['avg_wr']:.0f}%</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.6px;'>Avg WR</div></div>"
                    f"<div style='width:1px;height:28px;background:#272727;'></div>"
                    # Best Exp
                    f"<div style='text-align:center;padding:0 1rem;'>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{_exp_col};line-height:1.1;'>{_sst['best_exp']:+.2f}%</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.6px;'>Best Exp</div></div>"
                    f"<div style='width:1px;height:28px;background:#272727;'></div>"
                    # Avg Exp
                    f"<div style='text-align:center;padding:0 1rem;'>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{_avg_exp_col};line-height:1.1;'>{_sst['avg_exp']:+.2f}%</div>"
                    f"<div style='font-size:0.42rem;color:#555;text-transform:uppercase;letter-spacing:0.6px;'>Avg Exp</div></div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

                # Detail cards
                _top_n = _sc[:int(_cc_top_per_group)]
                _rest2 = _sc[int(_cc_top_per_group):]
                for _ci, _cr in enumerate(_top_n):
                    _cac4 = combo_accent_cycle[_ci % len(combo_accent_cycle)]
                    _make_combo_card(_cr, f"#{_ci + 1}", _cac4)
                    with st.container(key=f"combo_save_wrap_{_sv}_{_ci}"):
                        render_save_combo_button(
                            _ci + _sv * 100, _cr, _all_names, risk_val, reward_val, _period_label,
                            combo_signal_window,
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
                        "Signals/100":   round(_rr.get("signal_freq", 0), 1),
                        "Best Regime":   _rr["best_regime"] or "--",
                    } for _ri, _rr in enumerate(_rest2)]
                    st.markdown(
                        f"<div style='font-size:0.75rem;color:#666;font-weight:600;margin:0.8rem 0 0.3rem;'>"
                        f"📋 Remaining {len(_rest2)} {_sn} combinations:</div>",
                        unsafe_allow_html=True,
                    )
                    insight_toggle(
                        f"deep_tbl_glossary_{_sv}",
                        "What does each column mean? (tap to read)",
                        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.3rem 1.5rem;'>"
                        "<div class='itog-row'><div class='itog-dot'></div>"
                        "<div><strong>Win %</strong> — What percentage of trades made money. Above 50% = winning more than losing.</div></div>"
                        "<div class='itog-row'><div class='itog-dot'></div>"
                        "<div><strong>Avg Gain %</strong> — When a trade wins, how much does it make on average.</div></div>"
                        "<div class='itog-row'><div class='itog-dot'></div>"
                        "<div><strong>Profit Factor</strong> — Total money made ÷ total money lost. Above 1 = profitable. Above 2 = very good.</div></div>"
                        "<div class='itog-row'><div class='itog-dot'></div>"
                        "<div><strong>Expectancy %</strong> — Average profit per trade. Positive = making money.</div></div>"
                        "<div class='itog-row'><div class='itog-dot'></div>"
                        "<div><strong>Signals/100</strong> — How often this combo gives a signal per 100 trading days.</div></div>"
                        "<div class='itog-row'><div class='itog-dot'></div>"
                        "<div><strong>Best Regime</strong> — Which market condition (Trending, Sideways, or Volatile) this combo works best in.</div></div>"
                        "</div>"
                    )
                    st.dataframe(pd.DataFrame(_rest_rows2).set_index("Rank"), use_container_width=True)
