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
        f"<div style='background:#1b1b1b;border:1px solid #272727;"
        f"border-radius:10px;padding:1rem 1rem;text-align:center;'>"
        f"<div style='font-size:0.62rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.3rem;'>{label}</div>"
        f"<div style='font-size:{vsize};font-weight:800;color:{color};line-height:1.15;'>{val}</div>"
        + (f"<div style='font-size:0.72rem;color:#555;margin-top:0.22rem;'>{sub}</div>" if sub else "")
        + "</div>"
    )


def _glowbar(pct, color=INFO, height="9px"):
    pct = max(0, min(100, pct))
    return (
        f"<div style='background:#1a1a1a;border-radius:6px;height:{height};width:100%;'>"
        f"<div style='background:linear-gradient(90deg,{color}cc,{color});"
        f"width:{pct}%;height:100%;border-radius:6px;"
        f"box-shadow:0 0 8px {color}55;'></div></div>"
    )


def _sec(title, color=INFO, icon=""):
    return (
        f"<div style='display:flex;align-items:center;gap:0.6rem;"
        f"margin:2.2rem 0 1rem;padding:0;'>"
        f"<div style='width:3px;height:18px;border-radius:2px;background:{color};"
        f"box-shadow:0 0 8px {color}44;'></div>"
        f"<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
        f"text-transform:uppercase;letter-spacing:0.8px;'>{title}</span></div>"
    )


def _badge(text, color=INFO):
    return (
        f"<span style='background:rgba({color[1:3]},{color[3:5]},{color[5:7]},0.12)" if len(color)==7 and color.startswith('#') else f"<span style='background:{color}18"
        f";border-radius:6px;padding:0.2rem 0.65rem;font-size:0.82rem;font-weight:700;"
        f"color:{color};letter-spacing:0.5px;margin-right:0.4rem;white-space:nowrap;'>{text}</span>"
    )


def _sig_row(icon, title, detail, color):
    return (
        f"<div style='display:flex;gap:0.85rem;align-items:flex-start;"
        f"padding:0.85rem 0;border-bottom:1px solid #272727;'>"
        f"<span style='color:{color};font-size:1.15rem;flex-shrink:0;margin-top:0.05rem;'>{icon}</span>"
        f"<div><div style='font-size:0.97rem;color:#e0e0e0;font-weight:700;line-height:1.4;'>"
        f"{title}</div>"
        f"<div style='font-size:0.84rem;color:#888;margin-top:0.18rem;'>{detail}</div>"
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
        paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
        font=dict(color="#888", size=10),
        hovermode="x unified",
        legend=dict(bgcolor="#1b1b1b", bordercolor="#272727", borderwidth=1,
                    font=dict(size=9), x=0.01, y=0.99,
                    orientation="h", yanchor="top"),
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 3):
        fig.update_xaxes(gridcolor="#272727", showgrid=True, zeroline=False, row=i, col=1)
        fig.update_yaxes(gridcolor="#272727", showgrid=True, zeroline=False, row=i, col=1)
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

@st.cache_data(ttl=300, show_spinner=False)
def _build_ml_features(_df):
    """Enhanced feature engineering: 40+ features for maximum predictive power."""
    df = _df
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


@st.cache_data(ttl=3600, show_spinner=False)
def _ml_predict(_df, horizon=10):
    """
    5-model ensemble + Platt calibration + TimeSeriesSplit cross-validation.
    Models: XGBoost · LightGBM · RandomForest · ExtraTrees · GradientBoosting.
    Purged walk-forward with embargo gap — zero lookahead bias.
    Models are persisted to disk with joblib to avoid full retraining after restarts.
    """
    import os as _os
    import hashlib as _hashlib

    try:
        import joblib as _joblib
        _joblib_ok = True
    except ImportError:
        _joblib_ok = False

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

    df = _df
    feat = _build_ml_features(df)
    if len(feat) < 60:
        return None

    # ── Joblib cache key: hash of last 20 close prices + horizon ─────────────
    _cache_key = None
    _cache_path = None
    if _joblib_ok:
        try:
            _n_closes = df["Close"].iloc[-20:].round(4).values
            _key_str  = f"ml_{horizon}_" + "_".join(str(v) for v in _n_closes)
            _cache_key = _hashlib.md5(_key_str.encode()).hexdigest()
            _cache_dir = _os.path.join(_os.path.dirname(__file__), ".ml_cache")
            _os.makedirs(_cache_dir, exist_ok=True)
            _cache_path = _os.path.join(_cache_dir, f"{_cache_key}.joblib")
            if _os.path.isfile(_cache_path):
                _cached = _joblib.load(_cache_path)
                if isinstance(_cached, dict) and "up_prob" in _cached:
                    return _cached
        except Exception:
            _cache_path = None

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

    _result = {
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

    # ── Persist result to disk so restarts skip retraining ────────────────────
    if _joblib_ok and _cache_path:
        try:
            _joblib.dump(_result, _cache_path)
        except Exception:
            pass

    return _result


@st.cache_data(ttl=300, show_spinner=False)
def _price_predictor(_df, horizon=20):
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

    df = _df
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

@st.cache_data(ttl=300, show_spinner=False)
def _historical_analogy(_df, k=25, horizon=10):
    """
    Find the k most similar past market setups using KNN on all 45 features.
    Report what actually happened in those cases — fully transparent, zero black-box.
    This is the most honest form of 'prediction': consensus of historical analogues.
    Features are ATR-normalised before KNN so a 10 SAR stock matches a 200 SAR stock.
    """
    try:
        from sklearn.preprocessing import RobustScaler
        from sklearn.metrics.pairwise import euclidean_distances
    except ImportError:
        return None

    df = _df
    feat = _build_ml_features(df)
    if len(feat) < k + horizon + 20:
        return None

    # ── ATR normalization before scaling ──────────────────────────────────────
    # Compute 14-bar ATR for every row and divide momentum / vol features by it.
    # This makes the distance metric stable across price levels.
    try:
        _h = df["High"].astype(float).reindex(feat.index)
        _l = df["Low"].astype(float).reindex(feat.index)
        _c = df["Close"].astype(float).reindex(feat.index)
        _tr = _h.combine(_l, max) - _l  # simplified TR approx
        _atr_ser = _tr.rolling(14, min_periods=1).mean()
        _atr_arr = _atr_ser.values.reshape(-1, 1)
        _atr_arr = np.where(_atr_arr > 0, _atr_arr, 1.0)
        feat_norm = feat.copy()
        # Divide all ROC / return-type columns (prefix roc_, range_pos_) by ATR
        for _col in feat_norm.columns:
            if any(_col.startswith(p) for p in ("roc_", "range_pos_")):
                feat_norm[_col] = feat_norm[_col].values / _atr_arr.ravel()
    except Exception:
        feat_norm = feat  # fall back to raw features if ATR calc fails

    scaler = RobustScaler()
    X      = scaler.fit_transform(feat_norm.values)
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

@st.cache_data(ttl=300, show_spinner=False)
def _monte_carlo(_df, days=20, n_sims=1000):
    """Monte Carlo simulation using historical log-return statistics."""
    df = _df
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
        height=320, paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
        font=dict(color='#888', size=10),
        margin=dict(l=10, r=10, t=12, b=10),
        hovermode='x unified',
        legend=dict(bgcolor="#1b1b1b", bordercolor="#272727", borderwidth=1,
                    font=dict(size=9), orientation='h', y=-0.18, x=0),
        xaxis=dict(gridcolor="#272727", showgrid=True, zeroline=False),
        yaxis=dict(gridcolor="#272727", showgrid=True, zeroline=False),
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
    """Smart Money Trade Scanner — actionable setups only."""

    theme_palette = st.session_state.get('theme_palette', {})
    global BG, BG2, BDR
    BG  = theme_palette.get('panel', BG)
    BG2 = theme_palette.get('panel_alt', BG2)
    BDR = theme_palette.get('border', BDR)

    if len(df) < 30:
        st.warning("Not enough data for analysis. Need at least 30 days.")
        return
    if hasattr(latest, 'to_dict'):
        latest = latest.to_dict()
    if current_price <= 0:
        st.error("Invalid price data.")
        return

    cp = current_price

    # ── Compute signals ───────────────────────────────────────────────────────
    score, factor_scores, signals = _compute_ai_score(latest, df, cp)
    decision, dec_col, dec_reason = _decision_from_score(score)
    resistances, supports = _find_levels(df)
    fibs = _fibonacci(df)
    forecast_prices, slope_pct, r2 = _forecast(df, days=20)

    sup1 = supports[0]    if supports          else cp * 0.95
    sup2 = supports[1]    if len(supports) > 1 else cp * 0.90
    res1 = resistances[0] if resistances        else cp * 1.05
    res2 = resistances[1] if len(resistances) > 1 else cp * 1.10

    _atr = max(
        (atr_pct / 100) * cp if (atr_pct and atr_pct > 0) else cp * 0.02,
        cp * 0.005,
    )

    recent_20  = df.tail(20)
    swing_high = float(recent_20['High'].max()) if 'High' in df.columns else cp * 1.05
    swing_low  = float(recent_20['Low'].min())  if 'Low'  in df.columns else cp * 0.95
    _rsi       = rsi_current or 50

    # ── ML + historical engines ───────────────────────────────────────────────
    with st.spinner("Scanning for trade opportunities\u2026"):
        ml5   = _ml_predict(df, horizon=5)
        ml10  = _ml_predict(df, horizon=10)
        ml20  = _ml_predict(df, horizon=20)
        pt20  = _price_predictor(df, horizon=20)
        ana5  = _historical_analogy(df, k=25, horizon=5)
        ana10 = _historical_analogy(df, k=25, horizon=10)
        ana20 = _historical_analogy(df, k=25, horizon=20)

    # ══════════════════════════════════════════════════════════════════════════
    #  SIGNAL AGGREGATION
    # ══════════════════════════════════════════════════════════════════════════
    bp = 0       # bull points
    rp = 0       # risk / bear points
    bull_ev = [] # (icon, title, detail, color)
    bear_ev = []

    # 1. AI Score (12-indicator engine)
    n_bull_i = sum(1 for v in factor_scores.values() if v >= 60)
    n_bear_i = sum(1 for v in factor_scores.values() if v <= 40)
    if score >= 65:
        bp += 3
        bull_ev.append(('\u25b2', f'AI Score {score}/100 \u2014 strong bullish',
                        f'{n_bull_i}/12 indicators bullish', BULL))
    elif score >= 55:
        bp += 2
        bull_ev.append(('\u25b2', f'AI Score {score}/100 \u2014 bullish tilt',
                        f'{n_bull_i} indicators support upside', BULL))
    elif score <= 35:
        rp += 3
        bear_ev.append(('\u25bc', f'AI Score {score}/100 \u2014 strong bearish',
                        f'{n_bear_i}/12 indicators bearish', BEAR))
    elif score <= 45:
        rp += 2
        bear_ev.append(('\u25bc', f'AI Score {score}/100 \u2014 bearish tilt',
                        f'{n_bear_i} indicators negative', BEAR))

    # 2. ML Ensemble (5/10/20 day)
    for ml, lbl in [(ml5, '5D'), (ml10, '10D'), (ml20, '20D')]:
        if not ml:
            continue
        _up = ml['up_prob']
        _ac = ml['accuracy']
        if _up >= 55:
            bp += 2
            bull_ev.append(('\u25b2', f'{lbl} ML \u2192 {_up:.0f}% UP',
                            f'Accuracy {_ac:.0f}% on {ml["test_size"]} bars', BULL))
        elif _up <= 45:
            rp += 2
            bear_ev.append(('\u25bc', f'{lbl} ML \u2192 {100 - _up:.0f}% DOWN',
                            f'Accuracy {_ac:.0f}% on {ml["test_size"]} bars', BEAR))

    # 3. Historical pattern match (5/10/20 day)
    for ana, lbl in [(ana5, '5D'), (ana10, '10D'), (ana20, '20D')]:
        if not ana:
            continue
        _wr = ana['w_win_rate']
        if _wr >= 55:
            bp += 1
            bull_ev.append(('\u25b2', f'{lbl} Pattern \u2192 {_wr:.0f}% won',
                            f'{ana["n_up"]}/{ana["n_similar"]} up \u00b7 median {ana["median_return"]:+.1f}%', BULL))
        elif _wr <= 45:
            rp += 1
            bear_ev.append(('\u25bc', f'{lbl} Pattern \u2192 {100 - _wr:.0f}% lost',
                            f'{ana["n_down"]}/{ana["n_similar"]} down', BEAR))

    # 4. Key indicator signals (skip RSI \u2014 handled separately)
    for _icon, _title, _detail, _color in signals[:6]:
        if 'RSI' in _title:
            continue
        if _color == BULL:
            bp += 1
            bull_ev.append((_icon, _title, _detail, BULL))
        elif _color == BEAR:
            rp += 1
            bear_ev.append((_icon, _title, _detail, BEAR))

    # 5. RSI
    if _rsi < 30:
        bp += 2
        bull_ev.append(('\u26a1', f'RSI deeply oversold ({_rsi:.0f})', 'High bounce probability', BULL))
    elif _rsi < 40:
        bp += 1
        bull_ev.append(('\u25b2', f'RSI low ({_rsi:.0f})', 'Approaching oversold', BULL))
    elif _rsi > 70:
        rp += 2
        bear_ev.append(('\u26a0', f'RSI overbought ({_rsi:.0f})', 'Pullback risk elevated', BEAR))
    elif _rsi > 60:
        rp += 1
        bear_ev.append(('\u26a0', f'RSI high ({_rsi:.0f})', 'Approaching overbought', BEAR))

    # 6. Support / resistance proximity
    pct_sup = (cp - sup1) / cp * 100
    pct_res = (res1 - cp) / cp * 100
    if 0 <= pct_sup <= 3:
        bp += 2
        bull_ev.append(('\u25b2', f'Near support {sup1:.2f} ({pct_sup:.1f}% above)',
                        'Quality long entry zone', BULL))
    if 0 <= pct_res <= 3:
        rp += 1
        bear_ev.append(('\u26a0', f'Near resistance {res1:.2f} ({pct_res:.1f}% below)',
                        'Supply zone overhead', BEAR))

    # ── Trade decision ────────────────────────────────────────────────────────
    total_pts = max(bp + rp, 1)
    is_trade  = bp >= 5 and bp >= rp + 3
    confidence = min(round(bp / total_pts * 100), 94) if is_trade else 0

    # Aggregate ML / pattern stats
    ml_probs = [m['up_prob']  for m in [ml5, ml10, ml20] if m]
    avg_ml   = round(sum(ml_probs) / len(ml_probs), 1) if ml_probs else None

    ana_wrs  = [a['w_win_rate'] for a in [ana5, ana10, ana20] if a]
    avg_wr   = round(sum(ana_wrs) / len(ana_wrs), 1) if ana_wrs else None

    n_feat = next((m['n_features'] for m in [ml20, ml10, ml5] if m), 40)

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDER
    # ══════════════════════════════════════════════════════════════════════════

    # ── Pre-compute trade levels for hero card and chart ──────────────────────
    _entry = cp
    _sl_struct = min(swing_low, sup1) - _atr * 0.3
    _stop  = max(_sl_struct, _entry - _atr * 2.0, _entry * 0.92)
    _risk  = max(_entry - _stop, 0.001)

    # Target 1: ML median price or 1.5× risk to nearest resistance
    _use_ml_t = pt20 is not None and pt20.get('p50') is not None and pt20['p50'] > _entry
    if _use_ml_t:
        _t1 = pt20['p50']
        _t2 = pt20.get('p75') or (_entry + _risk * 2.5)
        if _t1 <= _entry: _t1 = _entry + _risk * 1.5
        if _t2 <= _t1:    _t2 = _entry + _risk * 2.5
    else:
        _t1 = min(_entry + _risk * 1.5, res1) if res1 > _entry else _entry + _risk * 1.5
        _t2 = min(_entry + _risk * 2.5, res2) if res2 > _entry else _entry + _risk * 2.5
    _rr1    = round((_t1 - _entry) / _risk, 2) if _risk > 0 else 0
    _rr2    = round((_t2 - _entry) / _risk, 2) if _risk > 0 else 0
    _sl_pct = round(abs(_stop - _entry) / _entry * 100, 2)
    _t1_pct = round((_t1 - _entry) / _entry * 100, 2)
    _t2_pct = round((_t2 - _entry) / _entry * 100, 2)

    # ── Display values ─────────────────────────────────────────────────────────
    hero_col   = BULL if is_trade else (NEUT if bp > rp else '#757575')
    hero_txt   = 'TRADE OPPORTUNITY' if is_trade else 'NO TRADE'
    hero_dir   = '\u25b2 LONG' if is_trade else ('\u25c6 HOLD' if bp >= rp else '\u25bc AVOID')
    hero_sub   = (
        f'Confidence {confidence}% \u2014 {bp} bullish vs {rp} bearish signals'
        if is_trade else
        f'Not enough conviction \u2014 {bp} bull vs {rp} bear signals'
    )
    score_col  = BULL if score >= 55 else (BEAR if score <= 45 else NEUT)
    ml_d_col   = BULL if (avg_ml or 50) >= 55 else (BEAR if (avg_ml or 50) <= 45 else NEUT)
    wr_d_col   = BULL if (avg_wr or 50) >= 55 else (BEAR if (avg_wr or 50) <= 45 else NEUT)
    ml_str     = f'{avg_ml:.0f}% UP' if avg_ml else 'N/A'
    wr_str     = f'{avg_wr:.0f}%'    if avg_wr else 'N/A'

    # AI Score: break down into bullish/bearish indicators
    bull_inds  = [(k, v) for k, v in factor_scores.items() if v >= 60]
    bear_inds  = [(k, v) for k, v in factor_scores.items() if v <= 40]
    neut_inds  = [(k, v) for k, v in factor_scores.items() if 40 < v < 60]
    _score_txt = (
        f"{len(bull_inds)}/12 bullish, {len(bear_inds)}/12 bearish, {len(neut_inds)} neutral"
    )
    _top_bull  = ', '.join(k for k, v in sorted(bull_inds, key=lambda x: x[1], reverse=True)[:3])
    _top_bear  = ', '.join(k for k, v in sorted(bear_inds, key=lambda x: x[1])[:3])

    # ML Probability: pick best accuracy model for display
    _best_ml_acc  = None
    _best_ml_name = None
    for _ml in [ml20, ml10, ml5]:
        if _ml and _ml.get('model_accs'):
            _best_acc_entry = max(_ml['model_accs'].items(), key=lambda x: x[1])
            _best_ml_name, _best_ml_acc = _best_acc_entry
            break
    _ml_acc_str = f'{_best_ml_acc:.0f}% ({_best_ml_name})' if _best_ml_acc else 'N/A'

    # Top ML features
    _top_feats = []
    for _ml in [ml20, ml10, ml5]:
        if _ml and _ml.get('top_features'):
            _top_feats = _ml['top_features'][:3]
            break
    _feat_str = ', '.join(nm for nm, _ in _top_feats) if _top_feats else 'N/A'

    # Pattern Win Rate: best analog stats
    _best_ana    = next((a for a in [ana20, ana10, ana5] if a), None)
    _ana_n       = _best_ana['n_similar']    if _best_ana else 0
    _ana_best    = _best_ana['best_case']    if _best_ana else None
    _ana_worst   = _best_ana['worst_case']   if _best_ana else None
    _ana_med     = _best_ana['median_return'] if _best_ana else None
    _ana_hor     = _best_ana['horizon']      if _best_ana else 20

    # ── 1. HERO CARD — Deep AI Analysis ─────────────────────────────────────
    # ── Market context extras ────────────────────────────────────────────────
    _hist_hi  = float(df['High'].tail(252).max()) if len(df) >= 50 else cp * 1.3
    _hist_lo  = float(df['Low'].tail(252).min())  if len(df) >= 50 else cp * 0.7
    _52w_pos  = round((cp - _hist_lo) / max(_hist_hi - _hist_lo, 0.01) * 100, 1)
    _52w_col  = BULL if _52w_pos >= 65 else (BEAR if _52w_pos <= 35 else NEUT)
    _adx_lbl  = ("Strong Trend" if (adx_current or 0) >= 30
                 else ("Trending" if (adx_current or 0) >= 20 else "Weak/Range"))
    _adx_col  = BULL if (adx_current or 0) >= 25 else (NEUT if (adx_current or 0) >= 15 else '#666')
    _rsi_lbl  = ("Oversold" if _rsi < 35 else ("Overbought" if _rsi > 65 else "Neutral"))
    _rsi_col  = BULL if _rsi < 35 else (BEAR if _rsi > 65 else '#9e9e9e')
    _reg_col  = (BULL if (current_regime or '') == "TREND" else
                 (INFO if (current_regime or '') == "BREAKOUT" else '#666'))
    _ema20c   = BULL if (price_vs_ema20  or 0) > 0 else BEAR
    _ema200c  = BULL if (price_vs_ema200 or 0) > 0 else BEAR
    _5dc      = BULL if (recent_5d_change  or 0) >= 0 else BEAR
    _20dc     = BULL if (recent_20d_change or 0) >= 0 else BEAR

    # Edge narrative
    if is_trade:
        _edge_txt = (
            f"{len(bull_inds)}/12 technical indicators bullish · "
            f"ML ensemble {avg_ml:.0f}% UP probability across 5/10/20-day horizons · "
            f"{avg_wr:.0f}% historical win rate from {_ana_n} analog setups. "
            f"Regime: {current_regime or 'Unknown'}. Strong BUY setup confirmed."
        ) if (avg_ml and avg_wr) else (
            f"{bp} bullish vs {rp} bearish signal points · "
            f"Regime: {current_regime or 'Unknown'} · {confidence}% confidence."
        )
    else:
        _dir_bias = "Bearish pressure dominant" if rp > bp else "Mixed — no clear edge"
        _edge_txt = (
            f"{bp} bull vs {rp} bear signal points. {_dir_bias}. "
            f"Wait for stronger multi-engine alignment before entering a position."
        )

    def _ctx_tile(lbl, val, col):
        return (
            f"<div style='text-align:center;padding:0.35rem 0.2rem;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.5px;font-weight:700;margin-bottom:0.15rem;'>{lbl}</div>"
            f"<div style='font-size:0.82rem;font-weight:800;color:{col};'>{val}</div>"
            f"</div>"
        )

    def _stat_tile_g(lbl, big_val, sub, t_col, bar_val=None):
        bar_html = (
            f"<div style='background:#1a1a1a;border-radius:999px;height:3px;"
            f"overflow:hidden;margin:0.3rem 0;'>"
            f"<div style='width:{int(min(bar_val,100))}%;height:100%;background:{t_col};"
            f"border-radius:999px;box-shadow:0 0 6px {t_col}44;'></div></div>"
        ) if bar_val is not None else ""
        return (
            f"<div style='background:#161616;border-radius:10px;padding:0.85rem 0.9rem;"
            f"border:1px solid #272727;'>"
            f"<div style='font-size:0.49rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.2rem;'>{lbl}</div>"
            f"<div style='font-size:1.8rem;font-weight:900;color:{t_col};line-height:1;'>{big_val}</div>"
            f"{bar_html}"
            f"<div style='font-size:0.62rem;color:#555;margin-top:0.25rem;'>{sub}</div>"
            f"</div>"
        )

    _ml_sub  = f"Accuracy: {_ml_acc_str}" if _ml_acc_str != 'N/A' else "5 models · 3 horizons"
    _wr_sub  = (f"Best: +{_ana_best:.1f}% / Worst: {_ana_worst:.1f}%"
                if _ana_best is not None else f"{_ana_n} analog setups")

    st.markdown(
        f"<div style='background:#1b1b1b;"
        f"border:1px solid #272727;"
        f"border-radius:16px;overflow:hidden;margin-bottom:1.2rem;"
        f"box-shadow:0 4px 24px rgba(0,0,0,0.3);'>"
        f"<div style='padding:1.6rem 2rem;"
        f"background:linear-gradient(135deg,rgba({','.join(str(int(hero_col[i:i+2],16)) for i in (1,3,5)) if hero_col.startswith('#') and len(hero_col)==7 else '85,85,85'},0.07),transparent);'>"

        # ── Row 1: direction verdict + AI score + signal edge
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
        f"flex-wrap:wrap;gap:1.5rem;margin-bottom:1rem;'>"
        f"<div>"
        f"<div style='font-size:0.55rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:2px;font-weight:700;margin-bottom:0.25rem;'>Deep AI Analysis</div>"
        f"<div style='font-size:2.4rem;font-weight:900;color:{hero_col};"
        f"line-height:1;letter-spacing:-1.5px;text-shadow:0 0 20px {hero_col}33;'>{hero_dir}</div>"
        f"<div style='font-size:0.8rem;color:#888;margin-top:0.3rem;'>{hero_sub}</div>"
        f"</div>"
        f"<div style='display:flex;gap:2.5rem;text-align:right;flex-shrink:0;'>"
        f"<div>"
        f"<div style='font-size:0.5rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>AI Score</div>"
        f"<div style='font-size:2.6rem;font-weight:900;color:{score_col};line-height:1;"
        f"text-shadow:0 0 20px {score_col}33;'>"
        f"{score}<span style='font-size:0.85rem;color:#555;'>/100</span></div>"
        f"<div style='font-size:0.6rem;color:#555;'>"
        f"{len(bull_inds)}&#9650; &middot; {len(bear_inds)}&#9660; &middot; {len(neut_inds)} neutral</div>"
        f"</div>"
        f"<div>"
        f"<div style='font-size:0.5rem;color:#606060;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>Signal Edge</div>"
        f"<div style='font-size:2.6rem;font-weight:900;color:{hero_col};line-height:1;'>"
        f"{'HIGH' if bp >= rp + 5 else ('MOD' if bp >= rp + 2 else ('LOW' if bp >= rp else 'NONE'))}"
        f"</div>"
        f"<div style='font-size:0.6rem;color:#555;'>{bp} bull &middot; {rp} bear pts</div>"
        f"</div>"
        f"</div>"
        f"</div>"

        # ── Edge narrative
        f"<div style='background:{hero_col}10;border:1px solid {hero_col}2E;"
        f"border-radius:10px;padding:0.7rem 1rem;margin-bottom:1.1rem;"
        f"font-size:0.78rem;color:#bbb;line-height:1.65;'>{_edge_txt}</div>"

        # ── 4-stat grid
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);"
        f"gap:0.6rem;padding-top:0.85rem;border-top:1px solid #272727;margin-bottom:1rem;'>"
        + _stat_tile_g("AI Score (12 indicators)", str(score), _score_txt, score_col, score)
        + _stat_tile_g("ML Ensemble (avg 5/10/20d)", ml_str, _ml_sub, ml_d_col, avg_ml or 50)
        + _stat_tile_g(f"Pattern Win Rate ({_ana_hor}d)", wr_str, _wr_sub, wr_d_col, avg_wr or 50)
        + _stat_tile_g("Top ML Drivers", (_feat_str[:26] if _feat_str != 'N/A' else '—'),
                       "XGBoost feature importance", INFO)
        + f"</div>"

        # ── Context strip (6 tiles)
        f"<div style='display:grid;grid-template-columns:repeat(6,1fr);"
        f"gap:0.5rem;padding-top:0.75rem;border-top:1px solid #272727;'>"
        + _ctx_tile("Regime",   current_regime or "—",                                _reg_col)
        + _ctx_tile("ADX",      f"{adx_current:.0f} &middot; {_adx_lbl}" if adx_current else "—", _adx_col)
        + _ctx_tile("RSI",      f"{_rsi:.0f} &middot; {_rsi_lbl}",                   _rsi_col)
        + _ctx_tile("EMA 200",  f"{'+' if (price_vs_ema200 or 0) >= 0 else ''}{(price_vs_ema200 or 0):.1f}%", _ema200c)
        + _ctx_tile("5D Chg",   f"{(recent_5d_change  or 0):+.1f}%",                _5dc)
        + _ctx_tile("52W Pos",  f"{_52w_pos:.0f}th pct",                             _52w_col)
        + f"</div>"

        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── PRICE LADDER (BUY / is_trade only) ──────────────────────────────────
    # ── PRICE LADDER (BUY / is_trade only) ──────────────────────────────────
    if is_trade:
        try:
            from _levels import price_ladder_html as _g_plh
            _g_t3 = round(_entry + (_entry - _stop) * 5.0, 2)
            st.markdown(_g_plh(_entry, _stop, _t1, _t2, _g_t3, True), unsafe_allow_html=True)
        except Exception:
            pass

    # ── METHODOLOGY NOTE ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='margin-top:1rem;padding:0.8rem 1rem;"
        f"background:#1b1b1b;border:1px solid #272727;border-radius:10px;"
        f"font-size:0.62rem;color:#555;'>"
        f"<b style='color:#757575;'>Methodology:</b> "
        f"Trade direction determined by {len(factor_scores)}-factor scoring engine, "
        f"5-model ML ensemble (XGBoost · LightGBM · RF · ET · GB) with Platt calibration + "
        f"TimeSeriesSplit CV, XGBoost quantile regression for price targets (P10–P90), "
        f"and 25-nearest-neighbour historical pattern matching. "
        f"Total data: {len(df)} bars · {n_feat} features. "
        f"Past performance does not guarantee future results.</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC GETTER — called from Decision Tab
# ══════════════════════════════════════════════════════════════════════════════

def get_ai_signal(df, cp):
    """Return a BUY signal dict for the Decision Tab, or None if no trade."""
    if df is None or len(df) < 30:
        return None
    try:
        latest = df.iloc[-1].to_dict()
        score, factor_scores, signals = _compute_ai_score(latest, df, float(cp))
        ml5  = _ml_predict(df, horizon=5)
        ml10 = _ml_predict(df, horizon=10)
        ml20 = _ml_predict(df, horizon=20)
        ana5  = _historical_analogy(df, k=25, horizon=5)
        ana10 = _historical_analogy(df, k=25, horizon=10)
        ana20 = _historical_analogy(df, k=25, horizon=20)

        bp = 0; rp = 0
        n_bull = sum(1 for v in factor_scores.values() if v >= 60)
        n_bear = sum(1 for v in factor_scores.values() if v <= 40)
        if score >= 65:   bp += 3
        elif score >= 55: bp += 2
        elif score <= 35: rp += 3
        elif score <= 45: rp += 2
        for _ml in [ml5, ml10, ml20]:
            if _ml:
                if   _ml['up_prob'] >= 55: bp += 2
                elif _ml['up_prob'] <= 45: rp += 2
        for _an in [ana5, ana10, ana20]:
            if _an:
                if   _an['w_win_rate'] >= 55: bp += 1
                elif _an['w_win_rate'] <= 45: rp += 1

        if not (bp >= 5 and bp >= rp + 3):
            return None

        total_pts  = max(bp + rp, 1)
        conf       = min(round(bp / total_pts * 100), 94)
        ml_probs   = [m['up_prob']     for m in [ml5, ml10, ml20] if m]
        ana_wrs    = [a['w_win_rate']  for a in [ana5, ana10, ana20] if a]
        avg_ml     = round(sum(ml_probs) / len(ml_probs), 1) if ml_probs else None
        avg_wr     = round(sum(ana_wrs)  / len(ana_wrs),  1) if ana_wrs  else None
        ana_best   = next((a for a in [ana20, ana10, ana5] if a), None)

        reasons = [f"AI Score {score}/100 — {n_bull}/12 indicators bullish"]
        if avg_ml:
            reasons.append(f"ML Ensemble: {avg_ml:.0f}% UP probability (5/10/20-day avg)")
        if ana_best:
            reasons.append(
                f"Historical win rate: {ana_best['w_win_rate']:.0f}% "
                f"from {ana_best['n_similar']} similar setups"
            )

        atr_ser  = (df["High"] - df["Low"]).rolling(14, min_periods=1).mean()
        atr      = max(float(atr_ser.iloc[-1]), float(cp) * 0.005)
        swing_lo = float(df["Low"].tail(20).min())
        _stop    = max(swing_lo - atr * 0.3, float(cp) * 0.92)
        _risk    = max(float(cp) - _stop, 0.001)
        _t1      = round(float(cp) + _risk * 1.5, 2)
        _t2      = round(float(cp) + _risk * 2.5, 2)
        _t3      = round(float(cp) + _risk * 4.236, 2)

        return dict(
            color=BULL,
            verdict_text="▲ LONG",
            sublabel=f"Deep AI Analysis — Confidence {conf}%",
            conf=conf,
            reasons=reasons[:3],
            entry=float(cp),
            stop=round(_stop, 2),
            t1=_t1,
            t2=_t2,
            t3=_t3,
        )
    except Exception:
        return None
