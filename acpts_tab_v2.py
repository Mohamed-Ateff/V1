"""
ACPTS V15 — Conservative Institutional Quant System
Scoring engine: 110 points max (continuous normalized).
Entry threshold: Score >= 70 (Institutional Grade).
Capital preservation is the absolute priority.

V15 changes vs V14:
  - Fix double-counting: volume/OBV only in Smart Money, not Momentum
  - All factors use continuous normalize() instead of hard thresholds
  - Market regime uses weighted composite score
  - Every score outputs a win-probability via logistic curve
  - Backtest engine in backtest.py uses identical scoring logic
"""

import streamlit as st
import math

# ── Design tokens ───────────────────────────────────────────────────────────
BULL = "#10a37f"
BEAR = "#ef4444"
NEUT = "#fbbf24"
INFO = "#4A9EFF"
GOLD = "#FFD700"
PURP = "#9b87c2"
TEAL = "#26A69A"
BG   = "#141414"
BG2  = "#1c1c1c"
BG3  = "#181818"

REG_CLR = {"TREND": TEAL, "RANGE": NEUT, "VOLATILE": "#FF6B6B"}
REG_LBL = {"TREND": "BULLISH TREND", "RANGE": "SIDEWAYS RANGE", "VOLATILE": "BEARISH / VOLATILE"}
REG_DESC = {
    "TREND": "Active — full risk budget available",
    "RANGE": "Limited — only 1 position allowed",
    "VOLATILE": "Full stop — 100% cash, no entries",
}
REG_ICON = {"TREND": "🟢", "RANGE": "🟡", "VOLATILE": "🔴"}


def _tip(text):
    """Render a small ? info icon with a tooltip."""
    return (f'<span title="{text}" style="font-size:0.5rem;color:#444;'
            f'cursor:help;font-weight:900;margin-left:0.25rem;">&#63;</span>')


def _msr(label, value, accent, sub="", tip_text=""):
    """Metric tile matching the app's _msr_tile pattern."""
    tip = _tip(tip_text) if tip_text else ""
    return (
        f"<div style='background:#181818;border:1px solid #303030;border-top:2px solid {accent};"
        f"border-radius:8px;padding:0.85rem 1rem;text-align:center;'>"
        f"<div style='font-size:0.62rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:0.8px;font-weight:600;margin-bottom:0.35rem;'>{label}{tip}</div>"
        f"<div style='font-size:1.15rem;font-weight:700;color:{accent};line-height:1.1;'>{value}</div>"
        f"<div style='font-size:0.68rem;color:#666;margin-top:0.25rem;font-weight:600;'>{sub}</div>"
        f"</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Normalize helper — continuous scoring, no hard thresholds
# ─────────────────────────────────────────────────────────────────────────────
def normalize(x, min_val, max_val):
    """Linear normalization to [0, 1]. Values outside range are clamped."""
    if max_val <= min_val:
        return 0.0
    if x <= min_val:
        return 0.0
    if x >= max_val:
        return 1.0
    return (x - min_val) / (max_val - min_val)


def rsi_bell(rsi, center=55, spread=15):
    """Bell-curve preference around ideal RSI center."""
    return max(0.0, 1.0 - abs(rsi - center) / spread)


# ─────────────────────────────────────────────────────────────────────────────
# Probabilistic output — score → win probability
# ─────────────────────────────────────────────────────────────────────────────
def score_to_probability(score):
    """Logistic curve mapping score → estimated win probability."""
    return 1.0 / (1.0 + math.exp(-(score - 65) / 5))


# ─────────────────────────────────────────────────────────────────────────────
# Market Regime Detection — weighted composite (V15)
# ─────────────────────────────────────────────────────────────────────────────
def _detect_regime(stocks):
    if not stocks:
        return "RANGE", 0.5
    n = len(stocks)

    # Market breadth
    pct_above_ema200 = sum(1 for s in stocks if s.get('above_ema200', False)) / n * 100
    avg_adx = sum(s.get('adx', 20) for s in stocks) / n

    # Macro: average 3-month return as proxy for index return
    avg_perf3m = sum(s.get('perf_3m', 0) for s in stocks) / n

    # Volatility: average risk % (ATR-based)
    avg_vol = sum(s.get('risk', 2) for s in stocks) / n

    # Component scores (all 0-1) — wider ranges for Saudi market reality
    trend_score    = normalize(pct_above_ema200, 25, 65)
    strength_score = normalize(avg_adx, 12, 30)
    macro_score    = normalize(avg_perf3m, -8, 8)
    vol_score      = 1 - normalize(avg_vol, 1.5, 6)  # lower vol = better

    regime_score = (
        trend_score    * 0.35 +
        strength_score * 0.25 +
        macro_score    * 0.25 +
        vol_score      * 0.15
    )

    if regime_score > 0.55:
        return "TREND", regime_score
    elif regime_score > 0.30:
        return "RANGE", regime_score
    else:
        return "VOLATILE", regime_score


# ─────────────────────────────────────────────────────────────────────────────
# Scoring Engine V15 — 110 pts max, continuous normalized, no double counting
# ─────────────────────────────────────────────────────────────────────────────
def _score_stock(s):
    bd = {}

    # 1. Trend Alignment (0-30) — structure only, no volume
    trend_pts = 0.0
    if s.get('above_ema200', False):
        trend_pts += 10
    if s.get('weekly_bullish', False):
        trend_pts += 10
    if s.get('monthly_bullish', False):
        trend_pts += 5
    rp = s.get('range_pos', 50)
    trend_pts += normalize(50 - rp, 0, 50) * 5  # lower range_pos = better entry
    bd['trend'] = min(round(trend_pts, 1), 30)

    # 2. Momentum (0-20) — ONLY price strength + trend strength
    #    NO volume_ratio or obv_rising (moved to Smart Money)
    adx = s.get('adx', 0)
    perf_5d = s.get('perf_5d', 0)
    price_strength = normalize(perf_5d, -3, 10)
    adx_norm = normalize(adx, 10, 40)
    mom_pts = (adx_norm * 0.7 + price_strength * 0.3) * 20
    bd['momentum'] = min(round(mom_pts, 1), 20)

    # 3. Sector Relative Strength (0-15) — continuous
    rs = s.get('rs_vs_tasi', 0)
    bd['sector_rs'] = round(normalize(rs, -2, 8) * 15, 1)

    # 4. RSI Sweet Spot (0-10) — bell curve around 55
    rsi = s.get('rsi', 50)
    bd['rsi'] = round(rsi_bell(rsi) * 10, 1)

    # 5. Signal Strength (0-10) — continuous from existing score
    raw_score = s.get('score', 0)
    bd['signal'] = round(normalize(raw_score, 0, 18) * 10, 1)

    # 6. Macro Alignment (0-10) — continuous
    macro_pts = 0.0
    if not s.get('tasi_bearish_mkt', False):
        macro_pts += 5
    perf3m = s.get('perf_3m', 0)
    macro_pts += normalize(perf3m, -5, 10) * 5
    bd['macro'] = min(round(macro_pts, 1), 10)

    # 7. Smart Money (0-10) — ONLY volume + OBV (sole owner)
    vol_ratio = s.get('vol_ratio', 1.0)
    obv_rising = 1.0 if s.get('obv_rising', False) else 0.0
    sm_pts = (normalize(vol_ratio, 1.0, 2.5) * 0.6 + obv_rising * 0.4) * 10
    bd['smart_money'] = min(round(sm_pts, 1), 10)

    # 8. Volatility Penalty (-15 to 0) — continuous
    risk_pct = s.get('risk', 0)
    vol_pen = -normalize(risk_pct, 2, 6) * 10  # scales -0 to -10
    eq = s.get('entry_quality', 'Good')
    if eq == 'Poor':
        vol_pen -= 5
    elif eq == 'Fair':
        vol_pen -= 2
    vol_pen = max(round(vol_pen, 1), -15)
    bd['penalty'] = vol_pen

    total = max(0, min(110, round(sum(bd.values()), 1)))
    bd['total'] = total

    # Win probability
    bd['probability'] = round(score_to_probability(total) * 100, 1)

    return total, bd


# ─────────────────────────────────────────────────────────────────────────────
# Render: ACPTS V14 Tab (Main entry point)
# ─────────────────────────────────────────────────────────────────────────────
def render_acpts_tab(all_stocks, scanned_count):
    # ── CSS ──────────────────────────────────────────────────────────────
    st.markdown("""<style>
    .av-empty {
        text-align: center; padding: 2.5rem 1.5rem;
        color: #555; font-size: 0.85rem;
        background: #0e0e0e; border-radius: 12px;
        border: 1px dashed #262626;
    }
    </style>""", unsafe_allow_html=True)

    # ── Header ───────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient(135deg, #0a0a0a 0%, #141414 100%);'
        'border:1px solid #222;border-left:4px solid #FFD700;border-radius:12px;'
        'padding:1.5rem 1.8rem;margin-bottom:1.2rem;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;">'
        '<div>'
        '<div style="font-size:1.3rem;font-weight:900;color:#FFD700;letter-spacing:1px;">'
        'ACPTS V15</div>'
        '<div style="font-size:0.78rem;color:#666;margin-top:0.25rem;line-height:1.5;">'
        'Conservative Institutional Quant Decision Engine'
        f'{_tip("Scores every stock out of 110 points using 8 normalized factors (no double-counting). Outputs win probability via logistic curve. Only stocks scoring 70+ qualify for entry.")}'
        '</div></div>'
        '<div style="text-align:right;">'
        '<div style="font-size:0.55rem;color:#555;font-weight:700;text-transform:uppercase;'
        'letter-spacing:1px;">ENTRY THRESHOLD</div>'
        '<div style="font-size:1.6rem;font-weight:900;color:#FFD700;line-height:1;">70'
        '<span style="font-size:0.7rem;color:#FFD70066;font-weight:600;">/110</span></div>'
        '</div></div></div>',
        unsafe_allow_html=True)

    if not all_stocks:
        st.markdown(
            '<div class="av-empty">No data — run the ACPTS scan first</div>',
            unsafe_allow_html=True)
        return

    # ── Market Regime ────────────────────────────────────────────────────
    regime, regime_score = _detect_regime(all_stocks)
    r_clr = REG_CLR[regime]
    r_lbl = REG_LBL[regime]
    r_desc = REG_DESC[regime]
    r_icon = REG_ICON[regime]
    max_positions = 3 if regime == "TREND" else (1 if regime == "RANGE" else 0)
    regime_pct = round(regime_score * 100)

    n_above200 = sum(1 for s in all_stocks if s.get('above_ema200', False))
    avg_adx = round(sum(s.get('adx', 20) for s in all_stocks) / max(len(all_stocks), 1), 1)
    n_weekly = sum(1 for s in all_stocks if s.get('weekly_bullish', False))
    pct_above = round(n_above200 / max(len(all_stocks), 1) * 100)
    pct_weekly = round(n_weekly / max(len(all_stocks), 1) * 100)

    st.markdown(
        f'<div style="background:linear-gradient(135deg, {r_clr}08 0%, #141414 100%);'
        f'border:1px solid #222;border-left:4px solid {r_clr};border-radius:12px;'
        f'padding:1.3rem 1.5rem;margin-bottom:1rem;">'
        f'<div style="font-size:0.58rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1.2px;margin-bottom:0.5rem;">MARKET REGIME'
        f'{_tip("Weighted composite: Breadth(35%) + ADX Strength(25%) + Macro Return(25%) + Low Volatility(15%). Score > 55% = Trend, 30-55% = Range, < 30% = Volatile.")}'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">'
        f'<div>'
        f'<div style="font-size:1.4rem;font-weight:900;color:{r_clr};line-height:1;">'
        f'{r_icon} {r_lbl}</div>'
        f'<div style="font-size:0.75rem;color:#888;margin-top:0.2rem;">{r_desc}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:0.55rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;">REGIME SCORE</div>'
        f'<div style="font-size:1.5rem;font-weight:900;color:{r_clr};line-height:1;">'
        f'{regime_pct}<span style="font-size:0.7rem;color:{r_clr}66;">%</span></div>'
        f'</div></div>'
        f'<div style="height:6px;background:#1c1c1c;border-radius:3px;overflow:hidden;margin:0.8rem 0 0.6rem;">'
        f'<div style="width:{regime_pct}%;height:100%;background:{r_clr};border-radius:3px;"></div></div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;">'
        + _msr("Above EMA200", f"{pct_above}%", BULL if pct_above > 50 else BEAR,
               tip_text="% of scanned stocks trading above their 200-day EMA. Above 60% = bullish market")
        + _msr("Avg ADX", f"{avg_adx}", "#fff" if avg_adx > 25 else "#666",
               tip_text="Average Directional Index across all stocks. Above 25 = strong trend, below 20 = weak/choppy")
        + _msr("Weekly Bullish", f"{pct_weekly}%", BULL if pct_weekly > 50 else NEUT,
               tip_text="% of stocks with bullish weekly structure (MA20w > MA50w with higher highs/lows)")
        + _msr("Max Positions", f"{max_positions}", r_clr,
               tip_text="Maximum simultaneous positions allowed by the current regime. Bull=3, Range=1, Bear=0")
        + '</div></div>',
        unsafe_allow_html=True)

    # ── VOLATILE REGIME → Warning Banner (but still show tabs) ─────────
    if regime == "VOLATILE":
        st.markdown(
            f'<div class="av-empty" style="border-color:#ef444444;color:#ef4444;padding:1.5rem;">'
            f'<div style="font-size:1.1rem;font-weight:900;margin-bottom:0.3rem;">⚠ FULL STOP — No Entries Allowed</div>'
            f'<div style="font-size:0.8rem;color:#888;line-height:1.6;">'
            f'Bear / Volatile regime detected. Cash is the best position. '
            f'Stocks below are scored for reference only.</div>'
            f'</div>',
            unsafe_allow_html=True)

    # ── Score all stocks ─────────────────────────────────────────────────
    scored = []
    for s in all_stocks:
        if s.get('score', 0) < 1:
            continue
        total, bd = _score_stock(s)
        scored.append({**s, 'v14_score': total, 'v14_bd': bd})
    scored.sort(key=lambda x: x['v14_score'], reverse=True)

    institutional = [s for s in scored if s['v14_score'] >= 70][:max_positions]
    watchlist     = [s for s in scored if 55 <= s['v14_score'] < 70]
    rejected      = [s for s in scored if s['v14_score'] < 55]

    # ── Capital Input ────────────────────────────────────────────────────
    col_cap, col_risk = st.columns([2, 1])
    with col_cap:
        capital = st.number_input(
            "Available Capital (SAR)",
            min_value=10000, max_value=50000000,
            value=st.session_state.get('acpts_capital', 100000),
            step=10000, key='acpts_capital_input')
        st.session_state['acpts_capital'] = capital
    with col_risk:
        risk_level = st.selectbox(
            "Risk per Trade",
            ["0.5% — Ultra Conservative", "1.0% — Conservative"],
            index=0, key='acpts_risk_level')
    risk_pct = 0.5 if "0.5%" in risk_level else 1.0

    # ── Stats Bar ────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;margin:1rem 0;">'
        + _msr("Scanned", str(scanned_count), "#888",
               tip_text="Total number of stocks analyzed in this scan")
        + _msr("Institutional", str(len(institutional)), GOLD,
               sub="Score ≥ 70",
               tip_text="Stocks that passed the 70/110 threshold. These are the only ones approved for entry.")
        + _msr("Watchlist", str(len(watchlist)), INFO,
               sub="Score 55-69",
               tip_text="Close to qualifying but missing points. Monitor for improvement.")
        + _msr("Rejected", str(len(rejected)), "#555",
               sub="Score < 55",
               tip_text="Did not meet minimum criteria. Too risky for institutional-grade entry.")
        + '</div>',
        unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────
    t_inst, t_watch, t_reject, t_rules = st.tabs([
        f"🏛 Institutional ({len(institutional)})",
        f"👁 Watchlist ({len(watchlist)})",
        f"✗ Rejected ({len(rejected)})",
        "📋 System Rules",
    ])

    with t_inst:
        if not institutional:
            st.markdown(
                '<div class="av-empty">'
                '<div style="font-size:1rem;font-weight:800;color:#FFD700;margin-bottom:0.5rem;">'
                'Cash is the Default Decision</div>'
                '<div style="color:#666;">No stock meets the institutional entry threshold '
                '(Score ≥ 70/110).<br>When no opportunity qualifies, staying in cash '
                'protects your capital.</div></div>',
                unsafe_allow_html=True)
        else:
            total_invested = 0
            for idx, s in enumerate(institutional):
                _render_institutional_card(s, idx + 1, capital, risk_pct)
                risk_val = s.get('risk', 2) / 100 * s.get('price', 0)
                if risk_val > 0:
                    pos_value = (capital * risk_pct / 100) / risk_val * s.get('price', 0)
                    total_invested += min(pos_value, capital * 0.30)

            invested_pct = min(round(total_invested / capital * 100), 75) if capital > 0 else 0
            cash_pct = 100 - invested_pct
            total_risk = len(institutional) * risk_pct
            _render_portfolio_summary(institutional, invested_pct, cash_pct, total_risk, max_positions)

    with t_watch:
        if not watchlist:
            st.markdown(
                '<div class="av-empty">No stocks in watchlist range (55-69)</div>',
                unsafe_allow_html=True)
        else:
            for s in watchlist[:10]:
                _render_watch_card(s)

    with t_reject:
        if not rejected:
            st.markdown(
                '<div class="av-empty">No rejected stocks</div>',
                unsafe_allow_html=True)
        else:
            _render_reject_table(rejected[:15])

    with t_rules:
        _render_rules_section()


# ─────────────────────────────────────────────────────────────────────────────
# Card: Institutional Grade (Score >= 70) — matches app.py _render_card style
# ─────────────────────────────────────────────────────────────────────────────
def _render_institutional_card(s, rank, capital, risk_pct):
    sc = s['v14_score']
    bd = s['v14_bd']
    price = s.get('price', 0)
    ticker = s.get('ticker', '?')
    name = s.get('name', ticker)
    sector = s.get('sector', '')
    rsi = s.get('rsi', 0)
    adx = s.get('adx', 0)
    vol_ratio = s.get('vol_ratio', 1.0)

    entry = price
    sl = s.get('stop_loss', 0)
    tp1 = s.get('target1', 0)
    tp2 = s.get('target2', 0)
    rr = s.get('rr_ratio', 0)
    risk_val = s.get('risk', 0)
    eq = s.get('entry_quality', 'Good')

    atr_approx = abs(entry - sl) / 2 if sl > 0 else entry * 0.02
    risk_amt = capital * (risk_pct / 100)
    pos_shares = int(risk_amt / (2 * atr_approx)) if atr_approx > 0 else 0
    pos_shares = int(pos_shares * (sc / 100))
    pos_value = pos_shares * price
    pos_pct = min(round(pos_value / capital * 100, 1), 30) if capital > 0 else 0

    bar_pct = round(sc / 110 * 100)
    bar_clr = GOLD if sc >= 100 else BULL
    rank_colors = {1: GOLD, 2: "#C0C0C0", 3: "#CD7F32"}
    rc = rank_colors.get(rank, BULL)

    # Entry quality badge
    eq_colors = {"Excellent": BULL, "Good": BULL, "Fair": NEUT, "Poor": BEAR}
    eq_clr = eq_colors.get(eq, "#888")

    # Win probability from logistic curve
    win_prob = bd.get('probability', round(score_to_probability(sc) * 100, 1))
    prob_clr = BULL if win_prob >= 65 else NEUT if win_prob >= 55 else BEAR

    # Score confidence
    confidence = round(sc / 110 * 100)
    conf_clr = BULL if confidence >= 85 else NEUT if confidence >= 75 else BEAR

    # Down pct from entry to stop
    down_pct = round((entry - sl) / entry * 100, 1) if entry > 0 and sl > 0 else 0
    # Up pct from entry to target1
    up_pct1 = round((tp1 - entry) / entry * 100, 1) if entry > 0 and tp1 > 0 else 0
    up_pct2 = round((tp2 - entry) / entry * 100, 1) if entry > 0 and tp2 > 0 else 0

    # ── HEADER ───────────────────────────────────────────────────────────
    header_html = (
        f'<div style="background:#141414;border:2px solid #FFD70055;border-radius:14px;'
        f'overflow:hidden;margin-bottom:1rem;box-shadow:0 0 30px rgba(255,215,0,0.04);">'

        # ── Top header row (like app.py cards) ───────────────────────────
        f'<div style="display:flex;align-items:stretch;border-bottom:1px solid #222;">'

        # Rank badge
        f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;'
        f'padding:1.2rem 1rem;border-right:1px solid #262626;min-width:4.5rem;background:#ffffff03;">'
        f'<div style="font-size:0.45rem;font-weight:800;color:#383838;letter-spacing:2.5px;'
        f'text-transform:uppercase;margin-bottom:0.15rem;">RANK</div>'
        f'<div style="font-size:1.8rem;font-weight:900;color:{rc};line-height:1;">{rank}</div>'
        f'</div>'

        # Ticker + Name + Badges
        f'<div style="flex:1;padding:1.1rem 1.4rem;display:flex;flex-direction:column;gap:0.45rem;">'
        f'<div style="display:flex;align-items:center;gap:0.4rem;">'
        f'<span style="font-size:1.25rem;font-weight:900;color:#fff;">{ticker}</span>'
        f'<span style="color:#2a2a2a;font-size:0.9rem;">&#8231;</span>'
        f'<span style="font-size:1.25rem;font-weight:400;color:#7a7a7a;">{name}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;">'
        f'<span style="font-size:0.65rem;padding:0.18rem 0.55rem;border-radius:5px;'
        f'background:{GOLD}15;color:{GOLD};border:1px solid {GOLD}40;font-weight:700;'
        f'letter-spacing:0.3px;">INSTITUTIONAL</span>'
        f'<span style="font-size:0.65rem;padding:0.18rem 0.55rem;border-radius:5px;'
        f'background:{eq_clr}15;color:{eq_clr};border:1px solid {eq_clr}40;font-weight:700;'
        f'letter-spacing:0.3px;">{eq} Entry</span>'
        f'<span style="font-size:0.65rem;padding:0.18rem 0.55rem;border-radius:5px;'
        f'background:#ffffff08;color:#666;border:1px solid #333;font-weight:600;">{sector}</span>'
        f'</div></div>'

        # Right metric boxes (Price, Score, Confidence)
        f'<div style="display:flex;align-items:stretch;gap:0;flex-shrink:0;">'
        # Price
        f'<div style="background:#ffffff08;border-left:1px solid #2a2a2a;'
        f'padding:0.6rem 1rem;text-align:right;min-width:5.5rem;'
        f'display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="font-size:0.58rem;font-weight:700;color:#525252;margin-bottom:0.25rem;">'
        f'Price · SAR</div>'
        f'<div style="font-size:1.35rem;font-weight:900;color:#e0e0e0;line-height:1;">'
        f'{price:.2f}</div></div>'
        # Score
        f'<div style="background:{bar_clr}0e;border-left:1px solid {bar_clr}20;'
        f'padding:0.6rem 1rem;text-align:right;min-width:5.5rem;'
        f'display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:0.2rem;'
        f'margin-bottom:0.25rem;">'
        f'<span style="font-size:0.58rem;font-weight:700;color:{bar_clr}99;">ACPTS Score</span>'
        f'{_tip("Total score from 8 factors: Trend(30) + Momentum(20) + Sector RS(15) + RSI(10) + Signal(10) + Macro(10) + Smart Money(10) − Penalty(15)")}'
        f'</div>'
        f'<div style="font-size:1.35rem;font-weight:900;color:{bar_clr};line-height:1;">'
        f'{sc}<span style="font-size:0.7rem;color:{bar_clr}66;font-weight:600;">/110</span></div>'
        f'</div>'
        # Confidence → Win Probability
        f'<div style="background:{prob_clr}0e;border-left:1px solid {prob_clr}20;'
        f'padding:0.6rem 1rem;text-align:right;min-width:5.5rem;'
        f'display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:0.2rem;'
        f'margin-bottom:0.25rem;">'
        f'<span style="font-size:0.58rem;font-weight:700;color:{prob_clr}99;">Win Prob</span>'
        f'{_tip("Estimated win probability via logistic curve: 1/(1+e^(-(score-65)/5)). Score 70≈73%, 80≈95%. Based on score quality, not historical data yet.")}'
        f'</div>'
        f'<div style="font-size:1.35rem;font-weight:900;color:{prob_clr};line-height:1;">'
        f'{win_prob:.0f}<span style="font-size:0.7rem;color:{prob_clr}66;">%</span></div>'
        f'</div></div></div>'
    )

    # ── SCORE BREAKDOWN ──────────────────────────────────────────────────
    bd_items = [
        ("Trend",       bd.get('trend', 0),      30, TEAL,  "EMA200 (+10) + weekly bullish (+10) + monthly (+5) + range position (0-5 continuous)"),
        ("Momentum",    bd.get('momentum', 0),    20, INFO,  "ADX normalized [10-40] × 0.7 + 5-day price strength × 0.3. No volume here (moved to Smart Money)."),
        ("Sector RS",   bd.get('sector_rs', 0),   15, PURP,  "Relative strength vs TASI, normalized [-2 to 8] continuously"),
        ("RSI",         bd.get('rsi', 0),         10, NEUT,  "Bell curve centered at 55 (±15 spread). Ideal=55, scores 0 at 40 or 70."),
        ("Signal",      bd.get('signal', 0),      10, BULL,  "Existing signal score normalized [0-18] to 0-10 continuously"),
        ("Macro",       bd.get('macro', 0),       10, TEAL,  "Non-bearish TASI (+5) + 3-month performance normalized [-5 to 10] × 5"),
        ("Smart Money", bd.get('smart_money', 0), 10, GOLD,  "Volume ratio normalized [1.0-2.5] × 0.6 + OBV rising × 0.4. Sole owner of volume signals."),
    ]
    pen = bd.get('penalty', 0)

    bd_html = ""
    for lbl, pts, mx, clr, tip_text in bd_items:
        pct = round(pts / mx * 100) if mx > 0 else 0
        bd_html += (
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.25rem 0;">'
            f'<div style="width:75px;font-size:0.62rem;color:#888;text-align:right;font-weight:600;">'
            f'{lbl}{_tip(tip_text)}</div>'
            f'<div style="flex:1;height:6px;background:#1c1c1c;border-radius:3px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;background:{clr};border-radius:3px;"></div></div>'
            f'<div style="width:42px;font-size:0.65rem;color:{clr};font-weight:700;text-align:right;">'
            f'{pts}/{mx}</div></div>'
        )
    if pen < 0:
        bd_html += (
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.25rem 0;">'
            f'<div style="width:75px;font-size:0.62rem;color:#888;text-align:right;font-weight:600;">'
            f'Penalty{_tip("Deducted for high ATR volatility (>3% risk) and poor entry quality (near resistance)")}</div>'
            f'<div style="flex:1;"></div>'
            f'<div style="width:42px;font-size:0.65rem;color:{BEAR};font-weight:700;text-align:right;">'
            f'{pen}</div></div>'
        )

    # ── TRADING PLAN ─────────────────────────────────────────────────────
    trade_html = (
        f'<div style="background:#141414;border-top:1px solid #2a2a2a;border-bottom:1px solid #2a2a2a;'
        f'padding:1rem 1.5rem;">'
        f'<div style="font-size:0.68rem;color:#909090;text-transform:uppercase;letter-spacing:1.2px;'
        f'font-weight:800;margin-bottom:0.8rem;">Your Trading Plan'
        f'{_tip("Entry = buy price. Stop = exit if wrong. T1/T2 = profit targets. R:R = reward÷risk ratio.")}'
        f'</div>'

        # 9-column grid matching app.py
        f'<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr auto 1fr;'
        f'align-items:center;width:100%;gap:0.3rem;">'

        # ENTRY
        f'<div style="text-align:center;background:#1e2a3a;border:1px solid #1e3a5f;'
        f'border-radius:10px;padding:0.7rem 0.5rem;">'
        f'<div style="font-size:1.1rem;font-weight:800;color:{INFO};">{entry:.2f}</div>'
        f'<div style="font-size:0.65rem;color:{INFO};margin-top:3px;font-weight:700;">ENTRY</div></div>'
        f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'

        # STOP
        f'<div style="text-align:center;background:#2a1a1a;border:1px solid #5f1e1e;'
        f'border-radius:10px;padding:0.7rem 0.5rem;">'
        f'<div style="font-size:1.1rem;font-weight:800;color:{BEAR};">{sl:.2f}</div>'
        f'<div style="font-size:0.65rem;color:{BEAR};margin-top:3px;font-weight:700;">'
        f'STOP &nbsp;−{down_pct:.1f}%</div></div>'
        f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'

        # TARGET 1
        f'<div style="text-align:center;background:#1a2a1e;border:1px solid #1e5f2a;'
        f'border-radius:10px;padding:0.7rem 0.5rem;">'
        f'<div style="font-size:1.1rem;font-weight:800;color:{BULL};">{tp1:.2f}</div>'
        f'<div style="font-size:0.65rem;color:{BULL};margin-top:3px;font-weight:700;">'
        f'TARGET 1 &nbsp;+{up_pct1:.1f}%</div></div>'
        f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'

        # TARGET 2
        f'<div style="text-align:center;background:#1a2a28;border:1px solid #1e4f4a;'
        f'border-radius:10px;padding:0.7rem 0.5rem;">'
        f'<div style="font-size:1.1rem;font-weight:800;color:{TEAL};">{tp2:.2f}</div>'
        f'<div style="font-size:0.65rem;color:{TEAL};margin-top:3px;font-weight:700;">'
        f'TARGET 2 &nbsp;+{up_pct2:.1f}%</div></div>'
        f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'

        # R:R
        f'<div style="text-align:center;background:{"#1a2a1e" if rr >= 2 else "#2a2a1a"};'
        f'border:1px solid {"#1e5f2a" if rr >= 2 else "#4f4a1e"};'
        f'border-radius:10px;padding:0.7rem 0.5rem;">'
        f'<div style="font-size:1.1rem;font-weight:800;color:{BULL if rr >= 2 else NEUT};">'
        f'{rr:.1f}x</div>'
        f'<div style="font-size:0.65rem;color:{BULL if rr >= 2 else NEUT};margin-top:3px;'
        f'font-weight:700;">R:R</div></div>'
        f'</div></div>'
    )

    # ── POSITION SIZING ──────────────────────────────────────────────────
    position_html = (
        f'<div style="padding:1rem 1.5rem;border-bottom:1px solid #2a2a2a;">'
        f'<div style="font-size:0.68rem;color:#909090;text-transform:uppercase;letter-spacing:1.2px;'
        f'font-weight:800;margin-bottom:0.7rem;">Position Sizing'
        f'{_tip("Calculated as: (Capital × Risk%) ÷ (2 × ATR) × (Score ÷ 100). Capped at 30% of capital per position.")}'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;">'
        + _msr("Shares", str(pos_shares), "#fff",
               tip_text="Number of shares to buy based on your capital, risk tolerance, and the stock's volatility")
        + _msr("Position Value", f"{pos_value:,.0f}", NEUT,
               sub="SAR",
               tip_text="Total value of this position = shares × current price")
        + _msr("Portfolio %", f"{pos_pct}%", INFO,
               tip_text="What percentage of your total capital this position represents. Capped at 30% max.")
        + _msr("Risk per Trade", f"{risk_pct}%", BEAR,
               tip_text="Maximum capital you're willing to lose on this single trade if stopped out")
        + '</div></div>'
    )

    # ── TECHNICAL SNAPSHOT ───────────────────────────────────────────────
    tech_html = (
        f'<div style="padding:1rem 1.5rem;border-bottom:1px solid #2a2a2a;">'
        f'<div style="font-size:0.68rem;color:#909090;text-transform:uppercase;letter-spacing:1.2px;'
        f'font-weight:800;margin-bottom:0.7rem;">Technical Snapshot'
        f'{_tip("Key technical indicators at the time of scoring")}'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;">'
        + _msr("RSI", f"{rsi:.0f}", BULL if 50 <= rsi <= 65 else (NEUT if 40 <= rsi <= 70 else BEAR),
               tip_text="Relative Strength Index. Ideal zone: 50-65 (momentum without being overbought)")
        + _msr("ADX", f"{adx:.0f}", BULL if adx > 25 else ("#888" if adx > 20 else "#555"),
               tip_text="Average Directional Index. >25 = strong trend, >30 = very strong trend")
        + _msr("Vol Ratio", f"{vol_ratio:.1f}x", BULL if vol_ratio > 1.5 else ("#888" if vol_ratio > 1.2 else "#555"),
               tip_text="Current volume relative to 20-day average. >1.5x suggests institutional interest")
        + _msr("Risk %", f"{risk_val:.1f}%", BEAR if risk_val > 3 else (NEUT if risk_val > 2 else BULL),
               tip_text="Estimated downside risk based on ATR volatility. Lower is better.")
        + '</div></div>'
    )

    # ── SCORE BREAKDOWN SECTION ──────────────────────────────────────────
    breakdown_section = (
        f'<div style="padding:1rem 1.5rem;border-bottom:1px solid #2a2a2a;">'
        f'<div style="font-size:0.68rem;color:#909090;text-transform:uppercase;letter-spacing:1.2px;'
        f'font-weight:800;margin-bottom:0.7rem;">Score Breakdown'
        f'{_tip("How the 110-point total is calculated. Each bar shows what the stock scored vs the maximum possible for that factor.")}'
        f'</div>{bd_html}</div>'
    )

    # ── WHY THIS STOCK ───────────────────────────────────────────────────
    reasons = s.get('why_reasons', [])
    why_html = ""
    if reasons:
        why_items = "".join(
            f'<div style="font-size:0.72rem;color:#888;line-height:1.6;'
            f'padding:0.15rem 0 0.15rem 0.6rem;border-left:2px solid #262626;">'
            f'{i+1}. {r}</div>'
            for i, r in enumerate(reasons[:5])
        )
        why_html = (
            f'<div style="padding:1rem 1.5rem;">'
            f'<div style="font-size:0.68rem;color:#909090;text-transform:uppercase;letter-spacing:1.2px;'
            f'font-weight:800;margin-bottom:0.7rem;">Why This Stock'
            f'{_tip("Key technical and fundamental reasons the system identified this stock as a candidate")}'
            f'</div>{why_items}</div>'
        )

    # ── ASSEMBLE CARD ────────────────────────────────────────────────────
    st.markdown(
        header_html + trade_html + position_html + tech_html + breakdown_section + why_html + '</div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Card: Watchlist (55-69)
# ─────────────────────────────────────────────────────────────────────────────
def _render_watch_card(s):
    sc = s['v14_score']
    bd = s['v14_bd']
    name = s.get('name', s.get('ticker', '?'))
    ticker = s.get('ticker', '?')
    sector = s.get('sector', '')
    price = s.get('price', 0)
    rr = s.get('rr_ratio', 0)
    rsi = s.get('rsi', 0)
    bar_pct = round(sc / 110 * 100)
    gap = 70 - sc
    win_prob = bd.get('probability', round(score_to_probability(sc) * 100, 1))

    # Find weakest areas
    check_items = [(k, v) for k, v in bd.items() if k not in ('total', 'penalty')]
    weakest = sorted(check_items, key=lambda x: x[1])
    weak_labels = {
        'trend': 'Trend', 'momentum': 'Momentum', 'sector_rs': 'Sector RS',
        'rsi': 'RSI', 'signal': 'Signal', 'macro': 'Macro', 'smart_money': 'Smart Money'
    }
    weak_str = ", ".join(f"{weak_labels.get(k, k)}: {v}" for k, v in weakest[:2])

    st.markdown(
        f'<div style="background:#141414;border:1px solid #242424;border-top:3px solid {INFO};'
        f'border-radius:14px;overflow:hidden;margin-bottom:0.8rem;">'

        # Header
        f'<div style="display:flex;align-items:stretch;border-bottom:1px solid #222;">'
        f'<div style="flex:1;padding:1rem 1.4rem;display:flex;flex-direction:column;gap:0.35rem;">'
        f'<div style="display:flex;align-items:center;gap:0.4rem;">'
        f'<span style="font-size:1.1rem;font-weight:900;color:#ccc;">{ticker}</span>'
        f'<span style="color:#2a2a2a;font-size:0.9rem;">&#8231;</span>'
        f'<span style="font-size:1.1rem;font-weight:400;color:#666;">{name}</span></div>'
        f'<div style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;">'
        f'<span style="font-size:0.65rem;padding:0.18rem 0.55rem;border-radius:5px;'
        f'background:{INFO}15;color:{INFO};border:1px solid {INFO}40;font-weight:700;">WATCHLIST</span>'
        f'<span style="font-size:0.65rem;padding:0.18rem 0.55rem;border-radius:5px;'
        f'background:#ffffff08;color:#666;border:1px solid #333;font-weight:600;">{sector}</span>'
        f'</div></div>'

        # Right metrics
        f'<div style="display:flex;align-items:stretch;gap:0;">'
        f'<div style="background:#ffffff08;border-left:1px solid #2a2a2a;'
        f'padding:0.6rem 1rem;text-align:right;min-width:5rem;'
        f'display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="font-size:0.55rem;font-weight:700;color:#525252;">Price</div>'
        f'<div style="font-size:1.2rem;font-weight:900;color:#e0e0e0;">{price:.2f}</div></div>'
        f'<div style="background:{INFO}0e;border-left:1px solid {INFO}20;'
        f'padding:0.6rem 1rem;text-align:right;min-width:5rem;'
        f'display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="font-size:0.55rem;font-weight:700;color:{INFO}99;">Score</div>'
        f'<div style="font-size:1.2rem;font-weight:900;color:{INFO};">{sc}'
        f'<span style="font-size:0.6rem;color:{INFO}66;">/110</span></div></div>'
        f'</div></div>'

        # Info bar
        f'<div style="padding:0.8rem 1.4rem;">'
        f'<div style="height:6px;background:#1c1c1c;border-radius:3px;overflow:hidden;margin-bottom:0.6rem;">'
        f'<div style="width:{bar_pct}%;height:100%;background:{INFO};border-radius:3px;"></div></div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">'
        f'<div style="font-size:0.7rem;color:#666;">'
        f'Needs <span style="color:{NEUT};font-weight:700;">+{gap} pts</span> for entry'
        f'{_tip("Points needed to reach the 70/110 institutional threshold")}'
        f'</div>'
        f'<div style="font-size:0.68rem;color:#555;">'
        f'R:R {rr:.1f}x · Prob {win_prob:.0f}% · Weak: {weak_str}'
        f'</div></div></div></div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Table: Rejected stocks (< 80)
# ─────────────────────────────────────────────────────────────────────────────
def _render_reject_table(stocks):
    if not stocks:
        return
    rows_html = ""
    for s in stocks:
        sc = s['v14_score']
        name = s.get('name', s.get('ticker', '?'))
        ticker = s.get('ticker', '?')
        bar_pct = round(sc / 110 * 100)
        # Identify main weakness
        bd = s.get('v14_bd', {})
        reasons = []
        if bd.get('trend', 0) < 10:
            reasons.append("Weak trend")
        if bd.get('momentum', 0) < 8:
            reasons.append("Low momentum")
        if bd.get('penalty', 0) < -5:
            reasons.append("High volatility")
        if bd.get('rsi', 0) < 4:
            reasons.append("Bad RSI zone")
        reason = ", ".join(reasons[:2]) if reasons else "Below threshold"

        rows_html += (
            f'<div style="display:grid;grid-template-columns:1.5fr 0.5fr 2fr 1.5fr;gap:0.5rem;'
            f'align-items:center;padding:0.45rem 0;border-bottom:1px solid #1a1a1a;">'
            f'<div>'
            f'<span style="font-size:0.78rem;color:#888;font-weight:600;">{name}</span>'
            f'<span style="font-size:0.62rem;color:#444;margin-left:0.4rem;">{ticker}</span></div>'
            f'<div style="font-size:0.82rem;font-weight:800;color:#555;text-align:center;">{sc}</div>'
            f'<div style="height:6px;background:#1c1c1c;border-radius:3px;overflow:hidden;">'
            f'<div style="width:{bar_pct}%;height:100%;background:#333;border-radius:3px;"></div></div>'
            f'<div style="font-size:0.62rem;color:#555;font-style:italic;">{reason}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:#141414;border:1px solid #222;border-radius:12px;'
        f'padding:1rem 1.3rem;">'
        f'<div style="display:grid;grid-template-columns:1.5fr 0.5fr 2fr 1.5fr;gap:0.5rem;'
        f'padding-bottom:0.45rem;border-bottom:1px solid #262626;margin-bottom:0.3rem;">'
        f'<div style="font-size:0.55rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;">Stock</div>'
        f'<div style="font-size:0.55rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;text-align:center;">Score</div>'
        f'<div style="font-size:0.55rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;">Level</div>'
        f'<div style="font-size:0.55rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;">Reason</div>'
        f'</div>{rows_html}</div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio Summary
# ─────────────────────────────────────────────────────────────────────────────
def _render_portfolio_summary(positions, invested_pct, cash_pct, total_risk, max_pos):
    n = len(positions)

    st.markdown(
        f'<div style="background:#0e0e0e;border:1px solid #262626;border-radius:12px;'
        f'padding:1.2rem 1.5rem;margin-top:1rem;">'
        f'<div style="font-size:0.68rem;color:{GOLD};font-weight:800;text-transform:uppercase;'
        f'letter-spacing:1px;margin-bottom:0.8rem;">Portfolio Summary'
        f'{_tip("Overview of your portfolio allocation based on the institutional entries above. Cash reserve should stay ≥25%.")}'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0.5rem;">'
        + _msr("Positions", f"{n}/{max_pos}", "#fff",
               tip_text="Open positions vs maximum allowed by market regime")
        + _msr("Invested", f"{invested_pct}%", NEUT,
               tip_text="Percentage of capital deployed in positions")
        + _msr("Cash", f"{cash_pct}%", BULL,
               tip_text="Remaining cash. System requires minimum 25% cash reserve at all times.")
        + _msr("Total Risk", f"{total_risk:.1f}%", BEAR,
               tip_text="Combined risk exposure across all positions. Should stay below 3%.")
        + _msr("Circuit Breaker", "Normal", BULL,
               tip_text="Monitors cumulative losses. Triggers at: 5% monthly = reduce size, 8% = pause 7 days, 12% = close all")
        + '</div></div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Rules — visual, structured, not just text
# ─────────────────────────────────────────────────────────────────────────────
def _render_rules_section():
    """Render system rules as structured visual sections with explanations."""

    def _rule_card(icon, title, rules_list, accent):
        """Build a single rules section card."""
        items = ""
        for num, (rule, explanation) in enumerate(rules_list, 1):
            items += (
                f'<div style="padding:0.55rem 0;border-bottom:1px solid #1a1a1a;">'
                f'<div style="display:flex;align-items:flex-start;gap:0.5rem;">'
                f'<div style="min-width:22px;height:22px;border-radius:6px;background:{accent}15;'
                f'border:1px solid {accent}30;display:flex;align-items:center;justify-content:center;'
                f'font-size:0.6rem;font-weight:800;color:{accent};flex-shrink:0;">{num}</div>'
                f'<div>'
                f'<div style="font-size:0.78rem;font-weight:700;color:#ccc;line-height:1.4;">{rule}</div>'
                f'<div style="font-size:0.68rem;color:#666;margin-top:0.15rem;line-height:1.5;">{explanation}</div>'
                f'</div></div></div>'
            )
        return (
            f'<div style="background:#141414;border:1px solid #222;border-radius:12px;'
            f'overflow:hidden;margin-bottom:1rem;">'
            f'<div style="background:{accent}08;border-bottom:1px solid {accent}20;'
            f'padding:0.9rem 1.3rem;display:flex;align-items:center;gap:0.5rem;">'
            f'<span style="font-size:1rem;">{icon}</span>'
            f'<span style="font-size:0.72rem;font-weight:800;color:{accent};text-transform:uppercase;'
            f'letter-spacing:1px;">{title}</span></div>'
            f'<div style="padding:0.3rem 1.3rem;">{items}</div></div>'
        )

    # ── Entry Rules ──────────────────────────────────────────────────────
    entry_rules = _rule_card("🏛", "Entry Rules", [
        ("No entry below Score 70/110",
         "The system requires institutional-grade conviction. Anything below 70 is not worth the risk."),
        ("Maximum 3 simultaneous positions",
         "Concentration risk control. Even in a bull market, never hold more than 3 stocks."),
        ("No trading in Bear/Volatile regime",
         "When the regime detector flags bearish conditions, stay 100% cash — no exceptions."),
        ("Range regime = 1 position only",
         "Sideways markets have lower win rates. Limit exposure to a single high-conviction trade."),
        ("Never ignore Market Regime",
         "The regime is determined by aggregate market data (EMA200, ADX, weekly structure). Trust the system."),
    ], GOLD)

    # ── Risk Management ──────────────────────────────────────────────────
    risk_rules = _rule_card("🛡", "Risk Management", [
        ("Risk 0.5%–1% per trade only",
         "Maximum capital at risk per position. 0.5% for ultra-conservative, 1% for conservative mode."),
        ("Never move Stop Loss lower",
         "Once set, the stop can only be moved UP (to lock in profit). Moving it down increases your risk."),
        ("Stop Loss = Entry − 2×ATR (Bull) or 1.5×ATR (Range)",
         "ATR-based stops adapt to each stock's volatility. More volatile = wider stop, fewer shares."),
        ("Maximum 30% of capital per single position",
         "Even if the scoring engine is highly confident, never put more than 30% in one stock."),
        ("Maximum 20% exposure per sector",
         "Diversification rule. If banking stocks score well, still limit banking to 20% of portfolio."),
    ], BEAR)

    # ── Exit Strategy ────────────────────────────────────────────────────
    exit_rules = _rule_card("🎯", "Exit Strategy", [
        ("TP1: Sell 40% at 1.5R profit",
         "Lock in partial profit at 1.5× your risk amount. This secures gains while keeping upside."),
        ("TP2: Sell 30% at 3R profit",
         "Second profit target at 3× risk. Most of your profit comes from these larger moves."),
        ("Remaining 30%: Trailing Stop at 1.5 ATR",
         "Let the final portion ride the trend with a dynamic trailing stop based on volatility."),
        ("Time Stop: Exit if < +0.5R after 7 trading days",
         "If a stock hasn't moved at least half your risk amount in 7 days, the setup has failed — exit."),
    ], BULL)

    # ── Circuit Breaker ──────────────────────────────────────────────────
    cb_rules = _rule_card("🔒", "Circuit Breaker — Capital Protection", [
        ("5% monthly loss → Reduce position size by 50%",
         "First warning level. Cut all new positions to half size until the month resets."),
        ("8% monthly loss → Pause all trading for 7 days",
         "Cool-off period. Review what went wrong before re-entering the market."),
        ("12% cumulative loss → Close ALL positions",
         "Emergency shutdown. Liquidate everything and go to 100% cash for capital preservation."),
        ("Last 5 trades all losers → Reduce risk to 0.5% only",
         "Streak protection. After 5 consecutive losses, switch to minimum risk mode until a winner."),
        ("Minimum 25% cash reserve at all times",
         "Always keep at least 25% of your capital in cash for opportunities and protection."),
    ], NEUT)

    # ── Scoring Engine Reference ─────────────────────────────────────────
    scoring_ref = _rule_card("📊", "Scoring Engine V15 — 110 Points Maximum", [
        ("Trend Alignment (0–30 pts)",
         "EMA200 position (+10) · Weekly bullish (+10) · Monthly bullish (+5) · Range position continuous (0-5)"),
        ("Momentum (0–20 pts) — NO volume/OBV",
         "ADX normalized [10-40] × 70% + 5-day price strength [−3 to 10] × 30%. Volume moved to Smart Money."),
        ("Sector Relative Strength (0–15 pts)",
         "Stock vs TASI performance, normalized continuously from −2% to +8% outperformance"),
        ("RSI Sweet Spot (0–10 pts)",
         "Bell curve centered at 55 (±15 spread). Score = max(0, 1 − |RSI−55|/15) × 10"),
        ("Signal Strength (0–10 pts)",
         "Existing signal score normalized continuously [0-18] → [0-10]"),
        ("Macro Alignment (0–10 pts)",
         "Non-bearish TASI (+5) + 3-month return normalized [−5% to +10%] × 5"),
        ("Smart Money Flow (0–10 pts) — SOLE volume owner",
         "Volume ratio normalized [1.0-2.5] × 60% + OBV rising × 40%. No duplication with Momentum."),
        ("Volatility Penalty (−15 to 0 pts)",
         "Risk normalized [2%-6%] → continuous −10 + entry quality (Poor=−5, Fair=−2)"),
    ], INFO)

    # ── Philosophy ───────────────────────────────────────────────────────
    philosophy = (
        '<div style="background:#141414;border:1px solid #222;border-radius:12px;overflow:hidden;">'
        f'<div style="background:{PURP}08;border-bottom:1px solid {PURP}20;'
        f'padding:0.9rem 1.3rem;display:flex;align-items:center;gap:0.5rem;">'
        f'<span style="font-size:1rem;">🧠</span>'
        f'<span style="font-size:0.72rem;font-weight:800;color:{PURP};text-transform:uppercase;'
        f'letter-spacing:1px;">Core Philosophy</span></div>'
        f'<div style="padding:1.2rem 1.5rem;">'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.8rem;">'

        f'<div style="background:#181818;border:1px solid #262626;border-radius:10px;'
        f'padding:1rem;text-align:center;">'
        f'<div style="font-size:1.5rem;margin-bottom:0.4rem;">🛡</div>'
        f'<div style="font-size:0.82rem;font-weight:700;color:#ccc;margin-bottom:0.3rem;">'
        f'Capital First</div>'
        f'<div style="font-size:0.68rem;color:#666;line-height:1.5;">'
        f'Protecting capital matters more than any single trade. A missed opportunity costs nothing '
        f'— a bad trade costs real money.</div></div>'

        f'<div style="background:#181818;border:1px solid #262626;border-radius:10px;'
        f'padding:1rem;text-align:center;">'
        f'<div style="font-size:1.5rem;margin-bottom:0.4rem;">🚫</div>'
        f'<div style="font-size:0.82rem;font-weight:700;color:#ccc;margin-bottom:0.3rem;">'
        f'Avoided Trade = Protection</div>'
        f'<div style="font-size:0.68rem;color:#666;line-height:1.5;">'
        f'The trade you skip protects your portfolio. Cash is a position. '
        f'Not trading is a valid strategy.</div></div>'

        f'<div style="background:#181818;border:1px solid #262626;border-radius:10px;'
        f'padding:1rem;text-align:center;">'
        f'<div style="font-size:1.5rem;margin-bottom:0.4rem;">🤖</div>'
        f'<div style="font-size:0.82rem;font-weight:700;color:#ccc;margin-bottom:0.3rem;">'
        f'System Decides, Not Emotions</div>'
        f'<div style="font-size:0.68rem;color:#666;line-height:1.5;">'
        f'Every entry, exit, and position size is determined by the scoring engine. '
        f'Emotional trading is not allowed.</div></div>'

        f'</div></div></div>'
    )

    st.markdown(entry_rules, unsafe_allow_html=True)
    st.markdown(risk_rules, unsafe_allow_html=True)
    st.markdown(exit_rules, unsafe_allow_html=True)
    st.markdown(cb_rules, unsafe_allow_html=True)
    st.markdown(scoring_ref, unsafe_allow_html=True)
    st.markdown(philosophy, unsafe_allow_html=True)
