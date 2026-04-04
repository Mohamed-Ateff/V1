import streamlit as st
import pandas as pd
import numpy as np
from datetime import date as _today_date
from favorites_tab import render_save_button


def signal_analysis_tab(df, info_icon):

    from app import detect_signals, evaluate_signal_success, find_consensus_signals, analyze_indicator_combinations, calculate_monthly_performance
    from app import create_ema_chart, create_adx_chart, create_rsi_chart, create_macd_chart, create_bollinger_bands_chart, create_stochastic_chart

    theme_palette = st.session_state.get('theme_palette', {})
    panel = theme_palette.get('panel', '#181818')
    panel_alt = theme_palette.get('panel_alt', '#212121')
    border = theme_palette.get('border', '#303030')
    text = theme_palette.get('text', '#ffffff')
    muted = theme_palette.get('muted', '#9e9e9e')

    def _hex_to_rgba(hex_color, alpha=0.12):
        hc = str(hex_color).strip().lstrip('#')
        if len(hc) != 6:
            return f'rgba(127, 127, 127, {alpha})'
        r = int(hc[0:2], 16)
        g = int(hc[2:4], 16)
        b = int(hc[4:6], 16)
        return f'rgba({r}, {g}, {b}, {alpha})'

    BULL = "#4caf50"
    BEAR = "#f44336"
    NEUT = "#ff9800"
    INFO = "#2196f3"
    PURP = "#9c27b0"
    BG2  = panel_alt
    BDR  = border

    def _sec(title, color=None):
        c = color or INFO
        return (f"<div style='font-size:1rem;color:#ffffff;font-weight:700;"
                f"margin:2rem 0 1rem 0;border-bottom:2px solid {c}33;"
                f"padding-bottom:0.5rem;'>{title}</div>")

    def _glowbar(pct, color=None, height="8px"):
        c = color or BULL
        pct = max(0, min(100, float(pct)))
        return (f"<div style='background:{BDR};border-radius:999px;height:{height};overflow:hidden;'>"
                f"<div style='width:{pct}%;height:100%;"
                f"background:linear-gradient(90deg,{c}99,{c});border-radius:999px;'></div></div>")

    st.markdown(f"""
    <style>
    [style*='background:linear-gradient(135deg,#0d1117 0%,#131929 60%,#0d1117 100%)'],
    [style*='background:linear-gradient(135deg,#0d1117 0%,#101520 100%)'],
    [style*='background:#0d1117'],
    [style*='background:#0a0d14'] {{
        background: {panel_alt} !important;
    }}

    [style*='border:1px solid #1e2535'],
    [style*='border:1px solid #1e2330'],
    [style*='border:1px solid #1a2035'],
    [style*='border:1px solid rgba(74,158,255,0.14)'] {{
        border-color: {border} !important;
    }}

    [style*='color:#e8eaf0'],
    [style*='color:#ffffff'],
    [style*='color:#fff'] {{
        color: {text} !important;
    }}

    [style*='color:#8fa8c8'],
    [style*='color:#8a95a8'],
    [style*='color:#9ab0c8'],
    [style*='color:#8892a4'] {{
        color: {muted} !important;
    }}

    .stDataFrame, .stDataEditor, .stTable,
    .stDataFrame table, .stDataEditor table, .stTable table,
    .stDataFrame th, .stDataFrame td,
    .stDataEditor th, .stDataEditor td,
    .stTable th, .stTable td {{
        background: {panel} !important;
        color: {text} !important;
        border-color: {border} !important;
    }}

    .sa-kpi-wrap {{
        background: {panel};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 1rem 1rem 0.9rem 1rem;
        margin: 0.2rem 0 1.2rem 0;
    }}
    .sa-kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
    }}
    .sa-kpi-card {{
        background: {panel_alt};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 0.8rem 0.85rem;
    }}
    .sa-kpi-label {{
        font-size: 0.67rem;
        color: {muted};
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }}
    .sa-kpi-value {{
        font-size: 1.55rem;
        font-weight: 900;
        line-height: 1;
    }}
    .sa-kpi-sub {{
        font-size: 0.7rem;
        color: {muted};
        margin-top: 0.25rem;
        font-weight: 600;
    }}
    .sa-table-title {{
        font-size: 0.82rem;
        color: {muted};
        text-transform: uppercase;
        letter-spacing: 0.6px;
        font-weight: 700;
        margin: 0.2rem 0 0.45rem 0;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── Hero panel (top section) ──────────────────────────────────────────────
    stop_loss = 0.02

    _rc1, _rc2, _rc3 = st.columns(3)
    with _rc1:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem;'>
            <span style='font-size:0.72rem;color:{BEAR};font-weight:800;text-transform:uppercase;
                         letter-spacing:0.6px;white-space:nowrap;'>RISK</span>
            <span style='font-size:0.7rem;color:#9e9e9e;'>— how much you are willing to lose per trade</span>
        </div>""", unsafe_allow_html=True)
        risk_val = st.number_input("Risk", min_value=1, max_value=100, value=1, step=1,
                                   label_visibility="collapsed", key="sa_risk_val")
    with _rc2:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem;'>
            <span style='font-size:0.72rem;color:{BULL};font-weight:800;text-transform:uppercase;
                         letter-spacing:0.6px;white-space:nowrap;'>REWARD</span>
            <span style='font-size:0.7rem;color:#9e9e9e;'>— expected gain relative to your risk</span>
        </div>""", unsafe_allow_html=True)
        reward_val = st.number_input("Reward", min_value=1, max_value=100, value=2, step=1,
                                     label_visibility="collapsed", key="sa_reward_val")
    with _rc3:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem;'>
            <span style='font-size:0.72rem;color:{INFO};font-weight:800;text-transform:uppercase;
                         letter-spacing:0.6px;white-space:nowrap;'>PERIOD</span>
            <span style='font-size:0.7rem;color:#9e9e9e;'>— max days to hold a position</span>
        </div>""", unsafe_allow_html=True)
        _period_map = {"Short Term (5d)": 5, "Medium Term (63d)": 63, "Long Term (252d)": 252}
        _period_label = st.selectbox("Period", list(_period_map.keys()), index=1,
                                     label_visibility="collapsed", key="sa_period_val")
        holding_period = _period_map[_period_label]

    rr_ratio      = reward_val / risk_val
    profit_target = stop_loss * rr_ratio
    rr_color      = BULL if rr_ratio >= 2 else NEUT if rr_ratio >= 1.5 else BEAR

    with st.spinner("Running backtest..."):
        signals_df = detect_signals(df)
        results, successful_signals, all_signal_details = evaluate_signal_success(
            df, signals_df, profit_target, holding_period, stop_loss
        )
        consensus_signals   = find_consensus_signals(signals_df)
        combo_results       = analyze_indicator_combinations(signals_df, df, profit_target, holding_period, stop_loss)
        monthly_performance = calculate_monthly_performance(all_signal_details)

    total_signals    = sum(d['total_signals'] for d in results.values())
    total_successful = len(successful_signals)   # only signals that actually hit the R:R profit target
    overall_success  = (total_successful / total_signals * 100) if total_signals > 0 else 0

    all_gains  = [s['gain'] for s in all_signal_details if s['gain'] > 0]
    all_losses = [abs(s['gain']) for s in all_signal_details if s['gain'] < 0]
    actual_avg_gain = float(np.mean(all_gains))  if all_gains  else 0.0
    actual_avg_loss = float(np.mean(all_losses)) if all_losses else 0.0
    actual_rr       = round(actual_avg_gain / actual_avg_loss, 2) if actual_avg_loss > 0 else 0.0
    pf_overall      = round(sum(all_gains) / sum(all_losses), 2) if all_losses and sum(all_losses) > 0 else 0.0
    expectancy      = round((overall_success / 100) * actual_avg_gain - (1 - overall_success / 100) * actual_avg_loss, 2)

    def wilson_score(data):
        n = data['total']
        p = data['success_rate'] / 100
        if n == 0:
            return 0
        z = 1.645
        denom  = 1 + z * z / n
        centre = p + z * z / (2 * n)
        spread = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
        return (centre - spread) / denom * 100

    best_combo = max(combo_results.items(), key=lambda x: wilson_score(x[1])) if combo_results else ("N/A", {'success_rate': 0})

    sc      = BULL if overall_success >= 50 else BEAR
    total_failed = total_signals - total_successful

    # KPI row
    st.markdown(f"""
    <div class='sa-kpi-wrap'>
        <div class='sa-kpi-grid'>
            <div class='sa-kpi-card' style='border-top:3px solid {INFO};'>
                <div class='sa-kpi-label'>Total Signals</div>
                <div class='sa-kpi-value' style='color:{INFO};'>{total_signals}</div>
                <div class='sa-kpi-sub'>Across all indicators</div>
            </div>
            <div class='sa-kpi-card' style='border-top:3px solid {BULL};'>
                <div class='sa-kpi-label'>Successful</div>
                <div class='sa-kpi-value' style='color:{BULL};'>{total_successful}</div>
                <div class='sa-kpi-sub'>Hit target at {risk_val}:{reward_val}</div>
            </div>
            <div class='sa-kpi-card' style='border-top:3px solid {BEAR};'>
                <div class='sa-kpi-label'>Failure</div>
                <div class='sa-kpi-value' style='color:{BEAR};'>{total_failed}</div>
                <div class='sa-kpi-sub'>Missed target at {risk_val}:{reward_val}</div>
            </div>
            <div class='sa-kpi-card' style='border-top:3px solid {sc};'>
                <div class='sa-kpi-label'>Win Rate</div>
                <div class='sa-kpi-value' style='color:{sc};'>{overall_success:.1f}%</div>
                <div class='sa-kpi-sub'>Overall hit rate</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Create sub-tabs for different analyses
    analysis_tab1, analysis_tab2 = st.tabs([
        "Indicator Analysis",
        "Indicator Combinations"
    ])

    with analysis_tab1:
        st.markdown('<div class="section-container" style="padding: 2rem;">', unsafe_allow_html=True)

        indicator_map = {
            # ── 1️⃣ Trend (Direction) ─────────────────────────────────────
            "EMA":   ("EMA (20/50/200)",         "Trend Following",          "Identifies and follows directional trends with multiple EMAs",          create_ema_chart),
            "SMA":   ("SMA (50/200)",             "Trend Following",          "Golden/death cross of 50-day and 200-day simple moving averages",        None),
            "PSAR":  ("Parabolic SAR",            "Trend Reversal",           "Dots flip below/above price to signal direction changes",               None),
            "ICHI":  ("Ichimoku Cloud",           "Trend & Support/Res",      "Price crossing above/below the Ichimoku cloud",                         None),
            "WMA":   ("WMA (20)",                 "Trend Following",          "Price crossing the 20-period weighted moving average",                  None),
            # ── 2️⃣ Momentum (Entry Timing) ───────────────────────────────
            "RSI":   ("RSI (14)",                 "Momentum",                 "Detects overbought/oversold conditions and reversals",                  create_rsi_chart),
            "MACD":  ("MACD (12/26/9)",           "Momentum Confirmation",    "Confirms trend changes and momentum shifts",                            create_macd_chart),
            "STOCH": ("Stochastic (14,3,3)",      "Reversal Signals",         "Identifies potential reversal points in the market",                    create_stochastic_chart),
            "ROC":   ("ROC (12)",                 "Momentum",                 "Zero-line crossover of the 12-period Rate of Change",                  None),
            "CCI":   ("CCI (20)",                 "Oscillator",               "Oversold below −100 / overbought above +100",                          None),
            "WILLR": ("Williams %R (14)",         "Oscillator",               "Oversold below −80 / overbought above −20",                            None),
            # ── 3️⃣ Volatility (Breakouts & Risk) ────────────────────────
            "BB":    ("Bollinger Bands (20,2)",   "Volatility & Support",     "Shows volatility levels and potential support or resistance",           create_bollinger_bands_chart),
            "KC":    ("Keltner Channel",           "Volatility Breakout",      "Price touching lower/upper Keltner bands signals mean reversion",       None),
            "DC":    ("Donchian Channel (20)",     "Breakout",                 "Price breaking above upper or below lower 20-period Donchian bands",    None),
            # ── 4️⃣ Volume (Smart Money Confirmation) ─────────────────────
            "MFI":   ("MFI (14)",                 "Volume Momentum",          "Money Flow Index oversold < 20 / overbought > 80",                     None),
            "CMF":   ("CMF (20)",                 "Volume Flow",              "Chaikin Money Flow zero-line crossover",                               None),
            "VWAP":  ("VWAP",                     "Volume Anchor",            "Price crossing the Volume Weighted Average Price",                     None),
            "OBV":   ("OBV",                      "Volume Trend",             "On-Balance Volume rising/falling in sync with price direction",         None),
            # ── 5️⃣ Trend Strength (Regime Detection) ─────────────────────
            "ADX":   ("ADX (14) +DI/−DI",         "Trend Strength",           "+DI crossing above −DI (ADX > 20) signals a trending move",            create_adx_chart),
        }

        perf_rows = []
        regime_rows = []
        indicator_performance = []

        # Pre-compute per-indicator stats from successful_signals only
        # (signals that actually hit the profit target — consistent with all other counts)
        succ_by_ind = {}
        for s in successful_signals:
            k = s['indicator']
            succ_by_ind.setdefault(k, []).append(s['gain'])

        for key, (name, desc, detail, chart_func) in indicator_map.items():
            if key not in results:
                continue
            data = results[key]
            total = data.get("total_signals", 0)
            if total <= 0:
                continue

            # Use successful_signals as the source — same as every other metric in this tab
            succ_gains  = succ_by_ind.get(key, [])
            succ_count_ind = len(succ_gains)
            win_rate    = (succ_count_ind / total * 100) if total > 0 else 0
            avg_gain    = round(float(np.mean(succ_gains)), 2)  if succ_gains  else 0.0

            # avg_loss still comes from all_signal_details (losing trades are not in successful_signals)
            loss_gains  = [abs(s['gain']) for s in all_signal_details if s['indicator'] == key and s['gain'] < 0]
            avg_loss    = round(-float(np.mean(loss_gains)), 2) if loss_gains else 0.0

            total_wins_val  = sum(succ_gains)
            total_loss_val  = sum(loss_gains)
            profit_factor   = round(total_wins_val / total_loss_val, 2) if total_loss_val > 0 else 0.0

            expectancy  = (win_rate / 100) * avg_gain + (1 - win_rate / 100) * avg_loss
            
            regime_perf = data.get("regime_performance", {})
            best_regime_for_ind = max(regime_perf, key=regime_perf.get) if regime_perf else ""
            
            indicator_signals = [s for s in all_signal_details if s['indicator'] == key]
            indicator_signals = sorted(indicator_signals, key=lambda s: pd.to_datetime(s['date']))
            
            win_days = [s['days_held'] for s in indicator_signals if s['success']]
            loss_days = [s['days_held'] for s in indicator_signals if not s['success']]
            med_win_days = float(np.median(win_days)) if win_days else 0.0
            med_loss_days = float(np.median(loss_days)) if loss_days else 0.0

            for regime in ["TREND", "RANGE", "VOLATILE"]:
                regime_signals = [s for s in indicator_signals if s.get('regime') == regime]
                if not regime_signals:
                    continue
                regime_returns = [s['gain'] / 100 for s in regime_signals]
                regime_wins = [s for s in regime_signals if s['success']]
                regime_win_rate = (len(regime_wins) / len(regime_signals)) * 100
                regime_avg_gain = float(np.mean([r for r in regime_returns if r > 0])) * 100 if regime_returns else 0
                regime_avg_loss = float(np.mean([r for r in regime_returns if r < 0])) * 100 if regime_returns else 0
                regime_expect = (regime_win_rate / 100) * regime_avg_gain + (1 - regime_win_rate / 100) * regime_avg_loss
                regime_rows.append({
                    "Indicator": key,
                    "Regime": regime,
                    "Signals": len(regime_signals),
                    "Win %": regime_win_rate,
                })

            perf_rows.append({
                "indicator": key,
                "total": total,
                "win_rate": win_rate,
                "avg_gain": avg_gain,
                "avg_loss": avg_loss,
                "profit_factor": profit_factor,
                "avg_hold": data.get('avg_hold_time', 0),
                "expectancy": expectancy,
                "med_win_days": med_win_days,
                "med_loss_days": med_loss_days,
            })
            
            indicator_performance.append({
                "key": key,
                "name": name,
                "desc": desc,
                "detail": detail,
                "accuracy": win_rate,
                "win_rate": win_rate,
                "total_signals": total,
                "avg_gain": avg_gain,
                "avg_loss": avg_loss,
                "profit_factor": profit_factor,
                "best_regime": best_regime_for_ind,
                "regime_performance": regime_perf,
                "chart_func": chart_func,
                "expectancy": expectancy,
                "max_gain": data.get("max_gain", 0),
                "max_loss": data.get("max_loss", 0),
                "signals": indicator_signals,
            })

        indicator_performance.sort(key=lambda x: (x["expectancy"], x["total_signals"]), reverse=True)
        top_indicators = indicator_performance[:4]

        if not top_indicators:
            st.info("No indicator signals available to analyze.")
        else:
            card_accents  = [BULL, INFO, NEUT, "#A78BFA"]
            regime_color_map = {"TREND": INFO, "RANGE": NEUT, "VOLATILE": BEAR}

            leaderboard_df = pd.DataFrame([
                {
                    "Indicator": i["name"],
                    "Win %": round(i["win_rate"], 1),
                    "Signals": int(i["total_signals"]),
                    "Avg Gain %": round(i["avg_gain"], 2),
                    "Avg Loss %": round(i["avg_loss"], 2),
                    "Best Regime": i["best_regime"] or "—",
                }
                for i in indicator_performance[:10]
            ])
            for idx, ind in enumerate(top_indicators):
                accent   = card_accents[idx]
                rank_num = str(idx + 1)
                br_color = regime_color_map.get(ind["best_regime"], accent)

                # ── stat box helper ──────────────────────────────────────
                def _sb(label, value, color, bg=None, sub=None, sub_color=None):
                    if bg is None:
                        bg = panel_alt
                    sub_html = (
                        f"<div style='font-size:0.72rem;font-weight:700;color:{sub_color or color};"
                        f"opacity:0.8;margin-top:0.25rem;line-height:1;'>{sub}</div>"
                    ) if sub else ""
                    return (
                        f"<div style='background:{bg};border:1px solid {border};border-radius:10px;"
                        f"padding:0.85rem 0.7rem;text-align:center;'>"
                        f"<div style='font-size:0.6rem;color:{muted};text-transform:uppercase;"
                        f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.35rem;'>{label}</div>"
                        f"<div style='font-size:1.25rem;font-weight:900;color:{color};line-height:1;'>{value}</div>"
                        f"{sub_html}"
                        f"</div>"
                    )

                win_pct   = ind["accuracy"]
                loss_pct  = 100 - win_pct
                total     = ind["total_signals"]
                wins      = round(win_pct / 100 * total)
                losses    = total - wins
                gain_col  = BULL if ind["avg_gain"] >= 1 else NEUT if ind["avg_gain"] > 0 else BEAR
                loss_col  = BEAR if ind["avg_loss"] < -1 else NEUT if ind["avg_loss"] < 0 else BULL

                card = (
                    f"<div style='background:{panel};"
                    f"border:1px solid {border};border-left:4px solid {accent};"
                    f"border-radius:14px;padding:1.6rem 1.8rem;margin-bottom:1rem;'>"

                    # ── top row: rank + name + win rate ──────────────────
                    f"<div style='display:flex;align-items:center;gap:1.2rem;margin-bottom:1.3rem;'>"

                    # rank circle
                    f"<div style='width:3rem;height:3rem;border-radius:50%;"
                    f"background:{accent}18;border:2px solid {accent};"
                    f"display:flex;align-items:center;justify-content:center;flex-shrink:0;'>"
                    f"<span style='font-size:1.1rem;font-weight:900;color:{accent};'>#{rank_num}</span>"
                    f"</div>"

                    # name + category
                    f"<div style='flex:1;'>"
                    f"<div style='font-size:1.15rem;font-weight:900;color:{text};line-height:1.2;'>{ind['name']}</div>"
                    f"<div style='font-size:0.78rem;color:{accent};font-weight:600;"
                    f"text-transform:uppercase;letter-spacing:0.5px;margin-top:0.2rem;'>{ind['desc']}</div>"
                    f"</div>"

                    # big win rate
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-size:2.6rem;font-weight:900;color:{accent};line-height:1;'>{win_pct:.0f}%</div>"
                    f"<div style='font-size:0.65rem;color:{muted};text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-top:0.1rem;'>Win Rate</div>"
                    f"</div>"
                    f"</div>"

                    # ── win/loss progress bar ─────────────────────────────
                    f"<div style='margin-bottom:1.3rem;'>"
                    f"<div style='display:flex;border-radius:6px;overflow:hidden;height:7px;margin-bottom:0.45rem;'>"
                    f"<div style='width:{win_pct:.1f}%;background:{accent};'></div>"
                    f"<div style='width:{loss_pct:.1f}%;background:{_hex_to_rgba(BEAR, 0.35)};'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span style='font-size:0.72rem;color:{accent};font-weight:700;'>"
                    f"✓ {total} signals · {win_pct:.0f}% winners</span>"
                    f"<span style='font-size:0.72rem;color:{BEAR};font-weight:700;'>"
                    f"{loss_pct:.0f}% losers</span>"
                    f"</div>"
                    f"</div>"

                    # ── stat grid ─────────────────────────────────────────
                    f"<div style='display:grid;grid-template-columns:repeat(6,1fr);gap:0.6rem;margin-bottom:1.3rem;'>"
                    + _sb("Signals",     str(total),                    text)
                    + _sb("Successful",  str(wins),                     BULL, _hex_to_rgba(BULL, 0.08),  sub=f"{win_pct:.0f}%",  sub_color=BULL)
                    + _sb("Failure",     str(losses),                   BEAR, _hex_to_rgba(BEAR, 0.08),  sub=f"{loss_pct:.0f}%", sub_color=BEAR)
                    + _sb("Avg Gain",    f"+{ind['avg_gain']:.2f}%",    gain_col,  _hex_to_rgba(BULL, 0.06))
                    + _sb("Avg Loss",    f"{ind['avg_loss']:.2f}%",     loss_col,  _hex_to_rgba(BEAR, 0.06))
                    + _sb("Best Regime", ind["best_regime"] or "—",     br_color,  _hex_to_rgba(br_color, 0.12))
                    + f"</div>"

                    f"</div>"
                )
                st.markdown(card, unsafe_allow_html=True)

                # ── Signal table ─────────────────────────────────────────
                sigs = ind.get("signals", [])
                if sigs:
                    sig_df = pd.DataFrame(sigs)[['date', 'entry_price', 'exit_price', 'gain', 'days_held', 'regime', 'exit_reason']].copy()
                    sig_df['date']        = pd.to_datetime(sig_df['date']).dt.strftime('%Y-%m-%d')
                    sig_df['entry_price'] = sig_df['entry_price'].round(2)
                    sig_df['exit_price']  = sig_df['exit_price'].round(2)
                    sig_df['gain']        = sig_df['gain'].round(2)
                    sig_df = sig_df.sort_values('date', ascending=False).reset_index(drop=True)
                    sig_df.index += 1
                    sig_df.columns = ['Date', 'Entry', 'Exit', 'Gain %', 'Days', 'Regime', 'Result']


                st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)

            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

    with analysis_tab2:
        from math import sqrt as _sqrt

        MIN_SIGNALS   = 5          # minimum co-signals to show a pair
        regime_colors = {'TREND': INFO, 'RANGE': NEUT, 'VOLATILE': BEAR}
        pair_accent   = [BULL, INFO, NEUT, '#A78BFA', BEAR, '#F472B6']
        pair_data     = []

        # Build full name lookup from indicator_map + indicator_performance
        _all_names = {ind['key']: ind['name'] for ind in indicator_performance}
        _all_accs  = {
            ind['key']: (card_accents[i] if i < len(card_accents) else '#9e9e9e')
            for i, ind in enumerate(indicator_performance)
        } if indicator_performance else {}

        if combo_results:
            for combo_key, cd in combo_results.items():
                if cd['total'] < MIN_SIGNALS:
                    continue

                parts = combo_key.split(' + ')
                if len(parts) != 2:
                    continue
                ka, kb = parts[0].strip(), parts[1].strip()

                n      = cd['total']
                wins_n = cd['successful']
                loss_n = cd['failed']
                wr     = cd['success_rate']
                rp     = {r: v for r, v in cd.get('regime_performance', {}).items() if v > 0}
                best_r = max(rp, key=rp.get) if rp else ''

                # Wilson lower-bound score (conservative confidence-adjusted ranking)
                p_w = wr / 100
                z   = 1.96
                ws  = (p_w + z**2/(2*n) - z*_sqrt(p_w*(1-p_w)/n + z**2/(4*n**2))) / (1 + z**2/n) * 100 if n > 0 else 0

                pair_data.append({
                    'ka': ka, 'kb': kb,
                    'short': f"{ka} + {kb}",
                    'total': n,
                    'wins': wins_n,
                    'losses': loss_n,
                    'win_rate': wr,
                    'avg_gain': cd['avg_gain'],
                    'avg_loss': cd['avg_loss'],
                    'profit_factor': cd['profit_factor'],
                    'expectancy': cd['expectancy'],
                    'avg_hold': cd.get('avg_hold', 0),
                    'regime_perf': rp,
                    'best_regime': best_r,
                    'wilson': ws,
                })

            pair_data.sort(key=lambda x: x['wilson'], reverse=True)
            pair_data = pair_data[:10]  # keep only the best 10

        # Use full name/accent lookups (fall back to key if not in top-4)
        top_names = _all_names
        top_accs  = _all_accs

        if not pair_data:
            st.info("No indicator pairs fired together enough times. Try a longer date range or lower the R:R ratio to generate more signals.")
        else:
            pair_summary_df = pd.DataFrame([
                {
                    'Pair': p['short'],
                    'Signals': p['total'],
                    'Win %': p['win_rate'],
                    'Best Regime': p['best_regime'] or '—',
                }
                for p in pair_data[:12]
            ])
            # ── Ranking summary row ───────────────────────────────────────
            top_pairs = pair_data[:6]
            cols_count = len(top_pairs)
            rank_row_html = f"<div style='display:grid;grid-template-columns:repeat({cols_count},1fr);gap:0.5rem;margin-bottom:1.5rem;'>"
            for i, row in enumerate(top_pairs):
                ac = pair_accent[i % len(pair_accent)]
                rank_row_html += (
                    f"<div style='background:{panel_alt};border:1px solid {border};border-top:2px solid {ac};"
                    f"border-radius:10px;padding:0.75rem 0.6rem;text-align:center;'>"
                    f"<div style='font-size:0.6rem;color:{muted};font-weight:700;text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-bottom:0.3rem;'>#{i+1}</div>"
                    f"<div style='font-size:0.82rem;font-weight:800;color:{ac};'>{row['short']}</div>"
                    f"<div style='font-size:1.1rem;font-weight:900;color:{text};margin-top:0.2rem;'>{row['win_rate']:.0f}%</div>"
                    f"<div style='font-size:0.65rem;color:{muted};'>{row['total']} signals</div>"
                    f"</div>"
                )
            rank_row_html += "</div>"
            st.markdown(rank_row_html, unsafe_allow_html=True)

            # ── Per-pair cards ────────────────────────────────────────────
            def _stat2(lbl, val, col):
                return (
                    "<div style='background:" + panel_alt + ";border:1px solid " + border + ";border-radius:8px;"
                    "padding:0.8rem 0.5rem;text-align:center;'>"
                    "<div style='font-size:0.72rem;color:" + muted + ";text-transform:uppercase;"
                    "letter-spacing:0.5px;margin-bottom:0.3rem;'>" + lbl + "</div>"
                    "<div style='font-size:1.2rem;font-weight:800;color:" + col + ";line-height:1;'>" + val + "</div>"
                    "</div>"
                )

            for i, row in enumerate(pair_data):
                accent   = pair_accent[i % len(pair_accent)]
                ka, kb   = row['ka'], row['kb']
                ac_a     = top_accs.get(ka, accent)
                ac_b     = top_accs.get(kb, accent)
                wr       = row['win_rate']
                lp       = 100 - wr
                n        = row['total']
                wins_n   = row['wins']
                losses_n = row['losses']
                pf_c     = BULL if row['profit_factor'] >= 1.5 else NEUT if row['profit_factor'] >= 1.0 else BEAR
                exp_c    = BULL if row['expectancy'] > 0 else BEAR
                gain_c   = BULL
                loss_c   = BEAR
                best_r   = row['best_regime']
                br_c     = regime_colors.get(best_r, accent)
                rp       = row['regime_perf']
                reliability = "HIGH" if n >= 30 else "MODERATE" if n >= 15 else "LOW SAMPLE"
                rel_color   = BULL if n >= 30 else NEUT if n >= 15 else BEAR

                bars = ""
                for reg, pct in rp.items():
                    rc = regime_colors.get(reg, '#888')
                    bw = min(100, max(0, pct))
                    bars += (
                        "<div style='margin-bottom:0.65rem;'>"
                        "<div style='display:flex;justify-content:space-between;margin-bottom:0.25rem;'>"
                        "<span style='font-size:0.75rem;color:" + muted + ";font-weight:700;"
                        "text-transform:uppercase;letter-spacing:0.5px;'>" + reg + "</span>"
                        "<span style='font-size:0.82rem;font-weight:800;color:" + rc + ";'>" + f"{pct:.0f}%" + "</span>"
                        "</div>"
                        "<div style='background:" + border + ";border-radius:4px;height:6px;'>"
                        "<div style='background:" + rc + ";border-radius:4px;height:6px;width:" + f"{bw:.0f}" + "%;'></div>"
                        "</div></div>"
                    )

                card = (
                    "<div style='background:" + panel + ";border:1px solid " + border + ";"
                    "border-top:3px solid " + accent + ";border-radius:14px;"
                    "padding:1.6rem 1.6rem;margin-bottom:1.2rem;'>"

                    # Header
                    "<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1.2rem;'>"
                    "<div>"
                    # Pill badges
                    "<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;'>"
                    "<span style='background:" + ac_a + "20;color:" + ac_a + ";font-size:0.8rem;font-weight:800;"
                    "padding:0.25rem 0.75rem;border-radius:20px;border:1px solid " + ac_a + "50;'>"
                    + top_names.get(ka, ka) + "</span>"
                    "<span style='color:" + muted + ";font-weight:700;font-size:0.9rem;'>+</span>"
                    "<span style='background:" + ac_b + "20;color:" + ac_b + ";font-size:0.8rem;font-weight:800;"
                    "padding:0.25rem 0.75rem;border-radius:20px;border:1px solid " + ac_b + "50;'>"
                    + top_names.get(kb, kb) + "</span>"
                    "</div>"
                    "<div style='font-size:0.78rem;color:" + muted + ";'>"
                    "Best regime: <span style='color:" + br_c + ";font-weight:700;'>"
                    + (best_r + f" ({rp.get(best_r, 0):.0f}% win rate)" if best_r else "—") +
                    "</span></div>"
                    "</div>"
                    # Big win rate
                    "<div style='text-align:right;'>"
                    "<div style='font-size:2.8rem;font-weight:900;color:" + accent + ";line-height:1;'>"
                    + f"{wr:.1f}" + "<span style='font-size:1.2rem;'>%</span></div>"
                    "<div style='font-size:0.75rem;color:" + muted + ";text-transform:uppercase;"
                    "letter-spacing:0.6px;margin-top:0.1rem;'>Win Rate</div>"
                    "<div style='font-size:0.72rem;color:" + muted + ";margin-top:0.2rem;'>" + str(n) + " signals</div>"
                    "</div>"
                    "</div>"

                    # Win/loss bar
                    "<div style='margin-bottom:1.3rem;'>"
                    "<div style='display:flex;border-radius:6px;overflow:hidden;height:8px;margin-bottom:0.4rem;'>"
                    "<div style='width:" + f"{wr:.1f}" + "%;background:" + BULL + ";'></div>"
                    "<div style='width:" + f"{lp:.1f}" + "%;background:" + BEAR + ";'></div>"
                    "</div>"
                    "<div style='display:flex;justify-content:space-between;'>"
                    "<span style='font-size:0.75rem;color:" + BULL + ";font-weight:700;'>&#x2714; "
                    + str(wins_n) + " wins (" + f"{wr:.1f}%" + ")</span>"
                    "<span style='font-size:0.75rem;color:" + BEAR + ";font-weight:700;'>"
                    + str(losses_n) + " losses (" + f"{lp:.1f}%" + ") &#x2716;</span>"
                    "</div></div>"

                    # Stats + regime
                    "<div style='display:grid;grid-template-columns:1fr 220px;gap:1.2rem;'>"
                    "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;align-content:start;'>"
                    + _stat2("Signals",     str(n),                            "#ffffff")
                    + _stat2("Winners",     str(wins_n),                       BULL)
                    + _stat2("Losers",      str(losses_n),                     BEAR)
                    + _stat2("Avg Gain",    "+" + f"{row['avg_gain']:.2f}%",   gain_c)
                    + _stat2("Avg Loss",    f"{row['avg_loss']:.2f}%",         loss_c)
                    + _stat2("Avg Hold",    f"{row['avg_hold']:.0f}d",         INFO)
                    + "</div>"
                    "<div style='background:" + panel_alt + ";border:1px solid " + border + ";"
                    "border-radius:10px;padding:1rem 1.1rem;'>"
                    "<div style='font-size:0.75rem;color:" + accent + ";font-weight:700;"
                    "text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.8rem;'>Regime Win Rate</div>"
                    + bars +
                    "</div>"
                    "</div></div>"
                )
                st.markdown(card, unsafe_allow_html=True)

                render_save_button(i, ka, kb, row, top_names)
                # ── Signal table for this combination ─────────────────
                _sigs = combo_results.get(f"{ka} + {kb}", {}).get('signals', [])
                if _sigs:
                    _sdf = pd.DataFrame(_sigs)[['date','entry_price','exit_price','gain','days_held','regime','result']].copy()
                    _sdf = _sdf.sort_values('date', ascending=False).reset_index(drop=True)
                    _sdf.index += 1
                    _sdf['result'] = _sdf['result'].map({
                        'profit':         'Profit',
                        'stop_loss':      'Stop Loss',
                        'timeout_profit': 'Timeout ↑',
                        'timeout_loss':   'Timeout ↓',
                        'timeout':        'Timeout',
                    }).fillna(_sdf['result'])
                    _sdf.columns = ['Date','Entry','Exit','Gain %','Days','Regime','Result']
                    _sv = _sdf.copy()
                    _sv['Entry']  = _sv['Entry'].map(lambda v: f"{v:.2f}")
                    _sv['Exit']   = _sv['Exit'].map(lambda v: f"{v:.2f}")
                    _sv['Gain %'] = _sv['Gain %'].map(lambda v: f"{v:+.2f}%")
                    _sv['Days']   = _sv['Days'].map(lambda v: f"{int(v)}")


                st.markdown("<div style='margin-bottom:2rem;'></div>", unsafe_allow_html=True)