"""
Patterns Tab — Advanced pattern detection with pivot-based analysis,
volume confirmation, measured-move targets, and full trade plan per pattern.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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


def _sec(title, color=None):
    c = color or INFO
    return (f"<div style='font-size:1rem;color:#ffffff;font-weight:700;"
            f"margin:2rem 0 1rem 0;border-bottom:2px solid {c}33;"
            f"padding-bottom:0.5rem;'>{title}</div>")


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
        paper_bgcolor=BG2, plot_bgcolor=BG,
        font=dict(color="#757575", size=10),
        hovermode="x unified",
        legend=dict(bgcolor=BG2, bordercolor=BDR, borderwidth=1, font=dict(size=9),
                    orientation="h", x=0.01, y=1.01, yanchor="bottom"),
        xaxis_rangeslider_visible=False,
    )
    for row_i in range(1, 3):
        fig.update_xaxes(gridcolor=BDR, showgrid=True, zeroline=False, row=row_i, col=1)
        fig.update_yaxes(gridcolor=BDR, showgrid=True, zeroline=False, row=row_i, col=1)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  PATTERN CARD COMPONENT
# ══════════════════════════════════════════════════════════════════════════════

def _pattern_card(p, current_price):
    bias_col = BULL if p["type"] == "Bullish" else BEAR if p["type"] == "Bearish" else NEUT
    sig_col  = BULL if p["signal"] == "BUY"  else BEAR if p["signal"] == "SELL"  else NEUT
    dt_str   = pd.to_datetime(p["date"]).strftime("%d %b %Y")
    bar_w    = p["strength"]

    html = (
        "<div style='background:" + BG3 + ";border:1px solid " + BDR + ";"
        "border-left:4px solid " + bias_col + ";border-radius:12px;"
        "padding:0.9rem 1.2rem;margin-bottom:0.6rem;"
        "display:flex;align-items:center;justify-content:space-between;gap:1rem;'>"
        # left: name + signal badge
        "<div style='display:flex;align-items:center;gap:0.65rem;min-width:0;'>"
        "<div style='font-size:0.96rem;font-weight:800;color:" + bias_col + ";'>"
        + p["pattern"] + "</div>"
        "<div style='font-size:0.67rem;font-weight:700;color:" + sig_col + ";"
        "background:" + sig_col + "22;border:1px solid " + sig_col + "66;"
        "border-radius:5px;padding:0.15rem 0.55rem;letter-spacing:0.6px;white-space:nowrap;'>"
        + p["signal"] + "</div>"
        "</div>"
        # right: strength bar + date
        "<div style='display:flex;align-items:center;gap:1.2rem;flex-shrink:0;'>"
        "<div style='display:flex;align-items:center;gap:0.5rem;'>"
        "<div style='width:70px;background:" + BDR + ";border-radius:4px;height:5px;'>"
        "<div style='background:" + bias_col + ";width:" + str(bar_w) + "%;"
        "height:5px;border-radius:4px;'></div></div>"
        "<div style='font-size:0.80rem;font-weight:700;color:" + bias_col + ";'>"
        + str(bar_w) + "%</div>"
        "</div>"
        "<div style='font-size:0.78rem;color:#9e9e9e;white-space:nowrap;'>" + dt_str + "</div>"
        "</div>"
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TAB FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def patterns_tab(df):
    global BG, BG2, BG3, BDR
    theme_palette = st.session_state.get('theme_palette', {})
    BG = theme_palette.get('panel', BG)
    BG2 = theme_palette.get('panel_alt', BG2)
    BG3 = theme_palette.get('panel_alt', BG3)
    BDR = theme_palette.get('border', BDR)

    if len(df) < 30:
        st.warning("Not enough data for pattern analysis.")
        return

    required = ["Open", "High", "Low", "Close", "Date"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        st.warning("Missing columns: " + ", ".join(missing))
        return

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    current_price = float(df["Close"].iloc[-1])
    latest_date   = df["Date"].max()

    # ── Run detection ────────────────────────────────────────────────────────
    cs_patterns   = _detect_candlestick(df)
    ch_patterns   = _detect_chart(df)
    all_patterns  = cs_patterns + ch_patterns

    # Sort by date desc, then strength desc
    all_patterns.sort(key=lambda x: (pd.to_datetime(x["date"]),
                                     x["strength"]), reverse=True)

    # Deduplicate: keep only the most recent instance of each pattern name
    # within a 2-bar calendar window to avoid same-day duplicates
    seen: dict = {}
    deduped = []
    for p in all_patterns:
        key = p["pattern"]
        dt  = pd.to_datetime(p["date"])
        if key in seen and abs((dt - seen[key]).days) < 2:
            continue
        seen[key] = dt
        deduped.append(p)
    all_patterns = deduped

    # Split: active = patterns on any of the last 10 actual trading bars
    # Using actual data dates avoids calendar-day gaps (weekends, holidays)
    recent_dates = set(df["Date"].tail(10).dt.normalize().tolist())
    active   = [p for p in all_patterns
                if pd.to_datetime(p["date"]).normalize() in recent_dates]
    hist     = [p for p in all_patterns
                if pd.to_datetime(p["date"]).normalize() not in recent_dates]

    bull_cnt = sum(1 for p in active if p["type"] == "Bullish")
    bear_cnt = sum(1 for p in active if p["type"] == "Bearish")
    neut_cnt = len(active) - bull_cnt - bear_cnt
    net_bias = bull_cnt - bear_cnt

    # Signal: BUY / SELL / WAIT
    if net_bias > 0:
        signal_lbl = "BUY"
        bias_col   = BULL
    elif net_bias < 0:
        signal_lbl = "SELL"
        bias_col   = BEAR
    else:
        signal_lbl = "WAIT"
        bias_col   = NEUT

    strongest = max(active, key=lambda p: p["strength"]) if active else None

    # Build reason sentence
    if not active:
        reason = "No active patterns detected in the last 10 trading sessions."
    else:
        top = max(active, key=lambda p: p["strength"])
        top_dt = pd.to_datetime(top["date"]).strftime("%b %d")
        top_sc = BULL if top["signal"] == "BUY" else BEAR if top["signal"] == "SELL" else NEUT
        top_sig_badge = (
            "<span style='color:" + top_sc + ";font-weight:700;'>"
            + top["signal"] + "</span>"
        )
        if net_bias > 0:
            reason = (
                str(bull_cnt) + " bullish vs " + str(bear_cnt) + " bearish pattern"
                + ("s" if bear_cnt != 1 else "") + " — "
                + "<strong style='color:#ffffff;'>" + top["pattern"] + "</strong>"
                + " (" + str(top["strength"]) + "% strength, " + top_sig_badge
                + " on " + top_dt + ") leads the signal."
            )
        elif net_bias < 0:
            reason = (
                str(bear_cnt) + " bearish vs " + str(bull_cnt) + " bullish pattern"
                + ("s" if bull_cnt != 1 else "") + " — "
                + "<strong style='color:#ffffff;'>" + top["pattern"] + "</strong>"
                + " (" + str(top["strength"]) + "% strength, " + top_sig_badge
                + " on " + top_dt + ") leads the signal."
            )
        else:
            reason = (
                "Equal bullish and bearish pressure (" + str(bull_cnt) + " each) — "
                + "<strong style='color:#ffffff;'>" + top["pattern"] + "</strong>"
                + " (" + str(top["strength"]) + "% strength) detected on " + top_dt
                + ". Wait for a clearer directional move."
            )

    # ── Hero banner ──────────────────────────────────────────────────────────
    hero_html = (
        "<div style='background:" + BG3 + ";border:1px solid " + BDR + ";"
        "border-left:5px solid " + bias_col + ";border-radius:14px;"
        "padding:1.5rem 1.8rem;margin-bottom:1.2rem;'>"
        "<div style='font-size:0.68rem;color:#9e9e9e;text-transform:uppercase;"
        "letter-spacing:1.1px;margin-bottom:0.4rem;font-weight:600;'>Pattern Signal</div>"
        "<div style='font-size:3rem;font-weight:900;color:" + bias_col + ";line-height:1;"
        "letter-spacing:-0.5px;'>" + signal_lbl + "</div>"
        "<div style='font-size:0.86rem;color:#9e9e9e;margin-top:0.6rem;line-height:1.6;"
        "max-width:600px;'>" + reason + "</div>"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

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
        _build_pattern_chart(df, all_patterns, current_price),
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
            "<div style='background:" + BG3 + ";border:1px solid " + BDR + ";border-radius:12px;"
            "padding:1.2rem 1.4rem;color:#9e9e9e;font-size:0.88rem;'>"
            "No patterns detected in the last 10 trading sessions."
            "</div>",
            unsafe_allow_html=True,
        )


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

