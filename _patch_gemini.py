"""
Patch gemini_tab.py:
  1. Replace hero card with improved deep-AI-analysis card
  2. Remove "Why This Decision — Signal Breakdown" section
  3. Improve Probability Breakdown section (conic rings, expected value, better layout)
"""

with open('gemini_tab.py', 'r', encoding='utf-8') as f:
    src = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1 — Replace hero card
# ─────────────────────────────────────────────────────────────────────────────
HERO_START = '    # ── 1. HERO CARD ──────────────────────────────────────────────────────────\n    st.markdown('
HERO_END   = '    # ── PRICE LADDER (BUY / is_trade only) ──────────────────────────────────'

idx_hs = src.find(HERO_START)
idx_he = src.find(HERO_END)
assert idx_hs != -1, f"HERO_START not found"
assert idx_he != -1, f"HERO_END not found"

NEW_HERO = '''\
    # ── 1. HERO CARD — Deep AI Analysis ─────────────────────────────────────
    # ── Market context extras ────────────────────────────────────────────────
    _hist_hi  = float(df['High'].tail(252).max()) if len(df) >= 50 else cp * 1.3
    _hist_lo  = float(df['Low'].tail(252).min())  if len(df) >= 50 else cp * 0.7
    _52w_pos  = round((cp - _hist_lo) / max(_hist_hi - _hist_lo, 0.01) * 100, 1)
    _52w_col  = BULL if _52w_pos >= 65 else (BEAR if _52w_pos <= 35 else NEUT)
    _adx_lbl  = ("Strong Trend" if (adx_current or 0) >= 30
                 else ("Trending" if (adx_current or 0) >= 20 else "Weak/Range"))
    _adx_col  = BULL if (adx_current or 0) >= 25 else (NEUT if (adx_current or 0) >= 15 else '#666')
    _rsi_lbl  = ("Oversold" if _rsi < 35 else ("Overbought" if _rsi > 65 else "Neutral"))
    _rsi_col  = BULL if _rsi < 35 else (BEAR if _rsi > 65 else '#9e9e9e')
    _reg_col  = (BULL if (current_regime or '') == "TREND" else
                 (INFO if (current_regime or '') == "BREAKOUT" else '#666'))
    _ema20c   = BULL if (price_vs_ema20  or 0) > 0 else BEAR
    _ema200c  = BULL if (price_vs_ema200 or 0) > 0 else BEAR
    _5dc      = BULL if (recent_5d_change  or 0) >= 0 else BEAR
    _20dc     = BULL if (recent_20d_change or 0) >= 0 else BEAR

    # Edge narrative
    if is_trade:
        _edge_txt = (
            f"{len(bull_inds)}/12 technical indicators bullish \u00b7 "
            f"ML ensemble {avg_ml:.0f}% UP probability across 5/10/20-day horizons \u00b7 "
            f"{avg_wr:.0f}% historical win rate from {_ana_n} analog setups. "
            f"Regime: {current_regime or 'Unknown'}. Strong BUY setup confirmed."
        ) if (avg_ml and avg_wr) else (
            f"{bp} bullish vs {rp} bearish signal points \u00b7 "
            f"Regime: {current_regime or 'Unknown'} \u00b7 {confidence}% confidence."
        )
    else:
        _dir_bias = "Bearish pressure dominant" if rp > bp else "Mixed \u2014 no clear edge"
        _edge_txt = (
            f"{bp} bull vs {rp} bear signal points. {_dir_bias}. "
            f"Wait for stronger multi-engine alignment before entering a position."
        )

    def _ctx_tile(lbl, val, col):
        return (
            f"<div style='text-align:center;padding:0.35rem 0.2rem;'>"
            f"<div style='font-size:0.48rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:0.5px;font-weight:700;margin-bottom:0.15rem;'>{lbl}</div>"
            f"<div style='font-size:0.82rem;font-weight:800;color:{col};'>{val}</div>"
            f"</div>"
        )

    def _stat_tile_g(lbl, big_val, sub, t_col, bar_val=None):
        bar_html = (
            f"<div style='background:{BDR};border-radius:999px;height:3px;"
            f"overflow:hidden;margin:0.3rem 0;'>"
            f"<div style='width:{int(min(bar_val,100))}%;height:100%;background:{t_col};"
            f"border-radius:999px;'></div></div>"
        ) if bar_val is not None else ""
        return (
            f"<div style='background:{BG};border-radius:12px;padding:0.85rem 0.9rem;"
            f"border:1px solid {BDR};border-top:3px solid {t_col};'>"
            f"<div style='font-size:0.49rem;color:#9e9e9e;text-transform:uppercase;"
            f"letter-spacing:0.7px;font-weight:700;margin-bottom:0.2rem;'>{lbl}</div>"
            f"<div style='font-size:1.8rem;font-weight:900;color:{t_col};line-height:1;'>{big_val}</div>"
            f"{bar_html}"
            f"<div style='font-size:0.62rem;color:#666;margin-top:0.25rem;'>{sub}</div>"
            f"</div>"
        )

    _ml_sub  = f"Accuracy: {_ml_acc_str}" if _ml_acc_str != 'N/A' else "5 models · 3 horizons"
    _wr_sub  = (f"Best: +{_ana_best:.1f}% / Worst: {_ana_worst:.1f}%"
                if _ana_best is not None else f"{_ana_n} analog setups")

    st.markdown(
        f"<div style='background:linear-gradient(135deg,{BG2} 0%,{BG} 100%);"
        f"border:1px solid {BDR};border-left:6px solid {hero_col};"
        f"border-radius:16px;padding:1.6rem 2rem;margin-bottom:1.2rem;'>"

        # ── Row 1: direction verdict + AI score + signal edge
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
        f"flex-wrap:wrap;gap:1.5rem;margin-bottom:1rem;'>"
        f"<div>"
        f"<div style='font-size:0.55rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:2px;font-weight:700;margin-bottom:0.25rem;'>Deep AI Analysis</div>"
        f"<div style='font-size:3rem;font-weight:900;color:{hero_col};"
        f"line-height:1;letter-spacing:-1.5px;'>{hero_dir}</div>"
        f"<div style='font-size:0.8rem;color:#9e9e9e;margin-top:0.3rem;'>{hero_sub}</div>"
        f"</div>"
        f"<div style='display:flex;gap:2.5rem;text-align:right;flex-shrink:0;'>"
        f"<div>"
        f"<div style='font-size:0.5rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>AI Score</div>"
        f"<div style='font-size:2.6rem;font-weight:900;color:{score_col};line-height:1;'>"
        f"{score}<span style='font-size:0.85rem;color:#555;'>/100</span></div>"
        f"<div style='font-size:0.6rem;color:#555;'>"
        f"{len(bull_inds)}&#9650; &middot; {len(bear_inds)}&#9660; &middot; {len(neut_inds)} neutral</div>"
        f"</div>"
        f"<div>"
        f"<div style='font-size:0.5rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>Signal Edge</div>"
        f"<div style='font-size:2.6rem;font-weight:900;color:{hero_col};line-height:1;'>"
        f"{'HIGH' if bp >= rp + 5 else ('MOD' if bp >= rp + 2 else ('LOW' if bp >= rp else 'NONE'))}"
        f"</div>"
        f"<div style='font-size:0.6rem;color:#555;'>{bp} bull &middot; {rp} bear pts</div>"
        f"</div>"
        f"</div>"
        f"</div>"

        # ── Edge narrative
        f"<div style='background:{hero_col}10;border:1px solid {hero_col}2E;"
        f"border-radius:10px;padding:0.7rem 1rem;margin-bottom:1.1rem;"
        f"font-size:0.78rem;color:#bbb;line-height:1.65;'>{_edge_txt}</div>"

        # ── 4-stat grid
        f"<div style='display:grid;grid-template-columns:repeat(4,1fr);"
        f"gap:0.6rem;padding-top:0.85rem;border-top:1px solid {BDR};margin-bottom:1rem;'>"
        + _stat_tile_g("AI Score (12 indicators)", str(score), _score_txt, score_col, score)
        + _stat_tile_g("ML Ensemble (avg 5/10/20d)", ml_str, _ml_sub, ml_d_col, avg_ml or 50)
        + _stat_tile_g(f"Pattern Win Rate ({_ana_hor}d)", wr_str, _wr_sub, wr_d_col, avg_wr or 50)
        + _stat_tile_g("Top ML Drivers", (_feat_str[:26] if _feat_str != 'N/A' else '—'),
                       "XGBoost feature importance", INFO)
        + f"</div>"

        # ── Context strip (6 tiles)
        f"<div style='display:grid;grid-template-columns:repeat(6,1fr);"
        f"gap:0.5rem;padding-top:0.75rem;border-top:1px solid {BDR};'>"
        + _ctx_tile("Regime",   current_regime or "—",                                _reg_col)
        + _ctx_tile("ADX",      f"{adx_current:.0f} &middot; {_adx_lbl}" if adx_current else "—", _adx_col)
        + _ctx_tile("RSI",      f"{_rsi:.0f} &middot; {_rsi_lbl}",                   _rsi_col)
        + _ctx_tile("EMA 200",  f"{'+' if (price_vs_ema200 or 0) >= 0 else ''}{(price_vs_ema200 or 0):.1f}%", _ema200c)
        + _ctx_tile("5D Chg",   f"{(recent_5d_change  or 0):+.1f}%",                _5dc)
        + _ctx_tile("52W Pos",  f"{_52w_pos:.0f}th pct",                             _52w_col)
        + f"</div>"

        f"</div>",
        unsafe_allow_html=True,
    )

    # ── PRICE LADDER (BUY / is_trade only) ──────────────────────────────────'''

src = src[:idx_hs] + NEW_HERO + '\n' + src[idx_he:]
print("PATCH 1 OK — hero card replaced")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2 — Remove "Why This Decision — Signal Breakdown" section
# ─────────────────────────────────────────────────────────────────────────────
WHY_START = '    # ── 4. WHY THIS DECISION — actionable signal breakdown ───────────────────'
PROB_START = "    # ── 5. PROBABILITY BREAKDOWN — compact, high-signal per horizon ─────────────"

idx_ws = src.find(WHY_START)
idx_ps = src.find(PROB_START)
assert idx_ws != -1, "WHY_START not found"
assert idx_ps != -1, "PROB_START not found"

# Remove the Why section entirely (jump from price ladder directly to Probability)
src = src[:idx_ws] + src[idx_ps:]
print("PATCH 2 OK — Why This Decision section removed")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 3 — Replace Probability Breakdown + Methodology note with improved version
# ─────────────────────────────────────────────────────────────────────────────
PROB_MARKER  = "    # ── 5. PROBABILITY BREAKDOWN — compact, high-signal per horizon ─────────────"
METHOD_END   = "f\"Past performance does not guarantee future results.</div>\","
# Find the end of the methodology note
idx_prob  = src.find(PROB_MARKER)
# We'll find end by locating the last st.markdown closing in the file
# Actually let's find the end of the methodology note
METHOD_SNIP = "        f\"Past performance does not guarantee future results.</div>\","
idx_mend_line = src.find(METHOD_SNIP)
assert idx_mend_line != -1, "method end not found"
# Move to end of that block (one more line: unsafe_allow_html + close paren)
end_block     = src.find('\n', idx_mend_line)
end_block     = src.find('\n', end_block + 1)  # unsafe_allow_html line
end_block     = src.find('\n', end_block + 1)  # closing paren "    )"
end_block     = src.find('\n', end_block + 1)  # newline after

assert idx_prob != -1, "PROB_MARKER not found"

NEW_PROB = '''\
    # ── 5. PROBABILITY BREAKDOWN — 5 / 10 / 20 Day ──────────────────────────
    st.markdown(_sec('Probability Breakdown \u2014 5 / 10 / 20 Day', PURP),
                unsafe_allow_html=True)

    def _scale_pt(val, scale):
        if val is None:
            return None
        return round(_entry + (val - _entry) * scale, 2)

    horizons_data = [
        (ml5,  ana5,  '5-Day',  'Next 5 days',  0.30),
        (ml10, ana10, '10-Day', 'Next 2 weeks', 0.60),
        (ml20, ana20, '20-Day', 'Next month',   1.00),
    ]
    pb_cols = st.columns(3, gap='medium')

    for col, (ml, ana, label, desc, pt_scale) in zip(pb_cols, horizons_data):
        ml_prob  = ml['up_prob']         if ml  else None
        wr_val   = ana['w_win_rate']     if ana else None
        med_ret  = ana['median_return']  if ana else None
        best_ret = ana['best_case']      if ana else None
        wrst_ret = ana['worst_case']     if ana else None
        n_sim    = ana['n_similar']      if ana else 0
        n_up     = ana['n_up']           if ana else 0
        n_dn     = ana.get('n_down', 0) if ana else 0

        _p25 = _scale_pt(pt20.get('p25') if pt20 else None, pt_scale)
        _p50 = _scale_pt(pt20.get('p50') if pt20 else None, pt_scale)
        _p75 = _scale_pt(pt20.get('p75') if pt20 else None, pt_scale)

        up_p = ml_prob or 50
        dn_p = 100 - up_p
        wv   = wr_val  or 50

        # Confluence badge
        ml_bull  = up_p >= 55;  ml_bear = up_p <= 45
        ana_bull = wv   >= 55;  ana_bear = wv  <= 45
        if   ml_bull and ana_bull:  conf_lbl, conf_col_h = '&#9679; BOTH AGREE UP',    BULL
        elif ml_bear and ana_bear:  conf_lbl, conf_col_h = '&#9679; BOTH AGREE DOWN',  BEAR
        elif ml_bull or  ana_bull:  conf_lbl, conf_col_h = '&#9680; MIXED \u2014 LEAN UP',  NEUT
        elif ml_bear or  ana_bear:  conf_lbl, conf_col_h = '&#9681; MIXED \u2014 LEAN DOWN', '#FF7043'
        else:                       conf_lbl, conf_col_h = '&#9675; NEUTRAL',              '#555'

        pc = BULL if up_p >= 55 else (BEAR if up_p <= 45 else NEUT)
        wc = BULL if wv   >= 55 else (BEAR if wv   <= 45 else NEUT)
        mc = BULL if (med_ret or 0) >= 0 else BEAR

        # Expected value (simple: win_rate × median_return)
        _ev = round((wv / 100) * (med_ret or 0), 2) if med_ret is not None else None
        _ev_col = BULL if (_ev or 0) >= 0 else BEAR

        # Price zone helper
        def _pz(price, clr, tier):
            if price is None:
                return ''
            pct = (price - _entry) / _entry * 100
            sgn = '+' if pct >= 0 else ''
            return (
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:0.32rem 0.7rem;border-radius:8px;"
                f"background:{clr}15;border:1px solid {clr}40;margin-bottom:0.25rem;'>"
                f"<span style='font-size:0.6rem;color:#666;font-weight:600;'>{tier}</span>"
                f"<div style='text-align:right;'>"
                f"<span style='font-size:0.82rem;font-weight:900;color:{clr};'>{price:.2f}</span>"
                f"<span style='font-size:0.65rem;color:{clr};margin-left:0.35rem;'>"
                f"{sgn}{pct:.1f}%</span>"
                f"</div></div>"
            )

        # ML probability ring (CSS conic-gradient)
        _ring_deg = int(up_p * 3.6)
        _ring_html = (
            f"<div style='position:relative;width:72px;height:72px;"
            f"flex-shrink:0;'>"
            f"<div style='width:72px;height:72px;border-radius:50%;"
            f"background:conic-gradient({pc} 0deg {_ring_deg}deg,"
            f" {BEAR} {_ring_deg}deg 360deg);'></div>"
            f"<div style='position:absolute;top:9px;left:9px;width:54px;height:54px;"
            f"border-radius:50%;background:{BG2};"
            f"display:flex;flex-direction:column;align-items:center;"
            f"justify-content:center;'>"
            f"<span style='font-size:1.1rem;font-weight:900;color:{pc};"
            f"line-height:1;'>{up_p:.0f}%</span>"
            f"<span style='font-size:0.45rem;color:#555;text-transform:uppercase;"
            f"letter-spacing:0.3px;'>UP</span>"
            f"</div></div>"
        )

        # Precompute conditional HTML blocks
        _wr_cnt   = f"{n_up}&#8593; / {n_dn}&#8595; of {n_sim}" if wr_val is not None else 'no data'
        _wr_num   = f"{wv:.0f}%" if wr_val is not None else 'N/A'

        if _p50 is not None:
            _zone_html = (
                f"<div style='font-size:0.55rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.5px;font-weight:700;margin-bottom:0.35rem;"
                f"margin-top:0.65rem;'>Price Forecast ({label})</div>"
                + (_pz(_p75, BULL, 'Bull case') if _p75 is not None else '')
                + _pz(_p50, NEUT, 'Base case')
                + (_pz(_p25, '#FF7043', 'Bear case') if _p25 is not None else '')
            )
        else:
            _zone_html = ''

        if wr_val is not None and med_ret is not None and best_ret is not None and wrst_ret is not None:
            _hist_html = (
                f"<div style='font-size:0.55rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.5px;font-weight:700;margin:0.65rem 0 0.35rem;'>"
                f"Historical Outcomes ({n_sim} setups)</div>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.28rem;'>"
                f"<div style='background:{BULL}12;border:1px solid {BULL}30;"
                f"border-radius:8px;padding:0.38rem;text-align:center;'>"
                f"<div style='font-size:0.47rem;color:#9e9e9e;margin-bottom:0.08rem;'>BEST</div>"
                f"<div style='font-size:0.95rem;font-weight:900;color:{BULL};'>"
                f"+{best_ret:.1f}%</div></div>"
                f"<div style='background:{mc}15;border:1px solid {mc}38;"
                f"border-radius:8px;padding:0.38rem;text-align:center;'>"
                f"<div style='font-size:0.47rem;color:#9e9e9e;margin-bottom:0.08rem;'>MEDIAN</div>"
                f"<div style='font-size:0.95rem;font-weight:900;color:{mc};'>"
                f"{med_ret:+.1f}%</div></div>"
                f"<div style='background:{BEAR}12;border:1px solid {BEAR}30;"
                f"border-radius:8px;padding:0.38rem;text-align:center;'>"
                f"<div style='font-size:0.47rem;color:#9e9e9e;margin-bottom:0.08rem;'>WORST</div>"
                f"<div style='font-size:0.95rem;font-weight:900;color:{BEAR};'>"
                f"{wrst_ret:.1f}%</div></div>"
                f"</div>"
            )
            _ev_html = (
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;margin-top:0.55rem;padding:0.38rem 0.7rem;"
                f"background:{_ev_col}10;border:1px solid {_ev_col}30;"
                f"border-radius:8px;'>"
                f"<span style='font-size:0.58rem;color:#666;font-weight:600;'>"
                f"Expected Value</span>"
                f"<span style='font-size:0.9rem;font-weight:900;color:{_ev_col};'>"
                f"{_ev:+.2f}%</span>"
                f"</div>"
            ) if _ev is not None else ''
        else:
            _hist_html = ''
            _ev_html   = ''

        with col:
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:4px solid {pc};border-radius:16px;"
                f"padding:1.2rem 1.1rem;height:100%;'>"

                # Header row
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:flex-start;margin-bottom:0.7rem;'>"
                f"<div>"
                f"<div style='font-size:0.62rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>"
                f"{label} &middot; {desc}</div>"
                f"<div style='font-size:0.78rem;font-weight:800;color:{conf_col_h};'>"
                f"{conf_lbl}</div>"
                f"</div>"
                + _ring_html +
                f"</div>"

                # ML vs History row
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.45rem;"
                f"margin-bottom:0.6rem;'>"
                f"<div style='background:{BG};border:1px solid {pc}50;"
                f"border-radius:10px;padding:0.6rem 0.7rem;text-align:center;'>"
                f"<div style='font-size:0.5rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.5px;margin-bottom:0.1rem;'>ML Model</div>"
                f"<div style='font-size:1.75rem;font-weight:900;color:{pc};line-height:1;'>"
                f"{up_p:.0f}%</div>"
                f"<div style='font-size:0.6rem;color:#666;margin-top:0.08rem;'>chance UP</div>"
                f"</div>"
                f"<div style='background:{BG};border:1px solid {wc}50;"
                f"border-radius:10px;padding:0.6rem 0.7rem;text-align:center;'>"
                f"<div style='font-size:0.5rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.5px;margin-bottom:0.1rem;'>History</div>"
                f"<div style='font-size:1.75rem;font-weight:900;color:{wc};line-height:1;'>"
                f"{_wr_num}</div>"
                f"<div style='font-size:0.6rem;color:#666;margin-top:0.08rem;'>{_wr_cnt}</div>"
                f"</div></div>"

                # Split bar (up vs down)
                f"<div style='display:flex;border-radius:6px;overflow:hidden;"
                f"height:8px;margin-bottom:0.7rem;'>"
                f"<div style='background:{BULL};width:{up_p}%;'></div>"
                f"<div style='background:{BEAR};width:{dn_p}%;'></div>"
                f"</div>"
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:0.55rem;margin-bottom:0.55rem;'>"
                f"<span style='color:{BULL};'>&#9650; {up_p:.0f}% UP</span>"
                f"<span style='color:{BEAR};'>&#9660; {dn_p:.0f}% DOWN</span>"
                f"</div>"

                + _zone_html
                + _hist_html
                + _ev_html

                + f"</div>",
                unsafe_allow_html=True,
            )

    # ── METHODOLOGY NOTE ──────────────────────────────────────────────────────
    st.markdown(
        f"<div style='margin-top:1rem;padding:0.8rem 1rem;"
        f"background:{BG2};border:1px solid {BDR};border-radius:10px;"
        f"font-size:0.62rem;color:#555;'>"
        f"<b style='color:#757575;'>Methodology:</b> "
        f"Trade direction determined by {len(factor_scores)}-factor scoring engine, "
        f"5-model ML ensemble (XGBoost \u00b7 LightGBM \u00b7 RF \u00b7 ET \u00b7 GB) with Platt calibration + "
        f"TimeSeriesSplit CV, XGBoost quantile regression for price targets (P10\u2013P90), "
        f"and 25-nearest-neighbour historical pattern matching. "
        f"Total data: {len(df)} bars \u00b7 {n_feat} features. "
        f"Past performance does not guarantee future results.</div>",
        unsafe_allow_html=True,
    )
'''

src = src[:idx_prob] + NEW_PROB
print("PATCH 3 OK — Probability Breakdown replaced")

with open('gemini_tab.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE — gemini_tab.py written")
