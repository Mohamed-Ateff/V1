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


# ══════════════════════════════════════════════════════════════════════════════
#  VOLUME PROFILE COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def _compute_volume_profile(df, bins=40):
    hi_all = float(df["High"].max())
    lo_all = float(df["Low"].min())
    if hi_all <= lo_all:
        return None

    price_range = hi_all - lo_all
    bin_size    = price_range / bins
    edges       = [lo_all + i * bin_size for i in range(bins + 1)]
    mids        = [(edges[i] + edges[i + 1]) / 2 for i in range(bins)]
    vols        = [0.0] * bins

    for _, row in df.iterrows():
        bar_lo  = float(row["Low"])
        bar_hi  = float(row["High"])
        bar_vol = float(row.get("Volume", 0) or 0)
        if bar_vol <= 0 or bar_hi <= bar_lo:
            continue
        for b in range(bins):
            overlap_lo = max(bar_lo, edges[b])
            overlap_hi = min(bar_hi, edges[b + 1])
            if overlap_hi > overlap_lo:
                vols[b] += bar_vol * (overlap_hi - overlap_lo) / (bar_hi - bar_lo)

    total_vol = sum(vols)
    if total_vol == 0:
        return None

    poc_idx = int(np.argmax(vols))
    poc     = mids[poc_idx]

    # Value Area — 70% of total volume centred on POC
    va_target = total_vol * 0.70
    va_vol    = vols[poc_idx]
    lo_idx    = poc_idx
    hi_idx    = poc_idx
    while va_vol < va_target:
        expand_up   = vols[hi_idx + 1] if hi_idx + 1 < bins else 0
        expand_down = vols[lo_idx - 1] if lo_idx - 1 >= 0  else 0
        if expand_up >= expand_down and hi_idx + 1 < bins:
            hi_idx += 1
            va_vol += vols[hi_idx]
        elif lo_idx - 1 >= 0:
            lo_idx -= 1
            va_vol += vols[lo_idx]
        else:
            break

    vah = mids[hi_idx]
    val = mids[lo_idx]

    vol_arr    = np.array(vols)
    nonzero    = vol_arr[vol_arr > 0]
    hvn_thresh = float(np.percentile(nonzero, 80)) if len(nonzero) else 0
    lvn_thresh = float(np.percentile(nonzero, 20)) if len(nonzero) else 0
    hvns = [mids[i] for i in range(bins) if vols[i] >= hvn_thresh]
    lvns = [mids[i] for i in range(bins) if 0 < vols[i] <= lvn_thresh]

    vwap = float(
        (df["Close"] * df["Volume"]).sum() / df["Volume"].sum()
    ) if "Volume" in df.columns and df["Volume"].sum() > 0 else float(df["Close"].mean())

    return dict(poc=poc, vah=vah, val=val, hvns=hvns, lvns=lvns,
                vwap=vwap, mids=mids, vols=vols,
                total=total_vol, bin_size=bin_size, hi=hi_all, lo=lo_all)


# ══════════════════════════════════════════════════════════════════════════════
#  SIGNAL ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _vp_signal(vp, current_price, df):
    poc  = vp["poc"];  vah = vp["vah"];  val = vp["val"];  vwap = vp["vwap"]
    cp   = current_price

    h, l, c = df["High"], df["Low"], df["Close"]
    tr  = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14, min_periods=1).mean().iloc[-1])
    if not np.isfinite(atr) or atr <= 0:
        atr = float((h - l).mean())

    recent_vol = float(df["Volume"].iloc[-3:].mean()) if "Volume" in df.columns else 1
    avg_vol    = float(df["Volume"].iloc[-20:].mean()) if "Volume" in df.columns else 1
    low_vol    = recent_vol < avg_vol * 0.85
    last_bull  = float(df["Close"].iloc[-1]) > float(df["Open"].iloc[-1]) if "Open" in df.columns else True

    score   = 0
    reasons = []
    zone    = ""

    near_val  = abs(cp - val) / max(val,  0.01) < 0.025   # within 2.5%
    near_poc  = abs(cp - poc) / max(poc,  0.01) < 0.025   # within 2.5%
    near_vah  = abs(cp - vah) / max(vah,  0.01) < 0.025
    above_poc = cp > poc
    above_vah = cp > vah
    below_val = cp < val
    in_va     = val <= cp <= vah

    # Zone base score
    if above_vah:
        zone = "Above VAH — extended above value"
        reasons.append(f"Price ({cp:.2f}) is above VAH ({vah:.2f}) — extended, risk of reversal but breakout possible")
        score += 15
    elif near_vah:
        zone = "VAH — Supply Ceiling"
        reasons.append(f"Price ({cp:.2f}) at VAH ({vah:.2f}) — near supply zone, tighter stop needed")
        score += 25
    elif near_poc:
        zone = "POC — Point of Control"
        reasons.append(f"Price ({cp:.2f}) at POC ({poc:.2f}) — max-volume decision level, strong directional edge")
        score += 45
    elif near_val:
        zone = "VAL — Value Area Low (Demand)"
        reasons.append(f"Price ({cp:.2f}) at VAL ({val:.2f}) — historically strong demand zone, buyers defend this level")
        score += 50
    elif below_val:
        zone = "Below VAL — Discounted vs Fair Value"
        reasons.append(f"Price ({cp:.2f}) below VAL ({val:.2f}) — trading below fair value, potential accumulation")
        score += 35
    elif above_poc and in_va:
        zone = "Upper Value Area — Bullish Bias"
        reasons.append(f"Price between POC ({poc:.2f}) and VAH ({vah:.2f}) — inside value, buyers in structural control")
        score += 35
    else:  # between val and poc
        zone = "Lower Value Area — Near Demand"
        reasons.append(f"Price between VAL ({val:.2f}) and POC ({poc:.2f}) — accumulation zone, demand building")
        score += 40

    # VWAP confirmation
    if cp > vwap:
        score += 10
        reasons.append(f"Price ({cp:.2f}) above VWAP ({vwap:.2f}) — bullish session bias confirmed")
    else:
        score -= 5
        reasons.append(f"Price ({cp:.2f}) below VWAP ({vwap:.2f}) — short-term selling pressure; wait for reclaim")

    # Volume context
    if low_vol:
        score += 10
        reasons.append("Recent volume below average — low-vol pullback is a classic high R:R entry condition")

    # Candle direction
    if last_bull:
        score += 10
        reasons.append("Last candle closed bullish — short-term momentum confirms active buyers")
    else:
        score -= 5
        reasons.append("Last candle closed bearish — consider waiting for a bullish reversal candle")

    # LVN trap
    lvns_below = [v for v in vp["lvns"] if v < cp]
    if lvns_below and abs(cp - max(lvns_below)) / max(cp, 0.01) < 0.02:
        score -= 10
        reasons.append(f"LVN at {max(lvns_below):.2f} just below — thin volume, price can drop fast through it")

    # Signal determination
    if above_vah and last_bull and cp > vwap:
        signal = "BUY"   # breakout continuation above value area
    elif score >= 50 and not near_vah:
        signal = "BUY"
    elif score >= 30:
        signal = "WATCH"
    else:
        signal = "NO TRADE"

    # Trade levels
    if signal in ("BUY", "WATCH"):
        entry = cp
        stop  = max(val - atr * 0.5, cp - atr * 2.0) if not below_val else cp - atr * 1.5
        t1    = poc if cp < poc else vah
        t2    = vah if cp < poc else vah + (vah - poc)
    else:
        entry = cp
        stop  = cp - atr * 1.5
        t1    = poc
        t2    = vah

    risk = abs(entry - stop)
    rr1  = round(abs(t1 - entry) / risk, 2) if risk > 0 else 0
    rr2  = round(abs(t2 - entry) / risk, 2) if risk > 0 else 0

    return dict(signal=signal, score=score, zone=zone,
                entry=entry, stop=stop, t1=t1, t2=t2,
                rr1=rr1, rr2=rr2, atr=atr, vwap=vwap, reasons=reasons)


# ══════════════════════════════════════════════════════════════════════════════
#  CHART
# ══════════════════════════════════════════════════════════════════════════════

def _build_vp_chart(df, vp, sig, current_price, tail=90):
    sub = df.tail(tail).copy()
    sub["Date"] = pd.to_datetime(sub["Date"])
    xh = list(sub["Date"])

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.78, 0.22],
        shared_yaxes=True,
        horizontal_spacing=0.008,
    )

    if all(col in df.columns for col in ["Open", "High", "Low"]):
        fig.add_trace(go.Candlestick(
            x=xh,
            open=sub["Open"].values, high=sub["High"].values,
            low=sub["Low"].values,   close=sub["Close"].values,
            name="OHLC",
            increasing_line_color=BULL, decreasing_line_color=BEAR,
            increasing_fillcolor="rgba(76,175,80,0.28)",
            decreasing_fillcolor="rgba(244,67,54,0.28)",
            line_width=0.8,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=xh, y=list(sub["Close"].values),
            mode="lines", name="Price",
            line=dict(color=INFO, width=1.8),
        ), row=1, col=1)

    if "EMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=xh, y=list(df["EMA_20"].values[-tail:]),
            mode="lines", name="EMA 20",
            line=dict(color="#4A9EFF", width=1.1, dash="dot"),
        ), row=1, col=1)

    poc, vah, val, vwap = vp["poc"], vp["vah"], vp["val"], vp["vwap"]
    for level, color, label, dash in [
        (poc,  "#FFD700", f"POC {poc:.2f}",   "solid"),
        (vah,  BEAR,      f"VAH {vah:.2f}",   "dash"),
        (val,  BULL,      f"VAL {val:.2f}",   "dash"),
        (vwap, PURP,      f"VWAP {vwap:.2f}", "dot"),
    ]:
        fig.add_hline(y=level, line_dash=dash, line_color=color, line_width=1.2,
                      opacity=0.85, annotation_text=label,
                      annotation_font_color=color, annotation_font_size=9,
                      row=1, col=1)

    if sig["signal"] in ("BUY", "WATCH"):
        fig.add_hline(y=sig["stop"], line_dash="dash", line_color=BEAR,
                      line_width=0.9, opacity=0.60,
                      annotation_text=f"SL {sig['stop']:.2f}",
                      annotation_font_color=BEAR, annotation_font_size=9, row=1, col=1)
        fig.add_hline(y=sig["t1"], line_dash="dot", line_color=BULL,
                      line_width=0.9, opacity=0.60,
                      annotation_text=f"T1 {sig['t1']:.2f}",
                      annotation_font_color=BULL, annotation_font_size=9, row=1, col=1)
        fig.add_hline(y=sig["t2"], line_dash="dot", line_color="#8BC34A",
                      line_width=0.9, opacity=0.60,
                      annotation_text=f"T2 {sig['t2']:.2f}",
                      annotation_font_color="#8BC34A", annotation_font_size=9, row=1, col=1)

    fig.add_hrect(y0=val, y1=vah, fillcolor="rgba(33,150,243,0.05)",
                  line_width=0, row=1, col=1)

    mids    = vp["mids"]
    vols_l  = vp["vols"]
    max_v   = max(vols_l) if vols_l else 1
    vol_arr = np.array(vols_l)
    nonzero = vol_arr[vol_arr > 0]
    p80 = float(np.percentile(nonzero, 80)) if len(nonzero) else 0
    p20 = float(np.percentile(nonzero, 20)) if len(nonzero) else 0

    bar_colors = []
    for i, m in enumerate(mids):
        if abs(m - poc) < vp["bin_size"] / 2:
            bar_colors.append("#FFD700")
        elif val <= m <= vah:
            bar_colors.append("rgba(33,150,243,0.55)")
        elif vols_l[i] >= p80:
            bar_colors.append("rgba(76,175,80,0.55)")
        elif vols_l[i] <= p20 and vols_l[i] > 0:
            bar_colors.append("rgba(244,67,54,0.35)")
        else:
            bar_colors.append("rgba(120,120,120,0.40)")

    fig.add_trace(go.Bar(
        x=[v / max_v for v in vols_l], y=mids,
        orientation="h", name="Vol by Price",
        marker_color=bar_colors, showlegend=False,
        hovertemplate="Price: %{y:.2f}<br>Vol: %{customdata:,.0f}<extra></extra>",
        customdata=vols_l,
    ), row=1, col=2)

    fig.update_layout(
        height=520, margin=dict(t=10, b=10, l=8, r=12),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color="#e0e0e0", family="Inter, Arial, sans-serif", size=12),
        hovermode="y unified",
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BDR, borderwidth=1,
                    font=dict(size=9, color="#9e9e9e"), x=0.01, y=0.99,
                    orientation="h", yanchor="top"),
        xaxis_rangeslider_visible=False,
    )
    for ci in [1, 2]:
        fig.update_xaxes(gridcolor=BDR, showgrid=True, zeroline=False, row=1, col=ci)
        fig.update_yaxes(gridcolor=BDR, showgrid=True, zeroline=False, row=1, col=ci)
    fig.update_xaxes(showticklabels=False, row=1, col=2)
    for ann in (fig.layout.annotations or []):
        if hasattr(ann, "font"):
            ann.font.size = 9
            ann.font.color = "#9e9e9e"
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TAB
# ══════════════════════════════════════════════════════════════════════════════

def volume_profile_tab(df, current_price):
    global BG, BG2, BDR
    theme = st.session_state.get("theme_palette", {})
    BG  = theme.get("panel",     BG)
    BG2 = theme.get("panel_alt", BG2)
    BDR = theme.get("border",    BDR)

    if len(df) < 30:
        st.warning("Need at least 30 bars for Volume Profile.")
        return
    if "Volume" not in df.columns or df["Volume"].sum() == 0:
        st.warning("No volume data available for this symbol.")
        return

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    vp = _compute_volume_profile(df, bins=40)
    if vp is None:
        st.error("Volume Profile calculation failed.")
        return

    sig = _vp_signal(vp, current_price, df)
    poc = vp["poc"];  vah = vp["vah"];  val = vp["val"];  vwap = vp["vwap"]

    if sig["signal"] == "BUY":
        sig_col = BULL;  sig_left = BULL;  sig_icon = "▲ BUY"
    elif sig["signal"] == "WATCH":
        sig_col = NEUT;  sig_left = NEUT;  sig_icon = "◆ WATCH"
    else:
        sig_col = "#555"; sig_left = "#444"; sig_icon = "⚫ NO TRADE"

    score_c = BULL if sig["score"] >= 60 else NEUT if sig["score"] >= 40 else "#555"

    # ══ 1. HERO ═══════════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='background:{BG2};border:1px solid {BDR};"
        f"border-left:5px solid {sig_left};border-radius:14px;"
        f"padding:1.6rem 2rem;margin-bottom:1.2rem;'>"
        f"<div style='margin-bottom:1.4rem;'>"
        f"<div style='font-size:0.70rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:1.1px;margin-bottom:0.4rem;font-weight:600;'>"
        f"Volume Profile Signal</div>"
        f"<div style='font-size:3rem;font-weight:900;color:{sig_col};"
        f"line-height:1;letter-spacing:-0.5px;'>{sig_icon}</div>"
        f"<div style='font-size:0.88rem;color:#9e9e9e;margin-top:0.5rem;'>"
        f"{sig['zone']}</div>"
        f"</div>"
        f"<div style='margin-bottom:1rem;'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:0.3rem;'>"
        f"<span style='font-size:0.67rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:0.6px;'>Confluence Score</span>"
        f"<span style='font-size:0.82rem;font-weight:800;color:{score_c};'>{sig['score']}/100</span>"
        f"</div>"
        + _glowbar(sig["score"], score_c, "6px") +
        f"</div>"
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);"
        f"border-top:1px solid {BDR};padding-top:1.1rem;gap:0.75rem;'>"
        + "".join([
            f"<div>"
            f"<div style='font-size:0.67rem;color:#9e9e9e;text-transform:uppercase;"
            f"letter-spacing:0.6px;margin-bottom:0.35rem;'>{ln}</div>"
            f"<div style='font-size:1.25rem;font-weight:800;color:{lc};'>${lv:.2f}</div>"
            f"<div style='font-size:0.72rem;color:#9e9e9e;margin-top:0.2rem;'>{ls}</div>"
            f"</div>"
            for ln, lv, lc, ls in [
                ("VAL — Demand Floor",    val,  BULL,      f"{(val  / current_price - 1)*100:+.2f}% from price"),
                ("POC — Max Volume",      poc,  "#FFD700", f"{(poc  / current_price - 1)*100:+.2f}% from price"),
                ("VAH — Supply Ceiling",  vah,  BEAR,      f"{(vah  / current_price - 1)*100:+.2f}% from price"),
                ("VWAP — Fair Value",     vwap, PURP,      f"{(vwap / current_price - 1)*100:+.2f}% from price"),
            ]
        ]) +
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ══ 2. KEY PRICE LEVELS — Volume Based ═══════════════════════════════════
    st.markdown(_sec("Key Price Levels — Volume Based", PURP), unsafe_allow_html=True)

    hvns_above = sorted([v for v in vp["hvns"] if v > current_price])
    hvns_below = sorted([v for v in vp["hvns"] if v < current_price], reverse=True)
    lvns_above = sorted([v for v in vp["lvns"] if v > current_price])
    lvns_below = sorted([v for v in vp["lvns"] if v < current_price], reverse=True)

    level_data = [
        ("HVN Above",  hvns_above[0] if hvns_above else None, BEAR,      "Strong resistance"),
        ("VAH",        vah,                                    BEAR,      "Supply ceiling"),
        ("POC",        poc,                                    "#FFD700", "Max volume"),
        ("Current",    current_price,                          INFO,      "—"),
        ("VAL",        val,                                    BULL,      "Demand floor"),
        ("HVN Below",  hvns_below[0] if hvns_below else None,  BULL,      "Strong support"),
    ]

    cols = st.columns(len(level_data), gap="small")
    for col, (label, price, color, desc) in zip(cols, level_data):
        with col:
            if price is None:
                st.markdown(
                    f"<div style='background:{BG2};border:1px solid {BDR};"
                    f"border-top:3px solid #333;border-radius:12px;"
                    f"padding:0.9rem 0.7rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#555;text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-bottom:0.4rem;'>{label}</div>"
                    f"<div style='font-size:1.15rem;font-weight:800;color:#444;'>—</div>"
                    f"<div style='font-size:0.62rem;color:#444;margin-top:0.2rem;'>{desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                dist = f"{(price / current_price - 1)*100:+.2f}%"
                st.markdown(
                    f"<div style='background:{BG2};border:1px solid {BDR};"
                    f"border-top:3px solid {color};border-radius:12px;"
                    f"padding:0.9rem 0.7rem;text-align:center;'>"
                    f"<div style='font-size:0.72rem;color:#9e9e9e;text-transform:uppercase;"
                    f"letter-spacing:0.6px;margin-bottom:0.4rem;'>{label}</div>"
                    f"<div style='font-size:1.15rem;font-weight:800;color:{color};'>${price:.2f}</div>"
                    f"<div style='font-size:0.75rem;color:#757575;margin-top:0.2rem;'>{dist}</div>"
                    f"<div style='font-size:0.62rem;color:#555;margin-top:0.1rem;'>{desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    if lvns_above and abs(lvns_above[0] - current_price) / max(current_price, 1) < 0.03:
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {NEUT}44;"
            f"border-left:3px solid {NEUT};border-radius:10px;"
            f"padding:0.65rem 1rem;margin-top:0.6rem;"
            f"font-size:0.78rem;color:#9e9e9e;'>"
            f"<span style='color:{NEUT};font-weight:700;'>LVN just above ({lvns_above[0]:.2f}): </span>"
            f"Thin volume — price can accelerate quickly if this level breaks upward.</div>",
            unsafe_allow_html=True,
        )
    if lvns_below and abs(lvns_below[0] - current_price) / max(current_price, 1) < 0.03:
        st.markdown(
            f"<div style='background:{BG2};border:1px solid {BEAR}44;"
            f"border-left:3px solid {BEAR};border-radius:10px;"
            f"padding:0.65rem 1rem;margin-top:0.6rem;"
            f"font-size:0.78rem;color:#9e9e9e;'>"
            f"<span style='color:{BEAR};font-weight:700;'>LVN just below ({lvns_below[0]:.2f}): </span>"
            f"Thin volume below — could drop fast if this level breaks.</div>",
            unsafe_allow_html=True,
        )

    # ══ 3. TRADE SETUP ════════════════════════════════════════════════════════
    st.markdown(_sec("Trade Setup — Entry · Stop Loss · Targets", sig_col), unsafe_allow_html=True)

    if sig["signal"] in ("BUY", "WATCH"):
        sl_pct   = (sig["stop"] / sig["entry"] - 1) * 100
        t1_pct   = (sig["t1"]   / sig["entry"] - 1) * 100
        t2_pct   = (sig["t2"]   / sig["entry"] - 1) * 100
        conf_pct = min(100, max(0, int(sig["score"] / 80 * 100)))

        def _lr(label, price, color, is_cur=False):
            bdr = f"border:1px solid {color};" if is_cur else f"border:1px solid {BDR};"
            bg  = BG if is_cur else BG2
            return (
                f"<div style='display:flex;justify-content:space-between;align-items:center;"
                f"{bdr}border-radius:8px;padding:0.45rem 0.8rem;margin-bottom:0.32rem;"
                f"background:{bg};'>"
                f"<span style='font-size:0.62rem;color:#666;font-weight:600;"
                f"text-transform:uppercase;letter-spacing:0.5px;'>{label}</span>"
                f"<span style='font-size:0.88rem;font-weight:900;color:{color};'>{price:.2f}</span>"
                f"</div>"
            )

        lad_col, met_col = st.columns(2, gap="medium")

        with lad_col:
            ladder = (
                _lr("TARGET 2",  sig["t2"],      '#8BC34A')
              + _lr("TARGET 1",  sig["t1"],      BULL)
              + _lr("PRICE",     current_price,  '#FFD700', is_cur=True)
              + _lr("ENTRY",     sig["entry"],   INFO)
              + _lr("STOP LOSS", sig["stop"],    BEAR)
            )
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:3px solid {sig_col};border-radius:14px;"
                f"padding:1.2rem 1.2rem;'>"
                f"<div style='font-size:0.56rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:1px;font-weight:700;margin-bottom:0.8rem;'>Price Ladder</div>"
                f"{ladder}"
                f"</div>",
                unsafe_allow_html=True,
            )

        with met_col:
            stats_rows = (
                f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
                f"border-bottom:1px solid {BDR};'>"
                f"<span style='font-size:0.68rem;color:#666;'>Stop risk</span>"
                f"<span style='font-size:0.78rem;font-weight:800;color:{BEAR};'>{sl_pct:.1f}%</span></div>"

                f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
                f"border-bottom:1px solid {BDR};'>"
                f"<span style='font-size:0.68rem;color:#666;'>Target 1 gain</span>"
                f"<span style='font-size:0.78rem;font-weight:800;color:{BULL};'>+{t1_pct:.1f}%</span></div>"

                f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
                f"border-bottom:1px solid {BDR};'>"
                f"<span style='font-size:0.68rem;color:#666;'>Target 2 gain</span>"
                f"<span style='font-size:0.78rem;font-weight:800;color:#8BC34A;'>+{t2_pct:.1f}%</span></div>"

                f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;"
                f"border-bottom:1px solid {BDR};'>"
                f"<span style='font-size:0.68rem;color:#666;'>R:R to T1</span>"
                f"<span style='font-size:0.78rem;font-weight:800;color:{BULL};'>{sig['rr1']:.1f}:1</span></div>"

                f"<div style='display:flex;justify-content:space-between;padding:0.38rem 0;'>"
                f"<span style='font-size:0.68rem;color:#666;'>R:R to T2</span>"
                f"<span style='font-size:0.78rem;font-weight:800;color:#8BC34A;'>{sig['rr2']:.1f}:1</span></div>"
            )
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:3px solid {sig_col};border-radius:14px;"
                f"padding:1.2rem 1.4rem;'>"
                f"<div style='font-size:0.56rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Trade Metrics</div>"
                f"<div style='display:flex;justify-content:space-between;align-items:baseline;"
                f"margin-bottom:0.4rem;'>"
                f"<span style='font-size:0.65rem;color:#666;'>Signal Confidence</span>"
                f"<span style='font-size:1.2rem;font-weight:900;color:{sig_col};'>{conf_pct}%</span>"
                f"</div>"
                + _glowbar(conf_pct, sig_col, "6px") +
                f"<div style='margin-top:0.75rem;'>{stats_rows}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    else:
        conf_pct = min(100, max(0, int(sig["score"] / 80 * 100)))
        st.markdown(
            f"<div style='background:{BG2};border:1px solid #44444488;"
            f"border-left:5px solid #555;border-radius:14px;"
            f"padding:1.5rem 2rem;'>"
            f"<div style='font-size:0.65rem;color:#9e9e9e;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>"
            f"Volume Profile — No Active Signal</div>"
            f"<div style='font-size:2rem;font-weight:900;color:#555;"
            f"letter-spacing:-0.5px;margin-bottom:0.4rem;'>NOT IN ZONE</div>"
            f"<div style='font-size:0.85rem;color:#9e9e9e;margin-bottom:0.6rem;'>"
            f"{sig['zone']}</div>"
            f"<div style='margin-bottom:1rem;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:0.25rem;'>"
            f"<span style='font-size:0.67rem;color:#666;text-transform:uppercase;"
            f"letter-spacing:0.5px;'>Confluence Score</span>"
            f"<span style='font-size:0.78rem;font-weight:800;color:#555;'>{conf_pct}%</span>"
            f"</div>"
            + _glowbar(conf_pct, "#555", "5px") +
            f"</div>"
            f"<div style='border-top:1px solid {BDR};padding-top:0.8rem;"
            f"display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.6rem;'>"
            + "".join([
                f"<div style='background:{BG};border-radius:10px;padding:0.65rem 0.85rem;'>"
                f"<div style='font-size:0.62rem;color:#555;text-transform:uppercase;"
                f"letter-spacing:0.5px;margin-bottom:0.2rem;'>{ln}</div>"
                f"<div style='font-size:1.05rem;font-weight:800;color:{lc};'>{lv:.2f}</div>"
                f"<div style='font-size:0.62rem;color:#555;margin-top:0.1rem;'>{ls}</div>"
                f"</div>"
                for ln, lv, lc, ls in [
                    ("Watch: VAL", val, BULL,      "demand floor"),
                    ("Watch: POC", poc, "#FFD700", "control level"),
                    ("Watch: VAH", vah, BEAR,      "supply ceiling"),
                ]
            ]) +
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ══ 4. CHART ══════════════════════════════════════════════════════════════
    st.markdown(_sec("Volume Profile Chart", INFO), unsafe_allow_html=True)
    fig = _build_vp_chart(df, vp, sig, current_price, tail=90)
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})

    st.markdown(
        f"<div style='display:flex;gap:1.5rem;flex-wrap:wrap;"
        f"padding:0.5rem 0.8rem;background:{BG};border:1px solid {BDR};"
        f"border-radius:8px;margin-bottom:0.5rem;'>"
        + "".join([
            f"<span style='font-size:0.63rem;color:{lc};font-weight:700;'>▬ {lt}</span>"
            for lc, lt in [
                ("#FFD700", "POC"),
                (BULL,      "VAL"),
                (BEAR,      "VAH"),
                (PURP,      "VWAP"),
                ("rgba(33,150,243,0.9)", "Value Area (70% vol)"),
                (BULL,      "HVN — strong support/resistance"),
                (BEAR,      "LVN — thin air, fast move zone"),
            ]
        ]) +
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='font-size:0.72rem;color:#9e9e9e;margin-top:1.5rem;"
        f"padding:0.75rem 1rem;background:{BG};border-radius:8px;border:1px solid {BDR};'>"
        f"Volume Profile is computed from the full selected date range. "
        f"POC, VAH, and VAL shift as new data is added. Not financial advice."
        f"</div>",
        unsafe_allow_html=True,
    )
