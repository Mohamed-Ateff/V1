import hashlib
import html

import pandas as pd
import streamlit as st

from signal_engine import detect_signals
from ui_helpers import info_icon, insight_toggle


BULL = "#4caf50"
BEAR = "#f44336"
NEUT = "#ff9800"
INFO = "#2196f3"
PURP = "#9c27b0"
GOLD = "#FFD700"
BG = "#181818"
BG2 = "#212121"
BDR = "#303030"


def _hex_rgba(hex_color, alpha=0.12):
    hc = str(hex_color).strip().lstrip("#")
    if len(hc) != 6:
        return f"rgba(127,127,127,{alpha})"
    red = int(hc[:2], 16)
    green = int(hc[2:4], 16)
    blue = int(hc[4:], 16)
    return f"rgba({red},{green},{blue},{alpha})"


def _escape(value):
    return html.escape(str(value))


def _lab_palette():
    palette = st.session_state.get("theme_palette", {})
    return {
        "panel": palette.get("panel", BG),
        "panel_alt": palette.get("panel_alt", BG2),
        "text": palette.get("text", "#ffffff"),
        "muted": palette.get("muted", "#9e9e9e"),
        "border": palette.get("border", BDR),
    }


def _inject_lab_css():
    palette = _lab_palette()
    panel = palette["panel"]
    panel_alt = palette["panel_alt"]
    text = palette["text"]
    muted = palette["muted"]
    border = palette["border"]
    st.markdown(
        f"""
        <style>
        .slab-hero {{
            background:{panel};
            border:1px solid {border};
            border-radius:20px;
            padding:1.35rem 1.4rem 1.2rem 1.4rem;
            margin-bottom:0.9rem;
            overflow:hidden;
        }}
        .slab-eyebrow {{
            font-size:0.66rem;
            color:{INFO};
            font-weight:900;
            text-transform:uppercase;
            letter-spacing:1px;
            margin-bottom:0.28rem;
        }}
        .slab-hero-grid {{
            display:grid;
            grid-template-columns:minmax(0, 1.4fr) minmax(280px, 0.95fr);
            gap:1rem;
            align-items:stretch;
        }}
        .slab-callout-top {{
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:0.8rem;
            flex-wrap:wrap;
            margin-bottom:0.9rem;
        }}
        .slab-title {{
            font-size:1.45rem;
            font-weight:900;
            color:{text};
            line-height:1.15;
            margin-bottom:0.35rem;
        }}
        .slab-subtitle {{
            font-size:0.82rem;
            color:{muted};
            line-height:1.7;
            max-width:760px;
        }}
        .slab-callout {{
            background:{panel_alt};
            border:1px solid {border};
            border-radius:16px;
            padding:1.05rem 1.1rem 1rem 1.1rem;
        }}
        .slab-kicker {{
            font-size:0.64rem;
            color:{muted};
            text-transform:uppercase;
            letter-spacing:0.95px;
            font-weight:800;
            margin-bottom:0.32rem;
        }}
        .slab-callout-heading {{
            font-size:0.82rem;
            color:{text};
            font-weight:800;
            display:flex;
            align-items:center;
            gap:0.35rem;
            letter-spacing:0.2px;
        }}
        .slab-callout-badge {{
            display:inline-flex;
            align-items:center;
            justify-content:center;
            gap:0.35rem;
            padding:0.42rem 0.7rem;
            border-radius:999px;
            border:1px solid transparent;
            font-size:0.7rem;
            font-weight:900;
            letter-spacing:0.3px;
        }}
        .slab-callout-title {{
            font-size:clamp(3.2rem, 7vw, 5rem);
            font-weight:950;
            line-height:0.92;
            letter-spacing:-0.05em;
            margin-bottom:0.8rem;
        }}
        .slab-callout-copy {{
            font-size:0.8rem;
            color:#b9b9b9;
            line-height:1.65;
        }}
        .slab-chip-row {{
            display:flex;
            flex-wrap:wrap;
            gap:0.45rem;
            margin-top:0.75rem;
        }}
        .slab-chip {{
            display:inline-flex;
            align-items:center;
            gap:0.35rem;
            padding:0.36rem 0.62rem;
            border-radius:999px;
            border:1px solid transparent;
            font-size:0.7rem;
            font-weight:800;
            letter-spacing:0.2px;
        }}
        .slab-side-panel {{
            background:{panel_alt};
            border:1px solid {border};
            border-radius:18px;
            padding:1rem 1rem 0.9rem 1rem;
            display:flex;
            flex-direction:column;
            gap:0.7rem;
            height:100%;
        }}
        .slab-side-row {{
            display:flex;
            justify-content:space-between;
            gap:0.8rem;
            padding-bottom:0.58rem;
            border-bottom:1px solid {border};
        }}
        .slab-side-row:last-child {{
            border-bottom:none;
            padding-bottom:0;
        }}
        .slab-side-label {{
            font-size:0.66rem;
            color:{muted};
            text-transform:uppercase;
            letter-spacing:0.7px;
            font-weight:800;
        }}
        .slab-side-value {{
            font-size:0.88rem;
            color:{text};
            font-weight:900;
            text-align:right;
        }}
        .slab-grid {{
            display:grid;
            grid-template-columns:repeat(auto-fit, minmax(165px, 1fr));
            gap:0.55rem;
            margin:0.72rem 0 0.95rem 0;
        }}
        .slab-metric {{
            background:{panel_alt};
            border:1px solid {border};
            border-radius:14px;
            padding:0.95rem 1rem;
        }}
        .slab-metric-label {{
            font-size:0.62rem;
            color:{muted};
            text-transform:uppercase;
            letter-spacing:0.85px;
            font-weight:800;
            margin-bottom:0.35rem;
            display:flex;
            align-items:center;
            gap:0.28rem;
        }}
        .slab-metric-value {{
            font-size:1.38rem;
            font-weight:900;
            line-height:1;
            margin-bottom:0.28rem;
        }}
        .slab-metric-sub {{
            font-size:0.74rem;
            color:{muted};
            line-height:1.5;
        }}
        .slab-section {{
            margin:1rem 0 0.65rem 0;
            display:flex;
            align-items:flex-start;
            gap:0.7rem;
        }}
        .slab-section-bar {{
            width:3px;
            height:1.15rem;
            border-radius:999px;
            margin-top:0.12rem;
        }}
        .slab-section-title {{
            font-size:0.92rem;
            font-weight:900;
            letter-spacing:0.6px;
            text-transform:uppercase;
            color:{text};
        }}
        .slab-section-subtitle {{
            font-size:0.76rem;
            color:{muted};
            margin-top:0.16rem;
            line-height:1.55;
        }}
        .slab-note {{
            background:{panel_alt};
            border:1px solid {border};
            border-radius:14px;
            padding:0.95rem 1rem;
            margin-bottom:0.8rem;
        }}
        .slab-note strong {{ color:{text}; }}
        .slab-card {{
            background:{panel_alt};
            border:1px solid {border};
            border-radius:16px;
            padding:1rem;
            height:100%;
        }}
        .slab-card-label {{
            font-size:0.64rem;
            color:{muted};
            text-transform:uppercase;
            letter-spacing:0.85px;
            font-weight:900;
            margin-bottom:0.38rem;
        }}
        .slab-card-value {{
            font-size:1.16rem;
            font-weight:900;
            line-height:1.2;
            margin-bottom:0.24rem;
        }}
        .slab-card-sub {{
            font-size:0.76rem;
            color:{muted};
            line-height:1.55;
            margin-bottom:0.65rem;
        }}
        .slab-list {{
            margin:0;
            padding-left:1rem;
        }}
        .slab-list li {{
            color:{text};
            font-size:0.76rem;
            line-height:1.6;
            margin-bottom:0.34rem;
        }}
        .slab-list li::marker {{
            color:{muted};
        }}
        .slab-mini {{
            display:flex;
            justify-content:space-between;
            gap:0.8rem;
            padding:0.42rem 0;
            border-top:1px solid {border};
        }}
        .slab-mini:first-of-type {{ border-top:none; padding-top:0; }}
        .slab-mini-label {{
            font-size:0.69rem;
            color:{muted};
            line-height:1.4;
        }}
        .slab-mini-value {{
            font-size:0.78rem;
            color:{text};
            font-weight:800;
            text-align:right;
        }}
        @media (max-width: 950px) {{
            .slab-hero-grid {{ grid-template-columns:1fr; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _metric_card(label, value, color, sub="", tip=""):
    tip_html = f" {info_icon(tip)}" if tip else ""
    sub_html = (
        f"<div class='slab-metric-sub'>{_escape(sub)}</div>"
        if sub else ""
    )
    return (
        f"<div class='slab-metric'>"
        f"<div class='slab-metric-label'>{_escape(label)}{tip_html}</div>"
        f"<div class='slab-metric-value' style='color:{color};text-shadow:0 0 16px {color}33;'>{_escape(value)}</div>"
        f"{sub_html}"
        f"</div>"
    )


def _section_header(title, color, subtitle=""):
    palette = _lab_palette()
    subtitle_html = (
        f"<div class='slab-section-subtitle'>{subtitle}</div>"
        if subtitle else ""
    )
    st.markdown(
        f"<div class='slab-section'>"
        f"<span class='slab-section-bar' style='background:{palette['border']};box-shadow:none;'></span>"
        f"<div><div class='slab-section-title'>{title}</div>{subtitle_html}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _verdict_color(verdict):
    if verdict in ("BUY", "LEAN BULL"):
        return BULL
    if verdict in ("SELL", "LEAN BEAR"):
        return BEAR
    return NEUT


def _direction_from_verdict(verdict):
    if verdict in ("BUY", "LEAN BULL"):
        return "BUY"
    if verdict in ("SELL", "LEAN BEAR"):
        return "SELL"
    return "WAIT"


def _risk_style(rr_value):
    if rr_value >= 2.5:
        return "Strong", BULL
    if rr_value >= 1.6:
        return "Usable", NEUT
    return "Thin", BEAR


def _agreement_style(score):
    if score >= 65:
        return "Aligned", BULL
    if score >= 52:
        return "Mixed", NEUT
    return "Conflicted", BEAR


def _chip(label, value, color):
    return (
        f"<span class='slab-chip' style='color:{color};background:{_hex_rgba(color, 0.10)};border-color:{_hex_rgba(color, 0.25)};'>"
        f"<span>{_escape(label)}</span><span style='color:#f0f0f0;'>{_escape(value)}</span>"
        f"</span>"
    )


def _mini_row(label, value):
    return (
        f"<div class='slab-mini'>"
        f"<div class='slab-mini-label'>{label}</div>"
        f"<div class='slab-mini-value'>{_escape(value)}</div>"
        f"</div>"
    )


def _reason_list(items, empty_message):
    if not items:
        return f"<div class='slab-card-sub'>{_escape(empty_message)}</div>"
    lis = "".join(f"<li>{_escape(item)}</li>" for item in items)
    return f"<ul class='slab-list'>{lis}</ul>"


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _frame_cache_key(df):
    try:
        hashed = pd.util.hash_pandas_object(df, index=True, categorize=True)
        return hashlib.md5(hashed.values.tobytes()).hexdigest()
    except Exception:
        parts = [str(len(df)), str(list(df.columns))]
        if len(df):
            parts.append(str(df.index[-1]))
        for col in ("Open", "High", "Low", "Close", "Volume", "REGIME"):
            if col in df.columns:
                parts.append(str(df[col].tail(10).tolist()))
        return "|".join(parts)


def _load_decision_data(df, current_price):
    from decision_tab import _score_engine

    cached = st.session_state.get("_score_engine_d")
    current_price = float(current_price)
    if isinstance(cached, dict) and abs(_safe_float(cached.get("cp"), current_price) - current_price) < 1e-6:
        return cached

    decision_data = _score_engine(df, current_price)
    st.session_state["_score_engine_d"] = decision_data
    return decision_data


def _top_factor_reasons(decision_data):
    factors = decision_data.get("factors", [])
    supports = sorted(
        [factor for factor in factors if factor.get("pts", 0) > 0],
        key=lambda factor: abs(factor.get("pts", 0)),
        reverse=True,
    )[:3]
    risks = sorted(
        [factor for factor in factors if factor.get("pts", 0) < 0],
        key=lambda factor: abs(factor.get("pts", 0)),
        reverse=True,
    )[:3]
    support_lines = [f"+{factor['pts']}: {factor['name']}" for factor in supports]
    risk_lines = [f"{factor['pts']}: {factor['name']}" for factor in risks]
    return support_lines, risk_lines


def _plain_action_note(decision_data, validator_snapshot, ai_snapshot, backtest_snapshot):
    verdict = decision_data.get("verdict", "WAIT")
    confluence = validator_snapshot.get("score")
    best_win = backtest_snapshot.get("best_win_rate")

    if verdict == "BUY":
        if confluence is not None and confluence >= 60:
            return "BUY is actionable. The engines are aligned enough, so the focus is execution and risk."
        return "BUY bias only. Take it only if the entry stays clean and the risk is controlled."

    if verdict == "SELL":
        if confluence is not None and confluence >= 60:
            return "SELL is actionable. The important part now is execution quality, not more analysis."
        return "SELL bias only. Wait for cleaner weakness before treating it as a high-conviction short."

    if verdict in ("LEAN BULL", "LEAN BEAR"):
        return f"{verdict} only. Watch for confirmation and do not force the trade yet."

    if best_win is not None and best_win >= 58:
        return "History still has edge, but the current chart is not clean enough yet."

    return "No clean edge right now. Wait for clearer structure or better agreement."


@st.cache_data(ttl=180, show_spinner=False)
def _build_ai_snapshot(_df, frame_key, latest_dict, current_price):
    from gemini_tab import _compute_ai_score, _decision_from_score, _historical_analogy, _ml_predict

    snapshot = {
        "score": None,
        "score_color": INFO,
        "decision": "Unavailable",
        "headline": "AI view unavailable",
        "ml_prob": None,
        "ml_direction": "--",
        "ml_accuracy": None,
        "historical_win_rate": None,
        "historical_avg_return": None,
        "historical_count": None,
        "summary_lines": [],
    }

    try:
        ai_score, _, _ = _compute_ai_score(latest_dict, _df, float(current_price))
        ai_decision, ai_color, ai_reason = _decision_from_score(ai_score)
        snapshot["score"] = round(float(ai_score), 1)
        snapshot["score_color"] = ai_color
        snapshot["decision"] = ai_decision
        snapshot["headline"] = ai_reason
        snapshot["summary_lines"].append(f"Fast AI score: {ai_score}/100")
    except Exception:
        pass

    try:
        ml_data = _ml_predict(_df, horizon=10)
        if ml_data:
            snapshot["ml_prob"] = float(ml_data.get("up_prob", 0.0))
            snapshot["ml_direction"] = ml_data.get("direction", "--")
            snapshot["ml_accuracy"] = float(ml_data.get("accuracy", 0.0))
            snapshot["summary_lines"].append(
                f"ML: {snapshot['ml_prob']:.0f}% chance up over {ml_data.get('horizon', 10)} bars"
            )
    except Exception:
        pass

    try:
        analogy = _historical_analogy(_df, k=25, horizon=10)
        if analogy:
            snapshot["historical_win_rate"] = float(analogy.get("w_win_rate", 0.0))
            snapshot["historical_avg_return"] = float(analogy.get("avg_return", 0.0))
            snapshot["historical_count"] = int(analogy.get("n_similar", 0))
            snapshot["summary_lines"].append(
                f"Analogues: {snapshot['historical_win_rate']:.0f}% weighted win rate from {snapshot['historical_count']} similar setups"
            )
    except Exception:
        pass

    return snapshot


@st.cache_data(ttl=180, show_spinner=False)
def _build_validator_snapshot(_df, frame_key, latest_dict, current_price, direction):
    from trade_validator_tab import _run_confluence, _score_confluence

    snapshot = {
        "score": None,
        "label": "Not scored",
        "color": NEUT,
        "agree": 0,
        "conflict": 0,
        "neutral": 0,
        "best_agree": [],
        "best_conflict": [],
        "verdicts": {},
    }

    try:
        results = _run_confluence(_df, latest_dict, float(current_price))
        if direction == "WAIT":
            verdicts = {key: {**eng, "verdict": "neutral"} for key, eng in results.items()}
            score = 50.0
        else:
            score, verdicts = _score_confluence(results, direction)

        snapshot["score"] = float(score)
        label, color = _agreement_style(score)
        snapshot["label"] = label
        snapshot["color"] = color
        snapshot["verdicts"] = verdicts
        snapshot["agree"] = sum(1 for eng in verdicts.values() if eng.get("verdict") == "agree")
        snapshot["conflict"] = sum(1 for eng in verdicts.values() if eng.get("verdict") == "conflict")
        snapshot["neutral"] = sum(1 for eng in verdicts.values() if eng.get("verdict") == "neutral")

        agrees = [eng for eng in verdicts.values() if eng.get("verdict") == "agree"]
        conflicts = [eng for eng in verdicts.values() if eng.get("verdict") == "conflict"]

        agrees = sorted(agrees, key=lambda eng: (eng.get("weight", 0), eng.get("strength") == "strong"), reverse=True)
        conflicts = sorted(conflicts, key=lambda eng: (eng.get("weight", 0), eng.get("strength") == "strong"), reverse=True)

        snapshot["best_agree"] = [f"{eng['label']}: {eng['signal']}" for eng in agrees[:2]]
        snapshot["best_conflict"] = [f"{eng['label']}: {eng['signal']}" for eng in conflicts[:2]]
    except Exception:
        pass

    return snapshot


@st.cache_data(ttl=180, show_spinner=False)
def _build_backtest_snapshot(_df, frame_key):
    from backtest_tab import _IND, _live_signals, _run_bt

    snapshot = {
        "available_count": 0,
        "best_label": "No proven setup",
        "best_win_rate": None,
        "best_return": None,
        "live_label": "No live trigger",
        "live_type": "WAIT",
        "live_color": NEUT,
        "live_detail": "No top strategy is firing in the last 3 bars.",
        "scan_note": "Backtest checks the same historical engine used in the Backtest tab.",
    }

    try:
        signals_df = detect_signals(_df)
        available = [key for key in _IND if f"{key}_Buy" in signals_df.columns]
        snapshot["available_count"] = len(available)
        if not available:
            snapshot["scan_note"] = "Not enough signal columns were available to run the proof layer."
            return snapshot

        all_results = {}
        for indicator_key in available:
            result = _run_bt(_df, signals_df, [indicator_key])
            if result:
                all_results[indicator_key] = result

        top_singles = sorted(all_results.values(), key=lambda item: item["score"], reverse=True)[:6]
        top_keys = [result["inds"][0] for result in top_singles]
        for left in range(len(top_keys)):
            for right in range(left + 1, len(top_keys)):
                pair = [top_keys[left], top_keys[right]]
                result = _run_bt(_df, signals_df, pair, require_all=True)
                if result:
                    all_results["+".join(pair)] = result

        ranked = sorted(all_results.items(), key=lambda item: item[1]["score"], reverse=True)
        if not ranked:
            snapshot["scan_note"] = "The proof layer could not find enough historical trades for a reliable edge read."
            return snapshot

        best_key, best_result = ranked[0]
        best_names = " + ".join(_IND.get(ind, ind) for ind in best_result["inds"])
        snapshot["best_label"] = best_names
        snapshot["best_win_rate"] = float(best_result.get("win_rate", 0.0))
        snapshot["best_return"] = float(best_result.get("total_return", 0.0))

        for _, result in ranked[:10]:
            live_hits = _live_signals(signals_df, result["inds"])
            buy_hits = [hit for hit in live_hits if hit.get("type") == "BUY"]
            sell_hits = [hit for hit in live_hits if hit.get("type") == "SELL"]
            is_combo = len(result["inds"]) > 1

            live_type = None
            if is_combo and len(buy_hits) == len(result["inds"]):
                live_type = "BUY"
            elif is_combo and len(sell_hits) == len(result["inds"]):
                live_type = "SELL"
            elif not is_combo and buy_hits:
                live_type = "BUY"
            elif not is_combo and sell_hits:
                live_type = "SELL"

            if live_type:
                live_names = " + ".join(_IND.get(ind, ind) for ind in result["inds"])
                snapshot["live_label"] = f"{live_type} now"
                snapshot["live_type"] = live_type
                snapshot["live_color"] = BULL if live_type == "BUY" else BEAR
                snapshot["live_detail"] = (
                    f"{live_names} is active now. Historical win rate {result.get('win_rate', 0):.0f}% over {result.get('total_trades', 0)} trades."
                )
                break

        if snapshot["live_label"] == "No live trigger":
            snapshot["live_detail"] = "No top-ranked setup is active now, so the proof layer is only giving context, not a trigger."
    except Exception:
        pass

    return snapshot


def _render_hero(decision_data, ai_snapshot, validator_snapshot, backtest_snapshot):
    palette = _lab_palette()
    verdict = decision_data.get("verdict", "WAIT")
    verdict_color = _verdict_color(verdict)
    confidence = decision_data.get("confidence", 0)
    _, rr_color = _risk_style(_safe_float(decision_data.get("rr2"), 0.0))
    regime = decision_data.get("regime", "N/A")
    backtest_wr = backtest_snapshot.get("best_win_rate")
    backtest_wr_text = f"{backtest_wr:.0f}%" if backtest_wr is not None else "--"
    validator_text = (
        f"{validator_snapshot['score']:.0f}/100"
        if validator_snapshot.get("score") is not None else "--"
    )
    ai_score_text = f"{ai_snapshot['score']:.0f}/100" if ai_snapshot.get("score") is not None else "--"
    entry_quality = decision_data.get("entry_quality", "N/A") or "N/A"
    entry_quality_color = decision_data.get("eq_col") or INFO

    st.markdown(
        f"<div class='slab-hero'>"
        f"<div class='slab-hero-grid'>"
        f"<div class='slab-callout'>"
        f"<div class='slab-callout-top'>"
        f"<div>"
        f"<div class='slab-kicker'>Best Call Now {info_icon('Fastest decision output from the engine for the current chart.')}</div>"
        f"<div class='slab-callout-heading'>Decision {info_icon('Primary action generated from the decision engine after scoring the current setup.')}</div>"
        f"</div>"
        f"<div class='slab-callout-badge' style='color:{verdict_color};border-color:{_hex_rgba(verdict_color, 0.32)};background:{_hex_rgba(verdict_color, 0.12)};'>Confidence {confidence}%</div>"
        f"</div>"
        f"<div class='slab-callout-title' style='color:{verdict_color};text-shadow:0 0 28px {verdict_color}33;'>{_escape(verdict)}</div>"
        f"<div class='slab-chip-row'>"
        f"{_chip('Regime', regime, palette['muted'])}"
        f"{_chip('R:R to T2', f"1:{_safe_float(decision_data.get('rr2'), 0.0):.1f}", rr_color)}"
        f"{_chip('Entry quality', entry_quality, entry_quality_color)}"
        f"</div></div>"
        f"<div class='slab-side-panel'>"
        f"<div class='slab-side-row'><span class='slab-side-label'>Decision score {info_icon('Net strength of the decision engine after weighting all active factors.')}</span><span class='slab-side-value' style='color:{verdict_color};'>{decision_data.get('pct', 0):+.1f}</span></div>"
        f"<div class='slab-side-row'><span class='slab-side-label'>AI read {info_icon('Fast AI score built from the AI analysis engine.')}</span><span class='slab-side-value'>{ai_score_text}</span></div>"
        f"<div class='slab-side-row'><span class='slab-side-label'>Validator agreement {info_icon('How much the separate engines agree with the current trade direction.')}</span><span class='slab-side-value'>{validator_text}</span></div>"
        f"<div class='slab-side-row'><span class='slab-side-label'>Best proven win rate {info_icon('Top historical setup from the proof layer. This is context, not a guarantee.')}</span><span class='slab-side-value'>{backtest_wr_text}</span></div>"
        f"</div>"
        f"</div>"
        f"<div class='slab-grid'>"
        f"{_metric_card('Bull vs Bear', f"{decision_data.get('bull_n', 0)} / {decision_data.get('bear_n', 0)}", verdict_color, tip='How many factors are helping vs hurting the current setup')}"
        f"{_metric_card('Risk', f"{_safe_float(decision_data.get('risk_pct'), 0.0):.1f}%", BEAR if _safe_float(decision_data.get('risk_pct'), 0.0) > 2.5 else NEUT, tip='Distance from entry to stop')}"
        f"{_metric_card('Validator', validator_snapshot.get('label', '--'), validator_snapshot.get('color', NEUT), tip='How much the separate engines agree with the current trade direction.')}"
        f"{_metric_card('Live Proof', backtest_snapshot.get('live_label', '--'), backtest_snapshot.get('live_color', NEUT), tip='Whether a strong historical setup is active right now.')}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_trade_plan(decision_data):
    verdict = decision_data.get("verdict", "WAIT")
    if verdict == "WAIT":
        st.markdown(
            "<div class='slab-note'><strong>No active trade plan.</strong> Verdict is WAIT.</div>",
            unsafe_allow_html=True,
        )
        return

    from _levels import price_ladder_html

    st.markdown(
        price_ladder_html(
            _safe_float(decision_data.get("cp"), 0.0),
            _safe_float(decision_data.get("stop"), 0.0),
            _safe_float(decision_data.get("t1"), 0.0),
            _safe_float(decision_data.get("t2"), 0.0),
            _safe_float(decision_data.get("t3"), 0.0),
            bool(decision_data.get("is_bullish")),
            decision_data.get("entry_quality", "") or "",
            decision_data.get("eq_col", "") or "",
        ),
        unsafe_allow_html=True,
    )


def _render_reason_cards(decision_data):
    palette = _lab_palette()
    support_lines, risk_lines = _top_factor_reasons(decision_data)
    _section_header("Why This Call", INFO)

    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>What Helps</div>"
            f"<div class='slab-card-value' style='color:{BULL};'>Support</div>"
            f"{_reason_list(support_lines, 'No positive drivers are strong enough yet.')}</div>",
            unsafe_allow_html=True,
        )
    with right_col:
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>What Can Break It</div>"
            f"<div class='slab-card-value' style='color:{BEAR};'>Risks</div>"
            f"{_reason_list(risk_lines, 'No major opposing factor is active right now.')}</div>",
            unsafe_allow_html=True,
        )


def _render_evidence_cards(ai_snapshot, validator_snapshot, backtest_snapshot):
    palette = _lab_palette()
    _section_header("Evidence", INFO)

    ai_prob = ai_snapshot.get("ml_prob")
    ai_prob_text = f"{ai_prob:.0f}% up" if ai_prob is not None else "--"
    history_wr = ai_snapshot.get("historical_win_rate")
    history_text = f"{history_wr:.0f}%" if history_wr is not None else "--"
    validator_score = validator_snapshot.get("score")
    validator_text = f"{validator_score:.0f}/100" if validator_score is not None else "--"
    backtest_wr = backtest_snapshot.get("best_win_rate")
    backtest_text = f"{backtest_wr:.0f}%" if backtest_wr is not None else "--"

    col_ai, col_validator, col_backtest = st.columns(3)
    with col_ai:
        ai_lines = []
        if ai_snapshot.get("ml_accuracy") is not None:
            ai_lines.append(_mini_row("ML accuracy", f"{ai_snapshot['ml_accuracy']:.0f}%"))
        if ai_snapshot.get("historical_count") is not None:
            ai_lines.append(_mini_row("Similar setups", str(ai_snapshot["historical_count"])))
        if ai_snapshot.get("historical_avg_return") is not None:
            ai_lines.append(_mini_row("Avg analogue return", f"{ai_snapshot['historical_avg_return']:+.2f}%"))
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>Forecast</div>"
            f"<div class='slab-card-value' style='color:{ai_snapshot.get('score_color', INFO)};'>{_escape(ai_snapshot.get('decision', 'Unavailable'))}</div>"
            f"<div class='slab-card-sub'>{_escape(ai_snapshot.get('headline', 'AI view unavailable'))}</div>"
            f"{_mini_row('Fast AI score', f"{ai_snapshot['score']:.0f}/100" if ai_snapshot.get('score') is not None else '--')}"
            f"{_mini_row('10-bar ML read', ai_prob_text)}"
            f"{_mini_row('Analogue win rate', history_text)}"
            f"{''.join(ai_lines)}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_validator:
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>Agreement</div>"
            f"<div class='slab-card-value' style='color:{validator_snapshot.get('color', NEUT)};'>{_escape(validator_snapshot.get('label', '--'))}</div>"
            f"{_mini_row('Confluence score', validator_text)}"
            f"{_mini_row('Agree', str(validator_snapshot.get('agree', 0)))}"
            f"{_mini_row('Conflict', str(validator_snapshot.get('conflict', 0)))}"
            f"{_mini_row('Neutral', str(validator_snapshot.get('neutral', 0)))}"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_backtest:
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>Proof</div>"
            f"<div class='slab-card-value' style='color:{backtest_snapshot.get('live_color', GOLD)};'>{_escape(backtest_snapshot.get('live_label', '--'))}</div>"
            f"<div class='slab-card-sub'>{_escape(backtest_snapshot.get('live_detail', ''))}</div>"
            f"{_mini_row('Best proven setup', backtest_snapshot.get('best_label', '--'))}"
            f"{_mini_row('Best win rate', backtest_text)}"
            f"{_mini_row('Total return', f"{backtest_snapshot['best_return']:+.1f}%" if backtest_snapshot.get('best_return') is not None else '--')}"
            f"{_mini_row('Signals scanned', str(backtest_snapshot.get('available_count', 0)))}"
            f"</div>",
            unsafe_allow_html=True,
        )


def _render_validator_conflicts(validator_snapshot):
    palette = _lab_palette()
    _section_header("Agreement Detail", BULL)

    agree_text = _reason_list(
        validator_snapshot.get("best_agree", []),
        "No major engine is strongly backing the current direction yet.",
    )
    conflict_text = _reason_list(
        validator_snapshot.get("best_conflict", []),
        "No major engine is strongly fighting the current direction.",
    )

    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>Strongest Agreement</div>"
            f"<div class='slab-card-value' style='color:{BULL};'>Backing the trade</div>"
            f"{agree_text}</div>",
            unsafe_allow_html=True,
        )
    with right_col:
        st.markdown(
            f"<div class='slab-card'>"
            f"<div class='slab-card-label' style='color:{palette['muted']};'>Strongest Conflict</div>"
            f"<div class='slab-card-value' style='color:{BEAR};'>Fighting the trade</div>"
            f"{conflict_text}</div>",
            unsafe_allow_html=True,
        )


def _render_ai_section(
    df,
    symbol_input,
    stock_name,
    latest,
    current_price,
    period_change,
    period_high,
    period_low,
    annual_vol,
    current_regime,
    adx_current,
    rsi_current,
    atr_pct,
    price_vs_ema20,
    price_vs_ema200,
    recent_5d_change,
    recent_20d_change,
):
    from gemini_tab import gemini_tab

    ai_key = f"_ai_loaded_{symbol_input}"
    if st.session_state.get(ai_key):
        gemini_tab(
            df,
            symbol_input,
            stock_name,
            latest,
            current_price,
            period_change,
            period_high,
            period_low,
            annual_vol,
            current_regime,
            adx_current,
            rsi_current,
            atr_pct,
            price_vs_ema20,
            price_vs_ema200,
            recent_5d_change,
            recent_20d_change,
        )
        return

    if st.button("Load Full AI Forecast", key=f"strategy_lab_ai_run_{symbol_input}", type="primary"):
        st.session_state[ai_key] = True
        st.rerun()


def strategy_lab_tab(
    df,
    symbol_input,
    stock_name,
    latest,
    current_price,
    period_change,
    period_high,
    period_low,
    annual_vol,
    current_regime,
    adx_current,
    rsi_current,
    atr_pct,
    price_vs_ema20,
    price_vs_ema200,
    recent_5d_change,
    recent_20d_change,
):
    _inject_lab_css()

    latest_dict = latest.to_dict() if hasattr(latest, "to_dict") else dict(latest)
    current_price = float(current_price)
    frame_key = _frame_cache_key(df)
    decision_data = _load_decision_data(df, current_price)
    direction = _direction_from_verdict(decision_data.get("verdict", "WAIT"))

    with st.spinner("Building the decision board..."):
        ai_snapshot = _build_ai_snapshot(df, frame_key, latest_dict, current_price)
        validator_snapshot = _build_validator_snapshot(df, frame_key, latest_dict, current_price, direction)
        backtest_snapshot = _build_backtest_snapshot(df, frame_key)

    _render_hero(decision_data, ai_snapshot, validator_snapshot, backtest_snapshot)

    _render_trade_plan(decision_data)
    _render_reason_cards(decision_data)
    _render_evidence_cards(ai_snapshot, validator_snapshot, backtest_snapshot)
    _render_validator_conflicts(validator_snapshot)

    _section_header("Deep Tools", PURP)
    deep_ai, deep_validator, deep_backtest = st.tabs(["AI Forecast", "Validator Detail", "Backtest Detail"])

    with deep_ai:
        _render_ai_section(
            df,
            symbol_input,
            stock_name,
            latest,
            current_price,
            period_change,
            period_high,
            period_low,
            annual_vol,
            current_regime,
            adx_current,
            rsi_current,
            atr_pct,
            price_vs_ema20,
            price_vs_ema200,
            recent_5d_change,
            recent_20d_change,
        )

    with deep_validator:
        from trade_validator_tab import trade_validator_tab

        trade_validator_tab(df, latest, current_price)

    with deep_backtest:
        from backtest_tab import backtest_tab

        backtest_tab(df, current_price)