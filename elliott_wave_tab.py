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


def _wave_role_summary(current_wave_label):
    notes = {
        "1": "Early trend leg. Useful mostly as a clue that a new move started, not the best place to chase hard.",
        "2": "Correction after Wave 1. Traders usually watch this area to prepare for a possible Wave 3 continuation.",
        "3": "Usually the strongest trend leg. Best if you caught it early; weaker if you are entering after a vertical push.",
        "4": "Pause or pullback before the final push. Good for planning continuation only if the pullback holds.",
        "5": "Final trend push. Better for protecting profits than for opening a late fresh chase trade.",
        "A": "First corrective leg. This usually warns that the previous trend is no longer clean.",
        "B": "Counter-move inside a correction. Often messy and lower quality than the main move.",
        "C": "Final corrective leg. This is where traders start watching for the next larger turn.",
    }
    return notes.get(current_wave_label, "The wave count is still incomplete, so use the pivots more than the label.")


def _build_wave_trade_tool(waves, projection, current_price, is_bull, violations, wave_score):
    current_wave_label = waves[-1]["label"] if waves else "?"
    direction = projection.get("direction") if projection else None

    if direction == "Extension":
        trade_is_bull = is_bull
        setup_label = "Trend continuation map"
        if current_wave_label in ("2", "4", "B"):
            use_now = "This is the cleaner Elliott use-case: wait for the pullback to finish, then use the ladder for continuation targets."
        else:
            use_now = "The continuation move may already be running. This is more useful for managing the trade than chasing a late candle."
        avoid_now = "Avoid fighting the main trend while this count stays valid."
        confirmation = "Price should hold the invalidation pivot and start expanding toward the first extension target."
        target_basis = "Targets are Fibonacci extension levels for the next motive wave."
    elif direction == "Retracement":
        trade_is_bull = not is_bull
        setup_label = "Pullback map"
        use_now = "Treat this as a pullback tool first. If you are already in the trend, use it to manage profits or plan the next re-entry."
        avoid_now = "Do not treat correction targets as automatic reversal entries without confirmation."
        confirmation = "Watch for momentum to slow near the target zone, then wait for a fresh turn before taking the main trend again."
        target_basis = "Targets are Fibonacci retracement zones of the wave that just completed."
    elif direction == "Reversal":
        trade_is_bull = not is_bull
        setup_label = "Post-impulse correction map"
        use_now = "The 5-wave run looks mature. Use this map to protect profits or stalk the correction, not to enter the old trend late."
        avoid_now = "Avoid assuming the old trend still has a clean runway while the count is shifting into correction mode."
        confirmation = "A break away from the final impulse extreme supports the bigger corrective move."
        target_basis = "Targets are correction zones measured from the completed 5-wave structure."
    else:
        trade_is_bull = is_bull
        setup_label = "Structure watch"
        use_now = "There is not enough wave structure yet for a reliable next-move map. Use the pivots as context only."
        avoid_now = "Avoid forcing a trade from a count that still lacks a clear projection."
        confirmation = "Wait for a cleaner wave completion or a fresh pivot sequence."
        target_basis = "Targets are not available yet because the next wave is not clear."

    anchor_type = "low" if trade_is_bull else "high"
    stop_anchor = None
    for wave in reversed(waves[:-1]):
        if wave["type"] != anchor_type:
            continue
        if trade_is_bull and wave["price"] < current_price:
            stop_anchor = wave
            break
        if not trade_is_bull and wave["price"] > current_price:
            stop_anchor = wave
            break

    if stop_anchor is not None:
        stop = float(stop_anchor["price"])
        stop_basis = (
            f"Stop uses Wave {stop_anchor['label']} at {stop_anchor['price']:.2f}. "
            f"If price breaks that pivot, this count is likely wrong."
        )
    else:
        fallback = current_price * (0.95 if trade_is_bull else 1.05)
        stop = float(fallback)
        stop_basis = "Stop falls back to the nearest visible swing area because a clean invalidation pivot was not found."

    if trade_is_bull and stop >= current_price:
        stop = current_price * 0.95
    if not trade_is_bull and stop <= current_price:
        stop = current_price * 1.05

    raw_targets = sorted(projection.get("targets", {}).values()) if projection else []
    if trade_is_bull:
        directional_targets = [target for target in raw_targets if target > current_price]
        fallback_targets = [current_price * 1.03, current_price * 1.05, current_price * 1.08]
    else:
        directional_targets = sorted([target for target in raw_targets if target < current_price], reverse=True)
        fallback_targets = [current_price * 0.97, current_price * 0.95, current_price * 0.92]

    while len(directional_targets) < 3:
        directional_targets.append(fallback_targets[len(directional_targets)])

    hard_violations = [v for v in violations if "violation" in v.lower()]
    if hard_violations:
        trust_label = "Broken count"
        trust_color = BEAR
        trust_note = "Hard Elliott rules are broken. Do not trust this ladder until the count is redone."
    elif wave_score >= 70:
        trust_label = "Usable count"
        trust_color = BULL
        trust_note = "No hard rule break and the score is solid. This is usable as a planning tool, not a guarantee."
    elif wave_score >= 40:
        trust_label = "Borderline count"
        trust_color = NEUT
        trust_note = "The count is usable only as a scenario map. Keep size smaller and demand confirmation."
    else:
        trust_label = "Weak count"
        trust_color = BEAR
        trust_note = "The wave structure is weak. Treat the ladder as low-confidence context only."

    return {
        "trade_is_bull": trade_is_bull,
        "trade_color": BULL if trade_is_bull else BEAR,
        "trade_side": "Long" if trade_is_bull else "Short",
        "setup_label": setup_label,
        "use_now": use_now,
        "avoid_now": avoid_now,
        "confirmation": confirmation,
        "target_basis": target_basis,
        "stop_basis": stop_basis,
        "stop": stop,
        "t1": directional_targets[0],
        "t2": directional_targets[1],
        "t3": directional_targets[2],
        "trust_label": trust_label,
        "trust_color": trust_color,
        "trust_note": trust_note,
        "hard_violations": hard_violations,
    }


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

@st.cache_data(ttl=300, show_spinner=False)
def _ew_compute(cache_key, _df_slice, pct_threshold, current_price, show_fib):
    pivots = _find_zigzag_pivots(_df_slice, pct_threshold)
    if len(pivots) < 3:
        return None
    wave_result = _detect_wave_pattern(pivots)
    if not wave_result:
        return None
    waves = wave_result["waves"]
    fib_retrace = _compute_fib_retracements(waves[0]["price"], waves[1]["price"]) if len(waves) >= 3 else None
    fib_extend  = _compute_fib_extensions(waves[0]["price"], waves[1]["price"], waves[2]["price"]) if len(waves) >= 3 else None
    divergences  = _compute_momentum_divergence(_df_slice, wave_result)
    vol_profiles = _volume_profile_waves(_df_slice, wave_result)
    alt_result, alternates = _alternation_check(waves)
    projection = _next_wave_projection(waves, current_price)
    fib_to_show = {}
    if show_fib in ("Retracements", "Both") and fib_retrace:
        fib_to_show.update(fib_retrace)
    if show_fib in ("Extensions", "Both") and fib_extend:
        fib_to_show.update(fib_extend)
    fig = _build_wave_chart(_df_slice, wave_result, fib_to_show if fib_to_show else None)
    return dict(
        wave_result=wave_result, pivots=pivots,
        fib_retrace=fib_retrace, fib_extend=fib_extend,
        divergences=divergences, vol_profiles=vol_profiles,
        alt_result=alt_result, alternates=alternates,
        projection=projection, fig=fig,
    )


def get_ew_signal(df, cp):
    """Return a signal dict for the Decision Tab aggregator, or None if no clear setup."""
    if df is None or len(df) < 50:
        return None
    try:
        import pandas as _pd
        n_bars = min(200, len(df))
        df_slice = df.iloc[-n_bars:].copy().reset_index(drop=False)
        if "Date" in df_slice.columns:
            df_slice = df_slice.set_index("Date")

        _ew = _ew_compute(
            f"ew_sig_{len(df)}_{round(float(cp),2)}",
            df_slice, 0.03, float(cp), False,
        )
        if _ew is None:
            return None

        wave_result = _ew["wave_result"]
        is_bull  = wave_result["is_bull"]
        wscore   = wave_result["score"]
        waves    = wave_result["waves"]
        wtype    = wave_result["type"]
        projection = _ew.get("projection") or {}

        # Only surface bullish setups with decent wave score
        if not is_bull or wscore < 45:
            return None

        cur_wave = waves[-1]["label"] if waves else "?"
        # Wave 2 or 4 pullback in a bullish impulse = ideal buy zone
        # Wave 3 or 5 ongoing = good momentum
        # ABC corrective bullish = potential reversal
        if cur_wave in ("2", "4"):
            conf = min(80, wscore + 10)
            phase_note = f"Wave {cur_wave} pullback — ideal entry before next impulse leg"
        elif cur_wave in ("3", "5"):
            conf = min(75, wscore)
            phase_note = f"Wave {cur_wave} in progress — momentum favors longs"
        elif cur_wave in ("A", "B", "C") and is_bull:
            conf = min(65, wscore - 5)
            phase_note = f"Corrective Wave {cur_wave} (bullish structure)"
        else:
            conf = min(60, wscore - 10)
            phase_note = f"Wave {cur_wave} — {wtype}"

        if conf < 45:
            return None

        reasons = [
            f"Elliott Wave: {wtype} — Wave {cur_wave} (score {wscore}/100)",
            phase_note,
        ]

        proj_t1 = projection.get("t1") or projection.get("target1") or None
        proj_t2 = projection.get("t2") or projection.get("target2") or None

        atr_ser = (df["High"] - df["Low"]).rolling(14, min_periods=1).mean()
        atr = max(float(atr_ser.iloc[-1]), float(cp) * 0.01)
        swing_lo = float(df["Low"].tail(20).min())
        _stop = max(swing_lo - atr * 0.3, float(cp) * 0.93)
        _risk = max(float(cp) - _stop, 0.001)

        return dict(
            color="#9c27b0",
            verdict_text="▲ BUY",
            sublabel=f"Elliott Wave — {wtype}",
            conf=int(conf),
            reasons=reasons,
            entry=float(cp),
            stop=round(_stop, 2),
            t1=proj_t1 if proj_t1 else round(float(cp) + _risk * 1.618, 2),
            t2=proj_t2 if proj_t2 else round(float(cp) + _risk * 2.618, 2),
            t3=round(float(cp) + _risk * 4.236, 2),
        )
    except Exception:
        return None


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

    # Fixed settings — no controls needed
    pct_threshold = 5.0
    show_fib = "Both"

    n_bars = min(200, len(df))
    df_slice = df.iloc[-n_bars:].copy().reset_index(drop=True)

    if len(df_slice) < 20:
        st.warning("Not enough data for Elliott Wave analysis. Need at least 20 bars.")
        return

    # ── Run Analysis (cached by df content + settings) ──
    _ew_key = (len(df_slice), str(df_slice["Close"].iloc[-1]) if len(df_slice) else "0",
               pct_threshold, n_bars, show_fib)
    _ew = _ew_compute(_ew_key, df_slice, pct_threshold, float(current_price), show_fib)
    if _ew is None:
        return

    wave_result  = _ew["wave_result"]
    pivots       = _ew["pivots"]
    waves        = wave_result["waves"]
    fib_retrace  = _ew["fib_retrace"]
    fib_extend   = _ew["fib_extend"]
    divergences  = _ew["divergences"]
    vol_profiles = _ew["vol_profiles"]
    alt_result   = _ew["alt_result"]
    alternates   = _ew["alternates"]
    projection   = _ew["projection"]

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
    trade_tool = _build_wave_trade_tool(waves, projection, current_price, is_bull, violations, wscore)
    wave_role_note = _wave_role_summary(current_wave_label)
    if vol_profiles:
        _last_volume = vol_profiles[-1]
        volume_note = (
            f"Wave {_last_volume['wave']} had {_last_volume['vol_trend'].lower()} volume across "
            f"{_last_volume['bars']} bars."
        )
    else:
        volume_note = "Volume behaviour for the current wave was not available."
    if alt_result:
        alternation_note = (
            f"Wave 2 was {alt_result['w2_type'].lower()} ({alt_result['w2_retrace']:.0f}%) and "
            f"Wave 4 was {alt_result['w4_type'].lower()} ({alt_result['w4_retrace']:.0f}%)."
        )
    else:
        alternation_note = "Alternation could not be checked because there are not enough completed impulse waves yet."

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

    # ── DECISION BOX ─────────────────────────────────────────────────────────
    if trade_tool and trade_tool.get("t1"):
        _ew_entry = float(trade_tool.get("entry", current_price))
        _ew_stop  = float(trade_tool.get("stop",  _ew_entry * 0.95))
        _ew_t1    = float(trade_tool["t1"])
        _ew_t2    = float(trade_tool.get("t2", _ew_t1))
        _ew_t3    = float(trade_tool.get("t3", _ew_t2))
        _ew_is_b  = bool(trade_tool.get("trade_is_bull", is_bull))

        if _ew_is_b and current_price > _ew_stop:
            _ew_dv   = "BUY"
            _ew_dcol = BULL
            _ew_dsub = f"Wave structure supports a long. Currently in {phase_detail}. Wave score {wscore}/100."
        else:
            _ew_dv   = "WAIT"
            _ew_dcol = NEUT
            _ew_dsub = f"Wave structure is not yet clear enough for a high-confidence entry. Score {wscore}/100 — wait for confirmation."

        _ew_rgb = {"BUY": "76,175,80", "WAIT": "255,152,0"}.get(_ew_dv, "255,152,0")

        _ew_ladder = ""
        if _ew_dv == "BUY":
            try:
                from _levels import price_ladder_html as _ew_plh
                _ew_ladder = _ew_plh(_ew_entry, _ew_stop, _ew_t1, _ew_t2, _ew_t3, True)
            except Exception:
                pass

        def _ew_tip(text):
            return (
                f"<span style='position:relative;display:inline-flex;align-items:center;"
                f"cursor:help;margin-left:0.3rem;'>"
                f"<span style='display:inline-flex;align-items:center;justify-content:center;"
                f"width:13px;height:13px;border-radius:50%;border:1px solid #3a3a3a;"
                f"font-size:0.48rem;color:#666;font-weight:700;'>?</span>"
                f"<span class='ew-tip' style='width:220px;font-size:0.7rem;line-height:1.5;'>"
                f"{text}</span></span>"
            )

        st.markdown(
            f"<div style='background:#181818;border:1px solid #232323;"
            f"border-top:3px solid {_ew_dcol};border-radius:14px;overflow:hidden;margin-bottom:1.4rem;'>"
            f"<div style='padding:1.6rem 2rem 1.3rem;border-bottom:1px solid #222;'>"
            f"<div style='font-size:0.72rem;color:#bbb;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Elliott Wave Decision</div>"
            f"<div style='font-size:3rem;font-weight:900;color:{_ew_dcol};"
            f"letter-spacing:-1.5px;line-height:1;'>{_ew_dv}</div>"
            f"<div style='font-size:0.85rem;color:#bbb;margin-top:0.6rem;"
            f"font-weight:500;line-height:1.6;'>{_ew_dsub}</div>"
            f"</div>"
            f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
            f"border-bottom:1px solid #222;'>"
            f"<div style='padding:0.9rem 1.4rem;border-right:1px solid #222;'>"
            f"<div style='display:flex;align-items:center;margin-bottom:0.3rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Wave Type</div>"
            + _ew_tip("Impulse = a 5-wave directional move (1-2-3-4-5). "
                      "Corrective = a 3-wave counter-move (A-B-C). "
                      "Impulse waves are the tradeable legs; corrective waves are the pauses.")
            + f"</div>"
            f"<div style='font-size:1rem;font-weight:800;color:{hero_color};'>{wtype}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.15rem;'>{phase}</div>"
            f"</div>"
            f"<div style='padding:0.9rem 1.4rem;border-right:1px solid #222;'>"
            f"<div style='display:flex;align-items:center;margin-bottom:0.3rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Wave Score</div>"
            + _ew_tip("How well this wave count follows Elliott Wave rules (0–100). "
                      "Starts at 100 and loses points for each rule violation. "
                      "Gains points for Fibonacci alignment. "
                      "80+ = excellent. 60–79 = good. 40–59 = fair. Below 40 = weak count, treat with caution.")
            + f"</div>"
            f"<div style='font-size:1rem;font-weight:800;color:{score_color};'>{wscore}/100</div>"
            f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.15rem;'>{_sq} count</div>"
            f"</div>"
            f"<div style='padding:0.9rem 1.4rem;'>"
            f"<div style='display:flex;align-items:center;margin-bottom:0.3rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Current Wave</div>"
            + _ew_tip("Which wave the price is currently in. "
                      "Waves 1, 3, 5 are bullish impulse legs — good for longs. "
                      "Waves 2, 4 are pullbacks — can be buying opportunities. "
                      "Waves A, B, C are corrective and usually less reliable for entries.")
            + f"</div>"
            f"<div style='font-size:1rem;font-weight:800;color:{_wc(waves[-1]) if waves else NEUT};'>"
            f"Wave {current_wave_label}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.15rem;'>{phase_detail}</div>"
            f"</div>"
            f"</div>"
            + (_ew_ladder if _ew_ladder else "")
            + f"</div>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # INTERACTIVE CHART
    # ── WAVE CHART ────────────────────────────────────────────────────────────
    st.plotly_chart(_ew["fig"], use_container_width=True, config={"displayModeBar": False})

    # ── WAVE INTEL — one unified block ────────────────────────────────────────
    # Trust status
    _trust_lbl   = trade_tool["trust_label"]
    _trust_col   = trade_tool["trust_color"]
    _trust_note  = trade_tool["trust_note"]
    _hard_breaks = len(trade_tool["hard_violations"])
    _alt_lbl     = "Yes" if alternates else "No"
    _alt_col     = BULL if alternates else "#555"

    # Projection
    if projection:
        _pdir      = projection["direction"]
        _pnext     = projection["next_wave"]
        _pcol      = BULL if _pdir == "Extension" else BEAR if _pdir == "Reversal" else NEUT
        _pdir_lbl  = {"Extension": "Trend continues", "Reversal": "Correction expected", "Retracement": "Pullback first"}.get(_pdir, _pdir)
    else:
        _pdir = _pnext = _pdir_lbl = "—"
        _pcol = "#555"

    # Momentum
    _div_lbl = "—"
    _div_col = "#555"
    if divergences:
        _d = divergences[0]
        _div_lbl = _d["type"].replace(" Divergence", "").replace(" Confirmation", " ✓")
        _div_col = _d["color"]

    def _ew_tip(text):
        return (
            f"<span style='position:relative;display:inline-flex;align-items:center;"
            f"cursor:help;margin-left:0.3rem;'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:13px;height:13px;border-radius:50%;border:1px solid #3a3a3a;"
            f"font-size:0.48rem;color:#666;font-weight:700;'>?</span>"
            f"<span class='ew-tip' style='width:220px;font-size:0.7rem;line-height:1.5;'>"
            f"{text}</span></span>"
        )

    def _ew_label(text, tooltip=""):
        return (
            f"<div style='display:flex;align-items:center;margin-bottom:0.3rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>{text}</div>"
            + (_ew_tip(tooltip) if tooltip else "")
            + f"</div>"
        )

    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;border-top:3px solid {GOLD};"
        f"border-radius:14px;overflow:hidden;margin-bottom:1.2rem;'>"

        # ── Row 1: 5 stat cells ───────────────────────────────────────────────
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid #222;'>"

        # Trust
        f"<div style='padding:0.85rem 1rem;border-right:1px solid #222;'>"
        + _ew_label("Trust",
            "Overall reliability of this wave count. High = few or no rule violations and good Fibonacci alignment. "
            "Low = the count has issues — treat targets with skepticism.")
        + f"<div style='font-size:0.95rem;font-weight:800;color:{_trust_col};'>{_trust_lbl}</div>"
        f"</div>"

        # Rule breaks
        f"<div style='padding:0.85rem 1rem;border-right:1px solid #222;'>"
        + _ew_label("Rule Breaks",
            "How many of the 3 hard Elliott Wave rules this count violates. "
            "The rules: Wave 2 never retraces more than 100% of Wave 1. "
            "Wave 3 is never the shortest impulse wave. "
            "Wave 4 never enters Wave 1's price territory. "
            "0 breaks = textbook count. Any break = treat with caution.")
        + f"<div style='font-size:0.95rem;font-weight:800;color:{BEAR if _hard_breaks else BULL};'>{_hard_breaks}</div>"
        f"</div>"

        # Next wave
        f"<div style='padding:0.85rem 1rem;border-right:1px solid #222;'>"
        + _ew_label("Next Wave",
            "The projected next wave based on where we are in the cycle. "
            "Extension = the trend continues in the same direction. "
            "Retracement = a pullback is expected before the next leg. "
            "Reversal = the full move may be over and a counter-trend move is likely.")
        + f"<div style='font-size:0.95rem;font-weight:800;color:{_pcol};'>{_pnext}</div>"
        f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.1rem;'>{_pdir_lbl}</div>"
        f"</div>"

        # Alternation
        f"<div style='padding:0.85rem 1rem;border-right:1px solid #222;'>"
        + _ew_label("Alternation",
            "Elliott Wave guideline: corrective waves tend to alternate in shape. "
            "If Wave 2 was a sharp correction, Wave 4 is usually flat (sideways), and vice versa. "
            "When alternation is present, the pattern is more reliable.")
        + f"<div style='font-size:0.95rem;font-weight:800;color:{_alt_col};'>{_alt_lbl}</div>"
        f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.1rem;'>W2 vs W4 shape</div>"
        f"</div>"

        # Momentum
        f"<div style='padding:0.85rem 1rem;'>"
        + _ew_label("Momentum",
            "RSI momentum check relative to each wave's price action. "
            "Bullish divergence = price made a lower low but RSI made a higher low — signals exhaustion in selling, potential reversal. "
            "Bearish divergence = price made a higher high but RSI made a lower high — signals buying momentum fading. "
            "Confirmation = momentum aligns with the wave direction, adding conviction.")
        + f"<div style='font-size:0.95rem;font-weight:800;color:{_div_col};'>{_div_lbl}</div>"
        f"</div>"

        f"</div>"  # end grid

        # ── Row 2: trust note + violation list OR targets ─────────────────────
        + (
            (
                f"<div style='padding:0.85rem 1.2rem;border-bottom:1px solid #222;'>"
                + _ew_label("Fibonacci Targets",
                    "Price projections based on Fibonacci extension ratios from the current wave structure. "
                    "These are common reversal zones where Elliott Wave theory suggests the next wave may end. "
                    "The most watched levels are 1.618× and 2.618× the prior wave's length.")
                + f"<div style='display:flex;gap:0.6rem;flex-wrap:wrap;'>"
                + "".join(
                    f"<div style='background:#141414;border:1px solid #232323;"
                    f"border-top:2px solid {BULL if (tp - current_price) > 0 else BEAR};"
                    f"border-radius:6px;padding:0.5rem 0.8rem;text-align:center;min-width:90px;'>"
                    f"<div style='font-size:0.72rem;color:#bbb;font-weight:700;"
                    f"text-transform:uppercase;margin-bottom:0.2rem;'>{fl}</div>"
                    f"<div style='font-size:1rem;font-weight:900;color:#ebebeb;'>{tp:.2f}</div>"
                    f"<div style='font-size:0.62rem;font-weight:700;"
                    f"color:{BULL if (tp - current_price) > 0 else BEAR};'>"
                    f"{(tp / current_price - 1)*100:+.1f}%</div>"
                    f"</div>"
                    for fl, tp in list(projection["targets"].items())[:5]
                )
                + f"</div></div>"
            ) if (projection and projection.get("targets")) else ""
        )

        # ── Row 3: violations or clean note ──────────────────────────────────
        + (
            f"<div style='padding:0.85rem 1.2rem;'>"
            + (
                "".join(
                    f"<div style='display:flex;align-items:flex-start;gap:0.5rem;margin-bottom:0.4rem;'>"
                    f"<span style='color:{BEAR if 'violation' in v.lower() else NEUT};"
                    f"font-size:0.7rem;flex-shrink:0;margin-top:0.05rem;'>"
                    f"{'✕' if 'violation' in v.lower() else '⚠'}</span>"
                    f"<span style='font-size:0.7rem;color:#aaa;line-height:1.4;'>{v}</span>"
                    f"</div>"
                    for v in violations[:4]
                ) if violations else
                f"<div style='font-size:0.7rem;color:{BULL};font-weight:600;'>"
                f"✓ &nbsp;{_trust_note}</div>"
            )
            + f"</div>"
        )

        + f"</div>",
        unsafe_allow_html=True,
    )
