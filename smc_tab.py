"""
Smart Money Concepts (SMC) Tab
Analyzes: Market Structure · Liquidity Zones · Sweeps · CHoCH/BOS · Order Blocks · FVGs
Outputs a complete trade plan with bias, entry, SL, TP, R:R and confidence.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
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


# ── Tiny UI helpers ───────────────────────────────────────────────────────────
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
        f"box-shadow:0 0 8px {color}55;'></div></div>"
    )


def _kv_row(label, value, vcolor="#ffffff"):
    return (
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:0.32rem 0;border-bottom:1px solid #272727;'>"
        f"<span style='font-size:0.75rem;color:#999;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;'>{label}</span>"
        f"<span style='font-size:0.82rem;font-weight:800;color:{vcolor};'>{value}</span>"
        f"</div>"
    )


def _badge(text, color):
    return (
        f"<span style='background:rgba({','.join(str(int(color[i:i+2],16)) for i in (1,3,5)) if color.startswith('#') and len(color)==7 else '85,85,85'},0.12);"
        f"border-radius:6px;padding:0.18rem 0.6rem;"
        f"font-size:0.78rem;font-weight:800;color:{color};letter-spacing:0.4px;'>{text}</span>"
    )


# ── Core SMC engine ───────────────────────────────────────────────────────────

def _find_swing_points(df, left=3, right=3):
    """Return indices of swing highs and lows using pivot logic."""
    highs, lows = [], []
    n = len(df)
    for i in range(left, n - right):
        hi = df["High"].iloc[i]
        lo = df["Low"].iloc[i]
        if all(df["High"].iloc[i - left:i] < hi) and all(df["High"].iloc[i + 1:i + right + 1] < hi):
            highs.append(i)
        if all(df["Low"].iloc[i - left:i] > lo) and all(df["Low"].iloc[i + 1:i + right + 1] > lo):
            lows.append(i)
    return highs, lows


def _market_structure(df, swing_highs, swing_lows):
    """
    Classify market structure based on the last 4+ swing points.
    Returns: trend ("UPTREND" | "DOWNTREND" | "RANGING"), highs list, lows list
    """
    sh_prices = [(i, df["High"].iloc[i]) for i in swing_highs[-6:]]
    sl_prices = [(i, df["Low"].iloc[i])  for i in swing_lows[-6:]]

    if len(sh_prices) >= 2 and len(sl_prices) >= 2:
        hh = sh_prices[-1][1] > sh_prices[-2][1]
        hl = sl_prices[-1][1] > sl_prices[-2][1]
        lh = sh_prices[-1][1] < sh_prices[-2][1]
        ll = sl_prices[-1][1] < sl_prices[-2][1]

        if hh and hl:
            trend = "UPTREND"
        elif lh and ll:
            trend = "DOWNTREND"
        else:
            trend = "RANGING"
    else:
        trend = "RANGING"

    return trend, sh_prices, sl_prices


def _liquidity_zones(df, swing_highs, swing_lows, tolerance_pct=0.003):
    """
    Find buy-side liquidity (equal highs) and sell-side liquidity (equal lows).
    Also marks recent swing high/low as major pools.
    """
    tol = float(df["Close"].iloc[-1]) * tolerance_pct

    buy_side   = []  # equal highs → buy-side liquidity above
    sell_side  = []  # equal lows  → sell-side liquidity below

    sh_prices = [df["High"].iloc[i] for i in swing_highs[-10:]]
    sl_prices = [df["Low"].iloc[i]  for i in swing_lows[-10:]]

    # Equal highs (clustered within tolerance)
    for idx_a, va in enumerate(sh_prices):
        for idx_b in range(idx_a + 1, len(sh_prices)):
            if abs(sh_prices[idx_b] - va) <= tol:
                buy_side.append(round((va + sh_prices[idx_b]) / 2, 2))

    # Equal lows
    for idx_a, va in enumerate(sl_prices):
        for idx_b in range(idx_a + 1, len(sl_prices)):
            if abs(sl_prices[idx_b] - va) <= tol:
                sell_side.append(round((va + sl_prices[idx_b]) / 2, 2))

    # Deduplicate
    buy_side  = sorted(set(buy_side),  reverse=True)[:4]
    sell_side = sorted(set(sell_side))[:4]

    # Major pools: most recent swing high/low
    major_high = float(df["High"].iloc[swing_highs[-1]]) if swing_highs else None
    major_low  = float(df["Low"].iloc[swing_lows[-1]])  if swing_lows  else None

    return buy_side, sell_side, major_high, major_low


def _detect_sweeps(df, buy_side, sell_side, major_high, major_low, lookback=20):
    """
    Detect the most recent liquidity sweep in the last `lookback` candles.
    A sweep = price wicks beyond a level and closes back inside.
    """
    recent = df.tail(lookback)
    sweeps = []

    levels = (
        [(lvl, "buy-side") for lvl in buy_side] +
        [(lvl, "sell-side") for lvl in sell_side]
    )
    if major_high:
        levels.append((major_high, "buy-side"))
    if major_low:
        levels.append((major_low, "sell-side"))

    for lvl, side in levels:
        for i in range(len(recent)):
            row = recent.iloc[i]
            if side == "buy-side":
                if row["High"] > lvl and row["Close"] < lvl:
                    sweeps.append({
                        "level": round(lvl, 2),
                        "side": side,
                        "type": "Bearish Sweep",
                        "bar": recent.index[i],
                        "close": round(float(row["Close"]), 2),
                    })
            else:
                if row["Low"] < lvl and row["Close"] > lvl:
                    sweeps.append({
                        "level": round(lvl, 2),
                        "side": side,
                        "type": "Bullish Sweep",
                        "bar": recent.index[i],
                        "close": round(float(row["Close"]), 2),
                    })

    # Most recent sweep
    return sweeps[-1] if sweeps else None


def _detect_choch_bos(df, swing_highs, swing_lows, trend):
    """
    Detect the most recent CHoCH (Change of Character) or BOS (Break of Structure).
    CHoCH = first break against the trend → structure shift
    BOS   = break in trend direction → continuation confirmed
    """
    events = []
    cp = float(df["Close"].iloc[-1])

    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        last_sh = df["High"].iloc[swing_highs[-1]]
        prev_sh = df["High"].iloc[swing_highs[-2]]
        last_sl = df["Low"].iloc[swing_lows[-1]]
        prev_sl = df["Low"].iloc[swing_lows[-2]]

        # In uptrend: price breaking below last HL = CHoCH (bearish shift)
        if trend == "UPTREND" and cp < last_sl:
            events.append({
                "type": "CHoCH", "direction": "Bearish",
                "level": round(float(last_sl), 2),
                "desc": "Price broke below last Higher Low — structure shifted bearish"
            })
        # In uptrend: price broke above last HH = BOS (bull continuation)
        elif trend == "UPTREND" and cp > last_sh:
            events.append({
                "type": "BOS", "direction": "Bullish",
                "level": round(float(last_sh), 2),
                "desc": "Break above prior swing high — bullish continuation confirmed"
            })
        # In downtrend: price breaking above last LH = CHoCH (bullish shift)
        if trend == "DOWNTREND" and cp > last_sh:
            events.append({
                "type": "CHoCH", "direction": "Bullish",
                "level": round(float(last_sh), 2),
                "desc": "Price broke above last Lower High — structure shifted bullish"
            })
        # In downtrend: price broke below last LL = BOS (bear continuation)
        elif trend == "DOWNTREND" and cp < last_sl:
            events.append({
                "type": "BOS", "direction": "Bearish",
                "level": round(float(last_sl), 2),
                "desc": "Break below prior swing low — bearish continuation confirmed"
            })
        # Ranging: look for swing-level breaks
        if trend == "RANGING":
            if cp > last_sh:
                events.append({
                    "type": "BOS", "direction": "Bullish",
                    "level": round(float(last_sh), 2),
                    "desc": "Break above range high — potential bullish breakout"
                })
            elif cp < last_sl:
                events.append({
                    "type": "BOS", "direction": "Bearish",
                    "level": round(float(last_sl), 2),
                    "desc": "Break below range low — potential bearish breakout"
                })

    return events[-1] if events else None


def _find_order_block(df, swing_highs, swing_lows, trend, choch):
    """
    Find the most recent order block:
    - Bullish OB: last bearish candle before a strong bullish displacement
    - Bearish OB: last bullish candle before a strong bearish displacement
    """
    if len(df) < 10:
        return None

    # Determine OB direction from CHoCH/BOS signal or trend
    if choch:
        ob_dir = "Bullish" if choch["direction"] == "Bullish" else "Bearish"
    elif trend == "UPTREND":
        ob_dir = "Bullish"
    elif trend == "DOWNTREND":
        ob_dir = "Bearish"
    else:
        return None

    closes = df["Close"].values
    opens  = df["Open"].values
    highs  = df["High"].values
    lows   = df["Low"].values
    n      = len(df)

    # Look for displacement (large candle) in last 30 bars
    atr = float(pd.Series(highs[-30:] - lows[-30:]).mean())

    for i in range(n - 2, max(n - 35, 3), -1):
        body = abs(closes[i] - opens[i])
        if body < atr * 0.8:
            continue

        if ob_dir == "Bullish":
            # Displacement = large bullish candle at index i
            if closes[i] > opens[i]:
                # OB = last bearish candle before i
                for j in range(i - 1, max(i - 6, 0), -1):
                    if closes[j] < opens[j]:
                        return {
                            "direction": "Bullish",
                            "high": round(float(highs[j]), 2),
                            "low":  round(float(lows[j]),  2),
                            "mid":  round((highs[j] + lows[j]) / 2, 2),
                            "bar_label": str(df.index[j])[:10] if hasattr(df.index[j], '__str__') else str(j),
                        }
        else:
            # Displacement = large bearish candle at index i
            if closes[i] < opens[i]:
                # OB = last bullish candle before i
                for j in range(i - 1, max(i - 6, 0), -1):
                    if closes[j] > opens[j]:
                        return {
                            "direction": "Bearish",
                            "high": round(float(highs[j]), 2),
                            "low":  round(float(lows[j]),  2),
                            "mid":  round((highs[j] + lows[j]) / 2, 2),
                            "bar_label": str(df.index[j])[:10] if hasattr(df.index[j], '__str__') else str(j),
                        }

    return None


def _find_fvgs(df, lookback=40):
    """
    Fair Value Gaps: 3-candle pattern where candle[i-2].high < candle[i].low (bullish FVG)
    or candle[i-2].low > candle[i].high (bearish FVG).
    Returns the most recent unfilled FVG.
    """
    fvgs = []
    tail  = df.tail(lookback)
    cp    = float(df["Close"].iloc[-1])

    for i in range(2, len(tail)):
        h0 = float(tail["High"].iloc[i - 2])
        l0 = float(tail["Low"].iloc[i - 2])
        h2 = float(tail["High"].iloc[i])
        l2 = float(tail["Low"].iloc[i])

        # Bullish FVG: gap between candle[i-2] high and candle[i] low
        if l2 > h0:
            mid = (l2 + h0) / 2
            # Only keep if unfilled (price hasn't traded into the gap)
            if cp > mid:  # price is above → might retrace into it
                fvgs.append({
                    "type": "Bullish", "high": round(l2, 2), "low": round(h0, 2),
                    "mid": round(mid, 2)
                })
        # Bearish FVG: gap between candle[i-2] low and candle[i] high
        elif h2 < l0:
            mid = (h2 + l0) / 2
            if cp < mid:
                fvgs.append({
                    "type": "Bearish", "high": round(l0, 2), "low": round(h2, 2),
                    "mid": round(mid, 2)
                })

    return fvgs[-1] if fvgs else None


def _build_trade_plan(df, current_price, trend, sweep, choch, ob, fvg,
                       buy_side, sell_side, major_high, major_low):
    """
    Assemble a complete trade plan from the SMC signals.
    Returns dict with: bias, entry_zone, stop_loss, take_profit, rr, confidence, quality_notes
    """
    cp = current_price
    cp_f = float(cp)

    # ── Bias ─────────────────────────────────────────────────────────────────
    score = 0
    notes = []

    # CHoCH/BOS
    if choch and choch["direction"] == "Bullish":
        score += 30
        notes.append(f"{'CHoCH' if choch['type']=='CHoCH' else 'BOS'} bullish at {choch['level']:.2f}")
    elif choch and choch["direction"] == "Bearish":
        score -= 30
        notes.append(f"{'CHoCH' if choch['type']=='CHoCH' else 'BOS'} bearish at {choch['level']:.2f}")

    # Trend alignment
    if trend == "UPTREND":
        score += 20
        notes.append("Market structure: uptrend (HH/HL)")
    elif trend == "DOWNTREND":
        score -= 20
        notes.append("Market structure: downtrend (LL/LH)")
    else:
        notes.append("Market structure: ranging")

    # Sweep
    if sweep:
        if sweep["type"] == "Bullish Sweep":
            score += 20
            notes.append(f"Bullish liquidity sweep at {sweep['level']:.2f}")
        else:
            score -= 20
            notes.append(f"Bearish liquidity sweep at {sweep['level']:.2f}")

    # Order block
    if ob:
        if ob["direction"] == "Bullish" and cp_f >= ob["low"] * 0.998 and cp_f <= ob["high"] * 1.002:
            score += 15
            notes.append(f"Price in bullish OB zone ({ob['low']:.2f}–{ob['high']:.2f})")
        elif ob["direction"] == "Bearish" and cp_f >= ob["low"] * 0.998 and cp_f <= ob["high"] * 1.002:
            score -= 15
            notes.append(f"Price in bearish OB zone ({ob['low']:.2f}–{ob['high']:.2f})")

    # FVG
    if fvg:
        if fvg["type"] == "Bullish":
            score += 10
            notes.append(f"Bullish FVG at {fvg['low']:.2f}–{fvg['high']:.2f}")
        else:
            score -= 10
            notes.append(f"Bearish FVG at {fvg['low']:.2f}–{fvg['high']:.2f}")

    # ── Bias verdict ─────────────────────────────────────────────────────────
    if score >= 25:
        bias = "BUY"
        bias_color = BULL
    elif score <= -25:
        bias = "SELL"
        bias_color = BEAR
    else:
        bias = "WAIT"
        bias_color = NEUT

    # ── Entry zone ───────────────────────────────────────────────────────────
    atr_ser  = pd.Series(df["High"].values - df["Low"].values).rolling(14, min_periods=1).mean()
    atr_val  = float(atr_ser.iloc[-1])

    if bias == "BUY":
        if ob and ob["direction"] == "Bullish":
            entry_lo = ob["low"]
            entry_hi = ob["high"]
        elif fvg and fvg["type"] == "Bullish":
            entry_lo = fvg["low"]
            entry_hi = fvg["high"]
        else:
            entry_lo = cp_f - atr_val * 0.3
            entry_hi = cp_f + atr_val * 0.1
        stop_loss  = round(entry_lo - atr_val * 0.5, 2)
        tp1        = round(entry_hi + atr_val * 2, 2)
        tp2_lvl    = max(buy_side[:1] + [entry_hi + atr_val * 4]) if buy_side else round(entry_hi + atr_val * 4, 2)
        take_profit = round(float(tp2_lvl if isinstance(tp2_lvl, (int, float)) else tp2_lvl[0]), 2)

    elif bias == "SELL":
        if ob and ob["direction"] == "Bearish":
            entry_lo = ob["low"]
            entry_hi = ob["high"]
        elif fvg and fvg["type"] == "Bearish":
            entry_lo = fvg["low"]
            entry_hi = fvg["high"]
        else:
            entry_lo = cp_f - atr_val * 0.1
            entry_hi = cp_f + atr_val * 0.3
        stop_loss  = round(entry_hi + atr_val * 0.5, 2)
        tp1        = round(entry_lo - atr_val * 2, 2)
        sl_lvl     = min(sell_side[:1] + [entry_lo - atr_val * 4]) if sell_side else round(entry_lo - atr_val * 4, 2)
        take_profit = round(float(sl_lvl if isinstance(sl_lvl, (int, float)) else sl_lvl[0]), 2)

    else:
        entry_lo = cp_f - atr_val * 0.2
        entry_hi = cp_f + atr_val * 0.2
        stop_loss    = round(cp_f - atr_val, 2)
        take_profit  = round(cp_f + atr_val, 2)
        tp1          = take_profit

    entry_lo = round(entry_lo, 2)
    entry_hi = round(entry_hi, 2)
    tp1      = round(tp1, 2)

    # R:R
    risk    = abs(cp_f - stop_loss)
    reward  = abs(take_profit - cp_f)
    rr      = round(reward / risk, 2) if risk > 0 else 0

    # Confidence (0-100)
    conf_raw  = min(100, max(0, abs(score)))
    # Penalise if price is not near entry zone
    near_entry = entry_lo <= cp_f <= entry_hi
    if not near_entry:
        conf_raw = max(0, conf_raw - 20)
    # Reward aligned CHoCH + OB + sweep combo
    combo = sum([choch is not None, ob is not None, sweep is not None, fvg is not None])
    conf  = min(100, conf_raw + combo * 5)

    return {
        "bias":        bias,
        "bias_color":  bias_color,
        "score":       score,
        "confidence":  conf,
        "entry_lo":    entry_lo,
        "entry_hi":    entry_hi,
        "stop_loss":   stop_loss,
        "take_profit": take_profit,
        "tp1":         tp1,
        "rr":          rr,
        "near_entry":  near_entry,
        "notes":       notes,
        "atr":         round(atr_val, 2),
    }


# ── Chart ─────────────────────────────────────────────────────────────────────

def _build_chart(df, swing_highs, swing_lows, buy_side, sell_side,
                 ob, fvg, sweep, choch, plan, current_price):
    tail = df.tail(80).copy()
    tail = tail.reset_index(drop=False)
    date_col = "Date" if "Date" in tail.columns else tail.columns[0]

    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=tail[date_col],
        open=tail["Open"], high=tail["High"],
        low=tail["Low"],   close=tail["Close"],
        increasing_line_color=BULL, decreasing_line_color=BEAR,
        increasing_fillcolor="rgba(76,175,80,0.6)", decreasing_fillcolor="rgba(244,67,54,0.6)",
        line_width=1, name="Price",
    ))

    # Buy-side liquidity lines
    for lvl in buy_side[:3]:
        fig.add_hline(y=lvl, line=dict(color="rgba(76,175,80,0.33)", width=1, dash="dot"),
                      annotation_text=f"BSL {lvl:.2f}", annotation_position="right",
                      annotation_font=dict(color=BULL, size=10))

    # Sell-side liquidity lines
    for lvl in sell_side[:3]:
        fig.add_hline(y=lvl, line=dict(color="rgba(244,67,54,0.33)", width=1, dash="dot"),
                      annotation_text=f"SSL {lvl:.2f}", annotation_position="right",
                      annotation_font=dict(color=BEAR, size=10))

    # Order block zone
    if ob:
        ob_fill   = "rgba(76,175,80,0.13)"  if ob["direction"] == "Bullish" else "rgba(244,67,54,0.13)"
        ob_border = BULL if ob["direction"] == "Bullish" else BEAR
        fig.add_hrect(y0=ob["low"], y1=ob["high"],
                      fillcolor=ob_fill, line_color=ob_border,
                      line_width=1.5,
                      annotation_text=f"OB ({ob['direction']})",
                      annotation_position="right",
                      annotation_font=dict(color=ob_border, size=10))

    # FVG zone
    if fvg:
        fig.add_hrect(y0=fvg["low"], y1=fvg["high"],
                      fillcolor="rgba(33,150,243,0.09)", line_color=INFO,
                      line_width=1,
                      annotation_text=f"FVG ({fvg['type']})",
                      annotation_position="left",
                      annotation_font=dict(color=INFO, size=10))

    # Entry zone
    if plan["bias"] != "WAIT":
        zone_fill   = "rgba(76,175,80,0.09)"  if plan["bias"] == "BUY" else "rgba(244,67,54,0.09)"
        zone_border = BULL if plan["bias"] == "BUY" else BEAR
        fig.add_hrect(y0=plan["entry_lo"], y1=plan["entry_hi"],
                      fillcolor=zone_fill, line_color=zone_border,
                      line_width=1.5,
                      annotation_text="Entry Zone",
                      annotation_position="right",
                      annotation_font=dict(color=zone_border, size=10))

    # Stop loss
    fig.add_hline(y=plan["stop_loss"],
                  line=dict(color=BEAR, width=1.5, dash="dash"),
                  annotation_text=f"SL {plan['stop_loss']:.2f}",
                  annotation_position="right",
                  annotation_font=dict(color=BEAR, size=10))

    # Take profit
    fig.add_hline(y=plan["take_profit"],
                  line=dict(color=BULL, width=1.5, dash="dash"),
                  annotation_text=f"TP {plan['take_profit']:.2f}",
                  annotation_position="right",
                  annotation_font=dict(color=BULL, size=10))

    # Current price
    fig.add_hline(y=float(current_price),
                  line=dict(color=GOLD, width=1, dash="dot"),
                  annotation_text=f"Now {float(current_price):.2f}",
                  annotation_position="right",
                  annotation_font=dict(color=GOLD, size=10))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
        margin=dict(l=10, r=100, t=30, b=10),
        height=520,
        font=dict(family="Inter, sans-serif", color="#888", size=11),
        xaxis=dict(gridcolor="#272727", showgrid=True, zeroline=False, linecolor="#272727"),
        yaxis=dict(gridcolor="#272727", showgrid=True, zeroline=False, linecolor="#272727"),
        showlegend=False,
    )
    return fig


# ── Main render ───────────────────────────────────────────────────────────────

def _df_key(df):
    return (len(df), str(df["Close"].iloc[-1]) if len(df) else "0", str(df.index[-1]) if len(df) else "0")


@st.cache_data(ttl=300, show_spinner=False)
def _smc_compute(df_key, _df, cp):
    swing_highs, swing_lows = _find_swing_points(_df, left=3, right=3)
    if len(swing_highs) < 2:
        swing_highs = list(range(0, len(_df) - 1, max(1, len(_df) // 8)))
    if len(swing_lows) < 2:
        swing_lows  = list(range(0, len(_df) - 1, max(1, len(_df) // 8)))
    trend, sh_prices, sl_prices = _market_structure(_df, swing_highs, swing_lows)
    buy_side, sell_side, major_high, major_low = _liquidity_zones(_df, swing_highs, swing_lows)
    sweep  = _detect_sweeps(_df, buy_side, sell_side, major_high, major_low)
    choch  = _detect_choch_bos(_df, swing_highs, swing_lows, trend)
    ob     = _find_order_block(_df, swing_highs, swing_lows, trend, choch)
    fvg    = _find_fvgs(_df)
    plan   = _build_trade_plan(_df, cp, trend, sweep, choch, ob, fvg, buy_side, sell_side, major_high, major_low)
    fig    = _build_chart(_df, swing_highs, swing_lows, buy_side, sell_side, ob, fvg, sweep, choch, plan, cp)
    return dict(
        swing_highs=swing_highs, swing_lows=swing_lows,
        trend=trend, sh_prices=sh_prices, sl_prices=sl_prices,
        buy_side=buy_side, sell_side=sell_side,
        major_high=major_high, major_low=major_low,
        sweep=sweep, choch=choch, ob=ob, fvg=fvg, plan=plan, fig=fig,
    )


def smc_tab(df, current_price):
    """Entry point called from app.py"""

    if df is None or len(df) < 30:
        st.warning("Not enough data for SMC analysis. Load at least 30 bars.")
        return

    df = df.copy()
    if "Date" not in df.columns:
        df = df.reset_index()
        if "index" in df.columns:
            df.rename(columns={"index": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])

    cp = float(current_price)

    # ── Run all engines (cached) ──────────────────────────────────────────────
    _c = _smc_compute(_df_key(df), df, cp)
    swing_highs = _c["swing_highs"]; swing_lows = _c["swing_lows"]
    trend       = _c["trend"];       sh_prices  = _c["sh_prices"];  sl_prices = _c["sl_prices"]
    buy_side    = _c["buy_side"];    sell_side  = _c["sell_side"]
    major_high  = _c["major_high"]; major_low  = _c["major_low"]
    sweep       = _c["sweep"];       choch      = _c["choch"]
    ob          = _c["ob"];          fvg        = _c["fvg"]
    plan        = _c["plan"]

    bias        = plan["bias"]
    bias_color  = plan["bias_color"]
    conf        = plan["confidence"]
    conf_color  = BULL if conf >= 65 else NEUT if conf >= 40 else BEAR
    trend_color = BULL if trend == "UPTREND" else BEAR if trend == "DOWNTREND" else NEUT
    rr_color    = BULL if plan["rr"] >= 2 else NEUT if plan["rr"] >= 1 else BEAR

    # ── DECISION BOX ─────────────────────────────────────────────────────────
    _smc_verdict = bias  # "BUY", "WAIT", or "SHORT"
    _smc_vc      = bias_color
    _smc_sub     = (
        f"Smart money structure confirms a long setup — {conf}% confidence"
        if bias == "BUY" else
        f"No high-probability institutional entry detected — {conf}% confidence"
    )
    _smc_reasons = []
    if sweep:   _smc_reasons.append(f"{sweep['type']} detected — liquidity grabbed, reversal zone active")
    if choch:   _smc_reasons.append(f"{choch['type']} {choch['direction']} — market structure shifted")
    if ob:      _smc_reasons.append(f"{ob['direction']} Order Block at {ob.get('level', 0):.2f} — institutional demand zone")
    _smc_reasons = _smc_reasons[:3]
    _smc_reasons_html = "".join(
        f"<div style='display:flex;align-items:flex-start;gap:0.4rem;margin-bottom:0.3rem;'>"
        f"<span style='color:{_smc_vc};font-size:0.65rem;flex-shrink:0;margin-top:0.05rem;'>▸</span>"
        f"<span style='font-size:0.68rem;color:#aaa;line-height:1.4;'>{_r}</span></div>"
        for _r in _smc_reasons
    )
    sweep_lbl_h = sweep["type"].replace(" Sweep","") if sweep else "None"
    sweep_col_h = BULL if sweep and sweep["type"] == "Bullish Sweep" else BEAR if sweep else "#555"
    choch_lbl_h = f"{choch['type']} {choch['direction'][:4]}" if choch else "None"
    choch_col_h = BULL if choch and choch["direction"] == "Bullish" else BEAR if choch else "#555"
    ob_lbl_h    = ob["direction"][:4] if ob else "None"
    ob_col_h    = BULL if ob and ob["direction"] == "Bullish" else BEAR if ob else "#555"

    # ── Tooltip CSS + helper ──────────────────────────────────────────────────
    st.markdown("""<style>
    .smc-tip-w{position:relative;display:inline-flex;align-items:center;cursor:help;margin-left:0.3rem}
    .smc-tip-w .smc-tt{visibility:hidden;opacity:0;position:absolute;bottom:130%;left:50%;
        transform:translateX(-50%);background:#1e1e1e;color:#ccc;border:1px solid #333;
        border-radius:6px;padding:0.45rem 0.6rem;font-size:0.7rem;font-weight:500;
        line-height:1.5;white-space:normal;width:220px;text-align:left;z-index:200;
        pointer-events:none;transition:opacity .15s;box-shadow:0 4px 14px rgba(0,0,0,.5);
        text-transform:none;letter-spacing:0}
    .smc-tip-w .smc-tt::after{content:'';position:absolute;top:100%;left:50%;
        transform:translateX(-50%);border:5px solid transparent;border-top-color:#333}
    .smc-tip-w:hover .smc-tt{visibility:visible;opacity:1}
    </style>""", unsafe_allow_html=True)

    def _smctip(text):
        return (
            f"<span class='smc-tip-w'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:13px;height:13px;border-radius:50%;border:1px solid #3a3a3a;"
            f"font-size:0.48rem;color:#666;font-weight:700;'>?</span>"
            f"<span class='smc-tt'>{text}</span></span>"
        )

    _smc_tile_tips = {
        "Structure":   "Market structure: is price making higher highs & higher lows (Bullish) or lower highs & lower lows (Bearish)? Structure is the backbone of SMC — it tells you the dominant direction of institutional order flow.",
        "Sweep":       "Liquidity sweep: did price briefly spike beyond a recent swing high/low to trigger stop-losses before reversing? Institutions do this to grab cheap liquidity before pushing price the other way. A bullish sweep above a high followed by a drop = bearish. A bearish sweep below a low followed by a rally = bullish.",
        "CHoCH/BOS":   "Change of Character (CHoCH) = first sign of a trend reversal — price breaks the prior structure in the opposite direction. Break of Structure (BOS) = trend continuation confirmed. CHoCH is earlier/riskier; BOS is more conservative confirmation.",
        "Order Block": "The last bullish or bearish candle before a large impulsive move. Institutions placed their orders here and are likely to defend this zone on a retest. Bullish OB = last bearish candle before a strong up move. Bearish OB = last bullish candle before a strong down move.",
        "R : R":       "Risk to Reward ratio for this setup. For every 1 unit risked (distance to stop loss), how many units is the target away? 1:2 minimum is considered good. Below 1:1.5 = poor setup, the reward doesn't justify the risk.",
    }

    def _stat_tile(label, value, color):
        return (
            f"<div style='padding:0.85rem 1.1rem;border-right:1px solid #222;'>"
            f"<div style='display:flex;align-items:center;margin-bottom:0.3rem;'>"
            f"<div style='font-size:0.72rem;color:#ccc;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;'>{label}</div>"
            + _smctip(_smc_tile_tips.get(label, ""))
            + f"</div>"
            f"<div style='font-size:1rem;font-weight:800;color:{color};'>{value}</div>"
            f"</div>"
        )

    tiles_html = (
        _stat_tile("Structure",  trend,                trend_color)
      + _stat_tile("Sweep",      sweep_lbl_h,          sweep_col_h)
      + _stat_tile("CHoCH/BOS",  choch_lbl_h,          choch_col_h)
      + _stat_tile("Order Block",ob_lbl_h,             ob_col_h)
      + _stat_tile("R : R",      f"1:{plan['rr']:.1f}", rr_color)
    )

    _smc_ladder = ""
    if bias == "BUY":
        try:
            from _levels import price_ladder_html as _s2_plh
            _s2_stop = plan["stop_loss"]
            _s2_t1   = plan["take_profit"]
            _s2_R    = abs(cp - _s2_stop)
            _s2_t2   = round(cp + _s2_R * 3.0, 2)
            _s2_t3   = round(cp + _s2_R * 5.0, 2)
            _smc_ladder = _s2_plh(cp, _s2_stop, _s2_t1, _s2_t2, _s2_t3, True)
        except Exception:
            pass

    st.markdown(
        f"<div style='background:#181818;border:1px solid #232323;"
        f"border-top:3px solid {_smc_vc};border-radius:14px;overflow:hidden;margin-bottom:1.4rem;'>"
        f"<div style='padding:1.4rem 1.8rem;border-bottom:1px solid #222;'>"
        f"<div style='font-size:0.72rem;color:#bbb;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem;'>Smart Money Decision</div>"
        f"<div style='display:flex;align-items:center;gap:1.2rem;'>"
        f"<div style='font-size:2.4rem;font-weight:900;color:{_smc_vc};"
        f"line-height:1;letter-spacing:-1px;'>{_smc_verdict}</div>"
        f"<div style='flex:1;'>"
        f"<div style='font-size:0.82rem;color:#bbb;line-height:1.5;'>{_smc_sub}</div>"
        f"</div>"
        f"<div style='text-align:center;background:#141414;border:1px solid #232323;"
        f"border-radius:8px;padding:0.6rem 1rem;flex-shrink:0;'>"
        f"<div style='font-size:1.4rem;font-weight:900;color:{conf_color};line-height:1;'>{conf}%</div>"
        f"<div style='display:flex;align-items:center;justify-content:center;gap:0.25rem;margin-top:0.2rem;'>"
        f"<div style='font-size:0.65rem;color:#bbb;text-transform:uppercase;letter-spacing:0.5px;'>Confidence</div>"
        + _smctip("SMC confidence score (0–100). Combines structure direction, liquidity sweep, CHoCH/BOS signal, and order block proximity. Above 65 = strong institutional signal. Below 40 = no clear smart money footprint.")
        + f"</div></div></div>"
        + (f"<div style='margin-top:0.8rem;'>{_smc_reasons_html}</div>" if _smc_reasons_html else "")
        + f"</div>"
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid #222;'>"
        + tiles_html +
        f"</div>"
        + _smc_ladder
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ── 4 SIGNAL CARDS in a single 4-column row ────────────────────────────
    st.markdown(_sec("SMC Signal Breakdown", PURP), unsafe_allow_html=True)
    insight_toggle(
        "smc_breakdown",
        "What are Smart Money Concepts (SMC)?",
        "<p><strong>Order Blocks (OB)</strong> &mdash; The last bullish or bearish candle before a strong impulsive move. "
        "Institutions place large orders here, making these zones high-probability reversal areas.</p>"
        "<p><strong>Fair Value Gaps (FVG)</strong> &mdash; Price imbalances created when the market moved so fast that the buy/sell orders were not filled. "
        "Price tends to fill these gaps before continuing in the original direction.</p>"
        "<p><strong>Change of Character (CHoCH)</strong> &mdash; The first sign that a trend may be reversing. "
        "In an uptrend: price breaks below the previous swing low for the first time.</p>"
        "<p><strong>Break of Structure (BOS)</strong> &mdash; Confirms the trend is continuing. "
        "In an uptrend: price breaks above the previous swing high, confirming bullish momentum.</p>"
        "<p><strong>Liquidity Sweeps</strong> &mdash; Smart money triggers stop-losses clustered above swing highs or below swing lows "
        "to grab liquidity before reversing. A sweep followed by a strong rejection is a powerful entry signal.</p>"
    )
    
    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")

    # ── helper: compact signal card
    def _sig_card(col, accent, label, badge_text, badge_col, rows, footer=""):
        with col:
            rows_html = "".join([_kv_row(k, v, c) for k, v, c in rows])
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #272727;"
                f"border-radius:12px;overflow:hidden;height:100%;'>"
                f"<div style='padding:0.85rem 1.1rem;"
                f"background:linear-gradient(135deg,rgba({','.join(str(int(accent[i:i+2],16)) for i in (1,3,5)) if accent.startswith('#') and len(accent)==7 else '85,85,85'},0.06),transparent);'>"
                f"<div style='font-size:0.56rem;color:#999;text-transform:uppercase;"
                f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>{label}</div>"
                + _badge(badge_text, badge_col) +
                f"<div style='margin-top:0.65rem;'>{rows_html}</div>"
                + (f"<div style='font-size:0.66rem;color:#999;margin-top:0.5rem;"
                   f"line-height:1.4;border-top:1px solid #272727;padding-top:0.4rem;'>{footer}</div>"
                   if footer else "")
                + f"</div></div>",
                unsafe_allow_html=True,
            )

    # Market Structure
    last_sh_str = (f"{sh_prices[-2][1]:.2f} → {sh_prices[-1][1]:.2f}"
                   if len(sh_prices) >= 2 else
                   f"{sh_prices[-1][1]:.2f}" if sh_prices else "—")
    last_sl_str = (f"{sl_prices[-2][1]:.2f} → {sl_prices[-1][1]:.2f}"
                   if len(sl_prices) >= 2 else
                   f"{sl_prices[-1][1]:.2f}" if sl_prices else "—")
    _sig_card(sc1, trend_color, "Market Structure", trend, trend_color, [
        ("Last Highs", last_sh_str, trend_color),
        ("Last Lows",  last_sl_str, trend_color),
        ("ATR (14)",   f"{plan['atr']:.2f}", "#aaa"),
    ])

    # Liquidity
    bsl_str   = ", ".join([f"{l:.2f}" for l in buy_side[:2]]) or "None"
    ssl_str   = ", ".join([f"{l:.2f}" for l in sell_side[:2]]) or "None"
    sw_lbl    = f"{sweep['type']} @ {sweep['level']:.2f}" if sweep else "No recent sweep"
    sw_col    = BULL if sweep and sweep["type"] == "Bullish Sweep" else BEAR if sweep else "#555"
    sw_badge  = "SWEPT" if sweep else "NO SWEEP"
    _sig_card(sc2, GOLD, "Liquidity Pools", sw_badge, sw_col, [
        ("BSL (above)", bsl_str, BULL),
        ("SSL (below)", ssl_str, BEAR),
        ("Last Sweep",  sw_lbl,  sw_col),
    ])

    # CHoCH / BOS
    if choch:
        ch_color  = BULL if choch["direction"] == "Bullish" else BEAR
        ch_badge  = f"{choch['type']} {choch['direction'][:4]}"
        ch_rows   = [
            ("Level", f"{choch['level']:.2f}" if isinstance(choch['level'], float) else "—", ch_color),
        ]
        ch_footer = choch["desc"]
    else:
        ch_color = "#555"; ch_badge = "None"
        ch_rows  = [("Status", "No break detected", "#555")]
        ch_footer = "Watching for structure shift"
    _sig_card(sc3, ch_color, "CHoCH / BOS", ch_badge, ch_color, ch_rows, ch_footer)

    # OB + FVG
    if ob:
        ob_col2  = BULL if ob["direction"] == "Bullish" else BEAR
        ob_badge = f"OB {ob['direction'][:4]}"
        ob_range = f"{ob['low']:.2f} – {ob['high']:.2f}"
    else:
        ob_col2  = "#555"; ob_badge = "No OB"; ob_range = "Not identified"
    if fvg:
        fvg_range = f"{fvg['low']:.2f} – {fvg['high']:.2f}"
        fvg_col2  = INFO
        fvg_type  = fvg["type"]
    else:
        fvg_range = "None"; fvg_col2 = "#555"; fvg_type = "—"
    _sig_card(sc4, ob_col2, "Order Block & FVG",
              ob_badge, ob_col2, [
                  ("OB Zone", ob_range,                    ob_col2),
                  ("FVG",     f"{fvg_type}: {fvg_range}", fvg_col2),
              ])

    # ── CHART ─────────────────────────────────────────────────────────────────
    st.markdown(_sec("SMC Chart", INFO), unsafe_allow_html=True)
    st.plotly_chart(_c["fig"], width='stretch')


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC GETTER — called from Decision Tab
# ══════════════════════════════════════════════════════════════════════════════

def get_smc_signal(df, cp):
    """Return a BUY signal dict for the Decision Tab, or None if no trade."""
    if df is None or len(df) < 30:
        return None
    try:
        df = df.copy()
        if "Date" not in df.columns:
            df = df.reset_index()
            if "index" in df.columns:
                df.rename(columns={"index": "Date"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])

        swing_highs, swing_lows = _find_swing_points(df, left=3, right=3)
        if len(swing_highs) < 2:
            swing_highs = list(range(0, len(df) - 1, max(1, len(df) // 8)))
        if len(swing_lows) < 2:
            swing_lows  = list(range(0, len(df) - 1, max(1, len(df) // 8)))

        trend, sh_prices, sl_prices  = _market_structure(df, swing_highs, swing_lows)
        buy_side, sell_side, mh, ml  = _liquidity_zones(df, swing_highs, swing_lows)
        sweep  = _detect_sweeps(df, buy_side, sell_side, mh, ml)
        choch  = _detect_choch_bos(df, swing_highs, swing_lows, trend)
        ob     = _find_order_block(df, swing_highs, swing_lows, trend, choch)
        fvg    = _find_fvgs(df)
        plan   = _build_trade_plan(
            df, float(cp), trend, sweep, choch, ob, fvg,
            buy_side, sell_side, mh, ml,
        )
        if plan["bias"] != "BUY":
            return None

        _risk = max(abs(float(cp) - plan["stop_loss"]), 0.001)
        _t3   = round(float(cp) + _risk * 5.0, 2)

        # Build reason list from notes
        reasons = list(plan["notes"])[:3]
        if not reasons:
            reasons = [
                f"SMC Score: {plan['score']:+d} — institutional bias confirmed",
                f"Structure: {trend}",
                f"R:R {plan['rr']:.1f}:1",
            ]

        return dict(
            color=BULL,
            verdict_text="▲ BUY",
            sublabel=f"Smart Money Concepts — {trend}",
            conf=plan["confidence"],
            reasons=reasons,
            entry=float(cp),
            stop=plan["stop_loss"],
            t1=plan["tp1"],
            t2=plan["take_profit"],
            t3=_t3,
        )
    except Exception:
        return None
