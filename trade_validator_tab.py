"""
Trade Validator — Auto Decision Engine
Automatically validates the current trade opportunity against every analytical
engine. No manual inputs — direction and levels are derived directly from the
Decision Intelligence engine (same as Decision tab).
"""

import streamlit as st
import numpy as np
import pandas as pd
from ui_helpers import insight_toggle

# ── Design tokens (match rest of app) ────────────────────────────────────────
BULL  = "#4caf50"
BEAR  = "#f44336"
NEUT  = "#ff9800"
INFO  = "#2196f3"
PURP  = "#9c27b0"
GOLD  = "#FFD700"
BG    = "#181818"
BG2   = "#212121"
BDR   = "#303030"


# ── UI helpers ────────────────────────────────────────────────────────────────
def _sec(title, color=INFO):
    return (
        f"<div style='display:flex;align-items:center;gap:0.6rem;"
        f"margin:2.2rem 0 1rem;padding:0;'>"
        f"<div style='width:3px;height:18px;border-radius:2px;background:{color};"
        f"box-shadow:0 0 8px {color}44;'></div>"
        f"<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
        f"text-transform:uppercase;letter-spacing:0.8px;'>{title}</span></div>"
    )


def _glowbar(pct, color=BULL, height="7px"):
    pct = max(0, min(100, float(pct)))
    return (
        f"<div style='background:#1a1a1a;border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:linear-gradient(90deg,{color}cc,{color});border-radius:999px;"
        f"box-shadow:0 0 8px {color}55;'>"
        f"</div></div>"
    )


def _row(lbl, val, col="#fff", big=False):
    fs = "1.1rem" if big else "0.85rem"
    return (
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:0.42rem 0;border-bottom:1px solid #272727;'>"
        f"<span style='font-size:0.62rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:0.5px;font-weight:700;'>{lbl}</span>"
        f"<span style='font-size:{fs};font-weight:900;color:{col};'>{val}</span>"
        f"</div>"
    )


# ── Engine runner ─────────────────────────────────────────────────────────────
def _run_confluence(df, latest, current_price):
    """Run all analytical engines and return structured per-engine results."""
    results = {}
    cp = float(current_price)

    # ── Engine 1: AI Score (12 technical factors) ────────────────────────────
    try:
        from gemini_tab import _compute_ai_score, _decision_from_score
        score, _, _ = _compute_ai_score(latest, df, cp)
        decision, dec_col, dec_reason = _decision_from_score(score)

        if   score >= 65: ai_dir, ai_str = 'BUY',     'strong'
        elif score >= 52: ai_dir, ai_str = 'BUY',     'weak'
        elif score <= 35: ai_dir, ai_str = 'SELL',    'strong'
        elif score <= 48: ai_dir, ai_str = 'SELL',    'weak'
        else:             ai_dir, ai_str = 'NEUTRAL',  'none'

        results['ai_score'] = {
            'label':      'AI Score  (12 Factors)',
            'signal':     f"{decision} — {score}/100",
            'signal_col': dec_col,
            'direction':  ai_dir,
            'strength':   ai_str,
            'detail':     dec_reason,
            'weight':     25,
        }
    except Exception as e:
        results['ai_score'] = {
            'label': 'AI Score', 'signal': 'Error', 'direction': 'NEUTRAL',
            'strength': 'none', 'weight': 25, 'signal_col': '#555', 'detail': str(e),
        }

    # ── Engine 2: ML Ensemble (5-model, 10-day) ──────────────────────────────
    try:
        from gemini_tab import _ml_predict
        ml = _ml_predict(df, horizon=10)
        if ml:
            prob = ml['up_prob']
            if   prob >= 60: ml_dir, ml_str = 'BUY',     'strong'
            elif prob >= 55: ml_dir, ml_str = 'BUY',     'weak'
            elif prob <= 40: ml_dir, ml_str = 'SELL',    'strong'
            elif prob <= 45: ml_dir, ml_str = 'SELL',    'weak'
            else:            ml_dir, ml_str = 'NEUTRAL',  'none'

            results['ml'] = {
                'label':      'ML Ensemble  (5 Models · 10-Day)',
                'signal':     f"{prob:.0f}% chance UP",
                'signal_col': BULL if prob >= 55 else (BEAR if prob <= 45 else NEUT),
                'direction':  ml_dir,
                'strength':   ml_str,
                'detail':     f"{ml['model_name']} · {ml['n_features']} features · {ml['cv_folds']}-fold CV",
                'weight':     25,
            }
        else:
            results['ml'] = {
                'label': 'ML Ensemble', 'signal': 'Insufficient data', 'direction': 'NEUTRAL',
                'strength': 'none', 'weight': 25, 'signal_col': '#555', 'detail': 'Need >=60 bars',
            }
    except Exception as e:
        results['ml'] = {
            'label': 'ML Ensemble', 'signal': 'Error', 'direction': 'NEUTRAL',
            'strength': 'none', 'weight': 25, 'signal_col': '#555', 'detail': str(e),
        }

    # ── Engine 3: Historical Analogues (KNN, 10-day) ─────────────────────────
    try:
        from gemini_tab import _historical_analogy
        ana = _historical_analogy(df, k=25, horizon=10)
        if ana:
            wr = ana['w_win_rate']
            if   wr >= 62: ana_dir, ana_str = 'BUY',     'strong'
            elif wr >= 55: ana_dir, ana_str = 'BUY',     'weak'
            elif wr <= 38: ana_dir, ana_str = 'SELL',    'strong'
            elif wr <= 45: ana_dir, ana_str = 'SELL',    'weak'
            else:          ana_dir, ana_str = 'NEUTRAL',  'none'

            results['historical'] = {
                'label':      'Historical Analogues  (KNN - 25 setups)',
                'signal':     f"{wr:.0f}% win rate  ({ana['n_up']} up / {ana['n_down']} dn of {ana['n_similar']})",
                'signal_col': BULL if wr >= 55 else (BEAR if wr <= 45 else NEUT),
                'direction':  ana_dir,
                'strength':   ana_str,
                'detail':     (f"Median: {ana['median_return']:+.1f}%  |  "
                               f"Best: +{ana['best_case']:.1f}%  |  "
                               f"Worst: {ana['worst_case']:.1f}%"),
                'weight':     20,
            }
        else:
            results['historical'] = {
                'label': 'Historical Analogues', 'signal': 'No data', 'direction': 'NEUTRAL',
                'strength': 'none', 'weight': 20, 'signal_col': '#555', 'detail': 'Insufficient history',
            }
    except Exception as e:
        results['historical'] = {
            'label': 'Historical Analogues', 'signal': 'Error', 'direction': 'NEUTRAL',
            'strength': 'none', 'weight': 20, 'signal_col': '#555', 'detail': str(e),
        }

    # ── Engine 4: SMC Bias + Engine 5: Market Structure ──────────────────────
    try:
        from smc_tab import (
            _find_swing_points, _market_structure, _liquidity_zones,
            _detect_sweeps, _detect_choch_bos, _find_order_block,
            _find_fvgs, _build_trade_plan,
        )

        df_s = df.copy()
        if "Date" not in df_s.columns:
            df_s = df_s.reset_index()
            if "index" in df_s.columns:
                df_s.rename(columns={"index": "Date"}, inplace=True)
        df_s["Date"] = pd.to_datetime(df_s["Date"])

        sh, sl = _find_swing_points(df_s)
        if len(sh) < 2:
            sh = list(range(0, len(df_s) - 1, max(1, len(df_s) // 8)))
        if len(sl) < 2:
            sl = list(range(0, len(df_s) - 1, max(1, len(df_s) // 8)))

        trend, sh_p, sl_p = _market_structure(df_s, sh, sl)
        bsl, ssl, mh, ml2 = _liquidity_zones(df_s, sh, sl)
        sweep  = _detect_sweeps(df_s, bsl, ssl, mh, ml2)
        choch  = _detect_choch_bos(df_s, sh, sl, trend)
        ob     = _find_order_block(df_s, sh, sl, trend, choch)
        fvg    = _find_fvgs(df_s)
        plan   = _build_trade_plan(df_s, cp, trend, sweep, choch, ob, fvg, bsl, ssl, mh, ml2)

        smc_bias = plan['bias']
        smc_conf = plan['confidence']
        if   smc_bias == 'BUY':  smc_dir, smc_str = 'BUY',     'strong' if smc_conf >= 65 else 'weak'
        elif smc_bias == 'SELL': smc_dir, smc_str = 'SELL',    'strong' if smc_conf >= 65 else 'weak'
        else:                    smc_dir, smc_str = 'NEUTRAL',  'none'

        choch_str = f"{choch['type']} {choch['direction'][:4]}" if choch else 'None'
        ob_str    = ob['direction'] if ob else 'None'

        results['smc'] = {
            'label':      'SMC Analysis',
            'signal':     f"{smc_bias}  -  {smc_conf}% confidence",
            'signal_col': plan['bias_color'],
            'direction':  smc_dir,
            'strength':   smc_str,
            'detail':     f"Score: {plan['score']:+d}  |  CHoCH/BOS: {choch_str}  |  OB: {ob_str}",
            'weight':     20,
        }

        if   trend == 'UPTREND':   tr_dir, tr_str = 'BUY',  'strong'
        elif trend == 'DOWNTREND': tr_dir, tr_str = 'SELL', 'strong'
        else:                      tr_dir, tr_str = 'NEUTRAL', 'none'

        tr_color = BULL if trend == 'UPTREND' else (BEAR if trend == 'DOWNTREND' else NEUT)
        sh_txt = (f"SH: {sh_p[-2][1]:.2f} -> {sh_p[-1][1]:.2f}"
                  if len(sh_p) >= 2 else 'Insufficient swings')

        results['structure'] = {
            'label':      'Market Structure',
            'signal':     trend,
            'signal_col': tr_color,
            'direction':  tr_dir,
            'strength':   tr_str,
            'detail':     sh_txt,
            'weight':     10,
        }

    except Exception as e:
        results['smc'] = {
            'label': 'SMC Analysis', 'signal': 'Error', 'direction': 'NEUTRAL',
            'strength': 'none', 'weight': 20, 'signal_col': '#555', 'detail': str(e),
        }
        results['structure'] = {
            'label': 'Market Structure', 'signal': 'Error', 'direction': 'NEUTRAL',
            'strength': 'none', 'weight': 10, 'signal_col': '#555', 'detail': '',
        }

    return results


def _score_confluence(results, direction):
    """
    Score each engine's agreement with the given trade direction.
    Strong agree/conflict => +/-1.0  |  Weak => +/-0.6  |  Neutral => 0.
    Returns (confluence_score 0-100, verdicts dict).
    """
    verdicts     = {}
    total_weight = 0
    weighted_sum = 0.0

    for key, eng in results.items():
        eng_dir  = eng['direction']
        strength = eng.get('strength', 'none')
        weight   = eng['weight']
        total_weight += weight

        if eng_dir == 'NEUTRAL':
            raw, verdict = 0.0, 'neutral'
        elif eng_dir == direction:
            raw     = 1.0 if strength == 'strong' else 0.6
            verdict = 'agree'
        else:
            raw     = -1.0 if strength == 'strong' else -0.6
            verdict = 'conflict'

        weighted_sum += raw * weight
        verdicts[key] = {**eng, 'verdict': verdict, 'raw_score': raw}

    if total_weight > 0:
        norm = (weighted_sum / total_weight + 1.0) / 2.0 * 100
    else:
        norm = 50.0

    return round(norm, 1), verdicts


# ── Main render ───────────────────────────────────────────────────────────────
def trade_validator_tab(df, latest, current_price):
    """Entry point called from app.py — fully automatic, no user inputs."""

    if df is None or len(df) < 30:
        st.warning("Not enough data. Need at least 30 bars.")
        return
    if hasattr(latest, 'to_dict'):
        latest = latest.to_dict()

    cp = float(current_price)

    # ── Step 1: Get auto-decision from Decision Intelligence engine ──────────
    # Reuse cached result from Decision tab if available (avoids duplicate computation)
    try:
        d = st.session_state.get("_score_engine_d")
        if d is None:
            from decision_tab import _score_engine
            d = _score_engine(df, cp)
    except Exception as e:
        st.error(f"Decision engine error — {e}")
        return

    raw_verdict = d["verdict"]   # BUY / SELL / LEAN BULL / LEAN BEAR / WAIT
    if raw_verdict in ("BUY", "LEAN BULL"):
        direction = "BUY"
    elif raw_verdict in ("SELL", "LEAN BEAR"):
        direction = "SELL"
    else:
        direction = "WAIT"

    # ── Auto-derived trade levels from decision engine ───────────────────────
    entry_p  = cp
    stop_p   = d["stop"]
    t1, t2, t3 = d["t1"], d["t2"], d["t3"]
    risk_per_share   = abs(entry_p - stop_p)
    reward_per_share = abs(t2 - entry_p)
    rr2 = d["rr2"]
    sl_pct = abs(entry_p - stop_p) / entry_p * 100 if entry_p > 0 else 0.0

    # ── Step 2: Run all engines and score confluence ─────────────────────────
    with st.spinner("Running all engines… (first run may take 20-40 s)"):
        try:
            results = _run_confluence(df, latest, cp)
            if direction != "WAIT":
                confluence_score, verdicts = _score_confluence(results, direction)
            else:
                cs_b, vs_b = _score_confluence(results, "BUY")
                cs_s, vs_s = _score_confluence(results, "SELL")
                if cs_b >= cs_s:
                    confluence_score, verdicts = cs_b, vs_b
                else:
                    confluence_score, verdicts = cs_s, vs_s
        except Exception as e:
            import traceback
            st.error(f"Engine error — {e}")
            st.code(traceback.format_exc())
            return

    agree_count    = sum(1 for v in verdicts.values() if v['verdict'] == 'agree')
    conflict_count = sum(1 for v in verdicts.values() if v['verdict'] == 'conflict')
    neutral_count  = sum(1 for v in verdicts.values() if v['verdict'] == 'neutral')
    n_engines      = len(verdicts)

    # ── Step 3: Map to display values ────────────────────────────────────────
    if direction == "BUY":
        if raw_verdict == "BUY":
            act_txt, act_label = "BUY",  "Strong Bullish — All Systems Go"
        else:
            act_txt, act_label = "BUY",  "Lean Bullish — Wait for Confirmation"
        act_col, act_icon = BULL, "+"
    elif direction == "SELL":
        if raw_verdict == "SELL":
            act_txt, act_label = "SELL", "Strong Bearish — All Systems Alert"
        else:
            act_txt, act_label = "SELL", "Lean Bearish — Watch for Breakdown"
        act_col, act_icon = BEAR, "-"
    else:
        act_txt, act_label = "WAIT", "Signals Mixed — No Clear Edge"
        act_col, act_icon  = NEUT,  "="

    cs_col    = BULL if confluence_score >= 70 else (BEAR if confluence_score < 45 else NEUT)
    conf_col  = BULL if d["confidence"] >= 65 else NEUT if d["confidence"] >= 40 else BEAR
    score_pct = max(2, min(100, abs(d["pct"])))

    # ══════════════════════════════════════════════════════════════════════════
    #  HERO — Verdict card
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='background:#1b1b1b;"
        f"border:1px solid #272727;"
        f"border-radius:16px;overflow:hidden;margin-bottom:1.2rem;"
        f"box-shadow:0 4px 24px rgba(0,0,0,0.3);'>"
        f"<div style='padding:1.8rem 2rem;"
        f"background:linear-gradient(135deg,rgba({','.join(str(int(act_col[i:i+2],16)) for i in (1,3,5)) if act_col.startswith('#') and len(act_col)==7 else '85,85,85'},0.07),transparent);'>"
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
        f"flex-wrap:wrap;gap:1.5rem;margin-bottom:1rem;'>"
        f"<div>"
        f"<div style='font-size:0.58rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:1.5px;font-weight:700;margin-bottom:0.35rem;'>Trade Verdict</div>"
        f"<div style='font-size:2.8rem;font-weight:900;color:{act_col};"
        f"line-height:1;letter-spacing:-1px;text-shadow:0 0 20px {act_col}33;'>{act_icon}&nbsp;{act_txt}</div>"
        f"<div style='font-size:0.82rem;color:#888;margin-top:0.5rem;"
        f"font-weight:600;'>{act_label}</div>"
        f"</div>"
        f"<div style='text-align:right;display:flex;gap:2rem;'>"
        f"<div>"
        f"<div style='font-size:0.58rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.25rem;'>Decision Conf.</div>"
        f"<div style='font-size:2.4rem;font-weight:900;color:{conf_col};"
        f"line-height:1;text-shadow:0 0 20px {conf_col}33;'>{d['confidence']}%</div>"
        f"<div style='font-size:0.68rem;color:#555;margin-top:0.15rem;'>"
        f"{d['bull_n']} bull - {d['bear_n']} bear signals</div>"
        f"</div>"
        f"<div>"
        f"<div style='font-size:0.58rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.25rem;'>Engine Confluence</div>"
        f"<div style='font-size:2.4rem;font-weight:900;color:{cs_col};"
        f"line-height:1;text-shadow:0 0 20px {cs_col}33;'>{confluence_score:.0f}%</div>"
        f"<div style='font-size:0.68rem;color:#555;margin-top:0.15rem;'>"
        f"<span style='color:{BULL};'>{agree_count}</span> agree &middot; "
        f"<span style='color:{BEAR};'>{conflict_count}</span> conflict &middot; "
        f"<span style='color:#555;'>{neutral_count}</span> neutral</div>"
        f"</div>"
        f"</div></div>"
        f"<div style='margin-bottom:0.9rem;'>"
        f"<div style='display:flex;justify-content:space-between;"
        f"font-size:0.58rem;color:#555;margin-bottom:0.25rem;'>"
        f"<span>Decision score: {d['total_pts']:+d} pts / +/-{d['total_max']}</span>"
        f"<span style='color:{act_col};font-weight:700;'>{d['pct']:+.0f}%</span></div>"
        + _glowbar(score_pct, act_col, '8px') +
        f"</div>"
        f"</div>"
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ── Price Ladder (BUY only) ──────────────────────────────────────────────
    if direction == "BUY":
        try:
            from _levels import price_ladder_html as _tv_plh
            st.markdown(_tv_plh(d["entry"], d["stop"], d["t1"], d["t2"], d["t3"], True), unsafe_allow_html=True)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #  WHY — Key reasons behind the verdict
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Why This Verdict — Key Factors", act_col), unsafe_allow_html=True)
    insight_toggle(
        "tv_verdict",
        "How is this verdict determined?",
        "<p>The Trade Validator runs the current trade setup through every analytical engine simultaneously "
        "and weighs the evidence. The verdict is determined by the <strong>net weight of all signals</strong>:</p>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Strong BUY</strong> &mdash; 4 or more engines confirm bullish setup with high confidence.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Weak BUY</strong> &mdash; Majority bullish but some engines are neutral or conflicted.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>HOLD / NEUTRAL</strong> &mdash; Mixed signals. The evidence is split; waiting for clarity is recommended.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>AVOID</strong> &mdash; Multiple engines flagging bearish conditions or invalid setup structure.</span></div>"
        "<p>Each key factor listed below shows exactly which part of the analysis pushed the verdict in its direction.</p>"
    )
    
    factors        = d.get("factors", [])
    sorted_factors = sorted(factors, key=lambda f: abs(f["pts"]), reverse=True)
    top_bull       = [f for f in sorted_factors if f["pts"] > 0][:5]
    top_bear       = [f for f in sorted_factors if f["pts"] < 0][:5]
    max_pts        = max((abs(f["pts"]) for f in sorted_factors), default=1)

    def _factor_impact_row(f, color):
        bar_w    = int(abs(f["pts"]) / max(abs(f["max"]), 1) * 100) if f["max"] else 0
        cat_lut  = {
            "Trend": INFO, "Momentum": BULL, "Oscillator": NEUT,
            "Volume": "#26c6da", "Pattern": PURP, "ML": GOLD,
        }
        cat_col = cat_lut.get(f["cat"], "#888")
        return (
            f"<div style='display:flex;align-items:center;gap:0.7rem;"
            f"padding:0.55rem 0.8rem;margin-bottom:0.3rem;"
            f"background:{color}09;border-radius:10px;border:1px solid #272727;'>"
            f"<div style='width:2.2rem;height:2.2rem;border-radius:50%;flex-shrink:0;"
            f"background:{color}22;border:2px solid {color}55;"
            f"display:flex;align-items:center;justify-content:center;'>"
            f"<span style='font-size:0.72rem;font-weight:900;color:{color};'>{f['pts']:+d}</span></div>"
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-size:0.74rem;color:#ddd;font-weight:700;"
            f"line-height:1.3;margin-bottom:0.22rem;'>{f['name']}</div>"
            f"<div style='background:#1a1a1a;border-radius:999px;height:3px;overflow:hidden;'>"
            f"<div style='width:{bar_w}%;height:100%;background:{color};"
            f"border-radius:999px;box-shadow:0 0 6px {color}44;'></div></div></div>"
            f"<div style='text-align:right;flex-shrink:0;'>"
            f"<div style='display:inline-block;background:{cat_col}18;"
            f"border:1px solid {cat_col}44;border-radius:4px;padding:0.1rem 0.45rem;"
            f"font-size:0.49rem;color:{cat_col};font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.5px;margin-bottom:0.1rem;'>{f['cat']}</div>"
            f"<div style='font-size:0.6rem;color:#555;'>{f['pts']:+d} / {f['max']} pts</div>"
            f"</div></div>"
        )

    reason_col1, reason_col2 = st.columns(2, gap="medium")

    with reason_col1:
        if top_bull:
            rows_html = "".join(_factor_impact_row(f, BULL) for f in top_bull)
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #272727;"
                f"border-radius:12px;overflow:hidden;'>"
                f"<div style='padding:1rem 1.1rem;"
                f"background:linear-gradient(135deg,rgba(76,175,80,0.06),transparent);'>"
                f"<div style='font-size:0.57rem;color:{BULL};text-transform:uppercase;"
                f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.65rem;'>"
                f"&#9650; Bullish Evidence &mdash; {len(top_bull)} factors</div>"
                f"{rows_html}</div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #272727;"
                f"border-radius:12px;padding:1rem;text-align:center;"
                f"font-size:0.75rem;color:#555;'>No bullish factors detected</div>",
                unsafe_allow_html=True,
            )

    with reason_col2:
        if top_bear:
            rows_html = "".join(_factor_impact_row(f, BEAR) for f in top_bear)
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #272727;"
                f"border-radius:12px;overflow:hidden;'>"
                f"<div style='padding:1rem 1.1rem;"
                f"background:linear-gradient(135deg,rgba(244,67,54,0.06),transparent);'>"
                f"<div style='font-size:0.57rem;color:{BEAR};text-transform:uppercase;"
                f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.65rem;'>"
                f"&#9660; Risk Evidence &mdash; {len(top_bear)} factors</div>"
                f"{rows_html}</div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #272727;"
                f"border-radius:12px;padding:1rem;text-align:center;"
                f"font-size:0.75rem;color:#555;'>No bearish risk factors detected</div>",
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    #  ENGINE CONSENSUS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Cross-Engine Consensus", INFO), unsafe_allow_html=True)
    insight_toggle(
        "tv_consensus",
        "What is Cross-Engine Consensus?",
        "<p>The platform has 5 independent analytical engines, each looking at the market from a different lens:</p>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Signal Engine</strong> &mdash; Classic technical indicators (EMA, MACD, RSI, Volume).</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Price Action Engine</strong> &mdash; Chart patterns, candlestick formations, Bull/Bear score.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Volume Profile Engine</strong> &mdash; Where institutions traded (POC, VAH, VAL, HPZ).</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>SMC Engine</strong> &mdash; Smart Money Concepts: order blocks, FVGs, liquidity zones.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Regime Engine</strong> &mdash; What market state are we in: Trend, Range, or Volatile?</span></div>"
        "<p>When all 5 engines agree, the trade setup has the highest probability of success. "
        "When they conflict, the validator shows you exactly which engines disagree and why.</p>"
    )
    
    # ── Weighted summary header ──────────────────────────────────────────────
    total_w  = sum(v['weight'] for v in verdicts.values())
    agree_w  = sum(v['weight'] for v in verdicts.values() if v['verdict'] == 'agree')
    conf_w   = sum(v['weight'] for v in verdicts.values() if v['verdict'] == 'conflict')
    agree_bw = round(agree_w / max(total_w, 1) * 100)
    conf_bw  = round(conf_w  / max(total_w, 1) * 100)

    st.markdown(
        f"<div style='background:#1b1b1b;border:1px solid #272727;"
        f"border-radius:14px;overflow:hidden;margin-bottom:1rem;'>"
        f"<div style='padding:1.2rem 1.5rem;'>"
        f"<div style='display:flex;align-items:center;gap:2rem;flex-wrap:wrap;"
        f"margin-bottom:0.85rem;'>"

        # Consensus score
        f"<div>"
        f"<div style='font-size:0.52rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>Weighted Score</div>"
        f"<div style='font-size:2.4rem;font-weight:900;color:{cs_col};line-height:1;"
        f"text-shadow:0 0 20px {cs_col}33;'>"
        f"{confluence_score:.0f}%</div>"
        f"<div style='font-size:0.62rem;color:#555;margin-top:0.1rem;'>"
        f"{agree_count}/{n_engines} engines support the verdict</div>"
        f"</div>"

        # Count pills
        f"<div style='display:flex;gap:1.4rem;'>"
        f"<div style='text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:900;color:{BULL};'>{agree_count}</div>"
        f"<div style='font-size:0.55rem;color:{BULL};text-transform:uppercase;"
        f"letter-spacing:0.5px;'>Agree</div></div>"
        f"<div style='text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:900;color:{BEAR};'>{conflict_count}</div>"
        f"<div style='font-size:0.55rem;color:{BEAR};text-transform:uppercase;"
        f"letter-spacing:0.5px;'>Conflict</div></div>"
        f"<div style='text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:900;color:#555;'>{neutral_count}</div>"
        f"<div style='font-size:0.55rem;color:#555;text-transform:uppercase;"
        f"letter-spacing:0.5px;'>Neutral</div></div>"
        f"</div>"

        # Weighted bar
        f"<div style='flex:1;min-width:180px;'>"
        f"<div style='font-size:0.55rem;color:#555;margin-bottom:0.35rem;'>"
        f"Agreement weight: {agree_w}% &nbsp;·&nbsp; Conflict weight: {conf_w}%</div>"
        f"<div style='display:flex;border-radius:999px;overflow:hidden;height:14px;"
        f"background:#1a1a1a;'>"
        f"<div style='background:{BULL};width:{agree_bw}%;transition:width 0.3s;'></div>"
        f"<div style='background:{BEAR};width:{conf_bw}%;'></div>"
        f"<div style='flex:1;'></div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;"
        f"font-size:0.52rem;color:#444;margin-top:0.2rem;'>"
        f"<span style='color:{BULL};'>&#9650; {agree_bw}% agrees</span>"
        f"<span style='color:{BEAR};'>&#9660; {conf_bw}% conflicts</span>"
        f"</div></div>"
        f"</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── Per-engine rows ───────────────────────────────────────────────────────
    for key in ['ai_score', 'ml', 'historical', 'smc', 'structure']:
        if key not in verdicts:
            continue
        v        = verdicts[key]
        verdict  = v['verdict']
        strength = v.get('strength', 'none')
        if   verdict == 'agree':    v_icon, v_color, v_lbl = '&#10003;', BULL, 'AGREES'
        elif verdict == 'conflict': v_icon, v_color, v_lbl = '&#10007;', BEAR, 'CONFLICTS'
        else:                       v_icon, v_color, v_lbl = '&mdash;',  '#555', 'NEUTRAL'

        str_map  = {'strong': ('Strong',   v_color), 'weak': ('Moderate', NEUT), 'none': ('Flat', '#444')}
        str_lbl, str_col = str_map.get(strength, ('—', '#444'))

        st.markdown(
            f"<div style='background:#1b1b1b;border:1px solid #272727;"
            f"border-radius:12px;overflow:hidden;margin-bottom:0.5rem;'>"
            f"<div style='padding:0.9rem 1.2rem;"
            f"background:linear-gradient(135deg,rgba({','.join(str(int(v_color[i:i+2],16)) for i in (1,3,5)) if v_color.startswith('#') and len(v_color)==7 else '85,85,85'},0.06),transparent);'>"

            f"<div style='display:flex;align-items:center;gap:0.9rem;'>"

            # Status bubble
            f"<div style='width:2.6rem;height:2.6rem;border-radius:50%;flex-shrink:0;"
            f"background:{v_color}20;border:2px solid {v_color};"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:1.1rem;font-weight:900;color:{v_color};'>{v_icon}</div>"

            # Engine info
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-size:0.86rem;font-weight:800;color:#e0e0e0;"
            f"margin-bottom:0.15rem;'>{v['label']}</div>"
            f"<div style='font-size:0.64rem;color:#555;white-space:nowrap;"
            f"overflow:hidden;text-overflow:ellipsis;margin-bottom:0.3rem;'>"
            f"{v.get('detail','—')}</div>"
            # Weight progress bar
            f"<div style='display:flex;align-items:center;gap:0.45rem;'>"
            f"<div style='font-size:0.5rem;color:#444;flex-shrink:0;'>Engine weight</div>"
            f"<div style='flex:1;background:#1a1a1a;border-radius:999px;height:3px;'>"
            f"<div style='width:{v['weight']}%;height:100%;background:{v_color};"
            f"border-radius:999px;box-shadow:0 0 6px {v_color}44;'></div></div>"
            f"<div style='font-size:0.5rem;color:#444;flex-shrink:0;'>{v['weight']}%</div>"
            f"</div>"
            f"</div>"

            # Signal + verdict badge
            f"<div style='text-align:right;flex-shrink:0;min-width:164px;'>"
            f"<div style='font-size:0.9rem;font-weight:800;"
            f"color:{v.get('signal_col','#fff')};margin-bottom:0.25rem;'>"
            f"{v.get('signal','—')}</div>"
            f"<div style='display:flex;gap:0.35rem;justify-content:flex-end;"
            f"align-items:center;flex-wrap:wrap;'>"
            f"<div style='background:{v_color}18;"
            f"border-radius:7px;padding:0.13rem 0.75rem;"
            f"font-size:0.72rem;font-weight:900;color:{v_color};'>{v_lbl}</div>"
            f"<div style='font-size:0.6rem;color:{str_col};font-weight:700;'>{str_lbl}</div>"
            f"</div>"
            f"</div>"
            f"</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='margin-top:1.5rem;padding:0.6rem 1rem;background:#1b1b1b;"
        f"border:1px solid #272727;border-radius:10px;font-size:0.6rem;color:#444;'>"
        f"For informational purposes only. Statistical patterns — not guaranteed outcomes. "
        f"Levels are ATR-derived estimates, not precise entry/exit points."
        f"</div>",
        unsafe_allow_html=True,
    )
