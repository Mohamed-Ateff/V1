import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
from favorites_tab import render_save_button


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
    c1, c2, c3 = st.columns([2, 2, 2])
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
            signals_df, df, profit_target, holding_period, stop_loss
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
    # 0. FIRING RIGHT NOW  (indicators active on latest bar)
    # ══════════════════════════════════════════════════════════════════════════
    _buy_cols = [c for c in signals_df.columns if c.endswith("_Buy")]
    _last_row = signals_df.iloc[-1]
    _firing   = [c.replace("_Buy", "") for c in _buy_cols if _last_row.get(c, 0) == 1]

    if _firing:
        _pills = "".join(
            f"<span style='background:{BULL}18;border:1.5px solid {BULL};"
            f"border-radius:999px;padding:0.25rem 0.85rem;"
            f"font-size:0.75rem;font-weight:800;color:{BULL};"
            f"letter-spacing:0.5px;white-space:nowrap;'>{ind}</span>"
            for ind in _firing
        )
        st.markdown(
            f"<div style='background:{BULL}0d;border:1px solid {BULL}44;"
            f"border-left:4px solid {BULL};border-radius:12px;"
            f"padding:0.9rem 1.2rem;margin-bottom:1rem;"
            f"display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;'>"
            f"<div style='font-size:0.72rem;color:{BULL};text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:800;flex-shrink:0;'>&#9679; Firing Now</div>"
            f"{_pills}"
            f"<div style='margin-left:auto;font-size:0.68rem;color:{muted};'>"
            f"{len(_firing)} of {len(_buy_cols)} indicators active on latest bar</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {border};"
            f"border-left:4px solid #555;border-radius:12px;"
            f"padding:0.75rem 1.2rem;margin-bottom:1rem;"
            f"font-size:0.75rem;color:#555;'>"
            f"&#9675; No indicators firing on the latest bar</div>",
            unsafe_allow_html=True,
        )

    # ── Consensus signals banner (3+ indicator agreement) ────────────────────
    if consensus_signals:
        _strong = [c for c in consensus_signals if len(c.get("indicators", [])) >= 3][-5:]
        if _strong:
            _cpills = "".join(
                f"<span style='background:{GOLD}15;border:1px solid {GOLD}44;"
                f"border-radius:8px;padding:0.2rem 0.7rem;"
                f"font-size:0.68rem;font-weight:700;color:{GOLD};margin-right:0.4rem;'>"
                f"{str(c['date'])[:10]} — {len(c.get('indicators', []))} signals</span>"
                for c in reversed(_strong)
            )
            st.markdown(
                f"<div style='background:{GOLD}0a;border:1px solid {GOLD}33;"
                f"border-radius:10px;padding:0.75rem 1.2rem;margin-bottom:1rem;"
                f"font-size:0.72rem;color:{muted};'>"
                f"<span style='color:{GOLD};font-weight:800;text-transform:uppercase;"
                f"letter-spacing:0.6px;margin-right:0.6rem;'>&#9733; 3+ Consensus Days</span>"
                f"{_cpills}</div>",
                unsafe_allow_html=True,
            )

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
    tab_ind, tab_combo, tab_monthly, tab_equity = st.tabs([
        "Indicator Leaderboard",
        "Indicator Combinations",
        "Monthly Heatmap",
        "Equity Curve",
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
    # TAB 2 — INDICATOR COMBINATIONS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_combo:
        _all_names = {p["key"]: p["name"] for p in indicator_performance}
        _all_accs  = {p["key"]: card_accents[i % len(card_accents)]
                      for i, p in enumerate(indicator_performance)}
        pair_accent = [BULL, INFO, NEUT, PURP, "#F472B6", GOLD]

        pair_data = []
        if combo_results:
            for combo_key, cd in combo_results.items():
                if cd["total"] < 5:
                    continue
                parts = combo_key.split(" + ")
                if len(parts) != 2:
                    continue
                ka, kb = parts[0].strip(), parts[1].strip()
                n   = cd["total"]
                wr  = cd["success_rate"]
                rp  = {r: v for r, v in cd.get("regime_performance", {}).items() if v > 0}
                best_r = max(rp, key=rp.get) if rp else ""
                pair_data.append({
                    "ka": ka, "kb": kb, "short": f"{ka} + {kb}",
                    "total": n, "wins": cd["successful"], "losses": cd["failed"],
                    "win_rate": wr, "avg_gain": cd["avg_gain"], "avg_loss": cd["avg_loss"],
                    "profit_factor": cd["profit_factor"], "expectancy": cd["expectancy"],
                    "avg_hold": cd.get("avg_hold", 0),
                    "regime_perf": rp, "best_regime": best_r,
                    "wilson": _wilson(n, wr),
                })
            pair_data.sort(key=lambda x: x["wilson"], reverse=True)
            pair_data = pair_data[:10]

        if not pair_data:
            st.info("No indicator pairs fired together enough times. "
                    "Try a longer date range or lower the R:R ratio.")
        else:
            # ranking strip
            _top6 = pair_data[:6]
            _rhtml = (
                f"<div style='display:grid;grid-template-columns:repeat({len(_top6)},1fr);"
                f"gap:0.5rem;margin-bottom:1.5rem;'>"
            )
            for i, row in enumerate(_top6):
                ac = pair_accent[i % len(pair_accent)]
                _rhtml += (
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-top:2px solid {ac};border-radius:10px;"
                    f"padding:0.75rem 0.6rem;text-align:center;'>"
                    f"<div style='font-size:0.6rem;color:{muted};font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:0.6px;margin-bottom:0.3rem;'>#{i+1}</div>"
                    f"<div style='font-size:0.82rem;font-weight:800;color:{ac};'>{row['short']}</div>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{text_col};margin-top:0.2rem;'>"
                    f"{row['win_rate']:.0f}%</div>"
                    f"<div style='font-size:0.65rem;color:{muted};'>{row['total']} signals</div>"
                    f"</div>"
                )
            _rhtml += "</div>"
            st.markdown(_rhtml, unsafe_allow_html=True)

            def _stat2(lbl, val, col, _pa=panel_alt, _bd=border, _mu=muted):
                return (
                    f"<div style='background:{_pa};border:1px solid {_bd};"
                    f"border-radius:8px;padding:0.8rem 0.5rem;text-align:center;'>"
                    f"<div style='font-size:0.65rem;color:{_mu};text-transform:uppercase;"
                    f"letter-spacing:0.5px;margin-bottom:0.3rem;'>{lbl}</div>"
                    f"<div style='font-size:1.15rem;font-weight:800;color:{col};line-height:1;'>{val}</div>"
                    f"</div>"
                )

            for i, row in enumerate(pair_data):
                accent = pair_accent[i % len(pair_accent)]
                ka, kb = row["ka"], row["kb"]
                ac_a   = _all_accs.get(ka, accent)
                ac_b   = _all_accs.get(kb, accent)
                wr     = row["win_rate"]
                lp     = 100 - wr
                n      = row["total"]
                br_c   = regime_color_map.get(row["best_regime"], accent)
                rp     = row["regime_perf"]

                bars = ""
                for reg, pct in rp.items():
                    rc  = regime_color_map.get(reg, "#888")
                    bw  = min(100, max(0, pct))
                    bars += (
                        f"<div style='margin-bottom:0.6rem;'>"
                        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.2rem;'>"
                        f"<span style='font-size:0.72rem;color:{muted};font-weight:700;"
                        f"text-transform:uppercase;letter-spacing:0.5px;'>{reg}</span>"
                        f"<span style='font-size:0.78rem;font-weight:800;color:{rc};'>{pct:.0f}%</span>"
                        f"</div>"
                        f"<div style='background:{border};border-radius:4px;height:6px;'>"
                        f"<div style='background:{rc};border-radius:4px;height:6px;width:{bw:.0f}%;'></div>"
                        f"</div></div>"
                    )

                _br_label = (
                    row["best_regime"] + f" ({rp.get(row['best_regime'], 0):.0f}%)"
                    if row["best_regime"] else "—"
                )

                st.markdown((
                    f"<div style='background:{panel};border:1px solid {border};"
                    f"border-top:3px solid {accent};border-radius:14px;"
                    f"padding:1.6rem 1.6rem;margin-bottom:1rem;'>"

                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:flex-start;margin-bottom:1.2rem;'>"
                    f"<div>"
                    f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;'>"
                    f"<span style='background:{ac_a}20;color:{ac_a};font-size:0.8rem;font-weight:800;"
                    f"padding:0.25rem 0.75rem;border-radius:20px;border:1px solid {ac_a}50;'>"
                    f"{_all_names.get(ka, ka)}</span>"
                    f"<span style='color:{muted};font-weight:700;font-size:0.9rem;'>+</span>"
                    f"<span style='background:{ac_b}20;color:{ac_b};font-size:0.8rem;font-weight:800;"
                    f"padding:0.25rem 0.75rem;border-radius:20px;border:1px solid {ac_b}50;'>"
                    f"{_all_names.get(kb, kb)}</span></div>"
                    f"<div style='font-size:0.75rem;color:{muted};'>Best regime: "
                    f"<span style='color:{br_c};font-weight:700;'>{_br_label}</span></div>"
                    f"</div>"
                    f"<div style='text-align:right;'>"
                    f"<div style='font-size:2.8rem;font-weight:900;color:{accent};line-height:1;'>"
                    f"{wr:.1f}<span style='font-size:1.2rem;'>%</span></div>"
                    f"<div style='font-size:0.72rem;color:{muted};text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-top:0.1rem;'>Win Rate &middot; {n} signals</div>"
                    f"</div></div>"

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

                    f"<div style='display:grid;grid-template-columns:1fr 200px;gap:1.2rem;'>"
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;"
                    f"gap:0.5rem;align-content:start;'>"
                    + _stat2("Signals",  str(n),                          text_col)
                    + _stat2("Winners",  str(row["wins"]),                 BULL)
                    + _stat2("Losers",   str(row["losses"]),               BEAR)
                    + _stat2("Avg Gain", f"+{row['avg_gain']:.2f}%",       BULL)
                    + _stat2("Avg Loss", f"{row['avg_loss']:.2f}%",        BEAR)
                    + _stat2("Avg Hold", f"{row['avg_hold']:.0f}d",        INFO)
                    + "</div>"
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-radius:10px;padding:1rem 1.1rem;'>"
                    f"<div style='font-size:0.72rem;color:{accent};font-weight:700;"
                    f"text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.8rem;'>"
                    f"Regime Win Rate</div>"
                    + bars
                    + "</div></div></div>"
                ), unsafe_allow_html=True)

                render_save_button(i, ka, kb, row, _all_names)

                # trade history
                _sigs2 = combo_results.get(f"{ka} + {kb}", {}).get("signals", [])
                if _sigs2:
                    _cdf = pd.DataFrame(_sigs2)
                    _ccols = [c for c in ["date","entry_price","exit_price",
                                          "gain","days_held","regime","result"]
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
                        f"Trade history — {ka} + {kb} ({len(_sigs2)} trades)",
                        expanded=False,
                    ):
                        st.dataframe(_cdf, use_container_width=True)

                st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — MONTHLY PERFORMANCE HEATMAP
    # ══════════════════════════════════════════════════════════════════════════
    with tab_monthly:
        if monthly_performance is None or len(monthly_performance) == 0:
            st.info("Not enough signal data to build a monthly breakdown.")
        else:
            mp = monthly_performance.copy()
            mp["month"] = mp["month"].astype(str)
            mp = mp.sort_values("month")
            mp["year"] = mp["month"].str[:4]
            mp["mon"]  = mp["month"].str[5:7]

            mon_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                          "Jul","Aug","Sep","Oct","Nov","Dec"]
            years      = sorted(mp["year"].unique())
            _lookup    = {(r["year"], r["mon"]): r for _, r in mp.iterrows()}

            st.markdown(
                f"<div style='font-size:0.75rem;color:{muted};text-transform:uppercase;"
                f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.8rem;'>"
                f"Monthly Signal Win Rate &nbsp;|&nbsp; "
                f"<span style='color:{BULL};'>&#9632;</span> &ge;60% &nbsp;"
                f"<span style='color:{NEUT};'>&#9632;</span> 40&ndash;60% &nbsp;"
                f"<span style='color:{BEAR};'>&#9632;</span> &lt;40% &nbsp;"
                f"<span style='color:#444;'>&#9632;</span> No data</div>",
                unsafe_allow_html=True,
            )

            _col_w = " ".join(["56px"] + ["1fr"] * 12)
            heatmap = (
                f"<div style='display:grid;grid-template-columns:{_col_w};"
                f"gap:3px;font-size:0.72rem;'>"
                f"<div></div>"
            )
            for ml in mon_labels:
                heatmap += (
                    f"<div style='text-align:center;color:{muted};font-weight:700;"
                    f"font-size:0.62rem;text-transform:uppercase;letter-spacing:0.5px;"
                    f"padding:0.3rem 0;'>{ml}</div>"
                )
            for yr in years:
                heatmap += (
                    f"<div style='color:{text_col};font-weight:800;font-size:0.75rem;"
                    f"padding:0.4rem 0.2rem;display:flex;align-items:center;'>{yr}</div>"
                )
                for mi in range(1, 13):
                    row_data = _lookup.get((yr, f"{mi:02d}"))
                    if row_data is None:
                        heatmap += (
                            f"<div style='background:#1a1a1a;border-radius:5px;"
                            f"padding:0.4rem;text-align:center;color:#333;font-size:0.65rem;'>—</div>"
                        )
                    else:
                        wr_m  = float(row_data["success_rate"])
                        ag_m  = float(row_data["avg_gain"])
                        tot_m = int(row_data["total"])
                        c_col = BULL if wr_m >= 60 else NEUT if wr_m >= 40 else BEAR
                        heatmap += (
                            f"<div style='background:{c_col}22;border:1px solid {c_col}44;"
                            f"border-radius:5px;padding:0.4rem 0.1rem;text-align:center;' "
                            f"title='{tot_m} signals | avg {ag_m:+.1f}%'>"
                            f"<div style='font-size:0.75rem;font-weight:900;color:{c_col};'>"
                            f"{wr_m:.0f}%</div>"
                            f"<div style='font-size:0.55rem;color:{muted};margin-top:0.1rem;'>"
                            f"{tot_m}sig</div>"
                            f"</div>"
                        )
            heatmap += "</div>"
            st.markdown(heatmap, unsafe_allow_html=True)

            with st.expander("Monthly data table", expanded=False):
                _tbl = mp[["month","success_rate","total","avg_gain"]].copy()
                _tbl.columns = ["Month","Win %","Signals","Avg Gain %"]
                st.dataframe(_tbl.set_index("Month"), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — EQUITY CURVE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_equity:
        import plotly.graph_objects as go

        if not all_signal_details:
            st.info("No signal data available to build an equity curve.")
        else:
            _trades = sorted(all_signal_details, key=lambda x: pd.to_datetime(x["date"]))
            _dates  = [str(t["date"])[:10] for t in _trades]
            _gains  = [t["gain"] for t in _trades]
            _cumul  = np.cumsum(_gains).tolist()

            # per-indicator curves (top 3)
            _ind_curves = {}
            for _ip in indicator_performance[:3]:
                _it = sorted(
                    [s for s in all_signal_details if s["indicator"] == _ip["key"]],
                    key=lambda x: pd.to_datetime(x["date"]),
                )
                if len(_it) >= 3:
                    _ip_idx = indicator_performance.index(_ip)
                    _ind_curves[_ip["name"]] = {
                        "dates":  [str(t["date"])[:10] for t in _it],
                        "cum":    np.cumsum([t["gain"] for t in _it]).tolist(),
                        "accent": card_accents[_ip_idx % len(card_accents)],
                    }

            # drawdown series
            _peak = 0.0
            _dd_x, _dd_y = [], []
            for xi, cv in zip(_dates, _cumul):
                _peak = max(_peak, cv)
                _dd_x.append(xi)
                _dd_y.append(cv - _peak)

            final_ret = _cumul[-1]
            max_dd    = round(min(_dd_y), 2) if _dd_y else 0.0
            best_t    = round(max(_gains), 2) if _gains else 0.0
            worst_t   = round(min(_gains), 2) if _gains else 0.0

            fig = go.Figure()
            fig.add_hline(y=0, line_width=1, line_color="#333", line_dash="dot")

            # fill under main curve
            _line_col = BULL if final_ret >= 0 else BEAR
            fig.add_trace(go.Scatter(
                x=_dates, y=_cumul,
                fill="tozeroy",
                fillcolor=_hex_rgba(_line_col, 0.10),
                line=dict(color=_line_col, width=2.5),
                name="All Signals",
                hovertemplate="%{x}<br>Cumulative: %{y:.2f}%<extra></extra>",
            ))

            # per-indicator dotted lines
            for ind_name, ic in _ind_curves.items():
                fig.add_trace(go.Scatter(
                    x=ic["dates"], y=ic["cum"],
                    line=dict(color=ic["accent"], width=1.5, dash="dot"),
                    name=ind_name, opacity=0.75,
                    hovertemplate=f"{ind_name} %{{x}}: %{{y:.2f}}%<extra></extra>",
                ))

            # drawdown shading
            fig.add_trace(go.Scatter(
                x=_dd_x, y=_dd_y,
                fill="tozeroy",
                fillcolor=_hex_rgba(BEAR, 0.12),
                line=dict(color=BEAR, width=1, dash="dot"),
                name="Drawdown", opacity=0.6,
                hovertemplate="DD: %{y:.2f}%<extra></extra>",
            ))

            fig.update_layout(
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ffffff", size=12),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                            bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                xaxis=dict(showgrid=False, zeroline=False, color=muted),
                yaxis=dict(gridcolor="#2a2a2a", zeroline=False, color=muted, ticksuffix="%"),
                margin=dict(l=0, r=0, t=40, b=0),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # summary tiles
            _fin_col = BULL if final_ret >= 0 else BEAR
            _dd_col  = BEAR if max_dd < -5 else NEUT if max_dd < -2 else BULL

            def _etile(label, value, color):
                return (
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-top:3px solid {color};border-radius:10px;"
                    f"padding:0.9rem 1rem;text-align:center;'>"
                    f"<div style='font-size:0.62rem;color:{muted};text-transform:uppercase;"
                    f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.4rem;'>{label}</div>"
                    f"<div style='font-size:1.6rem;font-weight:900;color:{color};line-height:1;'>"
                    f"{value}</div></div>"
                )

            st.markdown(
                f"<div style='display:grid;grid-template-columns:repeat(5,1fr);"
                f"gap:0.8rem;margin-top:1rem;'>"
                + _etile("Total Trades",    str(len(_trades)),          INFO)
                + _etile("Cumulative Ret.", f"{final_ret:+.2f}%",       _fin_col)
                + _etile("Max Drawdown",    f"{max_dd:.2f}%",           _dd_col)
                + _etile("Best Trade",      f"+{best_t:.2f}%",          BULL)
                + _etile("Worst Trade",     f"{worst_t:.2f}%",          BEAR)
                + "</div>",
                unsafe_allow_html=True,
            )

            # regime filter
            st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
            _rf = st.selectbox(
                "Filter by regime",
                ["All", "TREND", "RANGE", "VOLATILE"],
                key="sa_eq_regime_filter",
            )
            if _rf != "All":
                _ft = [t for t in _trades if t.get("regime") == _rf]
                if _ft:
                    _fg   = [t["gain"] for t in _ft]
                    _fc   = np.cumsum(_fg).tolist()
                    _fd   = [str(t["date"])[:10] for t in _ft]
                    _f_wr = round(len([g for g in _fg if g > 0]) / len(_fg) * 100, 1)
                    _rc   = regime_color_map.get(_rf, NEUT)
                    fig2  = go.Figure()
                    fig2.add_hline(y=0, line_width=1, line_color="#333", line_dash="dot")
                    fig2.add_trace(go.Scatter(
                        x=_fd, y=_fc,
                        fill="tozeroy",
                        fillcolor=_hex_rgba(_rc, 0.12),
                        line=dict(color=_rc, width=2.5),
                        name=f"{_rf} regime",
                        hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
                    ))
                    fig2.update_layout(
                        height=260,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#ffffff", size=12),
                        xaxis=dict(showgrid=False, zeroline=False, color=muted),
                        yaxis=dict(gridcolor="#2a2a2a", zeroline=False, color=muted,
                                   ticksuffix="%"),
                        margin=dict(l=0, r=0, t=30, b=0),
                    )
                    st.markdown(
                        f"<div style='font-size:0.8rem;color:{_rc};font-weight:700;"
                        f"margin-bottom:0.4rem;'>{_rf} regime &mdash; {len(_ft)} trades "
                        f"&middot; {_f_wr}% win rate &middot; cumulative {_fc[-1]:+.2f}%</div>",
                        unsafe_allow_html=True,
                    )
                    st.plotly_chart(fig2, use_container_width=True,
                                    config={"displayModeBar": False})
                else:
                    st.info(f"No trades recorded in {_rf} regime.")
