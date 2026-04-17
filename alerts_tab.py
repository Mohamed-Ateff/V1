"""
Alerts Page -- Smart Trade Alerts with browser notifications.
Lives in the control panel next to Saved.  Auto-scans on open, sends
browser notifications for new high-conviction opportunities.
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta, date as _date

# ── design tokens ────────────────────────────────────────────────────────
BULL = "#10a37f"
BEAR = "#ef4444"
NEUT = "#fbbf24"
INFO = "#4A9EFF"
GOLD = "#FFD700"

# ── thresholds ───────────────────────────────────────────────────────────
# Tier 1 "Top Picks": multi-timeframe confirmed, strong R:R, high conviction
_TOP_CONV = 65
_TOP_RR   = 2.5
_TOP_MTF  = 2

# Tier 2 "Worth Watching": decent setups that pass basic quality
_MIN_CONV  = 40
_MIN_SCORE = 3
_MIN_RR    = 1.5

# ── CSS ──────────────────────────────────────────────────────────────────
_CSS = """
<style>
.alp-hero{
    background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    border:1px solid rgba(251,191,36,0.18);border-radius:16px;
    padding:1.8rem 2rem;margin-bottom:1.4rem;text-align:center;
    position:relative;overflow:hidden;
}
.alp-hero::before{
    content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
    background:radial-gradient(circle,rgba(251,191,36,0.05) 0%,transparent 70%);
    pointer-events:none;
}
.alp-hero h1{font-size:1.5rem;font-weight:800;color:#e2e8f0;margin:0 0 .3rem}
.alp-hero p{color:#94a3b8;font-size:.88rem;margin:0}
.alp-cnt{display:flex;justify-content:center;gap:2rem;margin-top:1.1rem;flex-wrap:wrap}
.alp-cnt-box{
    background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
    border-radius:12px;padding:.65rem 1.3rem;min-width:95px;
}
.alp-cnt-num{font-size:1.7rem;font-weight:800;line-height:1}
.alp-cnt-lbl{font-size:.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
.alp-tier{
    display:flex;align-items:center;gap:10px;
    margin:1.6rem 0 .7rem;padding-bottom:.45rem;
    border-bottom:1px solid rgba(255,255,255,.06);
}
.alp-tier-dot{width:10px;height:10px;border-radius:50%}
.alp-tier h3{margin:0;font-size:1rem;font-weight:700;color:#e2e8f0}
.alp-tier span{font-size:.75rem;color:#64748b}
.alp-card{
    background:#1b1b1b;border:1px solid #2a2a2a;border-radius:14px;
    padding:1.1rem 1.3rem;margin-bottom:.8rem;
    transition:border-color .2s,box-shadow .2s;
    position:relative;overflow:hidden;
}
.alp-card:hover{border-color:rgba(38,166,154,.3);box-shadow:0 4px 20px rgba(0,0,0,.3)}
.alp-glow{position:absolute;top:0;left:0;width:4px;height:100%;border-radius:14px 0 0 14px}
.alp-hdr{display:flex;align-items:center;justify-content:space-between;margin-bottom:.6rem}
.alp-sym{font-size:1.1rem;font-weight:800;letter-spacing:.5px}
.alp-name{font-size:.75rem;color:#94a3b8;margin-top:1px}
.alp-setup{font-size:.65rem;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:.3px;text-transform:uppercase}
.alp-dir{font-size:.8rem;font-weight:800;padding:4px 13px;border-radius:8px;letter-spacing:1px}
.alp-lvl{display:grid;grid-template-columns:repeat(4,1fr);gap:.45rem;background:rgba(255,255,255,.02);border-radius:10px;padding:.6rem;margin:.6rem 0}
.alp-lv{text-align:center}
.alp-lv-val{font-size:.9rem;font-weight:700;line-height:1.3}
.alp-lv-lbl{font-size:.62rem;color:#64748b;text-transform:uppercase;letter-spacing:.3px}
.alp-conv{display:flex;align-items:center;gap:8px;margin:.5rem 0 .25rem}
.alp-conv-lbl{font-size:.7rem;color:#64748b;min-width:65px}
.alp-conv-trk{flex:1;height:6px;background:#2a2a2a;border-radius:3px;overflow:hidden}
.alp-conv-fill{height:100%;border-radius:3px;transition:width .4s}
.alp-conv-val{font-size:.75rem;font-weight:700;min-width:34px;text-align:right}
.alp-chips{display:flex;gap:.5rem;flex-wrap:wrap;margin:.5rem 0}
.alp-chip{font-size:.67rem;padding:2px 9px;border-radius:16px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);color:#94a3b8}
.alp-chip-hot{background:rgba(16,163,127,.1);border-color:rgba(16,163,127,.25);color:#10a37f}
.alp-why{margin:.5rem 0 0;padding:.5rem .7rem;background:rgba(255,255,255,.02);border-radius:8px}
.alp-why-t{font-size:.7rem;color:#64748b;font-weight:600;margin-bottom:.25rem;text-transform:uppercase;letter-spacing:.5px}
.alp-why ul{margin:0;padding-left:1rem}
.alp-why li{font-size:.8rem;color:#cbd5e1;line-height:1.55}
.alp-mtf{display:flex;gap:5px;margin-top:3px}
.alp-mtf-b{font-size:.58rem;font-weight:700;padding:2px 6px;border-radius:6px;letter-spacing:.3px;background:rgba(16,163,127,.12);color:#10a37f;border:1px solid rgba(16,163,127,.25)}
.alp-empty{text-align:center;padding:2.5rem 1.5rem;background:#1b1b1b;border:1px dashed #2a2a2a;border-radius:14px;margin-top:1rem}
.alp-empty h3{color:#94a3b8;font-weight:600;margin:0 0 .4rem}
.alp-empty p{color:#64748b;font-size:.85rem;margin:0}
.alp-notif-bar{
    display:flex;align-items:center;justify-content:space-between;
    background:rgba(251,191,36,.06);border:1px solid rgba(251,191,36,.15);
    border-radius:10px;padding:.55rem 1rem;margin-bottom:1rem;
}
.alp-notif-bar span{font-size:.82rem;color:#fbbf24}
.alp-stats{display:flex;gap:1.5rem;flex-wrap:wrap;margin:.6rem 0 .3rem}
.alp-stat{font-size:.75rem;color:#64748b}
.alp-stat b{color:#94a3b8;font-weight:600}
</style>
"""

# ── notification JS ──────────────────────────────────────────────────────
_NOTIF_JS = """
<script>
(function() {
    var KEY = '__alp_notified__';
    var count = %d;
    var topCount = %d;
    var sig = count + '_' + topCount + '_' + '%s';
    if (count === 0) return;
    if (sessionStorage.getItem(KEY) === sig) return;
    sessionStorage.setItem(KEY, sig);
    function send() {
        var title = count + ' Trade Alert' + (count > 1 ? 's' : '') + ' Found';
        var body = topCount > 0
            ? topCount + ' top pick' + (topCount > 1 ? 's' : '') + ' with high conviction!'
            : count + ' worth-watching setup' + (count > 1 ? 's' : '');
        new Notification(title, {
            body: body,
            icon: 'https://em-content.zobj.net/source/apple/391/bell_1f514.png',
            tag: 'tadawul-alerts'
        });
    }
    if ('Notification' in window) {
        if (Notification.permission === 'granted') { send(); }
        else if (Notification.permission !== 'denied') {
            Notification.requestPermission().then(function(p) { if (p === 'granted') send(); });
        }
    }
})();
</script>
"""


# ── helpers ──────────────────────────────────────────────────────────────

def _conv_color(c):
    if c >= 70: return BULL
    if c >= 50: return NEUT
    return BEAR


def _rr_color(r):
    if r >= 3: return BULL
    if r >= 2: return NEUT
    return BEAR


def _mtf_badges(stock):
    parts = []
    if stock.get("score", 0) >= 3:
        parts.append('<span class="alp-mtf-b">Daily</span>')
    if stock.get("weekly_bullish"):
        parts.append('<span class="alp-mtf-b">Weekly</span>')
    if stock.get("monthly_bullish"):
        parts.append('<span class="alp-mtf-b">Monthly</span>')
    return "".join(parts)


def _strength_label(stock):
    """Return a human-readable strength summary."""
    factors = []
    s = stock.get("score", 0)
    c = stock.get("conviction", 0)
    rr = stock.get("rr_ratio", 0)
    mtf = stock.get("mtf_score", 0)

    if abs(s) >= 8:
        factors.append("Very strong signal")
    elif abs(s) >= 5:
        factors.append("Strong signal")
    else:
        factors.append("Moderate signal")

    if c >= 70:
        factors.append("high conviction")
    elif c >= 50:
        factors.append("decent conviction")

    if rr >= 3:
        factors.append("excellent R:R")
    elif rr >= 2:
        factors.append("good R:R")

    if mtf >= 2:
        factors.append("multi-TF confirmed")

    return " \u00b7 ".join(factors)


def _render_card(stock, side, is_top=False):
    sym   = stock["ticker"].replace(".SR", "")
    name  = stock.get("name", sym)
    price = stock["price"]
    conv  = stock.get("conviction", 50)
    setup = stock.get("setup_type", "Confluence")
    rr    = stock.get("rr_ratio", 0)
    entry = stock.get("entry", price)
    stop  = stock.get("stop_loss", price)
    t1    = stock.get("target1", price)
    t2    = stock.get("target2", price)
    score = stock.get("score", 0)
    rsi   = stock.get("rsi", 50)
    adx   = stock.get("adx", 0)
    vr    = stock.get("vol_ratio", 1)
    whys  = stock.get("why_reasons", [])
    mtf   = stock.get("mtf_score", 0)
    sector = stock.get("sector", "")

    is_buy = (side == "buy")
    ac = BULL if is_buy else BEAR
    dir_txt = "BUY" if is_buy else "SELL"
    dir_bg = "rgba(16,163,127,.12)" if is_buy else "rgba(239,68,68,.12)"

    stop_pct = abs(entry - stop) / entry * 100 if entry > 0 else 0
    t1_pct = abs(t1 - entry) / entry * 100 if entry > 0 else 0
    t2_pct = abs(t2 - entry) / entry * 100 if entry > 0 and t2 else 0

    # indicator chips
    chips = []
    if stock.get("above_ema200"):
        chips.append(("Above EMA 200", True))
    if stock.get("obv_rising"):
        chips.append(("OBV Rising", True))
    if vr >= 1.5:
        chips.append(("Vol " + f"{vr:.1f}" + "\u00d7", True))
    elif vr >= 1.2:
        chips.append(("Vol " + f"{vr:.1f}" + "\u00d7", False))
    if adx >= 25:
        chips.append((f"ADX {adx:.0f}", True))
    elif adx >= 20:
        chips.append((f"ADX {adx:.0f}", False))
    if rsi < 35:
        chips.append((f"RSI {rsi:.0f} Oversold", False))
    elif rsi > 65:
        chips.append((f"RSI {rsi:.0f} Strong", True))
    else:
        chips.append((f"RSI {rsi:.0f}", False))
    if mtf >= 2:
        chips.append((f"MTF {mtf}/3", True))
    rs = stock.get("rs_vs_tasi", 0)
    if rs and rs >= 5:
        chips.append((f"RS +{rs:.0f}%", True))

    chips_h = ""
    for label, hot in chips[:7]:
        cls = "alp-chip alp-chip-hot" if hot else "alp-chip"
        chips_h += '<span class="' + cls + '">' + label + '</span>'

    mtf_h = _mtf_badges(stock)
    cc = _conv_color(conv)
    strength = _strength_label(stock)

    # why bullets
    why_h = ""
    if whys:
        bullets = "".join("<li>" + w + "</li>" for w in whys[:5])
        why_h = (
            '<div class="alp-why">'
            '<div class="alp-why-t">Why this trade</div>'
            '<ul>' + bullets + '</ul>'
            '</div>'
        )

    mtf_div = ""
    if mtf_h:
        mtf_div = '<div class="alp-mtf">' + mtf_h + '</div>'

    # top pick glow
    border_extra = ""
    if is_top:
        border_extra = "border-color:rgba(255,215,0,.2);"

    # build levels - use target2 if available and different from target1
    t2_html = ""
    if t2 and abs(t2 - t1) > 0.01:
        t2_html = (
            '<div class="alp-lv"><div class="alp-lv-val" style="color:' + BULL + '">SAR ' + f"{t2:.2f}" + '</div>'
            '<div class="alp-lv-lbl">Target 2</div></div>'
        )
        grid_cols = "repeat(5,1fr)"
    else:
        grid_cols = "repeat(4,1fr)"

    html = (
        '<div class="alp-card" style="' + border_extra + '">'
        '<div class="alp-glow" style="background:linear-gradient(180deg,' + ac + ',' + ac + '44)"></div>'
        '<div class="alp-hdr">'
        '<div>'
        '<div class="alp-sym" style="color:' + ac + '">' + sym + '</div>'
        '<div class="alp-name">' + name
        + (' <span style="color:#475569;font-size:.65rem">' + sector + '</span>' if sector else '')
        + '</div>'
        + mtf_div +
        '</div>'
        '<div style="text-align:right;display:flex;align-items:center;gap:8px">'
        '<span class="alp-setup" style="background:' + dir_bg + ';color:' + ac + '">' + setup + '</span>'
        '<span class="alp-dir" style="background:' + dir_bg + ';color:' + ac + ';border:1px solid ' + ac + '44">' + dir_txt + '</span>'
        '</div>'
        '</div>'

        # strength line
        '<div style="font-size:.75rem;color:#64748b;margin-bottom:.4rem">' + strength + '</div>'

        # levels grid
        '<div class="alp-lvl" style="grid-template-columns:' + grid_cols + '">'
        '<div class="alp-lv"><div class="alp-lv-val" style="color:' + INFO + '">SAR ' + f"{entry:.2f}" + '</div><div class="alp-lv-lbl">Entry</div></div>'
        '<div class="alp-lv"><div class="alp-lv-val" style="color:' + BEAR + '">SAR ' + f"{stop:.2f}" + '</div><div class="alp-lv-lbl">Stop Loss</div></div>'
        '<div class="alp-lv"><div class="alp-lv-val" style="color:' + BULL + '">SAR ' + f"{t1:.2f}" + '</div><div class="alp-lv-lbl">Target 1</div></div>'
        + t2_html +
        '<div class="alp-lv"><div class="alp-lv-val" style="color:' + _rr_color(rr) + '">' + f"{rr:.1f}" + '\u00d7</div><div class="alp-lv-lbl">Risk : Reward</div></div>'
        '</div>'

        # conviction bar
        '<div class="alp-conv">'
        '<span class="alp-conv-lbl">Conviction</span>'
        '<div class="alp-conv-trk"><div class="alp-conv-fill" style="width:' + str(conv) + '%;background:' + cc + '"></div></div>'
        '<span class="alp-conv-val" style="color:' + cc + '">' + str(conv) + '%</span>'
        '</div>'

        # chips
        '<div class="alp-chips">' + chips_h + '</div>'

        # risk / potential / price line
        '<div style="display:flex;gap:1rem;margin-top:.25rem">'
        '<span style="font-size:.75rem;color:#64748b">Risk: <span style="color:' + BEAR + '">-' + f"{stop_pct:.1f}" + '%</span></span>'
        '<span style="font-size:.75rem;color:#64748b">Potential: <span style="color:' + BULL + '">+' + f"{t1_pct:.1f}" + '%</span></span>'
        '<span style="font-size:.75rem;color:#64748b">Score: <span style="color:#e2e8f0">' + str(abs(score)) + '</span></span>'
        '<span style="font-size:.75rem;color:#64748b">Price: <span style="color:#e2e8f0">SAR ' + f"{price:.2f}" + '</span></span>'
        '</div>'

        + why_h +
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _tier_header(title, color, count, sub=""):
    sub_h = '<span style="margin-left:auto;font-size:.72rem;color:#64748b">' + sub + '</span>' if sub else ""
    st.markdown(
        '<div class="alp-tier">'
        '<div class="alp-tier-dot" style="background:' + color + '"></div>'
        '<h3>' + title + '</h3>'
        '<span>(' + str(count) + ')</span>'
        + sub_h +
        '</div>',
        unsafe_allow_html=True,
    )


# ── main page ────────────────────────────────────────────────────────────

def render_alerts_page():
    """Full-page Alerts view with browser notifications."""

    from market_data import get_all_tadawul_tickers, run_market_analysis

    st.markdown(_CSS, unsafe_allow_html=True)

    # ── header row ────────────────────────────────────────────────────────
    _hc = st.columns([1.2, 6, 2.5])
    with _hc[0]:
        with st.container(key="alp_back"):
            st.markdown('<style>.st-key-alp_back .stButton>button{background:rgba(255,255,255,.04)!important;border:1px solid #2a2a2a!important;border-radius:10px!important;color:#94a3b8!important;font-size:.82rem!important;font-weight:600!important}</style>', unsafe_allow_html=True)
            if st.button("\u2190  Back", key="alp_back_btn", width="stretch"):
                st.session_state.show_alerts_page = False
                st.rerun()
    with _hc[1]:
        st.markdown(
            "<div style='display:flex;align-items:baseline;gap:.6rem;padding-top:.15rem;'>"
            "<span style='font-size:1.15rem;font-weight:900;color:#e0e0e0;"
            "letter-spacing:-.3px;'>\U0001f514 Smart Alerts</span>"
            "<span style='font-size:.78rem;color:#64748b;font-weight:500;'>High-conviction trade opportunities</span>"
            "</div>",
            unsafe_allow_html=True,
        )
    with _hc[2]:
        if st.button("\U0001f504 Rescan Now", key="alp_rescan", type="secondary", width="stretch"):
            st.session_state.pop("_alerts_results", None)
            st.session_state.pop("_alerts_ts", None)
            st.rerun()

    # ── auto-scan on open ─────────────────────────────────────────────────
    all_tickers = get_all_tadawul_tickers()
    tickers_list = list(all_tickers.keys())

    need_scan = False
    if "_alerts_results" not in st.session_state:
        need_scan = True
    else:
        ts = st.session_state.get("_alerts_ts", datetime.min)
        if (datetime.now() - ts).total_seconds() > 600:
            need_scan = True

    if need_scan:
        with st.spinner("Scanning " + str(len(tickers_list)) + " Tadawul stocks for trade setups..."):
            end_dt = _date.today()
            start_dt = end_dt - timedelta(days=200)
            res = run_market_analysis(
                tuple(tickers_list),
                min_score=1,
                start=start_dt,
                end=end_dt,
            )
            st.session_state["_alerts_results"] = res
            st.session_state["_alerts_ts"] = datetime.now()

    res = st.session_state.get("_alerts_results")
    if not res:
        st.warning("No scan results. Click **Rescan Now**.")
        return

    buys = res.get("buy", [])
    sells = res.get("sell", [])
    holds = res.get("hold", [])
    total_analyzed = len(buys) + len(sells) + len(holds)

    # ── classify into tiers ───────────────────────────────────────────────
    # Tier 1: Top Picks - the cream of the crop
    def _is_top(s):
        return (
            s.get("conviction", 0) >= _TOP_CONV
            and s.get("rr_ratio", 0) >= _TOP_RR
            and s.get("mtf_score", 0) >= _TOP_MTF
        )

    # Tier 2: Worth Watching - passes minimum quality bar
    def _is_watchable(s):
        return (
            s.get("conviction", 0) >= _MIN_CONV
            and abs(s.get("score", 0)) >= _MIN_SCORE
            and s.get("rr_ratio", 0) >= _MIN_RR
        )

    top_buys  = sorted([s for s in buys if _is_top(s)],
                        key=lambda x: x.get("priority_score", 0), reverse=True)
    top_sells = sorted([s for s in sells if _is_top(s)],
                        key=lambda x: abs(x.get("priority_score", 0)), reverse=True)

    watch_buys  = sorted([s for s in buys if _is_watchable(s) and not _is_top(s)],
                          key=lambda x: x.get("priority_score", 0), reverse=True)
    watch_sells = sorted([s for s in sells if _is_watchable(s) and not _is_top(s)],
                          key=lambda x: abs(x.get("priority_score", 0)), reverse=True)

    # If nothing passes quality, show ALL buy/sell signals as "signals detected"
    # so the page never looks completely empty when there IS data
    show_all_fallback = False
    n_top = len(top_buys) + len(top_sells)
    n_watch = len(watch_buys) + len(watch_sells)
    n_quality = n_top + n_watch

    remaining_buys = []
    remaining_sells = []
    if n_quality == 0 and (buys or sells):
        show_all_fallback = True
        remaining_buys = sorted(buys, key=lambda x: x.get("priority_score", 0), reverse=True)
        remaining_sells = sorted(sells, key=lambda x: abs(x.get("priority_score", 0)), reverse=True)

    n_all_signals = len(buys) + len(sells)

    # ── browser notification ──────────────────────────────────────────────
    ts_sig = st.session_state.get("_alerts_ts", datetime.now()).strftime("%H%M")
    n_notify = n_quality if n_quality > 0 else 0
    components.html(_NOTIF_JS % (n_notify, n_top, ts_sig), height=0)

    # ── notification bar ──────────────────────────────────────────────────
    if n_quality > 0:
        st.markdown(
            '<div class="alp-notif-bar">'
            '<span>\U0001f514 ' + str(n_quality) + ' alert' + ('s' if n_quality != 1 else '') + ' found'
            + (' -- ' + str(n_top) + ' top pick' + ('s' if n_top != 1 else '') + '!' if n_top > 0 else '')
            + '</span>'
            '<span style="font-size:.72rem;color:#64748b">Auto-refreshes every 10 min</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── hero card ─────────────────────────────────────────────────────────
    if n_quality > 0:
        emoji = "\U0001f525" if n_top > 0 else "\U0001f4e1"
        msg = str(n_quality) + " Trade Opportunity" + ("s" if n_quality != 1 else "") + " Found"
        sub = "Only showing setups where multiple indicators agree and risk/reward is favorable."
    elif show_all_fallback:
        emoji = "\U0001f4e1"
        msg = str(n_all_signals) + " Signal" + ("s" if n_all_signals != 1 else "") + " Detected"
        sub = "No setups passed the highest quality filters, but these signals were detected in the scan."
    else:
        emoji = "\U0001f634"
        msg = "No Setups Right Now"
        sub = "The market has no actionable trades today. Better to wait than force a bad trade."

    ts_str = st.session_state.get("_alerts_ts", datetime.now()).strftime("%I:%M %p")

    hero_html = (
        '<div class="alp-hero">'
        '<h1>' + emoji + ' ' + msg + '</h1>'
        '<p>' + sub + '</p>'
        '<div class="alp-cnt">'
        '<div class="alp-cnt-box"><div class="alp-cnt-num" style="color:' + GOLD + '">' + str(n_top) + '</div><div class="alp-cnt-lbl">Top Picks</div></div>'
        '<div class="alp-cnt-box"><div class="alp-cnt-num" style="color:' + INFO + '">' + str(n_watch) + '</div><div class="alp-cnt-lbl">Worth Watching</div></div>'
        '<div class="alp-cnt-box"><div class="alp-cnt-num" style="color:' + BULL + '">' + str(n_all_signals) + '</div><div class="alp-cnt-lbl">Total Signals</div></div>'
        '<div class="alp-cnt-box"><div class="alp-cnt-num" style="color:#94a3b8">' + str(total_analyzed) + '</div><div class="alp-cnt-lbl">Stocks Analyzed</div></div>'
        '</div>'
        '<p style="margin-top:1rem;font-size:.72rem;color:#475569">Last scan: ' + ts_str + ' \u00b7 ' + str(len(tickers_list)) + ' tickers</p>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # ── scan stats ────────────────────────────────────────────────────────
    if total_analyzed > 0:
        st.markdown(
            '<div class="alp-stats">'
            '<span class="alp-stat">Bullish: <b style="color:' + BULL + '">' + str(len(buys)) + '</b></span>'
            '<span class="alp-stat">Bearish: <b style="color:' + BEAR + '">' + str(len(sells)) + '</b></span>'
            '<span class="alp-stat">Neutral: <b>' + str(len(holds)) + '</b></span>'
            '<span class="alp-stat">Download success: <b>' + str(total_analyzed) + '/' + str(len(tickers_list)) + '</b></span>'
            '</div>',
            unsafe_allow_html=True,
        )
    elif total_analyzed == 0:
        st.error(
            "**0 stocks were analyzed** -- all downloads failed. "
            "This usually means a temporary network or API issue. "
            "Wait a minute and hit **Rescan Now**."
        )
        return

    # ── empty state ───────────────────────────────────────────────────────
    if n_quality == 0 and not show_all_fallback:
        st.markdown(
            '<div class="alp-empty">'
            '<h3>All clear -- no strong setups detected</h3>'
            '<p>Market is either choppy, uncertain, or fully priced in. '
            'Patience is a strategy. Check back later or hit Rescan after market hours.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Top Picks ─────────────────────────────────────────────────────────
    if n_top > 0:
        _tier_header(
            "\u2b50 Top Picks -- Highest Conviction",
            GOLD, n_top,
            "Multi-timeframe confirmed \u00b7 Strong R:R \u00b7 High conviction",
        )
        for s in top_buys:
            _render_card(s, "buy", is_top=True)
        for s in top_sells:
            _render_card(s, "sell", is_top=True)

    # ── Worth Watching ────────────────────────────────────────────────────
    if n_watch > 0:
        _tier_header(
            "\U0001f4e1 Worth Watching",
            INFO, n_watch,
            "Good setups -- monitor closely",
        )
        combined = [(s, "buy") for s in watch_buys] + [(s, "sell") for s in watch_sells]
        combined.sort(key=lambda x: x[0].get("priority_score", 0), reverse=True)
        for s, side in combined[:20]:
            _render_card(s, side)
        if len(combined) > 20:
            st.caption("+ " + str(len(combined) - 20) + " more setups not shown.")

    # ── Fallback: show all signals if nothing passed quality ──────────────
    if show_all_fallback:
        _tier_header(
            "\U0001f4ca All Detected Signals",
            "#94a3b8", n_all_signals,
            "Below quality threshold -- use as watchlist only",
        )
        all_sigs = [(s, "buy") for s in remaining_buys[:10]] + [(s, "sell") for s in remaining_sells[:10]]
        all_sigs.sort(key=lambda x: abs(x[0].get("score", 0)), reverse=True)
        for s, side in all_sigs[:15]:
            _render_card(s, side)

    # ── footer ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        "Alerts scan all Tadawul stocks through a multi-factor engine: "
        "technical indicators, price action, volume, multi-timeframe confirmation, "
        "and regime detection. Top Picks require conviction >=65%, R:R >=2.5x, "
        "and 2+ timeframe confirmation. This is an analysis tool -- not financial advice."
    )
