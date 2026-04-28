"""
trade_journal.py
────────────────
Full trade journal: log trades, auto-track outcomes, review & learn.
Opens as a full page like render_champions_vault_page().
"""
from __future__ import annotations
import streamlit as st
from datetime import date, datetime
import uuid

from auth import load_trades, upsert_trade, delete_trade, init_trade_journal


# ── Auto-init DB table on first import ───────────────────────────────────────
init_trade_journal()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user() -> str:
    return st.session_state.get('auth_username', '')


def _fetch_current_price(symbol: str) -> float | None:
    try:
        import yfinance as yf
        sym = symbol if symbol.endswith('.SR') else symbol
        _t  = yf.Ticker(sym)
        _h  = _t.history(period='2d', interval='1d', auto_adjust=True)
        if _h is not None and len(_h) > 0:
            return float(_h['Close'].iloc[-1])
    except Exception:
        pass
    return None


def _auto_update_trade(trade: dict) -> dict:
    """Fetch live price and update status/outcome fields if still OPEN."""
    if trade.get('status') != 'OPEN':
        return trade
    price = _fetch_current_price(trade['symbol'])
    if price is None:
        return trade

    ep  = float(trade.get('entry_price', 0))
    sl  = float(trade.get('stop_loss', 0))
    t1  = trade.get('target1')
    t2  = trade.get('target2')
    t3  = trade.get('target3')
    cap = float(trade.get('capital', 0))
    direction = trade.get('direction', 'LONG')

    # days held
    try:
        ed = datetime.strptime(trade['entry_date'], '%Y-%m-%d').date()
        days = (date.today() - ed).days
    except Exception:
        days = None

    risk_per_share = abs(ep - sl) if sl and ep else 1

    if direction == 'LONG':
        hit_stop = price <= sl if sl else False
        hit_t1   = price >= t1 if t1 else False
        hit_t2   = price >= t2 if t2 else False
        hit_t3   = price >= t3 if t3 else False
        pnl_pct  = (price - ep) / ep * 100 if ep else 0
    else:
        hit_stop = price >= sl if sl else False
        hit_t1   = price <= t1 if t1 else False
        hit_t2   = price <= t2 if t2 else False
        hit_t3   = price <= t3 if t3 else False
        pnl_pct  = (ep - price) / ep * 100 if ep else 0

    pnl_amount = cap * pnl_pct / 100 if cap else 0
    r_multiple = pnl_pct / (risk_per_share / ep * 100) if ep and risk_per_share else 0
    hit_target = int(hit_t3 or hit_t2 or hit_t1)

    updated = dict(trade)
    updated['days_held']  = days
    updated['pnl_pct']    = round(pnl_pct, 2)
    updated['pnl_amount'] = round(pnl_amount, 2)
    updated['r_multiple'] = round(r_multiple, 2)
    updated['hit_target'] = hit_target
    updated['hit_stop']   = int(hit_stop)
    updated['current_price'] = price  # runtime only, not persisted

    # auto-close if stop or highest target hit
    best_target = t3 or t2 or t1
    if hit_stop or (best_target and hit_target):
        exit_p = sl if hit_stop else best_target
        updated['status']     = 'CLOSED'
        updated['exit_price'] = exit_p
        updated['exit_date']  = str(date.today())
        if direction == 'LONG':
            final_pnl = (exit_p - ep) / ep * 100
        else:
            final_pnl = (ep - exit_p) / ep * 100
        updated['pnl_pct']    = round(final_pnl, 2)
        updated['pnl_amount'] = round(cap * final_pnl / 100, 2)
        updated['r_multiple'] = round(final_pnl / (risk_per_share / ep * 100), 2) if ep and risk_per_share else 0
        upsert_trade(_user(), updated)

    return updated


def _load_and_refresh() -> list:
    """Load trades from DB and auto-update open ones."""
    trades = load_trades(_user())
    refreshed = []
    for t in trades:
        refreshed.append(_auto_update_trade(t))
    return refreshed


# ── Stats ─────────────────────────────────────────────────────────────────────

def _compute_stats(trades: list) -> dict:
    closed = [t for t in trades if t.get('status') == 'CLOSED']
    open_  = [t for t in trades if t.get('status') == 'OPEN']
    wins   = [t for t in closed if (t.get('pnl_pct') or 0) > 0]
    losses = [t for t in closed if (t.get('pnl_pct') or 0) <= 0]

    win_rate  = len(wins) / len(closed) * 100 if closed else 0
    avg_win   = sum(t.get('pnl_pct', 0) for t in wins)   / len(wins)   if wins   else 0
    avg_loss  = sum(t.get('pnl_pct', 0) for t in losses) / len(losses) if losses else 0
    total_pnl = sum(t.get('pnl_amount', 0) for t in closed)
    avg_r     = sum(t.get('r_multiple', 0) for t in closed) / len(closed) if closed else 0

    # streak
    streak = 0
    for t in sorted(closed, key=lambda x: x.get('exit_date', ''), reverse=True):
        if (t.get('pnl_pct') or 0) > 0:
            if streak >= 0:
                streak += 1
            else:
                break
        else:
            if streak <= 0:
                streak -= 1
            else:
                break

    return {
        'total': len(trades), 'open': len(open_), 'closed': len(closed),
        'wins': len(wins), 'losses': len(losses),
        'win_rate': win_rate, 'avg_win': avg_win, 'avg_loss': avg_loss,
        'total_pnl': total_pnl, 'avg_r': avg_r, 'streak': streak,
    }


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display:none !important; }

.main .block-container, div.block-container {
    max-width: 96% !important;
    padding: 1.6rem 2rem 5rem !important;
}

/* ── top bar ── */
.tj-topbar {
    display:flex; align-items:center; gap:1.2rem;
    margin-bottom:1.8rem; flex-wrap:wrap;
}
.tj-title {
    font-size:1.55rem; font-weight:900; color:#e8e8e8;
    letter-spacing:-0.5px;
}
.tj-sub {
    font-size:0.74rem; color:#3a3a3a; font-weight:600;
}
.tj-divider { width:1px; height:2rem; background:#222; flex-shrink:0; }
.tj-kpi { display:flex; flex-direction:column; align-items:flex-start; }
.tj-kpi-val { font-size:1.15rem; font-weight:900; line-height:1; }
.tj-kpi-lbl { font-size:0.6rem; font-weight:700; color:#3a3a3a;
              text-transform:uppercase; letter-spacing:0.8px; margin-top:0.15rem; }

/* ── back button ── */
.st-key-tj_back .stButton > button {
    background:transparent !important; border:1px solid #252525 !important;
    border-radius:8px !important; color:#404040 !important;
    font-size:0.72rem !important; font-weight:700 !important;
    padding:0.45rem 0.9rem !important; height:auto !important;
    min-height:auto !important; transition:all 0.12s !important;
}
.st-key-tj_back .stButton > button:hover {
    border-color:#404040 !important; color:#c0c0c0 !important;
}

/* ── add trade button ── */
.st-key-tj_add .stButton > button {
    background:rgba(38,166,154,0.08) !important;
    border:1px solid rgba(38,166,154,0.30) !important;
    border-radius:8px !important; color:#26A69A !important;
    font-size:0.72rem !important; font-weight:800 !important;
    padding:0.45rem 0.9rem !important; height:auto !important;
    min-height:auto !important; transition:all 0.12s !important;
    letter-spacing:0.3px !important;
}
.st-key-tj_add .stButton > button:hover {
    background:rgba(38,166,154,0.15) !important;
    border-color:rgba(38,166,154,0.60) !important;
    box-shadow:0 0 14px rgba(38,166,154,0.15) !important;
}

/* ── filter pills ── */
.st-key-tj_filters .stButton > button {
    background:#161616 !important; border:1px solid #272727 !important;
    border-radius:20px !important; color:#505050 !important;
    font-size:0.7rem !important; font-weight:700 !important;
    min-height:1.9rem !important; padding:0 1rem !important;
    transition:all .15s !important;
}
[class*="st-key-tjf_on"] .stButton > button {
    background:rgba(38,166,154,0.10) !important;
    border:1px solid rgba(38,166,154,0.35) !important;
    color:#26A69A !important; font-weight:800 !important;
}

/* ── delete buttons ── */
[class*="st-key-tj_del_"] .stButton > button {
    background:rgba(239,83,80,0.05) !important;
    border:1px solid rgba(239,83,80,0.18) !important;
    border-radius:8px !important;
    color:rgba(239,83,80,0.40) !important;
    font-size:0.8rem !important; font-weight:700 !important;
    padding:0 !important;
    min-height:100% !important; height:100% !important;
    transition:all 0.15s ease !important;
}
[class*="st-key-tj_del_"] .stButton > button:hover {
    background:rgba(239,83,80,0.12) !important;
    border-color:rgba(239,83,80,0.50) !important;
    color:#ef5350 !important;
    box-shadow:0 0 12px rgba(239,83,80,0.15) !important;
}

/* ── close/edit buttons ── */
[class*="st-key-tj_close_"] .stButton > button,
[class*="st-key-tj_note_"] .stButton > button {
    background:transparent !important; border:1px solid #252525 !important;
    border-radius:8px !important; color:#404040 !important;
    font-size:0.7rem !important; font-weight:700 !important;
    padding:0.35rem 0.75rem !important; height:auto !important;
    min-height:auto !important; transition:all 0.1s !important;
}
[class*="st-key-tj_close_"] .stButton > button:hover {
    border-color:#26A69A55 !important; color:#26A69A !important;
}

/* ── trade card ── */
.tj-card {
    background:#111; border:1px solid #1e1e1e;
    border-radius:14px; overflow:hidden;
    margin-bottom:0.7rem;
    transition:border-color .15s, box-shadow .15s;
}
.tj-card:hover { border-color:#2a2a2a; box-shadow:0 4px 24px rgba(0,0,0,0.4); }
.tj-card-open  { border-left:3px solid #26A69A !important; }
.tj-card-win   { border-left:3px solid #26A69A !important; }
.tj-card-loss  { border-left:3px solid #ef5350 !important; }
.tj-card-break { border-left:3px solid #FFC107 !important; }

.tj-ch {
    display:flex; align-items:center; gap:0.65rem;
    padding:0.8rem 1.1rem; border-bottom:1px solid #1a1a1a;
    flex-wrap:wrap;
}
.tj-sym {
    font-size:1rem; font-weight:900; color:#d0d0d0; letter-spacing:0.2px;
}
.tj-sname { font-size:0.65rem; color:#383838; font-weight:600; }
.tj-dir {
    font-size:0.6rem; font-weight:800; padding:0.15rem 0.55rem;
    border-radius:20px; text-transform:uppercase; letter-spacing:0.5px;
}
.tj-status {
    font-size:0.6rem; font-weight:800; padding:0.15rem 0.55rem;
    border-radius:6px; text-transform:uppercase; letter-spacing:0.5px; border:1px solid;
}
.tj-setup {
    font-size:0.65rem; color:#404040; font-weight:600;
}
.tj-date { font-size:0.58rem; color:#383838; font-weight:600; margin-left:auto; }

/* stats grid */
.tj-sg {
    display:grid; background:#0e0e0e;
}
.tj-si {
    padding:0.6rem 0.7rem; border-right:1px solid #181818;
    position:relative; text-align:center;
}
.tj-si:last-child { border-right:none; }
.tj-sl { font-size:0.5rem; font-weight:700; text-transform:uppercase;
         letter-spacing:0.7px; color:#383838; margin-bottom:0.2rem; }
.tj-sv { font-size:0.9rem; font-weight:900; line-height:1; }
.tj-si-bar { position:absolute; top:0; left:0; right:0; height:2px; }

/* notes */
.tj-notes {
    padding:0.6rem 1.1rem; border-top:1px solid #181818;
    font-size:0.72rem; color:#505050; line-height:1.6;
    font-style:italic;
}
.tj-notes-lbl {
    font-size:0.55rem; font-weight:700; color:#2e2e2e;
    text-transform:uppercase; letter-spacing:0.8px; margin-bottom:0.25rem;
}

/* price bar */
.tj-pbar-wrap {
    padding:0.55rem 1.1rem 0.6rem; border-top:1px solid #181818;
    display:flex; align-items:center; gap:0.75rem;
}
.tj-pbar-lbl { font-size:0.58rem; color:#303030; font-weight:700;
               text-transform:uppercase; letter-spacing:0.5px; white-space:nowrap; }
.tj-pbar-track {
    flex:1; height:6px; background:#1e1e1e; border-radius:3px; position:relative;
    overflow:visible;
}
.tj-pbar-fill {
    position:absolute; left:0; top:0; height:100%; border-radius:3px;
    transition:width 0.4s ease;
}
.tj-pbar-price {
    font-size:0.72rem; font-weight:800; white-space:nowrap;
}

/* conviction stars */
.tj-stars { letter-spacing:2px; }

/* ── form panel ── */
.tj-form-wrap {
    background:#111; border:1px solid #1e1e1e;
    border-radius:16px; padding:1.4rem 1.6rem 1.8rem;
    margin-bottom:1.4rem;
}
.tj-form-title {
    font-size:0.9rem; font-weight:900; color:#e0e0e0;
    margin-bottom:1.2rem; letter-spacing:-0.2px;
}

/* ── stat hero cards ── */
.tj-hero {
    display:grid; grid-template-columns:repeat(5,1fr);
    gap:0.65rem; margin-bottom:1.4rem;
}
.tj-hc {
    background:#141414; border:1px solid #1e1e1e;
    border-radius:12px; padding:0.85rem 1rem;
    position:relative; overflow:hidden;
}
.tj-hc-bar { position:absolute; top:0; left:0; right:0; height:2px; border-radius:12px 12px 0 0; }
.tj-hc-val { font-size:1.6rem; font-weight:900; line-height:1; letter-spacing:-1px; }
.tj-hc-lbl { font-size:0.58rem; color:#404040; font-weight:700;
             text-transform:uppercase; letter-spacing:0.7px; margin-top:0.3rem; }

/* ── empty state ── */
.tj-empty {
    background:#111; border:1px solid #1a1a1a; border-radius:14px;
    padding:5rem 2rem; text-align:center;
}
.tj-empty-icon { font-size:2rem; color:#252525; margin-bottom:1rem; }
.tj-empty-t { font-size:1.1rem; font-weight:800; color:#333; margin-bottom:0.5rem; }
.tj-empty-s { font-size:0.8rem; color:#2a2a2a; max-width:380px;
              margin:0 auto; line-height:1.8; }
</style>
"""


# ── Add-trade form ────────────────────────────────────────────────────────────

def _render_add_form():
    """Inline form to log a new trade."""
    st.markdown("<div class='tj-form-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='tj-form-title'>Log New Trade</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        symbol = st.text_input("Symbol", placeholder="e.g. 2222 or 2222.SR",
                               key="tj_sym_inp").strip().upper()
    with c2:
        direction = st.selectbox("Direction", ["LONG", "SHORT"], key="tj_dir_sel")
    with c3:
        capital = st.number_input("Capital (SAR)", min_value=0.0, value=10000.0,
                                  step=500.0, key="tj_cap_inp")
    with c4:
        setup_type = st.selectbox("Setup Type",
            ["", "Breakout", "Pullback", "Reversal", "Support Bounce",
             "Resistance Break", "Pattern", "Trend Follow", "Other"],
            key="tj_setup_sel")

    c5, c6, c7, c8, c9 = st.columns(5)
    with c5:
        entry_price = st.number_input("Entry Price", min_value=0.0, value=0.0,
                                      step=0.5, format="%.2f", key="tj_ep_inp")
    with c6:
        stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.0,
                                    step=0.5, format="%.2f", key="tj_sl_inp")
    with c7:
        target1 = st.number_input("Target 1", min_value=0.0, value=0.0,
                                  step=0.5, format="%.2f", key="tj_t1_inp")
    with c8:
        target2 = st.number_input("Target 2", min_value=0.0, value=0.0,
                                  step=0.5, format="%.2f", key="tj_t2_inp")
    with c9:
        target3 = st.number_input("Target 3", min_value=0.0, value=0.0,
                                  step=0.5, format="%.2f", key="tj_t3_inp")

    c10, c11 = st.columns([4, 1])
    with c10:
        notes_before = st.text_area("Pre-trade notes — why are you taking this trade?",
                                    placeholder="Setup reason, market context, what do you expect…",
                                    key="tj_notes_inp", height=80)
    with c11:
        conviction = st.slider("Conviction", 1, 5, 3, key="tj_conv_sl",
                               help="1 = low, 5 = very high")
        emotion = st.selectbox("Emotional state",
            ["Neutral", "Confident", "Anxious", "FOMO", "Excited", "Uncertain"],
            key="tj_emo_sel")

    ca, cb = st.columns([1, 5])
    with ca:
        save = st.button("Log Trade", key="tj_save_btn", use_container_width=True)
    with cb:
        cancel = st.button("Cancel", key="tj_cancel_btn", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if cancel:
        st.session_state.tj_show_form = False
        st.rerun()

    if save:
        errs = []
        if not symbol:
            errs.append("Symbol is required.")
        if entry_price <= 0:
            errs.append("Entry price must be > 0.")
        if stop_loss <= 0:
            errs.append("Stop loss must be > 0.")
        if not errs:
            if not symbol.endswith('.SR') and symbol.isdigit():
                symbol = symbol + '.SR'
            # try to auto-fetch live price if entry_price looks like 0 default
            stock_name = ''
            try:
                import yfinance as yf
                _t = yf.Ticker(symbol)
                _i = _t.info
                stock_name = _i.get('longName', _i.get('shortName', '')) or ''
            except Exception:
                pass

            # compute position size (shares)
            risk_per_share = abs(entry_price - stop_loss)
            shares = round(capital / entry_price, 2) if entry_price > 0 else 0

            trade = {
                'id':           str(uuid.uuid4())[:16],
                'symbol':       symbol,
                'stock_name':   stock_name,
                'direction':    direction,
                'entry_price':  entry_price,
                'stop_loss':    stop_loss,
                'target1':      target1 if target1 > 0 else None,
                'target2':      target2 if target2 > 0 else None,
                'target3':      target3 if target3 > 0 else None,
                'capital':      capital,
                'shares':       shares,
                'entry_date':   str(date.today()),
                'status':       'OPEN',
                'setup_type':   setup_type,
                'conviction':   conviction,
                'notes_before': notes_before,
                'notes_after':  '',
                'grade':        '',
                'emotion':      emotion,
                'created_at':   datetime.now().isoformat(),
            }
            upsert_trade(_user(), trade)
            st.session_state.tj_show_form = False
            if 'tj_trades' in st.session_state:
                del st.session_state['tj_trades']
            st.rerun()
        else:
            for e in errs:
                st.error(e)


# ── Trade card ────────────────────────────────────────────────────────────────

def _render_trade_card(trade: dict, idx: int):
    sym      = trade.get('symbol', '').replace('.SR', '')
    sname    = trade.get('stock_name', '')
    status   = trade.get('status', 'OPEN')
    direction = trade.get('direction', 'LONG')
    ep       = float(trade.get('entry_price', 0))
    sl       = float(trade.get('stop_loss', 0))
    t1       = trade.get('target1')
    t2       = trade.get('target2')
    t3       = trade.get('target3')
    cap      = float(trade.get('capital', 0))
    shares   = trade.get('shares')
    pnl_pct  = trade.get('pnl_pct') or 0
    pnl_amt  = trade.get('pnl_amount') or 0
    r_mult   = trade.get('r_multiple') or 0
    days     = trade.get('days_held')
    setup    = trade.get('setup_type', '')
    conv     = int(trade.get('conviction') or 3)
    emotion  = trade.get('emotion', '')
    notes_b  = trade.get('notes_before', '')
    notes_a  = trade.get('notes_after', '')
    grade    = trade.get('grade', '')
    edate    = trade.get('entry_date', '')
    xdate    = trade.get('exit_date', '')
    xprice   = trade.get('exit_price')
    live     = trade.get('current_price')  # runtime only
    hit_stop = trade.get('hit_stop', 0)
    hit_tgt  = trade.get('hit_target', 0)

    # card class + accent
    if status == 'OPEN':
        card_cls = 'tj-card tj-card-open'
        accent   = '#26A69A'
    elif pnl_pct > 0:
        card_cls = 'tj-card tj-card-win'
        accent   = '#26A69A'
    elif pnl_pct < 0:
        card_cls = 'tj-card tj-card-loss'
        accent   = '#ef5350'
    else:
        card_cls = 'tj-card tj-card-break'
        accent   = '#FFC107'

    pnl_c = '#26A69A' if pnl_pct >= 0 else '#ef5350'
    r_c   = '#26A69A' if r_mult >= 1 else ('#FFC107' if r_mult >= 0 else '#ef5350')

    dir_bg = 'rgba(38,166,154,0.15)' if direction == 'LONG' else 'rgba(239,83,80,0.15)'
    dir_c  = '#26A69A' if direction == 'LONG' else '#ef5350'

    status_c = '#26A69A' if status == 'OPEN' else ('#26A69A' if pnl_pct > 0 else '#ef5350')
    status_lbl = status
    if status == 'CLOSED':
        status_lbl = 'WIN' if pnl_pct > 0 else ('LOSS' if pnl_pct < 0 else 'BREAKEVEN')

    stars = '★' * conv + '☆' * (5 - conv)
    date_str = f"{edate}" + (f" → {xdate}" if xdate else f" · {days}d" if days is not None else '')

    # price progress bar (OPEN trades)
    pbar_html = ''
    if status == 'OPEN' and live and ep and sl:
        best_t = t3 or t2 or t1
        if best_t:
            total_range = abs(best_t - sl)
            current_move = (live - sl) if direction == 'LONG' else (sl - live)
            progress = max(0, min(1, current_move / total_range)) if total_range else 0
            bar_c = '#26A69A' if current_move >= 0 else '#ef5350'
            pbar_html = (
                f"<div class='tj-pbar-wrap'>"
                f"<span class='tj-pbar-lbl'>SL {sl:.2f}</span>"
                f"<div class='tj-pbar-track'>"
                f"<div class='tj-pbar-fill' style='width:{progress*100:.1f}%;background:{bar_c};'></div>"
                f"</div>"
                f"<span class='tj-pbar-price' style='color:{bar_c};'>▶ {live:.2f}</span>"
                f"<span class='tj-pbar-lbl'>T {best_t:.2f}</span>"
                f"</div>"
            )

    # targets display
    tgts = []
    for lbl, tv in [('T1', t1), ('T2', t2), ('T3', t3)]:
        if tv:
            tgts.append(f"<span style='font-size:0.65rem;color:#404040;font-weight:700;'>{lbl} "
                        f"<span style='color:#606060;'>{tv:.2f}</span></span>")
    tgts_html = '&nbsp;·&nbsp;'.join(tgts) if tgts else ''

    # R:R display
    if ep and sl and t1:
        risk  = abs(ep - sl)
        rw    = abs(t1 - ep)
        rr    = rw / risk if risk else 0
        rr_html = f"<span style='font-size:0.65rem;color:#404040;font-weight:700;'>R:R <span style='color:#606060;'>{rr:.1f}</span></span>"
    else:
        rr_html = ''

    # 7-col stats grid
    cols_def = 'repeat(7,1fr)' if status != 'OPEN' else 'repeat(6,1fr)'

    grid_cells = (
        f"<div class='tj-si'>"
        f"<div class='tj-si-bar' style='background:{accent};'></div>"
        f"<div class='tj-sl'>Entry</div>"
        f"<div class='tj-sv' style='color:#c0c0c0;'>{ep:.2f}</div></div>"
        f"<div class='tj-si'>"
        f"<div class='tj-si-bar' style='background:#ef5350;'></div>"
        f"<div class='tj-sl'>Stop</div>"
        f"<div class='tj-sv' style='color:#ef5350;'>{sl:.2f}</div></div>"
    )
    if t1:
        _t1_lbl = 'Exit' if xprice and status == 'CLOSED' else 'Target'
        _t1_val = f"{xprice:.2f}" if xprice and status == 'CLOSED' else f"{t1:.2f}"
        grid_cells += (
            f"<div class='tj-si'>"
            f"<div class='tj-si-bar' style='background:#26A69A55;'></div>"
            f"<div class='tj-sl'>{_t1_lbl}</div>"
            f"<div class='tj-sv' style='color:#888;'>{_t1_val}</div></div>"
        )
    grid_cells += (
        f"<div class='tj-si'>"
        f"<div class='tj-si-bar' style='background:{pnl_c};'></div>"
        f"<div class='tj-sl'>P&amp;L %</div>"
        f"<div class='tj-sv' style='color:{pnl_c};'>{pnl_pct:+.2f}%</div></div>"
        f"<div class='tj-si'>"
        f"<div class='tj-si-bar' style='background:{pnl_c};'></div>"
        f"<div class='tj-sl'>P&amp;L SAR</div>"
        f"<div class='tj-sv' style='color:{pnl_c};'>{pnl_amt:+.0f}</div></div>"
        f"<div class='tj-si'>"
        f"<div class='tj-si-bar' style='background:{r_c};'></div>"
        f"<div class='tj-sl'>R Multiple</div>"
        f"<div class='tj-sv' style='color:{r_c};'>{r_mult:+.1f}R</div></div>"
    )
    if shares:
        grid_cells += (
            f"<div class='tj-si'>"
            f"<div class='tj-si-bar' style='background:#333;'></div>"
            f"<div class='tj-sl'>Shares</div>"
            f"<div class='tj-sv' style='color:#666;'>{shares:.0f}</div></div>"
        )

    notes_html = ''
    if notes_b:
        notes_html += (
            f"<div class='tj-notes'>"
            f"<div class='tj-notes-lbl'>Pre-trade</div>{notes_b}</div>"
        )
    if notes_a:
        notes_html += (
            f"<div class='tj-notes'>"
            f"<div class='tj-notes-lbl'>Post-trade</div>{notes_a}</div>"
        )

    emotion_badge = ''
    if emotion:
        emotion_badge = (
            f"<span style='font-size:0.6rem;color:#404040;border:1px solid #252525;"
            f"border-radius:20px;padding:0.12rem 0.45rem;font-weight:700;'>{emotion}</span>"
        )
    grade_badge = ''
    if grade:
        gc = {'A': '#26A69A', 'B': '#4A9EFF', 'C': '#FFC107', 'D': '#FF6B6B', 'F': '#ef5350'}.get(grade, '#666')
        grade_badge = (
            f"<span style='font-size:0.65rem;font-weight:900;color:{gc};"
            f"border:1px solid {gc}55;border-radius:6px;"
            f"padding:0.12rem 0.45rem;'>Grade {grade}</span>"
        )

    html = (
        f"<div class='{card_cls}'>"
        f"<div class='tj-ch'>"
        f"<span class='tj-sym'>{sym}</span>"
        + (f"<span class='tj-sname'>{sname}</span>" if sname else '')
        + f"<span class='tj-dir' style='background:{dir_bg};color:{dir_c};'>{direction}</span>"
        f"<span class='tj-status' style='color:{status_c};border-color:{status_c}55;'>{status_lbl}</span>"
        + (f"<span class='tj-setup'>{setup}</span>" if setup else '')
        + f"<span class='tj-stars' style='font-size:0.7rem;color:#FFC10755;'>{stars}</span>"
        + emotion_badge
        + grade_badge
        + (f"<span style='font-size:0.65rem;color:#444;'>{tgts_html}</span>" if tgts_html else '')
        + (f"&nbsp;&nbsp;{rr_html}" if rr_html else '')
        + f"<span class='tj-date'>{date_str}</span>"
        f"</div>"
        f"<div class='tj-sg' style='grid-template-columns:{cols_def};'>{grid_cells}</div>"
        + pbar_html
        + notes_html
        + f"</div>"
    )

    row_cols = st.columns([1, 0.06])
    with row_cols[0]:
        st.markdown(html, unsafe_allow_html=True)
    with row_cols[1]:
        with st.container(key=f"tj_del_{idx}"):
            if st.button("✕", key=f"tj_rm_{idx}", use_container_width=True):
                delete_trade(_user(), trade['id'])
                if 'tj_trades' in st.session_state:
                    del st.session_state['tj_trades']
                st.rerun()

    # ── close / add notes expander (OPEN trades only) ─────────────────────────
    if status == 'OPEN':
        with st.expander("Close trade / Add post-trade notes", expanded=False):
            nc1, nc2, nc3, nc4 = st.columns([1.5, 1.5, 1, 2])
            with nc1:
                exit_p = st.number_input("Exit Price", min_value=0.0, value=float(live or ep),
                                         step=0.5, format="%.2f", key=f"tj_xp_{idx}")
            with nc2:
                exit_d = st.date_input("Exit Date", value=date.today(), key=f"tj_xd_{idx}")
            with nc3:
                new_grade = st.selectbox("Grade", ["", "A", "B", "C", "D", "F"],
                                         key=f"tj_gr_{idx}")
            with nc4:
                new_notes_a = st.text_area("Post-trade notes — what happened? What did you learn?",
                                           value=notes_a,
                                           placeholder="Was your thesis correct? What would you do differently?",
                                           key=f"tj_na_{idx}", height=80)

            if st.button("Save & Close Trade", key=f"tj_close_{idx}", use_container_width=True):
                updated = dict(trade)
                ep_v = float(trade.get('entry_price', 0))
                sl_v = float(trade.get('stop_loss', 0))
                risk = abs(ep_v - sl_v)
                if direction == 'LONG':
                    final_pnl = (exit_p - ep_v) / ep_v * 100 if ep_v else 0
                else:
                    final_pnl = (ep_v - exit_p) / ep_v * 100 if ep_v else 0
                updated.update({
                    'status':      'CLOSED',
                    'exit_price':  exit_p,
                    'exit_date':   str(exit_d),
                    'pnl_pct':     round(final_pnl, 2),
                    'pnl_amount':  round(cap * final_pnl / 100, 2),
                    'r_multiple':  round(final_pnl / (risk / ep_v * 100), 2) if ep_v and risk else 0,
                    'days_held':   (exit_d - datetime.strptime(edate, '%Y-%m-%d').date()).days,
                    'notes_after': new_notes_a,
                    'grade':       new_grade,
                })
                upsert_trade(_user(), updated)
                if 'tj_trades' in st.session_state:
                    del st.session_state['tj_trades']
                st.rerun()


# ── Main page ─────────────────────────────────────────────────────────────────

def render_trade_journal_page():
    """Full-page trade journal. Call from app.py routing."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # load + auto-refresh trades (cache in session for this run)
    if 'tj_trades' not in st.session_state:
        st.session_state.tj_trades = _load_and_refresh()
    trades = st.session_state.tj_trades

    stats = _compute_stats(trades)

    # ── top bar ───────────────────────────────────────────────────────────────
    pnl_c = '#26A69A' if stats['total_pnl'] >= 0 else '#ef5350'
    wr_c  = '#26A69A' if stats['win_rate'] >= 55 else ('#FFC107' if stats['win_rate'] >= 45 else '#ef5350')
    streak_c = '#26A69A' if stats['streak'] > 0 else ('#ef5350' if stats['streak'] < 0 else '#666')
    streak_lbl = f"+{stats['streak']}" if stats['streak'] > 0 else str(stats['streak'])

    _tl, _tb, _ta = st.columns([0.11, 0.11, 1])
    with _tl:
        with st.container(key="tj_back"):
            if st.button("← Back", key="tj_back_btn", use_container_width=True):
                st.session_state.show_trade_journal = False
                if 'tj_trades' in st.session_state:
                    del st.session_state['tj_trades']
                st.rerun()
    with _tb:
        with st.container(key="tj_add"):
            _add_lbl = "✕ Cancel" if st.session_state.get('tj_show_form', False) else "+ Log Trade"
            if st.button(_add_lbl, key="tj_add_btn", use_container_width=True):
                st.session_state.tj_show_form = not st.session_state.get('tj_show_form', False)
                st.rerun()
    with _ta:
        st.markdown(
            "<div class='tj-topbar' style='margin-bottom:0;padding-top:0.1rem;'>"
            "<div class='tj-divider'></div>"
            "<div><div class='tj-title'>Trade Journal</div>"
            "<div class='tj-sub'>auto-tracked · learn from every move</div></div>"
            "<div class='tj-divider'></div>"
            f"<div class='tj-kpi'><div class='tj-kpi-val' style='color:#707070;'>{stats['total']}</div>"
            f"<div class='tj-kpi-lbl'>Total</div></div>"
            "<div class='tj-divider'></div>"
            f"<div class='tj-kpi'><div class='tj-kpi-val' style='color:#26A69A;'>{stats['open']}</div>"
            f"<div class='tj-kpi-lbl'>Open</div></div>"
            "<div class='tj-divider'></div>"
            f"<div class='tj-kpi'><div class='tj-kpi-val' style='color:{wr_c};'>{stats['win_rate']:.0f}%</div>"
            f"<div class='tj-kpi-lbl'>Win Rate</div></div>"
            "<div class='tj-divider'></div>"
            f"<div class='tj-kpi'><div class='tj-kpi-val' style='color:{pnl_c};'>{stats['total_pnl']:+.0f}</div>"
            f"<div class='tj-kpi-lbl'>Total P&L (SAR)</div></div>"
            "<div class='tj-divider'></div>"
            f"<div class='tj-kpi'><div class='tj-kpi-val' style='color:{streak_c};'>{streak_lbl}</div>"
            f"<div class='tj-kpi-lbl'>Streak</div></div>"
            "</div>",
            unsafe_allow_html=True)

    if st.session_state.get('tj_show_form', False):
        _render_add_form()

    # ── hero stat cards ───────────────────────────────────────────────────────
    if stats['closed'] > 0:
        avg_r_c   = '#26A69A' if stats['avg_r'] >= 1 else ('#FFC107' if stats['avg_r'] >= 0 else '#ef5350')
        aw_c      = '#26A69A'
        al_c      = '#ef5350'
        st.markdown(
            f"<div class='tj-hero'>"
            f"<div class='tj-hc'><div class='tj-hc-bar' style='background:#26A69A;'></div>"
            f"<div class='tj-hc-val' style='color:#26A69A;'>{stats['win_rate']:.0f}%</div>"
            f"<div class='tj-hc-lbl'>Win Rate</div></div>"
            f"<div class='tj-hc'><div class='tj-hc-bar' style='background:{avg_r_c};'></div>"
            f"<div class='tj-hc-val' style='color:{avg_r_c};'>{stats['avg_r']:+.1f}R</div>"
            f"<div class='tj-hc-lbl'>Avg R Multiple</div></div>"
            f"<div class='tj-hc'><div class='tj-hc-bar' style='background:#26A69A;'></div>"
            f"<div class='tj-hc-val' style='color:#26A69A;'>+{stats['avg_win']:.1f}%</div>"
            f"<div class='tj-hc-lbl'>Avg Win</div></div>"
            f"<div class='tj-hc'><div class='tj-hc-bar' style='background:#ef5350;'></div>"
            f"<div class='tj-hc-val' style='color:#ef5350;'>{stats['avg_loss']:.1f}%</div>"
            f"<div class='tj-hc-lbl'>Avg Loss</div></div>"
            f"<div class='tj-hc'><div class='tj-hc-bar' style='background:{pnl_c};'></div>"
            f"<div class='tj-hc-val' style='color:{pnl_c};'>{stats['total_pnl']:+.0f}</div>"
            f"<div class='tj-hc-lbl'>Total P&L (SAR)</div></div>"
            f"</div>",
            unsafe_allow_html=True)

    # ── filter tabs ───────────────────────────────────────────────────────────
    if 'tj_filter' not in st.session_state:
        st.session_state.tj_filter = 'all'
    _cur = st.session_state.tj_filter
    _fopts = [
        ('all',    f'All  ({stats["total"]})'),
        ('open',   f'Open  ({stats["open"]})'),
        ('closed', f'Closed  ({stats["closed"]})'),
        ('wins',   f'Wins  ({stats["wins"]})'),
        ('losses', f'Losses  ({stats["losses"]})'),
    ]
    with st.container(key="tj_filters"):
        _fc = st.columns(len(_fopts))
        for _i, (_k, _l) in enumerate(_fopts):
            _ak = 'tjf_on' if _cur == _k else 'tjf_off'
            with st.container(key=f"{_ak}_{_i}"):
                with _fc[_i]:
                    if st.button(_l, key=f"tjf_{_k}", width="stretch"):
                        st.session_state.tj_filter = _k
                        st.rerun()

    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    # ── filter trades ─────────────────────────────────────────────────────────
    _flt = st.session_state.get('tj_filter', 'all')
    if _flt == 'open':
        view = [t for t in trades if t.get('status') == 'OPEN']
    elif _flt == 'closed':
        view = [t for t in trades if t.get('status') == 'CLOSED']
    elif _flt == 'wins':
        view = [t for t in trades if t.get('status') == 'CLOSED' and (t.get('pnl_pct') or 0) > 0]
    elif _flt == 'losses':
        view = [t for t in trades if t.get('status') == 'CLOSED' and (t.get('pnl_pct') or 0) <= 0]
    else:
        view = trades

    # ── empty state ───────────────────────────────────────────────────────────
    if not view:
        st.markdown(
            "<div class='tj-empty'>"
            "<div class='tj-empty-icon'>📒</div>"
            "<div class='tj-empty-t'>No trades yet</div>"
            "<div class='tj-empty-s'>Tap <b style='color:#26A69A'>+ Log Trade</b> to record "
            "your first trade. Every entry is auto-tracked — stop loss hits, target reached, "
            "P&L, R-multiple, days held.</div></div>",
            unsafe_allow_html=True)
        return

    # ── render cards ─────────────────────────────────────────────────────────
    for _i, _t in enumerate(view):
        _render_trade_card(_t, _i)
