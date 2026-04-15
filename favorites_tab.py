"""
favorites_tab.py
────────────────
All favorites feature logic in one place:
  - favorites_css(palette)      → CSS string (injected via app.py style block)
  - render_favorites_panel(palette) → renders the full saved-strategies panel
  - render_save_button(i, ka, kb, row, top_names) → ☆/★ button on combo cards
"""

from __future__ import annotations
import streamlit as st
from datetime import date as _today_date
from auth import upsert_favorite, delete_favorite


# ── CSS ───────────────────────────────────────────────────────────────────────

def favorites_css(palette: dict) -> str:
    """
    Returns the CSS block for the favorites panel.
    `palette` must contain: cp_bg, cp_border, cp_shadow, c_text, c_muted
    """
    cp_bg     = palette["cp_bg"]
    cp_border = palette["cp_border"]
    cp_shadow = palette["cp_shadow"]
    c_text    = palette["c_text"]
    c_muted   = palette["c_muted"]

    return f"""
        /* ── Favorites panel wrapper ── */
        .st-key-fav_panel_wrap {{
            background: {cp_bg} !important;
            border: 1px solid {cp_border} !important;
            border-radius: 24px !important;
            box-shadow: {cp_shadow} !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            padding: 1.1rem 1.4rem 1.3rem 1.4rem !important;
            box-sizing: border-box !important;
            margin-bottom: 0.7rem !important;
        }}
        .st-key-fav_panel_wrap > div,
        .st-key-fav_panel_wrap [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-fav_panel_wrap [data-testid="stVerticalBlock"] {{
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}
        /* close button */
        .st-key-fav_close_panel .stButton > button {{
            background: rgba(239,83,80,0.07) !important;
            border: 1px solid rgba(239,83,80,0.30) !important;
            border-radius: 20px !important;
            color: rgba(239,83,80,0.75) !important;
            height: 2rem !important;
            min-height: 2rem !important;
            font-size: 0.72rem !important;
            font-weight: 800 !important;
            padding: 0 1rem !important;
            letter-spacing: 0.3px !important;
            transition: all 0.15s ease !important;
        }}
        .st-key-fav_close_panel .stButton > button:hover {{
            background: rgba(239,83,80,0.16) !important;
            border-color: rgba(239,83,80,0.65) !important;
            color: #ef5350 !important;
            box-shadow: 0 0 10px rgba(239,83,80,0.20) !important;
        }}
        /* delete buttons */
        [class*="st-key-fav_del_"] .stButton > button {{
            background: rgba(239,83,80,0.05) !important;
            border: 1px solid rgba(239,83,80,0.20) !important;
            border-radius: 10px !important;
            color: rgba(239,83,80,0.55) !important;
            min-height: 6rem !important;
            height: 100% !important;
            font-size: 1rem !important;
            padding: 0 !important;
            transition: all 0.15s ease !important;
        }}
        [class*="st-key-fav_del_"] .stButton > button:hover {{
            background: rgba(239,83,80,0.14) !important;
            border-color: rgba(239,83,80,0.60) !important;
            color: #ef5350 !important;
            box-shadow: 0 0 12px rgba(239,83,80,0.20) !important;
        }}
        /* save strategy button (combo cards) */
        [class*="st-key-fav_save_"] .stButton > button {{
            background: rgba(244,114,182,0.06) !important;
            border: 1px solid rgba(244,114,182,0.22) !important;
            border-radius: 20px !important;
            color: rgba(244,114,182,0.80) !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            min-height: 1.9rem !important;
            padding: 0 1rem !important;
            transition: all 0.15s ease !important;
        }}
        [class*="st-key-fav_save_"] .stButton > button:hover {{
            background: rgba(244,114,182,0.15) !important;
            border-color: rgba(244,114,182,0.55) !important;
            color: #f472b6 !important;
            box-shadow: 0 0 10px rgba(244,114,182,0.25) !important;
        }}
        /* panel inner elements */
        .fav-hdr {{ display:flex; align-items:center; gap:0.55rem;
                    padding-bottom:0.75rem; margin-bottom:0.75rem;
                    border-bottom:1px solid {cp_border}; }}
        .fav-hdr-icon {{ font-size:1rem; }}
        .fav-hdr-title {{ font-size:0.84rem; font-weight:800; color:{c_text};
                          flex:1; letter-spacing:0.2px; }}
        .fav-hdr-count {{ background:rgba(244,114,182,0.12);
                          border:1px solid rgba(244,114,182,0.28);
                          color:#f472b6; font-size:0.65rem; font-weight:800;
                          border-radius:20px; padding:0.12rem 0.55rem; }}
        .fav-empty {{ display:flex; flex-direction:column; align-items:center;
                      padding:1.8rem 1rem; gap:0.5rem; }}
        .fav-empty-icon {{ font-size:2rem; opacity:0.2; }}
        .fav-empty-txt {{ font-size:0.75rem; color:{c_muted}; text-align:center;
                          font-weight:600; max-width:320px; line-height:1.6;
                          opacity:0.75; }}
        .fav-card {{
            background: rgba(255,255,255,0.022);
            border: 1px solid {cp_border};
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 0.1rem;
        }}
        .fav-card-top {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.75rem 1rem 0.6rem 1rem;
            border-bottom: 1px solid {cp_border};
            background: rgba(244,114,182,0.035);
            flex-wrap: wrap;
        }}
        .fav-sym {{
            background: rgba(244,114,182,0.12);
            border: 1px solid rgba(244,114,182,0.30);
            border-radius: 8px;
            padding: 0.22rem 0.65rem;
            font-size: 0.78rem; font-weight: 900;
            color: #f472b6; letter-spacing: 0.5px;
        }}
        .fav-sep {{ color:{c_muted}; opacity:0.35; font-weight:300; font-size:1rem; }}
        .fav-pill {{
            background: rgba(38,166,154,0.10);
            border: 1px solid rgba(38,166,154,0.25);
            border-radius: 6px; padding: 0.15rem 0.55rem;
            font-size: 0.69rem; font-weight: 800; color: #26A69A;
        }}
        .fav-plus {{ font-size:0.65rem; color:{c_muted}; font-weight:700; }}
        .fav-regime {{
            margin-left: auto;
            font-size: 0.6rem; font-weight: 800;
            text-transform: uppercase; letter-spacing: 0.6px;
            border-radius: 20px; padding: 0.15rem 0.6rem;
            border: 1px solid currentColor; opacity: 0.85;
        }}
        .fav-date {{
            font-size: 0.58rem; color: {c_muted}; opacity: 0.55;
            margin-left: 0.2rem; align-self: center;
        }}
        .fav-card-bot {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            padding: 0.65rem 1rem 0.7rem 1rem;
            gap: 0;
        }}
        .fav-si {{
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            padding: 0.15rem 0;
        }}
        .fav-si:not(:last-child) {{
            border-right: 1px solid {cp_border};
        }}
        .fsl {{
            font-size: 0.51rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.6px;
            color: {c_muted}; margin-bottom: 0.18rem; opacity: 0.75;
        }}
        .fsv {{
            font-size: 0.92rem; font-weight: 900;
            color: {c_text}; line-height: 1;
        }}
    """


# ── Panel renderer ────────────────────────────────────────────────────────────

def render_favorites_panel() -> None:
    """Renders the full Saved Strategies panel when toggled open."""
    if not st.session_state.get('show_favorites_panel', False):
        return

    favs      = st.session_state.get('favorites', [])
    _r_colors = {'TREND': '#4A9EFF', 'RANGE': '#FFC107', 'VOLATILE': '#FF6B6B'}

    # split by type
    _ind_favs   = [f for f in favs if f.get('save_type') == 'indicator']
    _combo_favs = [f for f in favs if f.get('save_type') == 'combo']
    _strat_favs = [f for f in favs if f.get('save_type') not in ('indicator', 'combo')]

    with st.container(key="fav_panel_wrap"):
        # ── header row ────────────────────────────────────────────────
        hc1, hc2 = st.columns([9, 1])
        with hc1:
            count_badge = f"<span class='fav-hdr-count'>{len(favs)}</span>" if favs else ""
            st.markdown(
                f"<div class='fav-hdr'><span class='fav-hdr-icon'>★</span>"
                f"<span class='fav-hdr-title'>Saved Analysis</span>{count_badge}</div>",
                unsafe_allow_html=True)
        with hc2:
            with st.container(key="fav_close_panel"):
                if st.button("✕  Close", key="fav_close_btn", width="stretch"):
                    st.session_state.show_favorites_panel = False
                    st.rerun()

        # ── empty state ───────────────────────────────────────────────
        if not favs:
            st.markdown(
                "<div class='fav-empty'><div class='fav-empty-icon'>☆</div>"
                "<div class='fav-empty-txt'>Nothing saved yet.<br>"
                "Run a <b>Signal Analysis</b> and tap <b>☆ Save</b> on any indicator "
                "or combination card. Also works on <b>Tadawul AI</b> result pages.</div></div>",
                unsafe_allow_html=True)
            return

        # ── helper: render one fav card + delete button ───────────────
        def _fav_card(f_idx: int, fav: dict, label: str, accent: str,
                      extra_pills: list = None):
            _regime = fav.get('best_regime') or ''
            _bc     = _r_colors.get(_regime, '#9e9e9e')
            _wr     = fav.get('win_rate', 0)
            _wr_c   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
            _ag     = fav.get('avg_gain', 0)
            _al     = fav.get('avg_loss', 0)
            _ag_c   = '#26A69A' if _ag >= 1 else ('#FFC107' if _ag > 0 else '#ef5350')
            _sym    = fav.get('symbol', '').replace('.SR', '')
            _disp   = fav.get('pair_display', fav.get('pair', ''))
            _sn     = fav.get('stock_name', '')
            _exp_c  = '#26A69A' if fav.get('expectancy', 0) > 0 else '#ef5350'

            # pills row from pair_display (split by +)
            _parts = [p.strip() for p in _disp.split('+')]
            _pills_html = ''
            for pi, pn in enumerate(_parts):
                _pills_html += f"<span class='fav-pill'>{pn}</span>"
                if pi < len(_parts) - 1:
                    _pills_html += "<span class='fav-plus'>+</span>"

            # settings row (risk/reward + period) for indicators & combos
            _settings_html = ''
            _rv = fav.get('risk_val'); _rw = fav.get('reward_val')
            _pl = fav.get('period_label', '')
            if _rv and _rw:
                _settings_html = (
                    f"<span style='font-size:0.58rem;color:#9e9e9e;border:1px solid #404040;"
                    f"border-radius:4px;padding:0.1rem 0.4rem;'>"
                    f"R:R {_rv}:{_rw}</span>"
                    f"<span style='font-size:0.58rem;color:#9e9e9e;border:1px solid #404040;"
                    f"border-radius:4px;padding:0.1rem 0.4rem;margin-left:0.2rem;'>"
                    f"{_pl.split('(')[0].strip() if _pl else ''}</span>"
                )

            _card = (
                "<div class='fav-card' style='border-left:3px solid "
                + accent + ";'>"
                "<div class='fav-card-top'>"
                f"<span class='fav-sym'>{_sym}</span>"
                f"<span style='font-size:0.58rem;font-weight:700;color:{accent};"
                f"background:{accent}18;border:1px solid {accent}44;border-radius:4px;"
                f"padding:0.1rem 0.45rem;'>{label}</span>"
                "<span class='fav-sep'>|</span>"
                + _pills_html
                + (_settings_html)
                + (f"<span class='fav-regime' style='color:{_bc};border-color:{_bc};'>{_regime}</span>" if _regime else '')
                + f"<span class='fav-date'>{fav.get('saved_at', '')}</span>"
                "</div>"
                "<div class='fav-card-bot'>"
                f"<div class='fav-si'><span class='fsl'>Win Rate</span><span class='fsv' style='color:{_wr_c}'>{_wr:.1f}%</span></div>"
                f"<div class='fav-si'><span class='fsl'>Avg Gain</span><span class='fsv' style='color:{_ag_c}'>+{_ag:.2f}%</span></div>"
                f"<div class='fav-si'><span class='fsl'>Expectancy</span><span class='fsv' style='color:{_exp_c}'>{fav.get('expectancy',0):+.2f}%</span></div>"
                f"<div class='fav-si'><span class='fsl'>Signals</span><span class='fsv'>{fav.get('signals', 0)}</span></div>"
                "</div>"
                "</div>"
            )
            _ec1, _ec2 = st.columns([12, 1])
            with _ec1:
                st.markdown(_card, unsafe_allow_html=True)
            with _ec2:
                if st.button("✕", key=f"fav_del_{f_idx}", width="stretch"):
                    _user = st.session_state.get('auth_username', '')
                    delete_favorite(_user, fav.get('id', ''))
                    st.session_state.favorites = [x for x in favs if x.get('id') != fav.get('id')]
                    st.rerun()

        _global_idx = 0

        # ── Section: Saved Indicators ─────────────────────────────────
        if _ind_favs:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.5rem;"
                "margin:0.6rem 0 0.5rem 0;'>"
                "<span style='width:3px;height:0.9rem;background:#4caf50;border-radius:2px;"
                "flex-shrink:0;display:inline-block;'></span>"
                "<span style='font-size:0.72rem;font-weight:800;color:#4caf50;"
                "text-transform:uppercase;letter-spacing:0.5px;'>Saved Indicators</span>"
                f"<span style='font-size:0.58rem;color:#757575;'>({len(_ind_favs)})</span>"
                "</div>",
                unsafe_allow_html=True)
            for _fav in _ind_favs:
                _fav_card(_global_idx, _fav, "Indicator", "#4caf50")
                _global_idx += 1

        # ── Section: Saved Combinations ───────────────────────────────
        if _combo_favs:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.5rem;"
                "margin:0.9rem 0 0.5rem 0;'>"
                "<span style='width:3px;height:0.9rem;background:#FFD700;border-radius:2px;"
                "flex-shrink:0;display:inline-block;'></span>"
                "<span style='font-size:0.72rem;font-weight:800;color:#FFD700;"
                "text-transform:uppercase;letter-spacing:0.5px;'>Saved Combinations</span>"
                f"<span style='font-size:0.58rem;color:#757575;'>({len(_combo_favs)})</span>"
                "</div>",
                unsafe_allow_html=True)
            for _fav in _combo_favs:
                _fav_card(_global_idx, _fav, "Combo", "#FFD700")
                _global_idx += 1

        # ── Section: Saved Strategies (Tadawul AI) ────────────────────
        if _strat_favs:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.5rem;"
                "margin:0.9rem 0 0.5rem 0;'>"
                "<span style='width:3px;height:0.9rem;background:#f472b6;border-radius:2px;"
                "flex-shrink:0;display:inline-block;'></span>"
                "<span style='font-size:0.72rem;font-weight:800;color:#f472b6;"
                "text-transform:uppercase;letter-spacing:0.5px;'>Saved Strategies</span>"
                f"<span style='font-size:0.58rem;color:#757575;'>({len(_strat_favs)})</span>"
                "</div>",
                unsafe_allow_html=True)
            for _fav in _strat_favs:
                _parts  = _fav.get('pair', '').split(' + ')
                _pill_a = _parts[0] if _parts else ''
                _pill_b = _parts[1] if len(_parts) > 1 else ''
                _regime = _fav.get('best_regime') or ''
                _bc     = _r_colors.get(_regime, '#9e9e9e')
                _wr     = _fav.get('win_rate', 0)
                _wr_c   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
                _ag     = _fav.get('avg_gain', 0)
                _al     = _fav.get('avg_loss', 0)
                _ag_c   = '#26A69A' if _ag >= 1 else ('#FFC107' if _ag > 0 else '#ef5350')
                _sym    = _fav.get('symbol', '').replace('.SR', '')

                _card = (
                    "<div class='fav-card' style='border-left:3px solid #f472b6;'>"
                    "<div class='fav-card-top'>"
                    f"<span class='fav-sym'>{_sym}</span>"
                    "<span class='fav-sep'>|</span>"
                    f"<span class='fav-pill'>{_pill_a}</span>"
                    "<span class='fav-plus'>+</span>"
                    f"<span class='fav-pill'>{_pill_b}</span>"
                    + (f"<span class='fav-regime' style='color:{_bc};border-color:{_bc};'>{_regime}</span>" if _regime else '')
                    + f"<span class='fav-date'>{_fav.get('saved_at', '')}</span>"
                    "</div>"
                    "<div class='fav-card-bot'>"
                    f"<div class='fav-si'><span class='fsl'>Win Rate</span><span class='fsv' style='color:{_wr_c}'>{_wr:.1f}%</span></div>"
                    f"<div class='fav-si'><span class='fsl'>Avg Gain</span><span class='fsv' style='color:{_ag_c}'>+{_ag:.2f}%</span></div>"
                    f"<div class='fav-si'><span class='fsl'>Avg Loss</span><span class='fsv' style='color:#ef5350'>{_al:.2f}%</span></div>"
                    f"<div class='fav-si'><span class='fsl'>Signals</span><span class='fsv'>{_fav.get('signals', 0)}</span></div>"
                    "</div>"
                    "</div>"
                )
                _ec1, _ec2 = st.columns([12, 1])
                with _ec1:
                    st.markdown(_card, unsafe_allow_html=True)
                with _ec2:
                    if st.button("✕", key=f"fav_del_{_global_idx}", width="stretch"):
                        _user = st.session_state.get('auth_username', '')
                        delete_favorite(_user, _fav.get('id', ''))
                        st.session_state.favorites = [x for x in favs if x.get('id') != _fav.get('id')]
                        st.rerun()
                _global_idx += 1


# ── Save button (combo cards) ─────────────────────────────────────────────────

def render_save_button(i: int, ka: str, kb: str, row: dict, top_names: dict) -> None:
    """
    Renders the ☆/★ Save Strategy toggle button below a combination card.
    Call this right after st.markdown(card, ...) inside the pair_data loop.
    """
    _sym      = st.session_state.get('analyzed_symbol', '')
    _fav_id   = f"{_sym}__{ka}__{kb}"
    _cur_favs = st.session_state.get('favorites', [])
    _is_saved = any(f.get('id') == _fav_id for f in _cur_favs)
    _btn_lbl  = "★  Saved — click to remove" if _is_saved else "☆  Save Strategy"

    _sv_col, _ = st.columns([2, 8])
    with _sv_col:
        if st.button(_btn_lbl, key=f"fav_save_{i}_{ka}_{kb}", width="stretch"):
            _user = st.session_state.get('auth_username', '')
            if _is_saved:
                delete_favorite(_user, _fav_id)
                st.session_state.favorites = [f for f in _cur_favs if f.get('id') != _fav_id]
            else:
                if 'favorites' not in st.session_state:
                    st.session_state.favorites = []
                _entry_price = None
                _df = st.session_state.get('df')
                if _df is not None:
                    try:
                        _entry_price = float(_df['Close'].iloc[-1])
                    except Exception:
                        pass
                _new_fav = {
                    'id':            _fav_id,
                    'symbol':        _sym,
                    'stock_name':    st.session_state.get('analyzed_stock_name', ''),
                    'pair':          f"{ka} + {kb}",
                    'pair_display':  f"{top_names.get(ka, ka)} + {top_names.get(kb, kb)}",
                    'win_rate':      row['win_rate'],
                    'profit_factor': row['profit_factor'],
                    'expectancy':    row['expectancy'],
                    'avg_gain':      row['avg_gain'],
                    'avg_loss':      row['avg_loss'],
                    'signals':       row['total'],
                    'best_regime':   row['best_regime'],
                    'saved_at':      _today_date.today().strftime('%b %d, %Y'),
                    'entry_price':   _entry_price,
                    'save_type':     'strategy',
                }
                upsert_favorite(_user, _new_fav)
                st.session_state.favorites.append(_new_fav)
            st.rerun()


# ── Save button: single indicator ─────────────────────────────────────────────

def render_save_indicator_button(idx: int, ind: dict, risk_val: int,
                                  reward_val: int, period_label: str) -> None:
    """☆/★ save button for a single indicator card."""
    _sym         = st.session_state.get('analyzed_symbol', '')
    _period_key  = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _fav_id      = f"ind__{_sym}__{ind['key']}__r{risk_val}x{reward_val}__{_period_key}"
    _cur_favs    = st.session_state.get('favorites', [])
    _is_saved    = any(f.get('id') == _fav_id for f in _cur_favs)
    _btn_lbl     = "★  Saved — click to remove" if _is_saved else f"☆  Save  {ind['name']}"

    if st.button(_btn_lbl, key=f"fav_save_ind_{idx}_{ind['key']}", use_container_width=True):
        _user = st.session_state.get('auth_username', '')
        if _is_saved:
            delete_favorite(_user, _fav_id)
            st.session_state.favorites = [f for f in _cur_favs if f.get('id') != _fav_id]
        else:
            if 'favorites' not in st.session_state:
                st.session_state.favorites = []
            _new_fav = {
                'id':            _fav_id,
                'symbol':        _sym,
                'stock_name':    st.session_state.get('analyzed_stock_name', ''),
                'pair':          ind['key'],
                'pair_display':  ind['name'],
                'win_rate':      ind['win_rate'],
                'profit_factor': ind['profit_factor'],
                'expectancy':    ind['expectancy'],
                'avg_gain':      ind['avg_gain'],
                'avg_loss':      ind['avg_loss'],
                'signals':       ind['total'],
                'best_regime':   ind.get('best_regime', ''),
                'saved_at':      _today_date.today().strftime('%b %d, %Y'),
                'entry_price':   None,
                'save_type':     'indicator',
                'risk_val':      risk_val,
                'reward_val':    reward_val,
                'period_label':  period_label,
                'combo_indicators': ind['name'],
            }
            upsert_favorite(_user, _new_fav)
            st.session_state.favorites.append(_new_fav)
        st.rerun()


# ── Save button: N-way combo ─────────────────────────────────────────────────

def render_save_combo_button(idx: int, row: dict, all_names: dict,
                              risk_val: int, reward_val: int, period_label: str) -> None:
    """☆/★ save button for a combination card in the Signal Analysis tab."""
    _sym         = st.session_state.get('analyzed_symbol', '')
    _key_str     = '__'.join(sorted(row['indicators']))
    _period_key  = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _fav_id      = f"combo__{_sym}__{_key_str}__r{risk_val}x{reward_val}__{_period_key}"
    _cur_favs    = st.session_state.get('favorites', [])
    _is_saved = any(f.get('id') == _fav_id for f in _cur_favs)
    _ind_names = [all_names.get(k, k) for k in row['indicators']]
    _display   = ' + '.join(_ind_names)
    _btn_lbl   = "★  Saved — click to remove" if _is_saved else f"☆  Save  {row['size']}-Way Combo"

    if st.button(_btn_lbl, key=f"fav_save_combo_{idx}_{_key_str[:30]}", use_container_width=True):
        _user = st.session_state.get('auth_username', '')
        if _is_saved:
            delete_favorite(_user, _fav_id)
            st.session_state.favorites = [f for f in _cur_favs if f.get('id') != _fav_id]
        else:
            if 'favorites' not in st.session_state:
                st.session_state.favorites = []
            _new_fav = {
                'id':               _fav_id,
                'symbol':           _sym,
                'stock_name':       st.session_state.get('analyzed_stock_name', ''),
                'pair':             ' + '.join(row['indicators']),
                'pair_display':     _display,
                'win_rate':         row['win_rate'],
                'profit_factor':    row['profit_factor'],
                'expectancy':       row['expectancy'],
                'avg_gain':         row['avg_gain'],
                'avg_loss':         row['avg_loss'],
                'signals':          row['total'],
                'best_regime':      row.get('best_regime', ''),
                'saved_at':         _today_date.today().strftime('%b %d, %Y'),
                'entry_price':      None,
                'save_type':        'combo',
                'risk_val':         risk_val,
                'reward_val':       reward_val,
                'period_label':     period_label,
                'combo_indicators': _display,
            }
            upsert_favorite(_user, _new_fav)
            st.session_state.favorites.append(_new_fav)
        st.rerun()


# ── Full-page Saved Analysis view ─────────────────────────────────────────────

def render_saved_page() -> None:
    """Renders the full Saved Analysis page (replaces main content)."""
    favs      = st.session_state.get('favorites', [])
    _r_colors = {'TREND': '#4A9EFF', 'RANGE': '#FFC107', 'VOLATILE': '#FF6B6B'}

    _ind_favs   = [f for f in favs if f.get('save_type') == 'indicator']
    _combo_favs = [f for f in favs if f.get('save_type') == 'combo']
    _strat_favs = [f for f in favs if f.get('save_type') not in ('indicator', 'combo')]

    # ── page CSS ─────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .sp-back-btn .stButton > button {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid #404040 !important;
        border-radius: 8px !important; color: #9e9e9e !important;
        font-size: 0.78rem !important; font-weight: 600 !important;
        min-height: 2.2rem !important; padding: 0 1rem !important;
    }
    .sp-back-btn .stButton > button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: #606060 !important; color: #ffffff !important;
    }
    .sp-filter-row .stButton > button {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid #303030 !important; border-radius: 20px !important;
        color: #9e9e9e !important; font-size: 0.72rem !important;
        font-weight: 600 !important; min-height: 2rem !important;
        padding: 0 0.9rem !important; white-space: nowrap !important;
    }
    .sp-filter-row .stButton > button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: #606060 !important; color: #fff !important;
    }
    [class*="st-key-sp_f_active"] .stButton > button {
        background: rgba(38,166,154,0.12) !important;
        border-color: rgba(38,166,154,0.45) !important;
        color: #26A69A !important; font-weight: 700 !important;
    }
    [class*="st-key-sp_del_"] .stButton > button {
        background: transparent !important;
        border: 1px solid rgba(239,83,80,0.18) !important;
        border-radius: 8px !important; color: rgba(239,83,80,0.45) !important;
        height: 100% !important; min-height: 5.5rem !important;
        font-size: 0.9rem !important; padding: 0 !important;
    }
    [class*="st-key-sp_del_"] .stButton > button:hover {
        background: rgba(239,83,80,0.10) !important;
        border-color: rgba(239,83,80,0.55) !important; color: #ef5350 !important;
    }
    .sp-hero { display:grid; grid-template-columns:repeat(4,1fr);
               gap:0.8rem; margin-bottom:1.5rem; }
    .sp-hero-card { background:#212121; border:1px solid #303030;
                    border-radius:12px; padding:1rem 1.2rem;
                    display:flex; flex-direction:column; gap:0.2rem; }
    .sp-hero-val { font-size:2rem; font-weight:900; line-height:1; letter-spacing:-1px; }
    .sp-hero-lbl { font-size:0.65rem; color:#757575; font-weight:600;
                   text-transform:uppercase; letter-spacing:0.5px; }
    .sp-section-hdr { display:flex; align-items:center; gap:0.5rem;
                      margin:1.2rem 0 0.65rem 0; }
    .sp-section-bar { width:3px; height:1rem; border-radius:2px; flex-shrink:0; }
    .sp-section-title { font-size:0.78rem; font-weight:800;
                        text-transform:uppercase; letter-spacing:0.5px; }
    .sp-section-cnt { font-size:0.6rem; color:#757575; }
    .sp-card { background:#212121; border:1px solid #303030;
               border-radius:12px; overflow:hidden; margin-bottom:0.6rem; }
    .sp-card-head { display:flex; align-items:center; gap:0.65rem;
        padding:0.9rem 1.2rem 0.75rem 1.2rem; border-bottom:1px solid #2a2a2a;
        flex-wrap:wrap; }
    .sp-sym { background:rgba(38,166,154,0.10); border:1px solid rgba(38,166,154,0.25);
              border-radius:7px; padding:0.2rem 0.65rem;
              font-size:0.92rem; font-weight:900; color:#26A69A; letter-spacing:0.5px; }
    .sp-type-badge { font-size:0.6rem; font-weight:800; text-transform:uppercase;
                     letter-spacing:0.5px; border-radius:20px; padding:0.18rem 0.7rem;
                     border:1px solid currentColor; }
    .sp-tag { font-size:0.58rem; font-weight:700; border-radius:5px;
              padding:0.15rem 0.5rem; border:1px solid currentColor; white-space:nowrap; }
    .sp-date { font-size:0.57rem; color:#616161; margin-left:auto; }
    .sp-stats { display:grid; grid-template-columns:repeat(6,1fr);
               border-top:1px solid #2a2a2a; }
    .sp-stat { padding:0.7rem 0.5rem 0.65rem 0.5rem; text-align:center;
               border-right:1px solid #2a2a2a; }
    .sp-stat:last-child { border-right:none; }
    .sp-stat-lbl { font-size:0.51rem; font-weight:700; text-transform:uppercase;
                   letter-spacing:0.6px; color:#616161; margin-bottom:0.22rem; }
    .sp-stat-val { font-size:0.95rem; font-weight:900; line-height:1; }
    .sp-empty { display:flex; flex-direction:column; align-items:center;
                gap:0.6rem; padding:4rem 2rem; text-align:center; }
    .sp-empty-icon { font-size:2.5rem; opacity:0.15; }
    .sp-empty-title { font-size:0.95rem; font-weight:700; color:#9e9e9e; }
    .sp-empty-sub { font-size:0.73rem; color:#616161; max-width:320px; line-height:1.7; }
    </style>
    """, unsafe_allow_html=True)

    # ── header row ────────────────────────────────────────────────────────
    _hcols = st.columns([1, 7, 2])
    with _hcols[0]:
        with st.container(key="sp_back_btn"):
            if st.button("← Back", key="sp_back", width="stretch"):
                st.session_state.show_saved_page = False
                st.rerun()
    with _hcols[1]:
        _total = len(favs)
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:0.6rem;padding-top:0.1rem;'>"
            f"<span style='font-size:1.1rem;font-weight:900;color:#fff;'>Saved Analysis</span>"
            f"<span style='font-size:0.68rem;color:#9e9e9e;font-weight:600;'>"
            f"{_total} item{'s' if _total != 1 else ''} saved</span>"
            f"</div>",
            unsafe_allow_html=True)
    with _hcols[2]:
        _sort_by = st.selectbox(
            "Sort", ["Win Rate ↓", "Profit Factor ↓", "Expectancy ↓", "Signals ↓", "Date Saved ↓"],
            index=0, key="sp_sort", label_visibility="collapsed")

    st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

    # ── hero stats ─────────────────────────────────────────────────────────
    st.markdown(
        f"<div class='sp-hero'>"
        f"<div class='sp-hero-card' style='border-top:3px solid #26A69A;'>"
        f"<div class='sp-hero-val' style='color:#26A69A;'>{_total}</div>"
        f"<div class='sp-hero-lbl'>Total Saved</div></div>"
        f"<div class='sp-hero-card' style='border-top:3px solid #4caf50;'>"
        f"<div class='sp-hero-val' style='color:#4caf50;'>{len(_ind_favs)}</div>"
        f"<div class='sp-hero-lbl'>Indicators</div></div>"
        f"<div class='sp-hero-card' style='border-top:3px solid #FFD700;'>"
        f"<div class='sp-hero-val' style='color:#FFD700;'>{len(_combo_favs)}</div>"
        f"<div class='sp-hero-lbl'>Combinations</div></div>"
        f"<div class='sp-hero-card' style='border-top:3px solid #f472b6;'>"
        f"<div class='sp-hero-val' style='color:#f472b6;'>{len(_strat_favs)}</div>"
        f"<div class='sp-hero-lbl'>Strategies</div></div>"
        f"</div>",
        unsafe_allow_html=True)

    # ── filter tabs ────────────────────────────────────────────────────────
    if 'sp_filter' not in st.session_state:
        st.session_state.sp_filter = 'all'
    _cur_filter = st.session_state.sp_filter
    _filter_opts = [
        ('all',       f'All  ({_total})'),
        ('indicator', f'Indicators  ({len(_ind_favs)})'),
        ('combo',     f'Combinations  ({len(_combo_favs)})'),
        ('strategy',  f'Strategies  ({len(_strat_favs)})'),
    ]
    with st.container(key="sp_filter_row"):
        _fcols = st.columns(len(_filter_opts))
        for _fi, (_fk, _fl) in enumerate(_filter_opts):
            _active_key = 'active' if _cur_filter == _fk else 'btn'
            with st.container(key=f"sp_f_{_active_key}_{_fi}"):
                with _fcols[_fi]:
                    if st.button(_fl, key=f"sp_flt_{_fk}", width="stretch"):
                        st.session_state.sp_filter = _fk
                        st.rerun()

    st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)

    # ── empty state ────────────────────────────────────────────────────────
    if not favs:
        st.markdown(
            "<div class='sp-empty'><div class='sp-empty-icon'>☆</div>"
            "<div class='sp-empty-title'>Nothing saved yet</div>"
            "<div class='sp-empty-sub'>Run a Signal Analysis and tap <b>☆ Save</b> on any "
            "indicator or combination card. Tadawul AI strategies also save here.</div>"
            "</div>",
            unsafe_allow_html=True)
        return

    # ── sort helper ────────────────────────────────────────────────────────
    def _sort_favs(lst):
        if _sort_by.startswith('Win Rate'):
            return sorted(lst, key=lambda x: x.get('win_rate', 0), reverse=True)
        if _sort_by.startswith('Profit Factor'):
            return sorted(lst, key=lambda x: x.get('profit_factor', 0), reverse=True)
        if _sort_by.startswith('Expectancy'):
            return sorted(lst, key=lambda x: x.get('expectancy', 0), reverse=True)
        if _sort_by.startswith('Signals'):
            return sorted(lst, key=lambda x: x.get('signals', 0), reverse=True)
        return list(reversed(lst))

    # ── card renderer ──────────────────────────────────────────────────────
    def _sp_card(f_idx: int, fav: dict, accent: str, type_label: str, type_color: str):
        _sym   = fav.get('symbol', '').replace('.SR', '')
        _disp  = fav.get('pair_display', fav.get('pair', ''))
        _regime = fav.get('best_regime') or ''
        _rc    = _r_colors.get(_regime, '#9e9e9e')
        _wr    = fav.get('win_rate', 0)
        _wr_c  = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
        _pf    = fav.get('profit_factor', 0)
        _pf_c  = '#26A69A' if _pf >= 1.5 else ('#FFC107' if _pf >= 1 else '#ef5350')
        _ea    = fav.get('expectancy', 0)
        _ea_c  = '#26A69A' if _ea > 0 else '#ef5350'
        _ag    = fav.get('avg_gain', 0)
        _ag_c  = '#26A69A' if _ag > 0 else '#ef5350'
        _al    = fav.get('avg_loss', 0)
        _sig   = fav.get('signals', 0)
        _rv    = fav.get('risk_val')
        _rw    = fav.get('reward_val')
        _pl    = fav.get('period_label', '')
        _pl_s  = _pl.split('(')[0].strip() if _pl else ''
        _date  = fav.get('saved_at', '')

        _parts = [p.strip() for p in _disp.split('+')]
        _pills = ''
        for _pi, _pn in enumerate(_parts):
            _pills += (
                f"<span style='background:{accent}14;border:1px solid {accent}33;"
                f"border-radius:5px;padding:0.18rem 0.55rem;"
                f"font-size:0.75rem;font-weight:800;color:{accent};'>{_pn}</span>"
            )
            if _pi < len(_parts) - 1:
                _pills += f"<span style='font-size:0.7rem;color:#616161;padding:0 0.1rem;'>+</span>"

        _rr_html = (
            f"<span class='sp-tag' style='color:#64b5f6;border-color:rgba(100,181,246,0.35);"
            f"background:rgba(100,181,246,0.07);'>R:R {_rv}:{_rw}</span>"
        ) if _rv and _rw else ''

        _pd_html = (
            f"<span class='sp-tag' style='color:#ce93d8;border-color:rgba(206,147,216,0.35);"
            f"background:rgba(206,147,216,0.07);'>{_pl_s}</span>"
        ) if _pl_s else ''

        _rg_html = (
            f"<span class='sp-tag' style='color:{_rc};border-color:{_rc}44;"
            f"background:{_rc}0D;'>{_regime}</span>"
        ) if _regime else ''

        _html = (
            f"<div class='sp-card' style='border-left:3px solid {accent};'>"
            f"<div class='sp-card-head'>"
            f"<span class='sp-sym'>{_sym}</span>"
            f"<span class='sp-type-badge' style='color:{type_color};border-color:{type_color}44;"
            f"background:{type_color}0D;'>{type_label}</span>"
            f"<div style='flex:1;min-width:0;display:flex;flex-wrap:wrap;align-items:center;gap:0.3rem;'>"
            + _pills + f"</div>"
            + _rr_html + _pd_html + _rg_html
            + f"<span class='sp-date'>{_date}</span>"
            f"</div>"
            f"<div class='sp-stats'>"
            f"<div class='sp-stat' style='border-top:2px solid {_wr_c};'>"
            f"<div class='sp-stat-lbl'>Win Rate</div>"
            f"<div class='sp-stat-val' style='color:{_wr_c};'>{_wr:.1f}%</div></div>"
            f"<div class='sp-stat' style='border-top:2px solid {_pf_c};'>"
            f"<div class='sp-stat-lbl'>Profit Factor</div>"
            f"<div class='sp-stat-val' style='color:{_pf_c};'>{_pf:.2f}</div></div>"
            f"<div class='sp-stat' style='border-top:2px solid {_ea_c};'>"
            f"<div class='sp-stat-lbl'>Expectancy</div>"
            f"<div class='sp-stat-val' style='color:{_ea_c};'>{_ea:+.2f}%</div></div>"
            f"<div class='sp-stat' style='border-top:2px solid {_ag_c};'>"
            f"<div class='sp-stat-lbl'>Avg Gain</div>"
            f"<div class='sp-stat-val' style='color:{_ag_c};'>+{_ag:.2f}%</div></div>"
            f"<div class='sp-stat' style='border-top:2px solid #ef5350;'>"
            f"<div class='sp-stat-lbl'>Avg Loss</div>"
            f"<div class='sp-stat-val' style='color:#ef5350;'>{_al:.2f}%</div></div>"
            f"<div class='sp-stat' style='border-top:2px solid #616161;'>"
            f"<div class='sp-stat-lbl'>Signals</div>"
            f"<div class='sp-stat-val' style='color:#9e9e9e;'>{_sig}</div></div>"
            f"</div></div>"
        )
        _cc1, _cc2 = st.columns([13, 1])
        with _cc1:
            st.markdown(_html, unsafe_allow_html=True)
        with _cc2:
            if st.button("✕", key=f"sp_del_{f_idx}", width="stretch"):
                _user = st.session_state.get('auth_username', '')
                delete_favorite(_user, fav.get('id', ''))
                st.session_state.favorites = [x for x in favs if x.get('id') != fav.get('id')]
                st.rerun()

    _global_idx = 0

    def _section(title, color, fav_list, type_label, type_color):
        nonlocal _global_idx
        if not fav_list:
            return
        st.markdown(
            f"<div class='sp-section-hdr'>"
            f"<div class='sp-section-bar' style='background:{color};'></div>"
            f"<span class='sp-section-title' style='color:{color};'>{title}</span>"
            f"<span class='sp-section-cnt'>({len(fav_list)})</span>"
            f"</div>",
            unsafe_allow_html=True)
        for _fav in _sort_favs(fav_list):
            _sp_card(_global_idx, _fav, color, type_label, type_color)
            _global_idx += 1

    _active = st.session_state.get('sp_filter', 'all')
    if _active in ('all', 'indicator'):
        _section("Saved Indicators", "#4caf50", _ind_favs, "Indicator", "#4caf50")
    if _active in ('all', 'combo'):
        _section("Saved Combinations", "#FFD700", _combo_favs, "Combo", "#FFD700")
    if _active in ('all', 'strategy'):
        _section("Saved Strategies", "#f472b6", _strat_favs, "Strategy", "#f472b6")
