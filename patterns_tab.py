"""
Patterns Tab — Advanced pattern detection with pivot-based analysis,
volume confirmation, measured-move targets, and full trade plan per pattern.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots

# ── Design tokens ────────────────────────────────────────────────────────────
BULL  = "#4caf50"
BEAR  = "#f44336"
NEUT  = "#ff9800"
INFO  = "#2196f3"
PURP  = "#9c27b0"
BG    = "#181818"
BG2   = "#212121"
BG3   = "#212121"
BDR   = "#303030"
_STATE_COLORS = {
    "Developing": INFO,
    "Triggered": "#4A9EFF",
    "Retest": NEUT,
    "Confirmed": BULL,
    "Failed": BEAR,
    "Watch": NEUT,
}


def _sec(title, color=None):
    c = color or INFO
    return (f"<div style='display:flex;align-items:center;gap:0.6rem;"
            f"margin:2.2rem 0 1rem;padding:0;'>"
            f"<div style='width:3px;height:18px;border-radius:2px;background:{c};"
            f"box-shadow:0 0 8px {c}44;'></div>"
            f"<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
            f"text-transform:uppercase;letter-spacing:0.8px;'>{title}</span></div>")


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY: PIVOT DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _pivots(series, window=5):
    """Return (highs_idx, lows_idx) — indices of local maxima / minima."""
    arr   = np.asarray(series, dtype=float)
    n     = len(arr)
    highs, lows = [], []
    for i in range(window, n - window):
        seg = arr[i - window: i + window + 1]
        if arr[i] >= seg.max():
            highs.append(i)
        if arr[i] <= seg.min():
            lows.append(i)
    return highs, lows


def _linreg_slope(arr):
    """Slope of a linear regression through arr."""
    if len(arr) < 2:
        return 0.0
    x  = np.arange(len(arr), dtype=float)
    xm = x.mean(); ym = np.mean(arr)
    denom = np.sum((x - xm) ** 2)
    return float(np.sum((x - xm) * (arr - ym)) / denom) if denom > 0 else 0.0


def _vol_confirm(df, start_i, end_i):
    """True if avg volume over [start_i:end_i] > 20-bar avg at breakdown bar."""
    if "Volume" not in df.columns or end_i >= len(df):
        return False
    baseline = float(df["Volume"].rolling(20).mean().iloc[end_i] or 1)
    seg_vol  = float(df["Volume"].iloc[start_i:end_i].mean() or 0)
    return seg_vol > baseline * 1.1


# ══════════════════════════════════════════════════════════════════════════════
#  CANDLESTICK PATTERN DETECTION  (last 40 bars only, no redundant dupes)
# ══════════════════════════════════════════════════════════════════════════════

def _detect_candlestick(df):
    patterns = []
    tail     = df.reset_index(drop=True)
    n        = len(tail)
    if n < 5:
        return patterns

    for i in range(4, n):
        O, H, L, C = tail.iloc[i][["Open","High","Low","Close"]]
        body   = abs(C - O)
        rng    = H - L or 0.001
        upper  = H - max(O, C)
        lower  = min(O, C) - L
        is_bull = C >= O
        dt     = tail.iloc[i]["Date"]

        # ── Doji (body < 5% of range)
        if body / rng < 0.05:
            kind = "Gravestone Doji" if upper > rng * 0.6 else \
                   "Dragonfly Doji"  if lower > rng * 0.6 else "Doji"
            bias = "Bearish" if kind == "Gravestone Doji" else \
                   "Bullish" if kind == "Dragonfly Doji"  else "Neutral"
            patterns.append(_make(dt, kind, "Candlestick", bias, 55, C,
                "Indecision candle — balance of power shifting. "
                "Gravestone doji at top signals weakness; dragonfly at bottom signals strength."))

        # ── Marubozu (no wicks > 5% of body on either side)
        elif upper < body * 0.05 and lower < body * 0.05:
            if is_bull:
                patterns.append(_make(dt, "Bullish Marubozu", "Candlestick", "Bullish", 80, C,
                    "Full-body bull candle — strong buying pressure from open to close, no retreat."))
            else:
                patterns.append(_make(dt, "Bearish Marubozu", "Candlestick", "Bearish", 80, C,
                    "Full-body bear candle — strong selling pressure from open to close, no recovery."))

        # ── Hammer / Hanging Man (lower wick >= 2x body, small upper wick)
        elif lower >= body * 2.0 and upper <= body * 0.5:
            prev5_trend = tail["Close"].iloc[max(0,i-5):i]
            downtrend   = len(prev5_trend) >= 3 and float(prev5_trend.iloc[-1]) < float(prev5_trend.iloc[0])
            if downtrend:
                patterns.append(_make(dt, "Hammer", "Candlestick", "Bullish", 72, C,
                    "Rejected lower prices with long lower wick after downtrend — buyers stepping in."))
            else:
                patterns.append(_make(dt, "Hanging Man", "Candlestick", "Bearish", 65, C,
                    "Long lower wick after uptrend — sellers tested lower prices, warning sign."))

        # ── Shooting Star / Inverted Hammer (upper wick >= 2x body, small lower wick)
        elif upper >= body * 2.0 and lower <= body * 0.5:
            prev5_trend = tail["Close"].iloc[max(0,i-5):i]
            uptrend     = len(prev5_trend) >= 3 and float(prev5_trend.iloc[-1]) > float(prev5_trend.iloc[0])
            if uptrend:
                patterns.append(_make(dt, "Shooting Star", "Candlestick", "Bearish", 72, C,
                    "Rejected higher prices with long upper wick after uptrend — sellers overwhelmed buyers."))
            else:
                patterns.append(_make(dt, "Inverted Hammer", "Candlestick", "Bullish", 58, C,
                    "Long upper wick after downtrend — buyers attempted breakout, needs confirmation next bar."))

        # ── Multi-candle patterns (require i >= 1)
        if i >= 1:
            pO, pH, pL, pC = tail.iloc[i-1][["Open","High","Low","Close"]]
            pbody  = abs(pC - pO)

            # Bullish / Bearish Engulfing
            if pC < pO and is_bull and C > pO and O < pC and body > pbody * 1.05:
                patterns.append(_make(dt, "Bullish Engulfing", "Candlestick", "Bullish", 85, C,
                    "Bull candle fully wraps prior bear candle — momentum shift confirmed."))
            elif pC > pO and not is_bull and C < pO and O > pC and body > pbody * 1.05:
                patterns.append(_make(dt, "Bearish Engulfing", "Candlestick", "Bearish", 85, C,
                    "Bear candle fully engulfs prior bull candle — sellers seized full control."))

            # Harami (small candle inside prior body)
            if pbody > 0 and body < pbody * 0.5 and O > min(pO,pC) and C < max(pO,pC):
                bias = "Bullish" if pC < pO else "Bearish"
                patterns.append(_make(dt, bias + " Harami", "Candlestick", bias, 60, C,
                    "Small inside bar within prior candle body — momentum pausing, watch for breakout direction."))

            # Piercing Line / Dark Cloud Cover
            if pC < pO and is_bull and O < pL and C > (pO + pC) / 2:
                patterns.append(_make(dt, "Piercing Line", "Candlestick", "Bullish", 70, C,
                    "Bull candle opens below prior low and closes above midpoint — strong buying reversal."))
            elif pC > pO and not is_bull and O > pH and C < (pO + pC) / 2:
                patterns.append(_make(dt, "Dark Cloud Cover", "Candlestick", "Bearish", 70, C,
                    "Bear candle opens above prior high and closes below midpoint — strong selling reversal."))

        if i >= 2:
            p2O, p2H, p2L, p2C = tail.iloc[i-2][["Open","High","Low","Close"]]
            p1O, p1H, p1L, p1C = tail.iloc[i-1][["Open","High","Low","Close"]]
            p2body = abs(p2C - p2O)
            p1body = abs(p1C - p1O)

            # Morning Star / Evening Star
            if p2C < p2O and p1body < p2body * 0.3 and is_bull and C > (p2O + p2C) / 2:
                patterns.append(_make(dt, "Morning Star", "Candlestick", "Bullish", 90, C,
                    "3-candle bullish reversal: large red, small body gap, large green closes above midpoint."))
            elif p2C > p2O and p1body < p2body * 0.3 and not is_bull and C < (p2O + p2C) / 2:
                patterns.append(_make(dt, "Evening Star", "Candlestick", "Bearish", 90, C,
                    "3-candle bearish reversal: large green, small body gap, large red closes below midpoint."))

        if i >= 3:
            rows = [tail.iloc[i-j][["Open","Close"]].tolist() for j in range(3,0,-1)]
            # Three White Soldiers
            if all(r[1] > r[0] for r in rows) and rows[2][1] > rows[1][1] > rows[0][1]:
                if rows[1][0] > rows[0][0] and rows[2][0] > rows[1][0]:
                    patterns.append(_make(dt, "Three White Soldiers", "Candlestick", "Bullish", 82, C,
                        "Three consecutive rising bull candles each opening in prior body — sustained buying."))
            # Three Black Crows
            if all(r[1] < r[0] for r in rows) and rows[2][1] < rows[1][1] < rows[0][1]:
                if rows[1][0] < rows[0][0] and rows[2][0] < rows[1][0]:
                    patterns.append(_make(dt, "Three Black Crows", "Candlestick", "Bearish", 82, C,
                        "Three consecutive falling bear candles — sustained selling pressure."))

    return patterns


# ══════════════════════════════════════════════════════════════════════════════
#  CHART PATTERN DETECTION  (pivot-based)
# ══════════════════════════════════════════════════════════════════════════════

def _detect_chart(df):
    patterns = []
    if len(df) < 60:
        return patterns

    closes = df["Close"].values.astype(float)
    highs  = df["High"].values.astype(float)
    lows   = df["Low"].values.astype(float)
    dates  = df["Date"].values
    n      = len(df)
    cp     = closes[-1]

    ph_idx, pl_idx = _pivots(highs, window=8)
    _,      _      = _pivots(closes, window=5)  # unused but kept for clarity

    # Restrict to recent 120 bars to reduce stale signals
    lookback = 120
    start    = max(0, n - lookback)
    ph_idx   = [i for i in ph_idx if i >= start]
    pl_idx   = [i for i in pl_idx if i >= start]

    # ── Head & Shoulders (3 peaks: middle higher than both sides by >4%)
    if len(ph_idx) >= 3:
        for k in range(len(ph_idx) - 2):
            ls_i, hd_i, rs_i = ph_idx[k], ph_idx[k+1], ph_idx[k+2]
            ls, hd, rs = highs[ls_i], highs[hd_i], highs[rs_i]
            if (hd > ls * 1.04 and hd > rs * 1.04
                    and abs(ls - rs) / ls < 0.06
                    and (hd_i - ls_i) >= 10 and (rs_i - hd_i) >= 10):
                trfs = [i for i in pl_idx if ls_i < i < rs_i]
                if len(trfs) >= 2:
                    neck = (lows[trfs[0]] + lows[trfs[-1]]) / 2
                    measured = hd - neck
                    target   = round(neck - measured, 2)
                    stop     = round(hd * 1.005, 2)
                    vol_ok   = _vol_confirm(df, rs_i - 5, rs_i)
                    strength = 90 + (5 if vol_ok else 0)
                    desc = ("Neckline " + str(round(neck,2)) + ". "
                            "Measured-move target " + str(target) + ". "
                            "Stop above head " + str(stop) + ". "
                            + ("Volume confirmation." if vol_ok else "Awaiting volume confirmation."))
                    patterns.append(_make(dates[rs_i], "Head & Shoulders", "Chart", "Bearish",
                        min(strength, 95), closes[rs_i], desc,
                        entry=round(neck * 0.998, 2), stop_l=stop, target_p=target,
                        neckline=round(neck, 2)))

    # ── Inverse Head & Shoulders (3 troughs: middle lower than both sides by >4%)
    if len(pl_idx) >= 3:
        for k in range(len(pl_idx) - 2):
            ls_i, hd_i, rs_i = pl_idx[k], pl_idx[k+1], pl_idx[k+2]
            ls, hd, rs = lows[ls_i], lows[hd_i], lows[rs_i]
            if (hd < ls * 0.96 and hd < rs * 0.96
                    and abs(ls - rs) / ls < 0.06
                    and (hd_i - ls_i) >= 10 and (rs_i - hd_i) >= 10):
                trfs = [i for i in ph_idx if ls_i < i < rs_i]
                if len(trfs) >= 2:
                    neck = (highs[trfs[0]] + highs[trfs[-1]]) / 2
                    measured = neck - hd
                    target   = round(neck + measured, 2)
                    stop     = round(hd * 0.995, 2)
                    vol_ok   = _vol_confirm(df, rs_i - 5, rs_i)
                    strength = 90 + (5 if vol_ok else 0)
                    desc = ("Neckline " + str(round(neck,2)) + ". "
                            "Measured-move target " + str(target) + ". "
                            "Stop below head " + str(stop) + ". "
                            + ("Volume confirmation." if vol_ok else "Awaiting volume confirmation."))
                    patterns.append(_make(dates[rs_i], "Inverse H&S", "Chart", "Bullish",
                        min(strength, 95), closes[rs_i], desc,
                        entry=round(neck * 1.002, 2), stop_l=stop, target_p=target,
                        neckline=round(neck, 2)))

    # ── Double Top (2 peaks within 2.5%, 10+ bars apart)
    if len(ph_idx) >= 2:
        for k in range(len(ph_idx) - 1):
            p1_i, p2_i = ph_idx[k], ph_idx[k+1]
            p1, p2 = highs[p1_i], highs[p2_i]
            if abs(p1 - p2) / p1 < 0.025 and (p2_i - p1_i) >= 10:
                trfs = [i for i in pl_idx if p1_i < i < p2_i]
                if trfs:
                    neck    = lows[trfs[0]]
                    meas    = ((p1 + p2) / 2) - neck
                    target  = round(neck - meas, 2)
                    stop    = round(max(p1, p2) * 1.005, 2)
                    avg_top = round((p1 + p2) / 2, 2)
                    desc    = ("Two peaks near " + str(avg_top) + ". "
                               "Neckline " + str(round(neck,2)) + ". "
                               "Measured target " + str(target) + ".")
                    patterns.append(_make(dates[p2_i], "Double Top", "Chart", "Bearish", 85,
                        closes[p2_i], desc,
                        entry=round(neck * 0.997, 2), stop_l=stop, target_p=target,
                        neckline=round(neck, 2)))

    # ── Double Bottom (2 troughs within 2.5%)
    if len(pl_idx) >= 2:
        for k in range(len(pl_idx) - 1):
            p1_i, p2_i = pl_idx[k], pl_idx[k+1]
            p1, p2 = lows[p1_i], lows[p2_i]
            if abs(p1 - p2) / p1 < 0.025 and (p2_i - p1_i) >= 10:
                trfs = [i for i in ph_idx if p1_i < i < p2_i]
                if trfs:
                    neck   = highs[trfs[0]]
                    meas   = neck - ((p1 + p2) / 2)
                    target = round(neck + meas, 2)
                    stop   = round(min(p1, p2) * 0.995, 2)
                    avg_btm = round((p1 + p2) / 2, 2)
                    desc   = ("Two troughs near " + str(avg_btm) + ". "
                              "Neckline " + str(round(neck,2)) + ". "
                              "Measured target " + str(target) + ".")
                    patterns.append(_make(dates[p2_i], "Double Bottom", "Chart", "Bullish", 85,
                        closes[p2_i], desc,
                        entry=round(neck * 1.003, 2), stop_l=stop, target_p=target,
                        neckline=round(neck, 2)))

    # ── Ascending / Descending / Symmetrical Triangle (30 and 50 bar windows)
    for win in [30, 50]:
        if n < win + 5:
            continue
        seg_h   = highs[n - win: n]
        seg_l   = lows[n  - win: n]
        slope_h = _linreg_slope(seg_h)
        slope_l = _linreg_slope(seg_l)
        flat_tol = cp * 0.0006

        # Ascending triangle: flat top + rising bottom
        if abs(slope_h) < flat_tol and slope_l > flat_tol:
            res_level = float(np.mean(seg_h[-5:]))
            stop_l    = round(float(np.min(seg_l[-10:])), 2)
            height    = res_level - float(np.min(seg_l))
            tgt       = round(res_level + height, 2)
            desc      = ("Flat resistance near " + str(round(res_level,2)) +
                         ", rising support — coiling for upside breakout. "
                         "Target " + str(tgt) + ". Stop " + str(stop_l) + ".")
            patterns.append(_make(dates[-1], "Ascending Triangle", "Chart", "Bullish", 78,
                cp, desc, entry=round(res_level * 1.003, 2), stop_l=stop_l, target_p=tgt))
            break

        # Descending triangle: flat bottom + falling top
        if abs(slope_l) < flat_tol and slope_h < -flat_tol:
            sup_level = float(np.mean(seg_l[-5:]))
            stop_l2   = round(float(np.max(seg_h[-10:])), 2)
            height2   = float(np.max(seg_h)) - sup_level
            tgt2      = round(sup_level - height2, 2)
            desc2     = ("Flat support near " + str(round(sup_level,2)) +
                         ", falling resistance — coiling for downside break. "
                         "Target " + str(tgt2) + ". Stop " + str(stop_l2) + ".")
            patterns.append(_make(dates[-1], "Descending Triangle", "Chart", "Bearish", 78,
                cp, desc2, entry=round(sup_level * 0.997, 2), stop_l=stop_l2, target_p=tgt2))
            break

        # Symmetrical triangle
        if slope_h < -flat_tol and slope_l > flat_tol:
            mid   = (seg_h[-1] + seg_l[-1]) / 2
            width = seg_h[-1] - seg_l[-1]
            tgt_b = round(mid + width, 2)
            tgt_s = round(mid - width, 2)
            desc3 = ("Both highs and lows converging — coiling for breakout. "
                     "Bull target " + str(tgt_b) + " / Bear target " + str(tgt_s) + ". "
                     "Trade direction confirmed by breakout candle with volume.")
            patterns.append(_make(dates[-1], "Symmetrical Triangle", "Chart", "Neutral", 68,
                cp, desc3,
                entry=round(cp, 2), stop_l=round(seg_l[-1] * 0.995, 2), target_p=tgt_b))
            break

    # ── Bull Flag (strong pole >6% gain, then tight channel against pole)
    if n >= 30:
        pole_start = n - 30
        pole_end   = n - 12
        flag_start = n - 12
        if closes[pole_start] > 0:
            pole_gain = (closes[pole_end] - closes[pole_start]) / closes[pole_start]
        else:
            pole_gain = 0.0

        if pole_gain > 0.06:
            flag_sl = _linreg_slope(closes[flag_start:n])
            flag_hl = _linreg_slope(highs[flag_start:n])
            flag_ll = _linreg_slope(lows[flag_start:n])
            if -0.025 < flag_sl < 0.005 and flag_hl < 0 and flag_ll < 0:
                pole_height = closes[pole_end] - closes[pole_start]
                target      = round(closes[-1] + pole_height, 2)
                stop_f      = round(float(np.min(lows[flag_start:n])) * 0.997, 2)
                vol_ok      = _vol_confirm(df, flag_start, n - 1)
                strength    = 82 + (5 if vol_ok else 0)
                desc = ("Pole gain " + str(round(pole_gain*100,1)) + "%. "
                        "Consolidation channel holding. "
                        "Measured target " + str(target) + ". Stop " + str(stop_f) + ". "
                        + ("Volume confirmed." if vol_ok else "Watch for volume on breakout."))
                patterns.append(_make(dates[-1], "Bull Flag", "Chart", "Bullish",
                    min(strength, 87), cp, desc,
                    entry=round(float(np.max(highs[flag_start:n])) * 1.002, 2),
                    stop_l=stop_f, target_p=target))

    # ── Bear Flag
    if n >= 30:
        pole_start = n - 30
        pole_end   = n - 12
        flag_start = n - 12
        if closes[pole_start] > 0:
            pole_drop = (closes[pole_start] - closes[pole_end]) / closes[pole_start]
        else:
            pole_drop = 0.0

        if pole_drop > 0.06:
            flag_sl = _linreg_slope(closes[flag_start:n])
            flag_hl = _linreg_slope(highs[flag_start:n])
            flag_ll = _linreg_slope(lows[flag_start:n])
            if -0.005 < flag_sl < 0.025 and flag_hl > 0 and flag_ll > 0:
                pole_height = closes[pole_start] - closes[pole_end]
                target      = round(closes[-1] - pole_height, 2)
                stop_f      = round(float(np.max(highs[flag_start:n])) * 1.003, 2)
                vol_ok      = _vol_confirm(df, flag_start, n - 1)
                strength    = 82 + (5 if vol_ok else 0)
                desc = ("Pole drop " + str(round(pole_drop*100,1)) + "%. "
                        "Consolidation channel rising. "
                        "Measured target " + str(target) + ". Stop " + str(stop_f) + ". "
                        + ("Volume confirmed." if vol_ok else "Watch for volume on breakdown."))
                patterns.append(_make(dates[-1], "Bear Flag", "Chart", "Bearish",
                    min(strength, 87), cp, desc,
                    entry=round(float(np.min(lows[flag_start:n])) * 0.998, 2),
                    stop_l=stop_f, target_p=target))

    # ── Rising Wedge (both slopes up, converging)
    for win in [40, 60]:
        if n < win + 5:
            continue
        seg_h  = highs[n - win: n]
        seg_l  = lows[n  - win: n]
        sh     = _linreg_slope(seg_h)
        sl     = _linreg_slope(seg_l)
        spread = float(seg_h[-1] - seg_l[-1])
        init_s = float(seg_h[0]  - seg_l[0])

        if sh > 0 and sl > 0 and sl > sh and init_s > 0 and spread < init_s * 0.7:
            top_line = float(seg_h[-1])
            bot_line = float(seg_l[-1])
            target   = round(bot_line - (top_line - bot_line) * 1.5, 2)
            stop_w   = round(top_line * 1.005, 2)
            desc = ("Both highs and lows rising but converging — classic bearish reversal wedge. "
                    "Breakdown target " + str(target) + ". Stop " + str(stop_w) + ".")
            patterns.append(_make(dates[-1], "Rising Wedge", "Chart", "Bearish", 80,
                cp, desc, entry=round(bot_line * 0.998, 2), stop_l=stop_w, target_p=target))
            break

    # ── Falling Wedge (both slopes down, converging)
    for win in [40, 60]:
        if n < win + 5:
            continue
        seg_h  = highs[n - win: n]
        seg_l  = lows[n  - win: n]
        sh     = _linreg_slope(seg_h)
        sl     = _linreg_slope(seg_l)
        spread = float(seg_h[-1] - seg_l[-1])
        init_s = float(seg_h[0]  - seg_l[0])

        if sh < 0 and sl < 0 and sh < sl and init_s > 0 and spread < init_s * 0.7:
            top_line = float(seg_h[-1])
            bot_line = float(seg_l[-1])
            target   = round(top_line + (top_line - bot_line) * 1.5, 2)
            stop_w   = round(bot_line * 0.995, 2)
            desc = ("Both highs and lows falling but converging — classic bullish reversal wedge. "
                    "Breakout target " + str(target) + ". Stop " + str(stop_w) + ".")
            patterns.append(_make(dates[-1], "Falling Wedge", "Chart", "Bullish", 80,
                cp, desc, entry=round(top_line * 1.003, 2), stop_l=stop_w, target_p=target))
            break

    # ── Cup & Handle (U-shape base + shallow handle)
    if n >= 80:
        cup    = closes[n - 80: n - 10]
        cup_left  = float(np.max(cup[:10]))
        cup_right = float(np.max(cup[-10:]))
        cup_low   = float(np.min(cup))
        handle    = closes[n - 10: n]
        handle_low = float(np.min(handle))
        cup_depth  = ((cup_left + cup_right) / 2) - cup_low

        if (abs(cup_left - cup_right) / cup_left < 0.06
                and cup_depth / cup_left > 0.08
                and handle_low > cup_low
                and handle_low > (cup_left + cup_low) / 2):
            target = round(cup_right + cup_depth, 2)
            stop_c = round(handle_low * 0.995, 2)
            desc = ("U-shaped recovery with shallow handle pullback. "
                    "Cup depth " + str(round(cup_depth,2)) + ". "
                    "Breakout target " + str(target) + ". Stop " + str(stop_c) + ".")
            patterns.append(_make(dates[-1], "Cup & Handle", "Chart", "Bullish", 85,
                cp, desc, entry=round(cup_right * 1.002, 2), stop_l=stop_c, target_p=target))

    return patterns


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER — BUILD PATTERN DICT
# ══════════════════════════════════════════════════════════════════════════════

def _make(date, name, category, bias, strength, price, desc,
          entry=None, stop_l=None, target_p=None, neckline=None):
    sig = "BUY" if bias == "Bullish" else "SELL" if bias == "Bearish" else "WATCH"
    return dict(
        date=date, pattern=name, category=category, type=bias,
        strength=min(int(strength), 95), price=float(price), signal=sig,
        description=desc,
        entry=entry, stop=stop_l, target=target_p, neckline=neckline,
    )


def _atr14(df):
    h = df["High"].astype(float)
    l = df["Low"].astype(float)
    c = df["Close"].astype(float)
    tr = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14, min_periods=1).mean().iloc[-1])
    if not np.isfinite(atr) or atr <= 0:
        atr = float((h - l).mean())
    return max(atr, 0.01)


def _rsi14(df):
    close = df["Close"].astype(float)
    delta = close.diff()
    avg_gain = delta.clip(lower=0).rolling(14, min_periods=1).mean().iloc[-1]
    avg_loss = (-delta).clip(lower=0).rolling(14, min_periods=1).mean().iloc[-1]
    return float(100 - 100 / (1 + avg_gain / (avg_loss + 1e-9)))


def _dedupe_patterns(patterns):
    deduped = []
    seen = {}
    for pattern in patterns:
        key = pattern["pattern"]
        dt = pd.to_datetime(pattern["date"])
        if key in seen and abs((dt - seen[key]).days) < 2:
            continue
        seen[key] = dt
        deduped.append(pattern)
    return deduped


def _normalize_market_df(df):
    work_df = df.copy()
    if isinstance(work_df.columns, pd.MultiIndex):
        preferred = {"Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"}
        normalized_cols = []
        for col in work_df.columns.to_flat_index():
            parts = [str(part) for part in col if part not in ("", None)]
            chosen = next((part for part in parts if part in preferred), parts[0] if parts else "")
            normalized_cols.append(chosen)
        work_df.columns = normalized_cols
    return work_df


def _pattern_row(df, pattern_dt):
    normalized = pd.to_datetime(df["Date"]).dt.normalize()
    target = pd.to_datetime(pattern_dt).normalize()
    mask = normalized == target
    if mask.any():
        return df.loc[mask].iloc[-1], int(np.flatnonzero(mask.to_numpy())[-1])
    return df.iloc[-1], len(df) - 1


def _derive_pattern_levels(pattern, df, atr):
    row, _ = _pattern_row(df, pattern["date"])
    bar_high = float(row["High"])
    bar_low = float(row["Low"])
    pattern_price = float(pattern.get("price") or row["Close"])

    if pattern["type"] == "Bullish":
        entry = float(pattern.get("entry") or max(pattern_price, bar_high * 1.001))
        stop = float(pattern.get("stop") or min(bar_low, pattern_price - atr * 1.1))
        target = float(pattern.get("target") or (entry + max(entry - stop, atr) * 2.0))
        trigger = float(pattern.get("neckline") or entry)
    elif pattern["type"] == "Bearish":
        entry = float(pattern.get("entry") or min(pattern_price, bar_low * 0.999))
        stop = float(pattern.get("stop") or max(bar_high, pattern_price + atr * 1.1))
        target = float(pattern.get("target") or (entry - max(stop - entry, atr) * 2.0))
        trigger = float(pattern.get("neckline") or entry)
    else:
        entry = float(pattern.get("entry") or pattern_price)
        stop = float(pattern.get("stop") or (pattern_price - atr))
        target = float(pattern.get("target") or (pattern_price + atr))
        trigger = entry

    return {
        "entry_ref": round(entry, 2),
        "stop_ref": round(stop, 2),
        "target_ref": round(target, 2),
        "trigger_ref": round(trigger, 2),
        "bar_high": bar_high,
        "bar_low": bar_low,
    }


def _enrich_pattern(pattern, df, current_price, atr, vol_ratio):
    enriched = pattern.copy()
    levels = _derive_pattern_levels(pattern, df, atr)
    enriched.update(levels)

    _, pattern_pos = _pattern_row(df, pattern["date"])
    age_bars = max(0, len(df) - 1 - pattern_pos)
    recent = df.tail(3)
    last_close = float(df["Close"].iloc[-1])
    recent_low = float(recent["Low"].min())
    recent_high = float(recent["High"].max())
    trigger = max(levels["trigger_ref"], 0.01)
    stop = max(levels["stop_ref"], 0.01)
    target = levels["target_ref"]

    if pattern["type"] == "Bullish":
        failed = last_close <= stop * 1.002 or (recent_high >= trigger * 1.002 and last_close < trigger * 0.998)
        retest = last_close >= trigger * 0.998 and recent_low <= trigger * 1.004 and age_bars <= 8
        confirmed = last_close >= trigger * 1.008 and vol_ratio >= 1.05 and age_bars <= 12
        triggered = last_close >= trigger * 0.998 or abs(last_close - trigger) / trigger <= 0.012
        if failed:
            state = "Failed"
            note = "Breakout lost the trigger level or slipped through the invalidation zone."
        elif retest and current_price > trigger:
            state = "Retest"
            note = "Breakout is holding above the trigger after a retest, which is usually the cleanest continuation state."
        elif confirmed:
            state = "Confirmed"
            note = "Price is trading above the trigger with supporting volume, so the pattern is fully confirmed."
        elif triggered:
            state = "Triggered"
            note = "Price has reached the trigger, but the move still needs follow-through to become confirmed."
        else:
            state = "Developing"
            note = "Structure is present, but price has not broken the trigger cleanly yet."
        target_gap_pct = (target - current_price) / max(current_price, 0.01) * 100 if target else None
        rr = (target - current_price) / max(current_price - stop, 0.01) if target else None
    elif pattern["type"] == "Bearish":
        failed = last_close >= stop * 0.998 or (recent_low <= trigger * 0.998 and last_close > trigger * 1.002)
        retest = last_close <= trigger * 1.002 and recent_high >= trigger * 0.996 and age_bars <= 8
        confirmed = last_close <= trigger * 0.992 and vol_ratio >= 1.05 and age_bars <= 12
        triggered = last_close <= trigger * 1.002 or abs(last_close - trigger) / trigger <= 0.012
        if failed:
            state = "Failed"
            note = "Breakdown lost momentum and price reclaimed the invalidation zone."
        elif retest and current_price < trigger:
            state = "Retest"
            note = "Breakdown is holding below the trigger after a retest, which keeps bearish pressure intact."
        elif confirmed:
            state = "Confirmed"
            note = "Price is trading below the trigger with supporting volume, so the pattern is fully confirmed."
        elif triggered:
            state = "Triggered"
            note = "Price has reached the trigger, but the move still needs continuation to become confirmed."
        else:
            state = "Developing"
            note = "Structure is present, but price has not broken the trigger decisively yet."
        target_gap_pct = (current_price - target) / max(current_price, 0.01) * 100 if target else None
        rr = (current_price - target) / max(stop - current_price, 0.01) if target else None
    else:
        state = "Watch"
        note = "Neutral pattern. Wait for price to resolve direction before acting on it."
        target_gap_pct = None
        rr = None

    state_score = {
        "Failed": -3,
        "Developing": 0,
        "Triggered": 1,
        "Retest": 2,
        "Confirmed": 3,
        "Watch": 0,
    }.get(state, 0)

    enriched.update({
        "state": state,
        "state_color": _STATE_COLORS.get(state, INFO),
        "state_note": note,
        "state_score": state_score,
        "age_bars": age_bars,
        "vol_ratio": round(vol_ratio, 2),
        "target_gap_pct": round(target_gap_pct, 2) if target_gap_pct is not None and np.isfinite(target_gap_pct) else None,
        "rr": round(rr, 2) if rr is not None and np.isfinite(rr) else None,
    })
    return enriched


def _evaluate_guardrails(df, active_patterns, current_price, atr, rsi, vol_ratio):
    flags = []
    long_penalty = 0
    last_row = df.iloc[-1]
    day_range = max(float(last_row["High"] - last_row["Low"]), 0.01)
    upper_wick = float(last_row["High"] - max(last_row["Close"], last_row["Open"]))

    if len(df) > 21:
        prior_high = float(df["High"].iloc[-21:-1].max())
    else:
        prior_high = float(df["High"].iloc[:-1].max()) if len(df) > 1 else float(last_row["High"])
    weak_breakout = current_price > prior_high * 1.002 and vol_ratio < 0.95
    if weak_breakout:
        long_penalty += 2
        flags.append({
            "title": "Weak breakout volume",
            "detail": "Price stretched above the recent swing high, but volume did not confirm the move.",
            "color": NEUT,
        })

    if rsi >= 74:
        long_penalty += 2
        flags.append({
            "title": "RSI exhaustion",
            "detail": f"RSI is already {rsi:.0f}, so the move is entering late-stage extension territory.",
            "color": BEAR,
        })

    if atr > 0 and day_range / atr >= 1.8 and upper_wick / day_range >= 0.35:
        long_penalty += 2
        flags.append({
            "title": "Blow-off candle",
            "detail": "Latest candle expanded too far versus ATR and faded from the highs, which often marks exhaustion.",
            "color": BEAR,
        })

    failed_bullish = [p for p in active_patterns if p["type"] == "Bullish" and p.get("state") == "Failed"]
    if failed_bullish:
        long_penalty += 3
        names = ", ".join(p["pattern"] for p in failed_bullish[:2])
        flags.append({
            "title": "Failed bullish trigger",
            "detail": names + " already failed its breakout hold, so the long setup should be filtered unless price reclaims the trigger.",
            "color": BEAR,
        })

    tight_headroom = [
        p for p in active_patterns
        if p["type"] == "Bullish"
        and p.get("state") in {"Triggered", "Retest", "Confirmed"}
        and p.get("target_gap_pct") is not None
        and p["target_gap_pct"] < 2.5
    ]
    if tight_headroom:
        long_penalty += 1
        flags.append({
            "title": "Measured target is close",
            "detail": "At least one active bullish pattern is already near its measured target, so the reward window is narrowing.",
            "color": NEUT,
        })

    return {
        "flags": flags[:4],
        "long_penalty": long_penalty,
        "long_blocked": long_penalty >= 4,
        "status": "Filtered" if long_penalty >= 4 else "Caution" if long_penalty > 0 else "Clear",
        "status_color": BEAR if long_penalty >= 4 else NEUT if long_penalty > 0 else BULL,
    }


def get_pattern_context(df):
    if df is None or len(df) < 30:
        return None
    required = ["Open", "High", "Low", "Close", "Date"]
    if any(col not in df.columns for col in required):
        return None

    work_df = _normalize_market_df(df)
    work_df["Date"] = pd.to_datetime(work_df["Date"])
    current_price = float(work_df["Close"].iloc[-1])
    atr = _atr14(work_df)
    rsi = _rsi14(work_df)
    if "Volume" in work_df.columns and len(work_df) >= 20:
        base_vol = float(work_df["Volume"].tail(20).mean() or 0)
        last_vol = float(work_df["Volume"].iloc[-1] or 0)
        vol_ratio = (last_vol / base_vol) if base_vol > 0 else 1.0
    else:
        vol_ratio = 1.0

    all_patterns = _dedupe_patterns(sorted(
        _detect_candlestick(work_df) + _detect_chart(work_df),
        key=lambda item: (pd.to_datetime(item["date"]), item["strength"]),
        reverse=True,
    ))
    recent_dates = set(work_df["Date"].tail(10).dt.normalize().tolist())
    enriched = [_enrich_pattern(pattern, work_df, current_price, atr, vol_ratio) for pattern in all_patterns]
    active = [pattern for pattern in enriched if pd.to_datetime(pattern["date"]).normalize() in recent_dates]
    historical = [pattern for pattern in enriched if pd.to_datetime(pattern["date"]).normalize() not in recent_dates]

    bull_cnt = sum(1 for pattern in active if pattern["type"] == "Bullish")
    bear_cnt = sum(1 for pattern in active if pattern["type"] == "Bearish")
    neut_cnt = len(active) - bull_cnt - bear_cnt
    state_counts = {
        key: sum(1 for pattern in active if pattern.get("state") == key)
        for key in ["Developing", "Triggered", "Retest", "Confirmed", "Failed"]
    }

    long_bonus = 0
    short_bonus = 0
    long_reasons = []
    short_reasons = []
    ranked_active = sorted(
        active,
        key=lambda item: (item.get("state_score", 0), item["strength"], 1 if item["category"] == "Chart" else 0),
        reverse=True,
    )
    for pattern in ranked_active:
        if pattern["type"] not in {"Bullish", "Bearish"}:
            continue
        base = 2 if pattern["category"] == "Chart" else 1
        strength_bonus = 1 if pattern["strength"] >= 80 else 0
        state_bonus = max(pattern.get("state_score", 0), 0)
        points = min(base + strength_bonus + state_bonus, 4)
        reason = f"{pattern['pattern']} is {pattern.get('state', 'developing').lower()} ({pattern['strength']}% strength)"
        if pattern["type"] == "Bullish" and pattern.get("state") != "Failed":
            long_bonus += points
            if len(long_reasons) < 3:
                long_reasons.append(reason)
        if pattern["type"] == "Bearish" and pattern.get("state") != "Failed":
            short_bonus += points
            if len(short_reasons) < 3:
                short_reasons.append(reason)

    long_bonus = min(long_bonus, 6)
    short_bonus = min(short_bonus, 6)
    guardrails = _evaluate_guardrails(work_df, active, current_price, atr, rsi, vol_ratio)

    net_bias = bull_cnt - bear_cnt
    strongest = ranked_active[0] if ranked_active else None
    bias_score = long_bonus - short_bonus - guardrails["long_penalty"]
    if bias_score > 0 and bull_cnt > 0 and not guardrails["long_blocked"]:
        signal_lbl = "BUY"
        bias_col = BULL
    elif net_bias < 0 or short_bonus > long_bonus + 1:
        signal_lbl = "SELL"
        bias_col = BEAR
    else:
        signal_lbl = "WAIT"
        bias_col = NEUT

    if not active:
        reason = "No active patterns detected in the last 10 trading sessions."
    else:
        top = strongest
        reason = (
            f"{bull_cnt} bullish, {bear_cnt} bearish, {neut_cnt} neutral in the last 10 bars. "
            f"Lead pattern: {top['pattern']} is {top.get('state', 'developing').lower()} at {top['strength']}% strength."
        )
        if guardrails["long_penalty"]:
            reason += " Breakout filter is active, so long setups need extra confirmation."

    confluence_score = int(max(0, min(100, 50 + (long_bonus - short_bonus) * 8 - guardrails["long_penalty"] * 6)))

    return {
        "df": work_df,
        "current_price": current_price,
        "all_patterns": enriched,
        "active": active,
        "historical": historical,
        "bull_cnt": bull_cnt,
        "bear_cnt": bear_cnt,
        "neut_cnt": neut_cnt,
        "state_counts": state_counts,
        "net_bias": net_bias,
        "strongest": strongest,
        "signal": signal_lbl,
        "signal_color": bias_col,
        "reason": reason,
        "atr": atr,
        "rsi": rsi,
        "vol_ratio": vol_ratio,
        "long_bonus": long_bonus,
        "short_bonus": short_bonus,
        "long_reasons": long_reasons,
        "short_reasons": short_reasons,
        "guardrails": guardrails,
        "confluence_score": confluence_score,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  CHART BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_pattern_chart(df, patterns, current_price):
    tail_n = 90
    sub    = df.tail(tail_n).reset_index(drop=False)
    xh     = list(pd.to_datetime(sub["Date"]))

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.02)

    # Candlesticks or line
    if all(c in df.columns for c in ["Open", "High", "Low"]):
        fig.add_trace(go.Candlestick(
            x=xh,
            open=sub["Open"].values, high=sub["High"].values,
            low=sub["Low"].values,   close=sub["Close"].values,
            name="OHLC",
            increasing_line_color=BULL, decreasing_line_color=BEAR,
            increasing_fillcolor="rgba(0,200,150,0.35)",
            decreasing_fillcolor="rgba(255,77,109,0.35)",
            line_width=0.8,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=xh, y=list(sub["Close"].values),
            mode="lines", name="Price",
            line=dict(color=INFO, width=1.8),
        ), row=1, col=1)

    # EMAs
    for col, ec, lbl in [("EMA_20", "#4A9EFF", "EMA20"), ("EMA_50", "#A78BFA", "EMA50")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=xh, y=list(df[col].values[-tail_n:]),
                mode="lines", name=lbl,
                line=dict(color=ec, width=1.0, dash="dot"),
            ), row=1, col=1)

    # Pattern markers
    xh_set = set(xh)
    date_to_close = {}
    for _, row_data in sub.iterrows():
        date_to_close[pd.to_datetime(row_data["Date"]).date()] = row_data["Close"]

    bull_mx, bull_my, bull_mt = [], [], []
    bear_mx, bear_my, bear_mt = [], [], []
    neut_mx, neut_my, neut_mt = [], [], []

    for p in patterns:
        try:
            pd_dt = pd.to_datetime(p["date"])
            if pd_dt < xh[0]:
                continue
            py   = date_to_close.get(pd_dt.date(), p["price"])
            tip  = p["pattern"] + " (" + str(p["strength"]) + "%) · " + p["signal"]
            if p["type"] == "Bullish":
                bull_mx.append(pd_dt); bull_my.append(float(py) * 0.992); bull_mt.append(tip)
            elif p["type"] == "Bearish":
                bear_mx.append(pd_dt); bear_my.append(float(py) * 1.008); bear_mt.append(tip)
            else:
                neut_mx.append(pd_dt); neut_my.append(float(py)); neut_mt.append(tip)

            # Target / stop / neckline hlines for chart patterns only
            if p["category"] == "Chart":
                if p.get("target"):
                    fig.add_hline(y=p["target"], line_dash="dot", line_color=BULL,
                                  line_width=0.8, opacity=0.5,
                                  annotation_text="T " + str(p["target"]),
                                  annotation_font_color=BULL, annotation_font_size=8,
                                  row=1, col=1)
                if p.get("stop"):
                    fig.add_hline(y=p["stop"], line_dash="dot", line_color=BEAR,
                                  line_width=0.8, opacity=0.5,
                                  annotation_text="SL " + str(p["stop"]),
                                  annotation_font_color=BEAR, annotation_font_size=8,
                                  row=1, col=1)
                if p.get("neckline"):
                    fig.add_hline(y=p["neckline"], line_dash="dash", line_color=NEUT,
                                  line_width=1.0, opacity=0.6,
                                  annotation_text="NL " + str(p["neckline"]),
                                  annotation_font_color=NEUT, annotation_font_size=8,
                                  row=1, col=1)
        except Exception:
            continue

    if bull_mx:
        fig.add_trace(go.Scatter(x=bull_mx, y=bull_my, mode="markers", name="Bullish Signal",
            marker=dict(symbol="triangle-up", size=12, color=BULL,
                        line=dict(color="#003d2b", width=1)),
            text=bull_mt, hovertemplate="%{text}<extra></extra>",
        ), row=1, col=1)
    if bear_mx:
        fig.add_trace(go.Scatter(x=bear_mx, y=bear_my, mode="markers", name="Bearish Signal",
            marker=dict(symbol="triangle-down", size=12, color=BEAR,
                        line=dict(color="#5a0000", width=1)),
            text=bear_mt, hovertemplate="%{text}<extra></extra>",
        ), row=1, col=1)
    if neut_mx:
        fig.add_trace(go.Scatter(x=neut_mx, y=neut_my, mode="markers", name="Neutral Signal",
            marker=dict(symbol="diamond", size=9, color=NEUT,
                        line=dict(color="#5a4000", width=1)),
            text=neut_mt, hovertemplate="%{text}<extra></extra>",
        ), row=1, col=1)

    # Volume panel
    if "Volume" in df.columns:
        clv  = sub["Close"].values
        vcl  = [BULL if i == 0 or float(clv[i]) >= float(clv[i-1]) else BEAR
                for i in range(len(clv))]
        fig.add_trace(go.Bar(x=xh, y=list(sub["Volume"].values),
            name="Volume", marker_color=vcl, marker_opacity=0.55, showlegend=False,
        ), row=2, col=1)
        if len(df) >= 20:
            vma = df["Volume"].rolling(20).mean().values[-tail_n:]
            fig.add_trace(go.Scatter(x=xh, y=list(vma), mode="lines", name="Vol MA20",
                line=dict(color=NEUT, width=1.0, dash="dot"),
            ), row=2, col=1)

    fig.update_layout(
        height=520, margin=dict(l=4, r=4, t=14, b=4),
        paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
        font=dict(color="#666", size=10),
        hovermode="x unified",
        legend=dict(bgcolor="#1b1b1b", bordercolor="#272727", borderwidth=1, font=dict(size=9),
                    orientation="h", x=0.01, y=1.01, yanchor="bottom"),
        xaxis_rangeslider_visible=False,
    )
    for row_i in range(1, 3):
        fig.update_xaxes(gridcolor="#272727", showgrid=True, zeroline=False, row=row_i, col=1)
        fig.update_yaxes(gridcolor="#272727", showgrid=True, zeroline=False, row=row_i, col=1)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  PATTERN CARD COMPONENT
# ══════════════════════════════════════════════════════════════════════════════

def _pattern_card(p, current_price):
    bias_col  = BULL if p["type"] == "Bullish" else BEAR if p["type"] == "Bearish" else NEUT
    sig_col   = BULL if p["signal"] == "BUY"   else BEAR if p["signal"] == "SELL"  else NEUT
    state     = p.get("state", "Watch")
    state_col = p.get("state_color", _STATE_COLORS.get(state, INFO))
    bar_w     = p["strength"]
    entry     = p.get("entry_ref")
    stop      = p.get("stop_ref")
    target    = p.get("target_ref")
    rr        = p.get("rr")
    rr_txt    = f"{rr:.1f}x" if rr is not None else "—"
    bc        = ','.join(str(int(bias_col[i:i+2], 16)) for i in (1, 3, 5))
    sc        = ','.join(str(int(state_col[i:i+2], 16)) for i in (1, 3, 5))

    e_str = f"${entry:.2f}" if entry is not None else "—"
    s_str = f"${stop:.2f}"  if stop  is not None else "—"
    t_str = f"${target:.2f}" if target is not None else "—"
    html = (
        f"<div style='background:#1b1b1b;border:1px solid #282828;border-radius:12px;"
        f"overflow:hidden;margin-bottom:0.55rem;'>"
        f"<div style='padding:0.75rem 1.2rem;"
        f"background:linear-gradient(135deg,rgba({bc},0.06),transparent);"
        f"display:flex;align-items:center;justify-content:space-between;'>"
        f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
        f"<div style='font-size:0.9rem;font-weight:800;color:{bias_col};'>{p['pattern']}</div>"
        f"<div style='font-size:0.6rem;font-weight:700;color:{sig_col};"
        f"background:rgba({','.join(str(int(sig_col[i:i+2],16)) for i in (1,3,5))},0.12);"
        f"border-radius:4px;padding:0.1rem 0.5rem;'>{p['signal']}</div>"
        f"<div style='font-size:0.6rem;font-weight:700;color:{state_col};"
        f"background:rgba({sc},0.12);border-radius:4px;padding:0.1rem 0.5rem;'>{state}</div>"
        f"</div>"
        f"<div style='display:flex;align-items:center;gap:0.5rem;'>"
        f"<div style='width:60px;background:#1a1a1a;border-radius:3px;height:3px;'>"
        f"<div style='background:{bias_col};width:{bar_w}%;height:3px;border-radius:3px;'></div></div>"
        f"<div style='font-size:0.75rem;font-weight:700;color:{bias_col};'>{bar_w}%</div>"
        f"</div></div>"
        f"<div style='padding:0.6rem 1.2rem;display:flex;gap:0.6rem;align-items:center;"
        f"border-top:1px solid #232323;'>"
        f"<div style='flex:1;text-align:center;'>"
        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.15rem;'>Entry</div>"
        f"<div style='font-size:0.82rem;font-weight:700;color:#e0e0e0;'>{e_str}</div></div>"
        f"<div style='width:1px;background:#232323;height:28px;'></div>"
        f"<div style='flex:1;text-align:center;'>"
        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.15rem;'>Stop</div>"
        f"<div style='font-size:0.82rem;font-weight:700;color:{BEAR};'>{s_str}</div></div>"
        f"<div style='width:1px;background:#232323;height:28px;'></div>"
        f"<div style='flex:1;text-align:center;'>"
        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.15rem;'>Target</div>"
        f"<div style='font-size:0.82rem;font-weight:700;color:{BULL};'>{t_str}</div></div>"
        f"<div style='width:1px;background:#232323;height:28px;'></div>"
        f"<div style='flex:1;text-align:center;'>"
        f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:0.15rem;'>R:R</div>"
        f"<div style='font-size:0.82rem;font-weight:700;color:{state_col};'>{rr_txt}</div></div>"
        f"</div></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TAB FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def patterns_tab(df, pattern_context=None):
    global BG, BG2, BG3, BDR
    theme_palette = st.session_state.get('theme_palette', {})
    BG = theme_palette.get('panel', BG)
    BG2 = theme_palette.get('panel_alt', BG2)
    BG3 = theme_palette.get('panel_alt', BG3)
    BDR = theme_palette.get('border', BDR)

    pattern_context = pattern_context or get_pattern_context(df)
    if pattern_context is None:
        st.warning("Not enough data for pattern analysis.")
        return

    df = pattern_context["df"]
    current_price = pattern_context["current_price"]
    active = pattern_context["active"]
    hist = pattern_context["historical"]
    bull_cnt = pattern_context["bull_cnt"]
    bear_cnt = pattern_context["bear_cnt"]
    neut_cnt = pattern_context["neut_cnt"]
    signal_lbl = pattern_context["signal"]
    bias_col = pattern_context["signal_color"]
    strongest = pattern_context["strongest"]
    reason = pattern_context["reason"]
    guardrails = pattern_context["guardrails"]
    state_counts = pattern_context["state_counts"]

    # ── Hero banner ──────────────────────────────────────────────────────────
    hero_html = (
        "<div style='background:#1b1b1b;border:1px solid #272727;"
        "border-radius:14px;overflow:hidden;margin-bottom:1.4rem;"
        "box-shadow:0 4px 24px rgba(0,0,0,0.3);'>"
        "<div style='padding:1.6rem 2rem;"
        "background:linear-gradient(135deg,rgba(" + ','.join(str(int(bias_col[i:i+2],16)) for i in (1,3,5)) + ",0.08),transparent);'>"
        "<div style='font-size:0.62rem;color:#606060;text-transform:uppercase;"
        "letter-spacing:1.2px;margin-bottom:0.5rem;font-weight:700;'>Pattern Signal</div>"
        "<div style='font-size:2.4rem;font-weight:900;color:" + bias_col + ";line-height:1;"
        "letter-spacing:-1px;text-shadow:0 0 20px " + bias_col + "33;'>" + signal_lbl + "</div>"
        "<div style='font-size:0.82rem;color:#888;margin-top:0.6rem;line-height:1.7;"
        "max-width:600px;'>" + reason + "</div>"
        "</div></div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    summary_cards = [
        ("Bullish Active", str(bull_cnt), BULL, f"{pattern_context['long_bonus']} pts confluence"),
        ("Bearish Active", str(bear_cnt), BEAR, f"{pattern_context['short_bonus']} pts pressure"),
        ("Confirmed / Retest", str(state_counts["Confirmed"] + state_counts["Retest"]), INFO,
         f"{state_counts['Triggered']} triggered · {state_counts['Developing']} developing"),
        ("Breakout Filter", guardrails["status"], guardrails["status_color"],
         f"Penalty {guardrails['long_penalty']} · RSI {pattern_context['rsi']:.0f}"),
    ]
    sum_cols = st.columns(len(summary_cards), gap="small")
    for col, (label, value, color, detail) in zip(sum_cols, summary_cards):
        with col:
            st.markdown(
                "<div style='background:#1b1b1b;border:1px solid #272727;border-radius:12px;"
                "padding:0.9rem 1rem;box-shadow:0 1px 8px rgba(0,0,0,0.14);'>"
                "<div style='font-size:0.62rem;color:#606060;text-transform:uppercase;letter-spacing:0.7px;font-weight:700;'>" + label + "</div>"
                "<div style='font-size:1.45rem;font-weight:900;color:" + color + ";margin-top:0.35rem;'>" + value + "</div>"
                "<div style='font-size:0.72rem;color:#666;margin-top:0.3rem;line-height:1.5;'>" + detail + "</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    if guardrails["flags"]:
        st.markdown(_sec("False-Breakout & Exhaustion Filter", guardrails["status_color"]), unsafe_allow_html=True)
        for flag in guardrails["flags"]:
            st.markdown(
                "<div style='background:#1b1b1b;border:1px solid #272727;border-left:4px solid " + flag["color"] + ";"
                "border-radius:12px;padding:0.85rem 1rem;margin-bottom:0.55rem;'>"
                "<div style='font-size:0.78rem;font-weight:800;color:" + flag["color"] + ";margin-bottom:0.25rem;'>" + flag["title"] + "</div>"
                "<div style='font-size:0.76rem;color:#9a9a9a;line-height:1.55;'>" + flag["detail"] + "</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    # ── Price Ladder (BUY only) ──────────────────────────────────────────────
    if signal_lbl == "BUY":
        try:
            from _levels import compute_structural_levels as _csl, render_price_ladder as _rpl
            _p_lv = _csl(df, current_price, True)
            _rpl(_p_lv["entry"], _p_lv["stop"], _p_lv["t1"], _p_lv["t2"], _p_lv["t3"], True,
                 _p_lv.get("entry_quality", ""), _p_lv.get("eq_col", ""))
        except Exception:
            pass

    # ── Chart ────────────────────────────────────────────────────────────────
    st.plotly_chart(
        _build_pattern_chart(df, pattern_context["all_patterns"], current_price),
        width="stretch",
        config={"displayModeBar": False},
    )

    # ── Active pattern cards ─────────────────────────────────────────────────
    if active:
        heading_html = _sec(f"Active Patterns ({len(active)})", bias_col)
        st.markdown(heading_html, unsafe_allow_html=True)
        for p in active:
            _pattern_card(p, current_price)
    else:
        st.markdown(
            "<div style='background:#1b1b1b;border:1px solid #272727;border-radius:12px;"
            "padding:1.4rem 1.5rem;color:#666;font-size:0.85rem;'>"
            "No patterns detected in the last 10 trading sessions."
            "</div>",
            unsafe_allow_html=True,
        )



@st.cache_data(ttl=900, show_spinner=False)
def _scan_market_pattern_setups(limit=12):
    try:
        from market_data import get_all_tadawul_tickers
    except Exception:
        return {"ready": [], "alerts": [], "scanned": 0}

    tickers_map = get_all_tadawul_tickers()
    tickers = list(tickers_map.keys())
    frames = []
    batch_size = 40
    for start in range(0, len(tickers), batch_size):
        chunk = tickers[start:start + batch_size]
        try:
            part = yf.download(
                chunk,
                period="6mo",
                interval="1d",
                progress=False,
                threads=True,
                group_by="ticker",
                timeout=30,
                auto_adjust=False,
            )
            if part is not None and not part.empty:
                frames.append(part)
        except Exception:
            continue

    if not frames:
        return {"ready": [], "alerts": [], "scanned": 0}

    data = pd.concat(frames, axis=1) if len(frames) > 1 else frames[0]
    is_multi = isinstance(data.columns, pd.MultiIndex)
    ready = []
    alerts = []
    scanned = 0

    for ticker in tickers:
        try:
            if is_multi:
                if ticker not in data.columns.get_level_values(0):
                    continue
                hist = data[ticker].copy()
            else:
                hist = data.copy()

            hist = hist.dropna(subset=["Close"])
            if len(hist) < 80:
                continue

            hist = hist.reset_index()
            if "Date" not in hist.columns:
                hist = hist.rename(columns={hist.columns[0]: "Date"})

            required = ["Date", "Open", "High", "Low", "Close"]
            if any(col not in hist.columns for col in required):
                continue

            context = get_pattern_context(hist)
            if not context or not context.get("active"):
                continue

            scanned += 1
            bullish = sorted(
                [
                    pattern for pattern in context["active"]
                    if pattern["type"] == "Bullish" and pattern.get("state") in {"Triggered", "Retest", "Confirmed"}
                ],
                key=lambda item: (item.get("state_score", 0), item["strength"], item.get("rr") or 0),
                reverse=True,
            )
            bearish = sorted(
                [
                    pattern for pattern in context["active"]
                    if pattern["type"] == "Bearish" and pattern.get("state") in {"Triggered", "Retest", "Confirmed"}
                ],
                key=lambda item: (item.get("state_score", 0), item["strength"]),
                reverse=True,
            )

            if bullish and not context["guardrails"].get("long_blocked"):
                lead = bullish[0]
                score = int(max(0, min(100,
                    lead["strength"] * 0.6
                    + context["long_bonus"] * 6
                    + max(lead.get("rr") or 0, 0) * 7
                    - context["guardrails"].get("long_penalty", 0) * 8
                )))
                ready.append({
                    "ticker": ticker.replace(".SR", ""),
                    "name": tickers_map.get(ticker, ticker),
                    "bias": "Bullish",
                    "bias_color": BULL,
                    "pattern": lead["pattern"],
                    "state": lead.get("state", "Triggered"),
                    "state_color": lead.get("state_color", BULL),
                    "strength": lead["strength"],
                    "price": context["current_price"],
                    "entry": lead.get("entry_ref"),
                    "stop": lead.get("stop_ref"),
                    "target": lead.get("target_ref"),
                    "rr": lead.get("rr"),
                    "score": score,
                    "detail": lead.get("state_note", ""),
                })
                continue

            alert_pattern = bearish[0] if bearish else None
            if alert_pattern is None:
                failed_bulls = [pattern for pattern in context["active"] if pattern["type"] == "Bullish" and pattern.get("state") == "Failed"]
                if failed_bulls:
                    alert_pattern = sorted(failed_bulls, key=lambda item: item["strength"], reverse=True)[0]
            if alert_pattern is None:
                continue

            bias = "Bearish" if alert_pattern["type"] == "Bearish" else "Bull Trap"
            score = int(max(0, min(100,
                alert_pattern["strength"] * 0.6
                + context["short_bonus"] * 6
                + context["guardrails"].get("long_penalty", 0) * 8
            )))
            alert_detail = alert_pattern.get("state_note", "")
            if context["guardrails"].get("flags"):
                alert_detail = context["guardrails"]["flags"][0]["detail"]
            alerts.append({
                "ticker": ticker.replace(".SR", ""),
                "name": tickers_map.get(ticker, ticker),
                "bias": bias,
                "bias_color": BEAR,
                "pattern": alert_pattern["pattern"],
                "state": alert_pattern.get("state", "Watch"),
                "state_color": alert_pattern.get("state_color", BEAR),
                "strength": alert_pattern["strength"],
                "price": context["current_price"],
                "entry": alert_pattern.get("entry_ref"),
                "stop": alert_pattern.get("stop_ref"),
                "target": alert_pattern.get("target_ref"),
                "rr": alert_pattern.get("rr"),
                "score": score,
                "detail": alert_detail,
            })
        except Exception:
            continue

    ready.sort(key=lambda item: (item["score"], item["strength"]), reverse=True)
    alerts.sort(key=lambda item: (item["score"], item["strength"]), reverse=True)
    return {
        "ready": ready[:limit],
        "alerts": alerts[:limit],
        "scanned": scanned,
    }


def _scanner_row(setup):
    accent     = setup["bias_color"]
    state_col  = setup.get("state_color", accent)
    rr_txt     = f"{setup['rr']:.1f}x" if setup.get("rr") is not None else "—"
    entry_txt  = f"${setup['entry']:.2f}"  if setup.get("entry")  is not None else "—"
    stop_txt   = f"${setup['stop']:.2f}"   if setup.get("stop")   is not None else "—"
    target_txt = f"${setup['target']:.2f}" if setup.get("target") is not None else "—"
    ac = ','.join(str(int(accent[i:i+2], 16)) for i in (1, 3, 5))
    sc = ','.join(str(int(state_col[i:i+2], 16)) for i in (1, 3, 5))
    return (
        f"<div style='background:#1b1b1b;border:1px solid #282828;border-radius:11px;"
        f"overflow:hidden;margin-bottom:0.5rem;'>"
        # top row: ticker · name | pattern | state | score
        f"<div style='padding:0.7rem 1rem;display:flex;align-items:center;gap:0.7rem;"
        f"background:linear-gradient(135deg,rgba({ac},0.07),transparent);border-bottom:1px solid #232323;'>"
        f"<div style='font-size:0.92rem;font-weight:900;color:{accent};min-width:60px;'>{setup['ticker']}</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:0.78rem;font-weight:700;color:#e0e0e0;'>{setup['pattern']}</div>"
        f"<div style='font-size:0.62rem;color:#666;margin-top:0.1rem;'>{setup['name']}</div>"
        f"</div>"
        f"<div style='font-size:0.6rem;font-weight:700;color:{state_col};"
        f"background:rgba({sc},0.12);border-radius:4px;padding:0.12rem 0.5rem;white-space:nowrap;'>{setup['state']}</div>"
        f"<div style='font-size:1.3rem;font-weight:900;color:{accent};min-width:36px;text-align:right;line-height:1;'>{setup['score']}</div>"
        f"</div>"
        # bottom row: price · entry · stop · target · R:R
        f"<div style='padding:0.5rem 1rem;display:flex;gap:1rem;align-items:center;'>"
        f"<div style='flex:1;'><div style='font-size:0.55rem;color:#555;text-transform:uppercase;letter-spacing:0.4px;'>Price</div>"
        f"<div style='font-size:0.78rem;font-weight:700;color:#e0e0e0;'>${setup['price']:.2f}</div></div>"
        f"<div style='width:1px;background:#232323;height:24px;'></div>"
        f"<div style='flex:1;'><div style='font-size:0.55rem;color:#555;text-transform:uppercase;letter-spacing:0.4px;'>Entry</div>"
        f"<div style='font-size:0.78rem;font-weight:700;color:#e0e0e0;'>{entry_txt}</div></div>"
        f"<div style='width:1px;background:#232323;height:24px;'></div>"
        f"<div style='flex:1;'><div style='font-size:0.55rem;color:#555;text-transform:uppercase;letter-spacing:0.4px;'>Stop</div>"
        f"<div style='font-size:0.78rem;font-weight:700;color:{BEAR};'>{stop_txt}</div></div>"
        f"<div style='width:1px;background:#232323;height:24px;'></div>"
        f"<div style='flex:1;'><div style='font-size:0.55rem;color:#555;text-transform:uppercase;letter-spacing:0.4px;'>Target</div>"
        f"<div style='font-size:0.78rem;font-weight:700;color:{BULL};'>{target_txt}</div></div>"
        f"<div style='width:1px;background:#232323;height:24px;'></div>"
        f"<div style='flex:1;'><div style='font-size:0.55rem;color:#555;text-transform:uppercase;letter-spacing:0.4px;'>R:R</div>"
        f"<div style='font-size:0.78rem;font-weight:700;color:{state_col};'>{rr_txt}</div></div>"
        f"</div></div>"
    )


def _render_market_pattern_scanner():
    with st.spinner("Scanning Tadawul patterns..."):
        scan = _scan_market_pattern_setups(limit=12)

    hcols = st.columns([4, 1], gap="small")
    with hcols[0]:
        st.markdown(
            f"<div style='padding:0.4rem 0;'>"
            f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;letter-spacing:0.6px;'>Market Scanner · {scan['scanned']} symbols scanned</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with hcols[1]:
        if st.button("Refresh", key="ppa_refresh_scanner"):
            _scan_market_pattern_setups.clear()
            st.rerun()

    # Stats row
    stat_cols = st.columns(3, gap="small")
    for col, (label, val, color) in zip(stat_cols, [
        ("Symbols Scanned", str(scan["scanned"]), INFO),
        ("Long Setups",     str(len(scan["ready"])), BULL),
        ("Trap Alerts",     str(len(scan["alerts"])), BEAR),
    ]):
        with col:
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #282828;border-radius:10px;"
                f"padding:0.7rem 1rem;text-align:center;'>"
                f"<div style='font-size:0.6rem;color:#555;text-transform:uppercase;letter-spacing:0.6px;font-weight:700;margin-bottom:0.25rem;'>{label}</div>"
                f"<div style='font-size:1.6rem;font-weight:900;color:{color};line-height:1;'>{val}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Long setups
    st.markdown(_sec("Long Setups", BULL), unsafe_allow_html=True)
    if scan["ready"]:
        for setup in scan["ready"]:
            st.markdown(_scanner_row(setup), unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#1b1b1b;border:1px solid #282828;border-radius:10px;"
            "padding:1rem 1.2rem;color:#555;font-size:0.82rem;text-align:center;'>"
            "No confirmed long setups right now.</div>",
            unsafe_allow_html=True,
        )

    # Trap alerts
    st.markdown(_sec("Trap Alerts", BEAR), unsafe_allow_html=True)
    if scan["alerts"]:
        for setup in scan["alerts"]:
            st.markdown(_scanner_row(setup), unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='background:#1b1b1b;border:1px solid #282828;border-radius:10px;"
            "padding:1rem 1.2rem;color:#555;font-size:0.82rem;text-align:center;'>"
            "No trap alerts detected.</div>",
            unsafe_allow_html=True,
        )


def render_patterns_price_action_workspace(df, info_icon):
    from price_action_tab import price_action_analysis_tab
    pattern_context = get_pattern_context(df)
    price_action_analysis_tab(df, info_icon)
    patterns_tab(df, pattern_context=pattern_context)


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC GETTER — called from Decision Tab
# ══════════════════════════════════════════════════════════════════════════════

def get_patterns_signal(df, cp):
    """Return a BUY signal dict for the Decision Tab, or None if no bullish signal."""
    if df is None or len(df) < 30:
        return None
    required = ["Open", "High", "Low", "Close", "Date"]
    if any(c not in df.columns for c in required):
        return None
    try:
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"])

        cs_patterns  = _detect_candlestick(df)
        ch_patterns  = _detect_chart(df)
        all_patterns = cs_patterns + ch_patterns
        all_patterns.sort(key=lambda x: (pd.to_datetime(x["date"]), x["strength"]), reverse=True)

        recent_dates = set(df["Date"].tail(10).dt.normalize().tolist())
        active = [p for p in all_patterns
                  if pd.to_datetime(p["date"]).normalize() in recent_dates]

        bull_cnt = sum(1 for p in active if p["type"] == "Bullish")
        bear_cnt = sum(1 for p in active if p["type"] == "Bearish")
        net_bias = bull_cnt - bear_cnt

        if net_bias <= 0 or bull_cnt == 0:
            return None

        bull_patterns = [p for p in active if p["type"] == "Bullish"]
        strongest     = max(bull_patterns, key=lambda p: p["strength"])
        top_names     = ", ".join(p["pattern"] for p in sorted(
            bull_patterns, key=lambda x: x["strength"], reverse=True
        )[:3])

        reasons = [
            f"{bull_cnt} bullish vs {bear_cnt} bearish patterns in last 10 sessions",
            f"Strongest: {strongest['pattern']} ({strongest['strength']}% strength)",
        ]
        if len(bull_patterns) >= 2:
            reasons.append(f"Active bullish patterns: {top_names}")

        # Compute trade levels using _levels
        try:
            from _levels import compute_structural_levels as _csl
            _lv = _csl(df, float(cp), True)
            _entry = _lv["entry"]; _stop = _lv["stop"]
            _t1 = _lv["t1"]; _t2 = _lv["t2"]; _t3 = _lv["t3"]
        except Exception:
            _atr   = max(float((df["High"] - df["Low"]).rolling(14, min_periods=1).mean().iloc[-1]),
                         float(cp) * 0.005)
            _entry = float(cp)
            _stop  = round(_entry - _atr * 2.0, 2)
            _risk  = max(_entry - _stop, 0.001)
            _t1    = round(_entry + _risk * 1.5, 2)
            _t2    = round(_entry + _risk * 2.5, 2)
            _t3    = round(_entry + _risk * 4.236, 2)

        conf = min(round(bull_cnt / max(bull_cnt + bear_cnt, 1) * 100), 94)
        conf = max(conf, strongest["strength"])

        return dict(
            color=BULL,
            verdict_text="▲ BUY",
            sublabel=f"Pattern Signal — {bull_cnt} bullish patterns active",
            conf=conf,
            reasons=reasons[:3],
            entry=_entry,
            stop=_stop,
            t1=_t1,
            t2=_t2,
            t3=_t3,
        )
    except Exception:
        return None

