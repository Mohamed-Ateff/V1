"""
Elliott Wave Analysis Tab — Advanced multi-timeframe wave counting engine
with Fibonacci projections, wave probability scoring, and institutional-grade
visualisation for Streamlit.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
CYAN = "#00bcd4"
LIME = "#8bc34a"
PINK = "#F472B6"
CARD = "#1b1b1b"
BDR  = "#272727"
INNER = "#161616"
MUTED = "#606060"
TEXT  = "#e0e0e0"

WAVE_COLORS = {
    1: "#2196f3", 2: "#f44336", 3: "#4caf50", 4: "#ff9800", 5: "#9c27b0",
    "A": "#f44336", "B": "#ff9800", "C": "#9c27b0",
}

FIB_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618]


def _wc(w):
    """Get wave color for a wave dict."""
    lbl = w["label"]
    key = lbl if lbl in WAVE_COLORS else (int(lbl) if lbl.isdigit() else lbl)
    return WAVE_COLORS.get(key, MUTED)


def _hex_rgba(hex_color, alpha=0.12):
    hc = str(hex_color).strip().lstrip("#")
    if len(hc) != 6:
        return f"rgba(127,127,127,{alpha})"
    r, g, b = int(hc[:2], 16), int(hc[2:4], 16), int(hc[4:], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _sec(title, color=INFO):
    return (
        f"<div style='display:flex;align-items:center;gap:0.7rem;"
        f"margin:2rem 0 0.6rem 0;'>"
        f"<div style='width:3px;height:18px;border-radius:2px;background:{color};"
        f"box-shadow:0 0 8px {color}44;'></div>"
        f"<span style='font-size:0.85rem;font-weight:800;text-transform:uppercase;"
        f"letter-spacing:1px;color:#e0e0e0;'>{title}</span></div>"
    )


def _glowbar(pct, color=BULL, height="7px"):
    pct = max(0, min(100, float(pct)))
    return (
        f"<div style='background:#1a1a1a;border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:linear-gradient(90deg,{color}cc,{color});border-radius:999px;"
        f"box-shadow:0 0 8px {color}55;'></div></div>"
    )


def _stat_pill(label, value, color, bg=None, tip=None):
    _bg = bg or INNER
    _tip_html = ""
    if tip:
        _tip_html = (
            f"<span style='position:relative;cursor:help;margin-left:0.25rem;'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:12px;height:12px;border-radius:50%;background:rgba(255,255,255,0.06);"
            f"border:1px solid #333;font-size:0.45rem;color:#666;font-weight:700;'>?</span>"
            f"<span class='ew-tip'>{tip}</span></span>"
        )
    return (
        f"<div style='background:{_bg};border:1px solid {BDR};"
        f"border-radius:10px;padding:0.75rem 0.6rem;text-align:center;'>"
        f"<div style='font-size:0.55rem;color:{MUTED};text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.3rem;'>{label}{_tip_html}</div>"
        f"<div style='font-size:1.15rem;font-weight:900;color:{color};line-height:1;"
        f"text-shadow:0 0 14px {color}33;'>{value}</div></div>"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def _find_zigzag_pivots(df, pct_threshold=5.0):
    """Find zig-zag pivots using percentage threshold."""
    close = df["Close"].values
    dates = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df["Date"])
    n = len(close)
    if n < 10:
        return []

    pivots = []
    last_pivot_idx = 0
    last_pivot_val = close[0]
    last_dir = 0  # 0=unknown, 1=up, -1=down

    for i in range(1, n):
        chg = (close[i] - last_pivot_val) / last_pivot_val * 100

        if last_dir == 0:
            if chg >= pct_threshold:
                pivots.append({"idx": last_pivot_idx, "price": last_pivot_val,
                               "date": dates[last_pivot_idx], "type": "low"})
                last_dir = 1
            elif chg <= -pct_threshold:
                pivots.append({"idx": last_pivot_idx, "price": last_pivot_val,
                               "date": dates[last_pivot_idx], "type": "high"})
                last_dir = -1
        elif last_dir == 1:
            if close[i] > last_pivot_val:
                last_pivot_idx = i
                last_pivot_val = close[i]
            elif chg <= -pct_threshold:
                pivots.append({"idx": last_pivot_idx, "price": last_pivot_val,
                               "date": dates[last_pivot_idx], "type": "high"})
                last_pivot_idx = i
                last_pivot_val = close[i]
                last_dir = -1
        elif last_dir == -1:
            if close[i] < last_pivot_val:
                last_pivot_idx = i
                last_pivot_val = close[i]
            elif chg >= pct_threshold:
                pivots.append({"idx": last_pivot_idx, "price": last_pivot_val,
                               "date": dates[last_pivot_idx], "type": "low"})
                last_pivot_idx = i
                last_pivot_val = close[i]
                last_dir = 1

    # Add last point
    if pivots:
        last_type = "high" if last_dir == 1 else "low"
        pivots.append({"idx": last_pivot_idx, "price": last_pivot_val,
                       "date": dates[last_pivot_idx], "type": last_type})
    return pivots


def _validate_impulse_rules(waves):
    """Validate Elliott Wave impulse rules, return violations list."""
    violations = []
    if len(waves) < 5:
        return ["Insufficient pivots for a 5-wave impulse count"]

    p = [w["price"] for w in waves[:6]]  # 0=start, 1=end W1, 2=end W2, 3=end W3, 4=end W4, 5=end W5

    if len(p) < 6:
        return ["Need at least 6 pivot points for 5-wave count"]

    # Determine direction
    is_bull = p[1] > p[0]

    if is_bull:
        # Rule 1: Wave 2 cannot retrace more than 100% of Wave 1
        if p[2] <= p[0]:
            violations.append("Wave 2 retraces below the start of Wave 1 (violation)")

        # Rule 2: Wave 3 cannot be the shortest among 1, 3, 5
        w1_len = abs(p[1] - p[0])
        w3_len = abs(p[3] - p[2])
        w5_len = abs(p[5] - p[4])
        if w3_len < w1_len and w3_len < w5_len:
            violations.append("Wave 3 is the shortest impulse wave (violation)")

        # Rule 3: Wave 4 cannot overlap Wave 1 territory
        if p[4] <= p[1]:
            violations.append("Wave 4 overlaps Wave 1 price territory (violation)")

        # Guideline checks
        w2_retrace = abs(p[2] - p[1]) / w1_len * 100 if w1_len > 0 else 0
        if w2_retrace > 78.6:
            violations.append(f"Wave 2 deep retrace ({w2_retrace:.1f}% > 78.6%)")
    else:
        # Bearish impulse - mirror rules
        if p[2] >= p[0]:
            violations.append("Wave 2 retraces above the start of Wave 1 (violation)")

        w1_len = abs(p[0] - p[1])
        w3_len = abs(p[2] - p[3])
        w5_len = abs(p[4] - p[5])
        if w3_len < w1_len and w3_len < w5_len:
            violations.append("Wave 3 is the shortest impulse wave (violation)")

        if p[4] >= p[1]:
            violations.append("Wave 4 overlaps Wave 1 price territory (violation)")

    return violations


def _compute_fib_retracements(start_price, end_price):
    """Compute Fibonacci retracement levels."""
    diff = end_price - start_price
    levels = {}
    for fib in FIB_LEVELS:
        levels[fib] = end_price - diff * fib
    return levels


def _compute_fib_extensions(w1_start, w1_end, w2_end):
    """Compute Fibonacci extension targets for Wave 3/5."""
    w1_len = w1_end - w1_start
    levels = {}
    for fib in [1.0, 1.272, 1.618, 2.0, 2.618, 3.618]:
        levels[fib] = w2_end + w1_len * fib
    return levels


def _wave_degree_label(num_bars):
    """Map bar count to Elliott Wave degree."""
    if num_bars > 500:
        return "Primary", PURP
    if num_bars > 200:
        return "Intermediate", INFO
    if num_bars > 80:
        return "Minor", BULL
    if num_bars > 30:
        return "Minute", NEUT
    return "Minuette", MUTED


def _compute_wave_score(waves, violations, fib_alignment):
    """Score the wave count quality 0-100."""
    score = 100
    # Deduct for violations
    for v in violations:
        if "violation" in v.lower():
            score -= 25
        else:
            score -= 10
    # Bonus for Fibonacci alignment
    score += min(20, fib_alignment * 5)
    # Bonus for having complete 5 waves
    if len(waves) >= 6:
        score += 10
    return max(0, min(100, score))


def _detect_wave_pattern(pivots):
    """Attempt to label pivots as Elliott Wave counts (impulse or corrective)."""
    if len(pivots) < 3:
        return None

    # Try impulse (5-wave) pattern
    if len(pivots) >= 6:
        is_bull = pivots[1]["price"] > pivots[0]["price"]
        waves = []
        valid = True
        labels = ["0", "1", "2", "3", "4", "5"]

        for i, lbl in enumerate(labels[:min(len(pivots), 6)]):
            waves.append({
                "label": lbl, "price": pivots[i]["price"],
                "date": pivots[i]["date"], "idx": pivots[i]["idx"],
                "type": pivots[i]["type"],
            })

        violations = _validate_impulse_rules(waves)

        # Check Fibonacci alignment
        fib_hits = 0
        if len(waves) >= 3:
            w1_len = abs(waves[1]["price"] - waves[0]["price"])
            if w1_len > 0:
                w2_retrace = abs(waves[2]["price"] - waves[1]["price"]) / w1_len
                if abs(w2_retrace - 0.618) < 0.08 or abs(w2_retrace - 0.5) < 0.08:
                    fib_hits += 1
                if abs(w2_retrace - 0.382) < 0.08:
                    fib_hits += 1

        if len(waves) >= 4:
            w1_len = abs(waves[1]["price"] - waves[0]["price"])
            if w1_len > 0:
                w3_ext = abs(waves[3]["price"] - waves[2]["price"]) / w1_len
                if abs(w3_ext - 1.618) < 0.15 or abs(w3_ext - 2.618) < 0.15:
                    fib_hits += 2

        if len(waves) >= 6:
            w1_len = abs(waves[1]["price"] - waves[0]["price"])
            if w1_len > 0:
                w5_ext = abs(waves[5]["price"] - waves[4]["price"]) / w1_len
                if abs(w5_ext - 1.0) < 0.1 or abs(w5_ext - 0.618) < 0.1:
                    fib_hits += 1

        score = _compute_wave_score(waves, violations, fib_hits)
        pattern_type = "Impulse (Bullish)" if is_bull else "Impulse (Bearish)"

        return {
            "type": pattern_type,
            "is_bull": is_bull,
            "waves": waves,
            "violations": violations,
            "fib_hits": fib_hits,
            "score": score,
            "degree": _wave_degree_label(waves[-1]["idx"] - waves[0]["idx"] if len(waves) > 1 else 0),
        }

    # Try corrective (ABC) pattern
    if len(pivots) >= 4:
        waves = []
        labels = ["0", "A", "B", "C"]
        for i, lbl in enumerate(labels[:min(len(pivots), 4)]):
            waves.append({
                "label": lbl, "price": pivots[i]["price"],
                "date": pivots[i]["date"], "idx": pivots[i]["idx"],
                "type": pivots[i]["type"],
            })

        is_down = waves[1]["price"] < waves[0]["price"]
        violations = []
        fib_hits = 0

        a_len = abs(waves[1]["price"] - waves[0]["price"])
        if a_len > 0 and len(waves) >= 3:
            b_retrace = abs(waves[2]["price"] - waves[1]["price"]) / a_len
            if abs(b_retrace - 0.618) < 0.08 or abs(b_retrace - 0.5) < 0.08:
                fib_hits += 1
            if b_retrace > 1.0:
                violations.append("Wave B exceeds start of Wave A")

        score = _compute_wave_score(waves, violations, fib_hits)
        pattern_type = "Corrective (Bearish)" if is_down else "Corrective (Bullish)"

        return {
            "type": pattern_type,
            "is_bull": not is_down,
            "waves": waves,
            "violations": violations,
            "fib_hits": fib_hits,
            "score": score,
            "degree": _wave_degree_label(waves[-1]["idx"] - waves[0]["idx"] if len(waves) > 1 else 0),
        }

    return None


def _compute_channel(waves):
    """Compute the trend channel for the impulse wave."""
    if len(waves) < 4:
        return None
    # Base channel: line from Wave 0 to Wave 2
    # Parallel through Wave 1 (and Wave 3 if available)
    w0 = waves[0]
    w2 = waves[2] if len(waves) > 2 else waves[-1]
    w1 = waves[1]
    w3 = waves[3] if len(waves) > 3 else None

    return {
        "base_start": (w0["date"], w0["price"]),
        "base_end": (w2["date"], w2["price"]),
        "parallel_start": (w1["date"], w1["price"]),
        "parallel_end": (w3["date"], w3["price"]) if w3 else None,
    }


def _alternation_check(waves):
    """Check if Waves 2 and 4 alternate (guideline)."""
    if len(waves) < 5:
        return None, None
    w1_len = abs(waves[1]["price"] - waves[0]["price"])
    w3_len = abs(waves[3]["price"] - waves[2]["price"])

    w2_retrace = abs(waves[2]["price"] - waves[1]["price"]) / w1_len * 100 if w1_len else 0
    w4_retrace = abs(waves[4]["price"] - waves[3]["price"]) / w3_len * 100 if w3_len else 0

    w2_type = "Deep" if w2_retrace > 50 else "Shallow"
    w4_type = "Deep" if w4_retrace > 50 else "Shallow"

    alternates = w2_type != w4_type
    return {
        "w2_retrace": w2_retrace, "w2_type": w2_type,
        "w4_retrace": w4_retrace, "w4_type": w4_type,
        "alternates": alternates,
    }, alternates


def _next_wave_projection(waves, close_price):
    """Project the probable next wave movement."""
    if not waves or len(waves) < 2:
        return None

    last_wave = waves[-1]
    n_waves = len(waves) - 1  # subtract the "0" start

    if n_waves <= 4:
        # Still in impulse phase — project next wave
        if n_waves == 1:
            # After Wave 1, project Wave 2 retracement
            w1_len = abs(waves[1]["price"] - waves[0]["price"])
            targets = {
                "0.382": waves[1]["price"] - w1_len * 0.382 * (1 if waves[1]["price"] > waves[0]["price"] else -1),
                "0.500": waves[1]["price"] - w1_len * 0.500 * (1 if waves[1]["price"] > waves[0]["price"] else -1),
                "0.618": waves[1]["price"] - w1_len * 0.618 * (1 if waves[1]["price"] > waves[0]["price"] else -1),
            }
            return {"next_wave": "Wave 2", "direction": "Retracement", "targets": targets}
        elif n_waves == 2:
            # After Wave 2, project Wave 3 extension
            w1_len = waves[1]["price"] - waves[0]["price"]
            targets = {
                "1.000": waves[2]["price"] + w1_len * 1.000,
                "1.618": waves[2]["price"] + w1_len * 1.618,
                "2.618": waves[2]["price"] + w1_len * 2.618,
            }
            return {"next_wave": "Wave 3", "direction": "Extension", "targets": targets}
        elif n_waves == 3:
            # After Wave 3, project Wave 4 retracement
            w3_len = abs(waves[3]["price"] - waves[2]["price"])
            is_bull = waves[3]["price"] > waves[2]["price"]
            sign = -1 if is_bull else 1
            targets = {
                "0.236": waves[3]["price"] + w3_len * 0.236 * sign,
                "0.382": waves[3]["price"] + w3_len * 0.382 * sign,
                "0.500": waves[3]["price"] + w3_len * 0.500 * sign,
            }
            return {"next_wave": "Wave 4", "direction": "Retracement", "targets": targets}
        elif n_waves == 4:
            # After Wave 4, project Wave 5
            w1_len = waves[1]["price"] - waves[0]["price"]
            targets = {
                "0.618": waves[4]["price"] + w1_len * 0.618,
                "1.000": waves[4]["price"] + w1_len * 1.000,
                "1.618": waves[4]["price"] + w1_len * 1.618,
            }
            return {"next_wave": "Wave 5", "direction": "Extension", "targets": targets}
    elif n_waves == 5:
        # After 5-wave impulse, project ABC correction
        impulse_len = abs(waves[5]["price"] - waves[0]["price"])
        is_bull = waves[5]["price"] > waves[0]["price"]
        sign = -1 if is_bull else 1
        targets = {
            "0.382": waves[5]["price"] + impulse_len * 0.382 * sign,
            "0.500": waves[5]["price"] + impulse_len * 0.500 * sign,
            "0.618": waves[5]["price"] + impulse_len * 0.618 * sign,
        }
        return {"next_wave": "Wave A (Correction)", "direction": "Reversal", "targets": targets}

    return None


def _compute_momentum_divergence(df, wave_result):
    """Check RSI / MACD divergence at wave endpoints — key for Wave 5 exhaustion."""
    divergences = []
    if "RSI_14" not in df.columns:
        return divergences

    waves = wave_result["waves"]
    rsi = df["RSI_14"].values
    close = df["Close"].values

    # Check Wave 3 vs Wave 5 divergence
    if len(waves) >= 6:
        w3_idx = waves[3]["idx"]
        w5_idx = waves[5]["idx"]
        if w3_idx < len(rsi) and w5_idx < len(rsi):
            if wave_result["is_bull"]:
                if close[w5_idx] > close[w3_idx] and rsi[w5_idx] < rsi[w3_idx]:
                    divergences.append({
                        "type": "Bearish RSI Divergence (W3 vs W5)",
                        "severity": "HIGH",
                        "detail": f"Price made higher high but RSI ({rsi[w5_idx]:.0f}) < W3 RSI ({rsi[w3_idx]:.0f})",
                        "color": BEAR,
                    })
            else:
                if close[w5_idx] < close[w3_idx] and rsi[w5_idx] > rsi[w3_idx]:
                    divergences.append({
                        "type": "Bullish RSI Divergence (W3 vs W5)",
                        "severity": "HIGH",
                        "detail": f"Price made lower low but RSI ({rsi[w5_idx]:.0f}) > W3 RSI ({rsi[w3_idx]:.0f})",
                        "color": BULL,
                    })

    # Check Wave 1 vs Wave 3 for strength confirmation
    if len(waves) >= 4:
        w1_idx = waves[1]["idx"]
        w3_idx = waves[3]["idx"]
        if w1_idx < len(rsi) and w3_idx < len(rsi):
            if wave_result["is_bull"] and rsi[w3_idx] > rsi[w1_idx]:
                divergences.append({
                    "type": "W3 Momentum Confirmation",
                    "severity": "POSITIVE",
                    "detail": f"W3 RSI ({rsi[w3_idx]:.0f}) > W1 RSI ({rsi[w1_idx]:.0f}) -- strong trend",
                    "color": BULL,
                })

    return divergences


def _volume_profile_waves(df, wave_result):
    """Analyze volume characteristics per wave."""
    if "Volume" not in df.columns:
        return []

    waves = wave_result["waves"]
    vol = df["Volume"].values
    profiles = []

    for i in range(1, len(waves)):
        start_idx = waves[i - 1]["idx"]
        end_idx = waves[i]["idx"]
        if start_idx >= end_idx or end_idx > len(vol):
            continue

        wave_vol = vol[start_idx:end_idx]
        avg_vol = np.mean(wave_vol) if len(wave_vol) > 0 else 0
        total_vol = np.sum(wave_vol)
        trend = "Increasing" if len(wave_vol) > 2 and np.mean(wave_vol[-3:]) > np.mean(wave_vol[:3]) else "Decreasing"

        profiles.append({
            "wave": waves[i]["label"],
            "avg_volume": avg_vol,
            "total_volume": total_vol,
            "vol_trend": trend,
            "bars": end_idx - start_idx,
        })

    return profiles


# ═══════════════════════════════════════════════════════════════════════════════
# CHART BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_wave_chart(df, wave_result, fib_levels=None, show_channel=True, show_projections=True):
    """Build an interactive Plotly candlestick chart with wave labels and Fibonacci."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25], vertical_spacing=0.03,
    )

    dates = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df["Date"])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dates, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350",
        name="Price", showlegend=False,
    ), row=1, col=1)

    # Volume bars
    colors_vol = [
        "#26a69a" if c >= o else "#ef5350"
        for c, o in zip(df["Close"], df["Open"])
    ]
    fig.add_trace(go.Bar(
        x=dates, y=df["Volume"], marker_color=colors_vol,
        opacity=0.4, name="Volume", showlegend=False,
    ), row=2, col=1)

    # Wave labels and connectors
    if wave_result and wave_result["waves"]:
        waves = wave_result["waves"]
        wave_dates = [w["date"] for w in waves]
        wave_prices = [w["price"] for w in waves]

        # Wave connector line
        fig.add_trace(go.Scatter(
            x=wave_dates, y=wave_prices,
            mode="lines+markers+text",
            line=dict(color=GOLD, width=2, dash="dot"),
            marker=dict(size=10, color=GOLD, line=dict(color="#fff", width=1.5)),
            text=[w["label"] for w in waves],
            textposition="top center",
            textfont=dict(size=14, color=GOLD, family="Inter"),
            name="Wave Count",
            showlegend=True,
        ), row=1, col=1)

        # Fibonacci levels — colored & visible
        if fib_levels and len(waves) >= 2:
            _fib_colors = {
                0.236: "#64b5f6", 0.382: "#4fc3f7", 0.5: "#81c784",
                0.618: "#FFD700", 0.786: "#ffb74d", 1.0: "#ce93d8",
                1.272: "#f48fb1", 1.618: "#ef5350", 2.618: "#e53935",
                2.0: "#ff7043", 3.618: "#d32f2f",
            }
            for fib_val, price_level in fib_levels.items():
                _fc = _fib_colors.get(fib_val, "#FFD700")
                fig.add_hline(
                    y=price_level, line_dash="dash",
                    line_color=_fc, line_width=1.5,
                    annotation_text=f"  Fib {fib_val:.3f}  —  ${price_level:.2f}",
                    annotation_position="right",
                    annotation_font=dict(size=10, color=_fc, family="Inter"),
                    row=1, col=1,
                )

        # Channel lines
        if show_channel and len(waves) >= 4:
            channel = _compute_channel(waves)
            if channel and channel["parallel_end"]:
                fig.add_trace(go.Scatter(
                    x=[channel["base_start"][0], channel["base_end"][0]],
                    y=[channel["base_start"][1], channel["base_end"][1]],
                    mode="lines", line=dict(color="rgba(99,102,241,0.4)", width=1, dash="dash"),
                    name="Base Channel", showlegend=False,
                ), row=1, col=1)
                fig.add_trace(go.Scatter(
                    x=[channel["parallel_start"][0], channel["parallel_end"][0]],
                    y=[channel["parallel_start"][1], channel["parallel_end"][1]],
                    mode="lines", line=dict(color="rgba(99,102,241,0.4)", width=1, dash="dash"),
                    name="Parallel Channel", showlegend=False,
                ), row=1, col=1)

    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e0e0e0", size=11, family="Inter"),
        xaxis_rangeslider_visible=False,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    for ax in ["xaxis", "xaxis2", "yaxis", "yaxis2"]:
        fig.update_layout(**{ax: dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.04)")})

    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

def elliott_wave_tab(df, current_price):
    """Render the Elliott Wave analysis tab."""

    # ── CSS ──
    st.markdown("""<style>
    /* ─── Hero Card ─── */
    .ew-hero {
        background: #1b1b1b;
        border: 1px solid #272727;
        border-radius: 16px; overflow: hidden; margin-bottom: 1.4rem;
        box-shadow: 0 4px 28px rgba(0,0,0,0.3);
    }
    .ew-hero-header {
        padding: 1.5rem 1.8rem;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid #222;
    }
    .ew-hero-body { padding: 1.4rem 1.8rem 1.2rem 1.8rem; }

    /* ─── Wave Badge ─── */
    .ew-wave-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 2.4rem; height: 2.4rem; border-radius: 50%;
        font-size: 0.95rem; font-weight: 900; flex-shrink: 0;
        border: 2px solid; line-height: 1;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .ew-wave-badge:hover { transform: scale(1.12); }

    /* ─── Wave Timeline ─── */
    .ew-tl-strip {
        display: flex; align-items: stretch;
        width: 100%; padding: 0.2rem 0;
    }
    .ew-tl-node {
        display: flex; flex-direction: column; align-items: center;
        gap: 0.15rem; flex-shrink: 0; z-index: 1;
    }
    .ew-tl-line {
        flex: 1; display: flex; flex-direction: column;
        align-items: center; justify-content: flex-start;
        min-width: 0; padding-top: 1.15rem;
    }
    .ew-tl-bar {
        width: 100%; height: 3px; border-radius: 2px;
    }
    .ew-tl-mpct {
        font-size: 0.52rem; font-weight: 700;
        margin-top: 0.2rem; white-space: nowrap;
    }
    .ew-tl-price {
        font-size: 0.56rem; color: #777; font-weight: 600;
        letter-spacing: 0.2px; white-space: nowrap;
    }

    /* ─── Fibonacci Row ─── */
    .ew-fib-row {
        display: flex; align-items: center; gap: 0.8rem;
        padding: 0.6rem 0.9rem; border-radius: 8px;
        margin-bottom: 0.15rem; font-size: 0.75rem;
        transition: background 0.15s ease;
    }
    .ew-fib-row:hover { background: rgba(255,255,255,0.02); }
    .ew-fib-near {
        background: rgba(255,215,0,0.04) !important;
        border: 1px solid rgba(255,215,0,0.12);
    }
    .ew-fib-ext-near {
        background: rgba(33,150,243,0.04) !important;
        border: 1px solid rgba(33,150,243,0.12);
    }

    /* ─── Wave Detail Card ─── */
    .ew-wcard {
        background: linear-gradient(160deg, #1e1e1e, #1b1b1b);
        border: 1px solid #272727; border-radius: 14px;
        overflow: hidden; margin-bottom: 0.6rem;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .ew-wcard:hover {
        border-color: #333;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
    }
    .ew-wcard-body { padding: 1rem 1.3rem; }

    /* ─── Diagnostic / Divergence Card ─── */
    .ew-diag {
        background: #1b1b1b; border: 1px solid #272727;
        border-radius: 12px; padding: 0.9rem 1.2rem;
        margin-bottom: 0.5rem;
        transition: border-color 0.2s ease;
    }
    .ew-diag:hover { border-color: #333; }

    /* ─── Note Card ─── */
    .ew-note {
        background: #1b1b1b; border: 1px solid #272727;
        border-radius: 10px; padding: 0.8rem 1.1rem;
        margin-bottom: 0.35rem;
        transition: border-color 0.15s ease;
    }
    .ew-note:hover { border-color: #333; }

    /* ─── Projection Target ─── */
    .ew-target {
        background: #161616; border: 1px solid #272727;
        border-radius: 12px; padding: 0.9rem 0.7rem;
        text-align: center;
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .ew-target:hover { border-color: #333; transform: translateY(-2px); }

    /* ─── Divider ─── */
    .ew-divider {
        height: 1px; margin: 0.8rem 0;
        background: linear-gradient(90deg, transparent, #2a2a2a, transparent);
    }

    /* ─── Active badge glow pulse ─── */
    @keyframes ewPulse {
        0%,100% { box-shadow: 0 0 6px var(--glow); }
        50% { box-shadow: 0 0 14px var(--glow), 0 0 22px var(--glow); }
    }
    .ew-active { animation: ewPulse 2.5s ease-in-out infinite; }

    /* ─── Fib distance bar ─── */
    .ew-fib-dist {
        height: 4px; border-radius: 2px; background: #1a1a1a;
        flex: 1; overflow: hidden; min-width: 40px;
    }
    .ew-fib-dist-fill {
        height: 100%; border-radius: 2px;
        transition: width 0.3s ease;
    }

    /* ─── Tooltip ─── */
    .ew-tip {
        visibility: hidden; opacity: 0;
        position: absolute; bottom: 130%; left: 50%; transform: translateX(-50%);
        background: #222; color: #ccc; border: 1px solid #333;
        border-radius: 6px; padding: 0.4rem 0.6rem;
        font-size: 0.58rem; font-weight: 500; line-height: 1.45;
        white-space: normal; width: 180px; text-align: left;
        z-index: 100; pointer-events: none;
        transition: opacity 0.15s ease, visibility 0.15s ease;
        box-shadow: 0 4px 14px rgba(0,0,0,0.5);
        text-transform: none; letter-spacing: 0;
    }
    .ew-tip::after {
        content: ''; position: absolute; top: 100%; left: 50%;
        transform: translateX(-50%);
        border: 5px solid transparent; border-top-color: #333;
    }
    span:hover > .ew-tip { visibility: visible; opacity: 1; }

    .ew-ctrl-tip {
        display: inline-flex; align-items: center; justify-content: center;
        width: 14px; height: 14px; border-radius: 50%;
        background: rgba(255,255,255,0.04); border: 1px solid #333;
        font-size: 0.5rem; color: #555; font-weight: 700;
        cursor: help; margin-left: 0.35rem; position: relative;
    }
    .ew-ctrl-tip:hover > .ew-tip { visibility: visible; opacity: 1; }
    </style>""", unsafe_allow_html=True)

    # ── Educational Insight Toggle ──
    insight_toggle(
        "elliott_wave_edu",
        "What is Elliott Wave Theory?",
        "<h4 style='margin:0 0 0.6rem 0;color:#fff;font-size:0.9rem;'>Elliott Wave Principle</h4>"
        "<p>Elliott Wave Theory states that market prices unfold in specific patterns "
        "driven by collective investor psychology. Prices move in <strong>5-wave impulses</strong> "
        "(in the direction of the trend) followed by <strong>3-wave corrections</strong> (against the trend).</p>"
        "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem;margin:0.6rem 0;'>"
        "<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
        "<div style='font-size:1rem;font-weight:900;color:#90caf9;'>Impulse (1-2-3-4-5)</div>"
        "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
        "Waves 1, 3, 5 move WITH the trend (motive). Waves 2, 4 are counter-trend (corrective). "
        "Wave 3 is typically the longest and most powerful.</div></div>"
        "<div style='background:rgba(244,67,54,0.08);border:1px solid rgba(244,67,54,0.25);border-radius:8px;padding:0.6rem 0.8rem;'>"
        "<div style='font-size:1rem;font-weight:900;color:#ef9a9a;'>Correction (A-B-C)</div>"
        "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.25rem;'>"
        "After a 5-wave impulse completes, a 3-wave correction follows. Wave A starts the correction, "
        "B is a counter-trend bounce, and C completes the correction.</div></div>"
        "</div>"
        "<p style='margin-top:0.5rem;'><strong style='color:#FFD700;'>Three Cardinal Rules:</strong></p>"
        "<ul>"
        "<li>Wave 2 never retraces more than 100% of Wave 1</li>"
        "<li>Wave 3 is never the shortest impulse wave</li>"
        "<li>Wave 4 never enters the price territory of Wave 1</li>"
        "</ul>"
        "<p><strong style='color:#2196f3;'>Fibonacci Relationships:</strong> Waves commonly relate to each other "
        "by Fibonacci ratios (0.382, 0.618, 1.618). Wave 3 often extends 1.618x of Wave 1. "
        "Wave 2 typically retraces 0.5-0.618 of Wave 1.</p>"
    )

    # ── Controls ──
    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        st.markdown(
            "<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:0.8px;font-weight:700;margin-bottom:0.25rem;display:flex;align-items:center;'>"
            "Sensitivity"
            "<span class='ew-ctrl-tip'>?"
            "<span class='ew-tip'>How many waves to detect. <b>Low</b> = only big moves. "
            "<b>High/Ultra</b> = catches smaller swings too. Start with Medium.</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )
        sensitivity = st.select_slider(
            "Sensitivity", options=["Low", "Medium", "High", "Ultra"],
            value="Medium", label_visibility="collapsed", key="ew_sensitivity",
        )
    with c2:
        st.markdown(
            "<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:0.8px;font-weight:700;margin-bottom:0.25rem;display:flex;align-items:center;'>"
            "Lookback Period"
            "<span class='ew-ctrl-tip'>?"
            "<span class='ew-tip'>How far back to look. <b>100 bars</b> = recent moves only. "
            "<b>500+ bars</b> = bigger, longer-term wave patterns.</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )
        lookback = st.selectbox(
            "Lookback", ["Last 100 bars", "Last 200 bars", "Last 500 bars", "All data"],
            index=1, label_visibility="collapsed", key="ew_lookback",
        )
    with c3:
        st.markdown(
            "<div style='font-size:0.6rem;color:#606060;text-transform:uppercase;"
            "letter-spacing:0.8px;font-weight:700;margin-bottom:0.25rem;display:flex;align-items:center;'>"
            "Show Fibonacci"
            "<span class='ew-ctrl-tip'>?"
            "<span class='ew-tip'>Fibonacci lines show key price levels where waves often reverse. "
            "<b>Retracements</b> = pullback levels. <b>Extensions</b> = target levels.</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )
        show_fib = st.selectbox(
            "Fibonacci", ["Retracements", "Extensions", "Both", "None"],
            index=2, label_visibility="collapsed", key="ew_fib_mode",
        )

    # Map settings
    pct_map = {"Low": 8.0, "Medium": 5.0, "High": 3.0, "Ultra": 1.5}
    pct_threshold = pct_map[sensitivity]

    bars_map = {"Last 100 bars": 100, "Last 200 bars": 200, "Last 500 bars": 500, "All data": len(df)}
    n_bars = min(bars_map[lookback], len(df))
    df_slice = df.iloc[-n_bars:].copy().reset_index(drop=True)

    if len(df_slice) < 20:
        st.warning("Not enough data for Elliott Wave analysis. Need at least 20 bars.")
        return

    # ── Run Analysis ──
    with st.spinner("Detecting wave structure..."):
        pivots = _find_zigzag_pivots(df_slice, pct_threshold)

        if len(pivots) < 3:
            st.warning("Not enough significant pivots detected. Try lowering sensitivity or increasing lookback period.")
            return

        wave_result = _detect_wave_pattern(pivots)

        if not wave_result:
            st.warning("Could not identify a valid wave pattern. Try adjusting parameters.")
            return

        # Compute Fibonacci levels
        waves = wave_result["waves"]
        fib_retrace = None
        fib_extend = None

        if len(waves) >= 3:
            fib_retrace = _compute_fib_retracements(waves[0]["price"], waves[1]["price"])
        if len(waves) >= 3:
            fib_extend = _compute_fib_extensions(waves[0]["price"], waves[1]["price"], waves[2]["price"])

        # Divergence analysis
        divergences = _compute_momentum_divergence(df_slice, wave_result)

        # Volume analysis
        vol_profiles = _volume_profile_waves(df_slice, wave_result)

        # Alternation check
        alt_result, alternates = _alternation_check(waves)

        # Next wave projection
        projection = _next_wave_projection(waves, current_price)

    # ══════════════════════════════════════════════════════════════════════════
    # HERO CARD — Wave Status
    # ══════════════════════════════════════════════════════════════════════════
    wtype = wave_result["type"]
    wscore = wave_result["score"]
    is_bull = wave_result["is_bull"]
    degree_name, degree_color = wave_result["degree"]
    violations = wave_result["violations"]
    n_waves_detected = len(waves) - 1  # exclude "0"

    hero_color = BULL if is_bull else BEAR
    score_color = BULL if wscore >= 70 else NEUT if wscore >= 40 else BEAR
    current_wave_label = waves[-1]["label"] if waves else "?"

    # Determine where we are in the cycle
    if current_wave_label in ["1", "2", "3", "4", "5"]:
        phase = "Impulse Phase"
        phase_detail = f"Currently in Wave {current_wave_label}"
    elif current_wave_label in ["A", "B", "C"]:
        phase = "Corrective Phase"
        phase_detail = f"Currently in Wave {current_wave_label}"
    else:
        phase = "Wave 0 (Starting Point)"
        phase_detail = "Identifying initial structure"

    # Build wave timeline HTML — full-width with inline colored connectors
    _tl_parts = ""
    for _i, _w in enumerate(waves):
        _c = _wc(_w)
        _is_act = (_w == waves[-1])

        # Connector line between previous node and this one
        if _i > 0:
            _prev_w = waves[_i - 1]
            _mv = _w["price"] - _prev_w["price"]
            _mv_pct = (_mv / _prev_w["price"] * 100) if _prev_w["price"] else 0
            _mc = BULL if _mv > 0 else BEAR
            _tl_parts += (
                f"<div class='ew-tl-line'>"
                f"<div class='ew-tl-bar' style='background:linear-gradient(90deg,{_mc}55,{_mc});'></div>"
                f"<div class='ew-tl-mpct' style='color:{_mc};'>{_mv_pct:+.1f}%</div>"
                f"</div>"
            )

        # Node: badge + price
        _tl_parts += (
            f"<div class='ew-tl-node'>"
            f"<div class='ew-wave-badge{' ew-active' if _is_act else ''}' "
            f"style='color:{_c};border-color:{GOLD if _is_act else _c};"
            f"background:{_hex_rgba(_c, 0.12)};"
            f"{'--glow:' + _c + '55;box-shadow:0 0 12px ' + GOLD + '55;' if _is_act else ''}'>"
            f"{_w['label']}</div>"
            f"<div class='ew-tl-price'>${_w['price']:.2f}</div>"
            f"</div>"
        )

    _tl = f"<div class='ew-tl-strip'>{_tl_parts}</div>"

    _n_viols = len([v for v in violations if "violation" in v.lower()])

    # Score description
    if wscore >= 80:
        _sq = "Excellent"
    elif wscore >= 60:
        _sq = "Good"
    elif wscore >= 40:
        _sq = "Fair"
    else:
        _sq = "Weak"

    # RGB split for hero color gradient
    _hc = hero_color.lstrip("#")
    _hr, _hg, _hb = int(_hc[:2], 16), int(_hc[2:4], 16), int(_hc[4:], 16)

    st.markdown(
        f"<div class='ew-hero'>"

        # ── HEADER STRIP — Verdict + Score ──
        f"<div class='ew-hero-header' style='"
        f"background:linear-gradient(135deg,rgba({_hr},{_hg},{_hb},0.07),transparent);'>"

        f"<div style='display:flex;align-items:center;gap:0.9rem;'>"
        f"<div style='width:44px;height:44px;border-radius:12px;"
        f"background:rgba({_hr},{_hg},{_hb},0.12);"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-size:1.3rem;color:{hero_color};'>{'&#9650;' if is_bull else '&#9660;'}</div>"
        f"<div>"
        f"<div style='font-size:1.6rem;font-weight:900;color:{hero_color};letter-spacing:-0.5px;"
        f"line-height:1;'>{wtype}</div>"
        f"<div style='font-size:0.68rem;color:#888;margin-top:0.25rem;font-weight:500;'>"
        f"{phase_detail}</div>"
        f"</div></div>"

        f"<div style='text-align:right;'>"
        f"<div style='font-size:1.6rem;font-weight:900;color:{score_color};line-height:1;'>"
        f"{wscore}<span style='font-size:0.65rem;color:#555;font-weight:600;'>/100</span></div>"
        f"<div style='font-size:0.6rem;color:#666;margin-top:0.15rem;font-weight:600;"
        f"text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;"
        f"justify-content:flex-end;gap:0.25rem;'>Wave Score"
        f"<span class='ew-ctrl-tip'>?"
        f"<span class='ew-tip'>How reliable this wave count is (0–100). "
        f"Higher = more rules pass and more Fibonacci levels line up. "
        f"Above 70 is good, below 40 is weak.</span></span></div>"
        f"</div></div>"

        # ── BODY ──
        f"<div class='ew-hero-body'>"

        # Tags row
        f"<div style='display:flex;gap:0.4rem;margin-bottom:1rem;flex-wrap:wrap;'>"
        f"<span style='font-size:0.55rem;padding:0.18rem 0.55rem;border-radius:4px;"
        f"background:{_hex_rgba(degree_color, 0.12)};color:{degree_color};"
        f"font-weight:700;text-transform:uppercase;letter-spacing:0.5px;'>{degree_name} Degree</span>"
        f"<span style='font-size:0.55rem;padding:0.18rem 0.55rem;border-radius:4px;"
        f"background:{_hex_rgba(score_color, 0.1)};color:{score_color};"
        f"font-weight:700;'>{_sq} Quality</span>"
        f"<span style='font-size:0.55rem;padding:0.18rem 0.55rem;border-radius:4px;"
        f"background:{_hex_rgba(BULL if not _n_viols else BEAR, 0.1)};"
        f"color:{BULL if not _n_viols else BEAR};"
        f"font-weight:700;'>{_n_viols} Violations</span>"
        f"</div>"

        # Score bar
        + _glowbar(wscore, score_color)

        + "<div class='ew-divider'></div>"

        # ── Stats grid — 5 columns ──
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.6rem;"
        f"margin-bottom:1.1rem;'>"
        + _stat_pill("Waves", str(n_waves_detected), INFO, tip="Number of waves detected in the current pattern")
        + _stat_pill("Pivots", str(len(pivots)), CYAN, tip="Turning points found in the price. More pivots = more detailed wave count")
        + _stat_pill("Fib Hits", str(wave_result["fib_hits"]), GOLD, tip="How many waves line up with Fibonacci ratios. More hits = stronger pattern")
        + _stat_pill("Phase", phase.split()[0], hero_color, tip="Are we in the trending part (Impulse) or the pullback part (Corrective)?")
        + _stat_pill("Price", f"${current_price:.2f}", hero_color)
        + f"</div>"

        + "<div class='ew-divider'></div>"

        # ── Wave Sequence label + timeline ──
        f"<div style='font-size:0.5rem;color:#444;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.4rem;'>Wave Sequence</div>"
        + _tl

        + f"</div></div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PRICE LADDER — Wave-derived targets
    # ══════════════════════════════════════════════════════════════════════════
    if projection and projection["targets"]:
        st.markdown(_sec("Wave Price Ladder", GOLD), unsafe_allow_html=True)
        _tgts = sorted(projection["targets"].values())
        # Determine stop (previous wave low/high) and up to 3 targets
        if is_bull:
            _stop = waves[-1]["price"] if len(waves) >= 2 else current_price * 0.95
            # For bullish: stop is most recent corrective low, targets are extensions above
            if len(waves) >= 2:
                # Use the lowest recent wave pivot as stop
                recent_lows = [w["price"] for w in waves if w["type"] == "low"]
                _stop = min(recent_lows) if recent_lows else current_price * 0.95
            _targets_above = [t for t in _tgts if t > current_price]
            _t1 = _targets_above[0] if len(_targets_above) > 0 else current_price * 1.03
            _t2 = _targets_above[1] if len(_targets_above) > 1 else _t1 * 1.02
            _t3 = _targets_above[2] if len(_targets_above) > 2 else _t2 * 1.02
        else:
            recent_highs = [w["price"] for w in waves if w["type"] == "high"]
            _stop = max(recent_highs) if recent_highs else current_price * 1.05
            _targets_below = [t for t in reversed(_tgts) if t < current_price]
            _t1 = _targets_below[0] if len(_targets_below) > 0 else current_price * 0.97
            _t2 = _targets_below[1] if len(_targets_below) > 1 else _t1 * 0.98
            _t3 = _targets_below[2] if len(_targets_below) > 2 else _t2 * 0.98

        from _levels import price_ladder_html as _plh
        st.markdown(
            _plh(current_price, _stop, _t1, _t2, _t3, is_bull),
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # INTERACTIVE CHART
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Wave Chart with Fibonacci"), unsafe_allow_html=True)

    fib_to_show = None
    if show_fib in ["Retracements", "Both"] and fib_retrace:
        fib_to_show = fib_retrace
    if show_fib in ["Extensions", "Both"] and fib_extend:
        fib_to_show = {**(fib_to_show or {}), **fib_extend}

    fig = _build_wave_chart(df_slice, wave_result, fib_to_show)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # WAVE DETAILS — simplified, flat, educational
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Wave Breakdown", GOLD), unsafe_allow_html=True)

    insight_toggle(
        "ew_wave_detail_edu",
        "What does each wave mean?",
        "<p style='margin:0 0 0.6rem 0;'>Each wave represents a "
        "<strong>swing</strong> in the price — either up or down.</p>"
        "<div style='display:grid;grid-template-columns:repeat(2,1fr);gap:0.5rem;margin:0.6rem 0;'>"
        "<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.25);"
        "border-radius:8px;padding:0.6rem 0.8rem;'>"
        "<div style='font-weight:900;color:#90caf9;'>Waves 1, 3, 5</div>"
        "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.2rem;'>"
        "These move <strong>with</strong> the main trend. "
        "Wave 3 is usually the strongest and longest move — this is where the big money is made.</div></div>"
        "<div style='background:rgba(244,67,54,0.08);border:1px solid rgba(244,67,54,0.25);"
        "border-radius:8px;padding:0.6rem 0.8rem;'>"
        "<div style='font-weight:900;color:#ef9a9a;'>Waves 2, 4 &amp; A, B, C</div>"
        "<div style='font-size:0.72rem;color:#e0e0e0;line-height:1.5;margin-top:0.2rem;'>"
        "These move <strong>against</strong> the trend (pullbacks/corrections). "
        "They are normal and healthy — they set up the next big move.</div></div></div>"
        "<p style='font-size:0.72rem;color:#aaa;'><strong>Tip:</strong> A green <span style='color:#4caf50;'>&#9650;</span> percentage means price went up during that wave. "
        "A red <span style='color:#f44336;'>&#9660;</span> means price went down.</p>"
    )

    for i in range(1, len(waves)):
        prev = waves[i - 1]
        curr = waves[i]
        w_label = curr["label"]
        w_move = curr["price"] - prev["price"]
        w_pct = (w_move / prev["price"] * 100) if prev["price"] != 0 else 0
        w_bars = curr["idx"] - prev["idx"]
        w_is_up = w_move > 0
        w_color = _wc(curr)

        # Simple wave type description
        if w_label.isdigit():
            _wnum = int(w_label)
            if _wnum % 2 == 1:
                _wtype = "Trend Move"
                _wdesc = {1: "The start of a new trend", 3: "The strongest move — big momentum", 5: "The final push before a reversal"}.get(_wnum, "Trend wave")
            else:
                _wtype = "Pullback"
                _wdesc = {2: "Normal pullback after Wave 1", 4: "A pause before the final wave"}.get(_wnum, "Correction wave")
        else:
            _wtype = "Correction"
            _wdesc = {"A": "Start of the correction", "B": "A bounce within the correction", "C": "Final leg of the correction"}.get(w_label, "Corrective wave")

        st.markdown(
            f"<div class='ew-wcard'>"
            f"<div style='height:3px;background:linear-gradient(90deg,{w_color},{w_color}88,transparent);'></div>"
            f"<div class='ew-wcard-body'>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;'>"
            f"<div style='display:flex;align-items:center;gap:0.8rem;'>"
            f"<div class='ew-wave-badge' style='color:{w_color};border-color:{w_color};"
            f"background:{_hex_rgba(w_color, 0.1)};'>{w_label}</div>"
            f"<div>"
            f"<div style='font-size:0.82rem;font-weight:800;color:#e0e0e0;'>"
            f"Wave {w_label} &middot; {_wtype}</div>"
            f"<div style='font-size:0.62rem;color:#777;margin-top:0.15rem;'>{_wdesc}</div>"
            f"</div></div>"
            f"<div style='text-align:right;'>"
            f"<div style='font-size:1.4rem;font-weight:900;color:{BULL if w_is_up else BEAR};line-height:1;'>"
            f"{w_pct:+.1f}%</div>"
            f"<div style='font-size:0.58rem;color:#555;margin-top:0.15rem;'>${prev['price']:.2f} &rarr; ${curr['price']:.2f}</div>"
            f"</div></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # WHAT HAPPENS NEXT — Projection (the most actionable section)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("What Happens Next?", PURP), unsafe_allow_html=True)

    insight_toggle(
        "ew_projection_edu",
        "How do we predict the next move?",
        "<p style='margin:0 0 0.6rem 0;'>Based on which wave just finished, "
        "we can estimate <strong>where price is likely to go next</strong> using math "
        "(Fibonacci ratios).</p>"
        "<ul style='font-size:0.75rem;line-height:1.8;'>"
        "<li><strong>After a trend wave (1, 3, 5):</strong> Expect a pullback. "
        "The targets show how far the pullback might go.</li>"
        "<li><strong>After a pullback (2, 4):</strong> Expect the next trend move. "
        "The targets show how far up (or down) it might push.</li>"
        "<li><strong>After all 5 waves finish:</strong> Expect a bigger correction (A-B-C). "
        "The trend may be over for now.</li>"
        "</ul>"
        "<p style='font-size:0.72rem;color:#aaa;'><strong>Tip:</strong> The price targets below "
        "are <em>estimates</em>, not guarantees. Use them as areas to watch, not exact buy/sell points.</p>"
    )

    if projection:
        proj_color = BULL if projection["direction"] == "Extension" else BEAR if projection["direction"] == "Reversal" else NEUT
        # Simple explanation of what's expected
        if projection["direction"] == "Extension":
            _proj_explain = "Price is expected to <strong>continue moving</strong> in the trend direction."
        elif projection["direction"] == "Reversal":
            _proj_explain = "The 5-wave move is complete. Price is expected to <strong>pull back or reverse</strong>."
        else:
            _proj_explain = "Price is expected to <strong>pull back</strong> before the next move."

        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BDR};border-radius:14px;"
            f"overflow:hidden;margin-bottom:1rem;'>"
            f"<div style='height:4px;background:linear-gradient(90deg,{proj_color},{proj_color}88,transparent);'></div>"
            f"<div style='padding:1.4rem 1.6rem;'>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:0.6rem;'>"
            f"<div>"
            f"<div style='font-size:1.1rem;font-weight:900;color:#e0e0e0;'>"
            f"Next Expected: {projection['next_wave']}</div>"
            f"<div style='font-size:0.72rem;color:#999;margin-top:0.2rem;line-height:1.5;'>"
            f"{_proj_explain}</div></div>"
            f"<div style='padding:0.3rem 0.8rem;border-radius:6px;"
            f"background:{_hex_rgba(proj_color, 0.12)};border:1px solid {_hex_rgba(proj_color, 0.3)};"
            f"font-size:0.7rem;font-weight:700;color:{proj_color};'>"
            f"{'&#9650; Up' if projection['direction'] == 'Extension' else '&#9660; Down'}</div>"
            f"</div>"
            f"<div style='font-size:0.62rem;color:#666;margin-bottom:0.5rem;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.6px;'>Price Targets (areas to watch)</div>",
            unsafe_allow_html=True,
        )

        # Target levels
        _ncols = min(len(projection['targets']), 4)
        targets_html = (
            f"<div style='display:grid;grid-template-columns:repeat({_ncols},1fr);"
            f"gap:0.5rem;'>"
        )
        for fib_label, target_price in projection["targets"].items():
            t_dist = (target_price - current_price) / current_price * 100
            t_color = BULL if t_dist > 0 else BEAR
            targets_html += (
                f"<div class='ew-target'>"
                f"<div style='font-size:0.52rem;color:{MUTED};text-transform:uppercase;"
                f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.35rem;'>Target ({fib_label})</div>"
                f"<div style='font-size:1.25rem;font-weight:900;color:{t_color};line-height:1;'>"
                f"${target_price:.2f}</div>"
                f"<div style='font-size:0.6rem;color:{t_color};margin-top:0.25rem;font-weight:600;'>"
                f"{t_dist:+.1f}% from now</div></div>"
            )
        targets_html += "</div>"
        st.markdown(targets_html + "</div></div>", unsafe_allow_html=True)
    else:
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BDR};border-radius:12px;"
            f"padding:1.2rem;text-align:center;'>"
            f"<div style='font-size:0.8rem;color:#666;'>Not enough wave data to project the next move yet.</div></div>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # HEALTH CHECK — simplified rule validation
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Wave Health Check", INFO), unsafe_allow_html=True)

    insight_toggle(
        "ew_health_edu",
        "What is a wave health check?",
        "<p style='margin:0 0 0.5rem 0;'>Elliott Wave has <strong>3 rules that can never be broken</strong>. "
        "If any rule is broken, the wave count is wrong and needs to be re-done.</p>"
        "<ol style='font-size:0.75rem;line-height:1.8;'>"
        "<li><strong>Wave 2</strong> cannot go below where Wave 1 started "
        "(the pullback can't erase the entire first move)</li>"
        "<li><strong>Wave 3</strong> cannot be the shortest wave "
        "(the strongest move can't be smaller than both Wave 1 and 5)</li>"
        "<li><strong>Wave 4</strong> cannot overlap with Wave 1 "
        "(the second pullback can't drop into the first wave's territory)</li>"
        "</ol>"
        "<p style='font-size:0.72rem;color:#aaa;'><strong>Green check</strong> = all rules are valid, "
        "this wave count makes sense. <strong>Red X</strong> = something is broken.</p>"
    )

    if not violations:
        st.markdown(
            f"<div style='background:{_hex_rgba(BULL, 0.05)};border:1px solid {_hex_rgba(BULL, 0.2)};"
            f"border-radius:14px;padding:1.4rem 1.2rem;text-align:center;'>"
            f"<div style='font-size:1.5rem;margin-bottom:0.4rem;color:{BULL};'>&#10003;</div>"
            f"<div style='font-size:0.88rem;font-weight:800;color:{BULL};'>All Rules Pass</div>"
            f"<div style='font-size:0.68rem;color:#666;margin-top:0.25rem;'>"
            f"This wave count looks valid — no rules are broken</div></div>",
            unsafe_allow_html=True,
        )
    else:
        for v in violations:
            is_hard = "violation" in v.lower()
            v_color = BEAR if is_hard else NEUT
            v_icon = "&#10007;" if is_hard else "&#9888;"
            v_explain = "Rule Broken — this wave count may be invalid" if is_hard else "Minor warning — not a rule break but something to watch"
            st.markdown(
                f"<div class='ew-diag' style='border-left:3px solid {v_color};'>"
                f"<div style='display:flex;align-items:center;gap:0.7rem;'>"
                f"<span style='font-size:0.95rem;color:{v_color};'>{v_icon}</span>"
                f"<div>"
                f"<div style='font-size:0.78rem;font-weight:700;color:#e0e0e0;'>{v}</div>"
                f"<div style='font-size:0.58rem;color:#555;margin-top:0.12rem;'>{v_explain}</div>"
                f"</div></div></div>",
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # MOMENTUM SIGNALS — divergences in simple language
    # ══════════════════════════════════════════════════════════════════════════
    if divergences:
        st.markdown(_sec("Momentum Signals", NEUT), unsafe_allow_html=True)

        insight_toggle(
            "ew_divergence_edu",
            "What are momentum signals?",
            "<p style='margin:0 0 0.5rem 0;'>Momentum measures <strong>how strong a price move is</strong>. "
            "Sometimes price makes a new high, but the momentum (energy) behind it is weaker. "
            "This is called a <strong>divergence</strong> — and it often warns that the trend is getting tired.</p>"
            "<ul style='font-size:0.75rem;line-height:1.8;'>"
            "<li><strong style='color:#f44336;'>Bearish Divergence:</strong> Price goes higher, but momentum gets weaker "
            "— warning sign that the uptrend may be ending</li>"
            "<li><strong style='color:#4caf50;'>Bullish Divergence:</strong> Price goes lower, but momentum gets stronger "
            "— hint that the downtrend may be ending</li>"
            "<li><strong style='color:#4caf50;'>Momentum Confirmation:</strong> Price and momentum agree "
            "— the trend is healthy and strong</li>"
            "</ul>"
        )

        for div in divergences:
            # Simple language for each divergence
            if "bearish" in div["type"].lower():
                _simple = "The price went up but the energy behind the move got weaker — the trend may be running out of steam."
            elif "bullish" in div["type"].lower():
                _simple = "The price went down but the energy behind the selling got weaker — buyers may be stepping in soon."
            else:
                _simple = "The momentum confirms the price move — the trend looks strong and healthy."

            st.markdown(
                f"<div class='ew-diag' style='border-left:3px solid {div['color']};'>"
                f"<div style='display:flex;align-items:center;justify-content:space-between;'>"
                f"<div style='font-size:0.82rem;font-weight:800;color:#e0e0e0;'>{div['type']}</div>"
                f"<span style='font-size:0.56rem;padding:0.12rem 0.5rem;border-radius:4px;"
                f"background:{_hex_rgba(div['color'], 0.1)};color:{div['color']};"
                f"font-weight:700;'>{div['severity']}</span></div>"
                f"<div style='font-size:0.7rem;color:#999;margin-top:0.3rem;line-height:1.5;'>"
                f"{_simple}</div></div>",
                unsafe_allow_html=True,
            )
