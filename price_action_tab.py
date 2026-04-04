import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

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
        f"<div style='font-size:1rem;color:#ffffff;font-weight:700;"
        f"margin:2rem 0 1rem 0;border-bottom:2px solid {color}33;"
        f"padding-bottom:0.5rem;'>{title}</div>"
    )


def _glowbar(pct, color=BULL, height="8px"):
    pct = max(0, min(100, pct))
    return (
        f"<div style='background:{BDR};border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:linear-gradient(90deg,{color}99,{color});border-radius:999px;'></div></div>"
    )


def _pivot_sr(df, current_price, lookback=120, window=8):
    """Find nearest S/R from recent pivot points (not global min/max)."""
    n = min(len(df), lookback)
    sub = df.tail(n)
    highs, lows = sub['High'].values, sub['Low'].values
    res_c, sup_c = [], []
    for i in range(window, len(sub) - window):
        h_sl = highs[max(0, i - window):i + window + 1]
        l_sl = lows[max(0, i - window):i + window + 1]
        if highs[i] == h_sl.max() and highs[i] > current_price:
            res_c.append(float(highs[i]))
        if lows[i] == l_sl.min() and lows[i] < current_price:
            sup_c.append(float(lows[i]))
    res_c.sort()              # ascending — nearest resistance first
    sup_c.sort(reverse=True)  # descending — nearest support first
    fb_hi = float(sub['High'].tail(20).max())
    fb_lo = float(sub['Low'].tail(20).min())
    r1 = res_c[0] if res_c else max(fb_hi, current_price * 1.02)
    r2 = res_c[1] if len(res_c) > 1 else r1 + (r1 - current_price) * 0.5
    s1 = sup_c[0] if sup_c else min(fb_lo, current_price * 0.98)
    s2 = sup_c[1] if len(sup_c) > 1 else s1 - (current_price - s1) * 0.5
    return s1, s2, r1, r2


def _count_zone_tests(series, threshold, above=True, min_gap=3):
    """Count distinct zone test events (gaps of min_gap bars between tests)."""
    in_zone = (series >= threshold) if above else (series <= threshold)
    tests, gap = 0, min_gap
    for v in in_zone:
        if v:
            if gap >= min_gap:
                tests += 1
            gap = 0
        else:
            gap += 1
    return tests


def _compute_trade_setup(df, current_price, trend,
                          sup1, sup2, res1, res2,
                          swing_low, swing_high,
                          ma_series, s_touches, r_touches,
                          s_str, r_str, in_s, in_r):
    """Compute a price-action based trade setup: entry, stop, targets, reasons."""
    if len(df) < 15:
        return None

    h, l, c = df['High'], df['Low'], df['Close']

    # ATR-14
    tr  = pd.concat([(h - l),
                     (h - c.shift(1)).abs(),
                     (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr_s = tr.rolling(14, min_periods=1).mean()
    atr   = float(atr_s.iloc[-1])
    if not np.isfinite(atr) or atr <= 0:
        atr = float((h - l).mean())

    # MA relationship
    ma_now   = float(ma_series.iloc[-1]) if not ma_series.empty else current_price
    ma_5ago  = float(ma_series.iloc[-6]) if len(ma_series) >= 6 else ma_now
    price_above_ma = current_price > ma_now
    ma_slope_up    = ma_now > ma_5ago

    # RSI-14
    delta   = c.diff()
    avg_g   = delta.clip(lower=0).rolling(14, min_periods=1).mean().iloc[-1]
    avg_l   = (-delta).clip(lower=0).rolling(14, min_periods=1).mean().iloc[-1]
    rsi     = float(100 - 100 / (1 + avg_g / (avg_l + 1e-9)))

    # Last 2 candles
    c0 = df.iloc[-1]
    c1 = df.iloc[-2] if len(df) >= 2 else c0
    bull0  = c0['Close'] > c0['Open']
    bear0  = c0['Close'] < c0['Open']
    bull1  = c1['Close'] > c1['Open']
    bear1  = c1['Close'] < c1['Open']
    rng0   = float(c0['High'] - c0['Low'])
    body0  = float(abs(c0['Close'] - c0['Open']))
    uw0    = float(c0['High'] - max(c0['Close'], c0['Open']))
    lw0    = float(min(c0['Close'], c0['Open']) - c0['Low'])

    is_bull_engulf = (bull0 and bear1
                      and c0['Close'] > c1['Open']
                      and c0['Open']  < c1['Close'])
    is_bear_engulf = (bear0 and bull1
                      and c0['Close'] < c1['Open']
                      and c0['Open']  > c1['Close'])
    is_hammer = rng0 > 0 and lw0 > 2 * body0 and uw0 < 0.35 * rng0
    is_shoot  = rng0 > 0 and uw0 > 2 * body0 and lw0 < 0.35 * rng0
    is_doji   = rng0 > 0 and body0 < 0.1 * rng0

    patterns = []
    if is_bull_engulf: patterns.append(('Bullish Engulfing', BULL))
    if is_hammer:      patterns.append(('Hammer / Pin Bar',  BULL))
    if is_bear_engulf: patterns.append(('Bearish Engulfing', BEAR))
    if is_shoot:       patterns.append(('Shooting Star',     BEAR))
    if is_doji:        patterns.append(('Doji — Indecision', NEUT))

    # Volume confirmation
    vol_confirm = False
    if 'Volume' in df.columns and len(df) >= 10:
        avg_vol    = float(df['Volume'].iloc[-11:-1].mean())
        last_vol   = float(df['Volume'].iloc[-1])
        vol_confirm = last_vol > avg_vol * 1.2

    # ── Scoring ──────────────────────────────────────────────────────
    ls = 0; ss = 0; lr = []; sr = []

    # Trend
    if trend == 'UPTREND':
        ls += 3; lr.append("Primary trend is UPTREND — higher highs & higher lows confirm bullish bias")
    elif trend == 'DOWNTREND':
        ss += 3; sr.append("Primary trend is DOWNTREND — lower highs & lower lows confirm bearish bias")
    else:
        ls += 1; ss += 1
        lr.append("Sideways market — best traded from the extremes of the range")
        sr.append("Sideways market — best traded from the extremes of the range")

    # MA position
    if price_above_ma:
        ls += 2; lr.append(f"Price ({current_price:.2f}) is above the 20-MA ({ma_now:.2f}) — buyers are in control")
    else:
        ss += 2; sr.append(f"Price ({current_price:.2f}) is below the 20-MA ({ma_now:.2f}) — sellers are in control")

    # MA slope
    if ma_slope_up:
        ls += 1; lr.append("20-MA is rising — short-term momentum is bullish")
    else:
        ss += 1; sr.append("20-MA is declining — short-term momentum is bearish")

    # Zone proximity
    pct_sup = (current_price - sup1) / current_price * 100
    pct_res = (res1 - current_price) / current_price * 100
    if 0 <= pct_sup <= 3:
        ls += 2; lr.append(f"Price is only {pct_sup:.1f}% above Support ({sup1:.2f}) — high-quality long entry zone")
    if 0 <= pct_res <= 3:
        ss += 2; sr.append(f"Price is only {pct_res:.1f}% below Resistance ({res1:.2f}) — high-quality short entry zone")
    if in_s:
        ls += 1; lr.append("Price is inside the Support Zone — active demand area")
    if in_r:
        ss += 1; sr.append("Price is inside the Resistance Zone — active supply area")

    # Zone strength bonus
    if s_touches >= 3:
        ls += 1; lr.append(f"Support has been tested {s_touches}× — {s_str} demand zone, higher probability hold")
    if r_touches >= 3:
        ss += 1; sr.append(f"Resistance has been tested {r_touches}× — {r_str} supply zone, higher probability rejection")

    # Candle patterns
    if is_bull_engulf:
        ls += 3; lr.append("Bullish Engulfing candle — buyers completely overwhelmed sellers; high-conviction reversal signal")
    if is_hammer:
        ls += 2; lr.append("Hammer / Pin Bar — price rejected lower levels with a long lower wick; demand stepped in")
    if is_bear_engulf:
        ss += 3; sr.append("Bearish Engulfing candle — sellers completely overwhelmed buyers; high-conviction reversal signal")
    if is_shoot:
        ss += 2; sr.append("Shooting Star — price rejected higher levels with a long upper wick; supply stepped in")
    if is_doji and in_s:
        ls += 1; lr.append("Doji at support level — indecision after a decline; potential exhaustion of sellers")
    if is_doji and in_r:
        ss += 1; sr.append("Doji at resistance level — indecision after a rally; potential exhaustion of buyers")

    # Volume
    if vol_confirm and bull0:
        ls += 1; lr.append("Above-average volume on a bullish candle — institutional buyers present")
    if vol_confirm and bear0:
        ss += 1; sr.append("Above-average volume on a bearish candle — institutional sellers present")

    # RSI
    if   rsi < 30: ls += 2; lr.append(f"RSI deeply oversold ({rsi:.0f}) — high mean-reversion probability")
    elif rsi < 40: ls += 1; lr.append(f"RSI ({rsi:.0f}) — entering oversold territory; downside momentum fading")
    if   rsi > 70: ss += 2; sr.append(f"RSI overbought ({rsi:.0f}) — upside exhaustion signal")
    elif rsi > 60: ss += 1; sr.append(f"RSI ({rsi:.0f}) — approaching overbought; bullish momentum may tire")

    # ── Determine dominant direction ─────────────────────────────────
    total = max(ls + ss, 1)
    if ls > ss:
        setup = 'LONG';    reasons = lr; sc = BULL
        conf  = min(round(ls / total * 100), 94)
    elif ss > ls:
        setup = 'SHORT';   reasons = sr; sc = BEAR
        conf  = min(round(ss / total * 100), 94)
    else:
        setup = 'NEUTRAL'; reasons = (lr + sr)[:4]; sc = NEUT; conf = 50
    # Only return a trade setup for high-quality LONG setups
    # (user only trades long; skip shorts/neutrals and weak signals)
    if setup != 'LONG' or ls < 5:
        # Return info dict with no_trade flag so UI can show why
        return {
            'no_trade': True,
            'setup': setup,
            'conf': conf if setup == 'LONG' else 0,
            'ls': ls, 'ss': ss,
            'rsi': rsi, 'atr': atr,
            'reasons': lr if setup == 'LONG' else sr,
            'no_trade_reason': (
                'Bearish signals dominate — price action is not currently set up for a long entry.'
                if setup == 'SHORT' else
                'Signals are mixed or neutral — no clear long opportunity at this time.'
            ),
        }
    # ── Trade levels ─────────────────────────────────────────────────
    # Only LONG reaches here (SHORT/NEUTRAL returned early above)
    entry     = current_price
    sl_struct = min(float(swing_low), float(sup1)) - atr * 0.3
    stop      = max(sl_struct, entry - atr * 2.0, entry * 0.92)  # never > 8%
    risk      = max(entry - stop, 1e-6)
    t1        = min(entry + risk * 1.5, float(res1))
    t2        = min(entry + risk * 2.5, float(res2))
    rr1       = (t1 - entry) / risk
    rr2       = (t2 - entry) / risk
    if rr1 < 1.0:
        lr.append(f"\u26a0\ufe0f Poor R:R ({rr1:.1f}:1) \u2014 resistance at {res1:.2f} limits upside")
    sl_why    = (f"Below swing low (${float(swing_low):.2f}) & support (${float(sup1):.2f}) "
                 f"with 0.3× ATR ({atr:.2f}) buffer to avoid noise")

    risk_pct = abs(entry - stop) / entry * 100

    return {
        'setup': setup, 'conf': conf, 'setup_color': sc,
        'entry': entry, 'stop': stop, 'risk': abs(entry - stop),
        'risk_pct': risk_pct, 't1': t1, 't2': t2,
        'rr1': rr1, 'rr2': rr2,
        'rsi': rsi, 'atr': atr, 'patterns': patterns,
        'reasons': reasons, 'sl_why': sl_why,
        'ls': ls, 'ss': ss, 'ma_now': ma_now,
    }


def price_action_analysis_tab(df, info_icon):
    st.markdown(
        f"<div style='border-top:1px solid {BDR};margin:0 0 1.5rem 0;'></div>",
        unsafe_allow_html=True,
    )

    zone_width = 1.5
    ma_period  = 20
    recent_df  = df.copy()
    current_price = recent_df["Close"].iloc[-1]
    _sw          = min(len(df), 60)
    recent_swing = df.tail(_sw)

    swing_high  = recent_swing["High"].max()
    swing_low   = recent_swing["Low"].min()
    higher_high = recent_df["High"].iloc[-5:].max() > recent_df["High"].iloc[-15:-5].max()
    higher_low  = recent_df["Low"].iloc[-5:].min()  > recent_df["Low"].iloc[-15:-5].min()
    lower_low   = recent_df["Low"].iloc[-5:].min()  < recent_df["Low"].iloc[-15:-5].min()
    lower_high  = recent_df["High"].iloc[-5:].max() < recent_df["High"].iloc[-15:-5].max()

    if higher_high and higher_low:
        trend, t_col = "UPTREND",   BULL
    elif lower_low and lower_high:
        trend, t_col = "DOWNTREND", BEAR
    else:
        trend, t_col = "SIDEWAYS",  NEUT

    recent_day = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
    pivot = (recent_day["High"] + recent_day["Low"] + recent_day["Close"]) / 3
    r1_pp = 2 * pivot - recent_day["Low"]
    s1_pp = 2 * pivot - recent_day["High"]
    sup1, sup2, res1, res2 = _pivot_sr(df, current_price)

    range_sz  = swing_high - swing_low
    pos_pct   = int((current_price - swing_low) / range_sz * 100) if range_sz > 0 else 50
    dist_high = (swing_high - current_price) / current_price * 100
    dist_low  = (current_price - swing_low)  / current_price * 100

    r_zone_hi = res1 + zone_width;  r_zone_lo = res1 - zone_width
    s_zone_hi = sup1 + zone_width;  s_zone_lo = sup1 - zone_width
    r_touches = _count_zone_tests(df["High"], r_zone_lo, above=True)
    s_touches = _count_zone_tests(df["Low"],  s_zone_hi, above=False)

    def _zone_strength(t):
        if t >= 5: return "STRONG",   BULL
        if t >= 3: return "MODERATE", NEUT
        return           "WEAK",      "#757575"

    r_str, r_sc = _zone_strength(r_touches)
    s_str, s_sc = _zone_strength(s_touches)
    in_r = r_zone_lo <= current_price <= r_zone_hi
    in_s = s_zone_lo <= current_price <= s_zone_hi

    # ── 1. MARKET STRUCTURE HERO ──────────────────────────────────────────────
    trend_desc = ("Higher highs & higher lows" if trend == "UPTREND"
                  else "Lower lows & lower highs" if trend == "DOWNTREND"
                  else "No clear directional bias")
    bar_bg   = "#303030"
    pos_zone = "Upper" if pos_pct >= 66 else "Lower" if pos_pct <= 33 else "Middle"
    st.markdown(
        f"""
        <div style='background:{BG2};border:1px solid {BDR};border-left:5px solid {t_col};
                    border-radius:14px;padding:1.6rem 2rem;margin-bottom:1.2rem;'>
            <div style='margin-bottom:1.4rem;'>
                <div style='font-size:0.70rem;color:#9e9e9e;text-transform:uppercase;
                            letter-spacing:1.1px;margin-bottom:0.4rem;font-weight:600;'>
                    Market Structure</div>
                <div style='font-size:3rem;font-weight:900;color:{t_col};
                            line-height:1;letter-spacing:-0.5px;'>{trend}</div>
                <div style='font-size:0.88rem;color:#9e9e9e;margin-top:0.5rem;'>{trend_desc}</div>
            </div>
            <div style='display:grid;grid-template-columns:repeat(4,1fr);
                        border-top:1px solid {BDR};padding-top:1.1rem;gap:0.75rem;'>
                <div>
                    <div style='font-size:0.67rem;color:#9e9e9e;text-transform:uppercase;
                                letter-spacing:0.6px;margin-bottom:0.35rem;'>Range Position</div>
                    <div style='font-size:1.25rem;font-weight:800;color:{t_col};'>{pos_pct}%</div>
                    <div style='font-size:0.72rem;color:#9e9e9e;margin-top:0.2rem;'>{pos_zone} of {_sw}d range</div>
                </div>
                <div>
                    <div style='font-size:0.67rem;color:#9e9e9e;text-transform:uppercase;
                                letter-spacing:0.6px;margin-bottom:0.35rem;'>Swing High</div>
                    <div style='font-size:1.25rem;font-weight:800;color:#ffffff;'>${swing_high:.2f}</div>
                    <div style='font-size:0.72rem;color:{BEAR};margin-top:0.2rem;'>↑ {dist_high:.2f}% away</div>
                </div>
                <div>
                    <div style='font-size:0.67rem;color:#9e9e9e;text-transform:uppercase;
                                letter-spacing:0.6px;margin-bottom:0.35rem;'>Swing Low</div>
                    <div style='font-size:1.25rem;font-weight:800;color:#ffffff;'>${swing_low:.2f}</div>
                    <div style='font-size:0.72rem;color:{BULL};margin-top:0.2rem;'>↓ {dist_low:.2f}% cushion</div>
                </div>
                <div>
                    <div style='font-size:0.67rem;color:#9e9e9e;text-transform:uppercase;
                                letter-spacing:0.6px;margin-bottom:0.35rem;'>Range Size</div>
                    <div style='font-size:1.25rem;font-weight:800;color:#ffffff;'>${range_sz:.2f}</div>
                    <div style='font-size:0.72rem;color:#9e9e9e;margin-top:0.2rem;'>{_sw}-day Hi–Lo spread</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 2. KEY PRICE LEVELS ───────────────────────────────────────────────────
    st.markdown(_sec("Key Price Levels", INFO), unsafe_allow_html=True)
    level_data = [
        ("Resistance 2", res2,          BEAR,      f"{(res2  - current_price)/current_price*100:+.2f}%"),
        ("Resistance 1", res1,          "#FF7A7A",  f"{(res1  - current_price)/current_price*100:+.2f}%"),
        ("Pivot R1",     r1_pp,         NEUT,      f"{(r1_pp - current_price)/current_price*100:+.2f}%"),
        ("Current",      current_price, INFO,      "\u2014"),
        ("Pivot S1",     s1_pp,         "#7BDFB8",  f"{(s1_pp - current_price)/current_price*100:+.2f}%"),
        ("Support 1",    sup1,          BULL,      f"{(sup1  - current_price)/current_price*100:+.2f}%"),
        ("Support 2",    sup2,          "#26A69A",  f"{(sup2  - current_price)/current_price*100:+.2f}%"),
    ]
    cols = st.columns(len(level_data), gap="small")
    for col, (label, price, color, dist) in zip(cols, level_data):
        with col:
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:3px solid {color};border-radius:12px;"
                f"padding:0.9rem 0.7rem;text-align:center;'>"
                f"<div style='font-size:0.72rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.6px;margin-bottom:0.4rem;'>{label}</div>"
                f"<div style='font-size:1.15rem;font-weight:800;color:{color};'>${price:.2f}</div>"
                f"<div style='font-size:0.75rem;color:#757575;margin-top:0.2rem;'>{dist}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── 3. REACTION ZONES ────────────────────────────────────────────────────
    st.markdown(_sec("Key Reaction Zones", PURP), unsafe_allow_html=True)
    zc1, zc2 = st.columns(2, gap="medium")
    for col, lvl, sc, strength_str, touches, zone_lo, zone_hi, label in [
        (zc1, res1, r_sc, r_str, r_touches, r_zone_lo, r_zone_hi, "Resistance Zone"),
        (zc2, sup1, s_sc, s_str, s_touches, s_zone_lo, s_zone_hi, "Support Zone"),
    ]:
        col_accent = BEAR if label == "Resistance Zone" else BULL
        in_zone    = zone_lo <= current_price <= zone_hi
        in_html    = (f"<span style='color:{NEUT};font-weight:700;'>&#9889; IN ZONE</span>" if in_zone
                      else f"<span style='color:#757575;'>Outside</span>")
        with col:
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{col_accent}0d,{BG2});"
                f"border:1px solid {col_accent}30;border-left:4px solid {col_accent};"
                f"border-radius:16px;padding:1.5rem 1.6rem;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"margin-bottom:0.8rem;'>"
                f"<div style='font-size:0.78rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.8px;font-weight:700;'>{label}</div>"
                f"{in_html}</div>"
                f"<div style='font-size:2rem;font-weight:900;color:{col_accent};'>${lvl:.2f}</div>"
                f"<div style='font-size:0.82rem;color:#9e9e9e;margin:0.25rem 0 1rem;'>"
                f"Band: ${zone_lo:.2f} \u2013 ${zone_hi:.2f}</div>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;'>"
                f"<div style='background:{BG};border-radius:10px;padding:0.7rem 0.9rem;'>"
                f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                f"letter-spacing:0.5px;margin-bottom:0.2rem;'>Strength</div>"
                f"<div style='font-size:1rem;font-weight:700;color:{sc};'>{strength_str}</div>"
                f"</div>"
                f"<div style='background:{BG};border-radius:10px;padding:0.7rem 0.9rem;'>"
                f"<div style='font-size:0.72rem;color:#757575;text-transform:uppercase;"
                f"letter-spacing:0.5px;margin-bottom:0.2rem;'>Touches</div>"
                f"<div style='font-size:1rem;font-weight:700;color:{NEUT};'>{touches}</div>"
                f"</div></div>"
                f"<div style='margin-top:0.8rem;'>{_glowbar(min(touches*20,100), col_accent, '5px')}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── 4. TRADE SETUP (above chart) ─────────────────────────────────────────
    ma = recent_df["Close"].rolling(window=ma_period).mean()
    st.markdown(_sec("Trade Setup", BULL), unsafe_allow_html=True)

    ts = _compute_trade_setup(
        df=recent_df, current_price=current_price, trend=trend,
        sup1=sup1, sup2=sup2, res1=res1, res2=res2,
        swing_low=swing_low, swing_high=swing_high,
        ma_series=ma, s_touches=s_touches, r_touches=r_touches,
        s_str=s_str, r_str=r_str, in_s=in_s, in_r=in_r,
    )

    if ts is None:
        st.info("Need at least 15 bars of data to compute a trade setup.")
    elif ts.get('no_trade'):
        # ── No valid long setup ──
        dominant = ts['setup']
        dom_col  = BEAR if dominant == 'SHORT' else NEUT
        dom_icon = '▼ Bearish' if dominant == 'SHORT' else '◆ Neutral'
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {dom_col}33;"
            f"border-left:5px solid {dom_col};border-radius:14px;"
            f"padding:1.5rem 2rem;'>"
            f"<div style='font-size:0.65rem;color:#9e9e9e;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Price Action Trade Scan</div>"
            f"<div style='font-size:2rem;font-weight:900;color:{dom_col};"
            f"letter-spacing:-0.5px;margin-bottom:0.5rem;'>NO TRADE — {dom_icon}</div>"
            f"<div style='font-size:0.88rem;color:#9e9e9e;margin-bottom:1rem;'>"
            f"{ts['no_trade_reason']}</div>"
            f"<div style='border-top:1px solid {BDR};padding-top:0.8rem;"
            f"display:grid;grid-template-columns:1fr 1fr;gap:0.6rem;'>"
            f"<div style='background:{BG};border-radius:10px;padding:0.7rem 0.9rem;'>"
            f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:0.5px;margin-bottom:0.2rem;'>Bull Signal Score</div>"
            f"<div style='font-size:1.1rem;font-weight:800;color:{BULL};'>{ts['ls']} pts</div></div>"
            f"<div style='background:{BG};border-radius:10px;padding:0.7rem 0.9rem;'>"
            f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:0.5px;margin-bottom:0.2rem;'>Bear Signal Score</div>"
            f"<div style='font-size:1.1rem;font-weight:800;color:{BEAR};'>{ts['ss']} pts</div></div>"
            f"</div>"
            f"<div style='font-size:0.72rem;color:#555;margin-top:0.8rem;'>"
            f"RSI {ts['rsi']:.0f} · ATR {ts['atr']:.2f} SAR · "
            f"A valid long setup requires bull signals to clearly outweigh bear signals.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        sc   = ts['setup_color']
        setup = ts['setup']
        conf  = ts['conf']
        icon  = '▲ LONG'
        conf_bar_cl = BULL

        # Signal strength text
        if   conf >= 75: sig_txt = 'High Confidence'
        elif conf >= 60: sig_txt = 'Moderate Confidence'
        else:            sig_txt = 'Low Confidence'

        # ── Hero banner ──
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {BDR};"
            f"border-left:5px solid {sc};border-radius:14px;"
            f"padding:1.5rem 2rem;margin-bottom:1rem;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"margin-bottom:1rem;'>"
            f"<div>"
            f"<div style='font-size:0.65rem;color:#9e9e9e;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.3rem;'>Price Action Trade Setup</div>"
            f"<div style='font-size:2.6rem;font-weight:900;color:{sc};"
            f"letter-spacing:-1px;line-height:1;'>{icon}</div>"
            f"<div style='font-size:0.82rem;color:#9e9e9e;margin-top:0.4rem;'>"
            f"{sig_txt}</div>"
            f"</div>"
            f"<div style='text-align:right;'>"
            f"<div style='font-size:0.65rem;color:#9e9e9e;margin-bottom:0.3rem;"
            f"text-transform:uppercase;letter-spacing:1px;'>Signal Confidence</div>"
            f"<div style='font-size:3rem;font-weight:900;color:{sc};"
            f"line-height:1;letter-spacing:-2px;'>{conf}%</div>"
            f"</div>"
            f"</div>"
            # Confidence bar
            f"<div style='background:{BDR};border-radius:999px;height:6px;"
            f"overflow:hidden;margin-bottom:0.5rem;'>"
            f"<div style='width:{conf}%;height:100%;"
            f"background:linear-gradient(90deg,{conf_bar_cl}66,{conf_bar_cl});"
            f"border-radius:999px;'></div></div>"
            f"<div style='font-size:0.65rem;color:#555;'>"
            f"Long signals: {ts['ls']} pts &nbsp;|&nbsp; Short signals: {ts['ss']} pts</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # ── Price Ladder (BUY only) ──────────────────────────────────────────
        if sc == BULL:
            try:
                from _levels import price_ladder_html as _pa_plh
                _pa_R  = abs(ts["entry"] - ts["stop"])
                _pa_t3 = round(ts["entry"] + _pa_R * 5.0, 2)
                st.markdown(_pa_plh(ts["entry"], ts["stop"], ts["t1"], ts["t2"], _pa_t3, True), unsafe_allow_html=True)
            except Exception:
                pass

        # ── Five. CHART

    # ── 5. CHART ─────────────────────────────────────────────────────────────
    st.markdown(_sec("Price Action Chart — Candles · MA · Volume · Zones", INFO), unsafe_allow_html=True)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.78, 0.22], vertical_spacing=0.03,
    )
    fig.add_trace(go.Candlestick(
        x=recent_df.index,
        open=recent_df["Open"], high=recent_df["High"],
        low=recent_df["Low"],   close=recent_df["Close"],
        name="Price",
        increasing_fillcolor="rgba(0,200,150,0.4)",
        decreasing_fillcolor="rgba(255,77,109,0.4)",
        increasing_line_color=BULL,
        decreasing_line_color=BEAR,
    ), row=1, col=1)
    fig.add_hrect(y0=r_zone_lo, y1=r_zone_hi, fillcolor="rgba(255,77,109,0.08)",
                  layer="below", annotation_text="Resistance", annotation_position="right",
                  annotation=dict(font_color=BEAR, font_size=11),
                  row=1, col=1)
    fig.add_hrect(y0=s_zone_lo, y1=s_zone_hi, fillcolor="rgba(0,200,150,0.08)",
                  layer="below", annotation_text="Support", annotation_position="right",
                  annotation=dict(font_color=BULL, font_size=11),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=recent_df.index, y=ma, name=f"{ma_period}-MA",
                             line=dict(color="#FFC107", width=2)),
                  row=1, col=1)
    # Volume bars
    if 'Volume' in recent_df.columns:
        vol_colors = [BULL if c >= o else BEAR
                      for c, o in zip(recent_df['Close'], recent_df['Open'])]
        fig.add_trace(go.Bar(
            x=recent_df.index, y=recent_df['Volume'],
            name='Volume', marker_color=vol_colors,
            marker_line_width=0, opacity=0.5, showlegend=False,
        ), row=2, col=1)
    # Entry / stop / targets on chart if a valid LONG setup exists
    if ts is not None and not ts.get('no_trade'):
        fig.add_hline(y=ts['entry'], line_color="rgba(33,150,243,0.7)",
                      line_dash="dot", line_width=1.5,
                      annotation_text=f"  Entry {ts['entry']:.2f}",
                      annotation_font_color=INFO, row=1, col=1)
        fig.add_hline(y=ts['stop'], line_color="rgba(244,67,54,0.7)",
                      line_dash="dash", line_width=1.5,
                      annotation_text=f"  Stop {ts['stop']:.2f}",
                      annotation_font_color=BEAR, row=1, col=1)
        fig.add_hline(y=ts['t1'], line_color="rgba(76,175,80,0.6)",
                      line_dash="dot", line_width=1.2,
                      annotation_text=f"  T1 {ts['t1']:.2f}",
                      annotation_font_color=BULL, row=1, col=1)
        fig.add_hline(y=ts['t2'], line_color="rgba(139,195,74,0.5)",
                      line_dash="dot", line_width=1.2,
                      annotation_text=f"  T2 {ts['t2']:.2f}",
                      annotation_font_color="#8BC34A", row=1, col=1)
    else:
        fig.add_hline(y=current_price, line_color="rgba(74,158,255,0.5)",
                      line_dash="dot", line_width=1.5,
                      annotation_text=f"  {current_price:.2f}",
                      annotation_font_color=INFO, row=1, col=1)
    fig.update_xaxes(gridcolor=BDR, showline=False, zeroline=False,
                     tickfont=dict(color="#757575"))
    fig.update_yaxes(gridcolor=BDR, showline=False, zeroline=False,
                     tickfont=dict(color="#757575"))
    fig.update_layout(
        height=620, plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(color="#e0e0e0", family="Inter, Arial, sans-serif", size=12),
        hovermode="x unified", xaxis_rangeslider=dict(visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="right", x=1, font=dict(color="#9e9e9e"),
                    bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=10, b=10, l=40, r=60),
        bargap=0.1,
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC GETTER — called from Decision Tab
# ══════════════════════════════════════════════════════════════════════════════

def get_pa_signal(df, cp):
    """Return a BUY signal dict for the Decision Tab, or None if no trade."""
    if df is None or len(df) < 15:
        return None
    try:
        df = df.copy()
        zone_width   = 1.5
        _sw          = min(len(df), 60)
        recent_swing = df.tail(_sw)
        swing_high   = float(recent_swing["High"].max())
        swing_low    = float(recent_swing["Low"].min())

        hh = float(df["High"].iloc[-5:].max()) > float(df["High"].iloc[-15:-5].max())
        hl = float(df["Low"].iloc[-5:].min())  > float(df["Low"].iloc[-15:-5].min())
        ll = float(df["Low"].iloc[-5:].min())  < float(df["Low"].iloc[-15:-5].min())
        lh = float(df["High"].iloc[-5:].max()) < float(df["High"].iloc[-15:-5].max())

        if hh and hl:   trend = "UPTREND"
        elif ll and lh: trend = "DOWNTREND"
        else:           trend = "SIDEWAYS"

        sup1, sup2, res1, res2 = _pivot_sr(df, float(cp))
        r_zone_lo = res1 - zone_width
        s_zone_hi = sup1 + zone_width
        r_touches = _count_zone_tests(df["High"], r_zone_lo, above=True)
        s_touches = _count_zone_tests(df["Low"],  s_zone_hi, above=False)

        def _zstr(t):
            return "STRONG" if t >= 5 else ("MODERATE" if t >= 3 else "WEAK")

        r_str = _zstr(r_touches); s_str = _zstr(s_touches)
        in_r  = (res1 - zone_width) <= float(cp) <= (res1 + zone_width)
        in_s  = (sup1 - zone_width) <= float(cp) <= (sup1 + zone_width)
        ma_series = df["Close"].rolling(20, min_periods=1).mean()

        setup = _compute_trade_setup(
            df, float(cp), trend, sup1, sup2, res1, res2,
            swing_low, swing_high, ma_series,
            s_touches, r_touches, s_str, r_str, in_s, in_r,
        )
        if setup is None or setup.get("no_trade"):
            return None

        _risk = max(setup["entry"] - setup["stop"], 0.001)
        _t3   = round(setup["entry"] + _risk * 4.236, 2)
        return dict(
            color=BULL,
            verdict_text="▲ LONG",
            sublabel=f"Price Action Trade Setup — {trend}",
            conf=setup["conf"],
            reasons=setup["reasons"][:3],
            entry=setup["entry"],
            stop=round(setup["stop"], 2),
            t1=round(setup["t1"], 2),
            t2=round(setup["t2"], 2),
            t3=_t3,
        )
    except Exception:
        return None
