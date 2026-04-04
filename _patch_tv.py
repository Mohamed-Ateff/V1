"""
Patch trade_validator_tab.py:
  1. Improve Why This Verdict — Key Factors
  2. Improve Cross-Engine Consensus
  3. Remove Smart Price Levels, Quality Checklist, Risk Snapshot & Action Summary
     (replace with disclaimer only)
"""
import re

with open('trade_validator_tab.py', 'r', encoding='utf-8') as f:
    src = f.read()

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 1 — Replace WHY VERDICT section
# ─────────────────────────────────────────────────────────────────────────────
WHY_OLD_START = '    # ══════════════════════════════════════════════════════════════════════════\n    #  WHY — Key reasons behind the verdict'
WHY_OLD_END   = '    # ══════════════════════════════════════════════════════════════════════════\n    #  ENGINE CONSENSUS'

WHY_NEW = '''\
    # ══════════════════════════════════════════════════════════════════════════
    #  WHY — Key reasons behind the verdict
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Why This Verdict — Key Factors", act_col), unsafe_allow_html=True)

    factors        = d.get("factors", [])
    sorted_factors = sorted(factors, key=lambda f: abs(f["pts"]), reverse=True)
    top_bull       = [f for f in sorted_factors if f["pts"] > 0][:5]
    top_bear       = [f for f in sorted_factors if f["pts"] < 0][:5]
    max_pts        = max((abs(f["pts"]) for f in sorted_factors), default=1)

    def _factor_impact_row(f, color):
        bar_w    = int(abs(f["pts"]) / max(abs(f["max"]), 1) * 100) if f["max"] else 0
        cat_lut  = {
            "Trend": INFO, "Momentum": BULL, "Oscillator": NEUT,
            "Volume": "#26c6da", "Pattern": PURP, "ML": GOLD,
        }
        cat_col = cat_lut.get(f["cat"], "#9e9e9e")
        return (
            f"<div style='display:flex;align-items:center;gap:0.7rem;"
            f"padding:0.55rem 0.8rem;margin-bottom:0.3rem;"
            f"background:{color}09;border-radius:10px;border:1px solid {color}22;'>"
            f"<div style='width:2.2rem;height:2.2rem;border-radius:50%;flex-shrink:0;"
            f"background:{color}22;border:2px solid {color}55;"
            f"display:flex;align-items:center;justify-content:center;'>"
            f"<span style='font-size:0.72rem;font-weight:900;color:{color};'>{f['pts']:+d}</span></div>"
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-size:0.74rem;color:#ddd;font-weight:700;"
            f"line-height:1.3;margin-bottom:0.22rem;'>{f['name']}</div>"
            f"<div style='background:{BDR};border-radius:999px;height:3px;overflow:hidden;'>"
            f"<div style='width:{bar_w}%;height:100%;background:{color};"
            f"border-radius:999px;'></div></div></div>"
            f"<div style='text-align:right;flex-shrink:0;'>"
            f"<div style='display:inline-block;background:{cat_col}18;"
            f"border:1px solid {cat_col}44;border-radius:4px;padding:0.1rem 0.45rem;"
            f"font-size:0.49rem;color:{cat_col};font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.5px;margin-bottom:0.1rem;'>{f['cat']}</div>"
            f"<div style='font-size:0.6rem;color:#555;'>{f['pts']:+d} / {f['max']} pts</div>"
            f"</div></div>"
        )

    reason_col1, reason_col2 = st.columns(2, gap="medium")

    with reason_col1:
        if top_bull:
            rows_html = "".join(_factor_impact_row(f, BULL) for f in top_bull)
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:3px solid {BULL};border-radius:14px;padding:1rem 1.1rem;'>"
                f"<div style='font-size:0.57rem;color:{BULL};text-transform:uppercase;"
                f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.65rem;'>"
                f"&#9650; Bullish Evidence &mdash; {len(top_bull)} factors</div>"
                f"{rows_html}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-radius:14px;padding:1rem;text-align:center;"
                f"font-size:0.75rem;color:#555;'>No bullish factors detected</div>",
                unsafe_allow_html=True,
            )

    with reason_col2:
        if top_bear:
            rows_html = "".join(_factor_impact_row(f, BEAR) for f in top_bear)
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-top:3px solid {BEAR};border-radius:14px;padding:1rem 1.1rem;'>"
                f"<div style='font-size:0.57rem;color:{BEAR};text-transform:uppercase;"
                f"letter-spacing:1.2px;font-weight:700;margin-bottom:0.65rem;'>"
                f"&#9660; Risk Evidence &mdash; {len(top_bear)} factors</div>"
                f"{rows_html}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background:{BG2};border:1px solid {BDR};"
                f"border-radius:14px;padding:1rem;text-align:center;"
                f"font-size:0.75rem;color:#555;'>No bearish risk factors detected</div>",
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════════════════════════
    #  ENGINE CONSENSUS'''

# Do the replacement
idx_start = src.find(WHY_OLD_START)
idx_end   = src.find(WHY_OLD_END)
assert idx_start != -1, "WHY_OLD_START not found"
assert idx_end   != -1, "WHY_OLD_END not found"
src = src[:idx_start] + WHY_NEW + '\n' + src[idx_end:]
print("PATCH 1 OK — WHY replaced")

# ─────────────────────────────────────────────────────────────────────────────
# PATCH 2 — Replace everything from ENGINE CONSENSUS to EOF
#            (improved consensus + remove Smart Price Levels / Checklist / Risk Snapshot)
# ─────────────────────────────────────────────────────────────────────────────
CONSENSUS_MARKER = '    # ══════════════════════════════════════════════════════════════════════════\n    #  ENGINE CONSENSUS'
idx_consensus = src.find(CONSENSUS_MARKER)
assert idx_consensus != -1, "CONSENSUS_MARKER not found"

NEW_TAIL = '''\
    # ══════════════════════════════════════════════════════════════════════════
    #  ENGINE CONSENSUS
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(_sec("Cross-Engine Consensus", INFO), unsafe_allow_html=True)

    # ── Weighted summary header ──────────────────────────────────────────────
    total_w  = sum(v['weight'] for v in verdicts.values())
    agree_w  = sum(v['weight'] for v in verdicts.values() if v['verdict'] == 'agree')
    conf_w   = sum(v['weight'] for v in verdicts.values() if v['verdict'] == 'conflict')
    agree_bw = round(agree_w / max(total_w, 1) * 100)
    conf_bw  = round(conf_w  / max(total_w, 1) * 100)

    st.markdown(
        f"<div style='background:{BG2};border:1px solid {BDR};"
        f"border-radius:14px;padding:1.2rem 1.5rem;margin-bottom:1rem;'>"
        f"<div style='display:flex;align-items:center;gap:2rem;flex-wrap:wrap;"
        f"margin-bottom:0.85rem;'>"

        # Consensus score
        f"<div>"
        f"<div style='font-size:0.52rem;color:#9e9e9e;text-transform:uppercase;"
        f"letter-spacing:1px;font-weight:700;margin-bottom:0.15rem;'>Weighted Score</div>"
        f"<div style='font-size:2.8rem;font-weight:900;color:{cs_col};line-height:1;'>"
        f"{confluence_score:.0f}%</div>"
        f"<div style='font-size:0.62rem;color:#555;margin-top:0.1rem;'>"
        f"{agree_count}/{n_engines} engines support the verdict</div>"
        f"</div>"

        # Count pills
        f"<div style='display:flex;gap:1.4rem;'>"
        f"<div style='text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:900;color:{BULL};'>{agree_count}</div>"
        f"<div style='font-size:0.55rem;color:{BULL};text-transform:uppercase;"
        f"letter-spacing:0.5px;'>Agree</div></div>"
        f"<div style='text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:900;color:{BEAR};'>{conflict_count}</div>"
        f"<div style='font-size:0.55rem;color:{BEAR};text-transform:uppercase;"
        f"letter-spacing:0.5px;'>Conflict</div></div>"
        f"<div style='text-align:center;'>"
        f"<div style='font-size:2rem;font-weight:900;color:#555;'>{neutral_count}</div>"
        f"<div style='font-size:0.55rem;color:#555;text-transform:uppercase;"
        f"letter-spacing:0.5px;'>Neutral</div></div>"
        f"</div>"

        # Weighted bar
        f"<div style='flex:1;min-width:180px;'>"
        f"<div style='font-size:0.55rem;color:#555;margin-bottom:0.35rem;'>"
        f"Agreement weight: {agree_w}% &nbsp;·&nbsp; Conflict weight: {conf_w}%</div>"
        f"<div style='display:flex;border-radius:999px;overflow:hidden;height:14px;'>"
        f"<div style='background:{BULL};width:{agree_bw}%;transition:width 0.3s;'></div>"
        f"<div style='background:{BEAR};width:{conf_bw}%;'></div>"
        f"<div style='background:{BDR};flex:1;'></div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;"
        f"font-size:0.52rem;color:#444;margin-top:0.2rem;'>"
        f"<span style='color:{BULL};'>&#9650; {agree_bw}% agrees</span>"
        f"<span style='color:{BEAR};'>&#9660; {conf_bw}% conflicts</span>"
        f"</div></div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Per-engine rows ───────────────────────────────────────────────────────
    for key in ['ai_score', 'ml', 'historical', 'smc', 'structure']:
        if key not in verdicts:
            continue
        v        = verdicts[key]
        verdict  = v['verdict']
        strength = v.get('strength', 'none')
        if   verdict == 'agree':    v_icon, v_color, v_lbl = '&#10003;', BULL, 'AGREES'
        elif verdict == 'conflict': v_icon, v_color, v_lbl = '&#10007;', BEAR, 'CONFLICTS'
        else:                       v_icon, v_color, v_lbl = '&mdash;',  '#555', 'NEUTRAL'

        str_map  = {'strong': ('Strong',   v_color), 'weak': ('Moderate', NEUT), 'none': ('Flat', '#444')}
        str_lbl, str_col = str_map.get(strength, ('—', '#444'))

        st.markdown(
            f"<div style='background:{BG2};border:1px solid {BDR};"
            f"border-left:4px solid {v_color};border-radius:12px;"
            f"padding:0.9rem 1.2rem;margin-bottom:0.5rem;'>"

            f"<div style='display:flex;align-items:center;gap:0.9rem;'>"

            # Status bubble
            f"<div style='width:2.6rem;height:2.6rem;border-radius:50%;flex-shrink:0;"
            f"background:{v_color}20;border:2px solid {v_color};"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:1.1rem;font-weight:900;color:{v_color};'>{v_icon}</div>"

            # Engine info
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-size:0.86rem;font-weight:800;color:#fff;"
            f"margin-bottom:0.15rem;'>{v['label']}</div>"
            f"<div style='font-size:0.64rem;color:#666;white-space:nowrap;"
            f"overflow:hidden;text-overflow:ellipsis;margin-bottom:0.3rem;'>"
            f"{v.get('detail','—')}</div>"
            # Weight progress bar
            f"<div style='display:flex;align-items:center;gap:0.45rem;'>"
            f"<div style='font-size:0.5rem;color:#444;flex-shrink:0;'>Engine weight</div>"
            f"<div style='flex:1;background:{BDR};border-radius:999px;height:3px;'>"
            f"<div style='width:{v['weight']}%;height:100%;background:{v_color};"
            f"border-radius:999px;'></div></div>"
            f"<div style='font-size:0.5rem;color:#444;flex-shrink:0;'>{v['weight']}%</div>"
            f"</div>"
            f"</div>"

            # Signal + verdict badge
            f"<div style='text-align:right;flex-shrink:0;min-width:164px;'>"
            f"<div style='font-size:0.9rem;font-weight:800;"
            f"color:{v.get('signal_col','#fff')};margin-bottom:0.25rem;'>"
            f"{v.get('signal','—')}</div>"
            f"<div style='display:flex;gap:0.35rem;justify-content:flex-end;"
            f"align-items:center;flex-wrap:wrap;'>"
            f"<div style='background:{v_color}18;border:1.5px solid {v_color};"
            f"border-radius:7px;padding:0.13rem 0.75rem;"
            f"font-size:0.72rem;font-weight:900;color:{v_color};'>{v_lbl}</div>"
            f"<div style='font-size:0.6rem;color:{str_col};font-weight:700;'>{str_lbl}</div>"
            f"</div>"
            f"</div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='margin-top:1.5rem;padding:0.6rem 1rem;background:{BG2};"
        f"border:1px solid {BDR};border-radius:10px;font-size:0.6rem;color:#444;'>"
        f"For informational purposes only. Statistical patterns — not guaranteed outcomes. "
        f"Levels are ATR-derived estimates, not precise entry/exit points."
        f"</div>",
        unsafe_allow_html=True,
    )
'''

src = src[:idx_consensus] + NEW_TAIL
print("PATCH 2 OK — ENGINE CONSENSUS replaced + Smart Price Levels/Checklist/Risk removed")

with open('trade_validator_tab.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("DONE — trade_validator_tab.py written")
