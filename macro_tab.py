"""
macro_tab.py — Global Macro Intelligence Tab for TadawulAI
===========================================================
Displays macro factors that move Saudi stocks independently of technicals:
  - Macro Health Score (oil, VIX, USD, global risk)
  - Live macro instrument cards
  - "What this means for your trades" playbook
  - Saudi & global news headlines from RSS
"""

import streamlit as st
from macro_data import (
    get_macro_snapshot,
    compute_macro_health,
    get_saudi_news_headlines,
)


def _metric_card(label, price, unit, chg_1d, chg_5d, bullish_up):
    """Render a single macro instrument card."""
    c1d_col  = '#10a37f' if (chg_1d > 0) == bullish_up else '#ef4444'
    c5d_col  = '#10a37f' if (chg_5d > 0) == bullish_up else '#ef4444'
    c1d_sign = '+' if chg_1d >= 0 else ''
    c5d_sign = '+' if chg_5d >= 0 else ''

    # Format price
    if price >= 1000:
        p_str = f"{price:,.0f}"
    elif price >= 10:
        p_str = f"{price:.2f}"
    else:
        p_str = f"{price:.3f}"

    price_display = f"{p_str} {unit}".strip()

    return (
        f'<div style="background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;'
        f'padding:1rem 1.2rem;display:flex;flex-direction:column;gap:0.35rem;">'
        f'<div style="font-size:0.68rem;color:#888;text-transform:uppercase;'
        f'letter-spacing:1px;font-weight:700;">{label}</div>'
        f'<div style="font-size:1.3rem;font-weight:800;color:#fff;line-height:1.1;">'
        f'{price_display}</div>'
        f'<div style="display:flex;gap:0.8rem;">'
        f'<span style="font-size:0.78rem;font-weight:700;color:{c1d_col};">'
        f'{c1d_sign}{chg_1d:.2f}% today</span>'
        f'<span style="font-size:0.78rem;font-weight:600;color:{c5d_col};">·</span>'
        f'<span style="font-size:0.78rem;font-weight:700;color:{c5d_col};">'
        f'{c5d_sign}{chg_5d:.2f}% 5d</span>'
        f'</div>'
        f'</div>'
    )


def _score_gauge(score, label, color, bg):
    """Render the big macro health score gauge."""
    # Map score (-10 to +10) → arc width (10% to 90%)
    pct = (score + 10) / 20 * 100
    bar_color = color

    return (
        f'<div style="background:{bg};border:1px solid {color}44;border-radius:16px;'
        f'padding:1.5rem 2rem;text-align:center;">'
        f'<div style="font-size:0.7rem;color:#888;text-transform:uppercase;'
        f'letter-spacing:1.2px;font-weight:700;margin-bottom:0.5rem;">MACRO HEALTH SCORE</div>'

        # Score bar
        f'<div style="background:#1a1a1a;border-radius:999px;height:12px;'
        f'width:100%;margin:0.6rem 0;">'
        f'<div style="background:linear-gradient(90deg,#ef4444,#fbbf24,#10a37f);'
        f'border-radius:999px;height:12px;width:{pct:.0f}%;'
        f'transition:width 0.5s ease;"></div>'
        f'</div>'

        # Score number
        f'<div style="font-size:3rem;font-weight:900;color:{color};line-height:1;">'
        f'{score:+d}/10</div>'
        f'<div style="font-size:1.1rem;font-weight:700;color:{color};margin-top:0.3rem;">'
        f'{label}</div>'
        f'<div style="font-size:0.75rem;color:#666;margin-top:0.5rem;">'
        f'Based on oil prices, VIX fear gauge, USD strength, S&P 500 momentum · Updated every 30 min'
        f'</div>'
        f'</div>'
    )


def _playbook(score, factors, snapshot):
    """Return trading playbook advice based on macro conditions."""
    oil  = snapshot.get('brent') or snapshot.get('wti')
    vix  = snapshot.get('vix')
    oil_p = f"${oil['price']:.1f}/bbl" if oil else "N/A"
    vix_p = f"{vix['price']:.0f}" if vix else "N/A"

    if score >= 6:
        return (
            "Strong macro tailwinds for Saudi stocks.",
            [
                f"Oil at {oil_p} — Saudi government revenue strong, supports market confidence",
                "Global risk appetite is healthy — foreign investors more likely to buy",
                "This is a good environment to run full-size positions on high-conviction setups",
                "Focus on Energy, Petrochemicals, and Banks which benefit most from oil strength",
            ],
            '#10a37f'
        )
    elif score >= 2:
        return (
            "Macro is supportive but watch for reversals.",
            [
                "Conditions favor holding your buy signals — no major red flags",
                "Keep an eye on oil: a sudden drop > 3% in a day would change the picture",
                f"VIX at {vix_p} — global markets are calm, no panic yet",
                "Reasonable environment for normal position sizes",
            ],
            '#4A9EFF'
        )
    elif score >= -1:
        return (
            "Mixed signals — macro is neither helping nor hurting.",
            [
                "Be selective: only the highest-conviction setups (Score ≥ 12, Confidence ≥ 70%)",
                f"Oil at {oil_p} — not a strong tailwind right now",
                "Reduce position size by 25–30% until macro clarifies",
                "Avoid chasing breakouts — wait for the stock to prove itself first",
            ],
            '#fbbf24'
        )
    elif score >= -4:
        return (
            "Macro headwinds — trade with extra caution.",
            [
                f"Oil at {oil_p} — weakening oil hurts Saudi market broadly",
                f"VIX at {vix_p} — global risk aversion elevated",
                "Use 50% of your normal position size maximum",
                "Prioritize stocks with strong fundamentals AND technicals — avoid speculative names",
                "Set tighter stops — volatility is higher, gaps are more likely",
            ],
            '#f97316'
        )
    else:
        return (
            "Macro risk-OFF — significant headwinds for Saudi stocks.",
            [
                f"Oil at {oil_p} — major pressure on Saudi economy",
                f"VIX at {vix_p} — global panic level — foreign investors are selling across the board",
                "Do NOT chase buy signals in this environment",
                "If you must trade: only very oversold stocks (RSI < 25) with strong support",
                "Keep cash, wait for oil to stabilize and VIX to drop below 25",
                "This market environment can produce fast 5–10% drops even in strong stocks",
            ],
            '#ef4444'
        )


def render_macro_tab():
    """Main entry point — renders the full Macro Intelligence page."""

    st.markdown("""
    <style>
    section[data-testid="stMainBlockContainer"] { padding-top: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Fetch data ─────────────────────────────────────────────────────────────
    with st.spinner("Loading macro data..."):
        snapshot = get_macro_snapshot()

    if not snapshot:
        st.error("Could not load macro data. Check your internet connection.")
        return

    score, label, color, bg, factors = compute_macro_health(snapshot)

    # ── Macro Health Score (top banner) ───────────────────────────────────────
    st.markdown(_score_gauge(score, label, color, bg), unsafe_allow_html=True)
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Instrument cards ──────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-size:0.7rem;color:#666;text-transform:uppercase;"
        "letter-spacing:1.2px;font-weight:700;margin-bottom:0.6rem;'>Key Macro Instruments</div>",
        unsafe_allow_html=True
    )

    order = ['brent', 'vix', 'usd', 'gold', 'sp500', 'wti']
    available = [k for k in order if k in snapshot]
    cols = st.columns(len(available)) if available else []
    cards_html = "".join(
        _metric_card(
            snapshot[k]['label'],
            snapshot[k]['price'],
            snapshot[k]['unit'],
            snapshot[k]['chg_1d'],
            snapshot[k]['chg_5d'],
            snapshot[k]['bullish_up'],
        )
        for k in available
    )
    full_grid = (
        f'<div style="display:grid;grid-template-columns:repeat({len(available)},1fr);'
        f'gap:0.7rem;margin-bottom:1.2rem;">'
        + cards_html +
        f'</div>'
    )
    st.markdown(full_grid, unsafe_allow_html=True)

    # ── Two-column layout: Factors + Playbook ────────────────────────────────
    left, right = st.columns(2, gap="medium")

    with left:
        st.markdown(
            "<div style='font-size:0.7rem;color:#666;text-transform:uppercase;"
            "letter-spacing:1.2px;font-weight:700;margin-bottom:0.6rem;'>What's Driving the Score</div>",
            unsafe_allow_html=True
        )
        if factors:
            rows = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:0.7rem;'
                f'padding:0.7rem 0;border-bottom:1px solid #1e1e1e;">'
                f'<span style="font-size:1rem;flex-shrink:0;">{em}</span>'
                f'<div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:{fcolor};">{title}</div>'
                f'<div style="font-size:0.78rem;color:#888;margin-top:0.2rem;">{exp}</div>'
                f'</div></div>'
                for em, title, exp, fcolor in factors
            )
            st.markdown(
                f'<div style="background:#141414;border:1px solid #222;border-radius:12px;'
                f'padding:0.2rem 1rem;">{rows}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("No significant macro factors detected.")

    with right:
        pb_title, pb_tips, pb_color = _playbook(score, factors, snapshot)
        st.markdown(
            f"<div style='font-size:0.7rem;color:#666;text-transform:uppercase;"
            f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.6rem;'>Trading Playbook Right Now</div>",
            unsafe_allow_html=True
        )
        tips_html = "".join(
            f'<div style="display:flex;align-items:flex-start;gap:0.6rem;'
            f'padding:0.55rem 0;border-bottom:1px solid #1e1e1e;">'
            f'<span style="color:{pb_color};flex-shrink:0;font-size:0.85rem;margin-top:0.1rem;">▸</span>'
            f'<span style="font-size:0.83rem;color:#ccc;line-height:1.5;">{tip}</span>'
            f'</div>'
            for tip in pb_tips
        )
        st.markdown(
            f'<div style="background:#141414;border:1px solid #222;border-radius:12px;'
            f'padding:0.2rem 1rem;">'
            f'<div style="font-size:0.88rem;font-weight:700;color:{pb_color};'
            f'padding:0.8rem 0 0.4rem;">{pb_title}</div>'
            f'{tips_html}'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Saudi Market Context ──────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.7rem;color:#666;text-transform:uppercase;"
        "letter-spacing:1.2px;font-weight:700;margin-bottom:0.6rem;'>Saudi Market Sensitivity to Macro Events</div>",
        unsafe_allow_html=True
    )

    sensitivity_data = [
        ("🛢️ Oil Price",       "Very High",  '#ef4444',
         "60–70% of Saudi government revenue. A 10% oil drop typically pulls TASI down 4–8%."),
        ("🌍 Global Risk (VIX)", "High",      '#f97316',
         "Foreign investors hold ~20% of TASI. When VIX > 30 they sell EM including Saudi."),
        ("💵 USD Strength",    "Medium",     '#fbbf24',
         "SAR is pegged to USD so no FX risk, but strong USD pressures oil prices down."),
        ("📊 S&P 500",         "Medium",     '#fbbf24',
         "Saudi stocks correlate ~0.45 with S&P. A US bear market drags Saudi lower."),
        ("🪙 Gold",            "Low-Medium", '#4A9EFF',
         "Surging gold signals global fear. Indirectly negative — watch as a warning signal."),
        ("⚔️ Geopolitics",     "Variable",   '#a78bfa',
         "Middle East tensions can spike Saudi stocks (oil risk premium) or sink them (fear outflows)."),
    ]

    sens_rows = ""
    for icon_factor, impact, sc, desc in sensitivity_data:
        sens_rows += (
            f'<div style="display:flex;align-items:flex-start;gap:1rem;'
            f'padding:0.8rem 1rem;border-bottom:1px solid #1e1e1e;">'
            f'<div style="flex:0 0 150px;">'
            f'<div style="font-size:0.85rem;font-weight:700;color:#ddd;">{icon_factor}</div>'
            f'<span style="font-size:0.7rem;font-weight:800;color:{sc};background:{sc}18;'
            f'padding:0.15rem 0.55rem;border-radius:4px;margin-top:0.3rem;display:inline-block;">'
            f'{impact}</span>'
            f'</div>'
            f'<div style="font-size:0.8rem;color:#999;line-height:1.55;padding-top:0.1rem;">{desc}</div>'
            f'</div>'
        )

    st.markdown(
        f'<div style="background:#141414;border:1px solid #222;border-radius:12px;'
        f'overflow:hidden;">{sens_rows}</div>',
        unsafe_allow_html=True
    )

    # ── News Headlines ────────────────────────────────────────────────────────
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.7rem;color:#666;text-transform:uppercase;"
        "letter-spacing:1.2px;font-weight:700;margin-bottom:0.6rem;'>Latest News & Events</div>",
        unsafe_allow_html=True
    )

    with st.spinner("Loading news..."):
        headlines = get_saudi_news_headlines()

    if headlines:
        news_html = "".join(
            f'<a href="{h["link"]}" target="_blank" style="text-decoration:none;">'
            f'<div style="padding:0.75rem 1rem;border-bottom:1px solid #1e1e1e;'
            f'display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;'
            f'transition:background 0.15s;" '
            f'onmouseover="this.style.background=\'#1e1e1e\'" '
            f'onmouseout="this.style.background=\'transparent\'">'
            f'<div>'
            f'<div style="font-size:0.85rem;color:#ddd;font-weight:600;line-height:1.45;">'
            f'{h["title"]}</div>'
            f'<div style="font-size:0.7rem;color:#555;margin-top:0.25rem;">'
            f'{h["source"]} · {h["date"]}</div>'
            f'</div>'
            f'<span style="color:#444;flex-shrink:0;font-size:0.9rem;padding-top:0.1rem;">↗</span>'
            f'</div></a>'
            for h in headlines
        )
        st.markdown(
            f'<div style="background:#141414;border:1px solid #222;border-radius:12px;'
            f'overflow:hidden;">{news_html}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background:#141414;border:1px solid #222;border-radius:12px;'
            'padding:1.5rem;text-align:center;color:#555;font-size:0.85rem;">'
            'Could not load news headlines. Check your internet connection or try refreshing.'
            '</div>',
            unsafe_allow_html=True
        )

    # ── Refresh note ─────────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;color:#444;font-size:0.72rem;margin-top:1.2rem;'>"
        "Macro data refreshes every 30 min · News refreshes every 60 min · "
        "Data from Yahoo Finance & public RSS feeds"
        "</div>",
        unsafe_allow_html=True
    )
