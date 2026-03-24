"""
Smart Money Concepts (SMC) Tab
Analyzes: Market Structure · Liquidity Zones · Sweeps · CHoCH/BOS · Order Blocks · FVGs
Outputs a complete trade plan with bias, entry, SL, TP, R:R and confidence.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

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
        f"<div style='font-size:1rem;color:#fff;font-weight:700;"
        f"margin:2rem 0 0.9rem 0;border-bottom:2px solid {color}33;"
        f"padding-bottom:0.5rem;'>{title}</div>"
    )


def _glowbar(pct, color=BULL, height="7px"):
    pct = max(0, min(100, float(pct)))
    return (
        f"<div style='background:{BDR};border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:linear-gradient(90deg,{color}88,{color});border-radius:999px;'></div></div>"
    )


def _kv_row(label, value, vcolor="#ffffff"):
    return (
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"padding:0.32rem 0;border-bottom:1px solid {BDR};'>"
        f"<span style='font-size:0.65rem;color:#666;text-transform:uppercase;"
        f"letter-spacing:0.7px;font-weight:600;'>{label}</span>"
        f"<span style='font-size:0.82rem;font-weight:800;color:{vcolor};'>{value}</span>"
        f"</div>"
    )


def _badge(text, color):
    return (
        f"<span style='background:{color}18;border:1.5px solid {color};"
        f"border-radius:7px;padding:0.18rem 0.6rem;"
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
        paper_bgcolor=BG, plot_bgcolor=BG,
        margin=dict(l=10, r=100, t=30, b=10),
        height=520,
        font=dict(family="Inter, sans-serif", color="#9e9e9e", size=11),
        xaxis=dict(gridcolor=BDR, showgrid=True, zeroline=False, linecolor=BDR),
        yaxis=dict(gridcolor=BDR, showgrid=True, zeroline=False, linecolor=BDR),
        showlegend=False,
    )
    return fig


# ── Main render ───────────────────────────────────────────────────────────────

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

    # ── Run all engines ───────────────────────────────────────────────────────
    swing_highs, swing_lows = _find_swing_points(df, left=3, right=3)

    # Fallback if too few swings
    if len(swing_highs) < 2:
        swing_highs = list(range(0, len(df) - 1, max(1, len(df) // 8)))
    if len(swing_lows) < 2:
        swing_lows  = list(range(0, len(df) - 1, max(1, len(df) // 8)))

    trend, sh_prices, sl_prices = _market_structure(df, swing_highs, swing_lows)
    buy_side, sell_side, major_high, major_low = _liquidity_zones(df, swing_highs, swing_lows)
    sweep  = _detect_sweeps(df, buy_side, sell_side, major_high, major_low)
    choch  = _detect_choch_bos(df, swing_highs, swing_lows, trend)
    ob     = _find_order_block(df, swing_highs, swing_lows, trend, choch)
    fvg    = _find_fvgs(df)
    plan   = _build_trade_plan(
        df, cp, trend, sweep, choch, ob, fvg,
        buy_side, sell_side, major_high, major_low
    )

    bias        = plan["bias"]
    bias_color  = plan["bias_color"]
    conf        = plan["confidence"]
    conf_color  = BULL if conf >= 65 else NEUT if conf >= 40 else BEAR
    trend_color = BULL if trend == "UPTREND" else BEAR if trend == "DOWNTREND" else NEUT
    rr_color    = BULL if plan["rr"] >= 2 else NEUT if plan["rr"] >= 1 else BEAR

    # ── HERO ─────────────────────────────────────────────────────────────────
    bias_glow   = bias_color + "22"
    bias_border = bias_color + "44"

    # 5 quick-stat tiles for the hero bottom row
    sweep_lbl_h = sweep["type"].replace(" Sweep","") if sweep else "None"
    sweep_col_h = BULL if sweep and sweep["type"] == "Bullish Sweep" else BEAR if sweep else "#555"
    choch_lbl_h = f"{choch['type']} {choch['direction'][:4]}" if choch else "None"
    choch_col_h = BULL if choch and choch["direction"] == "Bullish" else BEAR if choch else "#555"
    ob_lbl_h    = ob["direction"][:4] if ob else "None"
    ob_col_h    = BULL if ob and ob["direction"] == "Bullish" else BEAR if ob else "#555"

    def _stat_tile(label, value, color):
        return (
            f"<div style='background:{BG};border:1px solid {BDR};border-radius:10px;"
            f"padding:0.55rem 0.9rem;text-align:center;'>"
            f"<div style='font-size:0.57rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.2rem;'>{label}</div>"
            f"<div style='font-size:0.92rem;font-weight:900;color:{color};'>{value}</div>"
            f"</div>"
        )

    tiles_html = (
        _stat_tile("Structure",  trend,         trend_color)
      + _stat_tile("Sweep",      sweep_lbl_h,   sweep_col_h)
      + _stat_tile("CHoCH/BOS",  choch_lbl_h,   choch_col_h)
      + _stat_tile("Order Block",ob_lbl_h,      ob_col_h)
      + _stat_tile("R : R",      f"1:{plan['rr']:.1f}", rr_color)
    )

    st.markdown(
        f"<div style='background:{BG2};"
        f"border:1px solid {BDR};border-left:5px solid {bias_color};border-radius:14px;"
        f"padding:2rem 2.2rem;margin-bottom:1.2rem;'>"
        # ── top row
        f"<div style='display:flex;align-items:flex-start;justify-content:space-between;"
        f"margin-bottom:1.6rem;gap:2rem;'>"
        # left block
        f"<div style='flex:1;'>"
        f"<div style='font-size:0.57rem;color:#555;text-transform:uppercase;"
        f"letter-spacing:1.5px;font-weight:700;margin-bottom:0.4rem;'>Smart Money Concepts</div>"
        f"<div style='font-size:0.85rem;color:#999;margin-bottom:1.2rem;'>Institutional Structure · Order Flow · Liquidity</div>"
        f"<div style='display:flex;align-items:center;gap:1.2rem;'>"
        f"<div style='background:{bias_glow};border:2px solid {bias_color};"
        f"border-radius:14px;padding:0.55rem 1.6rem;'>"
        f"<div style='font-size:2.8rem;font-weight:900;color:{bias_color};"
        f"letter-spacing:2px;line-height:1;'>{bias}</div>"
        f"</div>"
        f"<div>"
        f"<div style='font-size:0.7rem;color:#888;font-weight:600;margin-bottom:0.15rem;'>Market Bias</div>"
        f"<div style='font-size:0.78rem;color:#bbb;'>SMC Score &nbsp;"
        f"<b style='color:{bias_color};font-size:0.95rem;'>{plan['score']:+d}</b></div>"
        f"</div>"
        f"</div>"
        f"</div>"
        # right: confidence dial
        f"<div style='text-align:center;background:{BG};border:1px solid {BDR};"
        f"border-radius:16px;padding:1.2rem 1.8rem;min-width:110px;flex-shrink:0;'>"
        f"<div style='font-size:0.57rem;color:#555;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Confidence</div>"
        f"<div style='font-size:2.6rem;font-weight:900;color:{conf_color};"
        f"line-height:1;margin-bottom:0.4rem;'>{conf}%</div>"
        + _glowbar(conf, conf_color, "5px") +
        f"</div>"
        f"</div>"
        # ── bottom stat tiles
        f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.6rem;'>"
        f"{tiles_html}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── 4 SIGNAL CARDS in a single 4-column row ────────────────────────────
    st.markdown(_sec("SMC Signal Breakdown", PURP), unsafe_allow_html=True)

    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")

    # ── helper: compact signal card
    def _sig_card(col, accent, label, badge_text, badge_col, rows, footer=""):
        with col:
            rows_html = "".join([_kv_row(k, v, c) for k, v, c in rows])
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:3px solid {accent};border-radius:14px;"
                f"padding:1rem 1.1rem;height:100%;'>"
                f"<div style='font-size:0.56rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>{label}</div>"
                + _badge(badge_text, badge_col) +
                f"<div style='margin-top:0.65rem;'>{rows_html}</div>"
                + (f"<div style='font-size:0.66rem;color:#555;margin-top:0.5rem;"
                   f"line-height:1.4;border-top:1px solid {BDR};padding-top:0.4rem;'>{footer}</div>"
                   if footer else "")
                + f"</div>",
                unsafe_allow_html=True,
            )

    # Market Structure
    recent_sh = sh_prices[-3:] if len(sh_prices) >= 3 else sh_prices
    recent_sl = sl_prices[-3:] if len(sl_prices) >= 3 else sl_prices
    sh_labels = " → ".join([f"{p:.2f}" for _, p in recent_sh])
    sl_labels = " → ".join([f"{p:.2f}" for _, p in recent_sl])
    _sig_card(sc1, trend_color, "Market Structure", trend, trend_color, [
        ("Swing Highs", sh_labels, trend_color),
        ("Swing Lows",  sl_labels, trend_color),
        ("ATR (14)",    f"{plan['atr']:.2f}", "#aaa"),
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
        ch_color = BULL if choch["direction"] == "Bullish" else BEAR
        ch_badge = choch["type"]
        ch_rows  = [
            ("Type",      choch["type"],                                       ch_color),
            ("Direction", choch["direction"],                                  ch_color),
            ("Level",     f"{choch['level']:.2f}" if isinstance(choch['level'], float) else "—", "#aaa"),
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
                  ("OB Zone",  ob_range,  ob_col2),
                  ("OB Dir.",  ob["direction"] if ob else "—", ob_col2),
                  ("FVG",      f"{fvg_type}: {fvg_range}", fvg_col2),
              ])

    # ── TRADE PLAN ────────────────────────────────────────────────────────────
    st.markdown(_sec("Trade Plan — Entry · Stop Loss · Targets", bias_color), unsafe_allow_html=True)

    sl_p  = plan["stop_loss"]
    en_lo = plan["entry_lo"]
    en_hi = plan["entry_hi"]
    tp1_p = plan["tp1"]
    tp2_p = plan["take_profit"]
    cur   = float(cp)

    near_str = "✓ Price in zone" if plan["near_entry"] else "Wait for retrace"
    near_col = BULL if plan["near_entry"] else NEUT

    sl_pct  = (sl_p  / cur - 1) * 100
    tp1_pct = (tp1_p / cur - 1) * 100
    tp2_pct = (tp2_p / cur - 1) * 100
    risk_pct = abs(cur - sl_p) / cur * 100

    lad_col, met_col = st.columns(2, gap="medium")

    with lad_col:
        def _ladder_row(label, price, color, is_current=False):
            border = f"border:1px solid {color};" if is_current else f"border:1px solid {BDR};"
            bg     = BG if is_current else BG2
            return (
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"{border}border-radius:8px;padding:0.45rem 0.8rem;margin-bottom:0.32rem;"
                f"background:{bg};'>"
                f"<span style='font-size:0.62rem;color:#666;font-weight:600;"
                f"text-transform:uppercase;letter-spacing:0.5px;'>{label}</span>"
                f"<span style='font-size:0.88rem;font-weight:900;color:{color};'>{price:.2f}</span>"
                f"</div>"
            )

        ladder = (
            _ladder_row("TARGET 2", tp2_p, "#8BC34A")
          + _ladder_row("TARGET 1", tp1_p, BULL)
          + _ladder_row("PRICE",    cur,   GOLD, is_current=True)
          + _ladder_row("ENTRY HI", en_hi, INFO)
          + _ladder_row("ENTRY LO", en_lo, INFO)
          + _ladder_row("STOP",     sl_p,  BEAR)
        )
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {BDR};"
            f"border-top:3px solid {bias_color};border-radius:14px;"
            f"padding:1.2rem 1.2rem;'>"
            f"<div style='font-size:0.56rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.8rem;'>Price Ladder</div>"
            f"{ladder}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with met_col:
        notes_html = "".join([
            f"<div style='display:flex;align-items:flex-start;gap:0.4rem;"
            f"padding:0.3rem 0;border-bottom:1px solid {BDR};'>"
            f"<span style='color:{bias_color};font-size:0.7rem;margin-top:0.05rem;'>▸</span>"
            f"<span style='font-size:0.68rem;color:#999;line-height:1.45;'>{n}</span>"
            f"</div>"
            for n in plan["notes"]
        ]) or f"<div style='font-size:0.68rem;color:#555;'>No aligned signals.</div>"

        stats_rows = (
            f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
            f"border-bottom:1px solid {BDR};'>"
            f"<span style='font-size:0.68rem;color:#666;'>Stop risk</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:{BEAR};'>{risk_pct:.1f}%</span></div>"

            f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
            f"border-bottom:1px solid {BDR};'>"
            f"<span style='font-size:0.68rem;color:#666;'>Target 1 gain</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:{BULL};'>+{tp1_pct:.1f}%</span></div>"

            f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
            f"border-bottom:1px solid {BDR};'>"
            f"<span style='font-size:0.68rem;color:#666;'>Target 2 gain</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:#8BC34A;'>+{tp2_pct:.1f}%</span></div>"

            f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
            f"border-bottom:1px solid {BDR};'>"
            f"<span style='font-size:0.68rem;color:#666;'>R:R</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:{rr_color};'>1:{plan['rr']:.1f}</span></div>"

            f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
            f"border-bottom:1px solid {BDR};'>"
            f"<span style='font-size:0.68rem;color:#666;'>Entry zone</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:#fff;'>{en_lo:.2f} – {en_hi:.2f}</span></div>"

            f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;'>"
            f"<span style='font-size:0.68rem;color:#666;'>Price status</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:{near_col};'>{near_str}</span></div>"
        )
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {BDR};"
            f"border-top:3px solid {conf_color};border-radius:14px;"
            f"padding:1.2rem 1.4rem;'>"
            f"<div style='font-size:0.56rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Trade Metrics</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;"
            f"margin-bottom:0.4rem;'>"
            f"<span style='font-size:0.65rem;color:#666;'>Setup Confidence</span>"
            f"<span style='font-size:1.2rem;font-weight:900;color:{conf_color};'>{conf}%</span>"
            f"</div>"
            + _glowbar(conf, conf_color, "6px") +
            f"<div style='margin-top:0.75rem;'>{stats_rows}</div>"
            f"<div style='margin-top:0.8rem;border-top:1px solid {BDR};padding-top:0.6rem;'>"
            f"<div style='font-size:0.56rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.4rem;'>Quality Factors</div>"
            f"{notes_html}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── CHART ─────────────────────────────────────────────────────────────────
    st.markdown(_sec("SMC Chart", INFO), unsafe_allow_html=True)
    fig = _build_chart(
        df, swing_highs, swing_lows, buy_side, sell_side,
        ob, fvg, sweep, choch, plan, current_price
    )
    st.plotly_chart(fig, width='stretch')
