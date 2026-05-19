"""
Strategy Lab — AI Analysis
Full local AI engine: 12-factor score · ML ensemble · historical analogues · price forecast.
No external API. No validator. No backtest. Pure AI read on the current chart.
"""

import streamlit as st
import numpy as np
import pandas as pd

# ── Design tokens ──────────────────────────────────────────────────────────────
BULL = "#4caf50"
BEAR = "#f44336"
NEUT = "#ff9800"
INFO = "#2196f3"
PURP = "#9c27b0"
GOLD = "#FFD700"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _safe_float(v, default=0.0):
    try:
        f = float(v)
        return default if np.isnan(f) else f
    except Exception:
        return default


def _frame_key(df):
    try:
        return (len(df), round(float(df["Close"].iloc[-1]), 4))
    except Exception:
        return (len(df), 0)


# ── Cell builder (inline grid cell with right border) ─────────────────────────
def _cell(label, value, color, sub="", last=False):
    border = "" if last else "border-right:1px solid #222;"
    return (
        f"<div style='padding:0.9rem 1.2rem;{border}display:flex;"
        f"flex-direction:column;gap:0.22rem;'>"
        f"<div style='font-size:0.72rem;color:#888;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;'>{label}</div>"
        f"<div style='font-size:0.95rem;font-weight:800;color:{color};line-height:1.2;'>{value}</div>"
        + (f"<div style='font-size:0.75rem;color:#999;margin-top:0.05rem;'>{sub}</div>" if sub else "")
        + f"</div>"
    )


def _signal_row(icon, title, detail, color):
    return (
        f"<div style='display:flex;gap:0.85rem;align-items:flex-start;"
        f"padding:0.75rem 0;border-bottom:1px solid #1e1e1e;'>"
        f"<span style='color:{color};font-size:1.1rem;flex-shrink:0;margin-top:0.05rem;'>{icon}</span>"
        f"<div>"
        f"<div style='font-size:0.82rem;font-weight:800;color:#e0e0e0;line-height:1.3;'>{title}</div>"
        f"<div style='font-size:0.78rem;color:#aaa;margin-top:0.12rem;'>{detail}</div>"
        f"</div></div>"
    )


def _factor_bar(label, score):
    col = BULL if score >= 65 else (BEAR if score <= 40 else NEUT)
    pct = score
    return (
        f"<div style='margin-bottom:0.55rem;'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.22rem;'>"
        f"<span style='font-size:0.75rem;color:#aaa;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:0.5px;'>{label}</span>"
        f"<span style='font-size:0.65rem;font-weight:900;color:{col};'>{score}</span>"
        f"</div>"
        f"<div style='background:#1a1a1a;border-radius:999px;height:5px;overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;background:{col};"
        f"border-radius:999px;'></div>"
        f"</div>"
        f"</div>"
    )


def _horizon_card(label, ml_data, ana_data, cp):
    if not ml_data and not ana_data:
        return (
            f"<div style='background:#141414;border:1px solid #232323;"
            f"border-radius:10px;padding:1rem;'>"
            f"<div style='font-size:0.72rem;color:#888;text-transform:uppercase;"
            f"font-weight:700;letter-spacing:0.8px;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-size:0.8rem;color:#484848;'>Insufficient data</div>"
            f"</div>"
        )

    ml_up   = _safe_float(ml_data.get("up_prob", 50) if ml_data else 50)
    ml_acc  = _safe_float(ml_data.get("accuracy", 0) if ml_data else 0)
    ml_dir  = ml_data.get("direction", "—") if ml_data else "—"
    ml_col  = BULL if ml_up >= 55 else (BEAR if ml_up <= 45 else NEUT)

    ana_wr  = _safe_float(ana_data.get("w_win_rate", 0) if ana_data else 0)
    ana_ret = _safe_float(ana_data.get("avg_return", 0) if ana_data else 0)
    ana_n   = int(ana_data.get("n_similar", 0) if ana_data else 0)
    ana_col = BULL if ana_wr >= 55 else (BEAR if ana_wr <= 45 else NEUT)

    return (
        f"<div style='background:#141414;border:1px solid #232323;"
        f"border-top:3px solid {ml_col};border-radius:10px;padding:1rem;'>"
        f"<div style='font-size:0.72rem;color:#888;text-transform:uppercase;"
        f"font-weight:700;letter-spacing:0.8px;margin-bottom:0.65rem;'>{label}</div>"

        # ML row
        f"<div style='margin-bottom:0.55rem;'>"
        f"<div style='font-size:0.75rem;color:#999;font-weight:700;margin-bottom:0.2rem;'>ML Prediction</div>"
        f"<div style='font-size:1.05rem;font-weight:900;color:{ml_col};'>"
        f"{ml_up:.0f}% UP &nbsp;·&nbsp; {ml_dir}</div>"
        f"<div style='font-size:0.75rem;color:#999;'>Accuracy {ml_acc:.0f}%</div>"
        f"</div>"

        f"<div style='height:1px;background:#1e1e1e;margin:0.5rem 0;'></div>"

        # Analogue row
        f"<div>"
        f"<div style='font-size:0.75rem;color:#999;font-weight:700;margin-bottom:0.2rem;'>Historical Analogues</div>"
        f"<div style='font-size:1.05rem;font-weight:900;color:{ana_col};'>"
        f"{ana_wr:.0f}% win rate</div>"
        f"<div style='font-size:0.75rem;color:#999;'>"
        f"Avg return {ana_ret:+.2f}% · {ana_n} setups</div>"
        f"</div>"

        f"</div>"
    )


# ══════════════════════════════════════════════════════════════════════════════
# AI COMPUTE (cached)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=180, show_spinner=False)
def _ai_compute(cache_key, _df, _latest_dict, cp):
    from gemini_tab import _compute_ai_score, _decision_from_score, _historical_analogy, _ml_predict, _forecast

    result = {
        "score": 50, "score_col": NEUT,
        "decision": "WAIT", "dec_col": NEUT, "dec_reason": "Insufficient data",
        "factor_scores": {}, "signals": [],
        "ml5": None, "ml10": None, "ml20": None,
        "ana5": None, "ana10": None, "ana20": None,
        "forecast_prices": [], "slope_pct": 0.0, "r2": 0.0,
        "n_bull": 0, "n_bear": 0,
    }

    try:
        score, factor_scores, signals = _compute_ai_score(_latest_dict, _df, float(cp))
        decision, dec_col, dec_reason = _decision_from_score(score)
        result["score"]        = int(score)
        result["factor_scores"] = factor_scores
        result["signals"]      = signals
        result["decision"]     = decision
        result["dec_col"]      = dec_col
        result["dec_reason"]   = dec_reason
        result["score_col"]    = dec_col
        result["n_bull"] = sum(1 for v in factor_scores.values() if v >= 65)
        result["n_bear"] = sum(1 for v in factor_scores.values() if v <= 40)
    except Exception:
        pass

    try:
        result["ml5"]  = _ml_predict(_df, horizon=5)
        result["ml10"] = _ml_predict(_df, horizon=10)
        result["ml20"] = _ml_predict(_df, horizon=20)
    except Exception:
        pass

    try:
        result["ana5"]  = _historical_analogy(_df, k=25, horizon=5)
        result["ana10"] = _historical_analogy(_df, k=25, horizon=10)
        result["ana20"] = _historical_analogy(_df, k=25, horizon=20)
    except Exception:
        pass

    try:
        fp, sp, r2 = _forecast(_df, days=20)
        result["forecast_prices"] = fp
        result["slope_pct"]       = float(sp)
        result["r2"]              = float(r2)
    except Exception:
        pass

    return result


# ══════════════════════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=180, show_spinner=False)
def _ai_chart(cache_key, _df, cp, forecast_prices):
    try:
        from gemini_tab import _build_chart, _find_levels, _fibonacci
        supports, resistances = [], []
        try:
            resistances, supports = _find_levels(_df)
        except Exception:
            pass
        fibs = {}
        try:
            fibs = _fibonacci(_df)
        except Exception:
            pass
        return _build_chart(_df, cp, supports, resistances, fibs, forecast_prices)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TAB
# ══════════════════════════════════════════════════════════════════════════════

def strategy_lab_tab(
    df, symbol_input, stock_name, latest, current_price,
    period_change, period_high, period_low, annual_vol,
    current_regime, adx_current, rsi_current, atr_pct,
    price_vs_ema20, price_vs_ema200, recent_5d_change, recent_20d_change,
):
    cp = float(current_price)
    if len(df) < 30:
        st.warning("Need at least 30 bars for AI analysis.")
        return

    latest_dict = latest.to_dict() if hasattr(latest, "to_dict") else dict(latest)
    ck = _frame_key(df)

    with st.spinner("Running AI analysis…"):
        ai = _ai_compute(ck, df, latest_dict, cp)

    score      = ai["score"]
    dec        = ai["decision"]
    dec_col    = ai["dec_col"]
    dec_reason = ai["dec_reason"]
    factors    = ai["factor_scores"]
    signals    = ai["signals"]
    slope_pct  = ai["slope_pct"]
    r2         = ai["r2"]
    n_bull     = ai["n_bull"]
    n_bear     = ai["n_bear"]

    # Only BUY or WAIT shown (long-only)
    if dec in ("BUY", "WEAK BUY"):
        display_dec = "BUY"
        display_col = BULL
    else:
        display_dec = "WAIT"
        display_col = NEUT

    # Score quality
    if score >= 80:   sq = "Very Strong"
    elif score >= 65: sq = "Strong"
    elif score >= 52: sq = "Moderate"
    elif score >= 40: sq = "Weak"
    else:             sq = "Very Weak"

    # Forecast direction
    fp = ai["forecast_prices"]
    if fp:
        fc_col = BULL if fp[-1] > cp else BEAR
        fc_lbl = f"+{(fp[-1]/cp-1)*100:.1f}% / 20D" if fp[-1] > cp else f"{(fp[-1]/cp-1)*100:.1f}% / 20D"
    else:
        fc_col = NEUT
        fc_lbl = "—"

    # Trend slope
    slope_col = BULL if slope_pct > 0 else (BEAR if slope_pct < 0 else NEUT)

    # ML consensus across horizons
    ml_probs = [
        _safe_float(ai["ml5"].get("up_prob", 50) if ai["ml5"] else 50),
        _safe_float(ai["ml10"].get("up_prob", 50) if ai["ml10"] else 50),
        _safe_float(ai["ml20"].get("up_prob", 50) if ai["ml20"] else 50),
    ]
    ml_avg  = sum(ml_probs) / len(ml_probs)
    ml_col  = BULL if ml_avg >= 55 else (BEAR if ml_avg <= 45 else NEUT)
    ml_lbl  = f"{ml_avg:.0f}% UP"

    # Historical analogue best win rate
    ana_wrs = [
        _safe_float(ai["ana5"].get("w_win_rate", 0) if ai["ana5"] else 0),
        _safe_float(ai["ana10"].get("w_win_rate", 0) if ai["ana10"] else 0),
        _safe_float(ai["ana20"].get("w_win_rate", 0) if ai["ana20"] else 0),
    ]
    best_wr  = max(ana_wrs) if any(x > 0 for x in ana_wrs) else 0
    wr_col   = BULL if best_wr >= 55 else (BEAR if best_wr <= 45 else NEUT)

    # Trade ladder
    _ladder_html = ""
    if display_dec == "BUY":
        try:
            from _levels import price_ladder_html as _plh, compute_structural_levels
            lvls = compute_structural_levels(df, cp, True)
            _ladder_html = _plh(
                lvls["entry"], lvls["stop"], lvls["t1"], lvls["t2"], lvls["t3"],
                True, lvls.get("entry_quality", ""), lvls.get("eq_col", ""),
            )
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # DECISION BOX
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;"
        f"border-top:3px solid {display_col};border-radius:14px;"
        f"overflow:hidden;margin-bottom:1.4rem;'>"

        # Header
        f"<div style='padding:1.6rem 2rem 1.3rem;border-bottom:1px solid #222;'>"
        f"<div style='font-size:0.75rem;color:#999;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>AI Analysis</div>"
        f"<div style='font-size:3rem;font-weight:900;color:{display_col};"
        f"letter-spacing:-1.5px;line-height:1;'>{display_dec}</div>"
        f"<div style='font-size:0.8rem;color:#777;margin-top:0.6rem;"
        f"font-weight:500;line-height:1.6;'>{dec_reason}</div>"
        f"</div>"

        # 6-col metrics
        f"<div style='display:grid;grid-template-columns:repeat(6,1fr);"
        f"border-bottom:1px solid #222;'>"
        + _cell("AI Score", f"{score}/100", display_col, sq)
        + _cell("Bull Factors", str(n_bull), BULL, "of 12 indicators")
        + _cell("Bear Factors", str(n_bear), BEAR, "of 12 indicators")
        + _cell("ML Consensus", ml_lbl, ml_col, "5/10/20-day avg")
        + _cell("Best Win Rate", f"{best_wr:.0f}%", wr_col, "historical analogues")
        + _cell("20D Forecast", fc_lbl, fc_col, f"R²={r2:.2f}", last=True)
        + f"</div>"

        + (_ladder_html if _ladder_html else "")
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHART
    # ══════════════════════════════════════════════════════════════════════════
    chart = _ai_chart(ck, df, cp, fp)
    if chart is not None:
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # FACTOR SCORES + SIGNALS  — two-column layout
    # ══════════════════════════════════════════════════════════════════════════
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        # Factor breakdown card
        _factor_bars_html = "".join(
            _factor_bar(k, v) for k, v in factors.items()
        ) if factors else "<div style='font-size:0.78rem;color:#aaa;'>No factor data.</div>"

        st.markdown(
            f"<div style='background:#181818;border:1px solid #232323;"
            f"border-top:3px solid {PURP};border-radius:14px;"
            f"overflow:hidden;margin-bottom:1.2rem;'>"
            f"<div style='padding:1rem 1.2rem;border-bottom:1px solid #222;'>"
            f"<div style='font-size:0.72rem;color:#888;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>12-Factor Breakdown</div>"
            f"</div>"
            f"<div style='padding:1rem 1.2rem;'>"
            + _factor_bars_html +
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_right:
        # Signals card
        bull_sigs = [s for s in signals if s[2] == BULL or (len(s) > 3 and s[3] == BULL)]
        bear_sigs = [s for s in signals if s[2] == BEAR or (len(s) > 3 and s[3] == BEAR)]
        neut_sigs = [s for s in signals if s not in bull_sigs and s not in bear_sigs]

        def _sig_html(sigs):
            if not sigs:
                return "<div style='font-size:0.78rem;color:#aaa;padding:0.3rem 0;'>None detected</div>"
            # signals are (icon, title, detail, color) tuples
            return "".join(
                _signal_row(
                    s[0] if len(s) > 0 else "·",
                    s[1] if len(s) > 1 else "",
                    s[2] if len(s) > 2 else "",
                    s[3] if len(s) > 3 else NEUT,
                )
                for s in sigs[:5]
            )

        # Flatten all signals for display (they come as (icon,title,detail,color))
        all_sigs_html = ""
        if signals:
            all_sigs_html = "".join(
                _signal_row(s[0], s[1], s[2] if len(s) > 2 else "", s[3] if len(s) > 3 else NEUT)
                for s in signals[:8]
            )
        else:
            all_sigs_html = "<div style='font-size:0.78rem;color:#aaa;padding:0.3rem 0;'>No signals generated.</div>"

        st.markdown(
            f"<div style='background:#181818;border:1px solid #232323;"
            f"border-top:3px solid {INFO};border-radius:14px;"
            f"overflow:hidden;margin-bottom:1.2rem;'>"
            f"<div style='padding:1rem 1.2rem;border-bottom:1px solid #222;'>"
            f"<div style='font-size:0.72rem;color:#888;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Active Signals</div>"
            f"</div>"
            f"<div style='padding:0.5rem 1.2rem 1rem;'>"
            + all_sigs_html +
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # ML + ANALOGUE HORIZON CARDS  — 3 columns
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;"
        f"border-top:3px solid {GOLD};border-radius:14px;"
        f"overflow:hidden;margin-bottom:1.2rem;'>"

        f"<div style='padding:0.9rem 1.2rem;border-bottom:1px solid #222;'>"
        f"<div style='font-size:0.72rem;color:#888;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;'>ML Prediction &amp; Historical Analogues by Horizon</div>"
        f"</div>"

        f"<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;"
        f"padding:1rem 1.2rem;'>"
        + _horizon_card("5-Day",  ai["ml5"],  ai["ana5"],  cp)
        + _horizon_card("10-Day", ai["ml10"], ai["ana10"], cp)
        + _horizon_card("20-Day", ai["ml20"], ai["ana20"], cp)
        + f"</div>"
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # TREND REGRESSION CARD
    # ══════════════════════════════════════════════════════════════════════════
    if slope_pct != 0.0:
        st.markdown(
            f"<div style='background:#181818;border:1px solid #232323;"
            f"border-top:3px solid {slope_col};border-radius:14px;"
            f"overflow:hidden;margin-bottom:1.2rem;'>"

            f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
            f"border-bottom:1px solid #222;'>"
            + _cell("Regression Slope", f"{slope_pct:+.3f}% / day", slope_col,
                    "60-day log-linear fit")
            + _cell("Fit Quality R²", f"{r2:.3f}",
                    BULL if r2 >= 0.75 else (NEUT if r2 >= 0.5 else BEAR),
                    "1.0 = perfect trend")
            + _cell("20-Day Projection", fc_lbl, fc_col,
                    "from regression line", last=True)
            + f"</div>"
            + f"</div>",
            unsafe_allow_html=True,
        )
