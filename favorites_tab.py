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
            _sw = fav.get('signal_window')
            if fav.get('save_type') == 'combo' and _sw:
                _sw_i = int(_sw)
                _sw_lbl = 'Same bar' if _sw_i <= 1 else f'Sync {_sw_i} bars'
                _settings_html += (
                    f"<span style='font-size:0.58rem;color:#9e9e9e;border:1px solid #404040;"
                    f"border-radius:4px;padding:0.1rem 0.4rem;margin-left:0.2rem;'>"
                    f"{_sw_lbl}</span>"
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


# ── Internal helper: toggle a favorite in session_state + DB ─────────────────

def _toggle_favorite(fav_id: str, new_fav: dict | None) -> None:
    """
    Save or remove a favorite.
    If new_fav is None  → remove.
    If new_fav is dict  → add.
    Raises on error so callers can show a toast.
    """
    _user = st.session_state.get('auth_username', '')
    if not _user:
        raise RuntimeError("Not logged in")
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    _cur  = st.session_state.favorites
    _exists = any(f.get('id') == fav_id for f in _cur)

    if _exists:
        delete_favorite(_user, fav_id)
        st.session_state.favorites = [f for f in _cur if f.get('id') != fav_id]
    elif new_fav is not None:
        upsert_favorite(_user, new_fav)
        st.session_state.favorites = _cur + [new_fav]


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

    _sv_col, _ = st.columns([2, 8])
    with _sv_col:
        st.button(
            _btn_lbl,
            key=f"fav_save_{i}_{ka}_{kb}",
            width="stretch",
            on_click=_toggle_favorite,
            args=(_fav_id, None if _is_saved else _new_fav),
        )


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

    st.button(
        _btn_lbl,
        key=f"fav_save_ind_{idx}_{ind['key']}",
        width="stretch",
        on_click=_toggle_favorite,
        args=(_fav_id, None if _is_saved else _new_fav),
    )


# ── Save button: N-way combo ─────────────────────────────────────────────────

def render_save_combo_button(idx: int, row: dict, all_names: dict,
                              risk_val: int, reward_val: int, period_label: str,
                              signal_window: int = 1,
                              regime_tag: str | None = None,
                              button_label: str | None = None) -> None:
    """☆/★ save button for a combination card in the Signal Analysis tab."""
    _sym         = st.session_state.get('analyzed_symbol', '')
    _key_str     = '__'.join(sorted(row['indicators']))
    _period_key  = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _regime_tag  = (regime_tag or '').strip().upper()
    _regime_key  = f"__reg{_regime_tag}" if _regime_tag else ""
    _window_key  = f"__w{int(signal_window)}"
    _fav_id      = f"combo__{_sym}__{_key_str}__r{risk_val}x{reward_val}__{_period_key}{_window_key}{_regime_key}"
    _cur_favs    = st.session_state.get('favorites', [])
    _is_saved    = any(f.get('id') == _fav_id for f in _cur_favs)
    _ind_names   = [all_names.get(k, k) for k in row['indicators']]
    _display     = ' + '.join(_ind_names)
    _btn_lbl     = "★  Saved — click to remove" if _is_saved else (button_label or f"☆  Save  {row['size']}-Way Combo")

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
        'best_regime':      _regime_tag or row.get('best_regime', ''),
        'saved_at':         _today_date.today().strftime('%b %d, %Y'),
        'entry_price':      None,
        'save_type':        'combo',
        'risk_val':         risk_val,
        'reward_val':       reward_val,
        'period_label':     period_label,
        'combo_indicators': _display,
        'signal_window':    int(signal_window),
    }

    st.button(
        _btn_lbl,
        key=f"fav_save_combo_{idx}_{_key_str[:30]}",
        width="stretch",
        on_click=_toggle_favorite,
        args=(_fav_id, None if _is_saved else _new_fav),
    )


# ── Full-page Saved Analysis view ─────────────────────────────────────────────

def render_saved_page() -> None:
    """Renders the full Saved Analysis page (replaces main content)."""
    favs      = st.session_state.get('favorites', [])
    _r_colors = {'TREND': '#4A9EFF', 'RANGE': '#FFC107', 'VOLATILE': '#FF6B6B'}

    # Three categories: Indicators, Combinations, Regime Champions
    _ind_favs   = [f for f in favs if f.get('save_type') == 'indicator']
    _rc_favs    = [f for f in favs if f.get('save_type') == 'regime_champion']
    _combo_favs = [f for f in favs if f.get('save_type') not in ('indicator', 'regime_champion')]

    # ── page CSS ─────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── page wrapper ─────────────────────────────────────────────── */
    .sv-page { max-width: 960px; margin: 0 auto; }

    /* ── back button ──────────────────────────────────────────────── */
    .st-key-sv_back .stButton > button {
        background: transparent !important;
        border: 1px solid #272727 !important;
        border-radius: 10px !important; color: #606060 !important;
        font-size: 0.76rem !important; font-weight: 700 !important;
        min-height: 2.1rem !important; padding: 0 1rem !important;
        transition: all .15s ease !important;
    }
    .st-key-sv_back .stButton > button:hover {
        background: rgba(255,255,255,0.04) !important;
        border-color: #404040 !important; color: #e0e0e0 !important;
    }

    /* ── sort select ──────────────────────────────────────────────── */
    .st-key-sv_sort [data-baseweb="select"] {
        background: #161616 !important; border: 1px solid #272727 !important;
        border-radius: 10px !important; min-height: 2.1rem !important;
    }
    .st-key-sv_sort [data-baseweb="select"] * {
        color: #9e9e9e !important; font-size: 0.72rem !important;
        font-weight: 600 !important;
    }

    /* ── filter pills ─────────────────────────────────────────────── */
    .st-key-sv_filters .stButton > button {
        background: #161616 !important;
        border: 1px solid #272727 !important; border-radius: 20px !important;
        color: #606060 !important; font-size: 0.7rem !important;
        font-weight: 700 !important; min-height: 1.9rem !important;
        padding: 0 1rem !important; white-space: nowrap !important;
        transition: all .15s ease !important;
    }
    .st-key-sv_filters .stButton > button:hover {
        background: rgba(38,166,154,0.06) !important;
        border-color: rgba(38,166,154,0.25) !important; color: #26A69A !important;
    }
    [class*="st-key-svf_on"] .stButton > button {
        background: rgba(38,166,154,0.10) !important;
        border: 1px solid rgba(38,166,154,0.35) !important;
        color: #26A69A !important; font-weight: 800 !important;
        box-shadow: 0 0 12px rgba(38,166,154,0.08) !important;
    }

    /* ── delete buttons ───────────────────────────────────────────── */
    [class*="st-key-sv_del_"] .stButton > button {
        background: transparent !important;
        border: 1px solid rgba(239,83,80,0.12) !important;
        border-radius: 10px !important; color: rgba(239,83,80,0.30) !important;
        height: 100% !important; min-height: 100% !important;
        font-size: 0.85rem !important; padding: 0 !important;
        transition: all .15s ease !important;
    }
    [class*="st-key-sv_del_"] .stButton > button:hover {
        background: rgba(239,83,80,0.08) !important;
        border-color: rgba(239,83,80,0.50) !important; color: #ef5350 !important;
        box-shadow: 0 0 15px rgba(239,83,80,0.12) !important;
    }

    /* ── hero stat cards ──────────────────────────────────────────── */
    .sv-hero { display: grid; grid-template-columns: repeat(3, 1fr);
               gap: 0.7rem; margin-bottom: 1.4rem; }
    .sv-hc { background: #1b1b1b; border: 1px solid #272727;
             border-radius: 14px; padding: 1rem 1.2rem;
             position: relative; overflow: hidden; }
    .sv-hc::before { content: ''; position: absolute; top: 0; left: 0; right: 0;
                     height: 3px; border-radius: 14px 14px 0 0; }
    .sv-hc-val { font-size: 1.8rem; font-weight: 900; line-height: 1;
                 letter-spacing: -1px; }
    .sv-hc-lbl { font-size: 0.6rem; color: #606060; font-weight: 700;
                 text-transform: uppercase; letter-spacing: 0.6px; margin-top: 0.3rem; }

    /* ── section header ───────────────────────────────────────────── */
    .sv-sec { display: flex; align-items: center; gap: 0.55rem;
              margin: 1.6rem 0 0.7rem 0; }
    .sv-sec-bar { width: 3px; height: 1.1rem; border-radius: 2px; flex-shrink: 0; }
    .sv-sec-t { font-size: 0.76rem; font-weight: 800;
                text-transform: uppercase; letter-spacing: 0.6px; }
    .sv-sec-n { font-size: 0.6rem; color: #606060; font-weight: 600; }

    /* ── card ──────────────────────────────────────────────────────── */
    .sv-card { background: #1b1b1b; border: 1px solid #272727;
               border-radius: 14px; overflow: hidden; margin-bottom: 0.55rem;
               transition: border-color .15s ease, box-shadow .15s ease; }
    .sv-card:hover { border-color: #363636;
                     box-shadow: 0 4px 20px rgba(0,0,0,0.3); }

    /* card header */
    .sv-ch { display: flex; align-items: center; gap: 0.6rem;
             padding: 0.85rem 1.1rem; flex-wrap: wrap; }
    .sv-sym { font-size: 0.88rem; font-weight: 900; color: #26A69A;
              background: rgba(38,166,154,0.08); border: 1px solid rgba(38,166,154,0.20);
              border-radius: 8px; padding: 0.2rem 0.6rem; letter-spacing: 0.5px; }
    .sv-sname { font-size: 0.62rem; color: #505050; font-weight: 600; }
    .sv-type { font-size: 0.55rem; font-weight: 800; text-transform: uppercase;
               letter-spacing: 0.5px; border-radius: 20px; padding: 0.15rem 0.65rem;
               border: 1px solid; }
    .sv-pills { display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem;
                flex: 1; min-width: 0; }
    .sv-pill { font-size: 0.68rem; font-weight: 800; border-radius: 6px;
               padding: 0.15rem 0.5rem; border: 1px solid; }
    .sv-plus { font-size: 0.62rem; color: #404040; font-weight: 700; }
    .sv-tag { font-size: 0.55rem; font-weight: 700; border-radius: 5px;
              padding: 0.12rem 0.45rem; border: 1px solid; white-space: nowrap; }
    .sv-date { font-size: 0.55rem; color: #505050; font-weight: 600; margin-left: auto; }

    /* card stats grid */
    .sv-sg { display: grid; grid-template-columns: repeat(6, 1fr);
             background: #161616; }
    .sv-si { padding: 0.65rem 0.4rem; text-align: center;
             border-right: 1px solid #222222; position: relative; }
    .sv-si:last-child { border-right: none; }
    .sv-si::before { content: ''; position: absolute; top: 0; left: 0; right: 0;
                     height: 2px; }
    .sv-sl { font-size: 0.48rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.7px; color: #505050; margin-bottom: 0.2rem; }
    .sv-sv { font-size: 0.88rem; font-weight: 900; line-height: 1; }

    /* ── empty state ──────────────────────────────────────────────── */
    .sv-empty { display: flex; flex-direction: column; align-items: center;
                gap: 0.8rem; padding: 5rem 2rem; text-align: center; }
    .sv-empty-ring { width: 64px; height: 64px; border-radius: 50%;
                     border: 2px solid #272727; display: flex;
                     align-items: center; justify-content: center;
                     font-size: 1.6rem; color: #363636; }
    .sv-empty-t { font-size: 0.95rem; font-weight: 800; color: #606060; }
    .sv-empty-s { font-size: 0.72rem; color: #404040; max-width: 340px;
                  line-height: 1.7; }
    </style>
    """, unsafe_allow_html=True)

    _total = len(favs)

    # ── header row ────────────────────────────────────────────────────────
    _hc = st.columns([1.2, 6, 2.5])
    with _hc[0]:
        with st.container(key="sv_back"):
            if st.button("←  Back", key="sv_back_btn", width="stretch"):
                st.session_state.show_saved_page = False
                st.rerun()
    with _hc[1]:
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:0.6rem;padding-top:0.15rem;'>"
            f"<span style='font-size:1.15rem;font-weight:900;color:#e0e0e0;"
            f"letter-spacing:-0.3px;'>Saved Analysis</span>"
            f"<span style='font-size:0.65rem;font-weight:700;color:#505050;'>"
            f"{_total} item{'s' if _total != 1 else ''}</span></div>",
            unsafe_allow_html=True)
    with _hc[2]:
        with st.container(key="sv_sort"):
            _sort_by = st.selectbox(
                "Sort", ["Win Rate ↓", "Signals ↓", "Date Saved ↓"],
                index=0, key="sv_sort_sel", label_visibility="collapsed")

    # ── hero stats ─────────────────────────────────────────────────────────
    # compute best win rate across all
    _all_wr = [f.get('win_rate', 0) for f in favs]
    _best_wr = max(_all_wr) if _all_wr else 0
    _best_wr_c = '#26A69A' if _best_wr >= 55 else ('#FFC107' if _best_wr >= 45 else '#ef5350')

    st.markdown(
        f"<div class='sv-hero'>"
        f"<div class='sv-hc' style='--c:#26A69A;'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#26A69A,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#26A69A;'>{_total}</div>"
        f"<div class='sv-hc-lbl'>Total Saved</div></div>"
        f"<div class='sv-hc'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#4caf50,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#4caf50;'>{len(_ind_favs)}</div>"
        f"<div class='sv-hc-lbl'>Indicators</div></div>"
        f"<div class='sv-hc'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#FFD700,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#FFD700;'>{len(_combo_favs)}</div>"
        f"<div class='sv-hc-lbl'>Combinations</div></div>"
        f"<div class='sv-hc'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#a78bfa,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#a78bfa;'>{len(_rc_favs)}</div>"
        f"<div class='sv-hc-lbl'>Champions</div></div>"
        f"</div>",
        unsafe_allow_html=True)

    # ── filter tabs ────────────────────────────────────────────────────────
    if 'sp_filter' not in st.session_state:
        st.session_state.sp_filter = 'all'
    _cur = st.session_state.sp_filter
    _fopts = [
        ('all',       f'All  ({_total})'),
        ('indicator', f'Indicators  ({len(_ind_favs)})'),
        ('combo',     f'Combinations  ({len(_combo_favs)})'),
        ('champions', f'Champions  ({len(_rc_favs)})'),
    ]
    with st.container(key="sv_filters"):
        _fc = st.columns(len(_fopts))
        for _i, (_k, _l) in enumerate(_fopts):
            _ak = 'svf_on' if _cur == _k else 'svf_off'
            with st.container(key=f"{_ak}_{_i}"):
                with _fc[_i]:
                    if st.button(_l, key=f"svf_{_k}", width="stretch"):
                        st.session_state.sp_filter = _k
                        st.rerun()

    # ── empty state ────────────────────────────────────────────────────────
    if not favs:
        st.markdown(
            "<div class='sv-empty'>"
            "<div class='sv-empty-ring'>☆</div>"
            "<div class='sv-empty-t'>No saved analysis yet</div>"
            "<div class='sv-empty-s'>Run a <b>Signal Analysis</b> and tap "
            "<b>☆ Save</b> on any indicator or combination card to start "
            "building your collection.</div></div>",
            unsafe_allow_html=True)
        return

    # ── sort helper ────────────────────────────────────────────────────────
    def _sort(lst):
        if _sort_by.startswith('Win Rate'):
            return sorted(lst, key=lambda x: x.get('win_rate', 0), reverse=True)
        if _sort_by.startswith('Signals'):
            return sorted(lst, key=lambda x: x.get('signals', 0), reverse=True)
        return list(reversed(lst))  # Date Saved ↓  (newest first)

    # ── card renderer ──────────────────────────────────────────────────────
    def _card(idx: int, fav: dict, accent: str, type_lbl: str):
        _sym  = fav.get('symbol', '').replace('.SR', '')
        _sn   = fav.get('stock_name', '')
        _disp = fav.get('pair_display', fav.get('pair', ''))
        _reg  = fav.get('best_regime') or ''
        _rc   = _r_colors.get(_reg, '#606060')
        _wr   = fav.get('win_rate', 0)
        _wc   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
        _pf   = fav.get('profit_factor', 0)
        _pc   = '#26A69A' if _pf >= 1.5 else ('#FFC107' if _pf >= 1 else '#ef5350')
        _ea   = fav.get('expectancy', 0)
        _ec   = '#26A69A' if _ea > 0 else '#ef5350'
        _ag   = fav.get('avg_gain', 0)
        _ac   = '#26A69A' if _ag > 0 else '#ef5350'
        _al   = fav.get('avg_loss', 0)
        _sig  = fav.get('signals', 0)
        _rv   = fav.get('risk_val')
        _rw   = fav.get('reward_val')
        _pl   = (fav.get('period_label', '') or '').split('(')[0].strip()
        _sw   = fav.get('signal_window')
        _dt   = fav.get('saved_at', '')

        # pills
        _parts = [p.strip() for p in _disp.split('+')]
        _pills = ''
        for _pi, _pn in enumerate(_parts):
            _pills += (
                f"<span class='sv-pill' style='color:{accent};"
                f"border-color:{accent}33;background:{accent}0A;'>{_pn}</span>"
            )
            if _pi < len(_parts) - 1:
                _pills += "<span class='sv-plus'>+</span>"

        _tags = ''
        if _rv and _rw:
            _tags += (f"<span class='sv-tag' style='color:#64b5f6;"
                      f"border-color:rgba(100,181,246,0.25);background:rgba(100,181,246,0.06);'>"
                      f"R:R {_rv}:{_rw}</span>")
        if _pl:
            _tags += (f"<span class='sv-tag' style='color:#ce93d8;"
                      f"border-color:rgba(206,147,216,0.25);background:rgba(206,147,216,0.06);'>"
                      f"{_pl}</span>")
        if fav.get('save_type') == 'combo' and _sw:
            _sw_i = int(_sw)
            _sw_lbl = 'Same bar' if _sw_i <= 1 else f'Sync {_sw_i} bars'
            _tags += (f"<span class='sv-tag' style='color:#90caf9;'"
                      f"border-color:rgba(144,202,249,0.25);background:rgba(144,202,249,0.06);'>"
                      f"{_sw_lbl}</span>")
        if _reg:
            _tags += (f"<span class='sv-tag' style='color:{_rc};"
                      f"border-color:{_rc}33;background:{_rc}0A;'>{_reg}</span>")

        _h = (
            f"<div class='sv-card'>"
            # header
            f"<div class='sv-ch'>"
            f"<span class='sv-sym'>{_sym}</span>"
            + (f"<span class='sv-sname'>{_sn}</span>" if _sn else '')
            + f"<span class='sv-type' style='color:{accent};"
            f"border-color:{accent}33;background:{accent}0A;'>{type_lbl}</span>"
            f"<div class='sv-pills'>{_pills}</div>"
            + _tags
            + f"<span class='sv-date'>{_dt}</span>"
            f"</div>"
            # stats grid
            f"<div class='sv-sg'>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_wc};'></div>"
            f"<div class='sv-sl'>Win Rate</div>"
            f"<div class='sv-sv' style='color:{_wc};'>{_wr:.1f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_pc};'></div>"
            f"<div class='sv-sl'>Profit Factor</div>"
            f"<div class='sv-sv' style='color:{_pc};'>{_pf:.2f}</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_ec};'></div>"
            f"<div class='sv-sl'>Expectancy</div>"
            f"<div class='sv-sv' style='color:{_ec};'>{_ea:+.2f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_ac};'></div>"
            f"<div class='sv-sl'>Avg Gain</div>"
            f"<div class='sv-sv' style='color:{_ac};'>+{_ag:.2f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:#ef5350;'></div>"
            f"<div class='sv-sl'>Avg Loss</div>"
            f"<div class='sv-sv' style='color:#ef5350;'>{_al:.2f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:#505050;'></div>"
            f"<div class='sv-sl'>Signals</div>"
            f"<div class='sv-sv' style='color:#9e9e9e;'>{_sig}</div></div>"
            f"</div></div>"
        )
        _c1, _c2 = st.columns([14, 1])
        with _c1:
            st.markdown(_h, unsafe_allow_html=True)
        with _c2:
            with st.container(key=f"sv_del_{idx}"):
                if st.button("✕", key=f"sv_rm_{idx}", width="stretch"):
                    _user = st.session_state.get('auth_username', '')
                    delete_favorite(_user, fav.get('id', ''))
                    st.session_state.favorites = [x for x in favs if x.get('id') != fav.get('id')]
                    st.rerun()

    # ── render sections ───────────────────────────────────────────────────
    _gidx = 0
    _active = st.session_state.get('sp_filter', 'all')

    def _section(title, color, flist, tlbl):
        nonlocal _gidx
        if not flist:
            return
        st.markdown(
            f"<div class='sv-sec'>"
            f"<div class='sv-sec-bar' style='background:{color};'></div>"
            f"<span class='sv-sec-t' style='color:{color};'>{title}</span>"
            f"<span class='sv-sec-n'>({len(flist)})</span></div>",
            unsafe_allow_html=True)
        for _f in _sort(flist):
            _card(_gidx, _f, color, tlbl)
            _gidx += 1

    if _active in ('all', 'indicator'):
        _section("Indicators", "#4caf50", _ind_favs, "Indicator")
    if _active in ('all', 'combo'):
        _section("Combinations", "#FFD700", _combo_favs, "Combination")
    if _active in ('all', 'champions'):
        _section("Regime Champions", "#a78bfa", _rc_favs, "Champion")


# ── Regime Champion save button ───────────────────────────────────────────────

def render_save_regime_champion_button(row, regime_key, period_label, save_idx):
    """☆/★ Save-to-Vault toggle button rendered below a Regime Champion card.

    Uses an inline button-return check (not on_click) so it works reliably
    inside @st.fragment.  Calls st.rerun() with no scope so Streamlit picks
    fragment scope when inside a fragment, app scope when outside — keeping
    the user on the same tab after saving.
    """
    _sym    = st.session_state.get('analyzed_symbol', '')
    _pk     = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _combo  = row.get('label', '')
    _fav_id = f"rc__{_sym}__{regime_key}__{_pk}__r{save_idx}"

    _cur_favs = st.session_state.get('favorites', [])
    _is_saved = any(f.get('id') == _fav_id for f in _cur_favs)

    _new_fav = {
        'id':               _fav_id,
        'symbol':           _sym,
        'stock_name':       st.session_state.get('analyzed_stock_name', ''),
        'pair':             _combo,
        'pair_display':     _combo,
        'win_rate':         row.get('win_rate', 0),
        'profit_factor':    row.get('profit_factor', 0),
        'expectancy':       row.get('expectancy', 0),
        'avg_gain':         row.get('avg_gain', 0),
        'avg_loss':         row.get('avg_loss', 0),
        'signals':          row.get('total', 0),
        'best_regime':      regime_key,
        'saved_at':         _today_date.today().strftime('%b %d, %Y'),
        'save_type':        'regime_champion',
        'period_label':     period_label,
        'combo_indicators': _combo,
        'signal_window':    row.get('signal_window', 1),
        'risk_val':         st.session_state.get('sa_risk_val', 1),
        'reward_val':       st.session_state.get('sa_reward_val', 2),
    }

    _wrap_key = f"rcbtn_s_{save_idx}_{regime_key}" if _is_saved else f"rcbtn_u_{save_idx}_{regime_key}"
    _btn_key  = f"rc_save_{_fav_id.replace('__','_').replace('.','_').replace(' ','_')}"
    _btn_lbl  = "★  Saved to Vault  ·  click to remove" if _is_saved else "☆  Save to Vault"

    def _do_save(_fid=_fav_id, _nf=_new_fav, _saved=_is_saved):
        try:
            _toggle_favorite(_fid, None if _saved else _nf)
        except Exception as _e:
            st.toast(f"Save failed: {_e}", icon="❌")
            return
        if _saved:
            st.toast("Removed from Champions Vault", icon="🗑️")
        else:
            st.toast("Saved to Champions Vault!", icon="⚡")

    with st.container(key=_wrap_key):
        st.button(_btn_lbl, key=_btn_key, on_click=_do_save, use_container_width=True)


# ── Champions Vault full-page view ────────────────────────────────────────────

def render_champions_vault_page():
    favs    = st.session_state.get('favorites', [])
    rc_favs = [f for f in favs if f.get('save_type') == 'regime_champion']
    _user   = st.session_state.get('auth_username', '')

    _PERIODS = ['Short (5d)', 'Medium (63d)', 'Long (252d)']
    _P_LABEL  = ['Short', 'Medium', 'Long']
    _P_SUB    = ['5 days', '63 days', '252 days']
    _REGIMES  = [
        ('TREND',    '#26A69A', '↗'),
        ('RANGE',    '#4A9EFF', '↔'),
        ('VOLATILE', '#FF6B6B', '⚡'),
    ]

    st.markdown("""
    <style>
    /* ── page chrome ── */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] { display:none !important; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 1100px !important;
    }

    /* ── page header ── */
    .cv-page-hdr {
        display: flex; align-items: center; gap: 1rem;
        padding-bottom: 1.8rem;
        border-bottom: 1px solid #13171b;
        margin-bottom: 2rem;
    }
    .cv-icon {
        width: 44px; height: 44px; border-radius: 12px;
        background: rgba(167,139,250,0.1); border: 1px solid rgba(167,139,250,0.18);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem; flex-shrink: 0;
    }
    .cv-title { font-size: 1.45rem; font-weight: 900; color: #edf0f4; letter-spacing: -0.5px; }
    .cv-subtitle { font-size: 0.68rem; font-weight: 600; color: #38434f; margin-top: 0.15rem; }
    .cv-badge {
        margin-left: auto;
        font-size: 0.62rem; font-weight: 800; letter-spacing: 0.5px;
        color: #a78bfa; background: rgba(167,139,250,0.08);
        border: 1px solid rgba(167,139,250,0.16);
        border-radius: 999px; padding: 0.3rem 0.85rem;
        text-transform: uppercase; white-space: nowrap;
    }

    /* ── hero stats ── */
    .cv-stats {
        display: grid; grid-template-columns: repeat(6,1fr); gap: 0.75rem;
        margin-bottom: 2.8rem;
    }
    .cv-stat {
        background: #0c0f12; border: 1px solid #161b1f;
        border-radius: 16px; padding: 1.1rem 1.15rem 0.95rem;
        position: relative; overflow: hidden;
    }
    .cv-stat-bar {
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        border-radius: 16px 16px 0 0;
    }
    .cv-stat-val {
        font-size: 1.7rem; font-weight: 900; line-height: 1; margin-bottom: 0.3rem;
    }
    .cv-stat-lbl {
        font-size: 0.5rem; font-weight: 800; color: #252d38;
        text-transform: uppercase; letter-spacing: 1px;
    }

    /* ── stock section ── */
    .cv-stock-hdr {
        display: flex; align-items: center; gap: 0.85rem;
        margin: 0 0 1.1rem 0;
    }
    .cv-stock-accent { width: 3px; height: 1.5rem; border-radius: 2px; background: #a78bfa; flex-shrink:0; }
    .cv-stock-sym  { font-size: 1.15rem; font-weight: 900; color: #e5eaf0; letter-spacing:-0.3px; }
    .cv-stock-name { font-size: 0.64rem; font-weight: 700; color: #2e3a48; }
    .cv-stock-pill {
        margin-left: auto;
        font-size: 0.56rem; font-weight: 800; letter-spacing: 0.4px;
        color: #5a6570; background: #0f1316;
        border: 1px solid #181e24; border-radius: 999px;
        padding: 0.22rem 0.65rem; text-transform: uppercase;
    }

    /* ── grid ── */
    .cv-col-lbl {
        font-size: 0.56rem; font-weight: 800; color: #22292f;
        text-transform: uppercase; letter-spacing: 0.9px; padding-bottom: 0.45rem;
    }
    .cv-col-lbl.period { text-align: center; border-bottom: 1px solid #111518; }
    .cv-grid-div { height: 1px; background: #0e1215; margin: 0.3rem 0 1rem 0; }

    /* ── regime pill ── */
    .cv-reg {
        display: inline-flex; align-items: center; gap: 0.3rem;
        font-size: 0.68rem; font-weight: 800;
        padding: 0.32rem 0.8rem; border-radius: 999px; white-space: nowrap;
    }

    /* ── champion card ── */
    .cv-card {
        background: #0c0f12; border: 1px solid #161b1f;
        border-radius: 14px; padding: 0.95rem 1rem 0.8rem;
        position: relative; overflow: hidden;
    }
    .cv-card-top { position:absolute; top:0; left:0; right:0; height:2px; border-radius:14px 14px 0 0; }
    .cv-card-combo {
        font-size: 0.78rem; font-weight: 800; color: #c5ccd4;
        line-height: 1.5; margin-bottom: 0.6rem;
    }
    .cv-card-stats { display: flex; gap: 0.8rem; flex-wrap: wrap; }
    .cv-cs { display: flex; flex-direction: column; gap: 0.1rem; }
    .cv-cl { font-size: 0.44rem; font-weight: 800; color: #1e2730;
             text-transform: uppercase; letter-spacing: 0.6px; }
    .cv-cv { font-size: 0.82rem; font-weight: 900; line-height: 1; }

    /* ── empty cell ── */
    .cv-empty-cell {
        display: flex; align-items: center; justify-content: center;
        min-height: 90px; color: #131820; font-size: 1.5rem;
    }

    /* ── empty page state ── */
    .cv-empty-page {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 6rem 2rem; text-align: center; gap: 1.3rem;
    }
    .cv-empty-ring {
        width: 88px; height: 88px; border-radius: 50%;
        border: 2px solid #161b1f;
        display: flex; align-items: center; justify-content: center;
        font-size: 2.4rem; color: #1a2028;
    }
    .cv-empty-title { font-size: 1.05rem; font-weight: 800; color: #303a45; }
    .cv-empty-body  { font-size: 0.74rem; color: #222c36; max-width: 420px; line-height: 1.9; }

    /* ── back button ── */
    .st-key-cv_back_wrap .stButton > button {
        background: transparent !important;
        border: 1px solid #191e23 !important;
        border-radius: 10px !important;
        color: #384450 !important;
        font-size: 0.72rem !important; font-weight: 700 !important;
        padding: 0.52rem 1rem !important;
        height: auto !important; min-height: auto !important;
        letter-spacing: 0.2px !important;
    }
    .st-key-cv_back_wrap .stButton > button:hover {
        border-color: #2a3540 !important;
        color: #7a8fa0 !important;
        background: rgba(255,255,255,0.025) !important;
    }

    /* ── remove button ── */
    [class*="st-key-cvr_"] .stButton > button {
        background: transparent !important;
        border: 1px solid #161b1f !important;
        border-radius: 7px !important;
        color: #222c36 !important;
        font-size: 0.58rem !important; font-weight: 700 !important;
        padding: 0.22rem 0.6rem !important;
        height: auto !important; min-height: auto !important;
        transition: all 0.15s ease !important;
        margin-top: 0.45rem !important;
    }
    [class*="st-key-cvr_"] .stButton > button:hover {
        background: rgba(239,83,80,0.07) !important;
        border-color: rgba(239,83,80,0.35) !important;
        color: #ef5350 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── header ────────────────────────────────────────────────────────────
    _n       = len(rc_favs)
    _stocks  = len(set(f.get('symbol', '') for f in rc_favs))
    _hdr_l, _hdr_r = st.columns([8, 1.4])
    with _hdr_l:
        st.markdown(
            "<div class='cv-page-hdr'>"
            "<div class='cv-icon'>⚡</div>"
            "<div><div class='cv-title'>Champions Vault</div>"
            "<div class='cv-subtitle'>Saved regime champions grouped by stock and holding period</div></div>"
            f"<span class='cv-badge'>{_n} saved · {_stocks} stock{'s' if _stocks != 1 else ''}</span>"
            "</div>",
            unsafe_allow_html=True)
    with _hdr_r:
        with st.container(key="cv_back_wrap"):
            if st.button("← Back", key="cv_back_btn", use_container_width=True):
                st.session_state.show_champions_vault = False
                st.rerun()

    # ── hero stats ────────────────────────────────────────────────────────
    _trend_n = sum(1 for f in rc_favs if f.get('best_regime') == 'TREND')
    _range_n = sum(1 for f in rc_favs if f.get('best_regime') == 'RANGE')
    _vol_n   = sum(1 for f in rc_favs if f.get('best_regime') == 'VOLATILE')
    _avg_wr  = (sum(f.get('win_rate', 0)       for f in rc_favs) / _n) if _n else 0
    _avg_pf  = (sum(f.get('profit_factor', 0)  for f in rc_favs) / _n) if _n else 0
    _wc      = '#26A69A' if _avg_wr >= 55 else ('#FFC107' if _avg_wr >= 45 else '#ef5350')
    _pc      = '#26A69A' if _avg_pf >= 1.5 else ('#FFC107' if _avg_pf >= 1.0 else '#ef5350')
    st.markdown(
        f"<div class='cv-stats'>"
        f"<div class='cv-stat'><div class='cv-stat-bar' style='background:linear-gradient(90deg,#a78bfa,transparent)'></div>"
        f"<div class='cv-stat-val' style='color:#a78bfa'>{_n}</div><div class='cv-stat-lbl'>Total Saved</div></div>"

        f"<div class='cv-stat'><div class='cv-stat-bar' style='background:linear-gradient(90deg,#26A69A,transparent)'></div>"
        f"<div class='cv-stat-val' style='color:#26A69A'>{_trend_n}</div><div class='cv-stat-lbl'>Trend</div></div>"

        f"<div class='cv-stat'><div class='cv-stat-bar' style='background:linear-gradient(90deg,#4A9EFF,transparent)'></div>"
        f"<div class='cv-stat-val' style='color:#4A9EFF'>{_range_n}</div><div class='cv-stat-lbl'>Range</div></div>"

        f"<div class='cv-stat'><div class='cv-stat-bar' style='background:linear-gradient(90deg,#FF6B6B,transparent)'></div>"
        f"<div class='cv-stat-val' style='color:#FF6B6B'>{_vol_n}</div><div class='cv-stat-lbl'>Volatile</div></div>"

        f"<div class='cv-stat'><div class='cv-stat-bar' style='background:linear-gradient(90deg,{_wc},transparent)'></div>"
        f"<div class='cv-stat-val' style='color:{_wc}'>{_avg_wr:.1f}%</div><div class='cv-stat-lbl'>Avg Win Rate</div></div>"

        f"<div class='cv-stat'><div class='cv-stat-bar' style='background:linear-gradient(90deg,{_pc},transparent)'></div>"
        f"<div class='cv-stat-val' style='color:{_pc}'>{_avg_pf:.2f}x</div><div class='cv-stat-lbl'>Avg P. Factor</div></div>"
        f"</div>",
        unsafe_allow_html=True)

    # ── empty state ────────────────────────────────────────────────────────
    if not rc_favs:
        st.markdown(
            "<div class='cv-empty-page'>"
            "<div class='cv-empty-ring'>⚡</div>"
            "<div class='cv-empty-title'>Your vault is empty</div>"
            "<div class='cv-empty-body'>Go to <b>Signal Analysis → Indicator Combinations → Regime Champions</b>, "
            "run analysis on any stock, then tap <b style='color:#a78bfa'>☆ Save to Vault</b> "
            "on any champion card.</div>"
            "</div>",
            unsafe_allow_html=True)
        return

    # ── build lookup ───────────────────────────────────────────────────────
    _lookup: dict = {}
    for _f in rc_favs:
        _s  = _f.get('symbol', '—')
        _sn = _f.get('stock_name', '')
        _pl = _f.get('period_label', '—')
        _rg = _f.get('best_regime', '—')
        if _s not in _lookup:
            _lookup[_s] = {'sname': _sn, 'periods': {}}
        _lookup[_s]['periods'].setdefault(_pl, {})[_rg] = _f

    # ── render per stock ───────────────────────────────────────────────────
    for _sym, _sdata in sorted(_lookup.items()):
        _sname   = _sdata['sname']
        _periods = _sdata['periods']
        _sym_cnt = sum(len(v) for v in _periods.values())

        # stock header
        st.markdown(
            f"<div class='cv-stock-hdr'>"
            f"<div class='cv-stock-accent'></div>"
            f"<span class='cv-stock-sym'>{_sym}</span>"
            + (f"<span class='cv-stock-name'>{_sname}</span>" if _sname else "")
            + f"<span class='cv-stock-pill'>{_sym_cnt} saved</span>"
            "</div>",
            unsafe_allow_html=True)

        # column header row
        _gh = st.columns([0.9, 2.5, 2.5, 2.5], gap="medium")
        with _gh[0]:
            st.markdown("<div class='cv-col-lbl'>Regime</div>", unsafe_allow_html=True)
        for _ci, (_pl, _ps) in enumerate(zip(_P_LABEL, _P_SUB)):
            with _gh[_ci + 1]:
                st.markdown(
                    f"<div class='cv-col-lbl period'>{_pl}"
                    f"<span style='color:#181e24'> · {_ps}</span></div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='cv-grid-div'></div>", unsafe_allow_html=True)

        # one row per regime
        for _rk, _rc, _ri in _REGIMES:
            _row = st.columns([0.9, 2.5, 2.5, 2.5], gap="medium")

            with _row[0]:
                st.markdown(
                    f"<div style='padding:0.7rem 0'>"
                    f"<span class='cv-reg' style='color:{_rc};background:{_rc}10;"
                    f"border:1px solid {_rc}28'>{_ri}&nbsp;{_rk.title()}</span></div>",
                    unsafe_allow_html=True)

            for _pi, _period in enumerate(_PERIODS):
                with _row[_pi + 1]:
                    _f = _periods.get(_period, {}).get(_rk)
                    if _f:
                        _wr    = _f.get('win_rate', 0)
                        _pf    = _f.get('profit_factor', 0)
                        _exp   = _f.get('expectancy', 0)
                        _sig   = _f.get('signals', 0)
                        _combo = _f.get('combo_indicators', '—')
                        _fid   = _f.get('id', '')
                        _wc2   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
                        _ec    = '#26A69A' if _exp > 0 else '#ef5350'
                        _rkey  = f"cvr_{_sym[:6]}_{_rk[:2]}_{_pi}"

                        st.markdown(
                            f"<div class='cv-card'>"
                            f"<div class='cv-card-top' style='background:linear-gradient(90deg,{_rc},transparent)'></div>"
                            f"<div class='cv-card-combo'>{_combo}</div>"
                            f"<div class='cv-card-stats'>"
                            f"<div class='cv-cs'><div class='cv-cl'>Win Rate</div>"
                            f"<div class='cv-cv' style='color:{_wc2}'>{_wr:.1f}%</div></div>"
                            f"<div class='cv-cs'><div class='cv-cl'>P.Factor</div>"
                            f"<div class='cv-cv' style='color:#5a6878'>{_pf:.2f}</div></div>"
                            f"<div class='cv-cs'><div class='cv-cl'>Edge</div>"
                            f"<div class='cv-cv' style='color:{_ec}'>{_exp:+.2f}%</div></div>"
                            f"<div class='cv-cs'><div class='cv-cl'>Signals</div>"
                            f"<div class='cv-cv' style='color:#303c48'>{_sig}</div></div>"
                            f"</div></div>",
                            unsafe_allow_html=True)

                        def _do_remove(_fid=_fid):
                            delete_favorite(_user, _fid)
                            st.session_state.favorites = [
                                x for x in st.session_state.get('favorites', [])
                                if x.get('id') != _fid
                            ]
                            st.toast("Removed from Champions Vault", icon="🗑️")

                        with st.container(key=f"cvr_{_rkey}"):
                            st.button("✕ Remove", key=_rkey, on_click=_do_remove)
                    else:
                        st.markdown("<div class='cv-empty-cell'>—</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

