"""
AI Analysis & Prediction Tab
100% local — no external API. Pure statistics + indicator intelligence.
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

BULL  = "#4caf50"
BEAR  = "#f44336"
NEUT  = "#ff9800"
INFO  = "#2196f3"
PURP  = "#9c27b0"
BG    = "#181818"
BG2   = "#212121"
BDR   = "#303030"


def _kv(label, val, color=INFO, sub="", big=False):
    vsize = "1.75rem" if big else "1.5rem"
    return (
        f"<div style='background:{BG2};border:1px solid {BDR};"
        f"border-top:3px solid {color};border-radius:12px;"
        f"padding:1rem 1rem;text-align:center;'>"
        f"<div style='font-size:0.8rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:0.6px;font-weight:600;margin-bottom:0.3rem;'>{label}</div>"
        f"<div style='font-size:{vsize};font-weight:800;color:{color};line-height:1.15;'>{val}</div>"
        + (f"<div style='font-size:0.78rem;color:#9e9e9e;margin-top:0.22rem;'>{sub}</div>" if sub else "")
        + "</div>"
    )


def _glowbar(pct, color=INFO, height="9px"):
    pct = max(0, min(100, pct))
    return (
        f"<div style='background:{BDR};border-radius:6px;height:{height};width:100%;'>"
        f"<div style='background:linear-gradient(90deg,{color}99,{color});"
        f"width:{pct}%;height:100%;border-radius:6px;"
        f"box-shadow:0 0 8px {color}66;'></div></div>"
    )


def _sec(title, color=INFO, icon=""):
    return (
        f"<div style='font-size:1rem;color:#ffffff;"
        f"font-weight:700;margin:2rem 0 1rem 0;"
        f"border-bottom:2px solid {color}33;padding-bottom:0.5rem;'>"
        f"{title}</div>"
    )


def _badge(text, color=INFO):
    return (
        f"<span style='background:{color}22;border:1px solid {color}55;color:{color};"
        f"border-radius:6px;padding:0.2rem 0.65rem;font-size:0.82rem;font-weight:700;"
        f"letter-spacing:0.5px;margin-right:0.4rem;white-space:nowrap;'>{text}</span>"
    )


def _sig_row(icon, title, detail, color):
    return (
        f"<div style='display:flex;gap:0.85rem;align-items:flex-start;"
        f"padding:0.85rem 0;border-bottom:1px solid {BDR};'>"
        f"<span style='color:{color};font-size:1.15rem;flex-shrink:0;margin-top:0.05rem;'>{icon}</span>"
        f"<div><div style='font-size:0.97rem;color:#ffffff;font-weight:700;line-height:1.4;'>"
        f"{title}</div>"
        f"<div style='font-size:0.84rem;color:#9e9e9e;margin-top:0.18rem;'>{detail}</div>"
        f"</div></div>"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  12-FACTOR AI ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _compute_ai_score(latest, df, current_price):
    scores  = {}
    signals = []
    close   = df["Close"].values
    n       = len(close)

    def _g(key, alt=None, default=None):
        v = latest.get(key)
        if v is None and alt:
            v = latest.get(alt)
        if v is None:
            return default
        try:
            f = float(v)
            return default if np.isnan(f) else f
        except Exception:
            return default

    # 1. EMA Stack
    e20  = _g("EMA_20",  default=current_price)
    e50  = _g("EMA_50",  default=current_price)
    e200 = _g("EMA_200", default=current_price)
    ts   = sum([current_price > e20, current_price > e50, current_price > e200,
                e20 > e50, e50 > e200]) * 20
    scores["EMA Stack"] = ts
    if ts >= 80:
        signals.append(("▲", "Perfect bullish EMA alignment", "Price > EMA20 > EMA50 > EMA200", BULL))
    elif ts >= 60:
        signals.append(("▲", "Bullish EMA positioning", "Most moving averages aligned upward", BULL))
    elif ts <= 20:
        signals.append(("▼", "Perfect bearish EMA alignment", "Price < EMA20 < EMA50 < EMA200", BEAR))
    elif ts <= 40:
        signals.append(("▼", "Bearish EMA positioning", "Most moving averages aligned downward", BEAR))

    # 2. RSI
    rsi = _g("RSI_14", "RSI", 50)
    if   50 <= rsi <= 65:  rs = 75
    elif 65 < rsi <= 70:   rs = 60
    elif rsi > 70:         rs = 22
    elif 40 <= rsi < 50:   rs = 50
    elif 30 <= rsi < 40:   rs = 38
    else:                   rs = 15
    scores["RSI (14)"] = rs
    if rsi > 70:
        signals.append(("⚠", f"RSI overbought at {rsi:.1f}", "Mean-reversion risk elevated", BEAR))
    elif rsi < 30:
        signals.append(("⚡", f"RSI oversold at {rsi:.1f}", "Bounce / mean-reversion potential", BULL))
    elif rsi > 55:
        signals.append(("▲", f"RSI in bullish momentum zone ({rsi:.1f})", "Healthy uptrend reading", BULL))

    # 3. MACD
    macd  = _g("MACD_12_26_9", "MACD", 0)
    msig  = _g("MACDs_12_26_9", "MACD_Signal", 0)
    mhist = _g("MACDh_12_26_9", default=macd - msig)
    if   macd > 0 and macd > msig and mhist > 0:  ms = 88
    elif macd > 0 and macd > msig:                 ms = 72
    elif macd > 0 and macd < msig:                 ms = 42
    elif macd < 0 and macd > msig:                 ms = 55
    else:                                           ms = 18
    scores["MACD"] = ms
    if macd > msig and macd > 0:
        signals.append(("▲", "MACD bullish cross above zero", f"Histogram: {mhist:+.3f}", BULL))
    elif macd < msig and macd < 0:
        signals.append(("▼", "MACD bearish cross below zero", f"Histogram: {mhist:+.3f}", BEAR))
    elif macd < 0 and macd > msig:
        signals.append(("◈", "MACD recovering below zero", "Potential bullish divergence", NEUT))

    # 4. Bollinger Bands
    bbu = _g("BBU_20_2.0", "BB_Upper", current_price * 1.02)
    bbl = _g("BBL_20_2.0", "BB_Lower", current_price * 0.98)
    bbm = _g("BBM_20_2.0", "BB_Middle", (bbu + bbl) / 2)
    bbw = (bbu - bbl) / bbm * 100 if bbm else 4
    bb_pos = (current_price - bbl) / (bbu - bbl) * 100 if (bbu - bbl) else 50
    if   bb_pos <= 20:                 bs = 72
    elif bb_pos >= 80:                 bs = 28
    elif 40 <= bb_pos <= 60:           bs = 55
    else:                               bs = 50
    scores["Bollinger"] = bs
    if bb_pos <= 15:
        signals.append(("⚡", "Price at lower Bollinger Band", "Potential oversold bounce zone", BULL))
    elif bb_pos >= 85:
        signals.append(("⚠", "Price at upper Bollinger Band", "Potential overbought zone", BEAR))

    # 5. ADX (trend strength)
    adx = _g("ADX_14", "ADX", 20)
    dip = _g("DMP_14", "DI+", 20)
    din = _g("DMN_14", "DI-", 20)
    if   adx >= 30 and dip > din:     ads = 82
    elif adx >= 30 and din > dip:     ads = 18
    elif adx >= 25 and dip > din:     ads = 68
    elif adx >= 25 and din > dip:     ads = 32
    elif adx < 20:                     ads = 50
    else:                               ads = 50
    scores["ADX"] = ads
    if adx >= 30:
        trend_dir = "bullish" if dip > din else "bearish"
        signals.append(("▲" if dip > din else "▼", f"Strong {trend_dir} trend (ADX {adx:.1f})",
                        f"DI+ {dip:.1f} vs DI- {din:.1f}", BULL if dip > din else BEAR))

    # 6. Stochastic
    stk = _g("STOCHk_14_3_3", default=50)
    std = _g("STOCHd_14_3_3", default=50)
    if   stk < 20:                     sts = 70
    elif stk > 80:                     sts = 30
    elif stk > std and stk < 80:       sts = 62
    elif stk < std and stk > 20:       sts = 38
    else:                               sts = 50
    scores["Stochastic"] = sts
    if stk < 20:
        signals.append(("⚡", f"Stochastic oversold ({stk:.1f})", "Potential reversal zone", BULL))
    elif stk > 80:
        signals.append(("⚠", f"Stochastic overbought ({stk:.1f})", "Potential pullback zone", BEAR))

    # 7. Volume trend
    if "Volume" in df.columns and len(df) >= 20:
        vol_20 = df["Volume"].tail(20).mean()
        vol_5  = df["Volume"].tail(5).mean()
        vol_ratio = vol_5 / vol_20 if vol_20 else 1
        if   vol_ratio >= 1.5:  vs = 70
        elif vol_ratio >= 1.2:  vs = 60
        elif vol_ratio <= 0.6:  vs = 35
        else:                    vs = 50
        scores["Volume"] = vs
        if vol_ratio >= 1.5:
            signals.append(("▲", "Volume surge detected", f"{vol_ratio:.1f}x average volume", INFO))
    else:
        scores["Volume"] = 50

    # 8. Momentum (5-day)
    if n >= 6:
        mom_5 = (close[-1] / close[-6] - 1) * 100
        if   mom_5 >= 5:   mos = 78
        elif mom_5 >= 2:   mos = 65
        elif mom_5 <= -5:  mos = 22
        elif mom_5 <= -2:  mos = 35
        else:               mos = 50
        scores["Momentum"] = mos
        if mom_5 >= 3:
            signals.append(("▲", f"Strong 5-day momentum (+{mom_5:.1f}%)", "Price gaining strength", BULL))
        elif mom_5 <= -3:
            signals.append(("▼", f"Weak 5-day momentum ({mom_5:.1f}%)", "Price losing strength", BEAR))
    else:
        scores["Momentum"] = 50

    # 9. ATR volatility
    atr = _g("ATRr_14", default=2)
    if   atr <= 1.5:  atrs = 60
    elif atr >= 4:    atrs = 35
    else:              atrs = 50
    scores["Volatility"] = atrs

    # 10. Price vs 200 EMA
    dist_200 = (current_price / e200 - 1) * 100 if e200 else 0
    if   dist_200 >= 10:  d200s = 55
    elif dist_200 >= 5:   d200s = 65
    elif dist_200 >= 0:   d200s = 70
    elif dist_200 >= -5:  d200s = 40
    else:                  d200s = 25
    scores["EMA200 Dist"] = d200s

    # 11. Recent highs/lows
    if n >= 20:
        hi_20 = df["High"].tail(20).max()
        lo_20 = df["Low"].tail(20).min()
        range_pos = (current_price - lo_20) / (hi_20 - lo_20) * 100 if (hi_20 - lo_20) else 50
        if   range_pos >= 80:  rps = 60
        elif range_pos <= 20:  rps = 65
        else:                   rps = 50
        scores["Range Pos"] = rps
    else:
        scores["Range Pos"] = 50

    # 12. Trend consistency
    if n >= 10:
        up_days = sum(1 for i in range(-10, 0) if close[i] > close[i-1])
        if   up_days >= 7:  tcs = 72
        elif up_days >= 5:  tcs = 58
        elif up_days <= 3:  tcs = 35
        else:                tcs = 50
        scores["Consistency"] = tcs
    else:
        scores["Consistency"] = 50

    # Weighted average
    weights = {
        "EMA Stack": 15, "RSI (14)": 12, "MACD": 12, "Bollinger": 8,
        "ADX": 10, "Stochastic": 8, "Volume": 8, "Momentum": 10,
        "Volatility": 5, "EMA200 Dist": 5, "Range Pos": 4, "Consistency": 3
    }
    total_w = sum(weights.values())
    final_score = sum(scores[k] * weights[k] for k in scores) / total_w

    return int(round(final_score)), scores, signals


def _decision_from_score(score):
    if score >= 65: return "BUY",          BULL, "Good setup — bullish bias confirmed"
    if score >= 52: return "WEAK BUY",     "#8BC34A", "Mild bullish lean — wait for confirmation"
    if score >= 48: return "HOLD",         NEUT, "No clear edge — stay neutral"
    if score >= 35: return "WEAK SELL",    "#FF9800", "Mild bearish lean — caution advised"
    if score >= 22: return "SELL",         BEAR, "Bearish confluence — avoid longs"
    return           "STRONG SELL",        "#b71c1c", "Multiple bearish signals — high risk"


# ══════════════════════════════════════════════════════════════════════════════
#  SUPPORT / RESISTANCE
# ══════════════════════════════════════════════════════════════════════════════

def _find_levels(df, n_levels=3):
    if len(df) < 20:
        return [], []
    highs = df["High"].values
    lows  = df["Low"].values
    price = df["Close"].iloc[-1]
    
    # Find pivot highs and lows using full selected date range
    resistances = sorted(set(highs), reverse=True)[:n_levels * 2]
    supports    = sorted(set(lows))[:n_levels * 2]
    
    # Filter to levels above/below current price
    resistances = [r for r in resistances if r > price][:n_levels]
    supports    = [s for s in supports if s < price][:n_levels]
    
    return resistances, supports


def _fibonacci(df):
    if len(df) < 20:
        return {}
    hi = df["High"].max()
    lo = df["Low"].min()
    diff = hi - lo
    return {
        "r_236": lo + diff * 0.236,
        "r_382": lo + diff * 0.382,
        "r_500": lo + diff * 0.500,
        "r_618": lo + diff * 0.618,
        "r_786": lo + diff * 0.786,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PRICE FORECAST (simple linear regression)
# ══════════════════════════════════════════════════════════════════════════════

def _forecast(df, days=20):
    close = df["Close"].values
    n = len(close)
    if n < 30:
        return [close[-1]] * days, 0, 0
    
    # Use last 60 days for regression
    y = np.log(close[-60:])
    x = np.arange(len(y))
    
    # Linear regression
    xm, ym = x.mean(), y.mean()
    slope = np.sum((x - xm) * (y - ym)) / np.sum((x - xm) ** 2)
    intercept = ym - slope * xm
    
    # R² calculation
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - ym) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    
    # Forecast
    future_x = np.arange(len(y), len(y) + days)
    future_y = np.exp(slope * future_x + intercept)
    
    slope_pct = (np.exp(slope) - 1) * 100
    
    return list(future_y), slope_pct, r2


# ══════════════════════════════════════════════════════════════════════════════
#  CHART BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_chart(df, current_price, supports, resistances, fibs, forecast_prices, all_signal_details=None):
    tail = 90
    close = df["Close"].values
    xh = list(df["Date"].tail(tail))

    # Forecast dates
    last_date = pd.to_datetime(df["Date"].iloc[-1])
    xf = [last_date + pd.Timedelta(days=i+1) for i in range(len(forecast_prices))]
    yf = forecast_prices
    fc = BULL if yf[-1] > current_price else BEAR

    # ── Layout: 2 panels ─────────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.80, 0.20],
        vertical_spacing=0.020,
    )

    # ── Row 1 — Candlesticks ─────────────────────────────────────────────────
    if all(c in df.columns for c in ["Open", "High", "Low"]):
        sub = df.tail(tail)
        fig.add_trace(go.Candlestick(
            x=xh,
            open=sub["Open"].values, high=sub["High"].values,
            low=sub["Low"].values,   close=sub["Close"].values,
            name="OHLC",
            increasing_line_color=BULL, decreasing_line_color=BEAR,
            increasing_fillcolor="rgba(76,175,80,0.35)",
            decreasing_fillcolor="rgba(244,67,54,0.35)",
            line_width=0.8,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=xh, y=list(close[-tail:]),
            mode="lines", name="Price",
            line=dict(color=INFO, width=1.8),
        ), row=1, col=1)

    # EMAs
    ema_cfg = [("EMA_20", "#4A9EFF", "EMA20"), ("EMA_50", "#A78BFA", "EMA50"), ("EMA_200", "#FFC107", "EMA200")]
    for col, ec, lbl in ema_cfg:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=xh, y=list(df[col].values[-tail:]),
                mode="lines", name=lbl,
                line=dict(color=ec, width=1.1, dash="dot"),
            ), row=1, col=1)

    # Forecast band + line
    dv    = float(df["Close"].pct_change().std()) * current_price
    upper = [y + dv * (i ** 0.5 * 1.3) for i, y in enumerate(yf)]
    lower = [y - dv * (i ** 0.5 * 1.3) for i, y in enumerate(yf)]
    fa    = "rgba(76,175,80,0.07)" if fc == BULL else "rgba(244,67,54,0.07)"
    fig.add_trace(go.Scatter(
        x=xf + xf[::-1], y=upper + lower[::-1],
        fill="toself", fillcolor=fa, line=dict(width=0),
        showlegend=False, name="AI Band",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=xf, y=yf, mode="lines+markers", name="Forecast",
        line=dict(color=fc, width=2.0, dash="dot"),
        marker=dict(size=5, color=fc),
    ), row=1, col=1)

    # S/R lines
    for sv in supports[:2]:
        fig.add_hline(y=sv, line_dash="dash", line_color=BULL, line_width=0.9,
                      opacity=0.45, annotation_text=f"S {sv:.2f}",
                      annotation_font_color=BULL, annotation_font_size=9, row=1, col=1)
    for rv in resistances[:2]:
        fig.add_hline(y=rv, line_dash="dash", line_color=BEAR, line_width=0.9,
                      opacity=0.45, annotation_text=f"R {rv:.2f}",
                      annotation_font_color=BEAR, annotation_font_size=9, row=1, col=1)

    # ── Row 2 — Volume ───────────────────────────────────────────────────────
    if "Volume" in df.columns:
        clv = df["Close"].values[-tail:]
        vcl = [BULL if i == 0 or clv[i] >= clv[i-1] else BEAR for i in range(len(clv))]
        fig.add_trace(go.Bar(
            x=xh, y=list(df["Volume"].values[-tail:]),
            name="Volume", marker_color=vcl, marker_opacity=0.60,
            showlegend=False,
        ), row=2, col=1)

    # ── Styling ───────────────────────────────────────────────────────────────
    fig.update_layout(
        height=500, margin=dict(l=6, r=6, t=22, b=8),
        paper_bgcolor=BG2, plot_bgcolor=BG,
        font=dict(color="#757575", size=10),
        hovermode="x unified",
        legend=dict(bgcolor=BG2, bordercolor=BDR, borderwidth=1,
                    font=dict(size=9), x=0.01, y=0.99,
                    orientation="h", yanchor="top"),
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 3):
        fig.update_xaxes(gridcolor=BDR, showgrid=True, zeroline=False, row=i, col=1)
        fig.update_yaxes(gridcolor=BDR, showgrid=True, zeroline=False, row=i, col=1)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  PROBABILITY ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _probability_engine(df, latest, current_price, score, slope_pct, r2):
    close = df["Close"].values
    n = len(close)
    out = {}

    for horizon in [5, 10, 20]:
        if n < horizon + 40:
            out[horizon] = {"prob": 50, "base_rate": 50, "n_samples": 0,
                           "factors": [], "confidence": "Low"}
            continue

        # Forward label: 1 if close[i+horizon] > close[i]
        labels = np.array([1 if close[i+horizon] > close[i] else 0 
                          for i in range(n - horizon)])
        base_rate = labels.mean() * 100

        # Simple adjustment based on score
        score_adj = (score - 50) * 0.3
        prob = base_rate + score_adj
        
        # Clamp
        prob = max(5, min(95, prob))
        
        out[horizon] = {
            "prob": round(prob, 1),
            "base_rate": round(base_rate, 1),
            "n_samples": n - horizon,
            "factors": [],
            "confidence": "High" if n > 200 else "Medium" if n > 100 else "Low"
        }

    return out


# ══════════════════════════════════════════════════════════════════════════════
#  ML ENGINE  (4-Model Ensemble with Purged Walk-Forward CV)
# ══════════════════════════════════════════════════════════════════════════════

def _build_ml_features(df):
    """Enhanced feature engineering: 40+ features for maximum predictive power."""
    c        = df['Close']
    hi       = df['High']   if 'High'   in df.columns else c
    lo       = df['Low']    if 'Low'    in df.columns else c
    vol      = df['Volume'] if 'Volume' in df.columns else pd.Series(1.0, index=df.index)
    has_open = 'Open' in df.columns
    o        = df['Open']   if has_open else c
    _eps     = 1e-9

    feat = pd.DataFrame(index=df.index)

    # ── 1. Multi-lag returns (1/2/3/5/10/20d) ────────────────────────────────
    for lag in [1, 2, 3, 5, 10, 20]:
        feat[f'ret_{lag}d'] = c.pct_change(lag)

    # ── 2. Lagged 1-day returns (serial autocorrelation signal) ──────────────
    r1 = c.pct_change(1)
    for k in [1, 2, 3]:
        feat[f'lag{k}_r'] = r1.shift(k)

    # ── 3. Price acceleration (2nd derivative of price) ───────────────────────
    feat['accel'] = r1 - c.pct_change(5) / 5

    # ── 4. Candle body / shadow structure ─────────────────────────────────────
    if has_open:
        hi_oc      = pd.concat([o, c], axis=1).max(axis=1)
        lo_oc      = pd.concat([o, c], axis=1).min(axis=1)
        candle_rng = (hi - lo).where(lambda x: x > 0, np.nan)
        feat['body_ratio']   = (c - o) / candle_rng            # [-1,1] signed
        feat['upper_wic']    = (hi - hi_oc)   / candle_rng    # upper shadow
        feat['lower_wic']    = (lo_oc - lo)   / candle_rng    # lower shadow
        feat['gap']          = (o - c.shift(1)) / (c.shift(1) + _eps)
        feat['bull_count_5'] = (c > o).rolling(5).sum() / 5
        body_abs             = (c - o).abs()
        feat['pat_doji']     = (body_abs / (candle_rng + _eps) < 0.10).astype(float)
        feat['pat_lt_lower'] = (feat['lower_wic'] > 0.55).astype(float)  # hammer/long-tail
        feat['pat_engulf_b'] = (
            (c > o) & (body_abs > body_abs.shift(1)) & (c.shift(1) < o.shift(1))
        ).astype(float)  # bullish engulfing proxy

    # ── 5. RSI + slope ────────────────────────────────────────────────────────
    rsi_col = next((col for col in df.columns if 'RSI' in col), None)
    if rsi_col:
        rsi = pd.to_numeric(df[rsi_col], errors='coerce')
        feat['rsi']       = rsi / 100
        feat['rsi_slope'] = rsi.diff(3) / 300

    # ── 6. MACD histogram + acceleration ──────────────────────────────────────
    mh_col = next((col for col in df.columns if 'MACDh' in col), None)
    if mh_col:
        mh = pd.to_numeric(df[mh_col], errors='coerce')
        feat['macd_hist']  = mh / (c.abs() + _eps)
        feat['macd_accel'] = mh.diff(2) / (c.abs() + _eps)  # histogram acceleration

    # ── 7. Bollinger: %B position + bandwidth (squeeze) ───────────────────────
    bbu_col = next((col for col in df.columns if 'BBU' in col), None)
    bbl_col = next((col for col in df.columns if 'BBL' in col), None)
    if bbu_col and bbl_col:
        bbu    = pd.to_numeric(df[bbu_col], errors='coerce')
        bbl    = pd.to_numeric(df[bbl_col], errors='coerce')
        bb_rng = bbu - bbl
        feat['bb_pos']   = (c - bbl) / bb_rng.where(bb_rng > 0, np.nan)
        feat['bb_width'] = bb_rng   / c.where(c > 0, np.nan)

    # ── 8. EMA distances + EMA20 slope ────────────────────────────────────────
    for ema_col, key in [('EMA_20', 'e20'), ('EMA_50', 'e50'), ('EMA_200', 'e200')]:
        if ema_col in df.columns:
            ema = pd.to_numeric(df[ema_col], errors='coerce')
            feat[f'dist_{key}'] = c / ema.where(ema > 0, np.nan) - 1
    if 'EMA_20' in df.columns and 'EMA_50' in df.columns:
        e20 = pd.to_numeric(df['EMA_20'], errors='coerce')
        e50 = pd.to_numeric(df['EMA_50'], errors='coerce')
        feat['e20_e50']   = e20 / e50.where(e50 > 0, np.nan) - 1
        feat['ema_slope'] = e20.pct_change(5)  # EMA20 momentum

    # ── 9. ATR: normalised level + volatility regime ───────────────────────────
    atr_col = next((col for col in df.columns if 'ATR' in col), None)
    if atr_col:
        atr    = pd.to_numeric(df[atr_col], errors='coerce')
        feat['atr_norm']   = atr / c.where(c > 0, np.nan)
        atr_ma             = atr.rolling(20).mean()
        feat['atr_regime'] = atr / atr_ma.where(atr_ma > 0, np.nan)  # >1 = expanding vol

    # ── 10. Volume: 5/20 ratio + on-up-day strength ────────────────────────────
    vol_ma20          = vol.rolling(20).mean()
    vol_ma5           = vol.rolling(5).mean()
    feat['vol_ratio'] = vol_ma5 / vol_ma20.where(vol_ma20 > 0, np.nan)
    feat['vol_up']    = (c >= c.shift(1)).astype(float) * vol / (vol_ma20 + _eps)

    # ── 11. ADX ────────────────────────────────────────────────────────────────
    adx_col = next((col for col in df.columns if col.startswith('ADX_')), None)
    if adx_col:
        feat['adx'] = pd.to_numeric(df[adx_col], errors='coerce') / 100

    # ── 12. DI: directional flag + spread magnitude ────────────────────────────
    dmp_col = next((col for col in df.columns if 'DMP_' in col), None)
    dmn_col = next((col for col in df.columns if 'DMN_' in col), None)
    if dmp_col and dmn_col:
        dmp              = pd.to_numeric(df[dmp_col], errors='coerce')
        dmn              = pd.to_numeric(df[dmn_col], errors='coerce')
        feat['di_bull']  = (dmp > dmn).astype(float)
        feat['di_delta'] = (dmp - dmn) / 100

    # ── 13. Stochastic: level + slope ─────────────────────────────────────────
    sk_col = next((col for col in df.columns if 'STOCHk' in col), None)
    if sk_col:
        sk                  = pd.to_numeric(df[sk_col], errors='coerce')
        feat['stoch_k']     = sk / 100
        feat['stoch_slope'] = sk.diff(3) / 300

    # ── 14. Range position: 20-day + 60-day ───────────────────────────────────
    hi20 = hi.rolling(20).max()
    lo20 = lo.rolling(20).min()
    hi60 = hi.rolling(60).max()
    lo60 = lo.rolling(60).min()
    feat['range_pos_20'] = (c - lo20) / (hi20 - lo20 + _eps)
    feat['range_pos_60'] = (c - lo60) / (hi60 - lo60 + _eps)

    # ── 15. Realised vol: 10d + 20d + expansion ratio ─────────────────────────
    dr                 = c.pct_change()
    feat['rvol_10']    = dr.rolling(10).std()
    feat['rvol_20']    = dr.rolling(20).std()
    feat['rvol_ratio'] = feat['rvol_10'] / (feat['rvol_20'] + _eps)

    # ── 16. OBV: z-score + slope sign ─────────────────────────────────────────
    obv_col = next((col for col in df.columns if col == 'OBV'), None)
    if obv_col:
        obv             = pd.to_numeric(df[obv_col], errors='coerce')
        obv_ma          = obv.rolling(20).mean()
        obv_sd          = obv.rolling(20).std()
        feat['obv_z']   = (obv - obv_ma) / (obv_sd + _eps)
        feat['obv_slope'] = np.sign(obv.diff(5))

    # Impute NaN: forward-fill → backward-fill → column median → 0
    # This preserves all rows instead of silently dropping hundreds of bars
    feat = feat.ffill().bfill()
    for col in feat.columns:
        if feat[col].isna().any():
            feat[col] = feat[col].fillna(feat[col].median())
    feat = feat.fillna(0.0)

    return feat


def _ml_predict(df, horizon=10):
    """
    5-model ensemble + Platt calibration + TimeSeriesSplit cross-validation.
    Models: XGBoost · LightGBM · RandomForest · ExtraTrees · GradientBoosting.
    Purged walk-forward with embargo gap — zero lookahead bias.
    """
    try:
        from sklearn.ensemble import (
            RandomForestClassifier, ExtraTreesClassifier,
            GradientBoostingClassifier,
        )
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.model_selection import TimeSeriesSplit
        from sklearn.preprocessing import RobustScaler
        from sklearn.metrics import accuracy_score
        import copy as _copy
    except ImportError:
        return None

    feat = _build_ml_features(df)
    if len(feat) < 60:
        return None

    # Compute latest-bar features BEFORE slicing for training
    # (feat[-1] after horizon removal is horizon days old, not today)
    feat_now = feat.iloc[[-1]].copy()  # true current-state row

    close = df['Close'].reindex(feat.index)
    fwd   = close.shift(-horizon).reindex(feat.index)
    label = (fwd > close).astype(int)

    feat  = feat.iloc[:-horizon]
    label = label.iloc[:-horizon]

    # With imputed features all rows are valid; still drop any edge cases
    valid = label.notna() & feat.notna().all(axis=1)
    feat  = feat[valid].copy()
    label = label[valid].copy()

    if len(feat) < 40:
        return None

    embargo = max(5, horizon)
    scaler  = RobustScaler()
    X_all   = scaler.fit_transform(feat.values)
    y_all   = label.values
    X_now   = scaler.transform(feat_now.values)  # true latest bar

    # ── Build base classifiers ───────────────────────────────────────────────
    use_xgb  = False
    use_lgbm = False
    try:
        import xgboost as xgb
        use_xgb = True
    except ImportError:
        pass
    try:
        import lightgbm as lgb
        use_lgbm = True
    except ImportError:
        pass

    base_clfs = []
    if use_xgb:
        base_clfs.append(('XGB', xgb.XGBClassifier(
            n_estimators=400, max_depth=4, learning_rate=0.03,
            subsample=0.75, colsample_bytree=0.70,
            min_child_weight=5, gamma=0.15,
            reg_alpha=0.10, reg_lambda=1.5,
            use_label_encoder=False, eval_metric='logloss',
            random_state=42, verbosity=0,
        )))
    if use_lgbm:
        base_clfs.append(('LGBM', lgb.LGBMClassifier(
            n_estimators=400, num_leaves=15, learning_rate=0.03,
            min_child_samples=10, subsample=0.75, colsample_bytree=0.70,
            reg_alpha=0.10, reg_lambda=1.5,
            random_state=42, verbose=-1, n_jobs=-1,
        )))
    base_clfs += [
        ('RF', RandomForestClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=5,
            max_features='sqrt', random_state=42, n_jobs=-1,
        )),
        ('ET', ExtraTreesClassifier(
            n_estimators=300, max_depth=8, min_samples_leaf=5,
            max_features='sqrt', random_state=43, n_jobs=-1,
        )),
        ('GB', GradientBoostingClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.06,
            subsample=0.80, min_samples_leaf=8, random_state=44,
        )),
    ]
    if not base_clfs:
        return None

    # ── TimeSeriesSplit cross-validation ─────────────────────────────────────
    n_splits        = min(5, max(2, len(feat) // 60))
    tscv            = TimeSeriesSplit(n_splits=n_splits, gap=embargo)
    fold_proba      = np.full(len(y_all), np.nan)
    model_fold_accs = {n: [] for n, _ in base_clfs}
    importances     = {}

    for train_idx, test_idx in tscv.split(X_all):
        if len(train_idx) < 60 or len(test_idx) < 10:
            continue
        X_tr, X_te = X_all[train_idx], X_all[test_idx]
        y_tr, y_te = y_all[train_idx], y_all[test_idx]
        fold_sum   = np.zeros(len(test_idx))
        n_valid    = 0
        for mname, clf in base_clfs:
            clf.fit(X_tr, y_tr)
            p_te     = clf.predict_proba(X_te)[:, 1]
            fold_sum += p_te
            n_valid  += 1
            model_fold_accs[mname].append(
                accuracy_score(y_te, (p_te >= 0.5).astype(int)) * 100
            )
            if hasattr(clf, 'feature_importances_'):
                for fn, fv in zip(feat.columns, clf.feature_importances_):
                    importances[fn] = importances.get(fn, 0.0) + fv
        if n_valid > 0:
            fold_proba[test_idx] = fold_sum / n_valid

    valid_mask = ~np.isnan(fold_proba)
    cv_acc = (
        accuracy_score(y_all[valid_mask], (fold_proba[valid_mask] >= 0.5).astype(int)) * 100
        if valid_mask.sum() >= 10 else 50.0
    )
    model_accs = {
        n: round(float(np.mean(v)), 1)
        for n, v in model_fold_accs.items() if v
    }

    # ── Platt-calibrated probability (best individual model) ─────────────────
    up_prob_cal = None
    if model_accs:
        best_name = max(model_accs, key=model_accs.get)
        best_clf  = next(c for n, c in base_clfs if n == best_name)
        try:
            cal_split = int(len(X_all) * 0.80)
            cal_copy  = _copy.deepcopy(best_clf)
            cal_copy.fit(X_all[:cal_split], y_all[:cal_split])
            cal = CalibratedClassifierCV(cal_copy, method='sigmoid', cv='prefit')
            cal.fit(X_all[cal_split:], y_all[cal_split:])
            up_prob_cal = float(cal.predict_proba(X_now)[0][1]) * 100
        except Exception:
            up_prob_cal = None

    # ── Final ensemble: all models trained on full dataset ───────────────────
    proba_now_sum = np.zeros(1)
    for mname, clf in base_clfs:
        clf.fit(X_all, y_all)
        proba_now_sum += clf.predict_proba(X_now)[:, 1]
    ens_prob = float(proba_now_sum[0]) / len(base_clfs) * 100

    # Blend: 60% Platt-calibrated + 40% raw ensemble
    up_prob   = (up_prob_cal * 0.60 + ens_prob * 0.40) if up_prob_cal is not None else ens_prob
    direction = 'UP' if up_prob >= 50 else 'DOWN'

    n_fi     = sum(1 for _, m in base_clfs if hasattr(m, 'feature_importances_'))
    top_feat = []
    if n_fi > 0 and importances:
        avg_imp  = {k: v / n_fi for k, v in importances.items()}
        top_feat = [
            (nm, round(v * 100, 1))
            for nm, v in sorted(avg_imp.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

    return {
        'model_name':   f'{len(base_clfs)}-Model Ensemble',
        'horizon':      horizon,
        'up_prob':      round(up_prob, 1),
        'direction':    direction,
        'accuracy':     round(cv_acc, 1),
        'cv_folds':     n_splits,
        'test_size':    int(valid_mask.sum()),
        'top_features': top_feat,
        'n_features':   len(feat.columns),
        'model_accs':   model_accs,
    }


def _price_predictor(df, horizon=20):
    """
    XGBoost quantile regression: predicts actual SAR price at p10/p25/p50/p75/p90.
    Target = log-return at horizon days, back-transformed to SAR price.
    Validated with TimeSeriesSplit for realistic MAE.
    """
    try:
        import xgboost as xgb
        from sklearn.preprocessing import RobustScaler
        from sklearn.model_selection import TimeSeriesSplit
    except ImportError:
        return None

    feat = _build_ml_features(df)
    if len(feat) < 60:
        return None

    # True latest-bar features for prediction
    feat_now = feat.iloc[[-1]].copy()

    close   = df['Close'].reindex(feat.index)
    fwd_log = np.log(close.shift(-horizon) / (close + 1e-9)).reindex(feat.index)
    feat    = feat.iloc[:-horizon]
    fwd_log = fwd_log.iloc[:-horizon]

    valid   = fwd_log.notna() & feat.notna().all(axis=1)
    feat    = feat[valid].copy()
    fwd_log = fwd_log[valid].copy()

    if len(feat) < 40:
        return None

    cp     = float(df['Close'].iloc[-1])
    scaler = RobustScaler()
    X_all  = scaler.fit_transform(feat.values)
    y_all  = fwd_log.values
    X_now  = scaler.transform(feat_now.values)  # true latest bar

    tscv      = TimeSeriesSplit(n_splits=3, gap=max(5, horizon))
    mae_folds = []
    results   = {}

    for qname, q_val in [('p10', 0.10), ('p25', 0.25), ('p50', 0.50),
                          ('p75', 0.75), ('p90', 0.90)]:
        try:
            mdl = xgb.XGBRegressor(
                objective='reg:quantileerror',
                quantile_alpha=q_val,
                n_estimators=300, max_depth=3, learning_rate=0.05,
                subsample=0.80, colsample_bytree=0.75,
                reg_alpha=0.05, reg_lambda=1.0,
                random_state=42, verbosity=0,
            )
            if qname == 'p50':   # validate median accuracy
                for tr_i, te_i in tscv.split(X_all):
                    if len(tr_i) < 60:
                        continue
                    mdl.fit(X_all[tr_i], y_all[tr_i])
                    err = float(np.mean(np.abs(mdl.predict(X_all[te_i]) - y_all[te_i])))
                    mae_folds.append(err * cp)   # approx SAR dollar MAE
            mdl.fit(X_all, y_all)
            results[qname] = round(float(cp * np.exp(mdl.predict(X_now)[0])), 2)
        except Exception:
            results[qname] = None

    # Enforce monotone quantiles: p10 ≤ p25 ≤ p50 ≤ p75 ≤ p90
    keys = ['p10', 'p25', 'p50', 'p75', 'p90']
    vals = [results[k] for k in keys if results[k] is not None]
    if len(vals) >= 3 and vals != sorted(vals):
        for k, sv in zip(keys, sorted(vals)):
            results[k] = sv

    if not any(results.get(k) for k in keys):
        return None

    return {
        **results,
        'current': cp,
        'horizon': horizon,
        'mae':     round(float(np.mean(mae_folds)), 2) if mae_folds else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  HISTORICAL PATTERN MATCHING  (K-Nearest-Neighbours analogy engine)
# ══════════════════════════════════════════════════════════════════════════════

def _historical_analogy(df, k=25, horizon=10):
    """
    Find the k most similar past market setups using KNN on all 45 features.
    Report what actually happened in those cases — fully transparent, zero black-box.
    This is the most honest form of 'prediction': consensus of historical analogues.
    """
    try:
        from sklearn.preprocessing import RobustScaler
        from sklearn.metrics.pairwise import euclidean_distances
    except ImportError:
        return None

    feat = _build_ml_features(df)
    if len(feat) < k + horizon + 20:
        return None

    scaler = RobustScaler()
    X      = scaler.fit_transform(feat.values)
    close  = df['Close'].reindex(feat.index).values

    # Current state (last bar)
    x_now  = X[[-1]]

    # Search only rows that have `horizon` future bars available
    max_search = len(X) - horizon - 1
    if max_search < k:
        return None
    X_hist = X[:max_search]

    dists   = euclidean_distances(x_now, X_hist)[0]
    nn_idx  = np.argsort(dists)[:k]

    outcomes = []
    for idx in nn_idx:
        fut_idx = idx + horizon
        if fut_idx < len(close) and close[idx] > 0:
            ret = (close[fut_idx] / close[idx] - 1) * 100
            outcomes.append(ret)

    if len(outcomes) < 5:
        return None

    outcomes   = np.array(outcomes)
    n_up       = int((outcomes > 0).sum())
    n_total    = len(outcomes)
    win_rate   = n_up / n_total * 100

    # Weighted win rate — closer analogues count more
    top_dists  = dists[nn_idx[:len(outcomes)]]
    weights    = 1.0 / (top_dists + 1e-6)
    weights   /= weights.sum()
    w_win_rate = float(np.sum(weights * (outcomes > 0).astype(float))) * 100

    return {
        'n_similar':    n_total,
        'n_up':         n_up,
        'n_down':       n_total - n_up,
        'win_rate':     round(win_rate, 1),
        'w_win_rate':   round(w_win_rate, 1),
        'avg_return':   round(float(outcomes.mean()), 2),
        'median_return':round(float(np.median(outcomes)), 2),
        'best_case':    round(float(np.percentile(outcomes, 90)), 2),
        'worst_case':   round(float(np.percentile(outcomes, 10)), 2),
        'std':          round(float(outcomes.std()), 2),
        'horizon':      horizon,
        'direction':    'UP' if w_win_rate >= 50 else 'DOWN',
        'outcomes':     outcomes.tolist(),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  MONTE CARLO  (1 000 paths, log-normal returns)
# ══════════════════════════════════════════════════════════════════════════════

def _monte_carlo(df, days=20, n_sims=1000):
    """Monte Carlo simulation using historical log-return statistics."""
    close = df['Close'].values
    if len(close) < 40:
        return None

    log_r = np.diff(np.log(close[-60:]))
    mu    = log_r.mean()
    sigma = log_r.std()
    cp    = float(close[-1])

    rng   = np.random.default_rng(42)
    rand  = rng.normal(mu, sigma, (n_sims, days))
    paths = np.empty((n_sims, days))
    paths[:, 0] = cp * np.exp(rand[:, 0])
    for t in range(1, days):
        paths[:, t] = paths[:, t - 1] * np.exp(rand[:, t])

    final = paths[:, -1]
    return {
        'paths':   paths,
        'final':   final,
        'current': cp,
        'mu': mu, 'sigma': sigma, 'days': days,
        'p5':   float(np.percentile(final, 5)),
        'p25':  float(np.percentile(final, 25)),
        'p50':  float(np.percentile(final, 50)),
        'p75':  float(np.percentile(final, 75)),
        'p95':  float(np.percentile(final, 95)),
        'prob_up': round(float((final > cp).mean()) * 100, 1),
    }


def _build_mc_chart(mc, df):
    """Fan chart: percentile bands of 1 000 Monte Carlo paths."""
    paths   = mc['paths']
    cp      = mc['current']
    days    = mc['days']
    n_sims  = paths.shape[0]

    last_date = pd.to_datetime(df['Date'].iloc[-1])
    xd = [last_date + pd.Timedelta(days=i) for i in range(days)]

    p5  = np.percentile(paths, 5,  axis=0)
    p25 = np.percentile(paths, 25, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p75 = np.percentile(paths, 75, axis=0)
    p95 = np.percentile(paths, 95, axis=0)

    fig = go.Figure()

    # Sample 60 ghost paths
    idx = np.random.default_rng(1).choice(n_sims, 60, replace=False)
    for i in idx:
        is_up = paths[i, -1] >= cp
        clr   = 'rgba(76,175,80,0.06)' if is_up else 'rgba(244,67,54,0.06)'
        fig.add_trace(go.Scatter(
            x=xd, y=list(paths[i]),
            mode='lines', line=dict(width=0.4, color=clr),
            showlegend=False, hoverinfo='skip',
        ))

    # Filled bands
    fig.add_trace(go.Scatter(
        x=xd + xd[::-1], y=list(p95) + list(p5[::-1]),
        fill='toself', fillcolor='rgba(74,158,255,0.05)',
        line=dict(width=0), name='5%–95% range', showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=xd + xd[::-1], y=list(p75) + list(p25[::-1]),
        fill='toself', fillcolor='rgba(74,158,255,0.13)',
        line=dict(width=0), name='25%–75% range', showlegend=True,
    ))

    # Key lines
    line_cfg = [
        (p95, BULL,   1.1, 'dot',   'Bull P95'),
        (p50, NEUT,   2.0, 'solid', 'Median'),
        (p5,  BEAR,   1.1, 'dot',   'Bear P5'),
    ]
    for y, color, w, dash, name in line_cfg:
        fig.add_trace(go.Scatter(
            x=xd, y=list(y), mode='lines',
            line=dict(color=color, width=w, dash=dash),
            name=name, showlegend=True,
        ))

    # Current price reference
    fig.add_hline(
        y=cp, line_dash='dash',
        line_color='rgba(255,255,255,0.25)', line_width=1,
        annotation_text=f'  Now {cp:.2f}',
        annotation_font_color='#9e9e9e', annotation_font_size=9,
    )

    fig.update_layout(
        height=320, paper_bgcolor=BG2, plot_bgcolor=BG,
        font=dict(color='#757575', size=10),
        margin=dict(l=10, r=10, t=12, b=10),
        hovermode='x unified',
        legend=dict(bgcolor=BG2, bordercolor=BDR, borderwidth=1,
                    font=dict(size=9), orientation='h', y=-0.18, x=0),
        xaxis=dict(gridcolor=BDR, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=BDR, showgrid=True, zeroline=False),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TAB FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def gemini_tab(df, symbol_input, stock_name, latest,
               current_price, period_change, period_high, period_low,
               annual_vol, current_regime, adx_current, rsi_current,
               atr_pct, price_vs_ema20, price_vs_ema200,
               recent_5d_change, recent_20d_change):
    """Main AI Analysis tab."""
    
    theme_palette = st.session_state.get('theme_palette', {})
    global BG, BG2, BDR
    BG  = theme_palette.get('panel', BG)
    BG2 = theme_palette.get('panel_alt', BG2)
    BDR = theme_palette.get('border', BDR)

    if len(df) < 30:
        st.warning("Not enough data for AI analysis. Need at least 30 days.")
        return

    # Convert latest to dict if it's a Series
    if hasattr(latest, 'to_dict'):
        latest = latest.to_dict()
    
    if current_price <= 0:
        st.error("Invalid price data.")
        return

    # ── Compute everything ───────────────────────────────────────────────────
    score, factor_scores, signals = _compute_ai_score(latest, df, current_price)
    decision, dec_col, dec_reason = _decision_from_score(score)
    resistances, supports = _find_levels(df)
    fibs = _fibonacci(df)
    forecast_prices, slope_pct, r2 = _forecast(df, days=20)
    probabilities = _probability_engine(df, latest, current_price, score, slope_pct, r2)

    # Target / Stop calculation
    target_price = forecast_prices[-1] if forecast_prices else current_price
    sl_price = current_price * 0.95  # 5% stop loss
    target_pct = (target_price / current_price - 1) * 100
    sl_pct = (sl_price / current_price - 1) * 100
    tgt_col = BULL if target_pct > 0 else BEAR
    sl_col = BEAR
    tgt_sign = "+" if target_pct > 0 else ""
    sl_sign = ""

    # Score band color
    if score >= 65:   score_band_col = BULL
    elif score >= 52: score_band_col = "#8BC34A"
    elif score >= 48: score_band_col = NEUT
    elif score >= 35: score_band_col = "#FF9800"
    else:             score_band_col = BEAR

    # Count bullish/bearish/neutral factors
    bull_f = sum(1 for s in factor_scores.values() if s >= 60)
    bear_f = sum(1 for s in factor_scores.values() if s <= 40)
    neut_f = 12 - bull_f - bear_f

    # Score dots
    score_dots = ""
    for fname, fscore in factor_scores.items():
        dot_col = BULL if fscore >= 60 else BEAR if fscore <= 40 else NEUT
        score_dots += f"<span style='color:{dot_col};font-size:1.2rem;'>●</span> "

    # Top drivers
    sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
    top_bull_drv = [f[0] for f in sorted_factors[:3] if f[1] >= 60]
    top_bear_drv = [f[0] for f in sorted_factors[-3:] if f[1] <= 40]
    driver_str = f"<span style='color:{BULL};'>{' · '.join(top_bull_drv)}</span>" if top_bull_drv else "<span style='color:#757575;'>None strong</span>"

    # ══════════════════════════════════════════════════════════════════════════
    #  HERO PANEL
    # ══════════════════════════════════════════════════════════════════════════
    
    hero_html = (
        f"<div style='background:linear-gradient(135deg,{BG2} 0%,{BG} 100%);"
        f"border:1px solid {BDR};border-left:5px solid {dec_col};"
        f"border-radius:16px;padding:1.6rem 2rem;margin-bottom:1.4rem;'>"
        # Row 1: Decision + Score
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
        f"flex-wrap:wrap;gap:1rem;margin-bottom:1.1rem;'>"
        f"<div>"
        f"<div style='font-size:0.62rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.3rem;'>Decision</div>"
        f"<div style='font-size:4rem;font-weight:900;color:{dec_col};line-height:1;"
        f"letter-spacing:-1px;'>{decision}</div>"
        f"</div>"
        f"<div style='text-align:right;'>"
        f"<div style='font-size:0.62rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.3rem;'>AI Score</div>"
        f"<div style='font-size:3rem;font-weight:900;color:{score_band_col};"
        f"line-height:1;letter-spacing:-1px;'>{score}<span style='font-size:1.2rem;"
        f"color:#757575;font-weight:600;'>/100</span></div>"
        f"<div style='font-size:0.72rem;color:#757575;margin-top:0.3rem;'>"
        f"{bull_f} bullish · {bear_f} bearish · {neut_f} neutral</div>"
        f"</div>"
        f"</div>"
        # Score dots
        f"<div style='margin-bottom:1rem;'>{score_dots}"
        f"<span style='font-size:0.62rem;color:#757575;margin-left:0.5rem;'>"
        f"Each dot = 1 of 12 indicators ("
        f"<span style='color:{BULL};'>●</span> bullish "
        f"<span style='color:{NEUT};'>●</span> neutral "
        f"<span style='color:{BEAR};'>●</span> bearish)</span>"
        f"</div>"
        # Row 2: Target + Stop + Current
        f"<div style='display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:1rem;'>"
        f"<div style='background:{BG};border-radius:10px;padding:0.7rem 1.1rem;"
        f"border:1px solid {BDR};flex:1;min-width:140px;'>"
        f"<div style='font-size:0.6rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.3rem;'>20-Day Target</div>"
        f"<div style='font-size:1.5rem;font-weight:800;color:{tgt_col};'>"
        f"${target_price:,.2f}</div>"
        f"<div style='font-size:0.75rem;color:{tgt_col};'>"
        f"{tgt_sign}{target_pct:.1f}% from current</div>"
        f"</div>"
        f"<div style='background:{BG};border-radius:10px;padding:0.7rem 1.1rem;"
        f"border:1px solid {BDR};flex:1;min-width:140px;'>"
        f"<div style='font-size:0.6rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.3rem;'>Stop Loss</div>"
        f"<div style='font-size:1.5rem;font-weight:800;color:{sl_col};'>"
        f"${sl_price:,.2f}</div>"
        f"<div style='font-size:0.75rem;color:{sl_col};'>"
        f"{sl_pct:.1f}% from current</div>"
        f"</div>"
        f"<div style='background:{BG};border-radius:10px;padding:0.7rem 1.1rem;"
        f"border:1px solid {BDR};flex:1;min-width:140px;'>"
        f"<div style='font-size:0.6rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.3rem;'>Current Price</div>"
        f"<div style='font-size:1.5rem;font-weight:800;color:#ffffff;'>"
        f"${current_price:,.2f}</div>"
        f"<div style='font-size:0.75rem;color:#757575;'>Live quote</div>"
        f"</div>"
        f"</div>"
        # Row 3: Top drivers
        f"<div style='font-size:0.78rem;color:#9e9e9e;padding-top:0.8rem;"
        f"border-top:1px solid {BDR};'>"
        f"<span style='color:#757575;font-size:0.68rem;text-transform:uppercase;"
        f"letter-spacing:0.7px;font-weight:700;'>Top bullish drivers: </span>"
        f"{driver_str}"
        + (f"  <span style='color:#757575;font-size:0.68rem;text-transform:uppercase;"
           f"letter-spacing:0.7px;font-weight:700;'>· Bearish: </span>"
           f"<span style='color:{BEAR};'>{' · '.join(top_bear_drv)}</span>" if top_bear_drv else "")
        + f"</div>"
        f"</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    #  CHART
    # ══════════════════════════════════════════════════════════════════════════
    
    st.markdown(_sec("Technical Chart", INFO), unsafe_allow_html=True)
    fig = _build_chart(df, current_price, supports, resistances, fibs, forecast_prices)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    #  MACHINE LEARNING PREDICTION
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown(_sec("🤖 Machine Learning — Directional Probability", PURP), unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:0.75rem;color:#757575;margin:-0.6rem 0 1rem;'>"
        f"<b style='color:#9e9e9e;'>5-model ensemble</b> (XGBoost · LightGBM · RF · ET · GB) · "
        f"Platt calibration · TimeSeriesSplit CV · "
        f"<b style='color:#9e9e9e;'>{len(df)} bars</b> · "
        f"<b style='color:#9e9e9e;'>{len(_build_ml_features(df).dropna().columns)} features</b>. "
        f"Quantile price targets via <b style='color:#9e9e9e;'>XGBoost quantile regression</b> — "
        f"<b style='color:#9e9e9e;'>zero lookahead bias throughout.</b></div>",
        unsafe_allow_html=True,
    )

    with st.spinner("Analysing historical patterns · Training 5-model ensemble…"):
        ml5   = _ml_predict(df, horizon=5)
        ml10  = _ml_predict(df, horizon=10)
        ml20  = _ml_predict(df, horizon=20)
        pt20  = _price_predictor(df, horizon=20)
        ana5  = _historical_analogy(df, k=25, horizon=5)
        ana10 = _historical_analogy(df, k=25, horizon=10)
        ana20 = _historical_analogy(df, k=25, horizon=20)
        mc    = _monte_carlo(df, days=20, n_sims=1000)

    if ml5 is None and ml10 is None and ml20 is None and ana5 is None:
        st.info("Need at least 60 days of history for ML prediction. Extend the date range.")
    else:
        # ── HERO: Historical Pattern Match ───────────────────────────────────
        st.markdown(
            _sec('🔍 Historical Pattern Match — What Happened in Similar Setups?', INFO),
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:0.75rem;color:#757575;margin:-0.6rem 0 1rem;'>"
            f"Searched <b style='color:#9e9e9e;'>{len(df)}</b> historical bars of this stock · "
            f"Found the <b style='color:#9e9e9e;'>25 most similar market setups</b> using KNN "
            f"on <b style='color:#9e9e9e;'>45 technical features</b> · Closer matches weighted higher."
            f"</div>",
            unsafe_allow_html=True,
        )

        for ana, hrzn_lbl, hrzn_days in [
            (ana5, '5-Day', 5), (ana10, '10-Day', 10), (ana20, '20-Day', 20)
        ]:
            if ana is None:
                continue
            cp_val  = float(df['Close'].iloc[-1])
            up_c    = BULL if ana['direction'] == 'UP' else BEAR
            wwr     = ana['w_win_rate']
            avg_r   = ana['avg_return']
            med_r   = ana['median_return']
            best_r  = ana['best_case']
            worst_r = ana['worst_case']
            n_up    = ana['n_up']
            n_dn    = ana['n_down']
            n_tot   = ana['n_similar']

            if   wwr >= 70: sig_lbl, sig_col = 'STRONG BUY SIGNAL',  BULL
            elif wwr >= 60: sig_lbl, sig_col = 'BUY SIGNAL',         '#8BC34A'
            elif wwr >= 55: sig_lbl, sig_col = 'WEAK BUY',           NEUT
            elif wwr <= 30: sig_lbl, sig_col = 'STRONG SELL SIGNAL', BEAR
            elif wwr <= 40: sig_lbl, sig_col = 'SELL SIGNAL',        '#FF9800'
            elif wwr <= 45: sig_lbl, sig_col = 'WEAK SELL',          NEUT
            else:           sig_lbl, sig_col = 'NEUTRAL',            '#757575'

            win_pct   = n_up / n_tot * 100
            loss_pct  = n_dn / n_tot * 100
            avg_sign  = '+' if avg_r  >= 0 else ''
            med_sign  = '+' if med_r  >= 0 else ''
            best_sign = '+' if best_r >= 0 else ''
            wrst_sign = '+' if worst_r >= 0 else ''
            proj_price = round(cp_val * (1 + med_r / 100), 2)

            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-left:4px solid {up_c};border-radius:12px;"
                f"padding:1.1rem 1.25rem;margin-bottom:0.75rem;'>"
                # Header row
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;margin-bottom:0.65rem;'>"
                f"<div>"
                f"<span style='font-size:0.62rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:1px;font-weight:700;'>{hrzn_lbl} Outlook</span>"
                f"<span style='margin-left:0.75rem;background:{sig_col}22;"
                f"border:1px solid {sig_col}55;color:{sig_col};"
                f"border-radius:6px;padding:0.18rem 0.65rem;"
                f"font-size:0.7rem;font-weight:800;'>{sig_lbl}</span>"
                f"</div>"
                f"<div style='text-align:right;'>"
                f"<div style='font-size:2rem;font-weight:900;color:{up_c};"
                f"line-height:1;letter-spacing:-1px;'>"
                f"{'▲' if ana['direction']=='UP' else '▼'} {wwr:.0f}%</div>"
                f"<div style='font-size:0.65rem;color:#757575;'>weighted win rate</div>"
                f"</div>"
                f"</div>"
                # Win/loss bar
                f"<div style='display:flex;border-radius:5px;overflow:hidden;"
                f"height:8px;margin-bottom:0.55rem;'>"
                f"<div style='background:{BULL};width:{win_pct:.0f}%;'></div>"
                f"<div style='background:{BEAR};width:{loss_pct:.0f}%;'></div>"
                f"</div>"
                # Stats grid
                f"<div style='display:grid;grid-template-columns:repeat(5,1fr);"
                f"gap:0.5rem;margin-bottom:0.5rem;'>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:0.5px;'>Won</div>"
                f"<div style='font-size:1.05rem;font-weight:800;color:{BULL};'>"
                f"{n_up}/{n_tot}</div></div>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:0.5px;'>Avg Return</div>"
                f"<div style='font-size:1.05rem;font-weight:800;"
                f"color:{BULL if avg_r >= 0 else BEAR};'>"
                f"{avg_sign}{avg_r:.1f}%</div></div>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:0.5px;'>Median</div>"
                f"<div style='font-size:1.05rem;font-weight:800;"
                f"color:{BULL if med_r >= 0 else BEAR};'>"
                f"{med_sign}{med_r:.1f}%</div></div>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:0.5px;'>Best P90</div>"
                f"<div style='font-size:1.05rem;font-weight:800;color:{BULL};'>"
                f"{best_sign}{best_r:.1f}%</div></div>"
                f"<div style='text-align:center;'>"
                f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:0.5px;'>Worst P10</div>"
                f"<div style='font-size:1.05rem;font-weight:800;color:{BEAR};'>"
                f"{wrst_sign}{worst_r:.1f}%</div></div>"
                f"</div>"
                # Projected price
                f"<div style='border-top:1px solid {BDR};padding-top:0.5rem;"
                f"display:flex;align-items:center;gap:1rem;'>"
                f"<span style='font-size:0.62rem;color:#555;'>Median projected price "
                f"in {hrzn_days} days:</span>"
                f"<span style='font-size:1.1rem;font-weight:800;color:{up_c};'>"
                f"{proj_price:.2f} SAR</span>"
                f"<span style='font-size:0.65rem;color:{up_c};'>"
                f"({med_sign}{med_r:.1f}%)</span>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div style='font-size:0.62rem;color:#424242;margin-bottom:1.5rem;'>"
            f"How to read: the 25 past moments with the most similar combination of RSI, MACD, "
            f"EMA alignment, volume, momentum &amp; 40+ signals were found in this stock's own "
            f"history. Win rate = % of those cases where price was higher after the stated period. "
            f"Past results do not guarantee future performance.</div>",
            unsafe_allow_html=True,
        )

        # ── 5-model ensemble directional cards ───────────────────────────────
        st.markdown(
            _sec('🤖 5-Model Ensemble — Directional Probability', PURP),
            unsafe_allow_html=True,
        )

        # ── 3 horizon cards ──────────────────────────────────────────────────
        h_cols = st.columns(3, gap="small")
        for col, ml, label in zip(h_cols,
                                  [ml5, ml10, ml20],
                                  ["5-Day", "10-Day", "20-Day"]):
            with col:
                if ml is None:
                    st.markdown(
                        f"<div style='background:{BG2};border:1px solid {BDR};border-radius:12px;"
                        f"padding:1rem;text-align:center;color:#505050;'>{label}<br/>Not enough data</div>",
                        unsafe_allow_html=True,
                    )
                    continue

                up_p      = ml['up_prob']
                direc     = ml['direction']
                acc       = ml['accuracy']
                color     = BULL if direc == 'UP' else BEAR
                accs_html = ""
                if ml.get('model_accs'):
                    accs_html = (
                        "<br/><span style='color:#424242;font-size:0.57rem;'>"
                        + " · ".join(f"{k}:{v}%" for k, v in ml['model_accs'].items())
                        + "</span>"
                    )

                if acc >= 58:   rel_txt, rel_col = "Strong Signal",    BULL
                elif acc >= 54: rel_txt, rel_col = "Moderate Signal",  "#8BC34A"
                elif acc >= 50: rel_txt, rel_col = "Weak Signal",      NEUT
                else:           rel_txt, rel_col = "Below-random",     "#757575"

                bar_pct = up_p if direc == 'UP' else (100 - up_p)

                st.markdown(
                    f"<div style='background:{BG2};border:1px solid {BDR};"
                    f"border-top:3px solid {color};border-radius:12px;padding:1.1rem;'>"
                    f"<div style='font-size:0.58rem;color:#9e9e9e;text-transform:uppercase;"
                    f"letter-spacing:0.9px;font-weight:700;margin-bottom:0.5rem;'>{label} Outlook</div>"
                    f"<div style='font-size:2.8rem;font-weight:900;color:{color};line-height:1;"
                    f"letter-spacing:-1px;'>{'▲' if direc=='UP' else '▼'} {up_p:.0f}%</div>"
                    f"<div style='font-size:0.78rem;color:{color};font-weight:700;"
                    f"margin:0.25rem 0 0.5rem;'>{direc}</div>"
                    f"<div style='background:{BDR};border-radius:4px;height:5px;margin-bottom:0.6rem;'>"
                    f"<div style='background:{color};width:{bar_pct:.0f}%;height:100%;border-radius:4px;'></div></div>"
                    f"<div style='font-size:0.63rem;color:#757575;line-height:1.6;'>"
                    f"<span style='color:{rel_col};font-weight:700;'>{rel_txt}</span><br/>"
                    f"Historical accuracy: <b style='color:#c8c8c8;'>{acc:.1f}%</b><br/>"
                    f"Tested on {ml['test_size']} bars · {ml['model_name']}{accs_html}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

        # ── AI Price Target (quantile regression) ─────────────────────────────
        if pt20:
            st.markdown(
                _sec('🎯  AI Price Target — 20-Day Quantile Forecast', INFO),
                unsafe_allow_html=True,
            )
            cp_pt        = pt20['current']
            mae          = pt20.get('mae')
            pt_scenarios = [
                ('🐻 Bear', 'P10', pt20.get('p10'), BEAR),
                ('Low',     'P25', pt20.get('p25'), '#FF9800'),
                ('📍 Base', 'P50', pt20.get('p50'), NEUT),
                ('High',    'P75', pt20.get('p75'), '#8BC34A'),
                ('🚀 Bull', 'P90', pt20.get('p90'), BULL),
            ]
            pt_cols = st.columns(5, gap='small')
            for ptcol, (lbl, pctile, price, cc) in zip(pt_cols, pt_scenarios):
                with ptcol:
                    if price is None:
                        st.markdown(
                            f"<div style='background:{BG2};border:1px solid {BDR};"
                            f"border-radius:10px;padding:0.7rem;text-align:center;"
                            f"color:#505050;font-size:0.7rem;'>{lbl}<br/>—</div>",
                            unsafe_allow_html=True,
                        )
                        continue
                    pct   = (price / cp_pt - 1) * 100
                    sign  = '+' if pct >= 0 else ''
                    arrow = '▲' if pct >= 0 else '▼'
                    st.markdown(
                        f"<div style='background:{BG2};border:1px solid {BDR};"
                        f"border-top:3px solid {cc};border-radius:12px;"
                        f"padding:0.9rem 0.6rem;text-align:center;'>"
                        f"<div style='font-size:0.52rem;color:#9e9e9e;"
                        f"text-transform:uppercase;letter-spacing:0.8px;"
                        f"font-weight:700;margin-bottom:0.3rem;'>{lbl} · {pctile}</div>"
                        f"<div style='font-size:1.35rem;font-weight:900;color:{cc};"
                        f"line-height:1.1;'>{price:.2f}</div>"
                        f"<div style='font-size:0.7rem;color:{cc};font-weight:700;"
                        f"margin-top:0.25rem;'>{arrow} {sign}{pct:.1f}%</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            # Range indicator bar
            p10v = pt20.get('p10') or cp_pt * 0.90
            p90v = pt20.get('p90') or cp_pt * 1.10
            rng  = max(p90v - p10v, 0.01)
            pos  = min(100, max(0, (cp_pt - p10v) / rng * 100))
            mae_str = f" · ±{mae:.2f} SAR median error" if mae else ""
            st.markdown(
                f"<div style='margin-top:0.6rem;background:{BG2};border:1px solid {BDR};"
                f"border-radius:10px;padding:0.65rem 1rem;'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:0.62rem;color:#555;margin-bottom:0.3rem;'>"
                f"<span style='color:{BEAR};'>Bear P10 · {p10v:.2f}</span>"
                f"<span style='color:#9e9e9e;'>◆ Now: {cp_pt:.2f} SAR</span>"
                f"<span style='color:{BULL};'>Bull P90 · {p90v:.2f}</span>"
                f"</div>"
                f"<div style='position:relative;background:{BDR};border-radius:5px;height:10px;'>"
                f"<div style='background:linear-gradient(90deg,{BEAR}66,{NEUT}88,{BULL}66);"
                f"width:100%;height:100%;border-radius:5px;'></div>"
                f"<div style='position:absolute;top:50%;left:{pos:.0f}%;"
                f"transform:translateX(-50%) translateY(-50%);"
                f"width:14px;height:14px;background:#fff;border:2px solid {BG2};"
                f"border-radius:50%;box-shadow:0 0 8px rgba(255,255,255,0.55);'></div>"
                f"</div>"
                f"<div style='font-size:0.6rem;color:#424242;margin-top:0.35rem;"
                f"text-align:center;'>XGBoost quantile regression · "
                f"{pt20['horizon']}-day horizon{mae_str}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── Feature importance (10-day model) ────────────────────────────────
        ml_ref = ml10 or ml5 or ml20
        if ml_ref and ml_ref['top_features']:
            st.markdown(
                f"<div style='font-size:0.72rem;color:#9e9e9e;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:0.7px;"
                f"margin:1.2rem 0 0.5rem;'>What's driving the prediction</div>",
                unsafe_allow_html=True,
            )
            feat_labels = {
                'ret_1d': '1-Day Return', 'ret_3d': '3-Day Return', 'ret_5d': '5-Day Return',
                'ret_10d': '10-Day Return', 'ret_20d': '20-Day Return',
                'rsi': 'RSI', 'macd_hist': 'MACD Histogram',
                'bb_pos': 'Bollinger %B', 'atr_norm': 'ATR (normalised)',
                'dist_e20': 'Distance from EMA20', 'dist_e50': 'Distance from EMA50',
                'dist_e200': 'Distance from EMA200', 'e20_e50': 'EMA20 vs EMA50',
                'vol_ratio': 'Volume Ratio', 'adx': 'ADX', 'di_bull': 'DI+ > DI-',
                'stoch_k': 'Stochastic %K', 'range_pos_20': '20-Day Range Position',
                'rvol_20': 'Realised Volatility', 'obv_slope': 'OBV Slope',
            }
            hrzn = ml_ref['horizon']
            names = [feat_labels.get(f[0], f[0]) for f in ml_ref['top_features']]
            vals  = [f[1] for f in ml_ref['top_features']]
            colors_fi = [BULL if v > vals[0] * 0.6 else PURP if v > vals[0] * 0.3 else "#555"
                         for v in vals]

            fig_fi = go.Figure(go.Bar(
                x=vals[::-1], y=names[::-1],
                orientation='h',
                marker=dict(color=colors_fi[::-1], line=dict(width=0)),
                text=[f'{v:.1f}%' for v in vals[::-1]],
                textposition='outside', textfont=dict(size=9, color='#9e9e9e'),
            ))
            fig_fi.update_layout(
                height=max(200, len(names) * 28 + 30),
                paper_bgcolor=BG2, plot_bgcolor=BG,
                font=dict(color='#757575', size=10),
                margin=dict(l=10, r=60, t=8, b=8),
                xaxis=dict(title=f'Importance % ({hrzn}-day model)',
                           gridcolor=BDR, zeroline=False, showgrid=True),
                yaxis=dict(gridcolor='rgba(0,0,0,0)', showgrid=False),
            )
            st.plotly_chart(fig_fi, width="stretch", config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════════════════════
    #  MONTE CARLO SIMULATION
    # ══════════════════════════════════════════════════════════════════════════

    if mc:
        st.markdown(_sec("🎲 Monte Carlo Simulation — 1,000 Random Paths · 20 Days", NEUT),
                    unsafe_allow_html=True)

        daily_ann_vol = mc['sigma'] * np.sqrt(252) * 100
        st.markdown(
            f"<div style='font-size:0.75rem;color:#757575;margin:-0.6rem 0 1rem;'>"
            f"Each path draws daily returns from this stock's own log-return distribution "
            f"(μ={mc['mu']*100:.3f}%/day, σ={mc['sigma']*100:.2f}%/day · "
            f"annualised vol = <b style='color:#9e9e9e;'>{daily_ann_vol:.1f}%</b>). "
            f"No model — pure statistics.</div>",
            unsafe_allow_html=True,
        )

        mc_left, mc_right = st.columns([2, 1], gap="medium")

        with mc_left:
            fig_mc = _build_mc_chart(mc, df)
            st.plotly_chart(fig_mc, width="stretch", config={"displayModeBar": False})

        with mc_right:
            cp = mc['current']

            def _pct_str(price):
                pct = (price / cp - 1) * 100
                sign = "+" if pct >= 0 else ""
                return f"{price:.2f}", f"{sign}{pct:.1f}%"

            scenarios = [
                ("🐻  Bear (5th %ile)",    mc['p5'],  BEAR),
                ("Low (25th %ile)",        mc['p25'], "#FF9800"),
                ("📍 Base (median)",       mc['p50'], NEUT),
                ("High (75th %ile)",       mc['p75'], "#8BC34A"),
                ("🚀  Bull (95th %ile)",   mc['p95'], BULL),
            ]

            for label, price, col in scenarios:
                pv, ps = _pct_str(price)
                st.markdown(
                    f"<div style='background:{BG2};border:1px solid {BDR};"
                    f"border-radius:8px;padding:0.5rem 0.85rem;margin-bottom:0.35rem;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='font-size:0.63rem;color:#757575;'>{label}</span>"
                    f"<span style='color:{col};font-weight:700;font-size:0.92rem;'>{pv}"
                    f" <span style='font-size:0.65rem;'>({ps})</span></span></div>",
                    unsafe_allow_html=True,
                )

            prob_up = mc['prob_up']
            p_col = BULL if prob_up > 55 else BEAR if prob_up < 45 else NEUT
            st.markdown(
                f"<div style='background:{BG2};border:2px solid {p_col}44;"
                f"border-radius:12px;padding:0.85rem 1rem;margin-top:0.7rem;text-align:center;'>"
                f"<div style='font-size:0.55rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.9px;font-weight:700;margin-bottom:0.3rem;'>"
                f"Probability above current price</div>"
                f"<div style='font-size:2.4rem;font-weight:900;color:{p_col};line-height:1;'>"
                f"{prob_up:.1f}%</div>"
                f"<div style='font-size:0.62rem;color:#555;margin-top:0.22rem;'>"
                f"in {mc['days']} days · 1,000 simulations</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Histogram of final prices
        fig_hist = go.Figure()
        cp_line = mc['current']
        above = [v for v in mc['final'] if v >= cp_line]
        below = [v for v in mc['final'] if v <  cp_line]
        for sub, col, name in [(above, 'rgba(76,175,80,0.55)', 'Above current'),
                               (below, 'rgba(244,67,54,0.55)', 'Below current')]:
            if sub:
                fig_hist.add_trace(go.Histogram(
                    x=sub, nbinsx=40,
                    name=name,
                    marker=dict(color=col, line=dict(width=0.3, color='rgba(0,0,0,0.3)')),
                ))
        fig_hist.add_vline(
            x=cp_line, line_dash='dash', line_color='rgba(255,255,255,0.35)',
            line_width=1.5, annotation_text=f'  Current {cp_line:.2f}',
            annotation_font_color='#9e9e9e', annotation_font_size=9,
        )
        def _hex_to_rgba(h, a=0.53):
            h = h.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return f'rgba({r},{g},{b},{a})'
        for pval, pname, pcol in [(mc['p5'], 'P5', BEAR), (mc['p95'], 'P95', BULL)]:
            fig_hist.add_vline(x=pval, line_dash='dot', line_color=_hex_to_rgba(pcol),
                               line_width=1)
        fig_hist.update_layout(
            barmode='overlay', height=180,
            paper_bgcolor=BG2, plot_bgcolor=BG,
            font=dict(color='#757575', size=10),
            margin=dict(l=10, r=10, t=8, b=8),
            xaxis=dict(title='Price after 20 days', gridcolor=BDR, zeroline=False),
            yaxis=dict(title='Paths', gridcolor=BDR),
            legend=dict(bgcolor=BG2, bordercolor=BDR, borderwidth=1,
                        font=dict(size=9), orientation='h', y=-0.35, x=0),
            bargap=0.02,
        )
        st.plotly_chart(fig_hist, width="stretch", config={"displayModeBar": False})





