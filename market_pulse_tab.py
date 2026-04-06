"""
Market Pulse — Saudi Market Command Center  (TradingView Edition v2)
=====================================================================
Professional trading-terminal UI with TradingView color palette.
Sections:
  1. Hero row  — TASI price card · SVG arc health gauge · Market action panel
  2. Regime meter — 5-state horizontal indicator
  3. Breadth tiles — 6 KPIs with mini progress bars
  4. Sector rotation grid — 12 sectors, performance bars, momentum tags
  5. RS Leaders + Smart Money — side by side
"""

import math
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime, timezone, timedelta

# ── Breadth universe (56 liquid Tadawul stocks × 12 sectors) ─────────────────
_BREADTH = [
    "1010.SR","1030.SR","1060.SR","1080.SR","1120.SR","1150.SR","1180.SR",
    "2010.SR","2020.SR","2060.SR","2222.SR","2350.SR","2380.SR","1211.SR",
    "3010.SR","3020.SR","3040.SR","3050.SR","3060.SR",
    "7010.SR","7020.SR","7030.SR","7203.SR",
    "4001.SR","4003.SR","4164.SR","4190.SR",
    "8010.SR","8020.SR","8050.SR","8060.SR","8210.SR",
    "4002.SR","4004.SR","4007.SR","4017.SR",
    "4330.SR","4334.SR","4340.SR","4345.SR",
    "5110.SR",
    "4090.SR","4250.SR","4300.SR","4322.SR",
    "1302.SR","4142.SR","1321.SR",
    "2280.SR","6002.SR",
]

_SECTOR_MAP = {
    "Banks":        ["1010.SR","1030.SR","1060.SR","1080.SR","1120.SR","1150.SR","1180.SR"],
    "Petrochem":    ["2010.SR","2020.SR","2060.SR","2222.SR","2350.SR","2380.SR","1211.SR"],
    "Cement":       ["3010.SR","3020.SR","3040.SR","3050.SR","3060.SR"],
    "Telecom & IT": ["7010.SR","7020.SR","7030.SR","7203.SR"],
    "Retail":       ["4001.SR","4003.SR","4164.SR","4190.SR"],
    "Insurance":    ["8010.SR","8020.SR","8050.SR","8060.SR","8210.SR"],
    "Healthcare":   ["4002.SR","4004.SR","4007.SR","4017.SR"],
    "REITs":        ["4330.SR","4334.SR","4340.SR","4345.SR"],
    "Utilities":    ["5110.SR"],
    "Real Estate":  ["4090.SR","4250.SR","4300.SR","4322.SR"],
    "Industrials":  ["1302.SR","4142.SR","1321.SR"],
    "Consumer":     ["2280.SR","6002.SR"],
}

# ── TradingView Color Palette ─────────────────────────────────────────────────
_BG     = "#131722"
_PANEL  = "#1E222D"
_BORDER = "#2A2E39"
_BULL   = "#26A69A"   # TradingView teal-green
_BEAR   = "#EF5350"   # TradingView red
_BLUE   = "#2196F3"
_AMBER  = "#F29D38"
_LIME   = "#66BB6A"
_TEXT   = "#D1D4DC"
_TEXT2  = "#787B86"
_TEXT3  = "#4C525E"
_GOLD   = "#F5A623"


# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_pulse_data():
    """Download 3-month daily data for the breadth universe + TASI index."""
    tickers = _BREADTH + ["^TASI"]
    try:
        raw = yf.download(
            tickers, period="3mo", progress=False,
            threads=True, group_by="ticker", timeout=60,
        )
    except Exception:
        return None, None

    if raw is None or raw.empty:
        return None, None

    # ── TASI index ──────────────────────────────────────────────────────────
    tasi_close = None
    try:
        if "^TASI" in raw.columns.get_level_values(0):
            tasi_close = raw["^TASI"]["Close"].astype(float).dropna()
    except Exception:
        pass

    # ── Individual stocks ───────────────────────────────────────────────────
    records = []
    for ticker in _BREADTH:
        try:
            lv0 = raw.columns.get_level_values(0)
            if ticker not in lv0:
                continue
            d = raw[ticker].dropna(subset=["Close"]).copy()
            if len(d) < 25:
                continue

            c = d["Close"].astype(float)
            v = (d["Volume"].astype(float)
                 if "Volume" in d.columns
                 else pd.Series([0.0] * len(c), index=c.index))

            e20_s  = ta.ema(c, length=20)
            e50_s  = ta.ema(c, length=min(50, len(c) - 1))
            e200_s = ta.ema(c, length=200) if len(c) >= 200 else None

            def _last(s):
                if s is None:
                    return None
                s = s.dropna()
                return float(s.iloc[-1]) if len(s) > 0 else None

            e20  = _last(e20_s)
            e50  = _last(e50_s)
            e200 = _last(e200_s)
            cp   = float(c.iloc[-1])

            r1   = (cp / float(c.iloc[-2])  - 1) * 100 if len(c) >= 2  else 0.0
            r5   = (cp / float(c.iloc[-5])  - 1) * 100 if len(c) >= 5  else 0.0
            r20  = (cp / float(c.iloc[-20]) - 1) * 100 if len(c) >= 20 else 0.0
            r60  = (cp / float(c.iloc[-60]) - 1) * 100 if len(c) >= 60 else 0.0

            vol_avg = float(v.iloc[-20:].mean()) if len(v) >= 20 else 1.0
            vol_cur = float(v.iloc[-1]) if len(v) > 0 else vol_avg
            vol_r   = (vol_cur / vol_avg) if vol_avg > 0 else 1.0

            c_max     = float(c.max())
            c_min     = float(c.min())
            near_high = cp >= c_max * 0.98
            near_low  = cp <= c_min * 1.02

            sector = next(
                (s for s, tks in _SECTOR_MAP.items() if ticker in tks), "Other"
            )

            records.append({
                "ticker":     ticker.replace(".SR", ""),
                "cp":         cp,
                "r1":         r1,
                "above_e20":  bool(cp > e20)  if e20  is not None else False,
                "above_e50":  bool(cp > e50)  if e50  is not None else False,
                "above_e200": (bool(cp > e200) if e200 is not None else None),
                "r5":         r5,
                "r20":        r20,
                "r60":        r60,
                "vol_ratio":  vol_r,
                "near_high":  near_high,
                "near_low":   near_low,
                "sector":     sector,
            })
        except Exception:
            continue

    df = pd.DataFrame(records) if records else pd.DataFrame()

    tasi = {"tasi_price": 0.0, "tasi_r1": 0.0, "tasi_r5": 0.0, "tasi_r20": 0.0}
    if tasi_close is not None and len(tasi_close) >= 2:
        cp_t = float(tasi_close.iloc[-1])
        tasi["tasi_price"] = cp_t
        tasi["tasi_r1"]  = (cp_t / float(tasi_close.iloc[-2])  - 1) * 100 if len(tasi_close) >= 2  else 0.0
        tasi["tasi_r5"]  = (cp_t / float(tasi_close.iloc[-5])  - 1) * 100 if len(tasi_close) >= 5  else 0.0
        tasi["tasi_r20"] = (cp_t / float(tasi_close.iloc[-20]) - 1) * 100 if len(tasi_close) >= 20 else 0.0

    return df, tasi


def _health_score(df: pd.DataFrame) -> int:
    """0-100 composite market health from breadth internals."""
    if df is None or df.empty:
        return 50
    pct_e20  = float(df["above_e20"].mean()) * 100
    pct_e50  = float(df["above_e50"].mean()) * 100
    e200v    = df["above_e200"].dropna()
    pct_e200 = float(e200v.mean()) * 100 if len(e200v) > 0 else 50.0
    adv      = float((df["r20"] > 0).sum())
    dec      = float((df["r20"] < 0).sum())
    ad_ratio = adv / (adv + dec) if (adv + dec) > 0 else 0.5
    up_df    = df[df["r5"] > 0]
    dn_df    = df[df["r5"] < 0]
    vol_up   = float(up_df["vol_ratio"].mean()) if len(up_df) > 0 else 1.0
    vol_dn   = float(dn_df["vol_ratio"].mean()) if len(dn_df) > 0 else 1.0
    vol_bias = vol_up / (vol_up + vol_dn) if (vol_up + vol_dn) > 0 else 0.5
    score = (
        pct_e20  * 0.25 +
        pct_e50  * 0.25 +
        pct_e200 * 0.20 +
        ad_ratio * 100  * 0.20 +
        vol_bias * 100  * 0.10
    )
    return round(min(100, max(0, score)))


# ─────────────────────────────────────────────────────────────────────────────
# SVG / HTML HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _arc_gauge(health: int, color: str) -> str:
    """
    SVG semicircle arc gauge, 0-100 scale.
    Red (left) to Green (right). White needle dot at current health position.
    Math: arc path M 20 100 A 80 80 0 0 1 180 100 (L→top→R, clockwise).
    Needle angle: pi * (1 - health/100) from +x axis.
    """
    circ      = 251.3
    filled    = circ * health / 100.0
    angle_rad = math.pi * (1.0 - health / 100.0)
    dot_x     = 100.0 + 80.0 * math.cos(angle_rad)
    dot_y     = 100.0 - 80.0 * math.sin(angle_rad)
    uid       = abs(health)
    return (
        f'<svg viewBox="0 0 200 118" xmlns="http://www.w3.org/2000/svg" '
        f'style="display:block;margin:0 auto;width:185px;overflow:visible;">'
        f'<defs>'
        f'<linearGradient id="ag{uid}" x1="20" y1="60" x2="180" y2="60" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%"   stop-color="#EF5350"/>'
        f'<stop offset="28%"  stop-color="#FF7043"/>'
        f'<stop offset="50%"  stop-color="#FFB300"/>'
        f'<stop offset="72%"  stop-color="#66BB6A"/>'
        f'<stop offset="100%" stop-color="#26A69A"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<path d="M 20 100 A 80 80 0 0 1 180 100" '
        f'stroke="{_BORDER}" stroke-width="13" fill="none" stroke-linecap="round"/>'
        f'<path d="M 20 100 A 80 80 0 0 1 180 100" '
        f'stroke="url(#ag{uid})" stroke-width="13" fill="none" stroke-linecap="round" '
        f'stroke-dasharray="{filled:.1f} {circ:.1f}" stroke-dashoffset="0"/>'
        f'<circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="7" fill="{color}" '
        f'stroke="{_PANEL}" stroke-width="3"/>'
        f'<text x="100" y="82" text-anchor="middle" fill="{color}" '
        f'font-size="36" font-weight="900" '
        f'font-family="system-ui,-apple-system,BlinkMacSystemFont,sans-serif">{health}</text>'
        f'<text x="100" y="98" text-anchor="middle" fill="{_TEXT3}" '
        f'font-size="9" letter-spacing="2" '
        f'font-family="system-ui,-apple-system,BlinkMacSystemFont,sans-serif">HEALTH SCORE</text>'
        f'<text x="16"  y="115" text-anchor="middle" fill="{_TEXT3}" '
        f'font-size="8.5" font-family="system-ui,sans-serif">BEAR</text>'
        f'<text x="184" y="115" text-anchor="middle" fill="{_TEXT3}" '
        f'font-size="8.5" font-family="system-ui,sans-serif">BULL</text>'
        f'</svg>'
    )


def _pct_bar(pct: int, color: str, h: int = 5) -> str:
    """Thin horizontal progress bar for breadth tiles."""
    safe = min(100, max(0, pct))
    return (
        f'<div style="height:{h}px;background:{_BORDER};border-radius:3px;'
        f'margin-top:8px;overflow:hidden;">'
        f'<div style="width:{safe}%;height:100%;'
        f'background:linear-gradient(90deg,{color}77,{color});'
        f'border-radius:3px;"></div></div>'
    )


def _s(v: float) -> str:
    """Format float with leading + sign for positive."""
    return ("+" if v >= 0 else "") + f"{v:.1f}"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDERER
# ─────────────────────────────────────────────────────────────────────────────

def render_market_pulse_tab():
    """Render the full TradingView-style Market Pulse dashboard."""

    with st.spinner("Loading Saudi market data..."):
        df, tasi = _fetch_pulse_data()

    if df is None or df.empty:
        st.markdown(
            "<div style='text-align:center;color:#787B86;padding:5rem 0;font-size:1.1rem;'>"
            "Unable to load market data. Check your internet connection and try again.</div>",
            unsafe_allow_html=True,
        )
        return

    # --- Breadth metrics ---
    health   = _health_score(df)
    pct_e20  = round(float(df["above_e20"].mean()) * 100)
    pct_e50  = round(float(df["above_e50"].mean()) * 100)
    e200v    = df["above_e200"].dropna()
    pct_e200 = round(float(e200v.mean()) * 100) if len(e200v) > 0 else 0
    adv      = int((df["r20"] > 0).sum())
    dec      = int((df["r20"] < 0).sum())
    neu      = len(df) - adv - dec

    # --- TASI ---
    tasi_price = tasi.get("tasi_price", 0.0)
    tasi_r1    = tasi.get("tasi_r1", 0.0)
    tasi_r5    = tasi.get("tasi_r5", 0.0)
    tasi_r20   = tasi.get("tasi_r20", 0.0)
    tasi_disp  = f"{tasi_price:,.2f}" if tasi_price > 0 else "--"
    r1_sign    = "+" if tasi_r1 >= 0 else ""
    r1_col     = "#26A69A" if tasi_r1 >= 0 else "#EF5350"
    r1_arrow   = "▲" if tasi_r1 >= 0 else "▼"
    r5_col     = "#26A69A" if tasi_r5 >= 0 else "#EF5350"
    r20_col    = "#26A69A" if tasi_r20 >= 0 else "#EF5350"
    r5_s       = ("+" if tasi_r5  >= 0 else "") + f"{tasi_r5:.1f}"
    r20_s      = ("+" if tasi_r20 >= 0 else "") + f"{tasi_r20:.1f}"

    # --- Environment ---
    if health >= 68:
        env_label  = "BULL MARKET"
        env_sub    = "Breadth is strong across all timeframes. Trend-following setups have a high probability of working. Full conviction on best setups."
        env_guide  = "Deploy full capital  |  Full position size  |  Focus on RS leaders"
        env_col    = "#26A69A"
        sizing     = 100
    elif health >= 55:
        env_label  = "RISK ON"
        env_sub    = "Market is healthy but selective. Leading sectors are outperforming. Stick to stocks with all EMAs aligned and high RS."
        env_guide  = "Deploy 70% capital  |  Normal size  |  Leading sectors only"
        env_col    = "#66BB6A"
        sizing     = 70
    elif health >= 42:
        env_label  = "MIXED SIGNALS"
        env_sub    = "Breadth is uneven with many false breakouts. Only take score >= 8 setups with all EMAs aligned. Reduce position size significantly."
        env_guide  = "Max 40% capital  |  Reduce size 35%  |  High-conviction only"
        env_col    = "#F29D38"
        sizing     = 40
    elif health >= 28:
        env_label  = "UNDER PRESSURE"
        env_sub    = "Breadth deteriorating rapidly. High failure rate on new entries. Wait for a confirmed breadth reversal before buying anything new."
        env_guide  = "Hold maximum cash  |  No new longs  |  Protect open positions"
        env_col    = "#FF5722"
        sizing     = 10
    else:
        env_label  = "BEAR MARKET"
        env_sub    = "Conditions are hostile for long positions. Capital preservation is the only priority. Do not fight the trend."
        env_guide  = "Stand aside entirely  |  Cash is the position"
        env_col    = "#EF5350"
        sizing     = 0

    ts     = datetime.now(timezone(timedelta(hours=3))).strftime("%H:%M  %d %b %Y  AST")
    sbc    = env_col if sizing >= 60 else ("#F29D38" if sizing >= 30 else "#EF5350")

    # =================================================================
    # ROW 1 -- BREADTH HEALTH + MARKET CONDITIONS (full width)
    # =================================================================
    col_gauge, col_action = st.columns([1.1, 2.3], gap="medium")

    with col_gauge:
        h  = "<div style='background:#1E222D;border:1px solid #2A2E39;border-radius:16px;padding:1.4rem 1rem;height:100%;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;'>"
        h += "<div style='font-size:0.7rem;color:#4C525E;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:0.5rem;'>BREADTH HEALTH</div>"
        h += _arc_gauge(health, env_col)
        h += f"<div style='font-size:1.05rem;font-weight:900;color:{env_col};margin-top:0.4rem;letter-spacing:0.3px;'>{env_label}</div>"
        h += "</div>"
        st.markdown(h, unsafe_allow_html=True)

    with col_action:
        h  = f"<div style='background:#1E222D;border:1px solid #2A2E39;border-left:4px solid {env_col};border-radius:16px;padding:1.6rem 1.5rem;height:100%;box-sizing:border-box;'>"
        h += "<div style='font-size:0.7rem;color:#4C525E;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:0.65rem;'>MARKET CONDITIONS</div>"
        h += f"<div style='font-size:1.7rem;font-weight:900;color:{env_col};line-height:1.1;margin-bottom:0.7rem;'>{env_label}</div>"
        h += f"<div style='font-size:0.95rem;color:#A0A4B0;line-height:1.75;margin-bottom:1.3rem;'>{env_sub}</div>"
        h += "<div style='border-top:1px solid #2A2E39;padding-top:1rem;'>"
        h += f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>"
        h += f"<span style='font-size:0.88rem;color:#787B86;font-weight:600;'>Recommended Capital Allocation</span>"
        h += f"<span style='font-size:1.6rem;font-weight:900;color:{sbc};'>{sizing}%</span></div>"
        h += f"<div style='height:10px;background:#2A2E39;border-radius:5px;overflow:hidden;margin-bottom:0.7rem;'>"
        h += f"<div style='width:{sizing}%;height:100%;background:linear-gradient(90deg,{env_col}99,{env_col});border-radius:5px;'></div></div>"
        h += f"<div style='font-size:0.88rem;color:#787B86;line-height:1.7;'>{env_guide}</div>"
        h += "</div></div>"
        st.markdown(h, unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # =================================================================
    # ROW 2 -- TASI INDEX + REGIME METER
    # =================================================================
    zone_defs = [
        ("Bear Market",     0,  28, "#EF5350", health < 28),
        ("Under Pressure", 28,  42, "#FF5722", 28 <= health < 42),
        ("Mixed Signals",  42,  55, "#F29D38", 42 <= health < 55),
        ("Risk On",        55,  68, "#66BB6A", 55 <= health < 68),
        ("Bull Market",    68, 100, "#26A69A", health >= 68),
    ]
    zones_html = ""
    for zlabel, zlo, zhi, zcolor, zactive in zone_defs:
        zw   = zhi - zlo
        zbg  = zcolor if zactive else f"{zcolor}22"
        ztc  = "#D1D4DC" if zactive else "#4C525E"
        zfw  = "900" if zactive else "500"
        zbdr = f"border:2px solid {zcolor};" if zactive else f"border:1px solid {zcolor}30;"
        zones_html += (
            f"<div style='flex:{zw};background:{zbg};{zbdr}display:flex;align-items:center;"
            f"justify-content:center;padding:11px 4px;border-radius:8px;'>"
            f"<span style='font-size:0.85rem;font-weight:{zfw};color:{ztc};white-space:nowrap;'>{zlabel}</span></div>"
        )

    col_tasi, col_regime = st.columns([1.1, 2.3], gap="medium")

    with col_tasi:
        h  = "<div style='background:#1E222D;border:1px solid #2A2E39;border-radius:16px;padding:1.6rem 1.5rem;height:100%;box-sizing:border-box;'>"
        h += "<div style='font-size:0.7rem;color:#4C525E;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:0.7rem;'>TASI INDEX</div>"
        h += f"<div style='font-size:2.7rem;font-weight:900;color:#D1D4DC;letter-spacing:-1.5px;line-height:1;margin-bottom:0.5rem;'>{tasi_disp}</div>"
        h += f"<div style='font-size:1.15rem;font-weight:700;color:{r1_col};'>{r1_arrow} {r1_sign}{tasi_r1:.2f}%&ensp;<span style='font-size:0.78rem;color:#4C525E;font-weight:400;'>last session</span></div>"
        h += "<div style='margin-top:1.1rem;padding-top:1rem;border-top:1px solid #2A2E39;display:flex;flex-direction:column;gap:0.55rem;'>"
        h += f"<div style='display:flex;justify-content:space-between;align-items:center;'><span style='font-size:0.88rem;color:#787B86;'>5-Day</span><span style='font-size:0.92rem;font-weight:800;color:{r5_col};'>{r5_s}%</span></div>"
        h += f"<div style='display:flex;justify-content:space-between;align-items:center;'><span style='font-size:0.88rem;color:#787B86;'>20-Day</span><span style='font-size:0.92rem;font-weight:800;color:{r20_col};'>{r20_s}%</span></div>"
        h += "</div>"
        h += f"<div style='margin-top:1rem;font-size:0.7rem;color:#4C525E;'>{ts}</div>"
        h += "</div>"
        st.markdown(h, unsafe_allow_html=True)

    with col_regime:
        rm  = "<div style='background:#1E222D;border:1px solid #2A2E39;border-radius:16px;padding:1.5rem 1.6rem;height:100%;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;'>"
        rm += "<div style='font-size:0.7rem;color:#4C525E;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:1rem;'>REGIME METER</div>"
        rm += f"<div style='display:flex;gap:6px;'>{zones_html}</div>"
        rm += f"<div style='margin-top:1.1rem;font-size:0.9rem;color:#787B86;'>Active zone: <span style='color:{env_col};font-weight:800;'>{env_label}</span>&ensp;&bull;&ensp;Score: <span style='color:{env_col};font-weight:800;'>{health} / 100</span></div>"
        rm += "</div>"
        st.markdown(rm, unsafe_allow_html=True)

    # =================================================================
    # SECTION 3 -- BREADTH TILES
    # =================================================================
    st.markdown(
        "<div style='font-size:0.82rem;font-weight:800;color:#787B86;text-transform:uppercase;"
        "letter-spacing:1.5px;border-bottom:1px solid #2A2E39;padding-bottom:0.55rem;"
        "margin-bottom:0.75rem;'>MARKET BREADTH</div>",
        unsafe_allow_html=True,
    )

    def _tile(tlabel, tval, tunit, tsub, tcolor, tpct):
        p  = min(100, max(0, tpct))
        h  = f"<div style='background:#1E222D;border:1px solid #2A2E39;border-top:3px solid {tcolor};border-radius:14px;padding:1.1rem 1.2rem;'>"
        h += f"<div style='font-size:0.72rem;color:#4C525E;text-transform:uppercase;letter-spacing:0.9px;font-weight:700;margin-bottom:0.55rem;'>{tlabel}</div>"
        h += f"<div style='font-size:2.4rem;font-weight:900;color:{tcolor};line-height:1;'>{tval}<span style='font-size:0.9rem;font-weight:600;color:#4C525E;margin-left:4px;'>{tunit}</span></div>"
        h += f"<div style='font-size:0.78rem;color:#787B86;margin-top:0.4rem;'>{tsub}</div>"
        h += f"<div style='height:5px;background:#2A2E39;border-radius:3px;margin-top:0.75rem;overflow:hidden;'>"
        h += f"<div style='width:{p}%;height:100%;background:linear-gradient(90deg,{tcolor}55,{tcolor});border-radius:3px;'></div></div>"
        h += "</div>"
        return h

    e20_col  = "#26A69A" if pct_e20  >= 50 else ("#F29D38" if pct_e20  >= 30 else "#EF5350")
    e50_col  = "#26A69A" if pct_e50  >= 50 else ("#F29D38" if pct_e50  >= 30 else "#EF5350")
    e200_col = "#26A69A" if pct_e200 >= 50 else ("#F29D38" if pct_e200 >= 30 else "#EF5350")
    ad_total = adv + dec + neu
    ad_pct   = round(adv / ad_total * 100) if ad_total > 0 else 50
    ad_col   = "#26A69A" if ad_pct >= 55 else ("#F29D38" if ad_pct >= 45 else "#EF5350")
    ti_col   = "#26A69A" if tasi_r20 >= 0 else "#EF5350"
    ti_fill  = min(100, max(0, int(50 + tasi_r20 * 5)))

    bc1, bc2, bc3, bc4, bc5 = st.columns(5, gap="small")
    with bc1:
        st.markdown(_tile("Above EMA 20",  str(pct_e20),  "%", "Short-term trend",   e20_col,  pct_e20),  unsafe_allow_html=True)
    with bc2:
        st.markdown(_tile("Above EMA 50",  str(pct_e50),  "%", "Medium-term trend",  e50_col,  pct_e50),  unsafe_allow_html=True)
    with bc3:
        st.markdown(_tile("Above EMA 200", str(pct_e200), "%", "Long-term structure", e200_col, pct_e200), unsafe_allow_html=True)
    with bc4:
        ad_disp = f"{adv} / {dec}"
        st.markdown(_tile("Adv / Dec", ad_disp, "", f"{ad_pct}% advancing", ad_col, ad_pct), unsafe_allow_html=True)
    with bc5:
        st.markdown(_tile("TASI 20-Day", r20_s, "%", f"Index at {tasi_disp}", ti_col, ti_fill), unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # =================================================================
    # SECTION 4 -- SECTOR ROTATION
    # =================================================================
    st.markdown(
        "<div style='font-size:0.82rem;font-weight:800;color:#787B86;text-transform:uppercase;"
        "letter-spacing:1.5px;border-bottom:1px solid #2A2E39;padding-bottom:0.55rem;"
        "margin-bottom:0.75rem;'>SECTOR ROTATION  <span style='font-weight:500;font-size:0.72rem;color:#4C525E;'>sorted by 20-day performance</span></div>",
        unsafe_allow_html=True,
    )

    sector_rows = []
    for sec_name, tks in _SECTOR_MAP.items():
        sdf = df[df["sector"] == sec_name]
        if sdf.empty:
            continue
        r5_avg  = round(float(sdf["r5"].mean()),  1)
        r20_avg = round(float(sdf["r20"].mean()), 1)
        r60_avg = round(float(sdf["r60"].mean()), 1)
        bulls   = round(float(sdf["above_e50"].mean()) * 100)
        n_sec   = len(sdf)
        if   r20_avg >  6.0: trend, tc = "HOT",     "#26A69A"
        elif r20_avg >  1.5: trend, tc = "RISING",  "#66BB6A"
        elif r20_avg > -1.5: trend, tc = "FLAT",    "#F29D38"
        elif r20_avg > -5.0: trend, tc = "FALLING", "#FF5722"
        else:                trend, tc = "COLD",    "#EF5350"
        sector_rows.append({"sector": sec_name, "r5": r5_avg, "r20": r20_avg, "r60": r60_avg, "bulls": bulls, "n": n_sec, "trend": trend, "tc": tc})
    sector_rows.sort(key=lambda x: x["r20"], reverse=True)
    max_abs = max((abs(r["r20"]) for r in sector_rows), default=1.0) or 1.0

    sc1, sc2, sc3 = st.columns(3, gap="small")
    scols = [sc1, sc2, sc3]
    for idx, srow in enumerate(sector_rows):
        sc    = srow["tc"]
        bw    = min(100, abs(srow["r20"]) / max_abs * 100)
        bbc   = "#26A69A" if srow["r20"] >= 0 else "#EF5350"
        r5c   = "#26A69A" if srow["r5"]  >= 0 else "#EF5350"
        r60c  = "#26A69A" if srow["r60"] >= 0 else "#EF5350"
        s_r5  = ("+" if srow["r5"]  >= 0 else "") + f"{srow['r5']:.1f}"
        s_r20 = ("+" if srow["r20"] >= 0 else "") + f"{srow['r20']:.1f}"
        s_r60 = ("+" if srow["r60"] >= 0 else "") + f"{srow['r60']:.1f}"
        shc   = f"<div style='background:#1E222D;border:1px solid #2A2E39;border-radius:14px;padding:1.3rem 1.4rem;margin-bottom:0.6rem;'>"
        shc  += f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.9rem;'>"
        shc  += f"<div style='font-size:1.05rem;font-weight:800;color:#D1D4DC;'>{srow['sector']}</div>"
        shc  += f"<div style='font-size:0.75rem;color:{sc};font-weight:800;background:{sc}1E;padding:4px 12px;border-radius:5px;letter-spacing:0.5px;'>{srow['trend']}</div></div>"
        shc  += f"<div style='height:5px;background:#2A2E39;border-radius:3px;margin-bottom:0.9rem;overflow:hidden;'>"
        shc  += f"<div style='width:{bw:.0f}%;height:100%;background:{bbc};border-radius:3px;'></div></div>"
        shc  += f"<div style='font-size:1.45rem;font-weight:900;color:{sc};line-height:1;'>{s_r20}%</div>"
        shc  += f"<div style='font-size:0.7rem;color:#4C525E;margin-top:4px;margin-bottom:0.85rem;letter-spacing:0.3px;'>20-day return</div>"
        shc  += "<div style='display:flex;gap:1.4rem;padding-top:0.75rem;border-top:1px solid #2A2E39;'>"
        shc  += f"<div><div style='font-size:0.95rem;font-weight:700;color:{r5c};'>{s_r5}%</div><div style='font-size:0.7rem;color:#4C525E;margin-top:4px;'>5D</div></div>"
        shc  += f"<div><div style='font-size:0.95rem;font-weight:700;color:{r60c};'>{s_r60}%</div><div style='font-size:0.7rem;color:#4C525E;margin-top:4px;'>60D</div></div>"
        shc  += f"<div style='margin-left:auto;text-align:right;'><div style='font-size:1.05rem;font-weight:800;color:#2196F3;'>{srow['bulls']}%</div><div style='font-size:0.7rem;color:#4C525E;margin-top:4px;'>Bulls</div></div>"
        shc  += "</div></div>"
        with scols[idx % 3]:
            st.markdown(shc, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # =================================================================
    # SECTION 5 -- RS LEADERS + SMART MONEY
    # =================================================================
    left_col, right_col = st.columns([1, 1], gap="medium")

    with left_col:
        st.markdown(
            "<div style='font-size:0.82rem;font-weight:800;color:#787B86;text-transform:uppercase;"
            "letter-spacing:1.5px;border-bottom:1px solid #2A2E39;padding-bottom:0.55rem;"
            "margin-bottom:0.75rem;'>RS LEADERS  <span style='font-weight:500;font-size:0.72rem;color:#4C525E;'>outperforming TASI (20-day)</span></div>",
            unsafe_allow_html=True,
        )
        df_rs   = df.copy()
        df_rs["rs"] = df_rs["r20"] - tasi_r20
        leaders = df_rs.nlargest(8, "rs")
        rank_pal = {1: "#F5A623", 2: "#C0C0C0", 3: "#CD7F32"}
        for rank, (_, row) in enumerate(leaders.iterrows(), 1):
            rs_v    = round(float(row["rs"]),  1)
            r20_v   = round(float(row["r20"]), 1)
            rc      = "#26A69A" if rs_v > 0 else "#EF5350"
            ema_ok  = bool(row["above_e20"]) and bool(row["above_e50"])
            ema_col = "#26A69A" if ema_ok else "#4C525E"
            ema_txt = "EMAs aligned" if ema_ok else "Weak EMAs"
            nh_txt  = "  Near High" if bool(row.get("near_high", False)) else ""
            nh_col  = "#F29D38" if nh_txt else ""
            rkc     = rank_pal.get(rank, "#4C525E")
            rs_fmt  = ("+" if rs_v >= 0 else "") + f"{rs_v:.1f}"
            r20_fmt = ("+" if r20_v >= 0 else "") + f"{r20_v:.1f}"
            lhc  = f"<div style='background:#1E222D;border:1px solid #2A2E39;border-radius:12px;padding:0.9rem 1.1rem;margin-bottom:0.45rem;display:flex;align-items:center;gap:1rem;'>"
            lhc += f"<div style='font-size:1rem;font-weight:900;color:{rkc};min-width:28px;text-align:center;'>#{rank}</div>"
            lhc += "<div style='flex:1;min-width:0;'>"
            lhc += f"<div style='font-size:1.1rem;font-weight:900;color:#D1D4DC;'>{row['ticker']}"
            if nh_txt:
                lhc += f"<span style='font-size:0.72rem;color:{nh_col};margin-left:8px;font-weight:700;'>Near High</span>"
            lhc += f"<span style='font-size:0.78rem;color:#787B86;font-weight:400;margin-left:8px;'>{row['sector']}</span></div>"
            lhc += f"<div style='font-size:0.78rem;color:{ema_col};margin-top:4px;'>{ema_txt}</div>"
            lhc += "</div>"
            lhc += "<div style='text-align:right;'>"
            lhc += f"<div style='font-size:1.15rem;font-weight:900;color:{rc};'>{rs_fmt}%</div>"
            lhc += f"<div style='font-size:0.72rem;color:#4C525E;'>vs TASI &bull; {r20_fmt}% abs</div>"
            lhc += "</div></div>"
            st.markdown(lhc, unsafe_allow_html=True)

    with right_col:
        st.markdown(
            "<div style='font-size:0.82rem;font-weight:800;color:#787B86;text-transform:uppercase;"
            "letter-spacing:1.5px;border-bottom:1px solid #2A2E39;padding-bottom:0.55rem;"
            "margin-bottom:0.75rem;'>SMART MONEY  <span style='font-weight:500;font-size:0.72rem;color:#4C525E;'>unusual volume signals</span></div>",
            unsafe_allow_html=True,
        )
        alerts  = df[df["vol_ratio"] >= 1.8].sort_values("vol_ratio", ascending=False)
        accum   = alerts[alerts["r5"] > 0]
        distrib = alerts[alerts["r5"] <= 0]
        shown   = 0

        def _ac(arow, side):
            vr    = round(float(arow["vol_ratio"]), 1)
            r5_v  = round(float(arow["r5"]), 1)
            ca    = "#26A69A" if side == "accum" else "#EF5350"
            badge = "ACCUMULATION" if side == "accum" else "DISTRIBUTION"
            ema_s = "Above EMA50" if arow["above_e50"] else "Below EMA50"
            r5_s  = ("+" if r5_v >= 0 else "") + f"{r5_v:.1f}"
            ahc   = f"<div style='background:{ca}0C;border:1px solid {ca}2A;border-radius:12px;padding:0.9rem 1.1rem;margin-bottom:0.45rem;'>"
            ahc  += "<div style='display:flex;justify-content:space-between;align-items:center;'>"
            ahc  += "<div style='flex:1;'>"
            ahc  += f"<div style='font-size:1.1rem;font-weight:900;color:#D1D4DC;'>{arow['ticker']}&ensp;<span style='font-size:0.68rem;background:{ca}22;color:{ca};border-radius:4px;padding:2px 9px;font-weight:800;letter-spacing:0.5px;'>{badge}</span></div>"
            ahc  += f"<div style='font-size:0.78rem;color:#787B86;margin-top:5px;'>{ema_s}  &bull;  {arow['sector']}</div>"
            ahc  += "</div>"
            ahc  += "<div style='text-align:right;margin-left:1rem;'>"
            ahc  += f"<div style='font-size:1.15rem;font-weight:900;color:{ca};'>{vr}x vol</div>"
            ahc  += f"<div style='font-size:0.72rem;color:#4C525E;'>{r5_s}% (5-day)</div>"
            ahc  += "</div></div></div>"
            return ahc

        for _, arow in accum.head(5).iterrows():
            st.markdown(_ac(arow, "accum"), unsafe_allow_html=True)
            shown += 1
        for _, arow in distrib.head(max(0, 7 - shown)).iterrows():
            st.markdown(_ac(arow, "distrib"), unsafe_allow_html=True)

        if alerts.empty:
            ech  = "<div style='background:#1E222D;border:1px solid #2A2E39;border-radius:12px;padding:2.5rem;text-align:center;'>"
            ech += "<div style='font-size:1rem;color:#787B86;margin-bottom:0.45rem;'>No unusual volume today</div>"
            ech += "<div style='font-size:0.82rem;color:#4C525E;'>Participation is within normal range.</div>"
            ech += "</div>"
            st.markdown(ech, unsafe_allow_html=True)

    # Footer
    ftr  = f"<div style='margin-top:1.4rem;padding:0.9rem 0;border-top:1px solid #2A2E39;display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.4rem;'>"
    ftr += f"<span style='font-size:0.72rem;color:#4C525E;'>Universe: {len(df)} Tadawul stocks across 12 sectors  &bull;  Data refreshes every 30 minutes</span>"
    ftr += f"<span style='font-size:0.72rem;color:#4C525E;'>Updated: {ts}</span>"
    ftr += "</div>"
    st.markdown(ftr, unsafe_allow_html=True)
