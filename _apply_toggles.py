"""
Patch script: replace inline insight strips with insight_toggle() calls,
and add insight_toggle() after every major section header across all tabs.
"""
import re, sys

def patch_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    for (old, new) in replacements:
        if old not in txt:
            print(f"  WARNING: pattern not found in {path}:\n    {old[:100]!r}")
            continue
        txt = txt.replace(old, new, 1)
        print(f"  patched: {old[:60]!r}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(f"  => saved {path}")

# ─────────────────────────────────────────────────────────────────────────────
# 1.  decision_tab.py
# ─────────────────────────────────────────────────────────────────────────────
DEC = r"c:\Users\moham\OneDrive\Desktop\My app\decision_tab.py"

# 1a. remove hero-card inline insight strip
HERO_OLD = (
    "        # \u2500\u2500 Insight strip: what Signal Strength means \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "        f\"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);\"\n"
    "        f\"border-left:4px solid {conf_c};border-radius:12px;\"\n"
    "        f\"padding:1rem 1.3rem;margin-top:0.6rem;'>\"\n"
    "        f\"<div style='display:flex;align-items:flex-start;gap:0.75rem;'>\"\n"
    "        f\"<span style='font-size:1.3rem;line-height:1;flex-shrink:0;'>&#128161;</span>\"\n"
    "        f\"<div>\"\n"
    "        f\"<div style='font-size:0.78rem;font-weight:800;color:#e0e0e0;\"\n"
    "        f\"letter-spacing:0.4px;margin-bottom:0.4rem;'>How Signal Strength is calculated</div>\"\n"
    "        f\"<div style='font-size:0.78rem;color:#bdbdbd;line-height:1.65;'>\"\n"
    "        f\"The platform evaluates <b style='color:#e0e0e0;'>{total_sigs} independent indicator groups</b>:\"\n"
    "        f\" EMA Stack, MACD, RSI, Stochastic, Bollinger Bands, ADX + Directional Index, Volume &amp; OBV, and Market Regime.\"\n"
    "        f\" Each group votes <b style='color:#4caf50;'>Bullish &#9650;</b> or <b style='color:#f44336;'>Bearish &#9660;</b>\"\n"
    "        f\" based on current market data.\"\n"
    "        f\" <b style='color:#e0e0e0;'>Signal Strength = Bullish votes \u00f7 Total votes \u00d7 100%.</b>\"\n"
    "        f\" A reading above 60% means the majority of the market's signals agree on a bullish direction.\"\n"
    "        f\"</div>\"\n"
    "        f\"</div>\"\n"
    "        f\"</div>\"\n"
    "        f\"</div>\"\n"
    "        # Score bar\n"
)
HERO_NEW = "        # Score bar\n"

# 1b. add insight_toggle after the hero card st.markdown() call
HERO_AFTER_OLD = (
    "        unsafe_allow_html=True,\n"
    "    )\n"
    "\n"
    "\n"
    "    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
    "    #  2. PRICE LADDER  (BUY signal only)\n"
)
HERO_AFTER_NEW = (
    "        unsafe_allow_html=True,\n"
    "    )\n"
    "    insight_toggle(\n"
    "        \"signal_strength\",\n"
    "        \"How is Signal Strength calculated?\",\n"
    "        f\"<p>The platform scores <strong>{total_sigs} independent indicator groups</strong> \u2014 each one examines the market from a different angle:</p>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>EMA Stack</strong> \u2014 Are prices above or below the 20/50/200-day moving averages? Full alignment = strongest trend signal.</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>MACD</strong> \u2014 Is momentum increasing bullishly or bearishly? Is the MACD line crossing its signal line?</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>RSI</strong> \u2014 Is the stock oversold (below 35, bounce potential) or overbought (above 70, pullback risk)?</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Stochastic</strong> \u2014 Fast line crossing from oversold or overbought territory signals potential reversals.</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Bollinger Bands</strong> \u2014 Is price near or outside the lower band (oversold) or upper band (stretched)?</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>ADX + Directional Index</strong> \u2014 Is there a strong trend direction? Is +DI (bullish momentum) or &minus;DI (bearish) dominant?</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Volume &amp; OBV</strong> \u2014 Is smart money flowing in (accumulation) or out (distribution)?</span></div>\"\n"
    "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Market Regime</strong> \u2014 Is the market Trending, Range-bound, or Volatile? Signals perform differently in each state.</span></div>\"\n"
    "        \"<p><strong>Signal Strength % = Bullish votes &divide; Total votes &times; 100.</strong> \"\n"
    "        \"Above 60% means most groups agree on a bullish setup. The Composite Score bar weights how strong each vote is, not just the count.</p>\"\n"
    "    )\n"
    "\n"
    "\n"
    "    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
    "    #  2. PRICE LADDER  (BUY signal only)\n"
)

# 1c. remove inline insight strip from live buy signals loop
LIVE_STRIP_OLD = (
    "                # Insight strip\n"
    "                f\"<div style='background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.09);\"\n"
    "                f\"border-left:4px solid {_accent};border-radius:11px;\"\n"
    "                f\"padding:0.85rem 1.1rem;margin-top:0.5rem;margin-bottom:0.2rem;'>\"\n"
    "                f\"<div style='display:flex;align-items:flex-start;gap:0.7rem;'>\"\n"
    "                f\"<span style='font-size:1.15rem;line-height:1;flex-shrink:0;'>&#128161;</span>\"\n"
    "                f\"<div>\"\n"
    "                f\"<div style='font-size:0.75rem;font-weight:800;color:#e0e0e0;margin-bottom:0.3rem;'>\"\n"
    "                f\"Why is confidence {_conf}%?\"\n"
    "                f\"</div>\"\n"
    "                f\"<div style='font-size:0.76rem;color:#bdbdbd;line-height:1.6;'>\"\n"
    "                f\"{_conf_explain}\"\n"
    "                f\"</div>\"\n"
    "                f\"</div>\"\n"
    "                f\"</div>\"\n"
    "                f\"</div>\"\n"
    "\n"
    "                f\"</div>\",\n"
)
LIVE_STRIP_NEW = (
    "\n"
    "                f\"</div>\",\n"
)

# 1d. add insight_toggle after the live buy signal card's st.markdown
LIVE_AFTER_OLD = (
    "                unsafe_allow_html=True,\n"
    "            )\n"
    "\n"
    "            # \u2500\u2500 Price Ladder \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "            try:\n"
)
LIVE_AFTER_NEW = (
    "                unsafe_allow_html=True,\n"
    "            )\n"
    "            insight_toggle(\n"
    "                f\"conf_{_tlabel.replace(' ','_')}\",\n"
    "                f\"Why is confidence {_conf}% \u2014 {_tlabel}?\",\n"
    "                f\"<p>{_conf_explain}</p>\",\n"
    "            )\n"
    "\n"
    "            # \u2500\u2500 Price Ladder \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
    "            try:\n"
)

patch_file(DEC, [
    (HERO_OLD, HERO_NEW),
    (HERO_AFTER_OLD, HERO_AFTER_NEW),
    (LIVE_STRIP_OLD, LIVE_STRIP_NEW),
    (LIVE_AFTER_OLD, LIVE_AFTER_NEW),
])

# ─────────────────────────────────────────────────────────────────────────────
# 2.  signal_analysis_tab.py  — add toggles after KPI grid
# ─────────────────────────────────────────────────────────────────────────────
SIG = r"c:\Users\moham\OneDrive\Desktop\My app\signal_analysis_tab.py"

with open(SIG, 'r', encoding='utf-8') as f:
    sig_txt = f.read()

# Find the KPI grid closing call  (sa-kpi-grid rendered via st.markdown)
# We inject after the closing `unsafe_allow_html=True` of that block.
# Anchor: look for the unique string "sa-kpi-grid" + the next st.tabs call
KPI_ANCHOR = "    tab_ind, tab_combo = st.tabs("
if KPI_ANCHOR in sig_txt:
    idx = sig_txt.index(KPI_ANCHOR)
    # walk back to the nearest `)\n` before the tabs call
    preceding = sig_txt[:idx]
    last_close = preceding.rfind("    )\n")
    if last_close >= 0:
        insert_pos = last_close + len("    )\n")
        toggle_block = (
            "    insight_toggle(\n"
            "        \"kpi_metrics\",\n"
            "        \"What do these 6 performance numbers mean?\",\n"
            "        \"<p><strong>Win Rate</strong> &mdash; Percentage of signals where price hit the profit target before hitting the stop loss. \"\n"
            "        \"Above 50% means the indicator was right more than wrong.</p>\"\n"
            "        \"<p><strong>Total Signals</strong> &mdash; How many times this indicator fired during the backtested period.</p>\"\n"
            "        \"<p><strong>Successful Signals</strong> &mdash; Signals that resulted in a win (target reached first).</p>\"\n"
            "        \"<p><strong>Failed Signals</strong> &mdash; Signals that were stopped out (stop loss hit first).</p>\"\n"
            "        \"<p><strong>Profit Factor</strong> &mdash; Total winning gain &divide; total losses. \"\n"
            "        \"A value above 1.5 means the strategy generates 1.5x more profit than it loses &mdash; a solid edge. Below 1.0 = net loser.</p>\"\n"
            "        \"<p><strong>Expectancy</strong> &mdash; Average return per signal = (Win Rate &times; Avg Gain) &minus; (Loss Rate &times; Avg Loss). \"\n"
            "        \"A positive expectancy means the strategy has a mathematical edge over time.</p>\"\n"
            "    )\n"
        )
        sig_txt = sig_txt[:insert_pos] + toggle_block + sig_txt[insert_pos:]
        print(f"  patched KPI toggle in signal_analysis_tab.py")
    else:
        print("  WARNING: could not find closing ) before st.tabs in signal_analysis_tab")
else:
    print(f"  WARNING: tab_ind anchor not found in {SIG}")

with open(SIG, 'w', encoding='utf-8') as f:
    f.write(sig_txt)
print(f"  => saved {SIG}")

# ─────────────────────────────────────────────────────────────────────────────
# 3.  volume_profile_tab.py — toggles after 2 section headers
# ─────────────────────────────────────────────────────────────────────────────
VP = r"c:\Users\moham\OneDrive\Desktop\My app\volume_profile_tab.py"

VP_PATCHES = [
    (
        "    st.markdown(_sec(\"Key Price Levels \u2014 Volume Based\", PURP), unsafe_allow_html=True)\n",
        "    st.markdown(_sec(\"Key Price Levels \u2014 Volume Based\", PURP), unsafe_allow_html=True)\n"
        "    insight_toggle(\n"
        "        \"vp_levels\",\n"
        "        \"What are POC, VAH, and VAL?\",\n"
        "        \"<p><strong>Point of Control (POC)</strong> &mdash; The exact price where the most volume was traded. \"\n"
        "        \"This is the market's 'fair value' anchor. Price tends to return here when it drifts away.</p>\"\n"
        "        \"<p><strong>Value Area High (VAH)</strong> &mdash; The upper boundary of the price range that contained 70% of all trading volume. \"\n"
        "        \"Acting as resistance: price above VAH is trading in 'premium' territory.</p>\"\n"
        "        \"<p><strong>Value Area Low (VAL)</strong> &mdash; The lower boundary of the 70% value area. \"\n"
        "        \"Acting as support: price below VAL is trading in 'discount' territory and often attracts buyers.</p>\"\n"
        "        \"<p>When price is <strong>inside the Value Area</strong>, there is high acceptance &mdash; price may range. \"\n"
        "        \"When price breaks <strong>outside</strong>, it often moves fast until it finds a new value area.</p>\"\n"
        "    )\n",
    ),
    (
        "    st.markdown(_sec(\"Volume Profile Chart\", INFO), unsafe_allow_html=True)\n",
        "    st.markdown(_sec(\"Volume Profile Chart\", INFO), unsafe_allow_html=True)\n"
        "    insight_toggle(\n"
        "        \"vp_chart\",\n"
        "        \"How to read the Volume Profile chart?\",\n"
        "        \"<p>The horizontal bars show how much volume was traded at each price level. \"\n"
        "        \"<strong>Tall bars</strong> = high-acceptance zones where buyers and sellers agreed heavily on price.</p>\"\n"
        "        \"<p><strong>Short bars</strong> = low-volume nodes (LVNs) where price moved quickly and held briefly. \"\n"
        "        \"These are often where price accelerates through in the future.</p>\"\n"
        "        \"<p>The <strong style='color:#ff9800'>orange line</strong> marks the Point of Control (POC). \"\n"
        "        \"Price above the POC tends to be bullish; below is bearish. \"\n"
        "        \"Breakouts from the Value Area with volume confirmation are the highest-conviction setups.</p>\"\n"
        "    )\n",
    ),
]
patch_file(VP, VP_PATCHES)

# ─────────────────────────────────────────────────────────────────────────────
# 4.  smc_tab.py — toggle after SMC Signal Breakdown
# ─────────────────────────────────────────────────────────────────────────────
SMC = r"c:\Users\moham\OneDrive\Desktop\My app\smc_tab.py"

with open(SMC, 'r', encoding='utf-8') as f:
    smc_txt = f.read()

# Find the SMC section header render
SMC_ANCHOR = "_sec(\"SMC Signal Breakdown\""
if SMC_ANCHOR in smc_txt:
    idx = smc_txt.index(SMC_ANCHOR)
    # find the end of that st.markdown() call (the next \n after `unsafe_allow_html=True)`)
    end_idx = smc_txt.index("unsafe_allow_html=True)\n", idx) + len("unsafe_allow_html=True)\n")
    smc_insert = (
        "    insight_toggle(\n"
        "        \"smc_breakdown\",\n"
        "        \"What are Smart Money Concepts (SMC)?\",\n"
        "        \"<p><strong>Order Blocks (OB)</strong> &mdash; The last bullish or bearish candle before a strong impulsive move. \"\n"
        "        \"Institutions place large orders here, making these zones high-probability reversal areas.</p>\"\n"
        "        \"<p><strong>Fair Value Gaps (FVG)</strong> &mdash; Price imbalances created when the market moved so fast that the buy/sell orders were not filled. \"\n"
        "        \"Price tends to fill these gaps before continuing in the original direction.</p>\"\n"
        "        \"<p><strong>Change of Character (CHoCH)</strong> &mdash; The first sign that a trend may be reversing. \"\n"
        "        \"In an uptrend: price breaks below the previous swing low for the first time.</p>\"\n"
        "        \"<p><strong>Break of Structure (BOS)</strong> &mdash; Confirms the trend is continuing. \"\n"
        "        \"In an uptrend: price breaks above the previous swing high, confirming bullish momentum.</p>\"\n"
        "        \"<p><strong>Liquidity Sweeps</strong> &mdash; Smart money triggers stop-losses clustered above swing highs or below swing lows \"\n"
        "        \"to grab liquidity before reversing. A sweep followed by a strong rejection is a powerful entry signal.</p>\"\n"
        "    )\n"
    )
    smc_txt = smc_txt[:end_idx] + smc_insert + smc_txt[end_idx:]
    print("  patched SMC toggle")
else:
    print(f"  WARNING: SMC anchor not found in {SMC}")

with open(SMC, 'w', encoding='utf-8') as f:
    f.write(smc_txt)
print(f"  => saved {SMC}")

# ─────────────────────────────────────────────────────────────────────────────
# 5.  regime_analysis_tab.py — toggles after 2 section headers
# ─────────────────────────────────────────────────────────────────────────────
REG = r"c:\Users\moham\OneDrive\Desktop\My app\regime_analysis_tab.py"

with open(REG, 'r', encoding='utf-8') as f:
    reg_txt = f.read()

# Section 1: Regime Distribution
DIST_ANCHOR = "_sec(f\"Regime Distribution"
if DIST_ANCHOR in reg_txt:
    idx = reg_txt.index(DIST_ANCHOR)
    end_idx = reg_txt.index("unsafe_allow_html=True)\n", idx) + len("unsafe_allow_html=True)\n")
    reg_txt = reg_txt[:end_idx] + (
        "    insight_toggle(\n"
        "        \"regime_dist\",\n"
        "        \"What are TREND, RANGE, and VOLATILE regimes?\",\n"
        "        \"<p><strong>TREND</strong> &mdash; The market is moving strongly in one direction. \"\n"
        "        \"Price is above (bullish) or below (bearish) its moving averages, and ADX is above 25. \"\n"
        "        \"Trend-following indicators (EMA, MACD) are most reliable in this regime.</p>\"\n"
        "        \"<p><strong>RANGE</strong> &mdash; The market is moving sideways between support and resistance. \"\n"
        "        \"ADX is below 20, price oscillates without a clear direction. \"\n"
        "        \"Mean-reversion indicators (RSI, Stochastic, Bollinger Bands) perform best here.</p>\"\n"
        "        \"<p><strong>VOLATILE</strong> &mdash; The market is making large, unpredictable swings in both directions. \"\n"
        "        \"High ATR relative to recent history. All trade signals carry higher risk \"\n"
        "        \"and tighter risk management (smaller positions, wider stops) is recommended.</p>\"\n"
        "        \"<p>The <strong>Regime Distribution</strong> bar shows how the stock spent time in each state over the past period. \"\n"
        "        \"A stock that was in TREND 70% of the time is a reliable trend-follower.</p>\"\n"
        "    )\n"
    ) + reg_txt[end_idx:]
    print("  patched Regime Distribution toggle")
else:
    print(f"  WARNING: Regime Distribution anchor not found in {REG}")

# Section 2: Regime Timeline
TL_ANCHOR = "_sec(\"Regime Timeline"
if TL_ANCHOR in reg_txt:
    idx = reg_txt.index(TL_ANCHOR)
    end_idx = reg_txt.index("unsafe_allow_html=True)\n", idx) + len("unsafe_allow_html=True)\n")
    reg_txt = reg_txt[:end_idx] + (
        "    insight_toggle(\n"
        "        \"regime_timeline\",\n"
        "        \"How to read the Regime Timeline?\",\n"
        "        \"<p>Each colored block on the timeline represents consecutive days the stock spent in the same regime. \"\n"
        "        \"<strong style='color:#4caf50'>Green = TREND (bullish)</strong>, \"\n"
        "        \"<strong style='color:#f44336'>Red = TREND (bearish)</strong>, \"\n"
        "        \"<strong style='color:#ff9800'>Orange = RANGE</strong>, \"\n"
        "        \"<strong style='color:#9e9e9e'>Grey = VOLATILE</strong>.</p>\"\n"
        "        \"<p>Look for transitions: a shift from RANGE to TREND is often the start of a breakout. \"\n"
        "        \"A shift from TREND to VOLATILE may signal exhaustion. \"\n"
        "        \"Long runs of a single color indicate a persistent, reliable market condition.</p>\"\n"
        "    )\n"
    ) + reg_txt[end_idx:]
    print("  patched Regime Timeline toggle")
else:
    print(f"  WARNING: Regime Timeline anchor not found in {REG}")

with open(REG, 'w', encoding='utf-8') as f:
    f.write(reg_txt)
print(f"  => saved {REG}")

# ─────────────────────────────────────────────────────────────────────────────
# 6.  trade_validator_tab.py — toggles after 2 section headers
# ─────────────────────────────────────────────────────────────────────────────
TV = r"c:\Users\moham\OneDrive\Desktop\My app\trade_validator_tab.py"

with open(TV, 'r', encoding='utf-8') as f:
    tv_txt = f.read()

VERDICT_ANCHOR = "_sec(\"Why This Verdict"
if VERDICT_ANCHOR in tv_txt:
    idx = tv_txt.index(VERDICT_ANCHOR)
    end_idx = tv_txt.index("unsafe_allow_html=True)\n", idx) + len("unsafe_allow_html=True)\n")
    tv_txt = tv_txt[:end_idx] + (
        "    insight_toggle(\n"
        "        \"tv_verdict\",\n"
        "        \"How is this verdict determined?\",\n"
        "        \"<p>The Trade Validator runs the current trade setup through every analytical engine simultaneously \"\n"
        "        \"and weighs the evidence. The verdict is determined by the <strong>net weight of all signals</strong>:</p>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Strong BUY</strong> &mdash; 4 or more engines confirm bullish setup with high confidence.</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Weak BUY</strong> &mdash; Majority bullish but some engines are neutral or conflicted.</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>HOLD / NEUTRAL</strong> &mdash; Mixed signals. The evidence is split; waiting for clarity is recommended.</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>AVOID</strong> &mdash; Multiple engines flagging bearish conditions or invalid setup structure.</span></div>\"\n"
        "        \"<p>Each key factor listed below shows exactly which part of the analysis pushed the verdict in its direction.</p>\"\n"
        "    )\n"
    ) + tv_txt[end_idx:]
    print("  patched Trade Validator Verdict toggle")
else:
    print(f"  WARNING: Why This Verdict anchor not found in {TV}")

CONSENSUS_ANCHOR = "_sec(\"Cross-Engine Consensus"
if CONSENSUS_ANCHOR in tv_txt:
    idx = tv_txt.index(CONSENSUS_ANCHOR)
    end_idx = tv_txt.index("unsafe_allow_html=True)\n", idx) + len("unsafe_allow_html=True)\n")
    tv_txt = tv_txt[:end_idx] + (
        "    insight_toggle(\n"
        "        \"tv_consensus\",\n"
        "        \"What is Cross-Engine Consensus?\",\n"
        "        \"<p>The platform has 5 independent analytical engines, each looking at the market from a different lens:</p>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Signal Engine</strong> &mdash; Classic technical indicators (EMA, MACD, RSI, Volume).</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Price Action Engine</strong> &mdash; Chart patterns, candlestick formations, Bull/Bear score.</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Volume Profile Engine</strong> &mdash; Where institutions traded (POC, VAH, VAL, HPZ).</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>SMC Engine</strong> &mdash; Smart Money Concepts: order blocks, FVGs, liquidity zones.</span></div>\"\n"
        "        \"<div class='itog-row'><span class='itog-dot'></span><span><strong>Regime Engine</strong> &mdash; What market state are we in: Trend, Range, or Volatile?</span></div>\"\n"
        "        \"<p>When all 5 engines agree, the trade setup has the highest probability of success. \"\n"
        "        \"When they conflict, the validator shows you exactly which engines disagree and why.</p>\"\n"
        "    )\n"
    ) + tv_txt[end_idx:]
    print("  patched Cross-Engine Consensus toggle")
else:
    print(f"  WARNING: Cross-Engine Consensus anchor not found in {TV}")

with open(TV, 'w', encoding='utf-8') as f:
    f.write(tv_txt)
print(f"  => saved {TV}")

# ─────────────────────────────────────────────────────────────────────────────
# 7.  price_action_tab.py — toggles after section headers + replace inline texts
# ─────────────────────────────────────────────────────────────────────────────
PA = r"c:\Users\moham\OneDrive\Desktop\My app\price_action_tab.py"

with open(PA, 'r', encoding='utf-8') as f:
    pa_txt = f.read()

def inject_after_sec(txt, sec_needle, key, label, body):
    if sec_needle not in txt:
        print(f"  WARNING: PA section not found: {sec_needle!r}")
        return txt
    idx = txt.index(sec_needle)
    end_idx = txt.index("unsafe_allow_html=True)\n", idx) + len("unsafe_allow_html=True)\n")
    toggle = (
        f"    insight_toggle(\n"
        f"        {key!r},\n"
        f"        {label!r},\n"
        f"        {body!r},\n"
        f"    )\n"
    )
    print(f"  patched PA toggle: {key}")
    return txt[:end_idx] + toggle + txt[end_idx:]

pa_txt = inject_after_sec(
    pa_txt,
    "_sec(\"Key Price Levels\"",
    "pa_levels",
    "How are Key Price Levels identified?",
    (
        "<p><strong>Support levels</strong> are price zones where buying pressure historically exceeded selling pressure, causing price to bounce upward. "
        "The more times a level has been tested and held, the stronger and more reliable it is.</p>"
        "<p><strong>Resistance levels</strong> are zones where sellers dominated and price reversed downward. "
        "Once broken convincingly (with volume), resistance often flips to become support.</p>"
        "<p>Levels are identified using swing highs/lows from recent trading sessions, "
        "looking for clusters of price rejections and high-volume nodes.</p>"
    ),
)

pa_txt = inject_after_sec(
    pa_txt,
    "_sec(\"Key Reaction Zones\"",
    "pa_zones",
    "What are Key Reaction Zones?",
    (
        "<p>Reaction zones are wider price bands (not single lines) where the market has repeatedly shown a strong response. "
        "Unlike precise support/resistance levels, these are <strong>high-probability reversal areas</strong> based on multiple touches.</p>"
        "<p><strong>Zone Strength</strong> is rated by the number of times price tested that zone and reversed: "
        "3+ touches = Strong, 2 touches = Moderate, 1 touch = Weak.</p>"
        "<p>Zones near the current price with a Strong rating are the highest-priority levels to watch for entries or exits.</p>"
    ),
)

pa_txt = inject_after_sec(
    pa_txt,
    "_sec(\"Trade Setup\"",
    "pa_setup",
    "How are Bull and Bear scores calculated?",
    (
        "<p>The <strong style='color:#4caf50'>Bull Score</strong> and <strong style='color:#f44336'>Bear Score</strong> "
        "are composite ratings (0-100) from the Price Action Engine.</p>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Candlestick Patterns</strong> &mdash; Hammer, engulfing, doji, morning star etc. +5 to +20 points each.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Chart Patterns</strong> &mdash; Head &amp; shoulders, double tops/bottoms, triangles, flags. +10 to +25 points.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Price Action vs. Levels</strong> &mdash; Is price bouncing from support, or rejecting resistance? +5 to +15 points.</span></div>"
        "<div class='itog-row'><span class='itog-dot'></span><span><strong>Volume Confirmation</strong> &mdash; Does volume confirm the move? High volume on a breakout adds confidence. +5 to +10 points.</span></div>"
        "<p>A score above 60 indicates a clear directional bias. When Bull Score &gt; Bear Score by 15+ points, it is a <strong>high-conviction directional setup</strong>.</p>"
    ),
)

with open(PA, 'w', encoding='utf-8') as f:
    f.write(pa_txt)
print(f"  => saved {PA}")

print("\nAll patches applied.")
