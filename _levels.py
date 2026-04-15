"""
Shared Price Ladder component — professional-grade stop + target levels.

Stop  : Confirmed structural pivot + 0.5 ATR buffer (never arbitrary %)
T1    : First structural resistance ≥ 1.5R  (Fib 1.618 fallback)
T2    : Core structural resistance ≥ 2.5R   (Fib 2.618 fallback)
T3    : Major structural level  ≥ 4.0R      (Fib 4.236 fallback)

Entry quality: OPTIMAL / GOOD / ELEVATED / CHASING
  — tells you BEFORE you click BUY whether this is a smart entry
"""
import streamlit as st
import numpy as np
import hashlib

# ── Design tokens ──────────────────────────────────────────────────────────
BULL = "#4caf50"
BEAR = "#f44336"
NEUT = "#ff9800"
INFO = "#2196f3"
BG   = "#181818"
BG2  = "#212121"
BDR  = "#303030"
GOLD = "#FFD700"


# ── Internal helpers ───────────────────────────────────────────────────────

def _atr14(high, low, close, n):
    """14-bar Average True Range."""
    tr = []
    for i in range(1, min(15, n)):
        tr.append(max(
            float(high.iloc[-i]) - float(low.iloc[-i]),
            abs(float(high.iloc[-i]) - float(close.iloc[-i - 1])),
            abs(float(low.iloc[-i])  - float(close.iloc[-i - 1])),
        ))
    return float(np.mean(tr)) if tr else float(close.iloc[-1]) * 0.02


def _find_pivots(hi_arr, lo_arr, n, lookback=100, wings=3):
    """
    Confirmed pivot highs and lows using N-bar wing confirmation.
    A pivot HIGH: bar[i] >= all `wings` bars on left AND right.
    A pivot LOW:  bar[i] <= all `wings` bars on left AND right.
    Returns (pivot_highs, pivot_lows) — each a list of (price, bar_age).
    """
    ph, pl = [], []
    limit = min(lookback, n - wings - 2)
    for offset in range(wings, limit):
        pos = n - 1 - offset
        if pos < wings or pos + wings >= n:
            continue
        h = hi_arr[pos]; l = lo_arr[pos]
        lh = hi_arr[pos - wings: pos];      rh = hi_arr[pos + 1: pos + wings + 1]
        ll = lo_arr[pos - wings: pos];      rl = lo_arr[pos + 1: pos + wings + 1]
        if h >= max(lh) and h >= max(rh):
            ph.append((round(h, 2), offset))
        if l <= min(ll) and l <= min(rl):
            pl.append((round(l, 2), offset))
    return ph, pl


def _fib_extensions(swing_lo, swing_hi, is_bullish):
    """
    Fibonacci extension levels of the last completed impulse move.
    For bulls: project upward from swing_hi.
    For bears: project downward from swing_lo.
    Ratios used: 0.618, 1.0, 1.618, 2.618, 4.236
    """
    move = abs(swing_hi - swing_lo)
    if is_bullish:
        base = swing_hi
        return {
            "f618": round(base + move * 0.618, 2),
            "f100": round(base + move * 1.000, 2),
            "f162": round(base + move * 1.618, 2),
            "f262": round(base + move * 2.618, 2),
            "f424": round(base + move * 4.236, 2),
        }
    else:
        base = swing_lo
        return {
            "f618": round(base - move * 0.618, 2),
            "f100": round(base - move * 1.000, 2),
            "f162": round(base - move * 1.618, 2),
            "f262": round(base - move * 2.618, 2),
            "f424": round(base - move * 4.236, 2),
        }


def compute_structural_levels(df, cp, is_bullish):
    """
    Professional-grade stop + target computation.
    Cached per (symbol-fingerprint, cp, is_bullish) — fast on repeat calls.
    Returns dict with:
      entry, stop, t1, t2, t3,
      risk_pct, rr1, rr2, R,
      entry_quality, eq_col
    """
    # Build a lightweight cache key from the last 10 close prices + cp + direction
    try:
        _tail = tuple(round(float(x), 4) for x in df["Close"].iloc[-10:])
        _key  = (_tail, round(cp, 4), is_bullish)
        if not hasattr(st.session_state, "_levels_cache"):
            st.session_state._levels_cache = {}
        if _key in st.session_state._levels_cache:
            return st.session_state._levels_cache[_key]
    except Exception:
        _key = None

    result = _compute_structural_levels_impl(df, cp, is_bullish)

    try:
        if _key is not None:
            st.session_state._levels_cache[_key] = result
    except Exception:
        pass
    return result


def _compute_structural_levels_impl(df, cp, is_bullish):
    close = df["Close"].astype(float)
    high  = df["High"].astype(float)
    low   = df["Low"].astype(float)
    n     = len(close)

    hi_arr = list(high)
    lo_arr = list(low)

    atr = _atr14(high, low, close, n)

    # ── Key indicators ───────────────────────────────────────────────────
    e20  = float(close.rolling(20).mean().iloc[-1])  if n >= 20  else cp
    e50  = float(close.rolling(50).mean().iloc[-1])  if n >= 50  else cp
    e200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else cp
    rm   = close.rolling(20).mean()
    rs   = close.rolling(20).std()
    bbu  = float((rm + 2 * rs).iloc[-1]) if n >= 20 else cp * 1.04
    bbl  = float((rm - 2 * rs).iloc[-1]) if n >= 20 else cp * 0.96
    lb   = min(252, n)
    w52h = float(high.iloc[-lb:].max())
    w52l = float(low.iloc[-lb:].min())

    # ── Demand candle bodies (for stop anchor) ────────────────────────────
    # Find the CLOSE of confirmed bullish demand candles near pivot lows.
    # Using candle body close instead of wick low avoids stop hunts on
    # Saudi stocks that gap or spike through wick lows regularly.
    open_  = df["Open"].astype(float) if "Open" in df.columns else close
    bodies_lo = []   # (body_low, bar_index)
    for i in range(max(0, n - 120), n):
        o = float(open_.iloc[i]); c_ = float(close.iloc[i])
        l = float(low.iloc[i])
        # Bullish demand candle: closes near its high, wick >= 30% of range
        rng = float(high.iloc[i]) - l
        lw  = min(o, c_) - l
        if rng > 0 and lw / rng >= 0.30 and c_ >= o:
            bodies_lo.append((min(o, c_), i))     # body low = open (bullish)

    # ── Pivot detection ───────────────────────────────────────────────────
    ph_list, pl_list = _find_pivots(hi_arr, lo_arr, n, lookback=120, wings=3)

    # ── STOP: body-anchored structural stop ───────────────────────────────
    # Priority: body low of nearest demand candle → pivot low → ATR fallback
    if is_bullish:
        # 1. Find demand candle bodies below current price
        bodies_below = [(b, i) for b, i in bodies_lo if b < cp * 0.998]
        if bodies_below:
            nearest_body = max(b for b, _ in bodies_below)
            raw_stop = nearest_body - max(atr * 0.35, nearest_body * 0.003)
        else:
            # 2. Fall back to pivot low
            pls_below = [(p, age) for p, age in pl_list if p < cp * 0.999]
            if pls_below:
                struct_pivot = max(p for p, _ in pls_below)
                raw_stop = struct_pivot - max(atr * 0.5, struct_pivot * 0.004)
            else:
                raw_stop = cp - atr * 1.5
        diff = cp - raw_stop
        # Guardrails: keep between 0.8 ATR and 2.5 ATR
        if diff < atr * 0.8:
            stop = round(cp - atr * 1.5, 2)
        elif diff > atr * 2.5:
            stop = round(cp - atr * 2.0, 2)
        else:
            stop = round(raw_stop, 2)
    else:
        phs_above = [(p, age) for p, age in ph_list if p > cp * 1.001]
        if phs_above:
            struct_pivot = min(p for p, _ in phs_above)
            raw_stop = struct_pivot + max(atr * 0.5, struct_pivot * 0.004)
        else:
            raw_stop = cp + atr * 1.5
        diff = raw_stop - cp
        if diff < atr * 0.8:
            stop = round(cp + atr * 1.5, 2)
        elif diff > atr * 2.5:
            stop = round(cp + atr * 2.0, 2)
        else:
            stop = round(raw_stop, 2)

    R = abs(cp - stop)

    # ── OPTIMAL ENTRY ZONE ────────────────────────────────────────────────
    # Rather than "buy at market", suggest a tighter entry zone.
    # Entry low: nearest structural support / demand candle body.
    # Entry high: current price (enter only at or below this level).
    if is_bullish:
        _sup_candidates = []
        if bodies_below:
            _sup_candidates.append(max(b for b, _ in bodies_below))
        if pl_list:
            _pls = [p for p, _ in pl_list if p < cp * 0.998]
            if _pls:
                _sup_candidates.append(max(_pls))
        if e20 < cp:
            _sup_candidates.append(float(e20))
        if _sup_candidates:
            entry_zone_lo = round(max(_sup_candidates), 2)
            entry_zone_hi = round(min(cp, entry_zone_lo + atr * 1.0), 2)
        else:
            entry_zone_lo = round(cp - atr * 0.5, 2)
            entry_zone_hi = round(cp, 2)
    else:
        entry_zone_lo = round(cp, 2)
        entry_zone_hi = round(cp + atr * 0.5, 2)

    # ── ENTRY QUALITY: distance from structural support ───────────────────
    if is_bullish:
        nearest_sup = stop + max(atr * 0.5, stop * 0.004)
        dist = cp - nearest_sup
    else:
        nearest_res = stop - max(atr * 0.5, stop * 0.004)
        dist = nearest_res - cp

    if dist < atr * 0.5:
        entry_quality = "OPTIMAL";  eq_col = BULL
    elif dist < atr * 1.5:
        entry_quality = "GOOD";     eq_col = "#8BC34A"
    elif dist < atr * 3.0:
        entry_quality = "ELEVATED"; eq_col = NEUT
    else:
        entry_quality = "CHASING";  eq_col = BEAR

    # ── FIBONACCI EXTENSIONS from last impulse move ───────────────────────
    fibs = {}
    try:
        if is_bullish:
            # Last impulse: most recent confirmed pivot LOW → most recent pivot HIGH after it
            if pl_list and ph_list:
                last_pl_age  = pl_list[0][1]
                last_pl_px   = pl_list[0][0]
                # Pivot HIGH that came AFTER (= younger bar age) the last pivot low
                phs_after = [(p, age) for p, age in ph_list if age < last_pl_age]
                last_ph_px = phs_after[0][0] if phs_after else cp * 1.05
                fibs = _fib_extensions(last_pl_px, last_ph_px, True)
        else:
            if ph_list and pl_list:
                last_ph_age = ph_list[0][1]
                last_ph_px  = ph_list[0][0]
                pls_after   = [(p, age) for p, age in pl_list if age < last_ph_age]
                last_pl_px  = pls_after[0][0] if pls_after else cp * 0.95
                fibs = _fib_extensions(last_pl_px, last_ph_px, False)
    except Exception:
        fibs = {}

    # ── CANDIDATE TARGET LEVELS with CONFLUENCE SCORING ──────────────────
    # Each level accumulates score; higher = more institutional interest
    candidates = {}  # price → score

    def _add(price, score):
        price = round(float(price), 2)
        if is_bullish and price > cp * 1.008:
            candidates[price] = candidates.get(price, 0) + score
        elif not is_bullish and price < cp * 0.992:
            candidates[price] = candidates.get(price, 0) + score

    # 1. Fibonacci extensions (highest quality — institutional targets)
    fib_scores = {"f618": 3, "f100": 3, "f162": 4, "f262": 3, "f424": 2}
    for key, score in fib_scores.items():
        if key in fibs:
            _add(fibs[key], score)

    # 2. Confirmed pivot highs/lows (recent = stronger)
    if is_bullish:
        for p, age in ph_list:
            if p > cp * 1.008:
                score = 4 if age < 15 else (3 if age < 40 else 2)
                _add(p, score)
    else:
        for p, age in pl_list:
            if p < cp * 0.992:
                score = 4 if age < 15 else (3 if age < 40 else 2)
                _add(p, score)

    # 3. Key EMA levels (strong institutional anchors)
    for ema, score in [(e50, 3), (e200, 4)]:
        if is_bullish and ema > cp * 1.01:
            _add(ema, score)
        elif not is_bullish and ema < cp * 0.99:
            _add(ema, score)

    # 4. Bollinger Band and 52-week extremes
    if is_bullish:
        _add(bbu,  2)
        _add(w52h, 3)
    else:
        _add(bbl,  2)
        _add(w52l, 3)

    # 5. Psychological round-number levels (retail cluster orders here)
    step = (50 if cp >= 200 else (10 if cp >= 50 else (5 if cp >= 10 else 1)))
    base = int(cp / step) * step
    for i in range(1, 15):
        rn_up   = round(base + step * i, 2)
        rn_down = round(base - step * i, 2)
        if is_bullish and rn_up > cp * 1.005:
            _add(rn_up, 1)
        elif not is_bullish and rn_down < cp * 0.995:
            _add(rn_down, 1)

    # ── CLUSTER: merge levels within 1.5% of each other ─────────────────
    sorted_prices = sorted(candidates.keys(), reverse=not is_bullish)
    merged = []  # (price, score)
    for price in sorted_prices:
        score = candidates[price]
        if not merged:
            merged.append([price, score])
        else:
            last = merged[-1][0]
            if abs(price - last) / last < 0.015:   # within 1.5%
                # Merge into highest-score member, accumulate score
                if score > merged[-1][1]:
                    merged[-1] = [price, merged[-1][1] + score]
                else:
                    merged[-1][1] += score
            else:
                merged.append([price, score])

    # ── PICK T1/T2/T3 meeting minimum R:R requirements ───────────────────
    # Fibonacci golden-ratio fallbacks
    r_t1 = round(cp + 1.618 * R, 2) if is_bullish else round(cp - 1.618 * R, 2)
    r_t2 = round(cp + 2.618 * R, 2) if is_bullish else round(cp - 2.618 * R, 2)
    r_t3 = round(cp + 4.236 * R, 2) if is_bullish else round(cp - 4.236 * R, 2)

    def _rr(price):
        return abs(price - cp) / max(0.001, R)

    valid = [(p, s) for p, s in merged if _rr(p) >= 1.3]

    # T1: closest valid level ≥ 1.5R
    t1_cands = [(p, s) for p, s in valid if _rr(p) >= 1.5]
    t1 = t1_cands[0][0] if t1_cands else r_t1

    # T2: must be ≥ 2.5R AND beyond T1
    t2_cands = [(p, s) for p, s in valid
                if _rr(p) >= 2.5 and (p > t1 if is_bullish else p < t1)]
    t2 = t2_cands[0][0] if t2_cands else r_t2

    # T3: must be ≥ 4R AND beyond T2
    t3_cands = [(p, s) for p, s in valid
                if _rr(p) >= 4.0 and (p > t2 if is_bullish else p < t2)]
    t3 = t3_cands[0][0] if t3_cands else r_t3

    # Final sanity pass
    if is_bullish:
        if t1 <= cp: t1 = r_t1
        if t2 <= t1: t2 = r_t2
        if t3 <= t2: t3 = r_t3
    else:
        if t1 >= cp: t1 = r_t1
        if t2 >= t1: t2 = r_t2
        if t3 >= t2: t3 = r_t3

    risk_pct = R / cp * 100 if cp > 0 else 2.0
    rr1      = round(_rr(t1), 1)
    rr2      = round(_rr(t2), 1)

    return {
        "entry": cp, "stop": stop, "t1": t1, "t2": t2, "t3": t3,
        "risk_pct": round(risk_pct, 1), "rr1": rr1, "rr2": rr2, "R": round(R, 2),
        "entry_quality": entry_quality, "eq_col": eq_col,
        "entry_zone_lo": entry_zone_lo, "entry_zone_hi": entry_zone_hi,
    }


    """
    From raw OHLCV dataframe compute accurate stop + 3 structural targets.
    Returns dict: entry, stop, t1, t2, t3, risk_pct, rr1, rr2, R
    """
    close = df["Close"].astype(float)
    high  = df["High"].astype(float)
    low   = df["Low"].astype(float)
    n     = len(close)

    # ATR (14-bar)
    tr_vals = []
    for i in range(1, min(15, n)):
        tr_vals.append(max(
            float(high.iloc[-i]) - float(low.iloc[-i]),
            abs(float(high.iloc[-i]) - float(close.iloc[-i - 1])),
            abs(float(low.iloc[-i])  - float(close.iloc[-i - 1])),
        ))
    atr = float(np.mean(tr_vals)) if tr_vals else cp * 0.02

    # Key indicator levels
    e20  = float(close.rolling(20).mean().iloc[-1])  if n >= 20  else cp
    e50  = float(close.rolling(50).mean().iloc[-1])  if n >= 50  else cp
    e200 = float(close.rolling(200).mean().iloc[-1]) if n >= 200 else cp
    rm   = close.rolling(20).mean()
    rs   = close.rolling(20).std()
    bbu  = float((rm + 2 * rs).iloc[-1]) if n >= 20 else cp * 1.04
    bbl  = float((rm - 2 * rs).iloc[-1]) if n >= 20 else cp * 0.96
    lb   = min(252, n)
    w52h = float(high.iloc[-lb:].max())
    w52l = float(low.iloc[-lb:].min())

    # ── Stop: tightest valid stop behind real structure ────────────────────
    recent_15_low  = float(low.iloc[-15:].min())  if n >= 15 else cp - atr * 2
    recent_15_high = float(high.iloc[-15:].max()) if n >= 15 else cp + atr * 2

    if is_bullish:
        cand_swing = recent_15_low * 0.997
        cand_ema   = (e20 - atr * 0.3) if e20 < cp * 0.999 else None
        valid      = [c for c in [cand_swing, cand_ema] if c is not None and c < cp]
        raw_stop   = max(valid) if valid else cp - atr * 1.5
        diff_s     = cp - raw_stop
        if diff_s < atr * 0.4:
            stop = round(cp - atr * 1.5, 2)
        elif diff_s > atr * 3.5:
            stop = round(cp - atr * 2.0, 2)
        else:
            stop = round(max(raw_stop, cp * 0.5), 2)
    else:
        cand_swing = recent_15_high * 1.003
        cand_ema   = (e20 + atr * 0.3) if e20 > cp * 1.001 else None
        valid      = [c for c in [cand_swing, cand_ema] if c is not None and c > cp]
        raw_stop   = min(valid) if valid else cp + atr * 1.5
        diff_s     = raw_stop - cp
        if diff_s < atr * 0.4:
            stop = round(cp + atr * 1.5, 2)
        elif diff_s > atr * 3.5:
            stop = round(cp + atr * 2.0, 2)
        else:
            stop = round(raw_stop, 2)

    R = abs(cp - stop)

    # ── Targets: structural levels from the chart ──────────────────────────
    hi_arr = list(high)
    lo_arr = list(low)
    swing_highs, swing_lows = [], []
    look_back = min(80, n - 6)
    for offset in range(4, look_back):
        pos = n - 1 - offset
        if pos < 3 or pos + 3 >= n:
            continue
        h_c = hi_arr[pos]; l_c = lo_arr[pos]
        if h_c > max(hi_arr[pos - 3:pos]) and h_c > max(hi_arr[pos + 1:pos + 4]):
            swing_highs.append(round(h_c, 2))
        if l_c < min(lo_arr[pos - 3:pos]) and l_c < min(lo_arr[pos + 1:pos + 4]):
            swing_lows.append(round(l_c, 2))

    # R-multiple fallbacks
    r_t1 = round(cp + 1.5 * R, 2) if is_bullish else round(cp - 1.5 * R, 2)
    r_t2 = round(cp + 3.0 * R, 2) if is_bullish else round(cp - 3.0 * R, 2)
    r_t3 = round(cp + 5.0 * R, 2) if is_bullish else round(cp - 5.0 * R, 2)

    if is_bullish:
        res = [lv for lv in swing_highs if lv > cp * 1.005]
        for lv in [e50, e200, bbu, w52h]:
            if lv and lv > cp * 1.01:
                res.append(round(float(lv), 2))
        res = sorted(set(res))
        merged = []
        for lv in res:
            if not merged or lv > merged[-1] * 1.015:
                merged.append(lv)
        t1 = merged[0] if len(merged) >= 1 else r_t1
        t2 = merged[1] if len(merged) >= 2 else r_t2
        t3 = merged[2] if len(merged) >= 3 else r_t3
        if t1 <= cp: t1 = r_t1
        if t2 <= t1: t2 = r_t2
        if t3 <= t2: t3 = r_t3
    else:
        sup = [lv for lv in swing_lows if lv < cp * 0.995]
        for lv in [e50, e200, bbl, w52l]:
            if lv and lv < cp * 0.99:
                sup.append(round(float(lv), 2))
        sup = sorted(set(sup), reverse=True)
        merged = []
        for lv in sup:
            if not merged or lv < merged[-1] * 0.985:
                merged.append(lv)
        t1 = merged[0] if len(merged) >= 1 else r_t1
        t2 = merged[1] if len(merged) >= 2 else r_t2
        t3 = merged[2] if len(merged) >= 3 else r_t3
        if t1 >= cp: t1 = r_t1
        if t2 >= t1: t2 = r_t2
        if t3 >= t2: t3 = r_t3

    risk_pct = R / cp * 100 if cp > 0 else 2.0
    rr1      = round(abs(t1 - cp) / max(0.001, R), 1)
    rr2      = round(abs(t2 - cp) / max(0.001, R), 1)

    return {
        "entry": cp, "stop": stop, "t1": t1, "t2": t2, "t3": t3,
        "risk_pct": round(risk_pct, 1), "rr1": rr1, "rr2": rr2, "R": round(R, 2),
    }


def price_ladder_html(cp, stop, t1, t2, t3, is_bullish,
                      entry_quality="", eq_col="",
                      entry_zone_lo=None, entry_zone_hi=None):
    """
    Generate the unified Price Ladder HTML.
    Pure HTML string — no st.* calls (safe to call from any tab).
    Optional: entry_quality label + eq_col from compute_structural_levels().
    """
    entry    = cp
    stop_col = BEAR if is_bullish else BULL
    t_col    = BULL if is_bullish else BEAR

    def _pct(price):
        return (price / entry - 1) * 100 if entry > 0 else 0.0

    def _rr(price):
        return abs(price - entry) / max(0.001, abs(entry - stop))

    stop_pct = _pct(stop)
    t1_pct   = _pct(t1);  rr1 = _rr(t1)
    t2_pct   = _pct(t2);  rr2 = _rr(t2)
    t3_pct   = _pct(t3);  rr3 = _rr(t3)
    risk_pct = abs(stop_pct)

    rr1_col = BULL if rr1 >= 2.0 else (NEUT if rr1 >= 1.5 else BEAR)
    rr2_col = BULL if rr2 >= 3.0 else (NEUT if rr2 >= 2.0 else BEAR)
    rr3_col = BULL if rr3 >= 5.0 else (NEUT if rr3 >= 3.0 else BEAR)

    # Entry zone label for the Entry cell
    ez_lo = entry_zone_lo if entry_zone_lo is not None else cp
    ez_hi = entry_zone_hi if entry_zone_hi is not None else cp

    def _cell(label, price, dist_pct, color, sub=""):
        sign     = "+" if dist_pct > 0 else ""
        if label == "Entry":
            dist_str = "Entry Point"
            if abs(ez_hi - ez_lo) > 0.001:
                sub_html = (f"<div style='font-size:0.62rem;color:{color}bb;"
                            f"margin-top:0.3rem;font-weight:600;'"
                            f">Zone: {ez_lo:.2f}&ndash;{ez_hi:.2f}</div>")
            else:
                sub_html = ""
        else:
            dist_str = f"{sign}{dist_pct:.1f}%"
            sub_html = (f"<div style='font-size:0.64rem;color:{color}99;"
                        f"margin-top:0.25rem;font-weight:600;'>{sub}</div>") if sub else ""
        return (
            f"<div style='background:#161616;border:1px solid #272727;"
            f"border-radius:10px;padding:0.9rem 0.6rem;text-align:center;"
            f"transition:border-color 0.15s;'>"
            f"<div style='font-size:0.65rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.5rem;'>{label}</div>"
            f"<div style='font-size:1.25rem;font-weight:800;color:#ffffff;"
            f"line-height:1;'>{price:.2f}</div>"
            f"<div style='font-size:0.78rem;font-weight:700;color:{color};"
            f"margin-top:0.4rem;'>{dist_str}</div>"
            + sub_html +
            f"</div>"
        )

    def _meta(label, value, color):
        return (
            f"<div style='background:#131313;border:1px solid #272727;border-radius:8px;"
            f"padding:0.65rem 0.7rem;text-align:center;'>"
            f"<div style='font-size:0.58rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:0.6px;font-weight:700;margin-bottom:0.35rem;'>{label}</div>"
            f"<div style='font-size:1.1rem;font-weight:800;color:{color};line-height:1;'>"
            f"{value}</div></div>"
        )

    # Entry quality badge (only if provided)
    eq_badge = ""
    if entry_quality:
        _ec = eq_col or NEUT
        eq_badge = (
            f"<span style='font-size:0.65rem;font-weight:700;"
            f"color:{_ec};background:rgba({','.join(str(int(_ec[i:i+2],16)) for i in (1,3,5))},0.12);"
            f"border-radius:5px;padding:0.15rem 0.5rem;'>Entry: {entry_quality}</span>"
        )

    return (
        f"<div style='background:#1b1b1b;border:1px solid #272727;"
        f"border-radius:12px;overflow:hidden;margin-bottom:0.85rem;"
        f"box-shadow:0 2px 16px rgba(0,0,0,0.2);'>"

        # Header
        f"<div style='padding:1rem 1.4rem;border-bottom:1px solid #272727;"
        f"background:linear-gradient(135deg,rgba(255,215,0,0.07),rgba(255,215,0,0.02),transparent);"
        f"display:flex;align-items:center;gap:0.8rem;'>"
        f"<span style='font-size:1.1rem;font-weight:900;color:#FFD700;"
        f"letter-spacing:-0.3px;'>Price Ladder</span>"
        + eq_badge +
        f"</div>"

        # 5-col levels grid
        f"<div style='padding:1rem 1.2rem;'>"
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.55rem;margin-bottom:0.85rem;'>"
        + _cell("Stop Loss", stop, stop_pct,  stop_col)
        + _cell("Entry",     entry, 0.0,      INFO)
        + _cell("Target 1",  t1,   t1_pct,   t_col,  f"{rr1:.1f}R")
        + _cell("Target 2",  t2,   t2_pct,   t_col,  f"{rr2:.1f}R")
        + _cell("Target 3",  t3,   t3_pct,   t_col,  f"{rr3:.1f}R")
        + f"</div>"

        # 4-col risk/reward row
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.55rem;"
        f"border-top:1px solid #272727;padding-top:0.8rem;'>"
        + _meta("Max Risk",   f"{risk_pct:.1f}%",   BEAR)
        + _meta("R:R to T1",  f"1 : {rr1:.1f}",     rr1_col)
        + _meta("R:R to T2",  f"1 : {rr2:.1f}",     rr2_col)
        + _meta("R:R to T3",  f"1 : {rr3:.1f}",     rr3_col)
        + f"</div>"
        f"</div>"

        f"</div>"
    )


def render_price_ladder(cp, stop, t1, t2, t3, is_bullish,
                        entry_quality="", eq_col="",
                        entry_zone_lo=None, entry_zone_hi=None):
    """Single call to render the Price Ladder in any Streamlit tab."""
    st.markdown(
        price_ladder_html(cp, stop, t1, t2, t3, is_bullish, entry_quality, eq_col,
                          entry_zone_lo, entry_zone_hi),
        unsafe_allow_html=True,
    )

