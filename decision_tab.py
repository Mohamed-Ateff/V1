"""
Decision Intelligence Tab v3
Advanced probability engine with historical analogs, scenario analysis,
conditional win rates, and confidence intervals.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ui_helpers import insight_toggle

# Lazy-import sibling modules only when needed to avoid circular imports
def _import_pa():
    from price_action_tab import _compute_trade_setup
    return _compute_trade_setup

def _import_vp():
    from volume_profile_tab import _compute_volume_profile, _vp_signal
    return _compute_volume_profile, _vp_signal

def _import_pt():
    from patterns_tab import _detect_candlestick, _detect_chart
    return _detect_candlestick, _detect_chart

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS  (shared style with other tabs)
# ─────────────────────────────────────────────────────────────────────────────
BULL  = "#4caf50"
BEAR  = "#f44336"
NEUT  = "#ff9800"
INFO  = "#2196f3"
PURP  = "#9c27b0"
BG    = "#181818"
BG2   = "#212121"
BDR   = "#303030"


def _sec(title, color=INFO):
    return (
        f"<div style='display:flex;align-items:center;gap:0.6rem;"
        f"margin:2.2rem 0 1rem;padding:0;'>"
        f"<div style='width:3px;height:18px;border-radius:2px;background:{color};"
        f"box-shadow:0 0 8px {color}44;'></div>"
        f"<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
        f"text-transform:uppercase;letter-spacing:0.8px;'>{title}</span></div>"
    )


def _glowbar(pct, color=BULL, height="5px"):
    pct = max(0, min(100, pct))
    return (
        f"<div style='background:#1a1a1a;border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;border-radius:999px;"
        f"background:linear-gradient(90deg,{color}cc,{color});"
        f"box-shadow:0 0 8px {color}55;"
        f"transition:width 0.4s ease;'></div></div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL SUMMARY HELPERS  (compute signals from other tabs without importing
# their full render functions)
# ─────────────────────────────────────────────────────────────────────────────

def _get_pa_signal(df, current_price):
    """Re-derive the Price Action tab signal (Market Structure + Trade Setup)."""
    try:
        recent_20  = df.tail(20)
        swing_high = float(recent_20["High"].max())
        swing_low  = float(recent_20["Low"].min())
        higher_high = df["High"].iloc[-5:].max() > df["High"].iloc[-15:-5].max()
        higher_low  = df["Low"].iloc[-5:].min()  > df["Low"].iloc[-15:-5].min()
        lower_low   = df["Low"].iloc[-5:].min()  < df["Low"].iloc[-15:-5].min()
        lower_high  = df["High"].iloc[-5:].max() < df["High"].iloc[-15:-5].max()
        if higher_high and higher_low:
            trend, t_col = "UPTREND",   BULL
        elif lower_low and lower_high:
            trend, t_col = "DOWNTREND", BEAR
        else:
            trend, t_col = "SIDEWAYS",  NEUT

        res1 = float(df["High"].max())
        res2 = float(df["High"].nlargest(2).iloc[-1]) if len(df) >= 2 else res1
        sup1 = float(df["Low"].min())
        sup2 = float(df["Low"].nsmallest(2).iloc[-1]) if len(df) >= 2 else sup1

        ma   = df["Close"].rolling(window=20).mean()
        zone_width = 1.5
        r_zone_lo  = res1 - zone_width;  r_zone_hi = res1 + zone_width
        s_zone_lo  = sup1 - zone_width;  s_zone_hi = sup1 + zone_width
        r_touches  = len(df[df["High"] >= r_zone_lo])
        s_touches  = len(df[df["Low"]  <= s_zone_hi])
        r_str = "STRONG" if r_touches >= 5 else "MODERATE" if r_touches >= 3 else "WEAK"
        s_str = "STRONG" if s_touches >= 5 else "MODERATE" if s_touches >= 3 else "WEAK"
        in_r  = r_zone_lo <= current_price <= r_zone_hi
        in_s  = s_zone_lo <= current_price <= s_zone_hi

        _compute_trade_setup = _import_pa()
        ts = _compute_trade_setup(
            df=df, current_price=current_price, trend=trend,
            sup1=sup1, sup2=sup2, res1=res1, res2=res2,
            swing_low=swing_low, swing_high=swing_high,
            ma_series=ma, s_touches=s_touches, r_touches=r_touches,
            s_str=s_str, r_str=r_str, in_s=in_s, in_r=in_r,
        )

        if ts is None:
            return None
        if ts.get("no_trade"):
            signal = "WAIT"
            conf   = 0
            color  = "#555"
            sub    = ts.get("no_trade_reason", "No clear setup")
        else:
            signal = "BUY"
            conf   = ts.get("conf", 0)
            color  = BULL
            sub    = f"Confidence {conf}% · {trend}"
        return dict(label="Market Structure", signal=signal, conf=conf,
                    color=color, trend=trend, trend_col=t_col, sub=sub)
    except Exception:
        return None


def _get_vp_signal(df, current_price):
    """Re-derive the Volume Profile tab signal."""
    try:
        if "Volume" not in df.columns or df["Volume"].sum() == 0:
            return None
        _compute_volume_profile, _vp_signal = _import_vp()
        vp = _compute_volume_profile(df, bins=40)
        if vp is None:
            return None
        sig = _vp_signal(vp, current_price, df)
        raw_sig = sig["signal"]
        display_sig = "BUY" if raw_sig == "BUY" else "SELL" if raw_sig == "SELL" else "WAIT"
        if raw_sig == "BUY":
            color = BULL
        elif raw_sig == "SELL":
            color = BEAR
        elif raw_sig == "WATCH":
            color = NEUT
        else:
            color = "#555"
        pct_from_poc = (current_price / vp["poc"] - 1) * 100 if vp["poc"] else 0
        sub = f"Score {sig['score']}/100 · {sig['zone']}"
        return dict(label="Volume Profile", signal=display_sig,
                    score=sig["score"], color=color,
                    poc=vp["poc"], vah=vp["vah"], val=vp["val"], sub=sub)
    except Exception:
        return None


def _get_pattern_signal(df):
    """Re-derive the Patterns tab signal."""
    try:
        _detect_candlestick, _detect_chart = _import_pt()
        cs  = _detect_candlestick(df)
        ch  = _detect_chart(df)
        all_p = cs + ch

        recent_dates = set(df["Date"].tail(10).dt.normalize().tolist())
        active = [p for p in all_p
                  if pd.to_datetime(p["date"]).normalize() in recent_dates]

        bull_cnt = sum(1 for p in active if p["type"] == "Bullish")
        bear_cnt = sum(1 for p in active if p["type"] == "Bearish")
        net_bias = bull_cnt - bear_cnt

        if net_bias > 0:
            signal, color = "BUY",  BULL
        elif net_bias < 0:
            signal, color = "SELL", BEAR
        else:
            signal, color = "WAIT", NEUT

        strongest = max(active, key=lambda p: p["strength"]) if active else None
        if strongest:
            sub = f"{strongest['pattern']} · {strongest['strength']}% strength"
        elif not active:
            sub = "No active patterns in last 10 sessions"
        else:
            sub = f"{bull_cnt} bullish, {bear_cnt} bearish"

        return dict(label="Pattern Signal", signal=signal,
                    bull=bull_cnt, bear=bear_cnt, active=len(active),
                    color=color, sub=sub)
    except Exception:
        return None


def _render_signal_summaries(df, current_price):
    """Render 3 signal sub-cards (Market Structure, Pattern Signal, Volume Profile) side by side."""
    df = df.copy()
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    pa  = _get_pa_signal(df, current_price)
    vp  = _get_vp_signal(df, current_price)
    pat = _get_pattern_signal(df)

    def _mini_card_html(card):
        c   = card["color"]
        stats = card.get("stats", [])
        stats_rows = "".join([
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:0.45rem 0;'>"
            f"<span style='font-size:0.68rem;color:#9e9e9e;font-weight:500;'>{sn}</span>"
            f"<span style='font-size:0.78rem;font-weight:700;color:{sc};'>{sv}</span>"
            f"</div>"
            for sn, sv, sc in stats
        ])
        return (
            f"<div style='background:#1b1b1b;border:1px solid #272727;"
            f"border-radius:12px;overflow:hidden;"
            f"box-shadow:0 2px 12px rgba(0,0,0,0.2);'>"
            f"<div style='padding:0.8rem 1.1rem;border-bottom:1px solid #272727;"
            f"background:linear-gradient(135deg,rgba({','.join(str(int(c[i:i+2],16)) for i in (1,3,5))},0.07),transparent);'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<span style='font-size:0.78rem;color:#bdbdbd;font-weight:700;"
            f"text-transform:uppercase;letter-spacing:0.4px;'>{card['label']}</span>"
            f"<span style='font-size:1rem;font-weight:900;color:{c};"
            f"text-shadow:0 0 10px {c}33;'>{card['signal']}</span>"
            f"</div></div>"
            f"<div style='padding:0.85rem 1.1rem;'>"
            f"<div style='font-size:0.74rem;color:#888;margin-bottom:0.65rem;"
            f"line-height:1.5;'>{card['sub']}</div>"
            + _glowbar(card["bar"], c) +
            f"<div style='margin-top:0.75rem;border-top:1px solid #272727;padding-top:0.55rem;'>{stats_rows}</div>"
            f"</div></div>"
        )

    sub_cards = []
    if pa:
        sub_cards.append(dict(
            label="Market Structure",
            signal=pa["signal"],
            color=pa["color"],
            bar=pa["conf"] if pa.get("conf") else 0,
            sub=pa["sub"],
            stats=[
                ("Trend",  pa["trend"],  pa["trend_col"]),
                ("Setup",  pa["signal"], pa["color"]),
            ],
        ))
    if pat:
        pat_bar = min(100, max(0, (pat["bull"] + pat["bear"]) * 12))
        sub_cards.append(dict(
            label="Pattern Signal",
            signal=pat["signal"],
            color=pat["color"],
            bar=pat_bar,
            sub=pat["sub"],
            stats=[
                ("Active",   str(pat["active"]), INFO),
                ("Bullish",  str(pat["bull"]),    BULL),
                ("Bearish",  str(pat["bear"]),    BEAR),
            ],
        ))
    if vp:
        sub_cards.append(dict(
            label="Volume Profile",
            signal=vp["signal"],
            color=vp["color"],
            bar=vp.get("score", 0),
            sub=vp["sub"],
            stats=[
                ("VAL",   f"${vp['val']:.2f}",       BULL),
                ("POC",   f"${vp['poc']:.2f}",       "#FFD700"),
                ("VAH",   f"${vp['vah']:.2f}",       BEAR),
                ("Score", f"{vp.get('score',0)}/100", vp["color"]),
            ],
        ))

    if not sub_cards:
        return

    while len(sub_cards) < 3:
        sub_cards.append(None)

    col1, col2, col3 = st.columns(3, gap="small")
    for col, card in zip([col1, col2, col3], sub_cards[:3]):
        with col:
            if card:
                st.markdown(_mini_card_html(card), unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background:#1b1b1b;border:1px solid #272727;"
                    f"border-radius:12px;padding:1.1rem 1.2rem;opacity:0.2;"
                    f"text-align:center;color:#555;font-size:0.75rem;'>—</div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fv(df, col, bars_back=0, default=None):
    if col not in df.columns:
        return default
    s = df[col].dropna()
    if len(s) <= bars_back:
        return default
    v = s.iloc[-(1 + bars_back)]
    return float(v) if not (isinstance(v, float) and np.isnan(v)) else default


def _col(df, *names):
    for n in names:
        v = _fv(df, n)
        if v is not None:
            return v
    return None


def _pct(a, b):
    """Safe (a/b - 1) * 100."""
    if b and b != 0:
        return (float(a) / float(b) - 1) * 100
    return 0.0


def _quartile(lst, q):
    """q in [0,1]."""
    if not lst:
        return 0.0
    s = sorted(lst)
    idx = int(len(s) * q)
    return float(s[min(idx, len(s) - 1)])


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE  (unchanged from v2 — produces composite score + factors)
# ─────────────────────────────────────────────────────────────────────────────

def _score_engine(df, cp):
    close  = df["Close"].astype(float)
    high   = df["High"].astype(float)
    low    = df["Low"].astype(float)
    volume = (df["Volume"].astype(float) if "Volume" in df.columns
              else pd.Series(np.ones(len(close))))
    n = len(close)

    e20    = _fv(df, "EMA_20")  or cp
    e50    = _fv(df, "EMA_50")  or cp
    e200   = _fv(df, "EMA_200") or cp
    rsi    = _col(df, "RSI_14") or 50.0
    macd   = _col(df, "MACD_12_26_9") or 0.0
    macd_s = _col(df, "MACDs_12_26_9") or 0.0
    macd_h = _col(df, "MACDh_12_26_9") or 0.0
    macd_h_prev = _fv(df, "MACDh_12_26_9", bars_back=1) or 0.0
    adx    = _col(df, "ADX_14") or 15.0
    atr    = _col(df, "ATR_14") or (cp * 0.02)
    sk     = _col(df, "STOCHk_14_3_3") or 50.0
    sd_val = _col(df, "STOCHd_14_3_3") or 50.0
    sk_p   = _fv(df, "STOCHk_14_3_3", bars_back=1) or 50.0
    sd_p   = _fv(df, "STOCHd_14_3_3", bars_back=1) or 50.0
    bbl    = _col(df, "BBL_20_2.0", "BBL_20") or (cp * 0.97)
    bbu    = _col(df, "BBU_20_2.0", "BBU_20") or (cp * 1.03)
    mfi    = _col(df, "MFI_14")
    cmf    = _col(df, "CMF_20")
    cci    = _col(df, "CCI_20", "CCI_20_0.015")
    regime = (df.iloc[-1].get("REGIME", "VOLATILE")
              if "REGIME" in df.columns else "VOLATILE")

    vol_20  = float(volume.iloc[-20:].mean()) if n >= 20 else float(volume.mean())
    vol_cur = float(volume.iloc[-1])
    vol_ratio = vol_cur / vol_20 if vol_20 > 0 else 1.0

    obv_rising = None
    if "OBV" in df.columns:
        obv_s = df["OBV"].dropna()
        if len(obv_s) >= 10:
            obv_rising = float(obv_s.iloc[-1]) > float(obv_s.iloc[-10])

    lb = min(252, n)
    w52h = float(high.iloc[-lb:].max())
    w52l = float(low.iloc[-lb:].min())
    w52_pos = (cp - w52l) / (w52h - w52l) * 100 if (w52h - w52l) > 0 else 50.0

    atr_pct = atr / cp * 100 if cp > 0 else 2.0
    p5d  = _pct(cp, float(close.iloc[-5]))  if n >= 6  else 0.0
    p20d = _pct(cp, float(close.iloc[-20])) if n >= 21 else 0.0
    p60d = _pct(cp, float(close.iloc[-60])) if n >= 61 else 0.0
    bb_rng = bbu - bbl
    bb_pct = (cp - bbl) / bb_rng if bb_rng > 0 else 0.5

    factors = []

    def F(name, pts, max_pts, cat, direction):
        factors.append({"name": name, "pts": pts, "max": max_pts,
                        "cat": cat, "dir": direction})

    above_all = cp > e20 > e50 > e200
    below_all = cp < e20 < e50 < e200
    above_2   = cp > e20 and cp > e50
    below_2   = cp < e20 and cp < e50

    if above_all:
        F("EMA Stack Full Bull — price above EMA20, EMA50, EMA200", 8, 8, "Trend", 1)
    elif above_2:
        F("EMA Stack Partial Bull — price above EMA20 and EMA50", 5, 8, "Trend", 1)
    elif cp > e20:
        F("Price above EMA20 only (weak bull)", 2, 8, "Trend", 1)
    elif below_all:
        F("EMA Stack Full Bear — price below EMA20, EMA50, EMA200", -8, 8, "Trend", -1)
    elif below_2:
        F("EMA Stack Partial Bear — price below EMA20 and EMA50", -5, 8, "Trend", -1)
    elif cp < e20:
        F("Price below EMA20 only (weak bear)", -2, 8, "Trend", -1)

    macd_p1  = _fv(df, "MACD_12_26_9",  bars_back=1) or macd
    macds_p1 = _fv(df, "MACDs_12_26_9", bars_back=1) or macd_s
    cross_up   = macd > macd_s and macd_p1 <= macds_p1
    cross_down = macd < macd_s and macd_p1 >= macds_p1
    hist_acc   = macd_h > macd_h_prev

    if cross_up:
        F("MACD bullish crossover — fresh buy signal", 6, 6, "Momentum", 1)
    elif macd > macd_s and hist_acc:
        F("MACD bullish and accelerating", 4, 6, "Momentum", 1)
    elif macd > macd_s:
        F("MACD above signal line (bullish)", 2, 6, "Momentum", 1)
    elif cross_down:
        F("MACD bearish crossover — fresh sell signal", -6, 6, "Momentum", -1)
    elif macd < macd_s and not hist_acc:
        F("MACD bearish and weakening", -4, 6, "Momentum", -1)
    elif macd < macd_s:
        F("MACD below signal line (bearish)", -2, 6, "Momentum", -1)

    if rsi < 25:
        F(f"RSI deeply oversold ({rsi:.0f}) — extreme fear zone", 6, 6, "Momentum", 1)
    elif rsi < 35:
        F(f"RSI oversold ({rsi:.0f})", 4, 6, "Momentum", 1)
    elif rsi > 80:
        F(f"RSI deeply overbought ({rsi:.0f}) — extreme greed zone", -6, 6, "Momentum", -1)
    elif rsi > 70:
        F(f"RSI overbought ({rsi:.0f})", -4, 6, "Momentum", -1)
    elif 45 <= rsi <= 65:
        F(f"RSI neutral ({rsi:.0f}) — no directional edge", 0, 6, "Momentum", 0)

    if sk < 25 and sk > sd_val and sk_p <= sd_p:
        F(f"Stoch bullish crossover from oversold ({sk:.0f})", 4, 4, "Momentum", 1)
    elif sk < 25:
        F(f"Stoch oversold ({sk:.0f})", 2, 4, "Momentum", 1)
    elif sk > 75 and sk < sd_val and sk_p >= sd_p:
        F(f"Stoch bearish crossover from overbought ({sk:.0f})", -4, 4, "Momentum", -1)
    elif sk > 75:
        F(f"Stoch overbought ({sk:.0f})", -2, 4, "Momentum", -1)

    if bb_pct < 0.05:
        F("Price at lower Bollinger Band — 2-sigma oversold", 4, 4, "Volatility", 1)
    elif bb_pct < 0.20:
        F("Price near lower BB — value zone", 2, 4, "Volatility", 1)
    elif bb_pct > 0.95:
        F("Price at upper Bollinger Band — 2-sigma overbought", -4, 4, "Volatility", -1)
    elif bb_pct > 0.80:
        F("Price near upper BB — extended", -2, 4, "Volatility", -1)

    pos_di = _col(df, "DMP_14") or 20.0
    neg_di = _col(df, "DMN_14") or 20.0
    if adx > 30 and pos_di > neg_di:
        F(f"Strong bullish trend — ADX {adx:.0f}, +DI above -DI", 4, 4, "Trend", 1)
    elif adx > 20 and pos_di > neg_di:
        F(f"Bullish trend — ADX {adx:.0f}", 2, 4, "Trend", 1)
    elif adx > 30 and neg_di > pos_di:
        F(f"Strong bearish trend — ADX {adx:.0f}, -DI above +DI", -4, 4, "Trend", -1)
    elif adx > 20 and neg_di > pos_di:
        F(f"Bearish trend — ADX {adx:.0f}", -2, 4, "Trend", -1)
    elif adx < 15:
        F(f"No trend — ADX {adx:.0f}, choppy", 0, 4, "Trend", 0)

    if vol_ratio > 2.0 and p5d > 1:
        F(f"Heavy volume ({vol_ratio:.1f}x) on up-move — institutional buying", 3, 3, "Volume", 1)
    elif vol_ratio > 1.5 and p5d > 0:
        F(f"Above-avg volume ({vol_ratio:.1f}x) confirming rally", 2, 3, "Volume", 1)
    elif vol_ratio > 2.0 and p5d < -1:
        F(f"Heavy volume ({vol_ratio:.1f}x) on down-move — institutional selling", -3, 3, "Volume", -1)
    elif vol_ratio > 1.5 and p5d < 0:
        F(f"Above-avg volume ({vol_ratio:.1f}x) confirming decline", -2, 3, "Volume", -1)

    if obv_rising is not None:
        if obv_rising and p5d >= 0:
            F("OBV rising — smart money accumulating", 2, 2, "Volume", 1)
        elif not obv_rising and p5d <= 0:
            F("OBV falling — smart money distributing", -2, 2, "Volume", -1)
        elif obv_rising and p5d < 0:
            F("OBV up vs falling price — hidden accumulation signal", 1, 2, "Volume", 1)

    if mfi is not None:
        if mfi < 20:
            F(f"MFI oversold ({mfi:.0f}) — money flowing in at lows", 2, 2, "Volume", 1)
        elif mfi > 80:
            F(f"MFI overbought ({mfi:.0f}) — money outflow at highs", -2, 2, "Volume", -1)
    if cmf is not None:
        if cmf > 0.15:
            F(f"CMF positive ({cmf:.2f}) — sustained accumulation", 1, 1, "Volume", 1)
        elif cmf < -0.15:
            F(f"CMF negative ({cmf:.2f}) — sustained distribution", -1, 1, "Volume", -1)

    if cci is not None:
        if cci < -150:
            F(f"CCI deeply oversold ({cci:.0f})", 2, 2, "Momentum", 1)
        elif cci > 150:
            F(f"CCI overbought ({cci:.0f})", -2, 2, "Momentum", -1)

    if w52_pos >= 85 and p20d > 0:
        F(f"Near 52W high ({w52_pos:.0f}th pct) with positive momentum", 3, 3, "Momentum", 1)
    elif w52_pos <= 15:
        F(f"Near 52W low ({w52_pos:.0f}th pct) — maximum pessimism", 3, 3, "Momentum", 1)
    elif w52_pos >= 85 and p20d < 0:
        F(f"Near 52W high but losing momentum — potential top", -2, 3, "Momentum", -1)

    running_score = sum(f["pts"] for f in factors)
    if regime == "TREND":
        if running_score > 0:
            F("TRENDING regime — trend-following has highest win rate now", 3, 3, "Regime", 1)
        else:
            F("TRENDING regime — confirms current downtrend direction", -3, 3, "Regime", -1)
    elif regime == "RANGE":
        F("RANGE regime — mean reversion valid, extremes favour reversal", 1, 3, "Regime", 0)
    else:
        F("VOLATILE regime — mixed signals, expect whipsaws", -1, 3, "Regime", 0)

    total_pts = sum(f["pts"] for f in factors)
    total_max = sum(f["max"] for f in factors)
    pct = total_pts / total_max * 100 if total_max > 0 else 0.0

    bull_n = sum(1 for f in factors if f["dir"] > 0)
    bear_n = sum(1 for f in factors if f["dir"] < 0)

    # Count-based ratio boost: when signal count is heavily skewed,
    # nudge pct toward the dominant side to break WAIT deadlocks.
    total_dir = bull_n + bear_n
    if total_dir > 0:
        ratio = bull_n / total_dir          # 0..1
        if ratio >= 0.70:                   # ≥70% bullish signals
            pct += (ratio - 0.5) * 30       # up to +15 bonus
        elif ratio <= 0.30:                 # ≥70% bearish signals
            pct -= (0.5 - ratio) * 30       # up to -15 penalty

    if pct >= 35:
        verdict = "BUY";       confidence = min(95, int(40 + pct * 0.6))
    elif pct >= 15:
        verdict = "LEAN BULL"; confidence = min(70, int(30 + pct * 0.7))
    elif pct <= -35:
        verdict = "SELL";      confidence = min(95, int(40 + abs(pct) * 0.6))
    elif pct <= -15:
        verdict = "LEAN BEAR"; confidence = min(70, int(30 + abs(pct) * 0.7))
    else:
        verdict = "WAIT";      confidence = min(80, 40 + min(bull_n, bear_n) * 5)

    is_actionable = verdict in ("BUY", "SELL")
    is_lean       = verdict in ("LEAN BULL", "LEAN BEAR")
    is_bullish    = verdict in ("BUY", "LEAN BULL")

    entry  = cp

    # ── STOP + TARGETS: delegate to shared _levels module ─────────────────
    try:
        from _levels import compute_structural_levels as _csl
        _lv = _csl(df, cp, is_bullish)
        stop         = _lv["stop"]
        t1           = _lv["t1"];  t2 = _lv["t2"];  t3 = _lv["t3"]
        risk_pct     = _lv["risk_pct"]
        rr1          = _lv["rr1"]; rr2 = _lv["rr2"]
        R            = _lv["R"]
        entry_quality = _lv.get("entry_quality", "")
        eq_col        = _lv.get("eq_col", "")
    except Exception:
        # Fallback: simple ATR-based levels
        R        = atr * 1.5
        stop     = round(cp - R, 2) if is_bullish else round(cp + R, 2)
        t1       = round(cp + 1.618 * R, 2) if is_bullish else round(cp - 1.618 * R, 2)
        t2       = round(cp + 2.618 * R, 2) if is_bullish else round(cp - 2.618 * R, 2)
        t3       = round(cp + 4.236 * R, 2) if is_bullish else round(cp - 4.236 * R, 2)
        risk_pct = round(R / cp * 100, 1) if cp > 0 else 2.0
        rr1      = 1.6; rr2 = 2.6
        entry_quality = ""; eq_col = ""

    return {
        "verdict": verdict, "confidence": confidence,
        "is_actionable": is_actionable, "is_lean": is_lean, "is_bullish": is_bullish,
        "pct": round(pct, 1), "total_pts": total_pts, "total_max": total_max,
        "factors": factors, "bull_n": bull_n, "bear_n": bear_n,
        "entry": entry, "stop": stop, "t1": t1, "t2": t2, "t3": t3,
        "risk_pct": round(risk_pct, 1), "rr1": round(rr1, 1), "rr2": round(rr2, 1),
        "rsi": round(rsi, 1), "adx": round(adx, 1),
        "sk": round(sk, 1), "macd_h": round(macd_h, 4),
        "bb_pct": round(bb_pct * 100, 0), "vol_ratio": round(vol_ratio, 2),
        "atr_pct": round(atr_pct, 2), "atr_abs": round(atr, 4),
        "regime": regime,
        "w52_pos": round(w52_pos, 1), "p5d": round(p5d, 2),
        "p20d": round(p20d, 2), "p60d": round(p60d, 2),
        "e20": round(e20, 2), "e50": round(e50, 2), "e200": round(e200, 2),
        "w52h": round(w52h, 2), "w52l": round(w52l, 2), "cp": round(cp, 2),
        "entry_quality": entry_quality, "eq_col": eq_col,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED PROBABILITY ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _probability_engine(df, d):
    """
    Multi-layer probability model:
      Layer 1 - Historical base rate at each horizon (unconditional)
      Layer 2 - Historical ANALOG setups (same RSI zone + EMA side + MACD dir)
      Layer 3 - Regime-conditional win rates
      Layer 4 - Score-based Bayesian adjustment
      Layer 5 - Momentum persistence (short-term trend continuation bias)
      Layer 6 - Volatility dampening (high ATR -> pull toward 50%)
      Layer 7 - Confidence interval from analog spread + ATR scaling
    Returns rich dict per horizon: prob_up, n_analogs, analog_win_rate,
      avg_ret, median_ret, p10, p25, p75, p90, ci_lo, ci_hi,
      bull_target, base_target, bear_target,
      bull_probability, base_probability, bear_probability,
      bull_ret, base_ret, bear_ret,
      regime_win_rate, n_regime_analogs,
      key_driver, driver_contribution,
      when_right_avg, when_wrong_avg, ev
    """
    close  = df["Close"].astype(float)
    high   = df["High"].astype(float)
    low    = df["Low"].astype(float)
    n      = len(close)
    cp     = d["cp"]
    atr_pct  = d["atr_pct"]
    regime   = d["regime"]
    rsi_now  = d["rsi"]
    pct_score = d["pct"]
    is_bullish = d["is_bullish"]
    p5d      = d["p5d"]

    # Current indicator states (categorical)
    above_e20  = cp > d["e20"]
    macd_bull  = d["macd_h"] > 0
    rsi_zone   = ("oversold" if rsi_now < 35 else
                  "overbought" if rsi_now > 65 else "neutral")

    results = {}

    for days in [5, 10, 20]:
        min_needed = days + 5
        if n < min_needed:
            results[days] = _fallback_horizon(days, d)
            continue

        # ── Layer 1: Unconditional base rate ────────────────────────────
        window    = min(150, n - days - 1)
        all_rets  = []
        for i in range(window):
            p0 = float(close.iloc[-(days + 1 + i)])
            pN = float(close.iloc[-(1 + i)])
            all_rets.append(_pct(pN, p0))

        uncond_win_rate = sum(1 for r in all_rets if r > 0) / len(all_rets) if all_rets else 0.5
        uncond_avg      = float(np.mean(all_rets)) if all_rets else 0.0

        # ── Layer 2: Analog setups ───────────────────────────────────────
        # Match: same EMA20 side, same RSI zone, same MACD direction
        analog_rets     = []
        regime_rets     = []
        strong_rets     = []  # analogs where score also in same direction

        for i in range(min(250, n - days - 1)):
            bar_idx = -(days + 1 + i)
            if abs(bar_idx) >= n:
                break

            # Reconstruct past state
            past_close   = float(close.iloc[bar_idx])
            past_e20_raw = _fv(df, "EMA_20", bars_back=days + i)
            past_rsi_raw = _fv(df, "RSI_14", bars_back=days + i)
            past_macd_h  = _fv(df, "MACDh_12_26_9", bars_back=days + i)
            past_regime  = None
            if "REGIME" in df.columns:
                reg_s = df["REGIME"].dropna()
                reg_idx = -(days + 1 + i)
                if abs(reg_idx) < len(reg_s):
                    past_regime = reg_s.iloc[reg_idx]

            past_above_e20 = (past_close > past_e20_raw) if past_e20_raw else above_e20
            past_rsi_zone  = ("oversold"  if (past_rsi_raw or 50) < 35 else
                              "overbought" if (past_rsi_raw or 50) > 65 else "neutral")
            past_macd_bull = (past_macd_h or 0) > 0

            # Forward return FROM that analog point
            p0 = float(close.iloc[bar_idx])
            pN_idx = bar_idx + days
            if pN_idx >= 0:
                pN_idx = -1
            pN = float(close.iloc[pN_idx]) if abs(pN_idx) <= n else p0
            fwd_ret = _pct(pN, p0)

            # Regime analog
            if past_regime == regime:
                regime_rets.append(fwd_ret)

            # Full analog: same EMA side + same RSI zone
            same_ema  = past_above_e20 == above_e20
            same_rsi  = past_rsi_zone  == rsi_zone
            same_macd = past_macd_bull == macd_bull

            if same_ema and same_rsi:
                analog_rets.append(fwd_ret)
                if same_macd:
                    strong_rets.append(fwd_ret)

        # Choose best dataset (strong > analog > regime > unconditional)
        if len(strong_rets) >= 10:
            best_rets = strong_rets
            dataset_label = f"{len(strong_rets)} strong analogs (EMA+RSI+MACD match)"
        elif len(analog_rets) >= 8:
            best_rets = analog_rets
            dataset_label = f"{len(analog_rets)} analogs (EMA+RSI zone match)"
        elif len(regime_rets) >= 8:
            best_rets = regime_rets
            dataset_label = f"{len(regime_rets)} regime-matched periods"
        else:
            best_rets = all_rets
            dataset_label = f"{len(all_rets)} unconditional historical periods"

        m = len(best_rets)
        if m == 0:
            results[days] = _fallback_horizon(days, d)
            continue

        s_rets     = sorted(best_rets)
        wins       = sum(1 for r in best_rets if r > 0)
        analog_wr  = wins / m
        avg_ret    = float(np.mean(best_rets))
        median_ret = float(np.median(best_rets))
        p10        = _quartile(s_rets, 0.10)
        p25        = _quartile(s_rets, 0.25)
        p75        = _quartile(s_rets, 0.75)
        p90        = _quartile(s_rets, 0.90)

        # ── Layer 3: Score-based Bayesian update ────────────────────────
        # Shift analog win rate toward score direction
        # Each 10% of max score = ~2.5% adjustment
        score_adj  = float(np.clip(pct_score / 100 * 0.20, -0.18, 0.18))

        # ── Layer 4: Momentum bias ───────────────────────────────────────
        mom_adj = 0.0
        if abs(p5d) > 2:
            mom_adj = float(np.clip(p5d / 100 * 0.15, -0.06, 0.06))

        # ── Layer 5: Regime multiplier ───────────────────────────────────
        reg_adj = 0.0
        if regime == "TREND":
            reg_adj = 0.04 if is_bullish else -0.04
        elif regime == "VOLATILE":
            # In volatile regimes dampen toward 50% — less predictable
            analog_wr = analog_wr * 0.7 + 0.5 * 0.3

        # ── Layer 6: Volatility dampening ────────────────────────────────
        raw_prob = analog_wr + score_adj + mom_adj + reg_adj
        if atr_pct > 4:
            damp = float(np.clip((atr_pct - 4) / 10, 0, 0.5)) * 0.20
            raw_prob = raw_prob * (1 - damp) + 0.5 * damp

        prob_up = float(np.clip(raw_prob, 0.05, 0.95))

        # ── Layer 7: Confidence interval ────────────────────────────────
        # Use interquartile range from analogs blended with ATR projection
        daily_vol   = atr_pct / 1.414
        atr_proj    = daily_vol * (days ** 0.5)
        spread_half = max(abs(p75 - p25) / 2, atr_proj * 0.8)
        ci_lo  = round(cp * (1 + (avg_ret - spread_half * 1.28) / 100), 2)
        ci_hi  = round(cp * (1 + (avg_ret + spread_half * 1.28) / 100), 2)

        # ── Scenarios ────────────────────────────────────────────────────
        # Bull case  = 75th–90th percentile of analog returns
        # Base case  = median of analog returns
        # Bear case  = 10th–25th percentile
        bull_ret  = round((p75 + p90) / 2, 2)
        base_ret  = round(median_ret, 2)
        bear_ret  = round((p10 + p25) / 2, 2)

        bull_target = round(cp * (1 + bull_ret / 100), 2)
        base_target = round(cp * (1 + base_ret / 100), 2)
        bear_target = round(cp * (1 + bear_ret / 100), 2)

        # Assign scenario probabilities
        # Bull scenario = fraction of analogs above p75
        bull_p = sum(1 for r in best_rets if r >= p75) / m
        bear_p = sum(1 for r in best_rets if r <= p25) / m
        base_p = 1 - bull_p - bear_p

        # Expected value (from entry, accounting for prob distribution)
        when_right_avg = float(np.mean([r for r in best_rets if r > 0])) if any(r > 0 for r in best_rets) else 0.0
        when_wrong_avg = float(np.mean([r for r in best_rets if r <= 0])) if any(r <= 0 for r in best_rets) else 0.0
        ev = round(prob_up * when_right_avg + (1 - prob_up) * when_wrong_avg, 2)

        # Regime-specific win rate
        regime_wr = None
        if len(regime_rets) >= 5:
            regime_wr = round(sum(1 for r in regime_rets if r > 0) / len(regime_rets) * 100, 1)

        # Key driver (which signal group contributes most to bullish/bearish lean)
        cat_scores = {}
        for f in d["factors"]:
            cat = f["cat"]
            cat_scores[cat] = cat_scores.get(cat, 0) + f["pts"]
        if cat_scores:
            key_driver = max(cat_scores, key=lambda k: abs(cat_scores[k]))
            driver_pts = cat_scores[key_driver]
        else:
            key_driver = "N/A"
            driver_pts = 0

        results[days] = {
            "prob_up":           round(prob_up * 100, 1),
            "n_analogs":         m,
            "dataset_label":     dataset_label,
            "analog_win_rate":   round(analog_wr * 100, 1),
            "avg_ret":           round(avg_ret, 2),
            "median_ret":        round(median_ret, 2),
            "p10":               round(p10, 2), "p25": round(p25, 2),
            "p75":               round(p75, 2), "p90": round(p90, 2),
            "ci_lo":             ci_lo, "ci_hi": ci_hi,
            "bull_ret":          bull_ret, "base_ret": base_ret, "bear_ret": bear_ret,
            "bull_target":       bull_target, "base_target": base_target, "bear_target": bear_target,
            "bull_prob":         round(bull_p * 100, 0),
            "base_prob":         round(base_p * 100, 0),
            "bear_prob":         round(bear_p * 100, 0),
            "when_right_avg":    round(when_right_avg, 2),
            "when_wrong_avg":    round(when_wrong_avg, 2),
            "ev":                ev,
            "regime_win_rate":   regime_wr,
            "key_driver":        key_driver,
            "driver_pts":        driver_pts,
            "score_adj":         round(score_adj * 100, 1),
            "atr_proj":          round(atr_proj, 1),
        }

    return results


def _fallback_horizon(days, d):
    atr_pct = d["atr_pct"]
    cp      = d["cp"]
    pct     = d["pct"]
    prob_up = float(np.clip(0.5 + pct / 100 * 0.3, 0.1, 0.9))
    daily_vol = atr_pct / 1.414
    mv = daily_vol * (days ** 0.5) * (1 if prob_up > 0.5 else -1)
    return {
        "prob_up": round(prob_up * 100, 1),
        "n_analogs": 0, "dataset_label": "insufficient history",
        "analog_win_rate": round(prob_up * 100, 1),
        "avg_ret": round(mv, 2), "median_ret": round(mv, 2),
        "p10": round(-atr_pct * 2, 2), "p25": round(-atr_pct, 2),
        "p75": round(atr_pct, 2),      "p90": round(atr_pct * 2, 2),
        "ci_lo": round(cp * (1 - atr_pct * 0.03), 2),
        "ci_hi": round(cp * (1 + atr_pct * 0.03), 2),
        "bull_ret": round(atr_pct * 1.5, 2),
        "base_ret": round(mv, 2),
        "bear_ret": round(-atr_pct * 1.5, 2),
        "bull_target": round(cp * (1 + atr_pct * 0.015), 2),
        "base_target": round(cp * (1 + mv / 100), 2),
        "bear_target": round(cp * (1 - atr_pct * 0.015), 2),
        "bull_prob": 25.0, "base_prob": 50.0, "bear_prob": 25.0,
        "when_right_avg": round(abs(mv) * 1.2, 2),
        "when_wrong_avg": round(-abs(mv) * 0.8, 2),
        "ev": round(mv * 0.5, 2),
        "regime_win_rate": None,
        "key_driver": "N/A", "driver_pts": 0,
        "score_adj": 0.0, "atr_proj": round(daily_vol * (days ** 0.5), 1),
    }



# ─────────────────────────────────────────────────────────────────────────────
# CACHED EXTERNAL SIGNAL COLLECTION  (survives page refresh for 5 min)
# ─────────────────────────────────────────────────────────────────────────────
_EXT_TABS = [
    ("Price Action",   "price_action_tab",  "get_pa_signal"),
    ("Volume Profile", "volume_profile_tab", "get_vp_signal"),
    ("Chart Patterns", "patterns_tab",       "get_patterns_signal"),
    ("Smart Money",    "smc_tab",            "get_smc_signal"),
    ("AI Analysis",    "gemini_tab",         "get_ai_signal"),
]

@st.cache_data(ttl=300, show_spinner=False)
def _collect_ext_signals(_df_hash: str, _cp: float, df_json: str):
    """Compute external tab signals once; cached 5 min by data fingerprint."""
    import io
    _df = pd.read_json(io.StringIO(df_json))
    out = {}
    for _name, _mod, _fn in _EXT_TABS:
        try:
            _module = __import__(_mod)
            _sig = getattr(_module, _fn)(_df, _cp)
            # Convert to plain dict (avoid unpicklable objects)
            if _sig:
                out[_name] = {k: (v if not isinstance(v, (pd.Series, pd.DataFrame, np.ndarray)) else None)
                              for k, v in _sig.items()}
            else:
                out[_name] = None
        except Exception:
            out[_name] = None
    return out


# ─────────────────────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_decision_tab(df, symbol_input, stock_name, current_price):
    # Inject Inter font
    # Font is set globally in app.py

    d    = _score_engine(df, current_price)

    V       = d["verdict"]
    cp      = current_price
    is_bull = d["is_bullish"]

    # ── Collect scores from ALL tabs for the master scoring system ──────────
    # Each entry: (name, icon, score 0-100, label, color, reasons_list, is_active)
    # is_active: True if module returned real analysis, False if no signal/unavailable
    _tab_scores = []

    # 1. Technical Indicators (from _score_engine — ALWAYS active, full bull+bear)
    _ti_score = max(0, min(100, int(50 + d["pct"] * 0.5)))
    _ti_lbl = "Bullish" if d["pct"] > 15 else ("Bearish" if d["pct"] < -15 else "Neutral")
    _ti_col = BULL if d["pct"] > 15 else (BEAR if d["pct"] < -15 else "#FFC107")
    _ti_reasons = [f["name"] for f in sorted(d["factors"], key=lambda x: abs(x["pts"]), reverse=True)[:3]]
    _tab_scores.append(("Technical Indicators", "&#128200;", _ti_score, _ti_lbl, _ti_col, _ti_reasons, True))

    # 2-6. External tab signals — @st.cache_data (survives refresh, 5 min TTL)
    _ext_icons = {
        "Price Action": "&#128201;", "Volume Profile": "&#128202;",
        "Chart Patterns": "&#128300;", "Smart Money": "&#128176;",
        "AI Analysis": "&#129302;",
    }
    _tail = df["Close"].tail(5).tolist()
    _df_hash = f"{symbol_input}_{round(cp,2)}_{len(df)}_{[round(float(x),4) for x in _tail]}"
    _cached_sigs = _collect_ext_signals(_df_hash, cp, df.to_json())

    for _name, _icon in _ext_icons.items():
        _sig = _cached_sigs.get(_name)
        if _sig:
            _s_conf = min(95, _sig["conf"])
            _s_lbl = _sig.get("verdict_text", "▲ BUY").replace("▲ ", "")
            _s_reasons = _sig.get("reasons", [])[:2]
            _s_col = BULL
            # Active + bullish signal
            _tab_scores.append((_name, _icon, _s_conf, _s_lbl, _s_col, _s_reasons, True))
        else:
            # INACTIVE — no signal found. NOT bearish, just absent.
            _tab_scores.append((_name, _icon, 50, "No Signal", "#555", ["No setup detected — neutral"], False))

    # ── Categorize modules ──────────────────────────────────────────────────
    _active_tabs  = [s for s in _tab_scores if s[6]]           # modules with real data
    _active_count = len(_active_tabs)
    _bull_tabs    = sum(1 for s in _tab_scores if s[6] and s[2] >= 55)  # active + bullish
    _bear_real    = sum(1 for s in _tab_scores if s[6] and s[2] < 40)   # active + bearish (only TI can be this)
    _inactive     = sum(1 for s in _tab_scores if not s[6])             # no signal
    _total_tabs   = len(_tab_scores)

    # ── Master Score — ONLY count active modules ────────────────────────────
    # Inactive modules don't vote. They're absent, not bearish.
    _weights = []
    for (_n, _ic, _sc, _lb, _cl, _rs, _act) in _tab_scores:
        if _act:
            _w = 2.0 if _n == "Technical Indicators" else 1.0
            _weights.append((_sc, _w))
    if _weights:
        _master_score = int(sum(s * w for s, w in _weights) / sum(w for _, w in _weights))
    else:
        _master_score = _ti_score  # fallback to TI only
    _master_score = max(0, min(100, _master_score))

    # ── Final Verdict Logic ─────────────────────────────────────────────────
    # This is the most important logic in the entire app. Rules:
    #
    # BUY HIGH:     Engine=BUY + MasterScore>=60 + >=2 active bull + TI bullish + 0 active bearish
    # BUY MOD:      Engine=BUY + MasterScore>=55 + >=1 active bull + TI not bearish + 0 active bearish
    # SELL HIGH:    Engine=SELL + MasterScore<35 + TI bearish + 0 active bull
    # SELL MOD:     Engine=SELL/LEAN BEAR + MasterScore<42 + TI bearish
    # WAIT:         Everything else — the only safe default
    #
    # KEY PRINCIPLES:
    # - Inactive modules NEVER count for or against
    # - Only ACTIVE signals can confirm or deny
    # - TI is the backbone (always active) — must agree with verdict
    # - External tabs provide CONFIRMATION, not contradiction

    _ti_bullish = _ti_score >= 55
    _ti_bearish = _ti_score < 40
    _ti_neutral = not _ti_bullish and not _ti_bearish

    if (V == "BUY" and _master_score >= 60
            and _bull_tabs >= 2 and _bear_real == 0 and _ti_bullish):
        display_v = "BUY"
        vc = BULL
        dir_icon = "&#9650;"
        _verdict_confidence = "HIGH"
        vsub = f"{_bull_tabs} active modules confirm — Strong bullish confluence"

    elif (V == "BUY" and _master_score >= 55
            and _bull_tabs >= 1 and _bear_real == 0 and not _ti_bearish):
        display_v = "BUY"
        vc = BULL
        dir_icon = "&#9650;"
        _verdict_confidence = "MODERATE"
        vsub = f"{_bull_tabs} active module{'s' if _bull_tabs > 1 else ''} bullish — Entry with caution"

    elif (V == "SELL" and _master_score < 35
            and _ti_bearish and _bull_tabs == 0):
        display_v = "SELL"
        vc = BEAR
        dir_icon = "&#9660;"
        _verdict_confidence = "HIGH"
        vsub = f"Technical indicators strongly bearish — No bullish confirmation anywhere"

    elif (V in ("SELL", "LEAN BEAR") and _master_score < 42
            and _ti_bearish):
        display_v = "SELL"
        vc = BEAR
        dir_icon = "&#9660;"
        _verdict_confidence = "MODERATE"
        vsub = f"Bearish bias — TI bearish, {_bull_tabs} bull confirmations"

    else:
        display_v = "WAIT"
        vc = "#FFC107"
        dir_icon = "&#9670;"
        if V in ("BUY", "LEAN BULL") and _ti_bullish and _bull_tabs == 0:
            _verdict_confidence = "LOW"
            vsub = f"TI bullish but no other module confirms — wait for confirmation"
        elif V in ("BUY", "LEAN BULL") and _ti_neutral:
            _verdict_confidence = "LOW"
            vsub = f"Leaning bullish but TI is neutral — signals too weak"
        elif V in ("SELL", "LEAN BEAR") and _bull_tabs > 0:
            _verdict_confidence = "LOW"
            vsub = f"Leaning bearish but {_bull_tabs} module{'s' if _bull_tabs > 1 else ''} still bullish — conflicting"
        elif _ti_neutral and _bull_tabs == 0:
            _verdict_confidence = "NEUTRAL"
            vsub = f"No strong signals in any direction — sit tight"
        else:
            _verdict_confidence = "NEUTRAL"
            vsub = f"Mixed signals ({_bull_tabs} bull, {_bear_real} bear, {_inactive} inactive) — no clear edge"

    # ── Build "WHY" reasons ─────────────────────────────────────────────────
    _why_reasons = []
    # Top factors from _score_engine (strongest signals)
    _sorted_factors = sorted(d["factors"], key=lambda x: abs(x["pts"]), reverse=True)
    for _f in _sorted_factors[:3]:
        _dir_emoji = "&#9989;" if _f["dir"] > 0 else ("&#10060;" if _f["dir"] < 0 else "&#11036;")
        _why_reasons.append((_dir_emoji, _f["name"], _f["cat"]))

    # Add reasons from active tab signals
    for _n, _ic, _sc, _lb, _cl, _rs, _act in _tab_scores[1:]:  # skip TI (already covered)
        if _act and _sc >= 55 and _rs:
            _why_reasons.append(("&#9989;", f"{_n}: {_rs[0]}", _n))
        elif _act and _sc < 35 and _rs:
            _why_reasons.append(("&#10060;", f"{_n}: {_rs[0]}", _n))
    _why_reasons = _why_reasons[:6]  # cap at 6

    # Signal strength
    total_sigs   = d["bull_n"] + d["bear_n"]
    sig_strength = int(d["bull_n"] / max(1, total_sigs) * 100)
    conf_c       = BULL if sig_strength >= 60 else NEUT if sig_strength >= 40 else BEAR

    # Master score color
    _ms_col = BULL if _master_score >= 60 else ("#FFC107" if _master_score >= 40 else BEAR)

    # Verdict confidence color
    _vc_conf_col = BULL if _verdict_confidence == "HIGH" else ("#FFC107" if _verdict_confidence in ("MODERATE", "LOW") else "#555")

    # ══════════════════════════════════════════════════════════════════════════
    #  1. HERO CARD — Master scoring system from all tabs
    # ══════════════════════════════════════════════════════════════════════════

    # Tooltip + Hero CSS
    st.markdown("""<style>
    .dec-tip-wrap { position:relative; cursor:help; display:inline-flex; align-items:center; justify-content:center; }
    .dec-tip-icon {
        display:inline-flex;align-items:center;justify-content:center;
        width:13px;height:13px;border-radius:50%;background:rgba(255,255,255,0.05);
        border:1px solid #333;font-size:0.45rem;color:#666;font-weight:700;
        margin-left:0.3rem;
    }
    .dec-tip-box {
        visibility:hidden;opacity:0;position:absolute;bottom:140%;left:50%;
        transform:translateX(-50%);background:#222;color:#ccc;border:1px solid #333;
        border-radius:6px;padding:0.4rem 0.6rem;font-size:0.58rem;font-weight:500;
        line-height:1.45;white-space:normal;width:190px;text-align:left;z-index:100;
        pointer-events:none;transition:opacity 0.15s ease;
        box-shadow:0 4px 14px rgba(0,0,0,0.5);text-transform:none;letter-spacing:0;
    }
    .dec-tip-box::after {
        content:'';position:absolute;top:100%;left:50%;transform:translateX(-50%);
        border:5px solid transparent;border-top-color:#333;
    }
    .dec-tip-wrap:hover .dec-tip-box { visibility:visible; opacity:1; }
    </style>""", unsafe_allow_html=True)

    insight_toggle(
        "signal_strength",
        "How does the Master Score work?",
        "<p style='margin:0 0 0.6rem 0;'>The <strong>Master Score</strong> combines results from "
        "<strong>6 independent analysis modules</strong> — each one looks at the market differently. "
        "Technical Indicators gets <strong>2x weight</strong> because it provides full bullish + bearish analysis. "
        "The final score is a weighted average (0–100).</p>"
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin:0.6rem 0;'>"
        "<div style='background:rgba(33,150,243,0.08);border:1px solid rgba(33,150,243,0.2);border-radius:8px;padding:0.5rem 0.7rem;'>"
        "<div style='font-weight:800;color:#90caf9;font-size:0.78rem;'>&#128200; Technical Indicators</div>"
        "<div style='font-size:0.68rem;color:#bbb;line-height:1.5;margin-top:0.15rem;'>"
        "EMA trends, RSI, MACD, Stochastic, Bollinger Bands, ADX, Volume — <strong>2x weight</strong></div></div>"
        "<div style='background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);border-radius:8px;padding:0.5rem 0.7rem;'>"
        "<div style='font-weight:800;color:#81c784;font-size:0.78rem;'>&#128201; Price Action</div>"
        "<div style='font-size:0.68rem;color:#bbb;line-height:1.5;margin-top:0.15rem;'>"
        "Support/resistance, trend structure, swing highs/lows</div></div>"
        "<div style='background:rgba(156,39,176,0.08);border:1px solid rgba(156,39,176,0.2);border-radius:8px;padding:0.5rem 0.7rem;'>"
        "<div style='font-weight:800;color:#ce93d8;font-size:0.78rem;'>&#128202; Volume Profile</div>"
        "<div style='font-size:0.68rem;color:#bbb;line-height:1.5;margin-top:0.15rem;'>"
        "Where most trading happened — POC, value area, VWAP</div></div>"
        "<div style='background:rgba(255,152,0,0.08);border:1px solid rgba(255,152,0,0.2);border-radius:8px;padding:0.5rem 0.7rem;'>"
        "<div style='font-weight:800;color:#ffb74d;font-size:0.78rem;'>&#128300; Chart Patterns</div>"
        "<div style='font-size:0.68rem;color:#bbb;line-height:1.5;margin-top:0.15rem;'>"
        "Candlestick and chart patterns like engulfing, head &amp; shoulders</div></div>"
        "<div style='background:rgba(0,188,212,0.08);border:1px solid rgba(0,188,212,0.2);border-radius:8px;padding:0.5rem 0.7rem;'>"
        "<div style='font-weight:800;color:#80deea;font-size:0.78rem;'>&#128176; Smart Money</div>"
        "<div style='font-size:0.68rem;color:#bbb;line-height:1.5;margin-top:0.15rem;'>"
        "Order blocks, liquidity zones, institutional trading patterns</div></div>"
        "<div style='background:rgba(244,67,54,0.08);border:1px solid rgba(244,67,54,0.2);border-radius:8px;padding:0.5rem 0.7rem;'>"
        "<div style='font-weight:800;color:#ef9a9a;font-size:0.78rem;'>&#129302; AI Analysis</div>"
        "<div style='font-size:0.68rem;color:#bbb;line-height:1.5;margin-top:0.15rem;'>"
        "AI-powered deep analysis of all conditions combined</div></div>"
        "</div>"
        "<p style='font-size:0.72rem;color:#aaa;margin-top:0.5rem;'>"
        "<strong>The decision:</strong> "
        "BUY = Master Score 55+ AND the engine confirms AND 3+ modules agree. "
        "SELL = Score below 40 AND bearish engine AND 3+ modules weak. "
        "WAIT = Not enough agreement or mixed signals. "
        "The &ldquo;Why&rdquo; section shows exactly which signals drove the decision.</p>"
    )

    # ── Build tab score rows HTML ───────────────────────────────────────────
    _tab_tips = {
        "Technical Indicators": "EMA, MACD, RSI, Stochastic, Bollinger, ADX, Volume, OBV — weighted 2x in master score",
        "Price Action": "Support/resistance levels, trend direction, swing structure — buy setups only",
        "Volume Profile": "POC, value area, VWAP positioning — identifies where real demand sits",
        "Chart Patterns": "Candlestick + chart patterns in last 10 sessions — net bullish/bearish count",
        "Smart Money": "Order blocks, liquidity sweeps, CHoCH/BOS — institutional flow detection",
        "AI Analysis": "ML ensemble + historical analogy + 12-indicator AI scoring — highest bar for confirmation",
    }
    _tab_rows_html = ""
    for _tname, _ticon, _tscore, _tlbl, _tcol, _trsns, _tact in _tab_scores:
        _bar_col = BULL if _tscore >= 60 else ("#FFC107" if _tscore >= 40 else BEAR)
        _ttip = _tab_tips.get(_tname, "")
        _tip_html = (
            f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
            f"<span class='dec-tip-box'>{_ttip}</span></span>"
        ) if _ttip else ""
        # Status dot
        _dot_col = BULL if _tscore >= 55 else ("#FFC107" if _tscore >= 40 else BEAR if _tscore < 35 else "#555")
        _tab_rows_html += (
            f"<div style='display:flex;align-items:center;gap:0.7rem;padding:0.65rem 0;"
            f"border-bottom:1px solid #1e1e1e;'>"
            f"<div style='font-size:0.95rem;width:26px;text-align:center;'>{_ticon}</div>"
            f"<div style='flex:1;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.35rem;'>"
            f"<span style='font-size:0.72rem;font-weight:700;color:#e0e0e0;display:flex;align-items:center;'>"
            f"{_tname}{_tip_html}</span>"
            f"<span style='font-size:0.56rem;font-weight:700;color:{_tcol};padding:0.15rem 0.5rem;"
            f"border-radius:4px;background:{_tcol}14;border:1px solid {_tcol}22;'>{_tlbl}</span></div>"
            f"<div style='background:#1a1a1a;border-radius:999px;height:5px;overflow:hidden;'>"
            f"<div style='width:{_tscore}%;height:100%;border-radius:999px;"
            f"background:linear-gradient(90deg,{_bar_col}cc,{_bar_col});"
            f"box-shadow:0 0 6px {_bar_col}44;'></div></div>"
            f"</div>"
            f"<div style='font-size:1.05rem;font-weight:900;color:{_bar_col};min-width:36px;"
            f"text-align:right;font-variant-numeric:tabular-nums;'>{_tscore}</div>"
            f"</div>"
        )

    # ── Build "Why" reasons HTML ────────────────────────────────────────────
    _why_html = ""
    for _emoji, _reason, _cat in _why_reasons:
        _why_html += (
            f"<div style='display:flex;align-items:flex-start;gap:0.55rem;padding:0.5rem 0.7rem;"
            f"background:#141414;border:1px solid #222;border-radius:8px;margin-bottom:0.4rem;'>"
            f"<div style='font-size:0.75rem;margin-top:0.05rem;flex-shrink:0;'>{_emoji}</div>"
            f"<div style='flex:1;'>"
            f"<div style='font-size:0.68rem;color:#d0d0d0;line-height:1.5;font-weight:500;'>{_reason}</div>"
            f"<div style='font-size:0.5rem;color:#444;margin-top:0.15rem;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.5px;'>{_cat}</div>"
            f"</div></div>"
        )

    # RGB of vc for gradient
    _vc_rgb = ','.join(str(int(vc[i:i+2], 16)) for i in (1, 3, 5))

    # ── Score ring SVG ──────────────────────────────────────────────────────
    _ring_pct = max(0, min(100, _master_score))
    _ring_dash = round(251.2 * _ring_pct / 100, 1)  # circumference = 2*pi*40 ≈ 251.2
    _ring_svg = (
        f"<svg width='110' height='110' viewBox='0 0 110 110' style='display:block;'>"
        f"<circle cx='55' cy='55' r='40' fill='none' stroke='#1a1a1a' stroke-width='7'/>"
        f"<circle cx='55' cy='55' r='40' fill='none' stroke='{_ms_col}' stroke-width='7' "
        f"stroke-linecap='round' stroke-dasharray='{_ring_dash} 251.2' "
        f"transform='rotate(-90 55 55)' style='filter:drop-shadow(0 0 6px {_ms_col}55);'/>"
        f"<text x='55' y='50' text-anchor='middle' fill='{_ms_col}' "
        f"font-size='24' font-weight='900' font-family='Inter,sans-serif'>{_master_score}</text>"
        f"<text x='55' y='68' text-anchor='middle' fill='#555' "
        f"font-size='9' font-weight='700' font-family='Inter,sans-serif'>SCORE</text>"
        f"</svg>"
    )

    # ── Agreement gauge ─────────────────────────────────────────────────────
    _agree_pct = int(_bull_tabs / max(1, _active_count) * 100)

    st.markdown(
        f"<div style='background:#1b1b1b;border:1px solid #272727;"
        f"border-radius:16px;overflow:hidden;margin-bottom:1.4rem;"
        f"box-shadow:0 4px 30px rgba(0,0,0,0.4);'>"

        # ── TOP GLOW BAR (thin accent) ──────────────────────────────────────
        f"<div style='height:3px;background:linear-gradient(90deg,{vc}00,{vc},{vc}00);'></div>"

        # ── HEADER: Verdict + Score Ring ────────────────────────────────────
        f"<div style='padding:1.6rem 1.8rem 1.2rem;display:flex;justify-content:space-between;"
        f"align-items:center;'>"

        # Left: verdict
        f"<div style='display:flex;align-items:center;gap:1rem;'>"
        f"<div style='width:52px;height:52px;border-radius:14px;"
        f"background:rgba({_vc_rgb},0.10);border:1px solid rgba({_vc_rgb},0.2);"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-size:1.5rem;color:{vc};'>{dir_icon}</div>"
        f"<div>"
        f"<div style='display:flex;align-items:center;gap:0.6rem;'>"
        f"<span style='font-size:2rem;font-weight:900;color:{vc};letter-spacing:-1px;"
        f"line-height:1;text-shadow:0 0 24px {vc}33;'>{display_v}</span>"
        f"<span style='font-size:0.52rem;font-weight:700;color:{_vc_conf_col};"
        f"padding:0.15rem 0.5rem;border-radius:4px;border:1px solid {_vc_conf_col}33;"
        f"background:{_vc_conf_col}11;text-transform:uppercase;letter-spacing:0.8px;"
        f"'>{_verdict_confidence} CONF"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>HIGH = Engine + master score + 3+ modules agree. "
        f"MODERATE = Engine agrees but fewer modules confirm. "
        f"LOW/NEUTRAL = Mixed signals, proceed with caution.</span></span>"
        f"</span></div>"
        f"<div style='font-size:0.7rem;color:#888;margin-top:0.3rem;font-weight:500;"
        f"line-height:1.4;max-width:340px;'>{vsub}</div>"
        f"</div></div>"

        # Right: score ring
        f"<div style='text-align:center;'>{_ring_svg}</div>"
        f"</div>"

        # ── DIVIDER ────────────────────────────────────────────────────────
        f"<div style='height:1px;margin:0 1.8rem;"
        f"background:linear-gradient(90deg,transparent,#2a2a2a,transparent);'></div>"

        # ── BODY ───────────────────────────────────────────────────────────
        f"<div style='padding:1.2rem 1.8rem 1.5rem;'>"

        # ── Stats row ──────────────────────────────────────────────────────
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;margin-bottom:1.2rem;'>"

        # Stat 1: Bullish Modules
        f"<div style='text-align:center;padding:0.7rem 0.4rem;background:#141414;"
        f"border:1px solid #222;border-radius:10px;'>"
        f"<div style='font-size:1.2rem;font-weight:900;color:{BULL};'>{_bull_tabs}</div>"
        f"<div style='font-size:0.5rem;color:#555;margin-top:0.1rem;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;"
        f"justify-content:center;gap:0.15rem;'>Bullish"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>Active modules scoring 55+ (confirmed buy signal)</span></span>"
        f"</div></div>"

        # Stat 2: Bearish Modules
        f"<div style='text-align:center;padding:0.7rem 0.4rem;background:#141414;"
        f"border:1px solid #222;border-radius:10px;'>"
        f"<div style='font-size:1.2rem;font-weight:900;color:{BEAR};'>{_bear_real}</div>"
        f"<div style='font-size:0.5rem;color:#555;margin-top:0.1rem;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;"
        f"justify-content:center;gap:0.15rem;'>Bearish"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>Active modules scoring below 40 (confirmed bearish signal). Inactive modules do NOT count here.</span></span>"
        f"</div></div>"

        # Stat 3: Agreement
        f"<div style='text-align:center;padding:0.7rem 0.4rem;background:#141414;"
        f"border:1px solid #222;border-radius:10px;'>"
        f"<div style='font-size:1.2rem;font-weight:900;color:{conf_c};'>{_agree_pct}%</div>"
        f"<div style='font-size:0.5rem;color:#555;margin-top:0.1rem;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;"
        f"justify-content:center;gap:0.15rem;'>Agreement"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>% of ACTIVE modules that are bullish. "
        f"Inactive modules don't count. 50%+ = majority agree.</span></span>"
        f"</div></div>"

        # Stat 4: TI Composite
        f"<div style='text-align:center;padding:0.7rem 0.4rem;background:#141414;"
        f"border:1px solid #222;border-radius:10px;'>"
        f"<div style='font-size:1.2rem;font-weight:900;color:{vc};'>{d['pct']:+.0f}%</div>"
        f"<div style='font-size:0.5rem;color:#555;margin-top:0.1rem;font-weight:700;"
        f"text-transform:uppercase;letter-spacing:0.5px;display:flex;align-items:center;"
        f"justify-content:center;gap:0.15rem;'>TI Score"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>Technical Indicators weighted composite: "
        f"positive = net bullish, negative = net bearish. "
        f"Based on {d['bull_n']} bullish and {d['bear_n']} bearish factors.</span></span>"
        f"</div></div>"

        f"</div>"

        # ── WHY THIS DECISION ──────────────────────────────────────────────
        f"<div style='margin-bottom:1.2rem;'>"
        f"<div style='font-size:0.55rem;color:#444;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;display:flex;"
        f"align-items:center;gap:0.3rem;'>"
        f"&#128269; Why {display_v}?"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>The strongest signals that drove this decision, "
        f"ranked by impact. Green = bullish factor, Red = bearish factor.</span></span>"
        f"</div>"
        + _why_html
        + f"</div>"

        # ── MODULE BREAKDOWN ───────────────────────────────────────────────
        f"<div style='margin-bottom:0.4rem;'>"
        f"<div style='font-size:0.55rem;color:#444;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;display:flex;"
        f"align-items:center;gap:0.3rem;'>"
        f"&#128202; Score by Analysis Module"
        f"<span class='dec-tip-wrap'><span class='dec-tip-icon'>?</span>"
        f"<span class='dec-tip-box'>Each module scores 0–100 independently. "
        f"55+ = bullish, 40–54 = neutral, below 40 = bearish/inactive. "
        f"Technical Indicators is weighted 2x in the master score.</span></span>"
        f"</div>"
        + _tab_rows_html
        + f"</div>"

        # ── MASTER SCORE BAR ───────────────────────────────────────────────
        f"<div style='margin-top:0.3rem;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.3rem;'>"
        f"<span style='font-size:0.5rem;color:#444;text-transform:uppercase;"
        f"letter-spacing:0.7px;font-weight:700;'>Weighted Master Score</span>"
        f"<span style='font-size:0.75rem;font-weight:900;color:{_ms_col};'>{_master_score}/100</span></div>"
        f"<div style='background:#1a1a1a;border-radius:999px;height:8px;overflow:hidden;'>"
        f"<div style='width:{_master_score}%;height:100%;border-radius:999px;"
        f"background:linear-gradient(90deg,{_ms_col}cc,{_ms_col});"
        f"box-shadow:0 0 10px {_ms_col}55;'></div></div></div>"

        f"</div>"  # end body

        # ── BOTTOM GLOW BAR ────────────────────────────────────────────────
        f"<div style='height:2px;background:linear-gradient(90deg,{vc}00,{vc}66,{vc}00);'></div>"

        f"</div>",  # end card
        unsafe_allow_html=True,
    )
    

    # ══════════════════════════════════════════════════════════════════════════
    #  2. PRICE LADDER  (BUY signal only)
    # ══════════════════════════════════════════════════════════════════════════
    if V == "BUY":
        from _levels import price_ladder_html as _plh
        st.markdown(
            _plh(d["entry"], d["stop"], d["t1"], d["t2"], d["t3"], True,
                 d.get("entry_quality", ""), d.get("eq_col", ""),
                 d.get("entry_zone_lo"), d.get("entry_zone_hi")),
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  3. LIVE BUY SIGNALS FROM ALL TABS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Live Buy Signals", BULL), unsafe_allow_html=True)


    # ── Multi-timeframe D1 filter ─────────────────────────────────────────────
    _d1_filter_ok   = True   # default: pass
    _d1_filter_warn = ""
    try:
        import yfinance as _yf
        _sym_d1 = symbol_input.strip()
        _d1_key = f"_d1_df_{_sym_d1}"
        if _d1_key not in st.session_state:
            _tf_df = None
            for _d1_try in range(3):
                try:
                    _tf_df = _yf.download(_sym_d1, period="1y", interval="1d",
                                          progress=False, auto_adjust=True)
                    if _tf_df is not None and not _tf_df.empty:
                        break
                except Exception:
                    pass
            st.session_state[_d1_key] = _tf_df
        else:
            _tf_df = st.session_state[_d1_key]

        if _tf_df is not None and len(_tf_df) >= 55:
            if isinstance(_tf_df.columns, pd.MultiIndex):
                _tf_df.columns = _tf_df.columns.get_level_values(0)
            _d1_close = _tf_df["Close"].astype(float)
            _d1_e50   = float(_d1_close.rolling(50).mean().iloc[-1])
            _d1_prev5 = float(_d1_close.rolling(50).mean().iloc[-6])
            _d1_cp    = float(_d1_close.iloc[-1])
            _d1_rising = _d1_e50 > _d1_prev5
            if _d1_cp < _d1_e50 and not _d1_rising:
                _d1_filter_ok   = False
                _d1_filter_warn = (
                    f"&#128200; <b>Daily D1 bearish</b>: price is below the 50-day EMA "
                    f"({_d1_e50:.2f}) and the EMA is declining. "
                    f"Intraday BUY signals are counter-trend — trade with reduced size."
                )
            elif _d1_cp < _d1_e50:
                _d1_filter_warn = (
                    f"&#8595; <b>Daily D1 caution</b>: price is below the 50-day EMA "
                    f"({_d1_e50:.2f}). Trend is recovering but not yet confirmed."
                )
    except Exception:
        pass

    if _d1_filter_warn:
        _d1_col = BEAR if not _d1_filter_ok else NEUT
        st.markdown(
            f"<div style='background:#1b1b1b;border:1px solid #272727;"
            f"border-radius:10px;overflow:hidden;margin-bottom:1rem;"
            f"box-shadow:0 1px 8px rgba(0,0,0,0.15);'>"
            f"<div style='padding:0.8rem 1.2rem;font-size:0.78rem;color:#b0b0b0;"
            f"line-height:1.6;display:flex;align-items:center;gap:0.7rem;'>"
            f"<span style='display:inline-block;width:3px;height:1.4rem;"
            f"border-radius:2px;background:{_d1_col};flex-shrink:0;"
            f"box-shadow:0 0 6px {_d1_col}44;'></span>"
            f"{_d1_filter_warn}</div></div>",
            unsafe_allow_html=True,
        )

    # ── Collect signals from each tab (reuse cached results) ────────────────
    _tab_signals = []   # list of (tab_label, signal_dict)
    _sig_label_map = {
        "Price Action":   "Patterns & Price Action",
        "Chart Patterns": "Patterns",
        "Volume Profile": "Volume Profile",
        "Smart Money":    "Smart Money Concepts",
        "AI Analysis":    "AI Analysis",
    }
    for _sname, _slabel in _sig_label_map.items():
        _s = _cached_sigs.get(_sname)
        if _s:
            _tab_signals.append((_slabel, _s))

    # ── Render each signal box ────────────────────────────────────────────────
    if not _tab_signals:
        st.markdown(
            f"<div style='background:#1b1b1b;border:1px solid #272727;"
            f"border-radius:12px;padding:2.5rem 1.8rem;text-align:center;'>"
            f"<div style='font-size:1.5rem;margin-bottom:0.5rem;opacity:0.3;'>&#128683;</div>"
            f"<div style='font-size:0.85rem;color:#666;font-weight:600;'>No active BUY signals</div>"
            f"<div style='font-size:0.72rem;color:#4a4a4a;margin-top:0.35rem;'>"
            f"Stand aside until conditions improve</div></div>",
            unsafe_allow_html=True,
        )
    else:
        from _levels import price_ladder_html as _dec_plh

        for _idx, (_tlabel, _sig) in enumerate(_tab_signals):
            _conf   = _sig.get("conf", 50)
            _cc     = BULL if _conf >= 65 else (NEUT if _conf >= 45 else BEAR)
            _str_label = 'Strong' if _conf >= 65 else ('Moderate' if _conf >= 45 else 'Weak')

            # Spacing between cards
            if _idx > 0:
                st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

            # ── Signal card with depth ────────────────────────────────────────
            st.markdown(
                f"<div style='background:#1b1b1b;border:1px solid #272727;"
                f"border-radius:12px;overflow:hidden;"
                f"box-shadow:0 2px 16px rgba(0,0,0,0.25);'>"

                # Header — tab name + prominent BUY verdict
                f"<div style='padding:1rem 1.4rem;border-bottom:1px solid #272727;"
                f"display:flex;justify-content:space-between;align-items:center;"
                f"background:linear-gradient(135deg,rgba(76,175,80,0.07),transparent);'>"
                f"<div style='display:flex;align-items:center;gap:0.8rem;'>"
                f"<span style='font-size:0.85rem;font-weight:700;color:#bdbdbd;'>{_tlabel}</span>"
                f"<span style='font-size:1.1rem;font-weight:900;color:#4caf50;"
                f"text-shadow:0 0 12px rgba(76,175,80,0.3);'>&#9650; BUY</span>"
                f"</div>"
                f"<div style='display:flex;align-items:center;gap:0.5rem;'>"
                f"<span style='font-size:1.05rem;font-weight:800;color:{_cc};'>{_conf}%</span>"
                f"<span style='font-size:0.68rem;font-weight:600;padding:0.2rem 0.55rem;"
                f"border-radius:6px;background:rgba({','.join(str(int(_cc[i:i+2],16)) for i in (1,3,5))},0.12);"
                f"color:{_cc};'>{_str_label}</span>"
                f"</div>"
                f"</div>"

                # Body — progress bar
                f"<div style='padding:1rem 1.4rem;'>"
                + _glowbar(_conf, _cc) +
                f"</div>"

                f"</div>",
                unsafe_allow_html=True,
            )

            # ── Price Ladder inside ──────────────────────────────────────────
            try:
                st.markdown(
                    _dec_plh(
                        _sig["entry"], _sig["stop"],
                        _sig["t1"], _sig["t2"], _sig["t3"],
                        True,
                        _sig.get("entry_quality", ""),
                        _sig.get("eq_col", ""),
                        _sig.get("entry_zone_lo"),
                        _sig.get("entry_zone_hi"),
                    ),
                    unsafe_allow_html=True,
                )
            except Exception:
                pass

