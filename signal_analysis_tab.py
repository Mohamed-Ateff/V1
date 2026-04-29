import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
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
    # flush any pending save/remove toast from last on_click
    _pending_toast = st.session_state.pop('_rc_toast', None)
    if _pending_toast:
        st.toast(_pending_toast[0], icon=_pending_toast[1])

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

    # ── Run engines (cached in session_state — reruns like Save clicks are instant) ──
    _sym      = st.session_state.get('analyzed_symbol', '')
    _last_bar = str(df.index[-1]) if len(df) > 0 else ''
    _sa_key   = (_sym, _last_bar, holding_period, max_combo_depth, risk_val, reward_val)

    if st.session_state.get('_sa_cache_key') == _sa_key:
        (signals_df, results, successful_signals, all_signal_details,
         consensus_signals, combo_results, monthly_performance) = st.session_state['_sa_cache']
    else:
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
        st.session_state['_sa_cache'] = (
            signals_df, results, successful_signals, all_signal_details,
            consensus_signals, combo_results, monthly_performance,
        )
        st.session_state['_sa_cache_key'] = _sa_key

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

    # ── Per-indicator train/test split (last 25% of monthly signals) ──────────
    def _ind_test_wr(ind_signals):
        """Approximate out-of-sample WR from most recent 25% of months."""
        if not ind_signals:
            return None
        by_month = {}
        for s in ind_signals:
            m = str(s["date"])[:7]
            by_month.setdefault(m, {"wins": 0, "total": 0})
            by_month[m]["total"] += 1
            if s["gain"] > 0:
                by_month[m]["wins"] += 1
        months = sorted(by_month.keys())
        split  = max(1, len(months) // 4)
        test_months = months[-split:]
        vals = []
        for m in test_months:
            g = by_month[m]
            if g["total"] > 0:
                vals.append(g["wins"] / g["total"] * 100)
        return float(np.mean(vals)) if vals else None

    # ── Per-indicator rank score (framework §16 adapted for single indicators) ─
    # Testing 50% + Stability 20% + Trades 15% + Role diversity 10% + Balance 5%
    def _ind_rank_score(wr, test_w, total, wins, losses):
        if test_w is None:
            test_w = wr
        gap         = abs(wr - test_w)
        bal         = 1 - abs(wins - losses) / max(wins + losses, 1)
        test_score  = min(test_w, 100) / 100 * 50
        stab_score  = max(0, 1 - gap / 50) * 20
        trade_score = min(total / 20, 1) * 15
        div_score   = 10                          # single indicator always gets full diversity credit
        bal_score   = bal * 5
        return round(test_score + stab_score + trade_score + div_score + bal_score, 1)

    # ── Broad category + logic-type label ────────────────────────────────────
    _LOGIC_TYPE = {
        "Trend":      "Trend Filter",
        "Momentum":   "Entry Timing",
        "Volume":     "Confirmation",
        "Volatility": "Risk Filter",
    }

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
    # SIGNALS SUB-TABS
    # ══════════════════════════════════════════════════════════════════════════
    _sig_main_tabs = st.tabs(["Single Indicator", "Indicator Combinations"])

    with _sig_main_tabs[0]:
        # ── indicator map: key → (name, category, role, params, chart_fn) ──────────
        indicator_map = {
            "EMA":   ("EMA (20/50/200)",       "Trend",      "Trend Filter + Entry Timing",  "20/50/200",   create_ema_chart),
            "SMA":   ("SMA (50/200)",           "Trend",      "Trend Filter",                 "50/200",      None),
            "PSAR":  ("Parabolic SAR",          "Trend",      "Trailing Stop + Reversal",     "0.02/0.2",    None),
            "ICHI":  ("Ichimoku Cloud",         "Trend",      "Trend Filter + S/R Levels",    "9/26/52",     None),
            "WMA":   ("WMA (20)",               "Trend",      "Trend Filter",                 "20",          None),
            "RSI":   ("RSI (14)",               "Momentum",   "Entry Timing + Overbought",    "14",          None),
            "MACD":  ("MACD (12/26/9)",         "Momentum",   "Entry Signal + Confirmation",  "12/26/9",     create_macd_chart),
            "STOCH": ("Stochastic (14,3,3)",    "Momentum",   "Entry Timing + Mean Reversion","14/3/3",      create_stochastic_chart),
            "ROC":   ("ROC (12)",               "Momentum",   "Momentum Confirmation",        "12",          None),
            "CCI":   ("CCI (20)",               "Momentum",   "Extreme Deviation Filter",     "20",          None),
            "WILLR": ("Williams %R (14)",       "Momentum",   "Overbought/Oversold Timing",   "14",          None),
            "BB":    ("Bollinger Bands (20,2)", "Volatility", "Volatility Filter + Breakout", "20/2",        create_bollinger_bands_chart),
            "KC":    ("Keltner Channel",        "Volatility", "Breakout Confirmation",        "20/1.5",      None),
            "DC":    ("Donchian (20)",          "Volatility", "Breakout Entry Signal",        "20",          None),
            "MFI":   ("MFI (14)",              "Volume",     "Volume Momentum Confirmation",  "14",          None),
            "CMF":   ("CMF (20)",              "Volume",     "Volume Flow Confirmation",      "20",          None),
            "VWAP":  ("VWAP",                  "Volume",     "Institutional Anchor / Filter", "daily",       None),
            "OBV":   ("OBV",                   "Volume",     "Volume Trend Confirmation",     "cumulative",  None),
            "ADX":   ("ADX (14) +DI/-DI",      "Trend",      "Trend Strength Filter",        "14",          create_adx_chart),
        }

        _CAT_COLOR = {"Trend": INFO, "Momentum": BULL, "Volume": PURP, "Volatility": NEUT}

        # ── build per-indicator stats ─────────────────────────────────────────────
        succ_by_ind = {}
        for s in successful_signals:
            succ_by_ind.setdefault(s["indicator"], []).append(s["gain"])

        indicator_performance = []
        regime_color_map = {"TREND": INFO, "RANGE": NEUT, "VOLATILE": BEAR}

        for key, (name, category, role, params, chart_fn) in indicator_map.items():
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
            _twr = _ind_test_wr(ind_sigs)
            indicator_performance.append({
                "key": key, "name": name, "category": category,
                "role": role, "params": params,
                "total": total, "win_count": win_count,
                "win_rate": win_rate, "avg_gain": round(avg_gain, 2),
                "avg_loss": round(avg_loss, 2), "profit_factor": pf,
                "expectancy": round(exp, 2),
                "best_regime": best_regime, "regime_performance": regime_perf,
                "chart_fn": chart_fn, "signals": ind_sigs,
                "max_gain": data.get("max_gain", 0),
                "max_loss": data.get("max_loss", 0),
                "wilson": _wilson(total, win_rate),
                "test_wr":       round(_twr, 1) if _twr is not None else None,
                "stability_gap": round(abs(win_rate - _twr), 1) if _twr is not None else None,
                "rank_score":    _ind_rank_score(win_rate, _twr, total, win_count, total - win_count),
                "logic_type":    _LOGIC_TYPE.get(category, "Signal"),
            })

        indicator_performance = [x for x in indicator_performance if x["win_rate"] < 100]
        indicator_performance.sort(key=lambda x: x["rank_score"], reverse=True)
        card_accents = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

        # ══════════════════════════════════════════════════════════════════════════
        # INDICATOR LEADERBOARD
        # ══════════════════════════════════════════════════════════════════════════
        if not indicator_performance:
            st.info("No indicator data available for the selected period.")
        else:
            _ind_tips = {
                "Signals":       "Total number of times this indicator triggered a signal",
                "Wins":          "Number of signals that ended in a profitable trade",
                "Losses":        "Number of signals that resulted in a loss",
                "Avg Gain":      "Average profit on winning trades — higher means bigger wins",
                "Avg Loss":      "Average loss on losing trades — closer to 0 means better risk control",
                "Best Regime":   "Market condition where this indicator performed best (Trend/Range/Volatile)",
                "Profit Factor": "Total gains ÷ total losses — above 1.0 means profitable",
                "Expectancy":    "Average profit per trade across all signals",
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
                logic    = ind["logic_type"]

                _twr = ind["test_wr"]
                _gap = ind["stability_gap"]
                _rs  = ind["rank_score"]
                if _twr is not None:
                    _tw_c  = BULL if _twr >= win_pct - 5 else (NEUT if _twr >= win_pct - 15 else BEAR)
                    _rs_c  = BULL if _rs >= 70 else (NEUT if _rs >= 50 else BEAR)
                    _gap_c = BULL if _gap < 10 else (NEUT if _gap < 20 else BEAR)
                    _twr_str   = f"{_twr:.1f}%"
                    _gap_str   = f"{_gap:.0f}pts"
                    _twr_label = "recent 25%"
                else:
                    _tw_c = "#555"; _rs_c = NEUT; _gap_c = "#555"
                    _twr_str = "—"; _gap_str = "—"; _twr_label = "not enough data"

                _train_test_html = (
                    f"<div style='background:#0e0e0e;border:1px solid #1e1e1e;border-radius:8px;"
                    f"padding:0.55rem 0.8rem;margin-bottom:0.8rem;'>"
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:0.5rem;'>"
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:0.5rem;color:#404040;text-transform:uppercase;letter-spacing:0.6px;"
                    f"font-weight:700;margin-bottom:0.2rem;'>Training</div>"
                    f"<div style='font-size:1.0rem;font-weight:900;color:#888;'>{win_pct:.1f}%</div>"
                    f"<div style='font-size:0.52rem;color:#303030;'>full period</div></div>"
                    f"<div style='text-align:center;border-left:1px solid #1e1e1e;'>"
                    f"<div style='font-size:0.5rem;color:#404040;text-transform:uppercase;letter-spacing:0.6px;"
                    f"font-weight:700;margin-bottom:0.2rem;'>Testing</div>"
                    f"<div style='font-size:1.0rem;font-weight:900;color:{_tw_c};'>{_twr_str}</div>"
                    f"<div style='font-size:0.52rem;color:#303030;'>{_twr_label}</div></div>"
                    f"<div style='text-align:center;border-left:1px solid #1e1e1e;'>"
                    f"<div style='font-size:0.5rem;color:#404040;text-transform:uppercase;letter-spacing:0.6px;"
                    f"font-weight:700;margin-bottom:0.2rem;'>Stability</div>"
                    f"<div style='font-size:1.0rem;font-weight:900;color:{_gap_c};'>{_gap_str}</div>"
                    f"<div style='font-size:0.52rem;color:#303030;'>train − test</div></div>"
                    f"<div style='text-align:center;border-left:1px solid #1e1e1e;'>"
                    f"<div style='font-size:0.5rem;color:#404040;text-transform:uppercase;letter-spacing:0.6px;"
                    f"font-weight:700;margin-bottom:0.2rem;'>Rank Score</div>"
                    f"<div style='font-size:1.0rem;font-weight:900;color:{_rs_c};'>{_rs:.0f}</div>"
                    f"<div style='font-size:0.52rem;color:#303030;'>out of 100</div></div>"
                    f"</div></div>"
                )

                st.markdown((
                    f"<div style='background:#1b1b1b;border:1px solid #272727;"
                    f"border-radius:14px;overflow:hidden;margin-bottom:1.5rem;'>"
                    f"<div style='padding:1.6rem 1.8rem;"
                    f"background:linear-gradient(135deg,{_hex_rgba(accent,.07)},transparent);'>"
                    f"<div style='display:flex;align-items:center;gap:1.2rem;margin-bottom:1.1rem;'>"
                    f"<div style='width:3rem;height:3rem;border-radius:50%;"
                    f"background:{accent}18;border:2px solid {accent};"
                    f"display:flex;align-items:center;justify-content:center;flex-shrink:0;'>"
                    f"<span style='font-size:1.1rem;font-weight:900;color:{accent};'>#{idx+1}</span></div>"
                    f"<div style='flex:1;'>"
                    f"<div style='font-size:1.15rem;font-weight:900;color:#e0e0e0;'>{ind['name']}</div>"
                    f"<div style='display:flex;align-items:center;gap:0.4rem;margin-top:0.2rem;flex-wrap:wrap;'>"
                    f"<span style='font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;"
                    f"background:{accent}18;color:{accent};border-radius:20px;padding:0.12rem 0.55rem;'>{ind['category']}</span>"
                    f"<span style='font-size:0.62rem;background:#1a1a1a;color:#6c6c6c;border:1px solid #2a2a2a;"
                    f"border-radius:20px;padding:0.1rem 0.5rem;font-weight:600;'>{logic}</span>"
                    f"<span style='font-size:0.62rem;color:#555;font-weight:600;'>{ind['role']}</span>"
                    f"<span style='font-size:0.58rem;color:#383838;border:1px solid #252525;border-radius:4px;"
                    f"padding:0.06rem 0.38rem;font-weight:600;'>params: {ind['params']}</span>"
                    f"</div></div>"
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-size:2.6rem;font-weight:900;color:{accent};line-height:1;"
                    f"text-shadow:0 0 20px {accent}33;'>{win_pct:.0f}%</div>"
                    f"<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-top:0.1rem;'>Win Rate</div>"
                    f"</div></div>"
                    f"<div style='margin-bottom:0.9rem;'>"
                    f"<div style='display:flex;border-radius:6px;overflow:hidden;"
                    f"height:7px;background:#1a1a1a;margin-bottom:0.4rem;'>"
                    f"<div style='width:{win_pct:.1f}%;background:{accent};box-shadow:0 0 8px {accent}55;'></div>"
                    f"<div style='width:{loss_pct:.1f}%;background:{_hex_rgba(BEAR,.35)};'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span style='font-size:0.72rem;color:{accent};font-weight:700;'>"
                    f"&#10003; {total} signals &middot; {win_pct:.0f}% winners</span>"
                    f"<span style='font-size:0.72rem;color:{BEAR};font-weight:700;'>{loss_pct:.0f}% losers</span>"
                    f"</div></div>"
                    + _train_test_html
                    + f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;'>"
                    + _sb("Signals",       str(total),                    "#e0e0e0")
                    + _sb("Wins",          str(wins),                     BULL, _hex_rgba(BULL,.08), f"{win_pct:.0f}%")
                    + _sb("Losses",        str(losses),                   BEAR, _hex_rgba(BEAR,.08), f"{loss_pct:.0f}%")
                    + _sb("Best Regime",   ind["best_regime"] or "—", br_color, _hex_rgba(br_color,.10))
                    + _sb("Avg Gain",      f"+{ind['avg_gain']:.2f}%",    gain_col, _hex_rgba(BULL,.06))
                    + _sb("Avg Loss",      f"{ind['avg_loss']:.2f}%",     loss_col, _hex_rgba(BEAR,.06))
                    + _sb("Profit Factor", f"{ind['profit_factor']:.2f}", BULL if ind['profit_factor'] >= 1.5 else (NEUT if ind['profit_factor'] >= 1 else BEAR))
                    + _sb("Expectancy",    f"{ind['expectancy']:+.2f}%",  BULL if ind['expectancy'] > 0 else BEAR)
                    + "</div></div></div>"
                ), unsafe_allow_html=True)



    with _sig_main_tabs[1]:
        # ══════════════════════════════════════════════════════════════════════════
        # REGIME CHAMPIONS
        # ══════════════════════════════════════════════════════════════════════════
        _all_names = {p["key"]: p["name"] for p in indicator_performance}
        combo_accent_cycle = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

        def _wr_color(wr):
            if wr >= 65: return ("#1b5e20", "#81c784")
            if wr >= 55: return ("#2e7d32", "#a5d6a7")
            if wr >= 45: return ("#0d47a1", "#90caf9")
            if wr >= 35: return ("#b71c1c", "#ef9a9a")
            return ("#282828", "#606060")

        _regime_meta = {
            "TREND":    {"accent": INFO, "label": "Trend",    "summary": "Use when price is moving cleanly in one direction."},
            "RANGE":    {"accent": NEUT, "label": "Range",    "summary": "Use when price rotates between support and resistance."},
            "VOLATILE": {"accent": BEAR, "label": "Volatile", "summary": "Use when price expands quickly and needs fast confirmation."},
        }

        _broad_cat = {
            "Trend Following": "Trend", "Trend Reversal": "Trend",
            "Trend & S/R": "Trend", "Trend Strength": "Trend",
            "Momentum": "Momentum", "Oscillator": "Momentum", "Reversal": "Momentum",
            "Volatility": "Volatility", "Volatility Breakout": "Volatility", "Breakout": "Volatility",
            "Volume Momentum": "Volume", "Volume Flow": "Volume",
            "Volume Anchor": "Volume", "Volume Trend": "Volume",
        }

        def _ind_cat(key):
            raw = indicator_map.get(key, ("", "", "", "", None))[1]
            return _broad_cat.get(raw, "Other")

        def _test_wr_combo(cd):
            mwr = cd.get("monthly_win_rates", {})
            if not mwr:
                return cd["success_rate"]
            months = sorted(mwr.keys())
            split  = max(1, len(months) // 4)
            vals   = [mwr[m] for m in months[-split:] if mwr[m] is not None]
            return float(np.mean(vals)) if vals else cd["success_rate"]

        def _rank_score_combo(cd, parts, test_w):
            train_wr = cd["success_rate"]
            gap      = abs(train_wr - test_w)
            n        = cd["total"]
            n_cats   = len(set(_ind_cat(p) for p in parts))
            wins     = cd["successful"]
            losses   = cd["failed"]
            bal      = 1 - abs(wins - losses) / max(wins + losses, 1)
            return round(
                min(test_w, 100) / 100 * 50
                + max(0, 1 - gap / 50) * 20
                + min(n / 30, 1) * 15
                + min(n_cats / 3, 1) * 10
                + bal * 5,
                2,
            )

        all_combo_data = []
        if combo_results:
            for combo_key, cd in combo_results.items():
                parts = [p.strip() for p in combo_key.split(" + ")]
                n_c   = cd["total"]
                wr    = cd["success_rate"]
                if wr >= 100:
                    continue
                regime_perf_raw = cd.get("regime_performance", {})
                regime_totals   = cd.get("regime_totals", {})
                rp      = {r: regime_perf_raw.get(r, 0) for r in regime_perf_raw if regime_totals.get(r, 0) > 0}
                best_r  = max(rp, key=rp.get) if rp else ""
                _tw     = _test_wr_combo(cd)
                _gap    = round(abs(wr - _tw), 1)
                _cats   = [_ind_cat(p) for p in parts]
                _ccount = {}
                for c in _cats:
                    _ccount[c] = _ccount.get(c, 0) + 1
                all_combo_data.append({
                    "key":           combo_key,
                    "indicators":    parts,
                    "size":          len(parts),
                    "label":         " + ".join(_all_names.get(p, p) for p in parts),
                    "total":         n_c,
                    "active_bars":   cd.get("active_bars", n_c),
                    "regime_totals": regime_totals,
                    "wins":          cd["successful"],
                    "losses":        cd["failed"],
                    "win_rate":      wr,
                    "test_wr":       round(_tw, 1),
                    "stability_gap": _gap,
                    "avg_gain":      cd["avg_gain"],
                    "avg_loss":      cd["avg_loss"],
                    "profit_factor": cd["profit_factor"],
                    "expectancy":    cd["expectancy"],
                    "avg_hold":      cd.get("avg_hold", 0),
                    "regime_perf":   rp,
                    "best_regime":   best_r,
                    "rank_score":    _rank_score_combo(cd, parts, _tw),
                    "overloaded_cats": [c for c, n in _ccount.items() if n > 2],
                    "cat_counts":    _ccount,
                    "signal_freq":   cd.get("signal_frequency", 0),
                    "signal_window": cd.get("signal_window", combo_signal_window),
                    "consistency":   cd.get("monthly_consistency", 0),
                    "monthly_win_rates": cd.get("monthly_win_rates", {}),
                })
            all_combo_data.sort(key=lambda x: x["rank_score"], reverse=True)

        st.markdown(
            "<div style='margin:2.5rem 0 1.2rem;border-top:1px solid #272727;padding-top:1.5rem;'>"
            "<div style='font-size:1.1rem;font-weight:900;color:#e0e0e0;margin-bottom:0.2rem;'>"
            "Regime Champions</div>"
            "<div style='font-size:0.72rem;color:#606060;'>Best indicator combinations per market condition</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        if all_combo_data:

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
                if _total >= 25: return ("Deep sample",   INFO)
                if _total >= 15: return ("Strong sample", BULL)
                if _total >= 8:  return ("Usable sample", NEUT)
                return ("Thin sample", BEAR)

            def _render_focus_card(row, rank, focus_regime, hero=False):
                _meta         = _regime_meta[focus_regime]
                _accent       = _meta["accent"]
                _label        = _meta["label"]
                _sample_label, _sample_color = _sample_band(row)
                _wr_col  = BULL if row["win_rate"] >= 55 else NEUT if row["win_rate"] >= 45 else BEAR
                _pf_col  = BULL if row["profit_factor"] >= 1.3 else NEUT if row["profit_factor"] >= 1 else BEAR
                _exp_col = BULL if row["expectancy"] > 0 else BEAR
                _title   = f"Top {_label} setup" if hero else f"#{rank}"
                _card_pad = "1.25rem 1.35rem" if hero else "0.95rem 1.1rem"
                _card_rad = "16px" if hero else "14px"
                st.markdown(
                    (
                        f"<div style='background:{panel};border:1px solid {border};border-radius:{_card_rad};"
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
                        f"Overall Win{_tip_icon('Win rate across the full test period.')}</div>"
                        f"<div style='font-size:{'3rem' if hero else '2.2rem'};font-weight:900;color:{_wr_col};line-height:1;"
                        f"text-shadow:0 0 18px {_wr_col}33;'>{row['win_rate']:.1f}%</div>"
                        f"<div style='font-size:0.72rem;color:{muted};margin-top:0.18rem;font-weight:600;'>"
                        f"{row['wins']} winners · {row['losses']} losers</div>"
                        f"</div></div>"
                        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.4rem;margin-bottom:0.65rem;'>"
                        + _focus_metric('Entries', str(row['total']), INFO, f"{row['signal_freq']:.1f}/100 bars", 'Distinct trade entries in the full test.')
                        + _focus_metric('Winners', str(row['wins']), BULL, tip='Entries that finished positive.')
                        + _focus_metric('Losers',  str(row['losses']), BEAR, tip='Entries that finished negative.')
                        + _focus_metric('Profit Factor', f"{row['profit_factor']:.2f}", _pf_col, tip='Total gains divided by total losses.')
                        + _focus_metric('Expectancy', f"{row['expectancy']:+.2f}%", _exp_col, tip='Average edge per trade.')
                        + "</div>"
                        + f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:0.4rem;'>"
                        + _focus_metric('Avg Hold', f"{row['avg_hold']:.0f}d", INFO, tip='Average days held per trade.')
                        + _focus_metric('Avg Gain', f"+{row['avg_gain']:.2f}%", BULL, tip='Average size of winning trades.')
                        + _focus_metric('Avg Loss', f"{row['avg_loss']:.2f}%",  BEAR, tip='Average size of losing trades.')
                        + "</div></div></div>"
                    ),
                    unsafe_allow_html=True,
                )

            def _render_regime_champion_section(_section_name, _regime_key, _save_offset):
                _section_meta    = _regime_meta[_regime_key]
                _regime_combos_all = [row for row in all_combo_data if row["best_regime"] == _regime_key]
                if not _regime_combos_all:
                    _regime_combos_all = [
                        row for row in all_combo_data
                        if row.get("regime_totals", {}).get(_regime_key, 0) > 0
                    ]
                _regime_combos = sorted(
                    _regime_combos_all,
                    key=lambda row: (row["win_rate"], row["total"], row["profit_factor"], row["expectancy"]),
                    reverse=True,
                )[:10]

                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;"
                    f"margin:0.45rem 0 0.65rem 0;flex-wrap:wrap;'>"
                    f"<div>"
                    f"<div style='font-size:0.76rem;color:{_section_meta['accent']};font-weight:900;"
                    f"text-transform:uppercase;letter-spacing:0.8px;'>{_section_name} Champions</div>"
                    f"<div style='font-size:0.76rem;color:{muted};margin-top:0.18rem;'>"
                    f"Best 10 setups in {_section_name.lower()} conditions</div>"
                    f"</div>"
                    f"<div style='font-size:0.72rem;color:{muted};font-weight:700;'>"
                    f"Showing {min(10, len(_regime_combos_all))} of {len(_regime_combos_all)}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                if not _regime_combos:
                    st.markdown(
                        f"<div style='background:{panel};border:1px solid {border};border-radius:14px;"
                        f"padding:0.95rem 1rem;color:{muted};font-size:0.78rem;'>"
                        f"No {_section_name.lower()} combinations found.</div>",
                        unsafe_allow_html=True,
                    )
                    return

                _champion = _regime_combos[0]
                _render_focus_card(_champion, 1, _regime_key, hero=True)
                from favorites_tab import render_save_regime_champion_button
                render_save_regime_champion_button(_champion, _regime_key, _period_label, _save_offset + 1)

                if len(_regime_combos) > 1:
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.45rem 0;'>"
                        f"<span style='width:3px;height:1rem;background:{_section_meta['accent']};"
                        f"border-radius:2px;display:inline-block;'></span>"
                        f"<span style='font-size:0.8rem;font-weight:800;color:{_section_meta['accent']};"
                        f"text-transform:uppercase;letter-spacing:0.5px;'>More {_section_name.lower()} setups</span>"
                        f"<span style='font-size:0.62rem;color:{muted};'>Top {len(_regime_combos)} only</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(f"Only one {_section_name.lower()} setup matched.")

                for _rank, _row in enumerate(_regime_combos[1:], start=2):
                    _render_focus_card(_row, _rank, _regime_key, hero=False)
                    render_save_regime_champion_button(_row, _regime_key, _period_label, _save_offset + _rank)

        _regime_sections = [
            ("Trend",    "TREND",    0),
            ("Range",    "RANGE",    100),
            ("Volatile", "VOLATILE", 200),
        ]
        _champion_tabs = st.tabs([f"{_name} Champions" for _name, _, _ in _regime_sections])
        for _tab, (_section_name, _regime_key, _save_offset) in zip(_champion_tabs, _regime_sections):
            with _tab:
                if all_combo_data:
                    _render_regime_champion_section(_section_name, _regime_key, _save_offset)
                else:
                    st.info(f"No {_section_name.lower()} combinations available yet — run more signals to populate this tab.")
