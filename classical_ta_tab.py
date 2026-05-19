"""
Classical Technical Analysis Tab
Detects: Chart Patterns · Trend · Moving Averages · RSI · MACD · Bollinger · ATR
Outputs: Decision box + Trade Plan ladder + Pattern Intel card
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Design tokens ──────────────────────────────────────────────────────────────
BULL = "#4caf50"
BEAR = "#f44336"
NEUT = "#ff9800"
INFO = "#2196f3"
GOLD = "#FFD700"
PURP = "#9c27b0"


# ══════════════════════════════════════════════════════════════════════════════
# INDICATOR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _ema(series, n):
    return series.ewm(span=n, adjust=False).mean()


def _rsi(series, n=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(n).mean()
    loss  = (-delta.clip(upper=0)).rolling(n).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _atr(df, n=14):
    hi, lo, cl = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        hi - lo,
        (hi - cl.shift()).abs(),
        (lo - cl.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _macd(series, fast=12, slow=26, sig=9):
    m  = _ema(series, fast) - _ema(series, slow)
    s  = _ema(m, sig)
    return m, s, m - s


def _bollinger(series, n=20, k=2):
    ma  = series.rolling(n).mean()
    std = series.rolling(n).std()
    return ma + k * std, ma, ma - k * std


def _pivot_highs(hi, lo, n=3):
    """Indices of confirmed swing highs (n bars each side)."""
    out = []
    for i in range(n, len(hi) - n):
        if all(hi.iloc[i] >= hi.iloc[i - n:i]) and all(hi.iloc[i] >= hi.iloc[i + 1:i + n + 1]):
            out.append(i)
    return out


def _pivot_lows(hi, lo, n=3):
    """Indices of confirmed swing lows (n bars each side)."""
    out = []
    for i in range(n, len(lo) - n):
        if all(lo.iloc[i] <= lo.iloc[i - n:i]) and all(lo.iloc[i] <= lo.iloc[i + 1:i + n + 1]):
            out.append(i)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# PATTERN DETECTION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _detect_patterns(df, cp):
    """
    Detect classical chart patterns from recent OHLCV data.
    Returns list of dicts: {name, bias, confidence, description, target, stop}
    """
    hi  = df["High"].astype(float)
    lo  = df["Low"].astype(float)
    cl  = df["Close"].astype(float)
    vol = df["Volume"].astype(float) if "Volume" in df.columns else pd.Series(np.ones(len(df)))
    n   = len(df)

    ph_idx = _pivot_highs(hi, lo, n=3)
    pl_idx = _pivot_lows(hi, lo, n=3)

    patterns = []

    # ── 1. Double Top ────────────────────────────────────────────────────────
    if len(ph_idx) >= 2:
        h1_i, h2_i = ph_idx[-2], ph_idx[-1]
        h1, h2 = float(hi.iloc[h1_i]), float(hi.iloc[h2_i])
        if abs(h1 - h2) / max(h1, h2) < 0.025 and h2_i > h1_i:
            # Find the valley between them
            valley_lo = float(lo.iloc[h1_i:h2_i + 1].min())
            neckline  = valley_lo
            if cp < neckline * 1.03:  # already breaking or near neckline
                height = max(h1, h2) - neckline
                conf = 80 if abs(h1 - h2) / max(h1, h2) < 0.012 else 65
                patterns.append({
                    "name": "Double Top",
                    "bias": "BEAR",
                    "confidence": conf,
                    "description": f"Two peaks at similar highs ({h1:.2f} / {h2:.2f}). Neckline at {neckline:.2f}.",
                    "target": round(neckline - height, 2),
                    "stop":   round(max(h1, h2) * 1.008, 2),
                    "key_level": neckline,
                })

    # ── 2. Double Bottom ─────────────────────────────────────────────────────
    if len(pl_idx) >= 2:
        l1_i, l2_i = pl_idx[-2], pl_idx[-1]
        l1, l2 = float(lo.iloc[l1_i]), float(lo.iloc[l2_i])
        if abs(l1 - l2) / min(l1, l2) < 0.025 and l2_i > l1_i:
            valley_hi = float(hi.iloc[l1_i:l2_i + 1].max())
            neckline  = valley_hi
            if cp > neckline * 0.97:
                height = neckline - min(l1, l2)
                conf = 80 if abs(l1 - l2) / min(l1, l2) < 0.012 else 65
                patterns.append({
                    "name": "Double Bottom",
                    "bias": "BULL",
                    "confidence": conf,
                    "description": f"Two lows at similar support ({l1:.2f} / {l2:.2f}). Neckline at {neckline:.2f}.",
                    "target": round(neckline + height, 2),
                    "stop":   round(min(l1, l2) * 0.992, 2),
                    "key_level": neckline,
                })

    # ── 3. Head & Shoulders (bearish) ────────────────────────────────────────
    if len(ph_idx) >= 3:
        ls_i, hd_i, rs_i = ph_idx[-3], ph_idx[-2], ph_idx[-1]
        ls, hd, rs = float(hi.iloc[ls_i]), float(hi.iloc[hd_i]), float(hi.iloc[rs_i])
        if hd > ls and hd > rs and abs(ls - rs) / max(ls, rs) < 0.05:
            # Neckline: average of troughs between shoulders
            neck_lo1 = float(lo.iloc[ls_i:hd_i + 1].min())
            neck_lo2 = float(lo.iloc[hd_i:rs_i + 1].min())
            neckline = (neck_lo1 + neck_lo2) / 2
            if cp < neckline * 1.04:
                height = hd - neckline
                conf = 75 if abs(ls - rs) / max(ls, rs) < 0.03 else 60
                patterns.append({
                    "name": "Head & Shoulders",
                    "bias": "BEAR",
                    "confidence": conf,
                    "description": f"Head at {hd:.2f}, shoulders at {ls:.2f}/{rs:.2f}. Neckline ~{neckline:.2f}.",
                    "target": round(neckline - height, 2),
                    "stop":   round(rs * 1.01, 2),
                    "key_level": neckline,
                })

    # ── 4. Inverse Head & Shoulders (bullish) ────────────────────────────────
    if len(pl_idx) >= 3:
        ls_i, hd_i, rs_i = pl_idx[-3], pl_idx[-2], pl_idx[-1]
        ls, hd, rs = float(lo.iloc[ls_i]), float(lo.iloc[hd_i]), float(lo.iloc[rs_i])
        if hd < ls and hd < rs and abs(ls - rs) / min(ls, rs) < 0.05:
            neck_hi1 = float(hi.iloc[ls_i:hd_i + 1].max())
            neck_hi2 = float(hi.iloc[hd_i:rs_i + 1].max())
            neckline = (neck_hi1 + neck_hi2) / 2
            if cp > neckline * 0.96:
                height = neckline - hd
                conf = 75 if abs(ls - rs) / min(ls, rs) < 0.03 else 60
                patterns.append({
                    "name": "Inv. Head & Shoulders",
                    "bias": "BULL",
                    "confidence": conf,
                    "description": f"Head at {hd:.2f}, shoulders at {ls:.2f}/{rs:.2f}. Neckline ~{neckline:.2f}.",
                    "target": round(neckline + height, 2),
                    "stop":   round(rs * 0.99, 2),
                    "key_level": neckline,
                })

    # ── 5. Ascending Triangle ────────────────────────────────────────────────
    if len(ph_idx) >= 2 and len(pl_idx) >= 2:
        recent_hi = [float(hi.iloc[i]) for i in ph_idx[-3:]]
        recent_lo = [float(lo.iloc[i]) for i in pl_idx[-3:]]
        # Flat top + rising bottom
        hi_range = max(recent_hi) - min(recent_hi)
        lo_trend = recent_lo[-1] - recent_lo[0] if len(recent_lo) >= 2 else 0
        if hi_range / max(recent_hi) < 0.025 and lo_trend > 0:
            resistance = np.mean(recent_hi)
            atr_val    = float(_atr(df).iloc[-1])
            conf = 72
            patterns.append({
                "name": "Ascending Triangle",
                "bias": "BULL",
                "confidence": conf,
                "description": f"Flat resistance ~{resistance:.2f} with rising lows. Breakout bias upward.",
                "target": round(resistance + (resistance - recent_lo[-1]), 2),
                "stop":   round(recent_lo[-1] - atr_val * 0.5, 2),
                "key_level": resistance,
            })

    # ── 6. Descending Triangle ───────────────────────────────────────────────
    if len(ph_idx) >= 2 and len(pl_idx) >= 2:
        recent_hi = [float(hi.iloc[i]) for i in ph_idx[-3:]]
        recent_lo = [float(lo.iloc[i]) for i in pl_idx[-3:]]
        lo_range  = max(recent_lo) - min(recent_lo)
        hi_trend  = recent_hi[-1] - recent_hi[0] if len(recent_hi) >= 2 else 0
        if lo_range / min(recent_lo) < 0.025 and hi_trend < 0:
            support  = np.mean(recent_lo)
            atr_val  = float(_atr(df).iloc[-1])
            conf = 72
            patterns.append({
                "name": "Descending Triangle",
                "bias": "BEAR",
                "confidence": conf,
                "description": f"Flat support ~{support:.2f} with falling highs. Breakout bias downward.",
                "target": round(support - (recent_hi[-1] - support), 2),
                "stop":   round(recent_hi[-1] + atr_val * 0.5, 2),
                "key_level": support,
            })

    # ── 7. Bull Flag ─────────────────────────────────────────────────────────
    if n >= 30:
        # Strong impulse in prior 15 bars, then tight consolidation last 8
        impulse_window = cl.iloc[-23:-8]
        flag_window    = cl.iloc[-8:]
        impulse_chg    = (float(impulse_window.iloc[-1]) - float(impulse_window.iloc[0])) / float(impulse_window.iloc[0])
        flag_chg       = (float(flag_window.iloc[-1]) - float(flag_window.iloc[0])) / float(flag_window.iloc[0])
        flag_range     = (float(flag_window.max()) - float(flag_window.min())) / float(flag_window.mean())
        if impulse_chg > 0.06 and -0.04 < flag_chg < 0.01 and flag_range < 0.04:
            pole_height = float(impulse_window.iloc[-1]) - float(impulse_window.iloc[0])
            atr_val     = float(_atr(df).iloc[-1])
            patterns.append({
                "name": "Bull Flag",
                "bias": "BULL",
                "confidence": 70,
                "description": f"Strong {impulse_chg*100:.1f}% impulse followed by tight {flag_range*100:.1f}% consolidation.",
                "target": round(cp + pole_height, 2),
                "stop":   round(float(flag_window.min()) - atr_val * 0.3, 2),
                "key_level": float(flag_window.max()),
            })

    # ── 8. Bear Flag ─────────────────────────────────────────────────────────
    if n >= 30:
        impulse_window = cl.iloc[-23:-8]
        flag_window    = cl.iloc[-8:]
        impulse_chg    = (float(impulse_window.iloc[-1]) - float(impulse_window.iloc[0])) / float(impulse_window.iloc[0])
        flag_chg       = (float(flag_window.iloc[-1]) - float(flag_window.iloc[0])) / float(flag_window.iloc[0])
        flag_range     = (float(flag_window.max()) - float(flag_window.min())) / float(flag_window.mean())
        if impulse_chg < -0.06 and -0.01 < flag_chg < 0.04 and flag_range < 0.04:
            pole_height = float(impulse_window.iloc[0]) - float(impulse_window.iloc[-1])
            atr_val     = float(_atr(df).iloc[-1])
            patterns.append({
                "name": "Bear Flag",
                "bias": "BEAR",
                "confidence": 70,
                "description": f"Sharp {abs(impulse_chg)*100:.1f}% drop followed by tight {flag_range*100:.1f}% consolidation.",
                "target": round(cp - pole_height, 2),
                "stop":   round(float(flag_window.max()) + atr_val * 0.3, 2),
                "key_level": float(flag_window.min()),
            })

    # ── 9. Symmetrical Triangle ──────────────────────────────────────────────
    if len(ph_idx) >= 2 and len(pl_idx) >= 2:
        recent_hi = [float(hi.iloc[i]) for i in ph_idx[-3:]]
        recent_lo = [float(lo.iloc[i]) for i in pl_idx[-3:]]
        hi_trend  = recent_hi[-1] - recent_hi[0] if len(recent_hi) >= 2 else 0
        lo_trend  = recent_lo[-1] - recent_lo[0] if len(recent_lo) >= 2 else 0
        if hi_trend < 0 and lo_trend > 0:
            apex = (np.mean(recent_hi) + np.mean(recent_lo)) / 2
            width = np.mean(recent_hi) - np.mean(recent_lo)
            patterns.append({
                "name": "Symmetrical Triangle",
                "bias": "NEUT",
                "confidence": 60,
                "description": f"Converging highs and lows near {apex:.2f}. Breakout direction determines bias.",
                "target": round(cp + width if cp > apex else cp - width, 2),
                "stop":   round(cp - width * 0.4 if cp > apex else cp + width * 0.4, 2),
                "key_level": apex,
            })

    # ── 10. Rounding Bottom (Cup) ────────────────────────────────────────────
    if n >= 40 and len(pl_idx) >= 1:
        cup_slice = cl.iloc[-40:]
        mid_low   = float(cup_slice.iloc[15:25].min())
        edge_avg  = (float(cup_slice.iloc[:5].mean()) + float(cup_slice.iloc[-5:].mean())) / 2
        if mid_low < edge_avg * 0.95 and cp > edge_avg * 0.97:
            depth  = edge_avg - mid_low
            patterns.append({
                "name": "Rounding Bottom",
                "bias": "BULL",
                "confidence": 65,
                "description": f"Gradual U-shaped base forming. Rim resistance near {edge_avg:.2f}.",
                "target": round(edge_avg + depth * 0.618, 2),
                "stop":   round(mid_low * 0.99, 2),
                "key_level": edge_avg,
            })

    # Sort by confidence descending
    patterns.sort(key=lambda x: x["confidence"], reverse=True)
    return patterns


# ══════════════════════════════════════════════════════════════════════════════
# INDICATOR ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def _compute_indicators(df, cp):
    cl = df["Close"].astype(float)
    hi = df["High"].astype(float)
    lo = df["Low"].astype(float)
    n  = len(df)

    # Moving averages
    ma20  = float(_ema(cl, 20).iloc[-1])  if n >= 20  else cp
    ma50  = float(_ema(cl, 50).iloc[-1])  if n >= 50  else cp
    ma200 = float(_ema(cl, 200).iloc[-1]) if n >= 200 else cp

    # RSI
    rsi_s = _rsi(cl, 14)
    rsi   = float(rsi_s.iloc[-1]) if n >= 15 else 50.0

    # MACD
    macd_l, sig_l, hist_l = _macd(cl)
    macd_val  = float(macd_l.iloc[-1])  if n >= 26 else 0.0
    macd_sig  = float(sig_l.iloc[-1])   if n >= 26 else 0.0
    macd_hist = float(hist_l.iloc[-1])  if n >= 26 else 0.0
    macd_prev = float(hist_l.iloc[-2])  if n >= 27 else 0.0

    # Bollinger
    bbu, bbm, bbl = _bollinger(cl)
    bb_upper = float(bbu.iloc[-1]) if n >= 20 else cp * 1.04
    bb_mid   = float(bbm.iloc[-1]) if n >= 20 else cp
    bb_lower = float(bbl.iloc[-1]) if n >= 20 else cp * 0.96
    bb_width = (bb_upper - bb_lower) / bb_mid if bb_mid > 0 else 0

    # ATR
    atr_s  = _atr(df)
    atr    = float(atr_s.iloc[-1]) if n >= 15 else cp * 0.02
    atr_pct = atr / cp * 100

    # Trend via MA alignment
    if cp > ma20 > ma50 > ma200:
        trend     = "Strong Uptrend"
        trend_col = BULL
        trend_bias = True
    elif cp > ma50 > ma200:
        trend     = "Uptrend"
        trend_col = BULL
        trend_bias = True
    elif cp < ma20 < ma50 < ma200:
        trend     = "Strong Downtrend"
        trend_col = BEAR
        trend_bias = False
    elif cp < ma50 < ma200:
        trend     = "Downtrend"
        trend_col = BEAR
        trend_bias = False
    else:
        trend     = "Mixed / Ranging"
        trend_col = NEUT
        trend_bias = True  # default long-only

    # BB position
    bb_pos = (cp - bb_lower) / (bb_upper - bb_lower) if bb_upper > bb_lower else 0.5

    # Volume trend
    if "Volume" in df.columns and n >= 20:
        vol = df["Volume"].astype(float)
        vol_ma  = float(vol.rolling(20).mean().iloc[-1])
        vol_now = float(vol.iloc[-1])
        vol_ratio = vol_now / vol_ma if vol_ma > 0 else 1.0
    else:
        vol_ratio = 1.0

    # Support / Resistance (recent pivot extremes)
    ph = _pivot_highs(hi, lo, n=3)
    pl = _pivot_lows(hi, lo, n=3)
    res = sorted([float(hi.iloc[i]) for i in ph if float(hi.iloc[i]) > cp])
    sup = sorted([float(lo.iloc[i]) for i in pl if float(lo.iloc[i]) < cp], reverse=True)
    nearest_res = res[0] if res else cp * 1.05
    nearest_sup = sup[0] if sup else cp * 0.95

    return {
        "ma20": ma20, "ma50": ma50, "ma200": ma200,
        "rsi": rsi,
        "macd_val": macd_val, "macd_sig": macd_sig,
        "macd_hist": macd_hist, "macd_prev": macd_prev,
        "bb_upper": bb_upper, "bb_mid": bb_mid, "bb_lower": bb_lower,
        "bb_width": bb_width, "bb_pos": bb_pos,
        "atr": atr, "atr_pct": atr_pct,
        "trend": trend, "trend_col": trend_col, "trend_bias": trend_bias,
        "vol_ratio": vol_ratio,
        "nearest_res": nearest_res, "nearest_sup": nearest_sup,
    }


# ══════════════════════════════════════════════════════════════════════════════
# DECISION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _compute_decision(ind, patterns, cp):
    """
    Score across indicators + patterns → BUY / WAIT verdict.
    Returns: verdict, color, score (0-100), sub-text, is_bull
    """
    score = 50  # start neutral

    # MA trend
    if ind["trend_bias"]:
        score += 15
    else:
        score -= 10

    # Price vs MA20
    if cp > ind["ma20"]:
        score += 8
    else:
        score -= 8

    # Price vs MA50
    if cp > ind["ma50"]:
        score += 7
    else:
        score -= 7

    # RSI
    rsi = ind["rsi"]
    if 45 < rsi < 70:
        score += 8
    elif rsi >= 70:
        score -= 5  # overbought risk
    elif rsi < 35:
        score -= 8  # weak / oversold

    # MACD
    if ind["macd_hist"] > 0 and ind["macd_hist"] > ind["macd_prev"]:
        score += 10  # positive and strengthening
    elif ind["macd_hist"] > 0:
        score += 5
    elif ind["macd_hist"] < 0 and ind["macd_hist"] < ind["macd_prev"]:
        score -= 10
    else:
        score -= 3

    # Bollinger position
    bb_pos = ind["bb_pos"]
    if 0.35 < bb_pos < 0.75:
        score += 5   # mid-band — room to run
    elif bb_pos > 0.90:
        score -= 5   # near upper band — extended
    elif bb_pos < 0.15:
        score -= 5   # near lower band — weak

    # Volume confirmation
    if ind["vol_ratio"] > 1.3:
        score += 5
    elif ind["vol_ratio"] < 0.7:
        score -= 3

    # Pattern boost/drag
    bull_patterns = [p for p in patterns if p["bias"] == "BULL"]
    bear_patterns = [p for p in patterns if p["bias"] == "BEAR"]
    if bull_patterns:
        score += min(12, bull_patterns[0]["confidence"] // 8)
    if bear_patterns:
        score -= min(12, bear_patterns[0]["confidence"] // 8)

    score = max(0, min(100, score))

    # Only BUY or WAIT (never SHORT — long-only)
    if score >= 62:
        verdict = "BUY"
        color   = BULL
        is_bull = True
        sub = f"Score {score}/100 — {ind['trend']}. MA stack + momentum support a long entry."
    elif score >= 45:
        verdict = "WAIT"
        color   = NEUT
        is_bull = True
        sub = f"Score {score}/100 — Mixed signals. Wait for clearer trend alignment before entering."
    else:
        verdict = "WAIT"
        color   = NEUT
        is_bull = True
        sub = f"Score {score}/100 — Indicators skewed bearish. No long trade setup yet."

    return verdict, color, score, sub, is_bull


# ══════════════════════════════════════════════════════════════════════════════
# CHART BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_chart(df, ind, patterns, cp):
    cl = df["Close"].astype(float)
    hi = df["High"].astype(float)
    lo = df["Low"].astype(float)
    n  = len(df)
    dates = df.index if hasattr(df.index, "freq") or isinstance(df.index, pd.DatetimeIndex) else pd.RangeIndex(n)

    macd_line, sig_line, hist_line = _macd(cl)
    rsi_line = _rsi(cl, 14)
    bbu, bbm, bbl = _bollinger(cl)
    ema20  = _ema(cl, 20)
    ema50  = _ema(cl, 50)
    ema200 = _ema(cl, 200)

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20],
        vertical_spacing=0.03,
    )

    # ── Row 1: Candles + MAs + Bollinger ─────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=dates,
        open=df["Open"], high=hi, low=lo, close=cl,
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350",
        name="Price", showlegend=False,
    ), row=1, col=1)

    # Bollinger bands
    fig.add_trace(go.Scatter(
        x=dates, y=bbu, line=dict(color="rgba(33,150,243,0.3)", width=1),
        name="BB Upper", showlegend=False, fill=None,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=bbl, line=dict(color="rgba(33,150,243,0.3)", width=1),
        name="BB Lower", fill="tonexty",
        fillcolor="rgba(33,150,243,0.04)", showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=bbm, line=dict(color="rgba(33,150,243,0.5)", width=1, dash="dot"),
        name="BB Mid", showlegend=False,
    ), row=1, col=1)

    # Moving averages
    fig.add_trace(go.Scatter(
        x=dates, y=ema20, line=dict(color="#FFD700", width=1.5),
        name="EMA 20", showlegend=True,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=ema50, line=dict(color="#ff9800", width=1.5),
        name="EMA 50", showlegend=True,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=ema200, line=dict(color="#9c27b0", width=1.5),
        name="EMA 200", showlegend=True,
    ), row=1, col=1)

    # Pattern key levels as horizontal lines
    for p in patterns[:3]:
        col = BULL if p["bias"] == "BULL" else (BEAR if p["bias"] == "BEAR" else NEUT)
        fig.add_hline(
            y=p["key_level"],
            line=dict(color=col, width=1.2, dash="dash"),
            annotation_text=f"  {p['name']}",
            annotation_font=dict(size=9, color=col),
            annotation_position="right",
            row=1, col=1,
        )

    # ── Row 2: RSI ────────────────────────────────────────────────────────────
    rsi_colors = [
        BULL if v >= 50 else BEAR for v in rsi_line.fillna(50)
    ]
    fig.add_trace(go.Scatter(
        x=dates, y=rsi_line,
        line=dict(color=INFO, width=1.5),
        name="RSI 14", showlegend=False,
    ), row=2, col=1)
    fig.add_hline(y=70, line=dict(color=BEAR, width=0.8, dash="dot"), row=2, col=1)
    fig.add_hline(y=30, line=dict(color=BULL, width=0.8, dash="dot"), row=2, col=1)
    fig.add_hline(y=50, line=dict(color="#444", width=0.8, dash="dot"), row=2, col=1)

    # ── Row 3: MACD ───────────────────────────────────────────────────────────
    hist_colors = [BULL if v >= 0 else BEAR for v in hist_line.fillna(0)]
    fig.add_trace(go.Bar(
        x=dates, y=hist_line,
        marker_color=hist_colors, opacity=0.7,
        name="MACD Hist", showlegend=False,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=macd_line,
        line=dict(color="#2196f3", width=1.5),
        name="MACD", showlegend=False,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=dates, y=sig_line,
        line=dict(color="#ff9800", width=1.2),
        name="Signal", showlegend=False,
    ), row=3, col=1)

    fig.update_layout(
        height=560,
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
        yaxis2=dict(title="RSI", range=[0, 100]),
    )
    for ax in ["xaxis", "xaxis2", "xaxis3", "yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{ax: dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.04)",
        )})

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def _cta_compute(cache_key, _df_slice, cp):
    ind      = _compute_indicators(_df_slice, cp)
    patterns = _detect_patterns(_df_slice, cp)
    verdict, v_col, score, sub, is_bull = _compute_decision(ind, patterns, cp)
    fig      = _build_chart(_df_slice, ind, patterns, cp)
    return dict(
        ind=ind, patterns=patterns,
        verdict=verdict, v_col=v_col, score=score, sub=sub, is_bull=is_bull,
        fig=fig,
    )


def get_cta_signal(df, cp):
    """Return a signal dict for the Decision Tab aggregator, or None if no trade setup."""
    if df is None or len(df) < 30:
        return None
    try:
        n_bars = min(200, len(df))
        df_slice = df.iloc[-n_bars:].copy().reset_index(drop=False)
        if "Date" in df_slice.columns:
            df_slice = df_slice.set_index("Date")

        ind      = _compute_indicators(df_slice, float(cp))
        patterns = _detect_patterns(df_slice, float(cp))
        verdict, v_col, score, sub, is_bull = _compute_decision(ind, patterns, float(cp))

        # Only surface clear BUY setups
        if verdict != "BUY" or score < 55:
            return None

        bull_pats = [p for p in patterns if p["bias"] == "BULL"]
        reasons = [
            f"Classical TA score {score}/100 — {ind.get('trend', 'trend aligned')}",
        ]
        if bull_pats:
            reasons.append(f"{bull_pats[0]['name']} pattern detected (confidence {bull_pats[0]['confidence']}%)")

        atr_ser = (df["High"] - df["Low"]).rolling(14, min_periods=1).mean()
        atr = max(float(atr_ser.iloc[-1]), float(cp) * 0.01)
        swing_lo = float(df["Low"].tail(20).min())
        _stop = max(swing_lo - atr * 0.3, float(cp) * 0.93)
        _risk = max(float(cp) - _stop, 0.001)

        # Use pattern target if available, else ATR-based
        t1_price = bull_pats[0]["target"] if bull_pats else round(float(cp) + _risk * 1.5, 2)

        return dict(
            color="#2196f3",
            verdict_text="▲ BUY",
            sublabel=f"Classical TA — Score {score}/100",
            conf=int(min(score, 94)),
            reasons=reasons,
            entry=float(cp),
            stop=round(_stop, 2),
            t1=round(float(t1_price), 2),
            t2=round(float(cp) + _risk * 2.5, 2),
            t3=round(float(cp) + _risk * 4.0, 2),
        )
    except Exception:
        return None


def classical_ta_tab(df, current_price):
    """Render the Classical Technical Analysis tab."""

    cp = float(current_price)
    n_bars = min(200, len(df))
    df_slice = df.iloc[-n_bars:].copy()
    if hasattr(df_slice.index, "freq"):
        pass
    else:
        df_slice = df_slice.reset_index(drop=False)
        if "Date" in df_slice.columns:
            df_slice = df_slice.set_index("Date")

    if len(df_slice) < 20:
        st.warning("Need at least 20 bars for Classical TA analysis.")
        return

    cache_key = (len(df_slice), round(cp, 4), str(df_slice["Close"].iloc[-1])[:8])
    data = _cta_compute(cache_key, df_slice, cp)

    ind      = data["ind"]
    patterns = data["patterns"]
    verdict  = data["verdict"]
    v_col    = data["v_col"]
    score    = data["score"]
    sub      = data["sub"]
    is_bull  = data["is_bull"]

    # ── Score quality label ────────────────────────────────────────────────
    if score >= 80:   sq = "Strong"
    elif score >= 65: sq = "Good"
    elif score >= 50: sq = "Moderate"
    else:             sq = "Weak"

    # ── Top pattern (if any) ───────────────────────────────────────────────
    top_pattern = patterns[0] if patterns else None

    # ── Trade ladder ───────────────────────────────────────────────────────
    _ladder_html = ""
    if verdict == "BUY" and top_pattern and top_pattern["bias"] == "BULL":
        try:
            from _levels import price_ladder_html as _plh, compute_structural_levels
            lvls = compute_structural_levels(df_slice, cp, True)
            _ladder_html = _plh(
                lvls["entry"], lvls["stop"], lvls["t1"], lvls["t2"], lvls["t3"],
                True, lvls.get("entry_quality", ""), lvls.get("eq_col", ""),
            )
        except Exception:
            pass
    elif verdict == "BUY":
        try:
            from _levels import price_ladder_html as _plh, compute_structural_levels
            lvls = compute_structural_levels(df_slice, cp, True)
            _ladder_html = _plh(
                lvls["entry"], lvls["stop"], lvls["t1"], lvls["t2"], lvls["t3"],
                True, lvls.get("entry_quality", ""), lvls.get("eq_col", ""),
            )
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # DECISION BOX
    # ══════════════════════════════════════════════════════════════════════════

    # Trend cell
    trend_lbl = ind["trend"]
    trend_col = ind["trend_col"]

    # RSI cell
    rsi_val = ind["rsi"]
    if rsi_val >= 70:
        rsi_lbl = f"{rsi_val:.0f} — Overbought"
        rsi_col = BEAR
    elif rsi_val <= 30:
        rsi_lbl = f"{rsi_val:.0f} — Oversold"
        rsi_col = BULL
    elif rsi_val >= 55:
        rsi_lbl = f"{rsi_val:.0f} — Bullish"
        rsi_col = BULL
    elif rsi_val <= 45:
        rsi_lbl = f"{rsi_val:.0f} — Bearish"
        rsi_col = BEAR
    else:
        rsi_lbl = f"{rsi_val:.0f} — Neutral"
        rsi_col = NEUT

    # MACD cell
    if ind["macd_hist"] > 0 and ind["macd_hist"] > ind["macd_prev"]:
        macd_lbl = "Bullish ↑"
        macd_col = BULL
    elif ind["macd_hist"] > 0:
        macd_lbl = "Bullish ↗"
        macd_col = BULL
    elif ind["macd_hist"] < 0 and ind["macd_hist"] < ind["macd_prev"]:
        macd_lbl = "Bearish ↓"
        macd_col = BEAR
    else:
        macd_lbl = "Bearish ↘"
        macd_col = BEAR

    # Pattern cell
    if top_pattern:
        pat_lbl = top_pattern["name"]
        pat_col = BULL if top_pattern["bias"] == "BULL" else (BEAR if top_pattern["bias"] == "BEAR" else NEUT)
        pat_sub = f"{top_pattern['confidence']}% conf"
    else:
        pat_lbl = "None detected"
        pat_col = "#555"
        pat_sub = "Clean chart"

    # Score cell
    score_col = BULL if score >= 65 else (NEUT if score >= 50 else BEAR)

    # ── Tooltip CSS + helper ───────────────────────────────────────────────────
    st.markdown("""<style>
    .cta-tip-w{position:relative;display:inline-flex;align-items:center;cursor:help;margin-left:0.3rem}
    .cta-tip-w .cta-tt{visibility:hidden;opacity:0;position:absolute;bottom:130%;left:50%;
        transform:translateX(-50%);background:#1e1e1e;color:#ccc;border:1px solid #333;
        border-radius:6px;padding:0.45rem 0.6rem;font-size:0.7rem;font-weight:500;
        line-height:1.5;white-space:normal;width:220px;text-align:left;z-index:200;
        pointer-events:none;transition:opacity .15s;box-shadow:0 4px 14px rgba(0,0,0,.5);
        text-transform:none;letter-spacing:0}
    .cta-tip-w .cta-tt::after{content:'';position:absolute;top:100%;left:50%;
        transform:translateX(-50%);border:5px solid transparent;border-top-color:#333}
    .cta-tip-w:hover .cta-tt{visibility:visible;opacity:1}
    </style>""", unsafe_allow_html=True)

    def _ctatip(text):
        return (
            f"<span class='cta-tip-w'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:13px;height:13px;border-radius:50%;border:1px solid #3a3a3a;"
            f"font-size:0.48rem;color:#666;font-weight:700;'>?</span>"
            f"<span class='cta-tt'>{text}</span></span>"
        )

    def _ctalbl(text, tooltip=""):
        return (
            f"<div style='display:flex;align-items:center;margin-bottom:0.3rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>{text}</div>"
            + (_ctatip(tooltip) if tooltip else "")
            + f"</div>"
        )

    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;"
        f"border-top:3px solid {v_col};border-radius:14px;overflow:hidden;margin-bottom:1.4rem;'>"

        # Header
        f"<div style='padding:1.6rem 2rem 1.3rem;border-bottom:1px solid #222;'>"
        f"<div style='font-size:0.72rem;color:#bbb;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Classical TA Decision</div>"
        f"<div style='font-size:3rem;font-weight:900;color:{v_col};"
        f"letter-spacing:-1.5px;line-height:1;'>{verdict}</div>"
        f"<div style='font-size:0.88rem;color:#bbb;margin-top:0.6rem;"
        f"font-weight:500;line-height:1.6;'>{sub}</div>"
        f"</div>"

        # 5-col metrics
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid #222;'>"

        # Trend
        f"<div style='padding:0.9rem 1.2rem;border-right:1px solid #222;'>"
        + _ctalbl("Trend",
            "Direction of the price trend based on moving averages. "
            "Strong Bull = EMA20 > EMA50 > EMA200 and price above all three. "
            "Strong Bear = price below all three EMAs stacked down. "
            "Mixed = EMAs conflicting — no clear directional bias.")
        + f"<div style='font-size:0.9rem;font-weight:800;color:{trend_col};'>{trend_lbl}</div>"
        f"</div>"

        # RSI
        f"<div style='padding:0.9rem 1.2rem;border-right:1px solid #222;'>"
        + _ctalbl("RSI 14",
            "Relative Strength Index (14-period). Measures how fast price has been rising vs falling. "
            "Above 70 = overbought — price moved too fast, risk of pullback. "
            "Below 30 = oversold — price may have fallen too far, watch for bounce. "
            "45–70 = healthy bullish range. The best BUY zone is RSI rising through 50–60.")
        + f"<div style='font-size:0.9rem;font-weight:800;color:{rsi_col};'>{rsi_lbl}</div>"
        f"</div>"

        # MACD
        f"<div style='padding:0.9rem 1.2rem;border-right:1px solid #222;'>"
        + _ctalbl("MACD",
            "Moving Average Convergence Divergence. Shows momentum shifts. "
            "Bullish ↑ = histogram is positive and growing — buyers accelerating. "
            "Bullish ↗ = histogram is positive but flattening — momentum slowing. "
            "Bearish ↓/↘ = histogram negative — sellers in control. "
            "Best entries: when histogram crosses zero from below (bearish to bullish).")
        + f"<div style='font-size:0.9rem;font-weight:800;color:{macd_col};'>{macd_lbl}</div>"
        f"</div>"

        # Pattern
        f"<div style='padding:0.9rem 1.2rem;border-right:1px solid #222;'>"
        + _ctalbl("Pattern",
            "The strongest chart pattern detected on this stock. "
            "Bull patterns (Double Bottom, Inv H&S, Bull Flag) suggest an upcoming upward move. "
            "Bear patterns (Double Top, H&S) suggest a potential decline. "
            "Confidence % = how clearly the pattern matches ideal conditions. "
            "A high-confidence bull pattern with a BUY verdict is the ideal combo.")
        + f"<div style='font-size:0.9rem;font-weight:800;color:{pat_col};'>{pat_lbl}</div>"
        f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.1rem;'>{pat_sub}</div>"
        f"</div>"

        # Score
        f"<div style='padding:0.9rem 1.2rem;'>"
        + _ctalbl("Score",
            "Classical TA composite score (0–100). Combines MA alignment, price position, RSI, MACD momentum, Bollinger position, volume, and detected patterns. "
            "Above 62 = BUY. 45–61 = WAIT for clearer setup. Below 45 = bearish skew. "
            "Score drives the verdict — higher score = more factors aligned bullishly.")
        + f"<div style='font-size:0.9rem;font-weight:800;color:{score_col};'>{score}/100</div>"
        f"<div style='font-size:0.75rem;color:#aaa;margin-top:0.1rem;'>{sq}</div>"
        f"</div>"

        f"</div>"  # end grid

        + (_ladder_html if _ladder_html else "")
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # CHART
    # ══════════════════════════════════════════════════════════════════════════
    st.plotly_chart(data["fig"], use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    # PATTERN INTEL CARD
    # ══════════════════════════════════════════════════════════════════════════

    # ── MA Stack summary ───────────────────────────────────────────────────
    _ma_tooltips = {
        "EMA 20":  "20-period Exponential Moving Average. Short-term trend. Price above a rising EMA20 = short-term bullish. Best used for entry timing on pullbacks.",
        "EMA 50":  "50-period EMA. Medium-term trend reference. Traders watch this line for swing support/resistance. Golden cross (EMA20 crosses above EMA50) = bullish signal.",
        "EMA 200": "200-period EMA. The major long-term trend line. Price above EMA200 = long-term bull market. Below = bear market. Institutions pay close attention to this level.",
    }
    def _ma_badge(label, ma_val):
        is_above = cp > ma_val
        col      = BULL if is_above else BEAR
        txt      = "Above" if is_above else "Below"
        pct      = (cp / ma_val - 1) * 100 if ma_val > 0 else 0
        _tip     = _ma_tooltips.get(label, "")
        return (
            f"<div style='padding:0.75rem 1rem;border-right:1px solid #222;"
            f"display:flex;flex-direction:column;gap:0.22rem;'>"
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>{label}</div>"
            + (_ctatip(_tip) if _tip else "")
            + f"</div>"
            f"<div style='font-size:0.95rem;font-weight:800;color:{col};'>{txt}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;'>{ma_val:.2f} &nbsp;·&nbsp; {pct:+.1f}%</div>"
            f"</div>"
        )

    # BB position label
    bb_pos = ind["bb_pos"]
    if bb_pos > 0.85:
        bb_lbl = "Near Upper Band"
        bb_col = BEAR
    elif bb_pos < 0.15:
        bb_lbl = "Near Lower Band"
        bb_col = BULL
    elif bb_pos > 0.55:
        bb_lbl = "Upper Half"
        bb_col = BULL
    else:
        bb_lbl = "Lower Half"
        bb_col = NEUT
    bb_w_lbl = f"{ind['bb_width']*100:.1f}% width"

    # ATR label
    atr_pct = ind["atr_pct"]
    if atr_pct > 3.5:
        atr_lbl = "High Volatility"
        atr_col = BEAR
    elif atr_pct > 2.0:
        atr_lbl = "Normal"
        atr_col = NEUT
    else:
        atr_lbl = "Low Volatility"
        atr_col = BULL

    # Volume label
    vr = ind["vol_ratio"]
    if vr > 1.5:
        vol_lbl = f"{vr:.1f}× Avg — Strong"
        vol_col = BULL
    elif vr > 1.1:
        vol_lbl = f"{vr:.1f}× Avg — Above"
        vol_col = BULL
    elif vr < 0.7:
        vol_lbl = f"{vr:.1f}× Avg — Weak"
        vol_col = BEAR
    else:
        vol_lbl = f"{vr:.1f}× Avg — Normal"
        vol_col = NEUT

    # Build pattern cards grid
    def _pat_card(p):
        pc  = BULL if p["bias"] == "BULL" else (BEAR if p["bias"] == "BEAR" else NEUT)
        pct_to_target = (p["target"] / cp - 1) * 100
        pct_to_stop   = (p["stop"]   / cp - 1) * 100
        rr_raw = abs(pct_to_target) / abs(pct_to_stop) if pct_to_stop != 0 else 0
        rr_col = BULL if rr_raw >= 2.0 else (NEUT if rr_raw >= 1.5 else BEAR)
        conf   = p["confidence"]
        # confidence arc: 0–100 mapped to stroke-dasharray on a circle r=14
        circ   = 2 * 3.14159 * 14  # ~87.96
        dash   = round(circ * conf / 100, 1)
        gap    = round(circ - dash, 1)
        return (
            f"<div style='background:#141414;border:1px solid #232323;"
            f"border-top:3px solid {pc};border-radius:10px;"
            f"padding:1rem 1rem 0.85rem;display:flex;flex-direction:column;gap:0.6rem;'>"

            # Row 1: name + bias pill + confidence ring
            f"<div style='display:flex;align-items:flex-start;justify-content:space-between;gap:0.5rem;'>"
            f"<div>"
            f"<div style='font-size:0.82rem;font-weight:900;color:#ebebeb;"
            f"line-height:1.2;margin-bottom:0.3rem;'>{p['name']}</div>"
            f"<span style='font-size:0.68rem;font-weight:800;text-transform:uppercase;"
            f"letter-spacing:0.8px;color:{pc};"
            f"background:{'rgba(76,175,80,0.1)' if p['bias']=='BULL' else ('rgba(244,67,54,0.1)' if p['bias']=='BEAR' else 'rgba(255,152,0,0.1)')};"
            f"border:1px solid {'rgba(76,175,80,0.25)' if p['bias']=='BULL' else ('rgba(244,67,54,0.25)' if p['bias']=='BEAR' else 'rgba(255,152,0,0.25)')};"
            f"border-radius:4px;padding:0.1rem 0.45rem;'>{p['bias']}</span>"
            f"</div>"
            # SVG confidence ring
            f"<div style='flex-shrink:0;text-align:center;'>"
            f"<svg width='36' height='36' viewBox='0 0 36 36'>"
            f"<circle cx='18' cy='18' r='14' fill='none' stroke='#2a2a2a' stroke-width='3'/>"
            f"<circle cx='18' cy='18' r='14' fill='none' stroke='{pc}' stroke-width='3'"
            f" stroke-dasharray='{dash} {gap}' stroke-linecap='round'"
            f" transform='rotate(-90 18 18)'/>"
            f"<text x='18' y='22' text-anchor='middle' font-size='9' font-weight='800'"
            f" fill='{pc}' font-family='Inter'>{conf}</text>"
            f"</svg>"
            f"<div style='font-size:0.65rem;color:#888;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.6px;margin-top:-0.1rem;'>CONF</div>"
            f"</div>"
            f"</div>"

            # Row 2: description
            f"<div style='font-size:0.78rem;color:#aaa;line-height:1.5;"
            f"border-top:1px solid #1e1e1e;padding-top:0.55rem;'>{p['description']}</div>"

            # Row 3: target + stop chips
            f"<div style='display:flex;gap:0.5rem;'>"
            f"<div style='flex:1;background:#181818;border:1px solid #232323;"
            f"border-radius:6px;padding:0.45rem 0.6rem;'>"
            f"<div style='font-size:0.68rem;color:#888;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.6px;margin-bottom:0.15rem;'>Target</div>"
            f"<div style='font-size:0.88rem;font-weight:900;color:#ebebeb;"
            f"letter-spacing:-0.3px;'>{p['target']:.2f}</div>"
            f"<div style='font-size:0.6rem;font-weight:700;color:{BULL if pct_to_target>0 else BEAR};'>"
            f"{pct_to_target:+.1f}%</div>"
            f"</div>"
            f"<div style='flex:1;background:#181818;border:1px solid #232323;"
            f"border-radius:6px;padding:0.45rem 0.6rem;'>"
            f"<div style='font-size:0.68rem;color:#888;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.6px;margin-bottom:0.15rem;'>Stop</div>"
            f"<div style='font-size:0.88rem;font-weight:900;color:#ebebeb;"
            f"letter-spacing:-0.3px;'>{p['stop']:.2f}</div>"
            f"<div style='font-size:0.6rem;font-weight:700;color:{BEAR};'>"
            f"{pct_to_stop:+.1f}%</div>"
            f"</div>"
            f"<div style='flex:1;background:#181818;border:1px solid #232323;"
            f"border-radius:6px;padding:0.45rem 0.6rem;'>"
            f"<div style='font-size:0.68rem;color:#888;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.6px;margin-bottom:0.15rem;'>R:R</div>"
            f"<div style='font-size:0.88rem;font-weight:900;color:{rr_col};"
            f"letter-spacing:-0.3px;'>1:{rr_raw:.1f}</div>"
            f"<div style='font-size:0.6rem;font-weight:700;color:{rr_col};'>"
            f"{'Good' if rr_raw>=2 else ('Ok' if rr_raw>=1.5 else 'Low')}</div>"
            f"</div>"
            f"</div>"

            f"</div>"
        )

    if patterns:
        # Responsive grid: up to 3 per row
        _pats_html = (
            f"<div style='display:grid;grid-template-columns:repeat(3,1fr);"
            f"gap:0.75rem;'>"
            + "".join(_pat_card(p) for p in patterns[:6])
            + f"</div>"
        )
    else:
        _pats_html = (
            f"<div style='padding:1.2rem 0;text-align:center;'>"
            f"<div style='font-size:1.1rem;color:#333;font-weight:700;'>—</div>"
            f"<div style='font-size:0.78rem;color:#999;margin-top:0.3rem;'>"
            f"No classical patterns detected in this window</div>"
            f"</div>"
        )

    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;border-top:3px solid {INFO};"
        f"border-radius:14px;overflow:hidden;margin-bottom:1.2rem;'>"

        # ── Row 1: MA Stack ──────────────────────────────────────────────────
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #222;'>"
        + _ma_badge("EMA 20", ind["ma20"])
        + _ma_badge("EMA 50", ind["ma50"])
        + _ma_badge("EMA 200", ind["ma200"])
        # Bollinger cell (no border-right on last)
        + (
            f"<div style='padding:0.75rem 1rem;display:flex;flex-direction:column;gap:0.22rem;'>"
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Bollinger</div>"
            + _ctatip("Bollinger Bands — a volatility envelope around price. "
                      "Near Upper Band = price is stretched up, potential reversal zone. "
                      "Near Lower Band = price is stretched down, potential bounce zone. "
                      "Width % = how wide the bands are — wide = high volatility, narrow = low volatility (often precedes a breakout).")
            + f"</div>"
            f"<div style='font-size:0.95rem;font-weight:800;color:{bb_col};'>{bb_lbl}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;'>{bb_w_lbl}</div>"
            f"</div>"
        )
        + f"</div>"

        # ── Row 2: ATR + Volume + S/R ────────────────────────────────────────
        + f"<div style='display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #222;'>"
        + (
            f"<div style='padding:0.75rem 1rem;border-right:1px solid #222;"
            f"display:flex;flex-direction:column;gap:0.22rem;'>"
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>ATR 14</div>"
            + _ctatip("Average True Range (14-period). Measures daily price swing size — the typical distance from high to low. "
                      "High ATR = volatile stock, wider stops needed. "
                      "Low ATR = calm stock, tighter stops possible. "
                      "ATR as % of price helps compare stocks at different price levels.")
            + f"</div>"
            f"<div style='font-size:0.95rem;font-weight:800;color:{atr_col};'>{atr_lbl}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;'>{ind['atr']:.2f} · {atr_pct:.1f}% of price</div>"
            f"</div>"

            f"<div style='padding:0.75rem 1rem;border-right:1px solid #222;"
            f"display:flex;flex-direction:column;gap:0.22rem;'>"
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Volume</div>"
            + _ctatip("Today's volume vs. the 20-day average. "
                      "High (1.5×+) = strong conviction behind the move. "
                      "Low (below 0.7×) = thin, unreliable move. "
                      "Always look for volume confirmation on breakouts — breakouts without volume often fail.")
            + f"</div>"
            f"<div style='font-size:0.95rem;font-weight:800;color:{vol_col};'>{vol_lbl}</div>"
            f"</div>"

            f"<div style='padding:0.75rem 1rem;border-right:1px solid #222;"
            f"display:flex;flex-direction:column;gap:0.22rem;'>"
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Nearest Support</div>"
            + _ctatip("The closest price level below where buyers have historically stepped in. "
                      "Calculated from recent swing lows and pivot points. "
                      "A strong support nearby = better stop-loss anchor. "
                      "Price bouncing at support + bullish indicators = high-probability setup.")
            + f"</div>"
            f"<div style='font-size:0.95rem;font-weight:800;color:{BULL};'>"
            f"{ind['nearest_sup']:.2f}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;'>"
            f"{(ind['nearest_sup']/cp - 1)*100:+.1f}% from price</div>"
            f"</div>"

            f"<div style='padding:0.75rem 1rem;"
            f"display:flex;flex-direction:column;gap:0.22rem;'>"
            f"<div style='display:flex;align-items:center;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>Nearest Resistance</div>"
            + _ctatip("The closest price level above where sellers have historically shown up. "
                      "This is a natural target area and also where breakout confirmation happens. "
                      "A clean break above resistance with volume = bullish breakout entry. "
                      "If price is far from resistance, there's more room to run.")
            + f"</div>"
            f"<div style='font-size:0.95rem;font-weight:800;color:{BEAR};'>"
            f"{ind['nearest_res']:.2f}</div>"
            f"<div style='font-size:0.75rem;color:#aaa;'>"
            f"{(ind['nearest_res']/cp - 1)*100:+.1f}% from price</div>"
            f"</div>"
        )
        + f"</div>"

        # ── Row 3: Pattern cards ─────────────────────────────────────────────
        + f"<div style='padding:1rem 1.2rem 1.2rem;'>"
        + f"<div style='display:flex;align-items:center;margin-bottom:0.75rem;'>"
        + f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
        + f"letter-spacing:0.8px;font-weight:700;'>Detected Patterns</div>"
        + _ctatip("Chart patterns are recurring price formations that traders use to predict future moves. "
                  "Each pattern has a typical target (based on the pattern's height) and a stop below the pattern's key level. "
                  "Confidence % = how closely this pattern matches ideal conditions. "
                  "R:R = Risk/Reward ratio — target gain vs. stop loss distance. Aim for 2.0 or better.")
        + f"</div>"
        + _pats_html
        + f"</div>"

        + f"</div>",
        unsafe_allow_html=True,
    )
