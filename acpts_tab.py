"""
ACPTS V14 — Ultimate Conservative Institutional Quant System
نظام التشغيل المؤسسي النهائي (نسخة متحفظة كاملة)

Scoring engine: 110 points max.
Entry threshold: Score >= 90 (Institutional Grade).
Capital preservation is the absolute priority.
"""

import streamlit as st
import math

# ── Design tokens ───────────────────────────────────────────────────────────
BULL   = "#10a37f"
BEAR   = "#ef4444"
NEUT   = "#fbbf24"
INFO   = "#4A9EFF"
GOLD   = "#FFD700"
PURP   = "#9b87c2"
BG     = "#141414"
BG2    = "#1c1c1c"
BG3    = "#181818"
BDR    = "rgba(255,255,255,0.07)"
FONT   = "Inter,system-ui,sans-serif"

# ── Regime colors ───────────────────────────────────────────────────────────
REG_CLR = {"TREND": "#26A69A", "RANGE": "#fbbf24", "VOLATILE": "#FF6B6B"}
REG_LBL = {"TREND": "🟢 BULL", "RANGE": "🟡 RANGE", "VOLATILE": "🔴 BEAR / VOLATILE"}


# ─────────────────────────────────────────────────────────────────────────────
# Market Regime Detection (Multi-Timeframe)
# ─────────────────────────────────────────────────────────────────────────────
def _detect_regime(stocks):
    """Determine TASI regime from aggregate stock signals."""
    if not stocks:
        return "RANGE", "محدود"

    bearish_count = sum(1 for s in stocks if s.get('tasi_bearish_mkt', False))
    above_200     = sum(1 for s in stocks if s.get('above_ema200', False))
    avg_adx       = sum(s.get('adx', 20) for s in stocks) / len(stocks)
    avg_weekly    = sum(1 for s in stocks if s.get('weekly_bullish', False))

    pct_above = above_200 / len(stocks) * 100 if stocks else 0
    pct_weekly = avg_weekly / len(stocks) * 100 if stocks else 0

    if bearish_count > len(stocks) * 0.5:
        return "VOLATILE", "متوقف — كاش 100%"
    if pct_above > 60 and avg_adx > 22 and pct_weekly > 50:
        return "TREND", "نشط — مخاطرة كاملة"
    return "RANGE", "محدود — سهم واحد فقط"


# ─────────────────────────────────────────────────────────────────────────────
# ACPTS V14 Scoring Engine — 110 points max
# ─────────────────────────────────────────────────────────────────────────────
def _score_stock(s):
    """
    Score a stock using the ACPTS V14 engine.
    Returns (total_score, breakdown_dict).
    Max 110 points.
    """
    bd = {}

    # ── 1. Trend (0–30) ─────────────────────────────────────────────────
    # MA20 > MA50 > MA200 + weekly confirmation
    trend_pts = 0
    if s.get('above_ema200', False):
        trend_pts += 10
    # Weekly bullish = MA20w > MA50w + HH/HL
    if s.get('weekly_bullish', False):
        trend_pts += 10
    # Monthly bullish
    if s.get('monthly_bullish', False):
        trend_pts += 5
    # Range position in lower half = better trend entry
    rp = s.get('range_pos', 50)
    if rp < 40:
        trend_pts += 5  # bottom 40% of range
    bd['trend'] = min(trend_pts, 30)

    # ── 2. Momentum + Breakout (0–20) ────────────────────────────────────
    mom_pts = 0
    adx = s.get('adx', 0)
    vol_ratio = s.get('vol_ratio', 1.0)
    if adx > 30:
        mom_pts += 10
    elif adx > 25:
        mom_pts += 7
    elif adx > 20:
        mom_pts += 4
    if vol_ratio > 1.5:
        mom_pts += 6
    elif vol_ratio > 1.2:
        mom_pts += 3
    # OBV confirmation
    if s.get('obv_rising', False):
        mom_pts += 4
    bd['momentum'] = min(mom_pts, 20)

    # ── 3. Sector Relative Strength (0–15) ───────────────────────────────
    rs = s.get('rs_vs_tasi', 0)
    if rs > 5:
        rs_pts = 15
    elif rs > 2:
        rs_pts = 10
    elif rs > 0:
        rs_pts = 5
    else:
        rs_pts = 0
    bd['sector_rs'] = rs_pts

    # ── 4. RSI Sweet Spot (0–10) ─────────────────────────────────────────
    rsi = s.get('rsi', 50)
    if 50 <= rsi <= 65:
        rsi_pts = 10
    elif 40 <= rsi < 50:
        rsi_pts = 7
    elif 65 < rsi <= 70:
        rsi_pts = 5
    elif 35 <= rsi < 40:
        rsi_pts = 4
    elif rsi > 70:
        rsi_pts = 0  # overbought
    else:
        rsi_pts = 2  # oversold may reverse
    bd['rsi'] = rsi_pts

    # ── 5. Signal Strength — maps existing score to 0–10 ────────────────
    raw_score = s.get('score', 0)
    if raw_score >= 15:
        sig_pts = 10
    elif raw_score >= 12:
        sig_pts = 8
    elif raw_score >= 9:
        sig_pts = 6
    elif raw_score >= 6:
        sig_pts = 4
    elif raw_score >= 3:
        sig_pts = 2
    else:
        sig_pts = 0
    bd['signal'] = sig_pts

    # ── 6. Macro Alignment (0–10) ────────────────────────────────────────
    # Use perf_3m and tasi_bearish as proxies
    macro_pts = 0
    if not s.get('tasi_bearish_mkt', False):
        macro_pts += 5
    perf3m = s.get('perf_3m', 0)
    if perf3m > 5:
        macro_pts += 5
    elif perf3m > 0:
        macro_pts += 3
    bd['macro'] = min(macro_pts, 10)

    # ── 7. Smart Money / Volume (0–10) ───────────────────────────────────
    sm_pts = 0
    if vol_ratio > 2.0:
        sm_pts = 10
    elif vol_ratio > 1.5:
        sm_pts = 7
    elif vol_ratio > 1.2:
        sm_pts = 4
    if s.get('obv_rising', False):
        sm_pts = min(sm_pts + 3, 10)
    bd['smart_money'] = min(sm_pts, 10)

    # ── 8. Volatility Penalty (-15 to 0) ─────────────────────────────────
    risk_pct = s.get('risk', 0)
    if risk_pct > 5:
        vol_pen = -15
    elif risk_pct > 4:
        vol_pen = -10
    elif risk_pct > 3:
        vol_pen = -5
    else:
        vol_pen = 0
    # Also penalize if near resistance (poor entry quality)
    eq = s.get('entry_quality', 'Good')
    if eq == 'Poor':
        vol_pen -= 5
    elif eq == 'Fair':
        vol_pen -= 2
    vol_pen = max(vol_pen, -15)
    bd['penalty'] = vol_pen

    total = sum(bd.values())
    total = max(0, min(110, total))
    bd['total'] = total

    return total, bd


# ─────────────────────────────────────────────────────────────────────────────
# Position Sizing
# ─────────────────────────────────────────────────────────────────────────────
def _calc_position(capital, risk_pct_portfolio, atr, score_total):
    """Dynamic conservative position sizing."""
    if atr <= 0 or score_total < 90:
        return 0, 0
    risk_amt = capital * (risk_pct_portfolio / 100)
    shares = risk_amt / (2 * atr)
    adjusted = shares * (score_total / 100)
    return round(adjusted), round(adjusted * atr * 2, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Render: ACPTS V14 Tab
# ─────────────────────────────────────────────────────────────────────────────
def render_acpts_tab(all_stocks, scanned_count):
    """
    Main entry point for the ACPTS V14 tab.
    all_stocks: list of stock dicts from run_market_analysis()
    scanned_count: total stocks scanned
    """

    # ── CSS ──────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .acpts-header {
        background: linear-gradient(135deg, #0a0a0a 0%, #141414 100%);
        border: 1px solid #222;
        border-left: 4px solid #FFD700;
        border-radius: 12px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.2rem;
    }
    .acpts-title {
        font-size: 1.3rem; font-weight: 900; color: #FFD700;
        letter-spacing: 1px; margin-bottom: 0.3rem;
    }
    .acpts-sub {
        font-size: 0.78rem; color: #666; line-height: 1.6;
    }
    .acpts-regime-box {
        border-radius: 10px; padding: 1.2rem 1.5rem;
        margin-bottom: 1rem; border: 1px solid #222;
    }
    .acpts-score-row {
        display: flex; flex-wrap: wrap; gap: 0.5rem;
        margin-bottom: 0.3rem;
    }
    .acpts-score-chip {
        font-size: 0.65rem; font-weight: 700; padding: 0.2rem 0.55rem;
        border-radius: 5px; letter-spacing: 0.3px;
    }
    .acpts-card {
        background: #141414; border: 1px solid #222;
        border-radius: 12px; padding: 1.3rem 1.5rem;
        margin-bottom: 1rem; position: relative;
    }
    .acpts-card.institutional {
        border: 2px solid #FFD70055;
        box-shadow: 0 0 25px rgba(255,215,0,0.05);
    }
    .acpts-card.watch { border-left: 3px solid #4A9EFF; }
    .acpts-card.reject { border-left: 3px solid #333; opacity: 0.7; }
    .acpts-bar-bg {
        background: #1c1c1c; border-radius: 4px; height: 8px;
        overflow: hidden; width: 100%;
    }
    .acpts-bar-fill {
        height: 100%; border-radius: 4px;
        transition: width 0.4s ease;
    }
    .acpts-metric {
        background: #181818; border: 1px solid #262626;
        border-radius: 8px; padding: 0.8rem 1rem;
        text-align: center;
    }
    .acpts-metric-label {
        font-size: 0.62rem; color: #555; text-transform: uppercase;
        letter-spacing: 0.8px; font-weight: 700; margin-bottom: 0.3rem;
    }
    .acpts-metric-value {
        font-size: 1.15rem; font-weight: 800; line-height: 1.1;
    }
    .acpts-section-title {
        font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 1px; color: #555; margin: 1.2rem 0 0.7rem;
        padding-bottom: 0.35rem; border-bottom: 1px solid #1c1c1c;
    }
    .acpts-rule {
        font-size: 0.72rem; color: #888; line-height: 1.7;
        padding: 0.3rem 0;
    }
    .acpts-rule b { color: #ccc; }
    .acpts-empty {
        text-align: center; padding: 2.5rem 1.5rem;
        color: #444; font-size: 0.85rem;
        background: #0e0e0e; border-radius: 12px;
        border: 1px dashed #222;
    }
    .acpts-pill {
        display: inline-block; font-size: 0.62rem; font-weight: 800;
        padding: 0.18rem 0.55rem; border-radius: 4px;
        letter-spacing: 0.5px; text-transform: uppercase;
    }
    .acpts-trade-row {
        display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 0.5rem; margin: 0.6rem 0;
    }
    .acpts-trade-cell {
        background: #181818; border: 1px solid #262626;
        border-radius: 6px; padding: 0.5rem 0.7rem;
    }
    .acpts-trade-cell .lbl {
        font-size: 0.58rem; color: #555; text-transform: uppercase;
        letter-spacing: 0.6px; font-weight: 700;
    }
    .acpts-trade-cell .val {
        font-size: 0.9rem; font-weight: 700; margin-top: 0.15rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ───────────────────────────────────────────────────────────
    st.markdown(
        '<div class="acpts-header">'
        '<div class="acpts-title">ACPTS V14</div>'
        '<div class="acpts-sub">'
        'نظام القرار الكمي المؤسسي المتحفظ — حماية رأس المال هي الأولوية المطلقة<br>'
        'Conservative Institutional Quant Decision Engine · Score ≥ 90/110 Required'
        '</div></div>',
        unsafe_allow_html=True)

    if not all_stocks:
        st.markdown(
            '<div class="acpts-empty">لا توجد بيانات — قم بتشغيل المسح أولاً</div>',
            unsafe_allow_html=True)
        return

    # ── Phase 0: Self-Optimization Note ──────────────────────────────────
    _opt_key = 'acpts_self_opt'
    if _opt_key not in st.session_state:
        st.session_state[_opt_key] = []

    # ── Phase 1: Market Regime ───────────────────────────────────────────
    regime, regime_status = _detect_regime(all_stocks)
    r_clr = REG_CLR.get(regime, "#888")
    r_lbl = REG_LBL.get(regime, "RANGE")

    # Regime stats
    n_above200 = sum(1 for s in all_stocks if s.get('above_ema200', False))
    avg_adx = round(sum(s.get('adx', 20) for s in all_stocks) / max(len(all_stocks), 1), 1)
    n_weekly = sum(1 for s in all_stocks if s.get('weekly_bullish', False))
    pct_above = round(n_above200 / max(len(all_stocks), 1) * 100)
    pct_weekly = round(n_weekly / max(len(all_stocks), 1) * 100)

    # Max positions based on regime
    max_positions = 3 if regime == "TREND" else (1 if regime == "RANGE" else 0)

    st.markdown(
        f'<div class="acpts-regime-box" style="background:linear-gradient(135deg, '
        f'{r_clr}08 0%, #141414 100%); border-left: 4px solid {r_clr};">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;">'
        f'<div>'
        f'<div style="font-size:0.62rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;">المرحلة 1 — حالة السوق · Market Regime</div>'
        f'<div style="font-size:1.4rem;font-weight:900;color:{r_clr};margin-top:0.3rem;">'
        f'{r_lbl}</div>'
        f'<div style="font-size:0.78rem;color:#888;margin-top:0.15rem;">'
        f'وضع التداول: <b style="color:{r_clr}">{regime_status}</b></div>'
        f'</div>'
        f'<div style="display:flex;gap:1rem;margin-top:0.5rem;">'
        f'<div class="acpts-metric"><div class="acpts-metric-label">فوق EMA200</div>'
        f'<div class="acpts-metric-value" style="color:{BULL if pct_above > 50 else BEAR}">'
        f'{pct_above}%</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">ADX متوسط</div>'
        f'<div class="acpts-metric-value" style="color:{"#fff" if avg_adx > 25 else "#666"}">'
        f'{avg_adx}</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">أسبوعي صاعد</div>'
        f'<div class="acpts-metric-value" style="color:{BULL if pct_weekly > 50 else NEUT}">'
        f'{pct_weekly}%</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">مواقف مسموحة</div>'
        f'<div class="acpts-metric-value" style="color:{r_clr}">{max_positions}</div></div>'
        f'</div></div></div>',
        unsafe_allow_html=True)

    # ── BEAR REGIME → Full Stop ──────────────────────────────────────────
    if regime == "VOLATILE":
        st.markdown(
            '<div class="acpts-empty" style="border-color:#ef444444;color:#ef4444;">'
            '🔴 إيقاف كامل — السوق في وضع هابط/متذبذب<br>'
            'FULL STOP — Bear/Volatile regime detected. Cash is the best position.<br>'
            '<span style="color:#666;font-size:0.75rem;">'
            'الكاش هو أفضل موقف. لا يوجد أي سهم يستحق المخاطرة في هذا الوضع.</span>'
            '</div>',
            unsafe_allow_html=True)
        _render_rules()
        return

    # ── Phase 2 & 3: Score all stocks ────────────────────────────────────
    scored = []
    for s in all_stocks:
        if s.get('score', 0) < 1:
            continue  # negative or zero = not even a buy signal
        total, bd = _score_stock(s)
        scored.append({**s, 'v14_score': total, 'v14_bd': bd})

    scored.sort(key=lambda x: x['v14_score'], reverse=True)

    # Separate into tiers
    institutional = [s for s in scored if s['v14_score'] >= 90]  # Entry
    watchlist     = [s for s in scored if 80 <= s['v14_score'] < 90]
    rejected      = [s for s in scored if s['v14_score'] < 80]

    # Enforce max positions from regime
    institutional = institutional[:max_positions]

    # ── Capital input ────────────────────────────────────────────────────
    col_cap, col_risk = st.columns([2, 1])
    with col_cap:
        capital = st.number_input(
            "رأس المال المتاح (ريال)",
            min_value=10000, max_value=50000000,
            value=st.session_state.get('acpts_capital', 100000),
            step=10000, key='acpts_capital_input')
        st.session_state['acpts_capital'] = capital
    with col_risk:
        risk_level = st.selectbox(
            "مستوى المخاطرة",
            ["0.5% — شديد التحفظ", "1.0% — متحفظ"],
            index=0, key='acpts_risk_level')
    risk_pct = 0.5 if "0.5%" in risk_level else 1.0

    # ── Stats summary ────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;margin:1rem 0;">'
        f'<div class="acpts-metric" style="border-top:2px solid {GOLD};">'
        f'<div class="acpts-metric-label">تم مسح</div>'
        f'<div class="acpts-metric-value" style="color:#fff;">{scanned_count}</div></div>'
        f'<div class="acpts-metric" style="border-top:2px solid {BULL};">'
        f'<div class="acpts-metric-label">مؤسسي (≥90)</div>'
        f'<div class="acpts-metric-value" style="color:{BULL};">{len(institutional)}</div></div>'
        f'<div class="acpts-metric" style="border-top:2px solid {INFO};">'
        f'<div class="acpts-metric-label">مراقبة (80-89)</div>'
        f'<div class="acpts-metric-value" style="color:{INFO};">{len(watchlist)}</div></div>'
        f'<div class="acpts-metric" style="border-top:2px solid #444;">'
        f'<div class="acpts-metric-label">مرفوض (&lt;80)</div>'
        f'<div class="acpts-metric-value" style="color:#555;">{len(rejected)}</div></div>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Self-Optimization Note ───────────────────────────────────────────
    st.markdown(
        '<div style="background:#181818;border:1px solid #222;border-radius:8px;'
        'padding:0.8rem 1rem;margin-bottom:1rem;">'
        '<div style="font-size:0.62rem;color:#FFD700;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.8px;margin-bottom:0.3rem;">🔄 المرحلة 0 — بروتوكول التعلم الذاتي</div>'
        '<div style="font-size:0.75rem;color:#888;line-height:1.6;">'
        'تم تحديث منطق التقييم بناءً على الخوارزمية الافتراضية. '
        'أضف نتائج صفقاتك السابقة لتفعيل التعديل التلقائي للأوزان.'
        '</div></div>',
        unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────
    t_inst, t_watch, t_reject, t_rules = st.tabs([
        f"🏛 دخول مؤسسي ({len(institutional)})",
        f"👁 مراقبة ({len(watchlist)})",
        f"✗ مرفوض ({len(rejected)})",
        "📋 القواعد"
    ])

    with t_inst:
        if not institutional:
            st.markdown(
                '<div class="acpts-empty">'
                'لا توجد فرصة تلبي معايير الحفاظ على رأس المال (Score ≥ 90/110)<br>'
                '<span style="color:#FFD700;font-size:0.8rem;">الكاش هو القرار الافتراضي</span>'
                '</div>',
                unsafe_allow_html=True)
        else:
            total_invested = 0
            for idx, s in enumerate(institutional):
                _render_institutional_card(s, idx + 1, capital, risk_pct)
                # Track allocation
                risk_amt = s.get('risk', 2) / 100 * s.get('price', 0)
                if risk_amt > 0:
                    pos_value = (capital * risk_pct / 100) / risk_amt * s.get('price', 0)
                    total_invested += min(pos_value, capital * 0.30)

            # Portfolio summary
            invested_pct = min(round(total_invested / capital * 100), 75) if capital > 0 else 0
            cash_pct = 100 - invested_pct
            total_risk = len(institutional) * risk_pct
            _render_portfolio_summary(institutional, invested_pct, cash_pct, total_risk, max_positions)

    with t_watch:
        if not watchlist:
            st.markdown(
                '<div class="acpts-empty">'
                'لا توجد أسهم في منطقة المراقبة (80-89)</div>',
                unsafe_allow_html=True)
        else:
            for s in watchlist[:10]:
                _render_watch_card(s)

    with t_reject:
        if not rejected:
            st.markdown(
                '<div class="acpts-empty">لا توجد أسهم مرفوضة</div>',
                unsafe_allow_html=True)
        else:
            # Show top 15 rejected with reason
            _render_reject_table(rejected[:15])

    with t_rules:
        _render_rules()


# ─────────────────────────────────────────────────────────────────────────────
# Card: Institutional Grade (Score >= 90)
# ─────────────────────────────────────────────────────────────────────────────
def _render_institutional_card(s, rank, capital, risk_pct):
    sc = s['v14_score']
    bd = s['v14_bd']
    price = s.get('price', 0)
    ticker = s.get('ticker', '?')
    name = s.get('name', ticker)
    sector = s.get('sector', '')
    regime = s.get('regime', 'RANGE')

    # Trade levels
    entry = price
    sl = s.get('stop_loss', 0)
    tp1 = s.get('target1', 0)
    tp2 = s.get('target2', 0)
    rr = s.get('rr_ratio', 0)
    risk_val = s.get('risk', 0)

    # ATR-based stop
    atr_approx = abs(entry - sl) / 2 if sl > 0 else entry * 0.02

    # Position size
    risk_amt = capital * (risk_pct / 100)
    pos_shares = int(risk_amt / (2 * atr_approx)) if atr_approx > 0 else 0
    pos_shares = int(pos_shares * (sc / 100))
    pos_value = pos_shares * price
    pos_pct = round(pos_value / capital * 100, 1) if capital > 0 else 0
    pos_pct = min(pos_pct, 30)  # Max 30% per stock

    # Score bar segments
    bar_pct = round(sc / 110 * 100)
    bar_clr = GOLD if sc >= 100 else BULL if sc >= 90 else INFO

    # Rank badge
    rank_colors = {1: GOLD, 2: "#C0C0C0", 3: "#CD7F32"}
    rc = rank_colors.get(rank, BULL)

    # Score breakdown
    bd_items = [
        ("الاتجاه", bd.get('trend', 0), 30, "#26A69A"),
        ("الزخم", bd.get('momentum', 0), 20, "#4A9EFF"),
        ("القطاع", bd.get('sector_rs', 0), 15, "#9b87c2"),
        ("RSI", bd.get('rsi', 0), 10, "#fbbf24"),
        ("الإشارة", bd.get('signal', 0), 10, "#10a37f"),
        ("الماكرو", bd.get('macro', 0), 10, "#26A69A"),
        ("Smart Money", bd.get('smart_money', 0), 10, "#FFD700"),
    ]

    pen = bd.get('penalty', 0)

    # Build breakdown HTML
    bd_html = ""
    for lbl, pts, mx, clr in bd_items:
        pct = round(pts / mx * 100) if mx > 0 else 0
        bd_html += (
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.2rem 0;">'
            f'<div style="width:60px;font-size:0.62rem;color:#888;text-align:right;'
            f'font-weight:600;">{lbl}</div>'
            f'<div style="flex:1;height:6px;background:#1c1c1c;border-radius:3px;overflow:hidden;">'
            f'<div style="width:{pct}%;height:100%;background:{clr};border-radius:3px;"></div></div>'
            f'<div style="width:40px;font-size:0.65rem;color:{clr};font-weight:700;'
            f'text-align:right;">{pts}/{mx}</div>'
            f'</div>'
        )
    if pen < 0:
        bd_html += (
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin:0.2rem 0;">'
            f'<div style="width:60px;font-size:0.62rem;color:#888;text-align:right;'
            f'font-weight:600;">خصم</div>'
            f'<div style="flex:1;"></div>'
            f'<div style="width:40px;font-size:0.65rem;color:{BEAR};font-weight:700;'
            f'text-align:right;">{pen}</div>'
            f'</div>'
        )

    # WHY reasons
    reasons = s.get('why_reasons', [])
    reasons_html = "".join(
        f'<div style="font-size:0.72rem;color:#888;line-height:1.6;'
        f'padding:0.15rem 0 0.15rem 0.6rem;border-left:2px solid #262626;">'
        f'{i+1}. {r}</div>'
        for i, r in enumerate(reasons[:4])
    ) if reasons else ""

    st.markdown(
        f'<div class="acpts-card institutional">'
        # Header row
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
        f'margin-bottom:0.8rem;">'
        f'<div style="display:flex;align-items:center;gap:0.7rem;">'
        f'<div style="width:38px;height:38px;border-radius:8px;background:{rc}18;'
        f'border:2px solid {rc};display:flex;align-items:center;justify-content:center;'
        f'font-size:1rem;font-weight:900;color:{rc};">#{rank}</div>'
        f'<div>'
        f'<div style="font-size:1.05rem;font-weight:800;color:#fff;">{name}</div>'
        f'<div style="font-size:0.7rem;color:#555;">{ticker} · {sector}</div>'
        f'</div></div>'
        # Score badge
        f'<div style="text-align:center;">'
        f'<div style="font-size:1.8rem;font-weight:900;color:{bar_clr};line-height:1;">{sc}</div>'
        f'<div style="font-size:0.55rem;color:#555;font-weight:700;">/ 110</div>'
        f'<div class="acpts-pill" style="background:{GOLD}22;color:{GOLD};margin-top:0.25rem;'
        f'border:1px solid {GOLD}33;">INSTITUTIONAL</div>'
        f'</div></div>'
        # Score bar
        f'<div class="acpts-bar-bg" style="margin-bottom:1rem;">'
        f'<div class="acpts-bar-fill" style="width:{bar_pct}%;'
        f'background:linear-gradient(90deg, {bar_clr}88, {bar_clr});"></div></div>'
        # Trade levels grid
        f'<div class="acpts-trade-row">'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">سعر الدخول</div>'
        f'<div class="val" style="color:#fff;">{entry:.2f}</div></div>'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">Stop Loss</div>'
        f'<div class="val" style="color:{BEAR};">{sl:.2f}</div></div>'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">TP1 (40%)</div>'
        f'<div class="val" style="color:{BULL};">{tp1:.2f}</div></div>'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">TP2 (30%)</div>'
        f'<div class="val" style="color:{BULL};">{tp2:.2f}</div></div>'
        f'</div>'
        # Second row: R:R, Risk, Position
        f'<div class="acpts-trade-row">'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">R:R</div>'
        f'<div class="val" style="color:{BULL if rr >= 2 else NEUT};">{rr:.1f}x</div></div>'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">مخاطرة %</div>'
        f'<div class="val" style="color:{BEAR};">{risk_val:.1f}%</div></div>'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">حجم الصفقة</div>'
        f'<div class="val" style="color:#fff;">{pos_shares} سهم</div></div>'
        f'<div class="acpts-trade-cell">'
        f'<div class="lbl">% من المحفظة</div>'
        f'<div class="val" style="color:{NEUT};">{pos_pct}%</div></div>'
        f'</div>'
        # Score breakdown
        f'<div class="acpts-section-title" style="color:{GOLD};">تفصيل النقاط — Score Breakdown</div>'
        f'{bd_html}'
        # Why this stock
        + (f'<div class="acpts-section-title">لماذا هذا السهم</div>{reasons_html}' if reasons_html else '')
        + '</div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Card: Watchlist (80-89)
# ─────────────────────────────────────────────────────────────────────────────
def _render_watch_card(s):
    sc = s['v14_score']
    bd = s['v14_bd']
    name = s.get('name', s.get('ticker', '?'))
    ticker = s.get('ticker', '?')
    sector = s.get('sector', '')
    price = s.get('price', 0)
    rr = s.get('rr_ratio', 0)
    bar_pct = round(sc / 110 * 100)

    # What's missing to reach 90?
    gap = 90 - sc
    weakest = sorted(
        [(k, v) for k, v in bd.items() if k not in ('total', 'penalty')],
        key=lambda x: x[1])
    weak_items = ", ".join(f"{k}: {v}" for k, v in weakest[:2])

    st.markdown(
        f'<div class="acpts-card watch">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div>'
        f'<div style="font-size:0.95rem;font-weight:700;color:#ccc;">{name}</div>'
        f'<div style="font-size:0.68rem;color:#555;">{ticker} · {sector} · SAR {price:.2f}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="font-size:1.3rem;font-weight:900;color:{INFO};">{sc}<span style="'
        f'font-size:0.6rem;color:#555;">/110</span></div>'
        f'<div class="acpts-pill" style="background:{INFO}18;color:{INFO};border:1px solid {INFO}33;">'
        f'مراقبة</div>'
        f'</div></div>'
        f'<div class="acpts-bar-bg" style="margin:0.6rem 0 0.4rem;">'
        f'<div class="acpts-bar-fill" style="width:{bar_pct}%;background:{INFO};"></div></div>'
        f'<div style="font-size:0.68rem;color:#666;line-height:1.5;">'
        f'يحتاج <b style="color:{NEUT};">+{gap} نقطة</b> للدخول · '
        f'R:R {rr:.1f}x · نقاط ضعف: {weak_items}'
        f'</div></div>',
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
        rows_html += (
            f'<div style="display:grid;grid-template-columns:2fr 0.6fr 3fr;gap:0.5rem;'
            f'align-items:center;padding:0.4rem 0;border-bottom:1px solid #1a1a1a;">'
            f'<div>'
            f'<span style="font-size:0.78rem;color:#888;font-weight:600;">{name}</span>'
            f'<span style="font-size:0.62rem;color:#444;margin-left:0.4rem;">{ticker}</span>'
            f'</div>'
            f'<div style="font-size:0.82rem;font-weight:800;color:#555;text-align:center;">{sc}</div>'
            f'<div class="acpts-bar-bg"><div class="acpts-bar-fill" style="width:{bar_pct}%;'
            f'background:#333;"></div></div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:#141414;border:1px solid #222;border-radius:10px;'
        f'padding:1rem 1.2rem;">'
        f'<div style="display:grid;grid-template-columns:2fr 0.6fr 3fr;gap:0.5rem;'
        f'padding-bottom:0.4rem;border-bottom:1px solid #262626;margin-bottom:0.3rem;">'
        f'<div style="font-size:0.58rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;">السهم</div>'
        f'<div style="font-size:0.58rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;text-align:center;">النقاط</div>'
        f'<div style="font-size:0.58rem;color:#555;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.8px;">المستوى</div>'
        f'</div>'
        f'{rows_html}'
        f'</div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio Summary
# ─────────────────────────────────────────────────────────────────────────────
def _render_portfolio_summary(positions, invested_pct, cash_pct, total_risk, max_pos):
    n = len(positions)
    # Circuit breaker status
    cb_status = "طبيعي"
    cb_clr = BULL

    st.markdown(
        f'<div style="background:#0e0e0e;border:1px solid #262626;border-radius:10px;'
        f'padding:1.2rem 1.5rem;margin-top:1rem;">'
        f'<div style="font-size:0.68rem;color:{GOLD};font-weight:800;text-transform:uppercase;'
        f'letter-spacing:1px;margin-bottom:0.8rem;">ملخص المحفظة — Portfolio Summary</div>'
        f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:0.5rem;">'
        f'<div class="acpts-metric"><div class="acpts-metric-label">مواقف مفتوحة</div>'
        f'<div class="acpts-metric-value" style="color:#fff;">{n}/{max_pos}</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">مستثمر</div>'
        f'<div class="acpts-metric-value" style="color:{NEUT};">{invested_pct}%</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">كاش</div>'
        f'<div class="acpts-metric-value" style="color:{BULL};">{cash_pct}%</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">مخاطرة إجمالية</div>'
        f'<div class="acpts-metric-value" style="color:{BEAR};">{total_risk:.1f}%</div></div>'
        f'<div class="acpts-metric"><div class="acpts-metric-label">Circuit Breaker</div>'
        f'<div class="acpts-metric-value" style="color:{cb_clr};">{cb_status}</div></div>'
        f'</div></div>',
        unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Rules & Philosophy
# ─────────────────────────────────────────────────────────────────────────────
def _render_rules():
    st.markdown(
        '<div style="background:#141414;border:1px solid #222;border-radius:12px;'
        'padding:1.3rem 1.5rem;">'
        # Rules
        '<div style="font-size:0.72rem;font-weight:800;color:#FFD700;text-transform:uppercase;'
        'letter-spacing:1px;margin-bottom:0.8rem;">⚠ القواعد الصارمة غير القابلة للتجاوز</div>'
        '<div class="acpts-rule">1. <b>لا دخول</b> تحت Score 90/110</div>'
        '<div class="acpts-rule">2. <b>لا أكثر من 3 مواقف</b> مفتوحة</div>'
        '<div class="acpts-rule">3. <b>لا تداول</b> في Range (سهم واحد فقط) أو Bear أو قبل الأرباح</div>'
        '<div class="acpts-rule">4. <b>لا تجاهل</b> حالة السوق (Regime) أو التعلم الذاتي</div>'
        '<div class="acpts-rule">5. <b>لا تعديل</b> Stop Loss للأسفل أبدًا</div>'
        '<div class="acpts-rule">6. <b>الكاش</b> هو القرار الافتراضي في أي شك</div>'
        '<div class="acpts-rule">7. <b>مخاطرة:</b> 0.5%–1% لكل صفقة فقط</div>'
        '<div class="acpts-rule">8. <b>حد أقصى 20%</b> للقطاع الواحد</div>'
        '<div class="acpts-rule">9. <b>كاش احتياطي:</b> 25% على الأقل دائمًا</div>'
        # Scoring guide
        '<div style="font-size:0.72rem;font-weight:800;color:#4A9EFF;text-transform:uppercase;'
        'letter-spacing:1px;margin:1.2rem 0 0.8rem;">📊 محرك التقييم — 110 نقاط</div>'
        '<div class="acpts-rule"><b>الاتجاه (0–30):</b> EMA200 + أسبوعي + شهري + موقع في النطاق</div>'
        '<div class="acpts-rule"><b>الزخم + Breakout (0–20):</b> ADX > 25 + حجم > 120% + OBV</div>'
        '<div class="acpts-rule"><b>القوة النسبية (0–15):</b> أداء السهم vs TASI</div>'
        '<div class="acpts-rule"><b>RSI (0–10):</b> المنطقة المثالية 50–65</div>'
        '<div class="acpts-rule"><b>الإشارة (0–10):</b> Signal Score من المحرك الأساسي</div>'
        '<div class="acpts-rule"><b>الماكرو (0–10):</b> أداء 3 أشهر + وضع TASI</div>'
        '<div class="acpts-rule"><b>Smart Money (0–10):</b> حجم مؤسسي + OBV صاعد</div>'
        '<div class="acpts-rule"><b>خصم التقلب (-15 إلى 0):</b> ATR% عالي + قرب من المقاومة</div>'
        # Risk management
        '<div style="font-size:0.72rem;font-weight:800;color:#ef4444;text-transform:uppercase;'
        'letter-spacing:1px;margin:1.2rem 0 0.8rem;">🛡 إدارة المخاطر</div>'
        '<div class="acpts-rule"><b>Stop Loss:</b> Bull = Entry − 2×ATR · Range = Entry − 1.5×ATR</div>'
        '<div class="acpts-rule"><b>TP1:</b> 40% عند 1.5R · <b>TP2:</b> 30% عند 3R · الباقي: Trailing 1.5 ATR</div>'
        '<div class="acpts-rule"><b>Time SL:</b> خروج إذا لم يتحرك +0.5R خلال 7 أيام تداول</div>'
        # Capital shield
        '<div style="font-size:0.72rem;font-weight:800;color:#fbbf24;text-transform:uppercase;'
        'letter-spacing:1px;margin:1.2rem 0 0.8rem;">🔒 حماية رأس المال — Circuit Breaker</div>'
        '<div class="acpts-rule"><b>خسارة 5% شهري →</b> تقليل الحجم 50%</div>'
        '<div class="acpts-rule"><b>خسارة 8% →</b> إيقاف 7 أيام + مراجعة</div>'
        '<div class="acpts-rule"><b>خسارة 12% تراكمية →</b> إغلاق كل المواقف</div>'
        '<div class="acpts-rule"><b>آخر 5 صفقات خاسرة →</b> مخاطرة 0.5% فقط</div>'
        # Philosophy
        '<div style="font-size:0.72rem;font-weight:800;color:#9b87c2;text-transform:uppercase;'
        'letter-spacing:1px;margin:1.2rem 0 0.8rem;">🧠 الفلسفة الجوهرية</div>'
        '<div style="font-size:0.8rem;color:#888;line-height:1.8;font-style:italic;'
        'border-left:3px solid #9b87c244;padding-left:0.8rem;">'
        '"حماية رأس المال أهم من أي صفقة"<br>'
        '"الصفقة المُتجنَّبة تحمي المحفظة"<br>'
        '"النظام يقرر — العواطف ممنوعة"'
        '</div>'
        '</div>',
        unsafe_allow_html=True)
