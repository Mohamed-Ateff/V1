"""Patch decision_tab.py: remove inline insight strips, add insight_toggle() calls."""
with open('decision_tab.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# ── 1. Hero card: remove lines 925-944 (0-indexed: 924-943) ──────────────────
# Lines 925-944 inclusive are the inline insight strip
# We delete them by filtering; then after the hero card markdown we insert toggle

new_lines = []
i = 0
while i < len(lines):
    ln = lines[i]
    # Detect start of the inline insight strip inside hero card
    if '# \u2500\u2500 Insight strip: what Signal Strength means' in ln:
        # skip this line plus the next 19 lines (the strip through the closing divs)
        # but stop before "# Score bar"
        while i < len(lines) and '# Score bar' not in lines[i]:
            i += 1
        # lines[i] is now "# Score bar\n" — keep it
        continue
    # Detect start of inline insight strip inside live buy loop
    if ln.strip() == '# Insight strip':
        # skip from here through the "f\"</div>\"," that closes the card
        # The card closing is:  f"</div>",   (with trailing comma)
        # We need to keep only that closing line
        while i < len(lines):
            if lines[i].rstrip().endswith('f"</div>",'):
                new_lines.append(lines[i])  # keep the closing </div>,
                i += 1
                break
            i += 1
        continue
    new_lines.append(ln)
    i += 1

txt = ''.join(new_lines)

# ── 2. Insert insight_toggle after the hero card st.markdown() ───────────────
# Anchor: right after the hero card's `        unsafe_allow_html=True,\n    )\n`
# Followed by two blank lines + the price ladder section comment
LADDER_SEC = (
    '\n'
    '\n'
    '    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n'
    '    #  2. PRICE LADDER  (BUY signal only)\n'
)

HERO_TOGGLE = (
    '    insight_toggle(\n'
    '        "signal_strength",\n'
    '        "How is Signal Strength calculated?",\n'
    '        f"<p>The platform scores <strong>{total_sigs} independent indicator groups</strong> \u2014 each examines the market from a different angle:</p>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>EMA Stack</strong> \u2014 Are prices above or below the 20/50/200-day moving averages? Full alignment = strongest trend signal.</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>MACD</strong> \u2014 Is momentum increasing bullishly or bearishly? Is the MACD line crossing its signal line?</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>RSI</strong> \u2014 Is the stock oversold (below 35, bounce potential) or overbought (above 70, pullback risk)?</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>Stochastic</strong> \u2014 Fast line crossing from oversold or overbought territory signals potential reversals.</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>Bollinger Bands</strong> \u2014 Is price near the lower band (oversold) or upper band (stretched/overextended)?</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>ADX + Directional Index</strong> \u2014 Is there a strong trend? Is +DI (bullish) or &minus;DI (bearish) dominant?</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>Volume &amp; OBV</strong> \u2014 Is smart money flowing in (accumulation) or out (distribution)?</span></div>"\n'
    '        "<div class=\'itog-row\'><span class=\'itog-dot\'></span><span><strong>Market Regime</strong> \u2014 Is the market Trending, Range-bound, or Volatile? Signals behave differently in each.</span></div>"\n'
    '        "<p><strong>Signal Strength % = Bullish votes &divide; Total votes &times; 100.</strong> "\n'
    '        "Above 60% means most groups agree on a bullish setup. The Composite Score bar weights how strong each vote is, not just the count.</p>"\n'
    '    )\n'
)

if LADDER_SEC in txt:
    txt = txt.replace(LADDER_SEC, HERO_TOGGLE + LADDER_SEC, 1)
    print("  inserted hero insight_toggle")
else:
    print("  WARNING: LADDER_SEC anchor not found")

# ── 3. Insert insight_toggle after each live buy signal card ─────────────────
# Anchor: after `                unsafe_allow_html=True,\n            )\n`
# followed by `\n            # ── Price Ladder`
PRICE_LADDER_COMMENT = '\n            # \u2500\u2500 Price Ladder \u2500\u2500\u2500'

CONF_TOGGLE = (
    '            insight_toggle(\n'
    '                f"conf_{_tlabel.replace(\' \',\'_\')}",\n'
    '                f"Why is confidence {_conf}% \u2014 {_tlabel}?",\n'
    '                f"<p>{_conf_explain}</p>",\n'
    '            )\n'
)

if PRICE_LADDER_COMMENT in txt:
    txt = txt.replace(PRICE_LADDER_COMMENT, CONF_TOGGLE + PRICE_LADDER_COMMENT, 1)
    print("  inserted conf insight_toggle")
else:
    print("  WARNING: Price Ladder comment anchor not found")

with open('decision_tab.py', 'w', encoding='utf-8') as f:
    f.write(txt)
print("  => saved decision_tab.py")
