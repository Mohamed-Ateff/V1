"""
macro_data.py — Global Macro Data Engine for TadawulAI
=======================================================
Fetches and scores macro indicators that affect Saudi market independently
of technical analysis: oil prices, VIX fear gauge, USD strength, S&P 500,
Saudi Aramco, natural gas, emerging markets, and RSS news headlines.

All functions are cached to avoid redundant network calls.
"""

import streamlit as st
import yfinance as yf
import urllib.request
import xml.etree.ElementTree as ET

# Saudi budget breakeven oil price — below this the Saudi budget runs a deficit
_SAUDI_OIL_BREAKEVEN = 80.0   # USD/bbl (IMF estimate)
_SAUDI_OIL_COMFORT   = 90.0   # USD/bbl — comfortable surplus zone

# ── Macro instruments ─────────────────────────────────────────────────────────
# (ticker, display_label, unit, bullish_when_rising_for_saudi)
_MACRO_TICKERS = {
    'brent':   ('BZ=F',     'Brent Crude',   '$/bbl', True),
    'wti':     ('CL=F',     'WTI Crude',     '$/bbl', True),
    'gas':     ('NG=F',     'Natural Gas',   '$/MMBtu',True),
    'aramco':  ('2222.SR',  'Saudi Aramco',  'SAR',   True),
    'vix':     ('^VIX',     'VIX Fear',      '',      False),
    'usd':     ('DX-Y.NYB', 'USD Index',     '',      False),
    'gold':    ('GC=F',     'Gold',          '$/oz',  True),
    'sp500':   ('^GSPC',    'S&P 500',       '',      True),
    'em':      ('EEM',      'EM ETF',        '$',     True),
}

# ── Free RSS news feeds ───────────────────────────────────────────────────────
_NEWS_FEEDS = [
    ('Arab News',     'https://www.arabnews.com/economy/rss.xml'),
    ('Oil Price',     'https://oilprice.com/rss/main'),
    ('Saudi Gazette', 'https://saudigazette.com.sa/rss.xml'),
    ('Reuters Energy','https://feeds.reuters.com/reuters/businessNews'),
]


@st.cache_data(ttl=1800, show_spinner=False)
def get_macro_snapshot():
    """
    Fetch current price, 1-day change, 5-day change, and 30-day change for
    each macro instrument.  Returns a dict keyed by instrument name.
    Cached for 30 minutes.
    """
    result = {}
    tickers_str = ' '.join(t for t, *_ in _MACRO_TICKERS.values())
    try:
        raw = yf.download(tickers_str, period='45d', interval='1d',
                          progress=False, auto_adjust=True, group_by='ticker')
    except Exception:
        raw = None

    for key, (ticker, label, unit, bullish_up) in _MACRO_TICKERS.items():
        try:
            if raw is not None and ticker in raw.columns.get_level_values(0):
                close = raw[ticker]['Close'].dropna()
            else:
                data  = yf.download(ticker, period='45d', interval='1d',
                                    progress=False, auto_adjust=True)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                close = data['Close'].dropna()

            if len(close) < 2:
                continue

            price    = float(close.iloc[-1])
            prev_1d  = float(close.iloc[-2])
            prev_5d  = float(close.iloc[-min(6,  len(close))])
            prev_30d = float(close.iloc[-min(31, len(close))])
            chg_1d   = (price - prev_1d)  / prev_1d  * 100
            chg_5d   = (price - prev_5d)  / prev_5d  * 100
            chg_30d  = (price - prev_30d) / prev_30d * 100
            result[key] = {
                'label':      label,
                'unit':       unit,
                'price':      price,
                'chg_1d':     chg_1d,
                'chg_5d':     chg_5d,
                'chg_30d':    chg_30d,
                'bullish_up': bullish_up,
                'trend':      'up' if chg_5d > 0.5 else ('down' if chg_5d < -0.5 else 'flat'),
            }
        except Exception:
            pass

    return result


def compute_macro_health(snapshot: dict):
    """
    Comprehensive macro health score for Saudi market.
    Returns (score, label, color, bg, factors).

    Score range: -10 (severe risk-off) to +10 (strong risk-on).
    Factors: list of (emoji, short_title, explanation, impact_color) tuples.
    """
    score   = 0
    factors = []   # (emoji, title, detail, color)

    def _f(em, title, detail, color): factors.append((em, title, detail, color))

    # ── OIL — most important driver for Saudi (±5 pts total) ─────────────────
    oil = snapshot.get('brent') or snapshot.get('wti')
    if oil:
        p  = oil['price']
        c1 = oil['chg_1d']
        c5 = oil['chg_5d']
        c30= oil['chg_30d']

        # Price level context relative to Saudi breakeven
        deficit_gap = _SAUDI_OIL_BREAKEVEN - p
        if p < _SAUDI_OIL_BREAKEVEN - 15:
            score -= 2
            _f('🛢️', f'Brent ${p:.1f} — Critical Level',
               f'${abs(deficit_gap):.0f}/bbl BELOW Saudi budget breakeven (${_SAUDI_OIL_BREAKEVEN:.0f}). '
               f'Govt spending likely to be cut. High economic stress.', '#ef4444')
        elif p < _SAUDI_OIL_BREAKEVEN:
            score -= 1
            _f('🛢️', f'Brent ${p:.1f} — Below Breakeven',
               f'Saudi budget breakeven is ~${_SAUDI_OIL_BREAKEVEN:.0f}/bbl. '
               f'Currently ${abs(deficit_gap):.0f}/bbl short — fiscal pressure building.', '#f97316')
        elif p < _SAUDI_OIL_COMFORT:
            score += 1
            _f('🛢️', f'Brent ${p:.1f} — Near Breakeven',
               f'${p - _SAUDI_OIL_BREAKEVEN:.0f}/bbl above budget breakeven — manageable '
               f'but not comfortable. Vision 2030 projects need higher oil.', '#fbbf24')
        else:
            score += 2
            _f('🛢️', f'Brent ${p:.1f} — Comfortable Zone',
               f'${p - _SAUDI_OIL_BREAKEVEN:.0f}/bbl above breakeven — Saudi revenues healthy, '
               f'Vision 2030 investment flow supported.', '#10a37f')

        # Momentum: 5-day trend
        if c5 < -7:
            score -= 3
            _f('📉', f'Oil Crashing — {c5:.1f}% in 5 Days',
               f'Today: {("+" if c1>=0 else "")}{c1:.1f}%. '
               f'30-day: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'Rapid oil decline triggers Saudi stock selloffs — Aramco, banks, and petrochemicals hit hardest.', '#ef4444')
        elif c5 < -3:
            score -= 2
            _f('📉', f'Oil Falling Fast — {c5:.1f}% This Week',
               f'Today: {("+" if c1>=0 else "")}{c1:.1f}%. This pace, if sustained, '
               f'threatens Saudi budget assumptions. Expect pressure on TASI.', '#ef4444')
        elif c5 < -1:
            score -= 1
            _f('📉', f'Oil Weakening — {c5:.1f}% This Week',
               f'Gradual decline. 30d trend: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'Monitor — if OPEC doesn\'t respond, downtrend may accelerate.', '#f97316')
        elif c5 > 7:
            score += 3
            _f('📈', f'Oil Surging — +{c5:.1f}% This Week',
               f'Today: +{c1:.1f}%. 30-day: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'Strong Saudi revenue outlook — bullish for entire TASI, especially banks & Aramco.', '#10a37f')
        elif c5 > 3:
            score += 2
            _f('📈', f'Oil Rising — +{c5:.1f}% This Week',
               f'Positive momentum. 30d: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'Saudi stocks typically follow oil up with ~2-day lag.', '#10a37f')
        elif c5 > 1:
            score += 1
            _f('📈', f'Oil Edging Up — +{c5:.1f}% This Week',
               f'Mild positive. Today: {("+" if c1>=0 else "")}{c1:.1f}%. Stable macro backdrop.', '#4A9EFF')

    # ── NATURAL GAS (Saudi exports + global energy sentiment — ±1 pt) ────────
    gas = snapshot.get('gas')
    if gas:
        c5 = gas['chg_5d']
        p  = gas['price']
        if c5 > 10:
            score += 1
            _f('🔥', f'Natural Gas Surging +{c5:.1f}%',
               f'At ${p:.2f}/MMBtu. Global energy demand spike — supports energy sector broadly. '
               f'Saudi LNG projects (NEOM energy) benefit.', '#10a37f')
        elif c5 < -10:
            score -= 1
            _f('🔥', f'Natural Gas Collapsing {c5:.1f}%',
               f'At ${p:.2f}/MMBtu. Weak energy demand signal — may drag oil lower. '
               f'Watch for contagion to crude oil.', '#f97316')

    # ── VIX (global panic meter — ±3 pts) ────────────────────────────────────
    vix = snapshot.get('vix')
    if vix:
        v  = vix['price']
        c5 = vix['chg_5d']
        # Absolute level is more important than change for VIX
        if v > 45:
            score -= 3
            _f('😱', f'Extreme Panic — VIX {v:.0f}',
               f'VIX above 45 = market crisis level. Historical context: COVID peak was 85, '
               f'2008 GFC was 80. At this level, foreign investors flee ALL emerging markets including Saudi. '
               f'Do NOT buy into this environment.', '#ef4444')
        elif v > 35:
            score -= 3
            _f('😰', f'Market Panic — VIX {v:.0f}',
               f'VIX above 35 signals institutional fear. Foreign investors pulling out of EM. '
               f'Saudi stocks typically drop 5–15% in episodes like this. Reduce exposure now.', '#ef4444')
        elif v > 25:
            score -= 2
            _f('⚠️', f'High Fear — VIX {v:.0f}',
               f'Elevated anxiety. Foreign ownership of TASI was ~20% — they sell EM when VIX spikes. '
               f'Use 50% position sizes max. Avoid thin stocks.', '#ef4444')
        elif v > 18:
            score -= 1
            _f('⚠️', f'Elevated Tension — VIX {v:.0f}',
               f'Above normal anxiety ({("+" if c5>=0 else "")}{c5:.1f}% this week). '
               f'Markets nervous but not panicking. Trade normally but set stops.', '#fbbf24')
        elif v < 13:
            score += 2
            _f('😌', f'Extreme Calm — VIX {v:.0f}',
               f'VIX near multi-year lows. Risk appetite is very strong globally. '
               f'Great environment for momentum and breakout trades.', '#10a37f')
        elif v < 16:
            score += 2
            _f('😌', f'Low Fear — VIX {v:.0f}',
               f'Markets are calm. Foreign investors comfortable with EM exposure. '
               f'Good environment to run full position sizes on high-conviction setups.', '#10a37f')
        else:
            score += 1
            _f('😐', f'Normal Volatility — VIX {v:.0f}',
               f'Typical market environment. No unusual fear or greed signals.', '#4A9EFF')

    # ── USD INDEX (strong USD = oil priced higher in local currencies but
    #   also EM capital outflow — ±2 pts) ─────────────────────────────────────
    usd = snapshot.get('usd')
    if usd:
        c5  = usd['chg_5d']
        c30 = usd['chg_30d']
        p   = usd['price']
        if c5 > 2:
            score -= 2
            _f('💵', f'USD Surging +{c5:.1f}%',
               f'Dollar Index at {p:.1f}. Strong dollar = capital leaves EM including Saudi. '
               f'Also pressures oil: global buyers pay more, demand slows. Double headwind.', '#ef4444')
        elif c5 > 0.8:
            score -= 1
            _f('💵', f'USD Strengthening +{c5:.1f}%',
               f'Dollar at {p:.1f} (+{c5:.1f}% this week, {("+" if c30>=0 else "")}{c30:.1f}% in 30d). '
               f'Mild headwind for EM capital flows.', '#fbbf24')
        elif c5 < -2:
            score += 2
            _f('💵', f'USD Weakening {c5:.1f}%',
               f'Dollar at {p:.1f}. Weak USD = oil remains expensive globally (demand supported) '
               f'AND money flows back into EM. Double tailwind for Saudi stocks.', '#10a37f')
        elif c5 < -0.8:
            score += 1
            _f('💵', f'USD Softening {c5:.1f}%',
               f'Dollar at {p:.1f}. Mild tailwind for commodities and emerging markets.', '#4A9EFF')

    # ── S&P 500 (global risk-on/off — ±2 pts) ────────────────────────────────
    sp = snapshot.get('sp500')
    if sp:
        c1  = sp['chg_1d']
        c5  = sp['chg_5d']
        c30 = sp['chg_30d']
        p   = sp['price']
        if c5 < -5:
            score -= 2
            _f('📊', f'S&P 500 Selling Off — {c5:.1f}% This Week',
               f'Today: {("+" if c1>=0 else "")}{c1:.1f}%. 30d: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'US market in distress — contagion selling typically hits Saudi market 1–3 days later. '
               f'Be very cautious with new positions.', '#ef4444')
        elif c5 < -2:
            score -= 1
            _f('📊', f'S&P 500 Weak — {c5:.1f}% This Week',
               f'Global risk-off tone. 30d: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'International investors reducing EM allocation.', '#f97316')
        elif c5 > 5:
            score += 2
            _f('📊', f'S&P 500 Rallying — +{c5:.1f}% This Week',
               f'Today: +{c1:.1f}%. 30d: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'Strong global risk appetite — international money entering EM. '
               f'Positive for Saudi blue chips and growth stocks.', '#10a37f')
        elif c5 > 1.5:
            score += 1
            _f('📊', f'S&P 500 Positive — +{c5:.1f}% This Week',
               f'Healthy global sentiment. 30d: {("+" if c30>=0 else "")}{c30:.1f}%. '
               f'Good backdrop for Saudi market.', '#4A9EFF')

    # ── GOLD (flight-to-safety barometer — ±1 pt) ────────────────────────────
    gold = snapshot.get('gold')
    if gold:
        c5  = gold['chg_5d']
        p   = gold['price']
        c30 = gold['chg_30d']
        if c5 > 4:
            score -= 1
            _f('🥇', f'Gold Surging +{c5:.1f}%',
               f'At ${p:,.0f}/oz. Investors rushing to safety — geopolitical or economic shock feared. '
               f'30d: {("+" if c30>=0 else "")}{c30:.1f}%. Watch gold as early warning for broader selloff.', '#fbbf24')
        elif c5 > 2:
            _f('🥇', f'Gold Rising +{c5:.1f}%',
               f'At ${p:,.0f}/oz. Mild safety demand. Could signal upcoming market nervousness. '
               f'Cross-reference with VIX for confirmation.', '#fbbf24')
        elif c5 < -3:
            score += 1
            _f('🥇', f'Gold Retreating {c5:.1f}%',
               f'At ${p:,.0f}/oz. Investors selling safety assets = risk appetite returning. '
               f'Bullish signal for equities including Saudi market.', '#10a37f')

    # ── SAUDI ARAMCO (direct Saudi market proxy — ±1 pt) ─────────────────────
    aramco = snapshot.get('aramco')
    if aramco:
        c1 = aramco['chg_1d']
        c5 = aramco['chg_5d']
        p  = aramco['price']
        if c5 < -5:
            score -= 1
            _f('🏭', f'Aramco Selling Off — {c5:.1f}% This Week',
               f'At SAR {p:.2f}. Aramco is the backbone of TASI (30%+ weight). '
               f'Its weakness drags the entire index. Today: {("+" if c1>=0 else "")}{c1:.1f}%.', '#ef4444')
        elif c5 > 5:
            score += 1
            _f('🏭', f'Aramco Rising — +{c5:.1f}% This Week',
               f'At SAR {p:.2f}. Aramco lifting TASI — positive momentum for the whole market. '
               f'Today: {("+" if c1>=0 else "")}{c1:.1f}%.', '#10a37f')

    # ── EMERGING MARKETS ETF (EM capital flow gauge — ±1 pt) ─────────────────
    em = snapshot.get('em')
    if em:
        c5  = em['chg_5d']
        c30 = em['chg_30d']
        if c5 < -3:
            score -= 1
            _f('🌏', f'EM Sell-Off — {c5:.1f}% This Week',
               f'iShares MSCI EM ETF down {c5:.1f}% — broad emerging market outflows. '
               f'Saudi included in EM indices. 30d: {("+" if c30>=0 else "")}{c30:.1f}%.', '#ef4444')
        elif c5 > 3:
            score += 1
            _f('🌏', f'EM Inflows — +{c5:.1f}% This Week',
               f'Global money entering emerging markets. Saudi benefits as part of MSCI EM index. '
               f'30d: {("+" if c30>=0 else "")}{c30:.1f}%.', '#10a37f')

    # ── COMBINED SIGNAL: Oil crash + VIX spike = max danger ──────────────────
    if oil and vix:
        if oil['chg_5d'] < -5 and vix['price'] > 30:
            score -= 1   # extra penalty on top of individual penalties
            _f('🚨', 'COMBINED: Oil Crash + Market Panic',
               f'SIMULTANEOUS oil collapse ({oil["chg_5d"]:.1f}%) and high VIX ({vix["price"]:.0f}). '
               f'This is the worst possible scenario for Saudi stocks. '
               f'2014/2020/2022 crashes all had this combination. Extreme caution.', '#ef4444')

    # ── COMBINED SIGNAL: Oil rising + USD weakening = perfect storm ──────────
    if oil and usd:
        if oil['chg_5d'] > 3 and usd['chg_5d'] < -1:
            score += 1
            _f('✨', 'COMBINED: Oil Up + USD Down',
               f'Perfect combination for Saudi market: rising oil revenue AND weak dollar '
               f'attracting EM inflows simultaneously. Strong positive signal.', '#10a37f')

    # ── Clamp and label ───────────────────────────────────────────────────────
    score = max(-10, min(10, score))

    if score >= 6:
        label, color, bg = 'Strong Risk-ON 🚀', '#10a37f', '#0a1f1a'
    elif score >= 2:
        label, color, bg = 'Cautiously Bullish', '#4A9EFF', '#0d1f2d'
    elif score >= -1:
        label, color, bg = 'Neutral / Mixed ⚖️', '#fbbf24', '#1f1a08'
    elif score >= -4:
        label, color, bg = 'Caution ⚠️', '#f97316', '#1f1208'
    else:
        label, color, bg = 'Risk-OFF 🛑', '#ef4444', '#1f0808'

    return score, label, color, bg, factors



@st.cache_data(ttl=3600, show_spinner=False)
def get_saudi_news_headlines():
    """
    Fetch recent news headlines from free RSS feeds.
    Returns list of dicts: {title, source, link, date}.
    Cached for 1 hour.
    """
    headlines = []
    for source_name, feed_url in _NEWS_FEEDS:
        try:
            req = urllib.request.Request(
                feed_url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; TadawulAI/1.0)'},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                content = resp.read()

            root = ET.fromstring(content)
            ns   = {'atom': 'http://www.w3.org/2005/Atom'}

            # RSS 2.0 items or Atom entries
            items = root.findall('.//item') or root.findall('.//atom:entry', ns)
            for item in items[:8]:
                title_el   = item.find('title')
                link_el    = item.find('link')
                pubdate_el = item.find('pubDate') or item.find('atom:published', ns)
                title = (title_el.text or '').strip() if title_el is not None else ''
                if not title:
                    continue
                link  = (link_el.text or '#').strip() if link_el is not None else '#'
                date  = ((pubdate_el.text or '')[:16]).strip() if pubdate_el is not None else ''
                headlines.append({
                    'title':  title,
                    'source': source_name,
                    'link':   link,
                    'date':   date,
                })
        except Exception:
            pass

    return headlines[:25]


def macro_impact_on_signal(snapshot: dict, score: int) -> str:
    """
    Returns a plain-English one-line note about how current macro conditions
    should affect how a trader interprets buy signals.
    Used inline in scan results.
    """
    oil = snapshot.get('brent') or snapshot.get('wti')
    vix = snapshot.get('vix')

    notes = []
    if oil and oil['chg_5d'] < -3:
        notes.append(f"oil down {oil['chg_5d']:.1f}% this week")
    if vix and vix['price'] > 28:
        notes.append(f"VIX at {vix['price']:.0f} (elevated fear)")

    if not notes:
        return ""
    if score <= -4:
        return "⚠️ Macro risk-off: " + " · ".join(notes) + " — use smaller position sizes"
    return "⚠️ Macro caution: " + " · ".join(notes)
