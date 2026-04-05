"""
Combined Market Scanner + Stock Screener
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Period presets + date range → Run scan (inline, no page flip)
• KPI bar + Top 3 Podium
• Template pills (10 pre-built scans + Custom)
• Sub-tabs when in "All Stocks" mode mirroring existing results view
• Rich cards with Analyze → deep-dive button on every stock
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS  (match decision_tab / app.py)
# ─────────────────────────────────────────────────────────────────────────────
BULL = "#10a37f"
BEAR = "#ef4444"
NEUT = "#fbbf24"
INFO = "#4A9EFF"
PURP = "#9b87c2"
GOLD = "#FFD700"
TEAL = "#26A69A"
BG   = "#141414"
BG2  = "#1c1c1c"
BG3  = "#222222"
BDR  = "rgba(255,255,255,0.07)"
FONT = "Inter,system-ui,sans-serif"

PERIOD_PRESETS = [
    ("3M",  90),
    ("6M", 180),
    ("1Y", 365),
    ("2Y", 730),
]

# ─────────────────────────────────────────────────────────────────────────────
# SCAN TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────
TEMPLATES: dict = {
    "All Stocks": {
        "desc": "Show all scanned stocks organised by signal quality tabs",
        "color": INFO,
        "filter": None,
        "sort_key": "priority_score",
        "sort_asc": False,
    },
    "⭐ Perfect Setup": {
        "desc": "Both indicators AND price action positive · R:R ≥ 3 · Conviction ≥ 60%",
        "color": GOLD,
        "filter": lambda s: (
            s.get("ind_score", 0) >= 3 and
            s.get("pa_score",  0) >= 2 and
            s.get("score",     0) >= 5 and
            s.get("rr_ratio",  0) >= 3 and
            s.get("conviction",0) >= 60
        ),
        "sort_key": "priority_score",
        "sort_asc": False,
    },
    "🔥 Oversold Bounce": {
        "desc": "RSI < 35 + positive score — extreme oversold with bullish triggers",
        "color": BULL,
        "filter": lambda s: s.get("rsi", 50) < 35 and s.get("score", 0) > 0,
        "sort_key": "rsi",
        "sort_asc": True,
    },
    "🚀 Volume Surge": {
        "desc": "Volume 2×+ above 20-day average with bullish signal",
        "color": INFO,
        "filter": lambda s: s.get("vol_ratio", 1) >= 2.0 and s.get("score", 0) > 0,
        "sort_key": "vol_ratio",
        "sort_asc": False,
    },
    "📈 52W Breakout": {
        "desc": "Near 52-week high with positive 5-day momentum",
        "color": PURP,
        "filter": lambda s: (
            s.get("w52_pos", 0) >= 85 and
            s.get("score", 0) > 0 and
            s.get("perf_5d", 0) > 0
        ),
        "sort_key": "w52_pos",
        "sort_asc": False,
    },
    "🏆 Golden Cross": {
        "desc": "EMA50 crossed above EMA200 — major long-term bullish signal",
        "color": GOLD,
        "filter": lambda s: any("golden cross" in sig.lower() for sig in s.get("signals", [])),
        "sort_key": "priority_score",
        "sort_asc": False,
    },
    "🌟 RS Leader": {
        "desc": "Outperforming TASI by 5%+ — institutional accumulation",
        "color": TEAL,
        "filter": lambda s: s.get("rs_vs_tasi", 0) >= 5 and s.get("score", 0) > 0,
        "sort_key": "rs_vs_tasi",
        "sort_asc": False,
    },
    "💎 Deep Value": {
        "desc": "Near 52-week low · RSI < 40 — maximum fear zone, contrarian entry",
        "color": NEUT,
        "filter": lambda s: s.get("w52_pos", 100) <= 15 and s.get("rsi", 50) < 40,
        "sort_key": "w52_pos",
        "sort_asc": True,
    },
    "🎯 Range Bounce": {
        "desc": "RANGE regime + RSI oversold — mean-reversion setup",
        "color": "#f06292",
        "filter": lambda s: (
            s.get("regime") == "RANGE" and
            s.get("rsi", 50) < 40 and
            s.get("score", 0) > 0
        ),
        "sort_key": "rsi",
        "sort_asc": True,
    },
    "📅 Weekly Confirmed": {
        "desc": "Daily signal fully confirmed on weekly timeframe",
        "color": "#4dd0e1",
        "filter": lambda s: s.get("weekly_bullish") is True and s.get("score", 0) >= 4,
        "sort_key": "priority_score",
        "sort_asc": False,
    },
    "⚠️ Danger Zone": {
        "desc": "All indicators bearish — stocks to avoid",
        "color": BEAR,
        "filter": lambda s: s.get("score", 0) <= -5,
        "sort_key": "score",
        "sort_asc": True,
    },
    "🔧 Custom Filter": {
        "desc": "Build your own scan criteria using the filter panel below",
        "color": "#666",
        "filter": None,      # replaced at runtime by user settings
        "sort_key": "priority_score",
        "sort_asc": False,
    },
}

REGIME_C = {"TREND": INFO, "RANGE": NEUT, "VOLATILE": BEAR}
RISK_C   = {"Low": BULL, "Medium": NEUT, "High": BEAR}

SECTOR_C = {
    "Banks":           "#4A9EFF",
    "Petrochemicals":  "#FF6B6B",
    "Cement":          "#A78BFA",
    "Utilities":       "#34D399",
    "Telecom & Tech":  "#60A5FA",
    "Insurance":       "#F472B6",
    "Food & Agri":     "#FBBF24",
    "REITs":           "#6EE7B7",
    "Retail":          "#F97316",
    "Healthcare":      "#22D3EE",
    "Transport":       "#818CF8",
    "Real Estate":     "#FCD34D",
    "Other":           "#9CA3AF",
}


def _rgba(hex_c, a=0.14):
    h = str(hex_c).lstrip("#")
    if len(h) != 6:
        return f"rgba(127,127,127,{a})"
    r, g, b = int(h[:2],16), int(h[2:4],16), int(h[4:],16)
    return f"rgba({r},{g},{b},{a})"


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
def _css():
    st.markdown(f"""
    <style>
    /* ── Scan config panel ── */
    .scr-cfg {{
        background:{BG2};
        border:1px solid {BDR};
        border-radius:14px;
        padding:1.2rem 1.5rem 1.1rem;
        margin-bottom:1.4rem;
    }}
    .scr-cfg-title {{
        font-size:0.7rem;
        font-weight:800;
        text-transform:uppercase;
        letter-spacing:1px;
        color:#444;
        margin-bottom:0.9rem;
    }}
    .scr-preset-row {{
        display:flex;
        gap:0.4rem;
        margin-bottom:0.9rem;
    }}
    .scr-preset {{
        font-size:0.75rem;
        font-weight:800;
        padding:0.35rem 0.9rem;
        border-radius:8px;
        border:1.5px solid {BDR};
        background:{BG3};
        color:#555;
        cursor:default;
        letter-spacing:0.3px;
    }}
    .scr-preset.active {{
        border-color:{INFO};
        color:{INFO};
        background:{_rgba(INFO,.1)};
    }}

    /* ── Header / status bar ── */
    .scr-status {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:1.2rem;
        padding-bottom:0.8rem;
        border-bottom:1px solid {BDR};
    }}
    .scr-status-left {{ display:flex; align-items:center; gap:0.7rem; }}
    .scr-status-title {{
        font-size:1.15rem;
        font-weight:900;
        color:#e4e4e4;
        letter-spacing:-0.3px;
    }}
    .scr-status-badge {{
        font-size:0.62rem;
        font-weight:700;
        padding:0.22rem 0.65rem;
        border-radius:999px;
        letter-spacing:0.4px;
    }}

    /* ── KPI strip ── */
    .scr-kpis {{
        display:grid;
        grid-template-columns:repeat(6,1fr);
        gap:0.5rem;
        margin-bottom:1.2rem;
    }}
    .scr-kpi {{
        background:{BG2};
        border:1px solid {BDR};
        border-radius:10px;
        padding:0.65rem 0.7rem;
        text-align:center;
    }}
    .scr-kpi-v {{
        font-size:1.3rem;
        font-weight:900;
        letter-spacing:-0.5px;
        line-height:1;
        margin-bottom:0.2rem;
    }}
    .scr-kpi-l {{
        font-size:0.52rem;
        color:#404040;
        text-transform:uppercase;
        letter-spacing:0.7px;
        font-weight:700;
    }}

    /* ── Top picks podium ── */
    .scr-podium {{
        display:grid;
        grid-template-columns:repeat(3,1fr);
        gap:0.6rem;
        margin-bottom:1.2rem;
    }}
    .scr-pod {{
        border-radius:12px;
        overflow:hidden;
        border:1px solid {BDR};
    }}
    .scr-pod-hd {{
        display:flex;
        justify-content:space-between;
        align-items:flex-start;
        padding:0.7rem 0.85rem 0.3rem;
    }}
    .scr-pod-sym {{
        font-size:1rem;
        font-weight:900;
        line-height:1;
    }}
    .scr-pod-name {{
        font-size:0.6rem;
        color:#555;
        margin-top:0.18rem;
    }}
    .scr-pod-badge {{
        font-size:0.58rem;
        font-weight:700;
        padding:0.14rem 0.48rem;
        border-radius:999px;
    }}
    .scr-pod-bar {{
        padding:0.2rem 0.85rem 0.4rem;
    }}
    .scr-pod-track {{
        height:3px;
        background:{BDR};
        border-radius:2px;
        overflow:hidden;
    }}
    .scr-pod-fill {{ height:100%; border-radius:2px; }}
    .scr-pod-meta {{
        font-size:0.64rem;
        color:#666;
        padding:0 0.85rem 0.4rem;
        line-height:1.3;
    }}
    .scr-pod-lvls {{
        display:grid;
        grid-template-columns:repeat(4,1fr);
        border-top:1px solid {BDR};
    }}
    .scr-pod-lv {{
        text-align:center;
        padding:0.45rem 0.1rem;
        border-right:1px solid {BDR};
    }}
    .scr-pod-lv:last-child {{ border-right:none; }}
    .scr-pod-lv-v {{ font-size:0.78rem; font-weight:800; line-height:1; }}
    .scr-pod-lv-l {{ font-size:0.46rem; font-weight:600; color:#3a3a3a;
                     text-transform:uppercase; letter-spacing:0.5px; margin-top:3px; }}

    /* ── Template pills ── */
    .scr-tmpl-row {{
        display:flex;
        flex-wrap:wrap;
        gap:0.4rem;
        margin-bottom:1.2rem;
        padding:0.8rem 1rem;
        background:{BG2};
        border:1px solid {BDR};
        border-radius:12px;
    }}
    .scr-tmpl {{
        font-size:0.72rem;
        font-weight:700;
        padding:0.32rem 0.8rem;
        border-radius:999px;
        border:1.5px solid {BDR};
        color:#505050;
        cursor:default;
        white-space:nowrap;
    }}
    .scr-tmpl.active {{
        border-color:var(--tc);
        color:var(--tc);
        background:var(--tb);
    }}

    /* ── Section header ── */
    .scr-sec {{
        display:flex;
        align-items:center;
        gap:0.5rem;
        margin:0.2rem 0 0.6rem;
    }}
    .scr-sec-dot {{
        width:6px;
        height:6px;
        border-radius:50%;
        flex-shrink:0;
    }}
    .scr-sec-title {{
        font-size:0.62rem;
        font-weight:700;
        text-transform:uppercase;
        letter-spacing:0.9px;
    }}
    .scr-sec-count {{
        font-size:0.58rem;
        padding:0.1rem 0.48rem;
        border-radius:12px;
        background:{BG2};
        border:1px solid {BDR};
        color:#555;
    }}

    /* ── Stock card ── */
    .sc {{
        border-radius:14px;
        overflow:hidden;
        margin-bottom:0.5rem;
        background:{_rgba('#ffffff',.015)};
        border:1px solid {BDR};
        transition:background 0.12s;
    }}
    .sc:hover {{ background:{_rgba('#ffffff',.03)}; }}
    .sc-hd {{
        display:flex;
        align-items:flex-start;
        justify-content:space-between;
        padding:0.75rem 1rem 0.45rem;
        gap:0.75rem;
    }}
    .sc-sym  {{ font-size:1.05rem; font-weight:900; letter-spacing:-0.2px; line-height:1; }}
    .sc-sym.buy  {{ color:{BULL}; }} .sc-sym.sell {{ color:{BEAR}; }} .sc-sym.hold {{ color:{NEUT}; }}
    .sc-nameline {{ display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap; margin-top:0.28rem; }}
    .sc-name {{ font-size:0.68rem; color:#565656; max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
    .sc-tag  {{ font-size:0.58rem; font-weight:600; padding:0.1rem 0.4rem;
                border-radius:4px; background:{_rgba(PURP,.1)}; color:{PURP};
                border:1px solid {_rgba(PURP,.2)}; white-space:nowrap; }}
    .sc-right {{ text-align:right; flex-shrink:0; }}
    .sc-price {{ font-size:0.94rem; font-weight:700; color:#e0e0e0; letter-spacing:-0.2px; }}
    .sc-score {{ font-size:0.68rem; font-weight:800; padding:0.12rem 0.5rem; border-radius:999px; margin-top:0.28rem; display:inline-block; }}
    .sc-score.buy  {{ color:{BULL}; background:{_rgba(BULL,.12)}; border:1px solid {_rgba(BULL,.25)}; }}
    .sc-score.sell {{ color:{BEAR}; background:{_rgba(BEAR,.12)}; border:1px solid {_rgba(BEAR,.25)}; }}
    .sc-score.hold {{ color:{NEUT}; background:{_rgba(NEUT,.09)}; border:1px solid {_rgba(NEUT,.22)}; }}
    .sc-hr {{ height:1px; background:{BDR}; margin:0 1rem; }}
    .sc-data {{ display:flex; align-items:stretch; }}
    .sc-levels {{ display:flex; flex:1; }}
    .sc-lv {{ flex:1; text-align:center; padding:0.58rem 0.1rem;
              border-right:1px solid {BDR}; }}
    .sc-lv-v {{ font-size:0.88rem; font-weight:800; line-height:1; }}
    .sc-lv-l {{ font-size:0.48rem; font-weight:600; color:#3e3e3e;
                text-transform:uppercase; letter-spacing:0.5px; margin-top:3px; }}
    .sc-inds {{ display:flex; }}
    .sc-ind  {{ text-align:center; padding:0.58rem 0.55rem;
                border-right:1px solid {_rgba('#fff',.04)}; }}
    .sc-ind:last-child {{ border-right:none; }}
    .sc-iv {{ font-size:0.8rem; font-weight:700; line-height:1; }}
    .sc-il {{ font-size:0.46rem; font-weight:600; color:#404040;
              text-transform:uppercase; letter-spacing:0.4px; margin-top:3px; }}
    .sc-conv {{
        display:flex;
        align-items:center;
        gap:0.55rem;
        padding:0.35rem 1rem;
        background:rgba(0,0,0,0.09);
    }}
    .sc-conv-lbl {{ font-size:0.47rem; font-weight:700; text-transform:uppercase;
                    letter-spacing:0.5px; color:#3a3a3a; flex-shrink:0; }}
    .sc-conv-track {{ flex:1; height:3px; background:{BDR}; border-radius:2px; overflow:hidden; }}
    .sc-conv-fill  {{ height:100%; border-radius:2px; }}
    .sc-conv-val   {{ font-size:0.68rem; font-weight:700; flex-shrink:0; width:34px; text-align:right; }}
    .sc-foot {{
        display:flex;
        flex-wrap:wrap;
        gap:0.26rem;
        padding:0.44rem 1rem 0.64rem;
    }}
    .sc-chip {{ font-size:0.61rem; font-weight:600; padding:0.14rem 0.46rem; border-radius:6px; }}
    .sc-chip.up   {{ background:{_rgba(BULL,.1)};  color:{BULL}; border:1px solid {_rgba(BULL,.18)}; }}
    .sc-chip.dn   {{ background:{_rgba(BEAR,.1)};  color:{BEAR}; border:1px solid {_rgba(BEAR,.18)}; }}
    .sc-chip.neut {{ background:{_rgba('#fff',.04)};color:#666;   border:1px solid {BDR}; }}
    .sc-dot-sep   {{ color:#2a2a2a; font-size:0.75rem; display:flex; align-items:center; }}
    .sc-sigtag    {{ font-size:0.59rem; padding:0.13rem 0.42rem; border-radius:5px;
                     background:{_rgba('#fff',.03)}; border:1px solid {BDR}; color:#555; }}

    /* ── Sub-score strip ── */
    .sc-sub {{ display:flex; gap:0.6rem; padding:0.3rem 1rem 0;
               font-size:0.6rem; font-weight:700; }}

    /* ── Empty state ── */
    .scr-empty {{
        text-align:center;
        padding:2.5rem 1rem;
        color:#3a3a3a;
        font-size:0.82rem;
        font-weight:500;
    }}
    .scr-empty-icon {{ font-size:2rem; margin-bottom:0.5rem; }}

    /* ── Heatmap divider ── */
    .scr-hline {{ height:1px; background:{BDR}; margin:0.9rem 0 0.8rem; }}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CARD RENDERER  (with Analyze → button)
# ─────────────────────────────────────────────────────────────────────────────
def _card(stock, side, card_key_suffix=""):
    sym   = stock["ticker"].replace(".SR", "")
    name  = stock.get("name", sym)
    price = stock["price"]
    score = stock["score"]
    rsi   = stock.get("rsi", 50)
    adx   = stock.get("adx", 0)
    vr    = stock.get("vol_ratio", 1)
    obv_r = stock.get("obv_rising", True)
    ab200 = stock.get("above_ema200", True)
    p5d   = stock.get("perf_5d", 0)
    p1m   = stock.get("perf_1m", 0)
    p3m   = stock.get("perf_3m", 0)
    w52p  = stock.get("w52_pos", 50)
    entry = stock.get("entry", price)
    stop  = stock.get("stop_loss", price)
    t1    = stock.get("target1", price)
    rr    = stock.get("rr_ratio", 0)
    conv  = stock.get("conviction", 50)
    setup = stock.get("setup_type", "")
    sigs  = stock.get("signals", [])
    rs_t  = stock.get("rs_vs_tasi", 0)

    stop_pct = abs(entry - stop) / entry * 100 if entry > 0 else 0
    t1_pct   = abs(t1   - entry) / entry * 100 if entry > 0 else 0
    sdsp     = f"+{score}" if score > 0 else str(score)
    ac       = {  "buy": BULL, "sell": BEAR, "hold": NEUT}.get(side, "#888")
    cc       = BULL if conv >= 70 else (INFO if conv >= 45 else NEUT)
    rsic     = BULL if rsi < 35 else (BEAR if rsi > 65 else "#c0c0c0")
    adxc     = BULL if adx > 30 else (NEUT if adx > 20 else "#777")
    vrc      = INFO if vr > 1.5 else "#777"
    ema_c    = BULL if ab200 else BEAR
    obv_c    = BULL if obv_r else BEAR

    def _chip(v, lbl):
        cls = "up" if v > 0 else ("dn" if v < 0 else "neut")
        return f"<span class='sc-chip {cls}'>{lbl} {'+' if v>0 else ''}{v:.1f}%</span>"

    perf_h = (_chip(p5d,"5D") + _chip(p1m,"1M") + _chip(p3m,"3M")
              + f"<span class='sc-chip neut'>52W {w52p:.0f}%</span>"
              + f"<span class='sc-chip neut'>RS {rs_t:+.1f}%</span>")
    tags_h = "".join(f"<span class='sc-sigtag'>{s}</span>" for s in sigs[:4])
    sep_h  = "<span class='sc-dot-sep'>·</span>" if sigs else ""

    st.markdown(
        f'<div class="sc" style="border-left:3px solid {ac};">'
        f'<div class="sc-hd">'
        f'<div style="flex:1">'
        f'<div class="sc-sym {side}">{sym}</div>'
        f'<div class="sc-nameline">'
        f'<span class="sc-name">{name}</span>'
        f'<span class="sc-tag">{setup}</span>'
        f'</div>'
        f'</div>'
        f'<div class="sc-right">'
        f'<div class="sc-price">SAR {price:.2f}</div>'
        f'<div style="text-align:right;">'
        f'<span class="sc-score {side}">{sdsp}</span>'
        f'&nbsp;<span style="font-size:0.7rem;font-weight:700;color:{cc}">{conv}%</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div class="sc-hr"></div>'
        f'<div class="sc-data">'
        f'<div class="sc-levels">'
        f'<div class="sc-lv"><div class="sc-lv-v" style="color:{INFO}">{entry:.2f}</div><div class="sc-lv-l">Entry</div></div>'
        f'<div class="sc-lv"><div class="sc-lv-v" style="color:{BEAR}">-{stop_pct:.1f}%</div><div class="sc-lv-l">Stop</div></div>'
        f'<div class="sc-lv"><div class="sc-lv-v" style="color:{BULL}">+{t1_pct:.1f}%</div><div class="sc-lv-l">T1</div></div>'
        f'<div class="sc-lv" style="border-right:1px solid {BDR}">'
        f'<div class="sc-lv-v" style="color:{NEUT}">{rr:.1f}×</div><div class="sc-lv-l">R:R</div></div>'
        f'</div>'
        f'<div class="sc-inds">'
        f'<div class="sc-ind"><div class="sc-iv" style="color:{rsic}">{rsi:.0f}</div><div class="sc-il">RSI</div></div>'
        f'<div class="sc-ind"><div class="sc-iv" style="color:{adxc}">{adx:.0f}</div><div class="sc-il">ADX</div></div>'
        f'<div class="sc-ind"><div class="sc-iv" style="color:{vrc}">{vr:.1f}×</div><div class="sc-il">Vol</div></div>'
        f'<div class="sc-ind"><div class="sc-iv" style="color:{ema_c}">{"↑" if ab200 else "↓"}EMA</div><div class="sc-il">200</div></div>'
        f'<div class="sc-ind"><div class="sc-iv" style="color:{obv_c}">{"↑" if obv_r else "↓"}OBV</div><div class="sc-il">OBV</div></div>'
        f'</div>'
        f'</div>'
        f'<div class="sc-conv">'
        f'<span class="sc-conv-lbl">Conviction</span>'
        f'<div class="sc-conv-track"><div class="sc-conv-fill" style="width:{conv}%;background:{cc}"></div></div>'
        f'<span class="sc-conv-val" style="color:{cc}">{conv}%</span>'
        f'</div>'
        f'<div class="sc-foot">{perf_h}{sep_h}{tags_h}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Expandable trade plan + Analyze button
    with st.expander(f"Trade plan · {sym}", expanded=False):
        why     = stock.get("why_reasons", [])
        entry_s = stock.get("entry_strategy", "")
        t1_r    = stock.get("t1_reason", "")
        t2_r    = stock.get("t2_reason", "")
        t2      = stock.get("target2", entry)
        t2_pct  = abs(t2 - entry) / entry * 100 if entry > 0 else 0
        ps      = stock.get("pos_size_pct", 10)

        if entry_s:
            st.markdown(
                f"<div style='background:{_rgba(INFO,.07)};border:1px solid {_rgba(INFO,.2)};"
                f"border-left:3px solid {INFO};border-radius:8px;padding:0.65rem 0.9rem;"
                f"font-size:0.76rem;color:#ccc;margin-bottom:0.6rem;'>"
                f"<b style='color:{INFO};'>Entry Strategy</b><br>{entry_s}</div>",
                unsafe_allow_html=True,
            )
        if t1_r:
            t2_html = (
                f"<div style='background:{_rgba(GOLD,.05)};border:1px solid {_rgba(GOLD,.18)};"
                f"border-left:3px solid {GOLD};border-radius:8px;padding:0.65rem 0.9rem;"
                f"font-size:0.76rem;color:#ccc;margin-bottom:0.6rem;'>"
                f"<b style='color:{GOLD};'>Target 2 — {t2:.2f} (+{t2_pct:.1f}%) · size {ps}%</b><br>{t2_r}</div>"
                if t2_r else ""
            )
            st.markdown(
                f"<div style='background:{_rgba(BULL,.06)};border:1px solid {_rgba(BULL,.18)};"
                f"border-left:3px solid {BULL};border-radius:8px;padding:0.65rem 0.9rem;"
                f"font-size:0.76rem;color:#ccc;margin-bottom:0.6rem;'>"
                f"<b style='color:{BULL};'>Target 1 — {t1:.2f} (+{t1_pct:.1f}%)</b><br>{t1_r}</div>"
                f"{t2_html}",
                unsafe_allow_html=True,
            )
        if why:
            st.markdown(
                f"<div style='font-size:0.65rem;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:0.7px;color:#444;margin-bottom:0.45rem;'>Why this stock</div>",
                unsafe_allow_html=True,
            )
            for r in why:
                st.markdown(
                    f"<div style='font-size:0.75rem;color:#aaa;padding:0.4rem 0.75rem;"
                    f"border-left:2px solid {_rgba(ac,.45)};margin-bottom:0.35rem;'>{r}</div>",
                    unsafe_allow_html=True,
                )

        if st.button(f"Analyze {sym} →", key=f"scr_goto_{sym}_{card_key_suffix}",
                     type="secondary", use_container_width=True):
            st.session_state.screener_goto = sym
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SUB-BADGE (indicator / price action scores)
# ─────────────────────────────────────────────────────────────────────────────
def _sub_badge(s):
    sci = s.get("ind_score", 0)
    scp = s.get("pa_score",  0)
    ci  = BULL if sci > 0 else BEAR
    cp_ = BULL if scp > 0 else BEAR
    st.markdown(
        f'<div class="sc-sub">'
        f'<span style="color:{ci}">📊 Indicators {sci:+d}</span>'
        f'<span style="color:#2a2a2a">·</span>'
        f'<span style="color:{cp_}">📈 Price Action {scp:+d}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM FILTER PANEL
# ─────────────────────────────────────────────────────────────────────────────
def _custom_filter_panel():
    all_sectors = list(SECTOR_C.keys())
    with st.expander("🔧 Filter Controls", expanded=True):
        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            f_dir = st.selectbox("Direction", ["Buy Signals", "Sell Signals", "All"],
                                 key="scr_f_dir")
            f_reg = st.multiselect("Regime", ["TREND", "RANGE", "VOLATILE"],
                                   default=[], key="scr_f_regime")
            f_sec = st.multiselect("Sectors", all_sectors,
                                   default=[], key="scr_f_sectors")
        with r1c2:
            f_score   = st.slider("Min Score",       0, 15, 3,          key="scr_f_score")
            f_rsi     = st.slider("RSI Range",       0, 100, (0, 100),  key="scr_f_rsi")
            f_rr      = st.slider("Min R:R",         0.0, 10.0, 1.5, step=0.5, key="scr_f_rr")
        with r1c3:
            f_conv    = st.slider("Min Conviction %",  0, 100, 40,        key="scr_f_conv")
            f_vr      = st.slider("Min Volume Ratio",  0.0, 5.0, 0.0, step=0.25, key="scr_f_vr")
            f_w52     = st.slider("52W Position %",    0, 100, (0, 100),  key="scr_f_w52")
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            f_weekly  = st.selectbox("Weekly Trend",
                                     ["Any","Confirmed Bullish","Confirmed Bearish"],
                                     key="scr_f_weekly")
        with r2c2:
            f_e200    = st.selectbox("EMA 200",
                                     ["Any","Above EMA 200","Below EMA 200"],
                                     key="scr_f_e200")

    def _fn(s):
        sc = s.get("score", 0)
        if f_dir == "Buy Signals"  and sc <= 0: return False
        if f_dir == "Sell Signals" and sc >= 0: return False
        if abs(sc) < f_score: return False
        rsi = s.get("rsi", 50)
        if not (f_rsi[0] <= rsi <= f_rsi[1]): return False
        if s.get("rr_ratio", 0)    < f_rr:    return False
        if s.get("conviction", 0)  < f_conv:  return False
        if s.get("vol_ratio", 1)   < f_vr:    return False
        w52 = s.get("w52_pos", 50)
        if not (f_w52[0] <= w52 <= f_w52[1]): return False
        if f_reg and s.get("regime") not in f_reg:   return False
        if f_sec and s.get("sector") not in f_sec:   return False
        wb = s.get("weekly_bullish")
        if f_weekly == "Confirmed Bullish"  and wb is not True:  return False
        if f_weekly == "Confirmed Bearish"  and wb is not False: return False
        if f_e200 == "Above EMA 200" and not s.get("above_ema200", True): return False
        if f_e200 == "Below EMA 200" and s.get("above_ema200", True):     return False
        return True
    return _fn


# ─────────────────────────────────────────────────────────────────────────────
# SECTOR HEATMAP
# ─────────────────────────────────────────────────────────────────────────────
def _sector_heatmap(stocks):
    if not stocks:
        return
    sdata: dict = {}
    for s in stocks:
        sec = s.get("sector", "Other")
        if sec not in sdata:
            sdata[sec] = []
        sdata[sec].append(s.get("score", 0))
    rows = sorted(
        [(sec, float(np.mean(v)), len(v)) for sec, v in sdata.items()],
        key=lambda x: x[1], reverse=True,
    )
    labels = [r[0] for r in rows]
    vals   = [r[1] for r in rows]
    counts = [r[2] for r in rows]
    colors = [BULL if v > 0 else BEAR for v in vals]
    fig = go.Figure(go.Bar(
        y=labels, x=vals, orientation="h",
        marker_color=colors,
        text=[f"{v:+.1f}  ({c})" for v, c in zip(vals, counts)],
        textposition="auto",
        textfont=dict(size=11, color="#ffffff"),
        hovertemplate="%{y}: avg score %{x:+.1f}<extra></extra>",
    ))
    fig.add_vline(x=0, line_width=1, line_color="#2a2a2a")
    fig.update_layout(
        height=max(180, len(rows) * 32),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", size=11, family=FONT),
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis=dict(showgrid=False, zeroline=False, color="#444"),
        yaxis=dict(showgrid=False, zeroline=False, color="#bbb"),
        bargap=0.28,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# OVERVIEW CHARTS  (mirrors existing Scan All Market charts tab)
# ─────────────────────────────────────────────────────────────────────────────
def _overview_charts(buy_stocks, sell_stocks, hold_stocks, all_stocks):
    _PLOT_BG = "#141414"
    _GRID    = "rgba(255,255,255,0.05)"
    _FONT    = dict(family=FONT, color="#888", size=11)

    if not all_stocks:
        st.markdown("<div class='scr-empty'><div class='scr-empty-icon'>📊</div>No data.</div>",
                    unsafe_allow_html=True)
        return

    ov_c1, ov_c2 = st.columns(2)

    with ov_c1:
        fig_d = go.Figure(go.Pie(
            labels=["Buy", "Sell", "Watch"],
            values=[len(buy_stocks), len(sell_stocks), len(hold_stocks)],
            hole=0.62,
            marker=dict(colors=[BULL, BEAR, NEUT], line=dict(color=_PLOT_BG, width=3)),
            textinfo="label+percent",
            textfont=dict(size=11, family=FONT),
            hovertemplate="%{label}: %{value} stocks<extra></extra>",
        ))
        fig_d.add_annotation(
            text=f"<b>{len(all_stocks)}</b><br><span style='font-size:10px;color:#666'>scanned</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#ececec", family=FONT),
        )
        fig_d.update_layout(
            height=280, plot_bgcolor=_PLOT_BG, paper_bgcolor=_PLOT_BG,
            font=_FONT, margin=dict(t=30, b=10, l=15, r=15), showlegend=False,
            title=dict(text="Signal Distribution", font=dict(size=12, color="#555", family=FONT), x=0),
        )
        st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

    with ov_c2:
        s_buy  = Counter(s.get("sector", "Other") for s in buy_stocks)
        s_sell = Counter(s.get("sector", "Other") for s in sell_stocks)
        secs   = sorted(set(list(s_buy) + list(s_sell)))
        fig_s  = go.Figure()
        fig_s.add_trace(go.Bar(name="Buy",  x=secs, y=[s_buy.get(s, 0)  for s in secs],
                               marker_color=BULL, marker_opacity=0.8))
        fig_s.add_trace(go.Bar(name="Sell", x=secs, y=[s_sell.get(s, 0) for s in secs],
                               marker_color=BEAR, marker_opacity=0.8))
        fig_s.update_layout(
            barmode="group", height=280,
            plot_bgcolor=_PLOT_BG, paper_bgcolor=_PLOT_BG, font=_FONT,
            xaxis=dict(tickangle=-40, gridcolor=_GRID, showgrid=False, tickfont=dict(size=9)),
            yaxis=dict(gridcolor=_GRID),
            margin=dict(t=30, b=80, l=35, r=10),
            legend=dict(orientation="h", y=-0.6, font=dict(size=10)),
            title=dict(text="Signals by Sector", font=dict(size=12, color="#555", family=FONT), x=0),
        )
        st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})

    ov_c3, ov_c4 = st.columns(2)

    with ov_c3:
        if buy_stocks:
            rr_vals = [s.get("rr_ratio", 0) for s in buy_stocks if s.get("rr_ratio", 0) > 0]
            if rr_vals:
                fig_rr = go.Figure(go.Histogram(
                    x=rr_vals, nbinsx=15,
                    marker_color=BULL, marker_opacity=0.75,
                    hovertemplate="R:R %{x:.1f}: %{y} stocks<extra></extra>",
                ))
                fig_rr.update_layout(
                    height=230, plot_bgcolor=_PLOT_BG, paper_bgcolor=_PLOT_BG,
                    font=_FONT, margin=dict(t=30, b=30, l=35, r=10),
                    xaxis=dict(gridcolor=_GRID, color="#555"),
                    yaxis=dict(gridcolor=_GRID, color="#555"),
                    title=dict(text="R:R Distribution (Buy Signals)",
                               font=dict(size=12, color="#555", family=FONT), x=0),
                )
                st.plotly_chart(fig_rr, use_container_width=True, config={"displayModeBar": False})

    with ov_c4:
        if buy_stocks:
            conv_vals = [s.get("conviction", 0) for s in buy_stocks]
            if conv_vals:
                fig_cv = go.Figure(go.Histogram(
                    x=conv_vals, nbinsx=12,
                    marker_color=INFO, marker_opacity=0.75,
                    hovertemplate="Conviction %{x}%%: %{y} stocks<extra></extra>",
                ))
                fig_cv.update_layout(
                    height=230, plot_bgcolor=_PLOT_BG, paper_bgcolor=_PLOT_BG,
                    font=_FONT, margin=dict(t=30, b=30, l=35, r=10),
                    xaxis=dict(gridcolor=_GRID, color="#555"),
                    yaxis=dict(gridcolor=_GRID, color="#555"),
                    title=dict(text="Conviction Distribution",
                               font=dict(size=12, color="#555", family=FONT), x=0),
                )
                st.plotly_chart(fig_cv, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# SORT HELPER
# ─────────────────────────────────────────────────────────────────────────────
_SORT_KEYS = {
    "Priority Score":  lambda x: x.get("priority_score", 0),
    "Conviction %":    lambda x: x.get("conviction", 0),
    "Score":           lambda x: abs(x.get("score", 0)),
    "R:R Ratio":       lambda x: x.get("rr_ratio", 0),
    "Potential %":     lambda x: x.get("potential", 0),
    "RSI":             lambda x: x.get("rsi", 50),
    "Volume Ratio":    lambda x: x.get("vol_ratio", 1),
    "1M Perf":         lambda x: x.get("perf_1m", 0),
}


def _sort_controls():
    sc1, sc2 = st.columns([5, 1])
    with sc1:
        sort_by = st.selectbox(
            "Sort", list(_SORT_KEYS.keys()), index=0,
            key="scr_sort", label_visibility="collapsed",
        )
    with sc2:
        asc = st.toggle("↑", value=False, key="scr_sort_asc")
    fn = _SORT_KEYS.get(sort_by, _SORT_KEYS["Priority Score"])
    return lambda lst: sorted(lst, key=fn, reverse=not asc)


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS: "All Stocks" mode — 6 sub-tabs mirroring existing results page
# ─────────────────────────────────────────────────────────────────────────────
def _all_stocks_view(buy_stocks, sell_stocks, hold_stocks, all_stocks, _sort):
    ind_buy  = _sort([s for s in all_stocks if s.get("ind_score", 0) > 0])
    pa_buy   = _sort([s for s in all_stocks if s.get("pa_score",  0) > 0])
    both_buy = _sort([
        s for s in all_stocks
        if s.get("ind_score", 0) >= 2
        and s.get("pa_score",  0) >= 2
        and s.get("score",     0) >= 4
        and s.get("rr_ratio",  0) >= 2.0
    ])

    tab_ind, tab_pa, tab_perf, tab_sell, tab_hold, tab_ov, tab_heat = st.tabs([
        f"① Technical  {len(ind_buy)}",
        f"② Price Action  {len(pa_buy)}",
        f"③ Perfect Setup ⭐  {len(both_buy)}",
        f"▼ Avoid  {len(sell_stocks)}",
        f"◆ Watch  {len(hold_stocks)}",
        "  Charts  ",
        "  Sectors  ",
    ])

    def _sec_hdr(label, count, cls, note=""):
        note_html = f'<span class="scr-sec-count">{note}</span>' if note else ""
        st.markdown(
            f'<div class="scr-sec">'
            f'<div class="scr-sec-dot" style="background:{"#10a37f" if cls=="buy" else "#ef4444" if cls=="sell" else "#fbbf24"};"></div>'
            f'<span class="scr-sec-title" style="color:{"#10a37f" if cls=="buy" else "#ef4444" if cls=="sell" else "#fbbf24"};">{label}</span>'
            f'<span class="scr-sec-count">{count} stocks</span>'
            f'{note_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with tab_ind:
        _sec_hdr("Technical Indicators say UP", len(ind_buy), "buy",
                 "RSI · MACD · Bollinger · Stochastic · ADX · Volume · OBV")
        if ind_buy:
            for i, s in enumerate(ind_buy):
                _sub_badge(s)
                _card(s, "buy", f"ind_{i}")
        else:
            st.markdown("<div class='scr-empty'><div class='scr-empty-icon'>📊</div>"
                        "No stocks where indicators signal upward.</div>", unsafe_allow_html=True)

    with tab_pa:
        _sec_hdr("Price Action says UP", len(pa_buy), "buy",
                 "EMA Alignment · Golden Cross · 52W · Momentum · RS vs TASI")
        if pa_buy:
            for i, s in enumerate(pa_buy):
                _sub_badge(s)
                _card(s, "buy", f"pa_{i}")
        else:
            st.markdown("<div class='scr-empty'><div class='scr-empty-icon'>📈</div>"
                        "No stocks where price action signals upward.</div>", unsafe_allow_html=True)

    with tab_perf:
        _sec_hdr("⭐ Perfect Setup — High Conviction Only", len(both_buy), "buy",
                 "Ind ≥2 · PA ≥2 · Score ≥4 · R:R ≥2×")
        if both_buy:
            for i, s in enumerate(both_buy):
                _sub_badge(s)
                _card(s, "buy", f"perf_{i}")
        else:
            st.markdown(
                "<div class='scr-empty'><div class='scr-empty-icon'>⭐</div>"
                "No perfect setups right now — stocks in tabs ① and ② may have partial signals.<br>"
                "Market may not be offering ideal conditions today.</div>",
                unsafe_allow_html=True,
            )

    with tab_sell:
        _sec_hdr("Sell / Avoid Signals", len(sell_stocks), "sell")
        if sell_stocks:
            for i, s in enumerate(_sort(sell_stocks)):
                _card(s, "sell", f"sell_{i}")
        else:
            st.markdown("<div class='scr-empty'>No sell signals found.</div>", unsafe_allow_html=True)

    with tab_hold:
        _sec_hdr("Watch List", len(hold_stocks), "hold")
        if hold_stocks:
            for i, s in enumerate(_sort(hold_stocks)):
                _card(s, "hold", f"hold_{i}")
        else:
            st.markdown("<div class='scr-empty'>No neutral stocks.</div>", unsafe_allow_html=True)

    with tab_ov:
        _overview_charts(buy_stocks, sell_stocks, hold_stocks, all_stocks)

    with tab_heat:
        st.markdown(
            f"<div style='font-size:0.75rem;color:#555;margin-bottom:0.7rem;'>"
            f"Average score per sector across {len(all_stocks)} scanned stocks</div>",
            unsafe_allow_html=True,
        )
        _sector_heatmap(all_stocks)


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS: TEMPLATE mode — filtered cards
# ─────────────────────────────────────────────────────────────────────────────
def _template_view(stocks, tmpl_name, tmpl, _sort):
    accent = tmpl["color"]
    filtered = [s for s in stocks if tmpl["filter"](s)] if tmpl["filter"] else stocks
    filtered = _sort(filtered)

    # KPI mini-strip for filtered set
    n   = len(filtered)
    avg_conv = round(float(np.mean([s.get("conviction", 0) for s in filtered])), 1) if filtered else 0
    avg_rr   = round(float(np.mean([s.get("rr_ratio",   0) for s in filtered])), 2) if filtered else 0

    sec_count = Counter(s.get("sector", "Other") for s in filtered)
    top_sec   = max(sec_count, key=sec_count.get) if sec_count else "—"

    cc = BULL if avg_conv >= 60 else NEUT if avg_conv >= 40 else BEAR
    rc = BULL if avg_rr   >= 2  else NEUT if avg_rr   >= 1  else BEAR

    st.markdown(
        f"<div style='display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;"
        f"margin-bottom:1rem;padding:0.7rem 1rem;"
        f"background:{_rgba(accent,.06)};border:1px solid {_rgba(accent,.2)};"
        f"border-radius:10px;'>"
        f"<span style='font-size:1.1rem;font-weight:900;color:{accent};'>{n}</span>"
        f"<span style='font-size:0.68rem;color:#666;'>stocks matched</span>"
        f"<span style='margin-left:0.6rem;font-size:0.82rem;font-weight:800;color:{cc};'>{avg_conv}% conv.</span>"
        f"<span style='font-size:0.68rem;color:#666;'>avg</span>"
        f"<span style='margin-left:0.6rem;font-size:0.82rem;font-weight:800;color:{rc};'>{avg_rr:.1f}×</span>"
        f"<span style='font-size:0.68rem;color:#666;'>R:R</span>"
        f"<span style='margin-left:0.6rem;font-size:0.72rem;color:{INFO};font-weight:700;'>{top_sec}</span>"
        f"<span style='font-size:0.65rem;color:#555;'>top sector</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if n == 0:
        st.markdown(
            f"<div class='scr-empty'><div class='scr-empty-icon'>🔍</div>"
            f"No stocks matched <b>{tmpl_name}</b>.<br>"
            f"Try a different template or re-run the scan with a wider date range.</div>",
            unsafe_allow_html=True,
        )
        return

    side_map = {BULL: "buy", BEAR: "sell", NEUT: "hold"}
    # Infer display side from score sign
    for i, s in enumerate(filtered):
        sc    = s.get("score", 0)
        side_ = "buy" if sc > 0 else ("sell" if sc < 0 else "hold")
        _sub_badge(s)
        _card(s, side_, f"tmpl_{i}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def render_screener():
    from market_data import get_all_tadawul_tickers, run_market_analysis

    _css()

    all_tadawul = get_all_tadawul_tickers()
    total_n     = len(all_tadawul)

    # ── 1. SCAN CONFIG ───────────────────────────────────────────────────────
    ma_results = st.session_state.get("ma_results")

    if "scr_period_idx" not in st.session_state:
        st.session_state.scr_period_idx = 1   # default 6M

    # Header
    st.markdown(
        f"<div style='font-size:1.4rem;font-weight:900;color:#e4e4e4;"
        f"letter-spacing:-0.4px;margin-bottom:0.2rem;'>Market Scanner</div>"
        f"<div style='font-size:0.72rem;color:#404040;margin-bottom:1.2rem;'>"
        f"{total_n} Tadawul stocks · 12 regime-aware indicators · "
        f"ATR-based entry / stop / target levels</div>",
        unsafe_allow_html=True,
    )

    with st.container():
        # Period preset buttons
        preset_cols = st.columns(len(PERIOD_PRESETS) + 2)
        chosen_days = PERIOD_PRESETS[st.session_state.scr_period_idx][1]
        for i, (label, days) in enumerate(PERIOD_PRESETS):
            with preset_cols[i]:
                is_active = (i == st.session_state.scr_period_idx)
                if is_active:
                    st.markdown(
                        f"<style>.st-key-scr_pre_{i} .stButton>button"
                        f"{{border-color:{INFO}!important;color:{INFO}!important;"
                        f"background:{_rgba(INFO,.1)}!important;}}</style>",
                        unsafe_allow_html=True,
                    )
                if st.button(label, key=f"scr_pre_{i}", use_container_width=True):
                    st.session_state.scr_period_idx = i
                    st.rerun()
            chosen_days = PERIOD_PRESETS[st.session_state.scr_period_idx][1]

        # Run button
        with preset_cols[len(PERIOD_PRESETS)]:
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        with preset_cols[len(PERIOD_PRESETS) + 1]:
            run_clicked = st.button(
                "⟳  Run Scan",
                key="scr_run_btn",
                type="secondary",
                use_container_width=True,
            )

    if run_clicked:
        _sd = (datetime.now() - timedelta(days=chosen_days)).date()
        _ed = datetime.now().date()
        tickers = list(all_tadawul.keys())
        with st.spinner(f"Scanning {len(tickers)} stocks over {PERIOD_PRESETS[st.session_state.scr_period_idx][0]}… ~90 sec"):
            res = run_market_analysis(tuple(tickers), min_score=1, start=_sd, end=_ed)
            st.session_state.ma_results       = res
            st.session_state.ma_scanned_count = len(tickers)
            st.session_state.ma_scan_params   = {
                "start":  str(_sd),
                "end":    str(_ed),
                "period": PERIOD_PRESETS[st.session_state.scr_period_idx][0],
            }
            st.session_state.show_market_results = True
        st.rerun()

    # ── No results yet — or results available, offer to view ─────────────────
    if ma_results is None:
        st.markdown(
            f"<div style='text-align:center;padding:3.5rem 2rem;"
            f"background:{BG2};border:1px solid {BDR};border-radius:14px;"
            f"margin-top:1.5rem;'>"
            f"<div style='font-size:2.5rem;margin-bottom:0.7rem;'>🔍</div>"
            f"<div style='font-size:1rem;font-weight:800;color:#ccc;margin-bottom:0.4rem;'>"
            f"No scan data yet</div>"
            f"<div style='font-size:0.78rem;color:#444;'>"
            f"Choose a period above and click <b style='color:{INFO};'>⟳ Run Scan</b></div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    # Results exist — show a "View Results" button that flips to the full results page
    params   = st.session_state.get("ma_scan_params", {})
    scanned  = st.session_state.get("ma_scanned_count", 0)
    p_lbl    = params.get("period", "")
    s_lbl    = params.get("start", "")
    e_lbl    = params.get("end", "")

    n_buy  = len(ma_results.get("buy",  []))
    n_sell = len(ma_results.get("sell", []))
    n_hold = len(ma_results.get("hold", []))

    st.markdown(
        f"<div style='background:{BG2};border:1px solid {BDR};border-radius:12px;"
        f"padding:1.1rem 1.3rem;margin-top:1rem;'>"
        f"<div style='font-size:0.65rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.8px;color:#444;margin-bottom:0.6rem;'>Last Scan</div>"
        f"<div style='display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap;'>"
        f"<span style='font-size:1.1rem;font-weight:900;color:{BULL};'>{n_buy}</span>"
        f"<span style='font-size:0.68rem;color:#555;'>Buy</span>"
        f"<span style='font-size:1.1rem;font-weight:900;color:{BEAR};'>{n_sell}</span>"
        f"<span style='font-size:0.68rem;color:#555;'>Avoid</span>"
        f"<span style='font-size:1.1rem;font-weight:900;color:{NEUT};'>{n_hold}</span>"
        f"<span style='font-size:0.68rem;color:#555;'>Watch</span>"
        f"<span style='font-size:0.68rem;color:#444;margin-left:0.5rem;'>"
        f"{scanned} stocks · {p_lbl}{' · ' + s_lbl + ' → ' + e_lbl if s_lbl else ''}</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    if st.button("📊  View Full Results →", type="secondary",
                 use_container_width=True, key="scr_view_results"):
        st.session_state.show_market_results = True
        st.rerun()
