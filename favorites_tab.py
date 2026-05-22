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


# ── Save Strategy button ──────────────────────────────────────────────────────
# Uses on_click callback — NO @st.fragment in loops (causes identity bugs).
# The callback fires synchronously before the rerun, so the button label
# updates on the very next render with zero lag.

def _rc_toggle(fav_id: str, new_fav: dict) -> None:
    """on_click callback: toggle a regime-champion strategy save/remove."""
    _user = st.session_state.get('auth_username', '')
    if not _user:
        st.session_state['_rc_toast'] = ("Not logged in", "❌")
        return
    _cur = st.session_state.get('favorites', [])
    _exists = any(f.get('id') == fav_id for f in _cur)
    try:
        if _exists:
            delete_favorite(_user, fav_id)
            st.session_state.favorites = [f for f in _cur if f.get('id') != fav_id]
            st.session_state['_rc_toast'] = ("Strategy removed", "🗑️")
        elif new_fav is not None:
            upsert_favorite(_user, new_fav)
            st.session_state.favorites = _cur + [new_fav]
            st.session_state['_rc_toast'] = ("Strategy saved!", "⭐")
    except Exception as _e:
        st.session_state['_rc_toast'] = (f"Save failed: {_e}", "❌")


def render_save_regime_champion_button(row, regime_key, period_label, save_idx):
    _sym    = st.session_state.get('analyzed_symbol', '')
    _pk     = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _combo  = row.get('label', '')
    _fav_id = f"rc__{_sym}__{regime_key}__{_pk}__r{save_idx}"

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

    _cur_favs = st.session_state.get('favorites', [])
    _is_saved = any(f.get('id') == _fav_id for f in _cur_favs)
    _btn_lbl  = "★  Strategy Saved  ·  Click to Remove" if _is_saved else "☆  Save Strategy"

    st.button(
        _btn_lbl,
        key=f"sb_{save_idx}_{regime_key}",
        use_container_width=True,
        on_click=_rc_toggle,
        args=(_fav_id, _new_fav),
    )


# ── Saved Strategies full-page view ───────────────────────────────────────────

def render_champions_vault_page():
    favs    = st.session_state.get('favorites', [])
    rc_favs = [f for f in favs if f.get('save_type') == 'regime_champion']
    _user   = st.session_state.get('auth_username', '')

    _REGIME_META = {
        'TREND':    ('#26A69A', '↗', 'Trend'),
        'RANGE':    ('#4A9EFF', '↔', 'Range'),
        'VOLATILE': ('#FF6B6B', '⚡', 'Volatile'),
    }
    _PERIODS = ['Short (5d)', 'Medium (63d)', 'Long (252d)']
    _PERIOD_SHORT = {'Short (5d)': ('Short', '5D'), 'Medium (63d)': ('Medium', '63D'), 'Long (252d)': ('Long', '252D')}

    st.markdown("""
    <style>
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] { display:none !important; }

    .main .block-container, div.block-container {
        max-width: 96% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1.6rem !important;
        padding-bottom: 5rem !important;
    }

    /* ════════════════════════════════════════
       TOP BAR  (title + KPIs inline)
    ════════════════════════════════════════ */
    .ss-topbar {
        display:flex; align-items:center; gap:1.2rem;
        margin-bottom:1.6rem; flex-wrap:wrap;
    }
    .ss-topbar-title {
        font-size:1.55rem; font-weight:900; color:#e8e8e8;
        letter-spacing:-0.5px; white-space:nowrap;
    }
    .ss-topbar-sub {
        font-size:0.74rem; color:#3a3a3a; font-weight:600;
        white-space:nowrap;
    }
    .ss-topbar-divider {
        width:1px; height:2rem; background:#222; flex-shrink:0;
    }
    .ss-kpi-inline {
        display:flex; align-items:center; gap:0.3rem;
    }
    .ss-kpi-inline-val {
        font-size:1.15rem; font-weight:900; line-height:1;
    }
    .ss-kpi-inline-lbl {
        font-size:0.63rem; font-weight:700; color:#3a3a3a;
        text-transform:uppercase; letter-spacing:0.8px;
        margin-top:0.15rem;
    }
    .ss-kpi-dot {
        width:6px; height:6px; border-radius:50%; flex-shrink:0;
        margin-right:0.2rem; margin-bottom:0.05rem;
    }

    /* ── back button ── */
    .st-key-cv_back_wrap .stButton > button {
        background:transparent !important;
        border:1px solid #252525 !important;
        border-radius:8px !important; color:#404040 !important;
        font-size:0.72rem !important; font-weight:700 !important;
        padding:0.45rem 0.9rem !important;
        height:auto !important; min-height:auto !important;
        transition:all 0.12s ease !important; letter-spacing:0.2px !important;
    }
    .st-key-cv_back_wrap .stButton > button:hover {
        border-color:#404040 !important; color:#c0c0c0 !important;
    }

    /* ════════════════════════════════════════
       STOCK ROW  (full-width horizontal band)
    ════════════════════════════════════════ */
    .ss-stock-row {
        border:1px solid #b8860b55;
        border-radius:12px;
        margin-bottom:0.7rem;
        overflow:hidden;
        background:#141414;
        box-shadow:0 0 0 1px #b8860b18;
    }
    .ss-stock-row:hover {
        border-color:#DAA52088;
        box-shadow:0 0 0 1px #DAA52033;
    }

    /* stock label strip */
    .ss-stock-label {
        display:flex; align-items:center; gap:0.65rem;
        padding:0.6rem 1rem 0.55rem;
        background:#191919;
        border-bottom:1px solid #b8860b33;
    }
    .ss-stock-sym {
        font-size:0.95rem; font-weight:900; color:#d0d0d0;
        letter-spacing:0.2px;
    }
    .ss-stock-name {
        font-size:0.7rem; color:#383838; font-weight:600;
    }
    .ss-stock-count {
        margin-left:auto;
        font-size:0.62rem; font-weight:800; letter-spacing:0.6px;
        color:#383838; text-transform:uppercase;
    }

    /* inner 3-col grid */
    .ss-period-grid {
        display:grid; grid-template-columns:repeat(3,1fr);
    }
    .ss-period-col {
        border-right:1px solid #1a1a1a; padding:0.5rem 0.65rem 0.55rem;
    }
    .ss-period-col:last-child { border-right:none; }

    .ss-period-title {
        font-size:0.65rem; font-weight:800; color:#5a5a5a;
        text-transform:uppercase; letter-spacing:1px;
        margin-bottom:0.4rem; display:flex; align-items:center; gap:0.3rem;
    }
    .ss-period-title-dot {
        width:5px; height:5px; border-radius:50%; background:#a78bfa; flex-shrink:0;
    }

    /* ════════════════════════════════════════
       STRATEGY CHIP  (single row, minimal)
    ════════════════════════════════════════ */
    .ss-chip {
        display:flex; align-items:center; gap:0;
        background:#0f0f0f; border:1px solid #1d1d1d;
        border-radius:6px; overflow:hidden;
        margin-bottom:0.3rem;
        transition:border-color 0.1s;
    }
    .ss-chip:hover { border-color:#2a2a2a; }
    .ss-chip-bar { width:2px; flex-shrink:0; align-self:stretch; }
    .ss-chip-body {
        flex:1; min-width:0; padding:0.32rem 0.5rem;
        display:flex; align-items:center; gap:0.4rem;
    }
    .ss-chip-regime {
        font-size:0.6rem; font-weight:800; padding:0.18rem 0.52rem;
        border-radius:20px; text-transform:uppercase; letter-spacing:0.3px;
        white-space:nowrap; flex-shrink:0; line-height:1.4;
        border:none;
    }
    .ss-chip-name {
        font-size:0.72rem; font-weight:700; color:#888;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        flex:1; min-width:0; line-height:1.3;
    }
    .ss-chip-wr {
        font-size:0.72rem; font-weight:800;
        white-space:nowrap; flex-shrink:0; padding-right:0.1rem;
    }
    .ss-chip-sigs {
        font-size:0.58rem; font-weight:700; color:#363636;
        white-space:nowrap; flex-shrink:0;
    }

    /* ── empty column placeholder ── */
    .ss-col-empty {
        font-size:0.68rem; color:#1e1e1e; font-weight:600;
        padding:0.25rem 0; letter-spacing:0.3px;
    }

    /* ── remove button ── */
    [class*="st-key-ssrm_"] .stButton > button {
        background:transparent !important; border:none !important;
        color:#242424 !important;
        font-size:0.62rem !important; font-weight:700 !important;
        padding:0.25rem 0.35rem !important;
        height:auto !important; min-height:auto !important;
        transition:color 0.1s ease !important; line-height:1 !important;
    }
    [class*="st-key-ssrm_"] .stButton > button:hover {
        color:#ef5350 !important;
    }

    /* ════════════════════════════════════════
       SECTION DIVIDER
    ════════════════════════════════════════ */
    .ss-section-divider {
        display:flex; align-items:center; gap:0.8rem;
        margin:2.2rem 0 1.1rem;
    }
    .ss-section-line { flex:1; height:1px; background:#1a1a1a; }
    .ss-section-lbl {
        font-size:0.82rem; font-weight:800; color:#383838;
        text-transform:uppercase; letter-spacing:1.2px; white-space:nowrap;
        display:flex; align-items:center; gap:0.45rem;
    }
    .ss-section-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }

    /* ════════════════════════════════════════
       LIVE SIGNAL CARDS
    ════════════════════════════════════════ */
    .ls-card {
        background:#111; border:1px solid #1e1e1e;
        border-radius:12px; overflow:hidden;
        margin-bottom:0.6rem;
        transition:border-color 0.15s;
    }
    .ls-card:hover { border-color:#2a2a2a; }
    .ls-card-fire { border-color:#26A69A22 !important; }
    .ls-card-fire:hover { border-color:#26A69A55 !important; }

    .ls-top {
        display:flex; align-items:center; gap:0.65rem;
        padding:0.65rem 1rem; border-bottom:1px solid #181818;
        flex-wrap:wrap;
    }
    .ls-sym {
        font-size:0.9rem; font-weight:900; color:#c8c8c8;
        letter-spacing:0.2px; white-space:nowrap;
    }
    .ls-tag {
        font-size:0.6rem; font-weight:800; padding:0.14rem 0.48rem;
        border-radius:20px; border:none; text-transform:uppercase;
        letter-spacing:0.4px; white-space:nowrap;
    }
    .ls-combo-name {
        font-size:0.76rem; font-weight:600; color:#3a3a3a;
        flex:1; min-width:0; white-space:nowrap;
        overflow:hidden; text-overflow:ellipsis;
    }
    .ls-badge-fire {
        font-size:0.62rem; font-weight:800; padding:0.18rem 0.6rem;
        border-radius:4px; white-space:nowrap; flex-shrink:0;
        background:rgba(38,166,154,0.1); border:1px solid rgba(38,166,154,0.3);
        color:#26A69A; letter-spacing:0.4px; text-transform:uppercase;
    }

    /* indicator pills row */
    .ls-pills { display:flex; flex-wrap:wrap; gap:0.28rem; padding:0.45rem 1rem; }
    .ls-pill {
        font-size:0.7rem; font-weight:700; padding:0.16rem 0.5rem;
        border-radius:4px; border:1px solid; line-height:1.4;
    }

    /* price ladder — 4 cells */
    .ls-ladder {
        display:grid; grid-template-columns:repeat(4,1fr);
        border-top:1px solid #181818;
    }
    .ls-cell {
        padding:0.65rem 0.9rem; border-right:1px solid #181818;
        position:relative;
    }
    .ls-cell:last-child { border-right:none; }
    .ls-cell-top { position:absolute; top:0; left:0; right:0; height:1px; }
    .ls-cell-lbl {
        font-size:0.68rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.8px; color:#363636; margin-bottom:0.28rem;
    }
    .ls-cell-val {
        font-size:1.2rem; font-weight:900; line-height:1; letter-spacing:-0.2px;
    }
    .ls-cell-sub {
        font-size:0.72rem; font-weight:600; margin-top:0.18rem; color:#363636;
    }

    /* quiet/watching row */
    .ls-quiet {
        display:flex; align-items:center; gap:0.55rem;
        background:#0d0d0d; border:1px solid #181818;
        border-radius:8px; padding:0.45rem 0.8rem;
        margin-bottom:0.3rem; flex-wrap:wrap;
    }
    .ls-quiet-sym { font-size:0.82rem; font-weight:800; color:#545454; white-space:nowrap; }
    .ls-quiet-combo { font-size:0.72rem; color:#3a3a3a; flex:1; min-width:0;
                      white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .ls-quiet-prog { font-size:0.62rem; color:#444; font-weight:700;
                     white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px; }

    /* ════════════════════════════════════════
       EMPTY STATE
    ════════════════════════════════════════ */
    .ss-empty {
        background:#111; border:1px solid #1e1e1e; border-radius:14px;
        padding:5rem 2rem; text-align:center;
    }
    .ss-empty-icon { font-size:2rem; color:#252525; margin-bottom:1rem; }
    .ss-empty-title { font-size:1.2rem; font-weight:800; color:#383838; margin-bottom:0.5rem; }
    .ss-empty-body  { font-size:0.9rem; color:#2a2a2a; max-width:480px; margin:0 auto; line-height:1.8; }
    </style>
    """, unsafe_allow_html=True)

    # ── counts ────────────────────────────────────────────────────────────────
    _n       = len(rc_favs)
    _stocks  = len(set(f.get('symbol', '') for f in rc_favs))
    _trend_n = sum(1 for f in rc_favs if f.get('best_regime') == 'TREND')
    _range_n = sum(1 for f in rc_favs if f.get('best_regime') == 'RANGE')
    _vol_n   = sum(1 for f in rc_favs if f.get('best_regime') == 'VOLATILE')

    # ── top bar ───────────────────────────────────────────────────────────────
    _tl, _tr = st.columns([1, 0.13])
    with _tl:
        st.markdown(
            "<div class='ss-topbar'>"
            "<div>"
            "<div class='ss-topbar-title'>Saved Strategies</div>"
            "<div class='ss-topbar-sub'>Regime champions · grouped by stock &amp; period</div>"
            "</div>"
            "<div class='ss-topbar-divider'></div>"
            # stocks
            f"<div class='ss-kpi-inline'>"
            f"<div><div class='ss-kpi-inline-val' style='color:#707070'>{_stocks}</div>"
            f"<div class='ss-kpi-inline-lbl'>Stocks</div></div></div>"
            "<div class='ss-topbar-divider'></div>"
            # saved
            f"<div class='ss-kpi-inline'>"
            f"<div><div class='ss-kpi-inline-val' style='color:#a78bfa'>{_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Saved</div></div></div>"
            "<div class='ss-topbar-divider'></div>"
            # trend
            f"<div class='ss-kpi-inline'>"
            f"<div class='ss-kpi-dot' style='background:#26A69A'></div>"
            f"<div><div class='ss-kpi-inline-val' style='color:#26A69A'>{_trend_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Trend</div></div></div>"
            # range
            f"<div class='ss-kpi-inline'>"
            f"<div class='ss-kpi-dot' style='background:#4A9EFF'></div>"
            f"<div><div class='ss-kpi-inline-val' style='color:#4A9EFF'>{_range_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Range</div></div></div>"
            # volatile
            f"<div class='ss-kpi-inline'>"
            f"<div class='ss-kpi-dot' style='background:#FF6B6B'></div>"
            f"<div><div class='ss-kpi-inline-val' style='color:#FF6B6B'>{_vol_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Volatile</div></div></div>"
            "</div>",
            unsafe_allow_html=True)
    with _tr:
        with st.container(key="cv_back_wrap"):
            if st.button("← Back", key="cv_back_btn", use_container_width=True):
                st.session_state.show_champions_vault = False
                st.rerun()

    # ── empty state ───────────────────────────────────────────────────────────
    if not rc_favs:
        st.markdown(
            "<div class='ss-empty'>"
            "<div class='ss-empty-icon'>★</div>"
            "<div class='ss-empty-title'>No saved strategies yet</div>"
            "<div class='ss-empty-body'>Run analysis on any stock, go to "
            "<b style='color:#555'>Signal Analysis → Indicator Combinations → Regime Champions</b>, "
            "then tap <b style='color:#a78bfa'>☆ Save Strategy</b>.</div>"
            "</div>",
            unsafe_allow_html=True)
        return

    # ── build per-stock, per-period lookup ────────────────────────────────────
    _by_stock: dict = {}
    for _f in rc_favs:
        _s  = _f.get('symbol', '—')
        _sn = _f.get('stock_name', '')
        _pl = _f.get('period_label', 'Medium (63d)')
        if _s not in _by_stock:
            _by_stock[_s] = {'sname': _sn, 'periods': {p: [] for p in _PERIODS}}
        _matched = next((p for p in _PERIODS if p.lower().startswith(_pl.split()[0].lower())), _pl)
        _by_stock[_s]['periods'].setdefault(_matched, []).append(_f)

    for _sd in _by_stock.values():
        for _pl2 in _sd['periods']:
            _sd['periods'][_pl2].sort(key=lambda f: -float(f.get('win_rate', 0) or 0))

    # ── filter bar ───────────────────────────────────────────────────────────
    _fcol1, _fcol2, _fcol3 = st.columns([2, 1, 1], gap="small")
    with _fcol1:
        _search = st.text_input(" ", placeholder="Search symbol or indicator…",
                                key="cv_search", label_visibility="collapsed")
    with _fcol2:
        _regime_filter = st.selectbox(" ", ["All Regimes", "Trend", "Range", "Volatile"],
                                      key="cv_regime_filter", label_visibility="collapsed")
    with _fcol3:
        _period_filter = st.selectbox(" ", ["All Periods", "Short", "Medium", "Long"],
                                      key="cv_period_filter", label_visibility="collapsed")

    _sq = _search.strip().lower() if _search else ""
    _rf = _regime_filter if _regime_filter != "All Regimes" else ""
    _pf_sel = _period_filter if _period_filter != "All Periods" else ""

    # ── render one row per stock ──────────────────────────────────────────────
    _gidx = 0
    for _sym, _sdata in sorted(_by_stock.items()):
        _sname   = _sdata['sname']
        _periods = _sdata['periods']
        _sym_disp = _sym.replace('.SR', '')

        # apply filters
        if _sq and _sq not in _sym_disp.lower() and _sq not in _sname.lower() and \
           not any(_sq in f.get('combo_indicators','').lower()
                   for v in _periods.values() for f in v):
            continue
        if _rf:
            if not any(f.get('best_regime','').title() == _rf
                       for v in _periods.values() for f in v):
                continue
        if _pf_sel:
            if not any(_pf_sel in p for p in _periods if _periods[p]):
                continue

        _strat_n = sum(len(v) for v in _periods.values())

        # ── stock card header ────────────────────────────────────────────────
        st.markdown(
            f"<div class='ss-stock-row'>"
            f"<div class='ss-stock-label'>"
            f"<span class='ss-stock-sym'>{_sym_disp}</span>"
            + (f"<span class='ss-stock-name'>{_sname}</span>" if _sname else "")
            + f"<span class='ss-stock-count'>{_strat_n} saved</span>"
            f"</div>",
            unsafe_allow_html=True)

        # ── 3 columns: Short | Medium | Long — always side by side ──────────
        _PERIOD_ORDER = [('Short (5d)', 'Short', '5D'), ('Medium (63d)', 'Medium', '63D'), ('Long (252d)', 'Long', '252D')]
        _col_s, _col_m, _col_l = st.columns(3, gap="small")
        _period_cols = [_col_s, _col_m, _col_l]

        for (_pl3, _lbl3, _days3), _pcol in zip(_PERIOD_ORDER, _period_cols):
            _strats_p = _periods.get(_pl3, [])
            with _pcol:
                # period header
                st.markdown(
                    f"<div class='ss-period-title' style='padding:0.4rem 0 0.3rem;'>"
                    f"<div class='ss-period-title-dot'></div>{_lbl3}"
                    f"<span style='color:#3a3a3a;margin-left:0.25rem;font-size:0.58rem;font-weight:700;'>{_days3}</span>"
                    f"<span style='color:#2a2a2a;margin-left:auto;font-size:0.58rem;'>({len(_strats_p)})</span>"
                    f"</div>",
                    unsafe_allow_html=True)

                if not _strats_p:
                    st.markdown("<div class='ss-col-empty'>—</div>", unsafe_allow_html=True)
                    continue

                for _f in _strats_p:
                    _wr    = float(_f.get('win_rate', 0) or 0)
                    _sig   = int(_f.get('signals', 0) or 0)
                    _combo = _f.get('combo_indicators', '—')
                    _rk    = _f.get('best_regime', 'TREND')
                    _fid   = _f.get('id', '')

                    _rc, _ri, _rlbl = _REGIME_META.get(_rk, ('#a78bfa', '★', _rk.title()))
                    _wc = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
                    _rmkey = f"ssrm_{_fid.replace('.','_').replace(' ','_').replace('(','_').replace(')','_').replace('/','_')}"[:72]

                    _c_chip, _c_del = st.columns([14, 1])
                    with _c_chip:
                        st.markdown(
                            f"<div class='ss-chip'>"
                            f"<div class='ss-chip-bar' style='background:{_rc}'></div>"
                            f"<div class='ss-chip-body'>"
                            f"<span class='ss-chip-regime' style='background:{_rc};color:#0a0a0a;'>"
                            f"{_ri}&nbsp;{_rlbl}</span>"
                            f"<span class='ss-chip-name' title='{_combo}'>{_combo}</span>"
                            f"<span class='ss-chip-sigs'>{_sig}×</span>"
                            f"<span class='ss-chip-wr' style='color:{_wc}'>{_wr:.0f}%</span>"
                            f"</div></div>",
                            unsafe_allow_html=True)
                    with _c_del:
                        with st.container(key=_rmkey):
                            st.button("✕", key=f"btn_{_rmkey}",
                                      use_container_width=True,
                                      on_click=_rc_toggle, args=(_fid, None))
                    _gidx += 1

        # close stock card
        st.markdown("</div>", unsafe_allow_html=True)

    # ── LIVE SIGNALS SECTION ─────────────────────────────────────────────────
    _render_live_signals(rc_favs)


# ── Live signal checker ───────────────────────────────────────────────────────

# Maps display name fragments → signal column key in signals_df
_IND_KEY_MAP = {
    'EMA':        'EMA',
    'SMA':        'SMA',
    'Parabolic':  'PSAR',
    'Ichimoku':   'ICHI',
    'WMA':        'WMA',
    'RSI':        'RSI',
    'MACD':       'MACD',
    'Stochastic': 'STOCH',
    'ROC':        'ROC',
    'CCI':        'CCI',
    'Williams':   'WILLR',
    'Bollinger':  'BB',
    'Keltner':    'KC',
    'Donchian':   'DC',
    'MFI':        'MFI',
    'CMF':        'CMF',
    'VWAP':       'VWAP',
    'OBV':        'OBV',
    'ADX':        'ADX',
}

_PERIOD_DAYS = {'Short (5d)': '3mo', 'Medium (63d)': '6mo', 'Long (252d)': '2y'}

_REGIME_COLORS = {'TREND': '#26A69A', 'RANGE': '#4A9EFF', 'VOLATILE': '#FF6B6B'}
_REGIME_ICONS  = {'TREND': '↗', 'RANGE': '↔', 'VOLATILE': '⚡'}


def _combo_display_to_keys(combo_str: str) -> list[str]:
    """Convert 'EMA (20/50/200) + RSI (14)' → ['EMA', 'RSI']"""
    keys = []
    for part in combo_str.split('+'):
        part = part.strip()
        for fragment, key in _IND_KEY_MAP.items():
            if fragment.lower() in part.lower():
                keys.append(key)
                break
    return list(dict.fromkeys(keys))  # dedupe, preserve order


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_df_cached(symbol: str, yf_period: str):
    """Fetch OHLCV + compute all indicators. Returns (df, price) or (None, None)."""
    try:
        import yfinance as yf
        import pandas as pd
        import pandas_ta as ta

        _df = yf.download(symbol, period=yf_period, interval='1d', progress=False, auto_adjust=True)
        if _df is None or len(_df) < 20:
            return None, None
        _df.columns = [c[0] if isinstance(c, tuple) else c for c in _df.columns]
        _df = _df.reset_index()
        if 'Date' not in _df.columns and 'Datetime' in _df.columns:
            _df = _df.rename(columns={'Datetime': 'Date'})
        _df['Date'] = pd.to_datetime(_df['Date'])

        _c = _df['Close']
        _df['EMA_20']  = ta.ema(_c, length=20)
        _df['EMA_50']  = ta.ema(_c, length=50)
        _df['EMA_200'] = ta.ema(_c, length=200)
        _df['SMA_50']  = ta.sma(_c, length=50)
        _df['SMA_200'] = ta.sma(_c, length=200)
        _df['RSI_14']  = ta.rsi(_c, length=14)

        macd = ta.macd(_c)
        if macd is not None:
            for col in macd.columns: _df[col] = macd[col]

        bb = ta.bbands(_c, length=20)
        if bb is not None:
            for col in bb.columns: _df[col] = bb[col]

        stoch = ta.stoch(_df['High'], _df['Low'], _c)
        if stoch is not None:
            for col in stoch.columns: _df[col] = stoch[col]

        adx = ta.adx(_df['High'], _df['Low'], _c)
        if adx is not None:
            for col in adx.columns: _df[col] = adx[col]

        roc   = ta.roc(_c, length=12);                                    _df['ROC_12']   = roc   if roc   is not None else 0
        cci   = ta.cci(_df['High'], _df['Low'], _c, length=20);           _df['CCI_20']   = cci   if cci   is not None else 0
        willr = ta.willr(_df['High'], _df['Low'], _c, length=14);         _df['WILLR_14'] = willr if willr is not None else 0
        mfi   = ta.mfi(_df['High'], _df['Low'], _c, _df['Volume'], length=14); _df['MFI_14'] = mfi if mfi is not None else 0
        cmf   = ta.cmf(_df['High'], _df['Low'], _c, _df['Volume'], length=20); _df['CMF_20'] = cmf if cmf is not None else 0
        obv   = ta.obv(_c, _df['Volume']);                                 _df['OBV']      = obv   if obv   is not None else 0
        wma   = ta.wma(_c, length=20);                                     _df['WMA_20']   = wma   if wma   is not None else _c

        psar = ta.psar(_df['High'], _df['Low'], _c)
        if psar is not None:
            for col in psar.columns: _df[col] = psar[col]

        ichi = ta.ichimoku(_df['High'], _df['Low'], _c)
        if ichi is not None and isinstance(ichi, tuple):
            for part in ichi:
                if hasattr(part, 'columns'):
                    for col in part.columns: _df[col] = part[col]

        _df['REGIME'] = 'TREND'
        _df['VWAP']   = ((_df['High'] + _df['Low'] + _df['Close']) / 3 * _df['Volume']).cumsum() / _df['Volume'].cumsum()

        kc = ta.kc(_df['High'], _df['Low'], _c)
        if kc is not None:
            for col in kc.columns: _df[col] = kc[col]

        dc = ta.donchian(_df['High'], _df['Low'])
        if dc is not None:
            for col in dc.columns: _df[col] = dc[col]

        price = float(_df['Close'].iloc[-1])
        return _df, price
    except Exception:
        return None, None


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_signals_cached(symbol: str, yf_period: str):
    """Fetch OHLCV + compute indicators + detect signals. Cached 5 min."""
    try:
        from signal_engine import detect_signals
        _df, price = _fetch_df_cached(symbol, yf_period)
        if _df is None:
            return None, None
        sigs = detect_signals(_df)
        return sigs, price
    except Exception:
        return None, None


def _check_strategy_firing(sig_df, ind_keys: list[str], window: int = 3) -> dict:
    """
    Check if a combo strategy is currently firing.
    Returns dict with firing status and which indicators are active.
    """
    if sig_df is None or len(sig_df) == 0:
        return {'firing': False, 'active': [], 'missing': ind_keys}

    last_n = sig_df.tail(window)
    active, missing = [], []

    for key in ind_keys:
        buy_col = f"{key}_Buy"
        if buy_col not in last_n.columns:
            missing.append(key)
            continue
        fired = int(last_n[buy_col].sum()) > 0
        if fired:
            active.append(key)
        else:
            missing.append(key)

    firing = len(active) == len(ind_keys) and len(ind_keys) > 0
    return {'firing': firing, 'active': active, 'missing': missing}


def _run_full_strategy(_df, current_price):
    """Run all strategy engines and return BUY/NO TRADE verdict + price ladder."""
    try:
        from decision_tab import _get_pa_signal, _get_vp_signal, _get_pattern_signal
        from _levels import compute_structural_levels, price_ladder_html
        import pandas as pd

        df = _df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        pa  = _get_pa_signal(df, current_price)
        vp  = _get_vp_signal(df, current_price)
        pat = _get_pattern_signal(df)

        signals = [s for s in [pa, vp, pat] if s is not None]
        buy_count  = sum(1 for s in signals if s.get('signal') == 'BUY')
        wait_count = len(signals) - buy_count

        if buy_count >= 2:
            verdict = 'BUY'; verdict_color = '#26A69A'
        elif buy_count == 1 and wait_count == 0:
            verdict = 'BUY'; verdict_color = '#26A69A'
        else:
            verdict = 'NO TRADE'
            verdict_color = '#ef5350' if wait_count > buy_count else '#FFC107'

        ladder_html = None
        if verdict == 'BUY':
            try:
                lv = compute_structural_levels(df, current_price, True)
                ladder_html = price_ladder_html(
                    lv['entry'], lv['stop'], lv['t1'], lv['t2'], lv['t3'], True,
                    lv.get('entry_quality', ''), lv.get('eq_col', '')
                )
            except Exception:
                pass

        return {
            'verdict': verdict,
            'verdict_color': verdict_color,
            'buy_count': buy_count,
            'total': len(signals),
            'signals': signals,
            'ladder_html': ladder_html,
        }
    except Exception:
        return None


def _render_live_signals(rc_favs: list) -> None:
    """Render Live Signal Check — one block per stock, no repeated info."""
    if not rc_favs:
        return

    st.markdown(
        "<div style='margin:2.4rem 0 1.0rem;display:flex;align-items:center;gap:0.6rem;'>"
        "<div style='width:3px;height:18px;border-radius:2px;background:#26A69A;"
        "box-shadow:0 0 8px #26A69A44;'></div>"
        "<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
        "text-transform:uppercase;letter-spacing:0.8px;'>Live Signal Check</span>"
        "</div>",
        unsafe_allow_html=True)

    # group saved strategies by symbol
    _sym_groups: dict = {}
    for _f in rc_favs:
        _sym = _f.get('symbol', '')
        if _sym not in _sym_groups:
            _sym_groups[_sym] = {'sname': _f.get('stock_name', ''), 'strats': []}
        _sym_groups[_sym]['strats'].append(_f)

    _buy_blocks  = []
    _wait_blocks = []

    for _sym, _sdata in sorted(_sym_groups.items()):
        with st.spinner(f"Analysing {_sym.replace('.SR','')}…"):
            _df, _price = _fetch_df_cached(_sym, '1y')

        if _df is None or _price is None:
            continue

        _result = _run_full_strategy(_df, _price)
        _block = {
            'sym':    _sym,
            'sname':  _sdata['sname'],
            'price':  _price,
            'strats': _sdata['strats'],
            'result': _result,
        }
        if _result and _result['verdict'] == 'BUY':
            _buy_blocks.append(_block)
        else:
            _wait_blocks.append(_block)

    def _render_stock_block(b):
        _res      = b['result']
        _vc       = _res['verdict_color'] if _res else '#555'
        _vt       = _res['verdict']       if _res else 'NO DATA'
        _sym_disp = b['sym'].replace('.SR', '')

        # each saved strategy row
        _rows_html = ''
        for _f in b['strats']:
            _rk    = _f.get('best_regime', 'TREND')
            _rc_   = _REGIME_COLORS.get(_rk, '#a78bfa')
            _ri_   = _REGIME_ICONS.get(_rk, '★')
            _wr    = float(_f.get('win_rate', 0) or 0)
            _pf    = float(_f.get('profit_factor', 0) or 0)
            _ea    = float(_f.get('expectancy', 0) or 0)
            _sig   = int(_f.get('signals', 0) or 0)
            _combo = _f.get('combo_indicators', '—')
            _pl    = (_f.get('period_label', '') or '').split('(')[0].strip()
            _wc_   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
            _ec_   = '#26A69A' if _ea > 0 else '#ef5350'
            _rows_html += (
                f"<div style='padding:0.65rem 1rem;border-bottom:1px solid #181818;'>"
                # first line: regime pill + period + combo name
                f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.45rem;flex-wrap:wrap;'>"
                f"<span style='font-size:0.65rem;font-weight:800;padding:0.15rem 0.55rem;"
                f"border-radius:20px;background:{_rc_};color:#0a0a0a;white-space:nowrap;'>"
                f"{_ri_}&nbsp;{_rk.title()}</span>"
                f"<span style='font-size:0.72rem;color:#505050;white-space:nowrap;'>{_pl}</span>"
                f"<span style='font-size:0.78rem;font-weight:600;color:#888;"
                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;'"
                f" title='{_combo}'>{_combo}</span>"
                f"</div>"
                # second line: stats
                f"<div style='display:flex;gap:1.4rem;flex-wrap:wrap;'>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Win Rate&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:{_wc_};'>{_wr:.0f}%</span></div>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Profit Factor&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:#aaa;'>{_pf:.2f}</span></div>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Expectancy&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:{_ec_};'>{_ea:+.2f}%</span></div>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Signals&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:#666;'>{_sig}</span></div>"
                f"</div>"
                f"</div>"
            )

        _sname_span = (f"<span style='font-size:0.7rem;color:#383838;font-weight:600;'>{b['sname']}</span>"
                       if b['sname'] else '')
        _html = (
            f"<div style='background:#111;border:1px solid #1e1e1e;"
            f"border-left:3px solid {_vc};border-radius:12px;overflow:hidden;"
            f"margin-bottom:0.8rem;'>"
            # header: stock name + verdict
            f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"padding:0.8rem 1rem;border-bottom:1px solid #1a1a1a;'>"
            f"<div style='display:flex;align-items:baseline;gap:0.5rem;'>"
            f"<span style='font-size:1.1rem;font-weight:900;color:#d0d0d0;'>{_sym_disp}</span>"
            f"{_sname_span}</div>"
            f"<span style='font-size:1.3rem;font-weight:900;color:{_vc};'>{_vt}</span>"
            f"</div>"
            # strategy rows
            f"{_rows_html}"
            f"</div>"
        )
        st.markdown(_html, unsafe_allow_html=True)
        if _res and _res['verdict'] == 'BUY' and _res.get('ladder_html'):
            st.markdown(_res['ladder_html'], unsafe_allow_html=True)

    # ── BUY signals ──────────────────────────────────────────────────────────
    if _buy_blocks:
        st.markdown(
            f"<div style='font-size:0.7rem;font-weight:800;color:#26A69A;"
            f"text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.5rem;'>"
            f"BUY Signal &nbsp;({len(_buy_blocks)})</div>",
            unsafe_allow_html=True)
        for _b in _buy_blocks:
            _render_stock_block(_b)

    # ── No Trade ─────────────────────────────────────────────────────────────
    if _wait_blocks:
        st.markdown(
            f"<div style='font-size:0.7rem;font-weight:800;color:#444;"
            f"text-transform:uppercase;letter-spacing:0.8px;margin:1.2rem 0 0.5rem;'>"
            f"Watching &nbsp;({len(_wait_blocks)})</div>",
            unsafe_allow_html=True)
        for _b in _wait_blocks:
            _render_stock_block(_b)


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO SCANNER PAGE  —  fast, all tickers, period filter, 3-col grid
# ══════════════════════════════════════════════════════════════════════════════

def render_auto_scanner_page() -> None:
    from scanner_engine import scan_stock, scan_all_stocks, _REGIME_COLORS, _REGIME_ICONS
    from market_data import get_all_tadawul_tickers

    _PERIODS = ['Short', 'Medium', 'Long']

    _ticker_map = get_all_tadawul_tickers()   # {sym: name}
    _ALL_SYMS   = list(_ticker_map.keys())

    # ── helpers ───────────────────────────────────────────────────────────────
    def _ind_label(inds):
        _D = {'EMA':'EMA 20/50','SMA':'SMA 50/200','RSI':'RSI 14',
              'MACD':'MACD','BB':'Bollinger','STOCH':'Stochastic',
              'ADX':'ADX','CCI':'CCI 20','MFI':'MFI 14',
              'OBV':'OBV','VWAP':'VWAP','WILLR':'Williams %R','ROC':'ROC 12'}
        return ' + '.join(_D.get(k, k) for k in inds)

    def _wr_col(wr):
        return '#26A69A' if wr >= 55 else ('#FFC107' if wr >= 45 else '#ef5350')

    def _price_box(df, price):
        """Return price-ladder HTML or ''."""
        if df is None or price <= 0:
            return ''
        try:
            from _levels import compute_structural_levels
            lv  = compute_structural_levels(df, price, True)
            en  = lv['entry']; st_ = lv['stop']
            t1  = lv['t1'];    t2  = lv['t2']
            rp  = round(abs(en - st_) / en * 100, 1) if en else 0
            t1p = round((t1 - en) / en * 100, 1)     if en else 0
            t2p = round((t2 - en) / en * 100, 1)     if en else 0
            return (
                f"<div class='sc-pb'>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#64b5f6;'></div>"
                f"<div class='sc-pcl'>Entry</div>"
                f"<div class='sc-pcv' style='color:#64b5f6;'>{en:.2f}</div>"
                f"</div>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#ef5350;'></div>"
                f"<div class='sc-pcl'>Stop Loss</div>"
                f"<div class='sc-pcv' style='color:#ef5350;'>{st_:.2f}</div>"
                f"<div class='sc-pcs'>−{rp}%</div>"
                f"</div>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#26A69A;'></div>"
                f"<div class='sc-pcl'>Target 1</div>"
                f"<div class='sc-pcv' style='color:#26A69A;'>{t1:.2f}</div>"
                f"<div class='sc-pcs'>+{t1p}%</div>"
                f"</div>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#66bb6a;'></div>"
                f"<div class='sc-pcl'>Target 2</div>"
                f"<div class='sc-pcv' style='color:#66bb6a;'>{t2:.2f}</div>"
                f"<div class='sc-pcs'>+{t2p}%</div>"
                f"</div>"
                f"</div>"
            )
        except Exception:
            return ''

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    header[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stDecoration"]{display:none!important;}
    .main .block-container,div.block-container{
        max-width:98%!important;padding:1.3rem 1.6rem 5rem!important;}

    /* ── top bar ─────────────────────────────────────────────────────────── */
    .sc-tb{display:flex;align-items:center;gap:1rem;margin-bottom:1.2rem;flex-wrap:wrap;}
    .sc-title{font-size:1.4rem;font-weight:900;color:#e8e8e8;letter-spacing:-0.5px;}
    .sc-sub{font-size:0.62rem;color:#383838;font-weight:600;margin-top:0.1rem;}
    .sc-div{width:1px;height:1.8rem;background:#222;flex-shrink:0;}
    .sc-kv{font-size:1.1rem;font-weight:900;line-height:1.1;}
    .sc-kl{font-size:0.5rem;font-weight:700;color:#333;
           text-transform:uppercase;letter-spacing:1px;margin-top:0.12rem;}

    /* ── back button ─────────────────────────────────────────────────────── */
    .st-key-sc_back .stButton>button{
        background:transparent!important;border:1px solid #252525!important;
        border-radius:8px!important;color:#444!important;
        font-size:0.7rem!important;font-weight:700!important;
        padding:0.38rem 0.9rem!important;min-height:auto!important;
        transition:all .15s!important;}
    .st-key-sc_back .stButton>button:hover{
        border-color:#444!important;color:#888!important;}

    /* ── controls panel ──────────────────────────────────────────────────── */
    .sc-panel{background:#0c0c0c;border:1px solid #1e1e1e;border-radius:12px;
              padding:0.7rem 1rem;margin-bottom:1.2rem;}
    .sc-panel-row{display:flex;align-items:center;gap:0.5rem;
                  flex-wrap:wrap;margin-bottom:0.4rem;}
    .sc-panel-row:last-child{margin-bottom:0;}
    .sc-ctrl-lbl{font-size:0.52rem;font-weight:800;color:#404040;
                 text-transform:uppercase;letter-spacing:1px;
                 white-space:nowrap;min-width:3.2rem;}
    .sc-vsep{width:1px;height:1.2rem;background:#222;flex-shrink:0;margin:0 0.15rem;}

    /* all pill-style filter buttons share this base */
    [class*="st-key-scf_"] .stButton>button,
    [class*="st-key-scs_"] .stButton>button,
    [class*="st-key-scw_"] .stButton>button,
    [class*="st-key-sck_"] .stButton>button{
        background:#0a0a0a!important;border:1px solid #222!important;
        border-radius:20px!important;color:#3a3a3a!important;
        font-size:0.67rem!important;font-weight:800!important;
        min-height:1.65rem!important;padding:0 0.88rem!important;
        transition:all .12s!important;letter-spacing:0.1px!important;}

    /* Period pills — taller, refined, with subtle bg + hover glow */
    [class*="st-key-scp_"] .stButton>button{
        background:linear-gradient(180deg,#0f0f12,#0a0a0c)!important;
        border:1px solid #1f1f24!important;
        border-radius:12px!important;color:#5a5a62!important;
        font-size:0.72rem!important;font-weight:800!important;
        min-height:2.15rem!important;padding:0 1.1rem!important;
        letter-spacing:0.6px!important;text-transform:uppercase!important;
        transition:all .18s ease!important;
        box-shadow:inset 0 1px 0 rgba(255,255,255,0.02)!important;}
    [class*="st-key-scp_"] .stButton>button:hover{
        border-color:rgba(167,139,250,0.30)!important;
        color:#9d8fd8!important;
        background:linear-gradient(180deg,#121017,#0c0a0f)!important;}

    /* active period pill — purple, glowing */
    [class*="st-key-scp_on"] .stButton>button{
        background:linear-gradient(180deg,rgba(167,139,250,0.22),rgba(167,139,250,0.10))!important;
        border-color:rgba(167,139,250,0.55)!important;
        color:#e0d4ff!important;
        box-shadow:0 0 16px rgba(167,139,250,0.18),
                   inset 0 1px 0 rgba(255,255,255,0.06)!important;}

    /* active regime pill — teal */
    [class*="st-key-scf_on"] .stButton>button{
        background:rgba(38,166,154,0.12)!important;
        border-color:rgba(38,166,154,0.40)!important;
        color:#26A69A!important;}

    /* active min-WR pill — amber */
    [class*="st-key-scw_on"] .stButton>button{
        background:rgba(255,193,7,0.10)!important;
        border-color:rgba(255,193,7,0.38)!important;
        color:#FFC107!important;}

    /* active show pill — blue */
    [class*="st-key-scs_on"] .stButton>button{
        background:rgba(100,181,246,0.10)!important;
        border-color:rgba(100,181,246,0.38)!important;
        color:#64b5f6!important;}

    /* active sort pill — pink */
    [class*="st-key-sck_on"] .stButton>button{
        background:rgba(240,98,146,0.10)!important;
        border-color:rgba(240,98,146,0.38)!important;
        color:#f06292!important;}

    /* run scanner button — CTA, prominent gradient + glow */
    .st-key-sc_run .stButton>button{
        background:linear-gradient(135deg,rgba(38,166,154,0.32),rgba(38,166,154,0.14))!important;
        border:1px solid rgba(38,166,154,0.55)!important;
        border-radius:12px!important;color:#bff5ec!important;
        font-size:0.78rem!important;font-weight:900!important;
        min-height:2.15rem!important;padding:0 1.4rem!important;
        letter-spacing:0.8px!important;text-transform:uppercase!important;
        transition:all .18s ease!important;
        box-shadow:0 0 18px rgba(38,166,154,0.18),
                   inset 0 1px 0 rgba(255,255,255,0.08)!important;}
    .st-key-sc_run .stButton>button:hover{
        background:linear-gradient(135deg,rgba(38,166,154,0.45),rgba(38,166,154,0.22))!important;
        border-color:rgba(38,166,154,0.85)!important;
        color:#ffffff!important;
        box-shadow:0 0 26px rgba(38,166,154,0.42),
                   inset 0 1px 0 rgba(255,255,255,0.12)!important;
        transform:translateY(-1px)!important;}
    .st-key-sc_run .stButton>button:active{
        transform:translateY(0)!important;
        box-shadow:0 0 12px rgba(38,166,154,0.30)!important;}

    /* ── stock band (Section 1 — Scanned Strategies) ────────────────────── */
    .sc-band{border:1px solid #222;border-radius:13px;
             overflow:hidden;margin-bottom:0.5rem;background:#0d0d0d;}
    .sc-band-hdr{display:flex;align-items:center;gap:0.7rem;
                 padding:0.7rem 1rem;background:#111;
                 border-bottom:1px solid #1e1e1e;}
    .sc-sym{font-size:1.2rem;font-weight:900;color:#f0f0f0;letter-spacing:-0.3px;}
    .sc-sname{font-size:0.78rem;color:#888;font-weight:600;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:18rem;}
    .sc-ct{margin-left:auto;font-size:0.58rem;color:#404040;font-weight:700;
           background:#181818;border:1px solid #252525;border-radius:6px;
           padding:0.15rem 0.5rem;}

    /* ── regime card (Section 1) ─ calm, spacious, solid-color pills ───── */
    .sc-rpill{font-size:0.6rem;font-weight:800;padding:0.22rem 0.65rem;
              border-radius:6px;white-space:nowrap;flex-shrink:0;
              text-transform:uppercase;letter-spacing:0.6px;color:#0a0a0a;}
    .sc-rcard{border:1px solid #1c1c1c;border-radius:10px;overflow:hidden;
              background:#0c0c0c;height:100%;}
    .sc-rcard-top{display:flex;align-items:center;gap:0.5rem;
                  padding:0.7rem 0.9rem;border-bottom:1px solid #161616;}
    .sc-rcard-inds{padding:0.65rem 0.9rem;border-bottom:1px solid #161616;
                   display:flex;flex-wrap:wrap;gap:0.3rem;}
    .sc-rind-tag{display:inline-block;background:#121212;border:1px solid #1f1f1f;
                 border-radius:5px;padding:0.13rem 0.45rem;
                 font-size:0.62rem;font-weight:700;color:#7a7a7a;letter-spacing:0.1px;}
    .sc-rind-plus{display:inline-flex;align-items:center;justify-content:center;
                  width:13px;height:13px;border-radius:50%;
                  background:rgba(167,139,250,0.10);border:1px solid rgba(167,139,250,0.28);
                  color:#a78bfa;font-size:0.58rem;font-weight:900;line-height:1;
                  margin:0 0.15rem;vertical-align:middle;}
    .sc-rcard-stats{display:grid;grid-template-columns:repeat(3,1fr);}
    .sc-rstat{padding:0.85rem 0.5rem 0.8rem;border-right:1px solid #161616;
              text-align:center;}
    .sc-rstat:last-child{border-right:none;}
    .sc-rstat-v{font-size:1.05rem;font-weight:800;line-height:1;margin-bottom:0.4rem;}
    .sc-rstat-l{font-size:0.6rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.7px;color:#8a8a8a;
                display:inline-flex;align-items:center;gap:0.3rem;}
    .sc-help{display:inline-flex;align-items:center;justify-content:center;
             width:13px;height:13px;border-radius:50%;
             background:#181818;border:1px solid #303030;color:#888;
             font-size:0.55rem;font-weight:900;cursor:help;}
    .sc-help-pill{display:inline-flex;align-items:center;justify-content:center;
                  width:15px;height:15px;border-radius:50%;
                  background:#0c0c0c;border:1px solid #2a2a2a;color:#666;
                  font-size:0.55rem;font-weight:900;cursor:help;
                  transition:all .15s;}
    .sc-help-pill:hover{border-color:rgba(167,139,250,0.45);color:#a78bfa;
                        background:rgba(167,139,250,0.08);}
    .sc-rcard-stats2{display:grid;grid-template-columns:repeat(3,1fr);
                     border-top:1px solid #161616;}
    .sc-rstat2{padding:0.7rem 0.5rem 0.65rem;border-right:1px solid #161616;
               text-align:center;}
    .sc-rstat2:last-child{border-right:none;}
    .sc-rstat2-v{font-size:0.9rem;font-weight:800;line-height:1;margin-bottom:0.35rem;}
    .sc-rstat2-l{font-size:0.58rem;font-weight:700;text-transform:uppercase;
                 letter-spacing:0.7px;color:#8a8a8a;}
    .sc-cempty{font-size:0.62rem;color:#252525;font-weight:700;
               padding:1.6rem 0.65rem;text-align:center;}
    .sc-cfire{display:inline-block;margin-left:auto;font-size:0.6rem;font-weight:800;
              padding:0.22rem 0.6rem;border-radius:6px;
              background:#26A69A;color:#0a0a0a;
              letter-spacing:0.6px;text-transform:uppercase;}

    /* ── section divider ─────────────────────────────────────────────────── */
    .sc-sd{display:flex;align-items:center;gap:0.6rem;margin:2.5rem 0 1rem;}
    .sc-sdl{flex:1;height:1px;background:#191919;}
    .sc-sdp{display:flex;align-items:center;gap:0.45rem;
            background:#0d0d0d;border:1px solid #1e1e1e;
            border-radius:20px;padding:0.28rem 0.88rem;}
    .sc-sdd{width:7px;height:7px;border-radius:50%;}
    .sc-sdlbl{font-size:0.68rem;font-weight:800;color:#b8b8b8;
              text-transform:uppercase;letter-spacing:0.9px;}

    /* ── live pulse ──────────────────────────────────────────────────────── */
    @keyframes lp{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(38,166,154,0.5);}
                  60%{opacity:.5;box-shadow:0 0 0 5px rgba(38,166,154,0);}}
    .sc-live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;
                 background:#26A69A;animation:lp 2s ease-out infinite;flex-shrink:0;}

    /* ── LSC section label ───────────────────────────────────────────────── */
    .lsc-section-hdr{display:flex;align-items:center;gap:1rem;margin:2.8rem 0 1.4rem;}
    .lsc-section-line{flex:1;height:1px;background:linear-gradient(90deg,#1e1e1e,transparent);}
    .lsc-section-line-r{flex:1;height:1px;background:linear-gradient(90deg,transparent,#1e1e1e);}
    .lsc-section-pill{display:flex;align-items:center;gap:0.5rem;white-space:nowrap;
                      background:#0c0c0c;border:1px solid #242424;
                      border-radius:20px;padding:0.35rem 1.1rem;}
    .lsc-section-label{font-size:0.7rem;font-weight:900;color:#c0c0c0;
                       text-transform:uppercase;letter-spacing:1.2px;}
    .lsc-section-count{font-size:0.6rem;font-weight:900;
                       background:rgba(38,166,154,0.15);
                       border:1px solid rgba(38,166,154,0.30);
                       color:#26A69A;border-radius:20px;padding:0.08rem 0.5rem;}

    /* ── signal card ─────────────────────────────────────────────────────── */
    .lsc-card{border-radius:12px;overflow:hidden;margin-bottom:0.7rem;
              background:#0d0d0d;border:1px solid #222;}
    .lsc-card-strip{height:2px;width:100%;}

    /* header */
    .lsc-card-hdr{display:flex;align-items:center;gap:0.65rem;
                  padding:0.65rem 1.1rem;border-bottom:1px solid #1a1a1a;flex-wrap:nowrap;}
    .lsc-ticker{font-size:1.1rem;font-weight:900;color:#f0f0f0;
                letter-spacing:-0.3px;line-height:1;white-space:nowrap;}
    .lsc-co{font-size:1.1rem;font-weight:900;color:#333;white-space:nowrap;
            overflow:hidden;text-overflow:ellipsis;max-width:14rem;
            letter-spacing:-0.3px;line-height:1;}
    .lsc-mkt-badge{font-size:0.62rem;font-weight:900;padding:0.18rem 0.65rem;
                   border-radius:20px;border-width:1px;border-style:solid;
                   text-transform:uppercase;letter-spacing:0.4px;white-space:nowrap;}
    .lsc-best-badge{font-size:0.62rem;font-weight:900;padding:0.18rem 0.65rem;
                    border-radius:20px;border:1px solid #b8860baa;
                    background:linear-gradient(135deg,#b8860b,#8b6508);
                    color:#fff8dc;white-space:nowrap;
                    letter-spacing:0.4px;text-transform:uppercase;
                    box-shadow:0 0 16px #b8860b88,0 0 4px #b8860b66;}

    /* regime rows inside lsc card */
    .lsc-rrow{display:flex;align-items:center;gap:0.6rem;
              padding:0.65rem 1.1rem;border-top:1px solid #181818;
              border-left:2px solid transparent;}
    .lsc-rrow-left{display:flex;align-items:center;gap:0.45rem;flex-wrap:wrap;flex:1;min-width:0;}
    .lsc-rrow-inds{display:flex;flex-wrap:wrap;gap:0.28rem;margin-top:0.3rem;width:100%;}
    .lsc-rrow-stats{display:flex;gap:0;flex-shrink:0;}
    .lsc-rsc{padding:0.4rem 0.7rem;text-align:center;border-left:1px solid #1a1a1a;}
    .lsc-rsv{font-size:0.95rem;font-weight:900;line-height:1;letter-spacing:-0.2px;}
    .lsc-rsl{font-size:0.5rem;font-weight:800;text-transform:uppercase;
             letter-spacing:0.9px;color:#484848;margin-top:0.12rem;}
    .lsc-price-chip{font-size:1.0rem;font-weight:900;color:#26A69A;
                    white-space:nowrap;letter-spacing:-0.2px;}

    /* body */
    .lsc-body{padding:0.7rem 1.1rem 0.85rem;}

    /* indicators row */
    .lsc-top-row{display:flex;align-items:center;gap:0.45rem;
                 flex-wrap:wrap;margin-bottom:0.6rem;}
    .lsc-ind-tag{display:inline-block;background:#141414;border:1px solid #252525;
                 border-radius:6px;padding:0.22rem 0.65rem;
                 font-size:0.78rem;font-weight:700;color:#888;
                 letter-spacing:0.1px;white-space:nowrap;}
    .lsc-ind-plus{display:inline-flex;align-items:center;justify-content:center;
                  width:16px;height:16px;border-radius:50%;
                  background:rgba(167,139,250,0.10);border:1px solid rgba(167,139,250,0.28);
                  color:#a78bfa;font-size:0.7rem;font-weight:900;line-height:1;
                  margin:0 0.18rem;vertical-align:middle;}

    /* stats row */
    .lsc-stats{display:flex;gap:0;border:1px solid #202020;border-radius:9px;
               overflow:hidden;margin-bottom:0.6rem;}
    .lsc-sc{flex:1;padding:0.5rem 0.4rem;text-align:center;
            border-right:1px solid #1a1a1a;background:#0a0a0a;}
    .lsc-sc:last-child{border-right:none;}
    .lsc-sv{font-size:1.0rem;font-weight:900;line-height:1;letter-spacing:-0.2px;}
    .lsc-sl{font-size:0.55rem;font-weight:700;text-transform:uppercase;
            letter-spacing:0.8px;color:#505050;margin-top:0.14rem;}

    /* price ladder */
    .lsc-ladder{display:grid;grid-template-columns:repeat(5,1fr);
                border:1px solid #202020;border-radius:9px;overflow:hidden;}
    .lsc-lc{padding:0.65rem 0.8rem;border-right:1px solid #1a1a1a;
            background:#0a0a0a;position:relative;text-align:left;}
    .lsc-lc:last-child{border-right:none;}
    .lsc-lc-bar{position:absolute;top:0;left:0;right:0;height:3px;}
    .lsc-ll{font-size:0.58rem;font-weight:700;text-transform:uppercase;
            letter-spacing:0.8px;color:#a8a8a8;margin-bottom:0.18rem;}
    .lsc-lv{font-size:1.15rem;font-weight:900;line-height:1;letter-spacing:-0.3px;}
    .lsc-lp{font-size:0.68rem;font-weight:800;margin-top:0.14rem;}

    /* divider sep */
    .sc-sd{display:flex;align-items:center;gap:0.6rem;margin:2.2rem 0 1rem;}
    .sc-sdl{flex:1;height:1px;background:#191919;}
    .sc-sdp{display:flex;align-items:center;gap:0.45rem;
            background:#0d0d0d;border:1px solid #1e1e1e;
            border-radius:20px;padding:0.28rem 0.88rem;}
    .sc-sdd{width:7px;height:7px;border-radius:50%;}
    .sc-sdlbl{font-size:0.68rem;font-weight:800;color:#b8b8b8;
              text-transform:uppercase;letter-spacing:0.9px;}
    </style>
    """, unsafe_allow_html=True)

    # ── session state defaults ────────────────────────────────────────────────
    _SS_DEFS = [
        ('sc_period',  'Medium'),
        ('sc_results', None),
        ('sc_done',    False),
        ('sc_regime',  'All'),       # regime filter
        ('sc_minwr',   0),           # min win-rate filter (0 = off)
        ('sc_show',    'All'),       # All | Firing
        ('sc_sort',    'WinRate'),   # WinRate | Alpha | Firing
    ]
    for _k, _v in _SS_DEFS:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    # ── top bar ───────────────────────────────────────────────────────────────
    _n_res  = len(st.session_state.sc_results or [])
    _n_fire = sum(
        1 for row in (st.session_state.sc_results or [])
        if any((v or {}).get('firing')
               for v in (row.get('regimes') or {}).values())
    )
    _tl, _tr = st.columns([1, 0.12])
    with _tl:
        st.markdown(
            "<div class='sc-tb'>"
            "<div><div class='sc-title'>Strategy Scanner</div>"
            "<div class='sc-sub'>All Tadawul stocks · best combo per regime · auto</div></div>"
            "<div class='sc-div'></div>"
            f"<div><div class='sc-kv' style='color:#a78bfa;'>{len(_ALL_SYMS)}</div>"
            f"<div class='sc-kl'>Stocks</div></div>"
            "<div class='sc-div'></div>"
            f"<div><div class='sc-kv' style='color:#606060;'>{_n_res}</div>"
            f"<div class='sc-kl'>Scanned</div></div>"
            "<div class='sc-div'></div>"
            f"<div><div class='sc-kv' style='color:#26A69A;'>{_n_fire}</div>"
            f"<div class='sc-kl'>Firing</div></div>"
            "</div>",
            unsafe_allow_html=True)
    with _tr:
        with st.container(key="sc_back"):
            if st.button("← Back", key="sc_back_btn", use_container_width=True):
                st.session_state.show_champions_vault = False
                st.rerun()

    # ── controls panel ────────────────────────────────────────────────────────
    def _pill_row(label, options, state_key, prefix, reset_scan=False,
                  extra_cols=None):
        """Render a labeled row of pill buttons. Returns True if any clicked."""
        _cur = st.session_state[state_key]
        _n   = len(options)
        _widths = [0.42] + [0.65] * _n + (extra_cols or [])
        _cols = st.columns(_widths, gap="small")
        with _cols[0]:
            st.markdown(
                f"<div class='sc-ctrl-lbl' style='line-height:1.65rem;'>{label}</div>",
                unsafe_allow_html=True)
        for _i, (_lbl, _val) in enumerate(options):
            _active = 'on' if _cur == _val else f'off{_i}'
            with _cols[_i + 1]:
                with st.container(key=f"{prefix}_{_active}_{_i}"):
                    if st.button(_lbl, key=f"{prefix}_btn_{_val}",
                                 use_container_width=True):
                        st.session_state[state_key] = _val
                        if reset_scan:
                            st.session_state.sc_results = None
                            st.session_state.sc_done    = False
                        st.rerun()
        return _cols

    st.markdown("<div class='sc-panel'>", unsafe_allow_html=True)

    # Period tooltips
    _PERIOD_HELP = {
        'Short':  ('Short = ~3 months of daily data. Best for swing/momentum signals '
                   'that trigger within days. Highest signal frequency, more noise.'),
        'Medium': ('Medium = ~9 months of daily data. Balanced timeframe — captures '
                   'multi-week trends and most regime shifts. The recommended default.'),
        'Long':   ('Long = ~2 years of daily data. Best for stable, slow-moving '
                   'strategies. Fewer signals but each one is statistically stronger.'),
    }
    _PERIOD_LBL_HELP = ("Choose how much historical data to scan. Short = ~3 months, "
                        "Medium = ~9 months, Long = ~2 years. Longer periods give "
                        "more reliable stats but slower-moving signals.")
    _SCAN_HELP = ("Run the scanner across all Tadawul symbols for the selected period. "
                  "Recomputes regime, fits strategies, and detects which ones are "
                  "currently firing.")

    # Row 1: Period  +  vsep  +  ↻ Scan
    st.markdown("<div class='sc-panel-row'>", unsafe_allow_html=True)
    _r1 = st.columns([0.42, 0.65, 0.65, 0.65, 0.08, 0.75], gap="small")
    with _r1[0]:
        st.markdown(
            f"<div class='sc-ctrl-lbl' style='line-height:2.15rem;"
            f"display:inline-flex;align-items:center;gap:0.3rem;'>"
            f"Period"
            f"<span class='sc-help-pill' title='{_PERIOD_LBL_HELP}'>?</span>"
            f"</div>",
            unsafe_allow_html=True)
    for _pi, _po in enumerate(_PERIODS):
        _pk = 'scp_on' if st.session_state.sc_period == _po else f'scp_off{_pi}'
        with _r1[_pi + 1]:
            with st.container(key=f"{_pk}_{_pi}"):
                if st.button(_po, key=f"scp_{_po}", use_container_width=True,
                             help=_PERIOD_HELP.get(_po)):
                    st.session_state.sc_period  = _po
                    st.session_state.sc_results = None
                    st.session_state.sc_done    = False
                    st.rerun()
    with _r1[4]:
        st.markdown("<div class='sc-vsep'></div>", unsafe_allow_html=True)
    with _r1[5]:
        with st.container(key="sc_run"):
            if st.button("↻  Scan", key="sc_run_btn", use_container_width=True,
                         help=_SCAN_HELP):
                st.session_state.sc_results = None
                st.session_state.sc_done    = False
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # end sc-panel

    # ── scan ─────────────────────────────────────────────────────────────────
    _sel_period = st.session_state.sc_period

    if not st.session_state.sc_done:
        from scanner_engine import scan_all_stocks
        _out  = []
        _prog = st.progress(0, text="Downloading market data…")
        _prog.progress(0.05, text="Downloading all Tadawul data in one request…")
        _batch = scan_all_stocks(tuple(_ALL_SYMS), _sel_period, _v=18)
        _prog.progress(0.6, text="Analysing strategies…")
        _tot = len(_ALL_SYMS)
        for _i, _sym in enumerate(_ALL_SYMS):
            _data = _batch.get(_sym)
            if _data:
                _data['_sym']   = _sym
                _data['_sname'] = _ticker_map.get(_sym, '')
                _out.append(_data)
            if _i % 20 == 0:
                _prog.progress(0.6 + 0.38 * (_i + 1) / _tot,
                               text=f"Analysing {_sym.replace('.SR','')} ({_i+1}/{_tot})")
        _prog.empty()
        st.session_state.sc_results      = _out
        st.session_state.sc_done         = True
        st.session_state.sc_show_all_strats = False
        st.rerun()

    _rows_all = st.session_state.sc_results or []
    if not _rows_all:
        st.markdown(
            "<div style='background:#0d0d0d;border:1px solid #1a1a1a;"
            "border-radius:12px;padding:4rem 2rem;text-align:center;'>"
            "<div style='font-size:1rem;font-weight:800;color:#2a2a2a;'>"
            "No results — tap ↻ Scan</div></div>",
            unsafe_allow_html=True)
        return

    def _best_wr(row):
        regs = row.get('regimes') or {}
        vals = [float(cb.get('win_rate', 0) or 0) for cb in regs.values() if cb]
        return max(vals) if vals else 0.0

    def _has_firing(row):
        regs = row.get('regimes') or {}
        return any((cb or {}).get('firing') for cb in regs.values())

    # Drop stocks with no qualifying combo in any regime — empty cards are noise.
    _rows = [r for r in _rows_all
             if any((r.get('regimes') or {}).get(_rn) for _rn in ('TREND', 'RANGE', 'VOLATILE'))]

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Scanned Strategy Grid
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:0.7rem;"
        f"margin-bottom:0.9rem;'>"
        f"<span style='font-size:0.95rem;font-weight:900;color:#d0d0d0;letter-spacing:-0.2px;'>"
        f"Scanned Strategies</span>"
        f"<span style='font-size:0.55rem;color:#666;font-weight:700;"
        f"background:#0c0c0c;border:1px solid #1e1e1e;border-radius:50%;"
        f"width:15px;height:15px;display:inline-flex;align-items:center;"
        f"justify-content:center;cursor:help;' "
        f"title='All scanned stocks. Use the search to filter by symbol or company name.'>?</span>"
        f"<span style='font-size:0.6rem;color:#2e2e2e;margin-left:auto;font-weight:700;'>"
        f"{len(_rows)} stocks</span>"
        f"</div>",
        unsafe_allow_html=True)

    # ── dark search bar ──────────────────────────────────────────────────────
    st.markdown(
        "<style>"
        ".st-key-sc_search_box .stTextInput>div>div>input{"
        "background:#080808!important;border:1px solid #1e1e1e!important;"
        "border-radius:10px!important;color:#d0d0d0!important;"
        "font-size:0.78rem!important;font-weight:600!important;"
        "padding:0.55rem 0.9rem!important;letter-spacing:0.2px!important;"
        "transition:all .15s!important;}"
        ".st-key-sc_search_box .stTextInput>div>div>input::placeholder{"
        "color:#3a3a3a!important;font-weight:600!important;}"
        ".st-key-sc_search_box .stTextInput>div>div>input:focus{"
        "border-color:rgba(167,139,250,0.45)!important;"
        "box-shadow:0 0 0 1px rgba(167,139,250,0.20)!important;}"
        "</style>",
        unsafe_allow_html=True)
    with st.container(key="sc_search_box"):
        _sc_query = st.text_input(
            " ", placeholder="🔍  Search symbol or company name…",
            key="sc_search_q", label_visibility="collapsed")
    _sc_q = (_sc_query or '').strip().lower()
    if _sc_q:
        _rows = [r for r in _rows
                 if _sc_q in r['_sym'].replace('.SR', '').lower()
                 or _sc_q in (r.get('_sname') or '').lower()]

    _PREVIEW_COUNT = 5
    _show_all_key  = 'sc_show_all_strats'
    if _show_all_key not in st.session_state:
        st.session_state[_show_all_key] = False

    _rows_to_show = _rows if st.session_state[_show_all_key] else _rows[:_PREVIEW_COUNT]

    for _row in _rows_to_show:
        _sym   = _row['_sym']
        _sname = _row['_sname']
        _sym_d = _sym.replace('.SR', '')
        _regs  = _row.get('regimes', {})
        _n_ok  = sum(1 for v in _regs.values() if v)
        _has_fire = any((v or {}).get('firing') for v in _regs.values())

        st.markdown(
            f"<div class='sc-band'>"
            f"<div class='sc-band-hdr'>"
            f"<span class='sc-sym'>{_sym_d}</span>"
            + (f"<span class='sc-sname'>{_sname}</span>" if _sname else '')
            + (
                "<span style='margin-left:auto;font-size:0.52rem;font-weight:900;"
                "padding:0.12rem 0.5rem;border-radius:20px;"
                "background:rgba(38,166,154,0.13);border:1px solid rgba(38,166,154,0.38);"
                "color:#26A69A;letter-spacing:0.5px;'>● FIRING</span>"
                if _has_fire else
                f"<span class='sc-ct'>{_n_ok}/3 regimes</span>"
            )
            + f"</div></div>",
            unsafe_allow_html=True)

        _PF_HELP  = ("Profit Factor = total $ won ÷ total $ lost across all past "
                     "signals. 1.0 = breakeven, 2.0+ = strong, 3.0+ = exceptional.")
        _EXP_HELP = ("Expectancy = average % return per signal. +1.5% means each "
                     "signal on average gained 1.5%. Negative = losing strategy.")
        _REGIME_HELP = {
            'TREND':    ('Trending regime — directional, sustained price moves. '
                         'Best for momentum/breakout strategies.'),
            'RANGE':    ('Ranging regime — price oscillates between support and '
                         'resistance. Best for mean-reversion strategies.'),
            'VOLATILE': ('Volatile regime — large unpredictable swings. Hardest '
                         'to trade; strategies here use wider stops.'),
        }

        for _rname, _col in zip(('TREND','RANGE','VOLATILE'), st.columns(3, gap="small")):
            _combo  = _regs.get(_rname)
            _rc_col = _REGIME_COLORS.get(_rname, '#888')
            with _col:
                _rg_tip = _REGIME_HELP.get(_rname, '')
                if not _combo:
                    st.markdown(
                        f"<div class='sc-rcard'>"
                        f"<div class='sc-rcard-top'>"
                        f"<span class='sc-rpill' style='background:#181818;color:#2a2a2a;'>"
                        f"{_rname.title()}</span>"
                        f"<span class='sc-help-pill' title='{_rg_tip}'"
                        f" style='margin-left:0.3rem;'>?</span>"
                        f"</div>"
                        f"<div class='sc-cempty'>—</div>"
                        f"</div>",
                        unsafe_allow_html=True)
                    continue

                _wr     = float(_combo.get('win_rate', 0) or 0)
                _pf     = float(_combo.get('profit_factor', 0) or 0)
                _exp    = float(_combo.get('expectancy', 0) or 0)
                _tot    = int(_combo.get('total', 0) or 0)
                _wins   = int(_combo.get('wins', 0) or 0)
                _losses = int(_combo.get('losses', 0) or 0)
                _inds   = _combo.get('indicators', [])
                _fire   = _combo.get('firing', False)
                _wc     = _wr_col(_wr)
                _exp_c  = '#26A69A' if _exp > 0 else '#ef5350'
                _ind_tags = "<span class='sc-rind-plus'>+</span>".join(
                    f"<span class='sc-rind-tag'>{_ind_label([k])}</span>"
                    for k in _inds)

                st.markdown(
                    f"<div class='sc-rcard'>"
                    f"<div class='sc-rcard-top'>"
                    # Solid color-filled regime pill — no icon
                    f"<span class='sc-rpill' style='background:{_rc_col};'>"
                    f"{_rname.title()}</span>"
                    f"<span class='sc-help-pill' title='{_rg_tip}'"
                    f" style='margin-left:0.1rem;'>?</span>"
                    + (f"<span class='sc-cfire'>FIRING</span>" if _fire else '')
                    + f"</div>"
                    f"<div class='sc-rcard-inds'>{_ind_tags}</div>"
                    # Primary row: Win Rate · Profit Factor · Expectancy
                    f"<div class='sc-rcard-stats'>"
                    f"<div class='sc-rstat'>"
                    f"<div class='sc-rstat-v' style='color:{_wc};'>{_wr:.0f}%</div>"
                    f"<div class='sc-rstat-l'>Win Rate</div></div>"
                    f"<div class='sc-rstat'>"
                    f"<div class='sc-rstat-v' style='color:#a78bfa;'>{_pf:.1f}×</div>"
                    f"<div class='sc-rstat-l'>Profit Factor"
                    f"<span class='sc-help' title='{_PF_HELP}'>?</span></div></div>"
                    f"<div class='sc-rstat'>"
                    f"<div class='sc-rstat-v' style='color:{_exp_c};'>{_exp:+.1f}%</div>"
                    f"<div class='sc-rstat-l'>Expectancy"
                    f"<span class='sc-help' title='{_EXP_HELP}'>?</span></div></div>"
                    f"</div>"
                    # Secondary row: Wins · Losses · Total
                    f"<div class='sc-rcard-stats2'>"
                    f"<div class='sc-rstat2'>"
                    f"<div class='sc-rstat2-v' style='color:#26A69A;'>{_wins}</div>"
                    f"<div class='sc-rstat2-l'>Wins</div></div>"
                    f"<div class='sc-rstat2'>"
                    f"<div class='sc-rstat2-v' style='color:#ef5350;'>{_losses}</div>"
                    f"<div class='sc-rstat2-l'>Losses</div></div>"
                    f"<div class='sc-rstat2'>"
                    f"<div class='sc-rstat2-v' style='color:#a0a0a0;'>{_tot}</div>"
                    f"<div class='sc-rstat2-l'>Total</div></div>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True)

    # ── expand / collapse button for Section 1 ────────────────────────────
    if len(_rows) > _PREVIEW_COUNT:
        _remaining = len(_rows) - _PREVIEW_COUNT
        _btn_label = (
            f"Show all {len(_rows)} stocks  ↓"
            if not st.session_state[_show_all_key]
            else "Show less ↑"
        )
        st.markdown(
            "<style>"
            ".st-key-sc_expand_strats .stButton>button{"
            "background:transparent!important;border:1px solid #252525!important;"
            "border-radius:8px!important;color:#404040!important;"
            "font-size:0.68rem!important;font-weight:800!important;"
            "width:100%!important;padding:0.5rem!important;"
            "letter-spacing:0.4px!important;margin-bottom:0.5rem!important;"
            "transition:all .15s!important;}"
            ".st-key-sc_expand_strats .stButton>button:hover{"
            "border-color:#383838!important;color:#686868!important;}"
            "</style>",
            unsafe_allow_html=True)
        if st.button(_btn_label, key="sc_expand_strats"):
            st.session_state[_show_all_key] = not st.session_state[_show_all_key]
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Live Signal Check
    # ══════════════════════════════════════════════════════════════════════════
    import math as _math

    _REGIME_SHORT = {'TREND': 'Trend', 'RANGE': 'Range', 'VOLATILE': 'Volatile'}
    _IND_SHORT    = {'EMA':'EMA','SMA':'SMA','RSI':'RSI','MACD':'MACD',
                     'BB':'BB','STOCH':'Stoch','ADX':'ADX','CCI':'CCI',
                     'MFI':'MFI','OBV':'OBV','VWAP':'VWAP','WILLR':'W%R','ROC':'ROC'}

    # Only include stocks whose CURRENT regime's strategy is firing.
    def _cur_regime_firing(row):
        regs = row.get('regimes', {}) or {}
        cur  = row.get('current_regime', 'RANGE')
        return bool((regs.get(cur) or {}).get('firing'))

    _fire_rows_raw = [r for r in _rows if _cur_regime_firing(r)]

    def _lsc_score(row):
        regs = row.get('regimes', {}) or {}
        cur  = row.get('current_regime', 'RANGE')
        cb   = regs.get(cur) or {}
        wr   = float(cb.get('win_rate', 0) or 0)
        tot  = int(cb.get('total', 1) or 1)
        return wr * _math.sqrt(tot)

    def _lsc_bars_ago(row):
        """How many bars ago the firing strategy last triggered. Lower = newer."""
        try:
            import numpy as _np_b
            from scanner_engine import get_stock_df as _gsd_b, _build_states as _bs_b
            _df_b = _gsd_b(row['_sym'], _sel_period, _v=2)
            if _df_b is None or len(_df_b) < 21:
                return 10**9
            _cur_b = row.get('current_regime', 'RANGE')
            _cb_b  = (row.get('regimes', {}) or {}).get(_cur_b) or {}
            _inds_b = _cb_b.get('indicators', [])
            _st_b  = _bs_b(_df_b)
            if not _inds_b or not all(k in _st_b for k in _inds_b):
                return 10**9
            _ca = _st_b[_inds_b[0]].copy()
            for _ik in _inds_b[1:]:
                _ca = _ca & _st_b[_ik]
            _N = len(_df_b)
            _ed = _np_b.zeros(_N, dtype=_np_b.int8)
            _ed[1:] = ((_ca[1:] == 1) & (_ca[:-1] == 0)).astype(_np_b.int8)
            _f = _np_b.where(_ed == 1)[0]
            return (_N - 1 - int(_f[-1])) if len(_f) else 10**9
        except Exception:
            return 10**9

    # ── sort selector ────────────────────────────────────────────────────────
    if 'lsc_sort' not in st.session_state:
        st.session_state.lsc_sort = 'score'

    if st.session_state.lsc_sort == 'newest':
        _fire_rows = sorted(_fire_rows_raw, key=_lsc_bars_ago)
    else:
        _fire_rows = sorted(_fire_rows_raw, key=_lsc_score, reverse=True)
    _n_signals = len(_fire_rows)

    _LSC_HELP = ("Live Signal Check shows only stocks where the CURRENT market regime's "
                 "best strategy is firing right now. The colored chip indicates how "
                 "fresh the signal is — green = today, amber = recent, red = stale.")
    # section header  +  sort pills
    st.markdown(
        f"<div class='lsc-section-hdr'>"
        f"<div class='lsc-section-line'></div>"
        f"<div class='lsc-section-pill'>"
        f"<span class='sc-live-dot'></span>"
        f"<span class='lsc-section-label'>Live Signal Check</span>"
        f"<span class='sc-help-pill' title='{_LSC_HELP}'>?</span>"
        + (f"<span class='lsc-section-count'>{_n_signals}</span>" if _n_signals else '')
        + f"</div>"
        f"<div class='lsc-section-line-r'></div>"
        f"</div>",
        unsafe_allow_html=True)

    if _n_signals:
        st.markdown(
            "<style>"
            "[class*='st-key-lscsort_'] .stButton>button{"
            "background:#0a0a0a!important;border:1px solid #222!important;"
            "border-radius:18px!important;color:#5a5a5a!important;"
            "font-size:0.6rem!important;font-weight:800!important;"
            "min-height:1.5rem!important;padding:0 0.85rem!important;"
            "letter-spacing:0.4px!important;text-transform:uppercase!important;"
            "transition:all .12s!important;}"
            "[class*='st-key-lscsort_on'] .stButton>button{"
            "background:rgba(38,166,154,0.13)!important;"
            "border-color:rgba(38,166,154,0.40)!important;"
            "color:#26A69A!important;}"
            ".lsc-sort-lbl{font-size:0.55rem;font-weight:800;color:#444;"
            "text-transform:uppercase;letter-spacing:1px;line-height:1.5rem;}"
            "</style>",
            unsafe_allow_html=True)
        _sr = st.columns([0.18, 0.20, 0.22, 0.40], gap="small")
        with _sr[0]:
            st.markdown("<div class='lsc-sort-lbl'>Sort by</div>", unsafe_allow_html=True)
        with _sr[1]:
            _k1 = 'lscsort_on_score' if st.session_state.lsc_sort == 'score' else 'lscsort_off_score'
            with st.container(key=_k1):
                if st.button("Best fit", key="lscsort_btn_score", use_container_width=True):
                    st.session_state.lsc_sort = 'score'
                    st.rerun()
        with _sr[2]:
            _k2 = 'lscsort_on_newest' if st.session_state.lsc_sort == 'newest' else 'lscsort_off_newest'
            with st.container(key=_k2):
                if st.button("Newest", key="lscsort_btn_newest", use_container_width=True):
                    st.session_state.lsc_sort = 'newest'
                    st.rerun()

    if not _fire_rows:
        st.markdown(
            "<div style='background:#0c0c0c;border:1px solid #1e1e1e;"
            "border-radius:14px;padding:3rem;text-align:center;'>"
            "<div style='font-size:0.75rem;font-weight:800;color:#2e2e2e;"
            "text-transform:uppercase;letter-spacing:1.2px;'>No best-fit signals</div>"
            "<div style='font-size:0.62rem;color:#222;margin-top:0.4rem;'>"
            "No stock's current-regime strategy is firing right now</div></div>",
            unsafe_allow_html=True)
    else:
        # chart expand state
        if 'lsc_chart_open' not in st.session_state:
            st.session_state.lsc_chart_open = {}

        for _ri in range(0, len(_fire_rows), 2):
            _pair = _fire_rows[_ri:_ri + 2]
            _grid = st.columns(len(_pair), gap="medium")
            for _col_slot, _row in zip(_grid, _pair):
             with _col_slot:
              _sym        = _row['_sym']
              _sname      = _row['_sname']
              _sym_d      = _sym.replace('.SR', '')
              _regs       = _row.get('regimes', {})
              _price      = float(_row.get('price', 0) or 0)
              _cur_regime = _row.get('current_regime', 'RANGE')
              from scanner_engine import get_stock_df as _gsd
              _df_f       = _gsd(_sym, _sel_period, _v=2)

              _firing_regimes = [rn for rn in ('TREND','RANGE','VOLATILE')
                                 if (_regs.get(rn) or {}).get('firing')]
              # Only surface the stock when its CURRENT regime's strategy is firing.
              # If the stock is in TREND and TREND is firing → show it. Otherwise
              # skip (do not advertise off-regime firings).
              if _cur_regime not in _firing_regimes:
                  continue

              _best_rname = _cur_regime
              _best_combo = (_regs.get(_best_rname) or {})
              _best_col   = _REGIME_COLORS.get(_best_rname, '#888')
              _wr     = float(_best_combo.get('win_rate', 0) or 0)
              _tot    = int(_best_combo.get('total', 0) or 0)
              _wins   = int(_best_combo.get('wins', 0) or 0)
              _losses = int(_best_combo.get('losses', 0) or 0)
              _inds   = _best_combo.get('indicators', [])
              _wc     = _wr_col(_wr)

              # price ladder
              _ladder = ''; _en = _sl_p = _t1 = _t2 = 0.0
              if _df_f is not None and _price > 0:
                  try:
                      from _levels import compute_structural_levels
                      _lv   = compute_structural_levels(_df_f, _price, True)
                      _en   = _lv['entry']; _sl_p = _lv['stop']
                      _t1   = _lv['t1'];    _t2   = _lv['t2']
                      _eq   = _lv.get('entry_quality', '')
                      _eqc  = _lv.get('eq_col', '#64b5f6')
                      _rp   = round(abs(_en - _sl_p) / _en * 100, 1) if _en else 0
                      _t1p  = round((_t1 - _en) / _en * 100, 1) if _en else 0
                      _t2p  = round((_t2 - _en) / _en * 100, 1) if _en else 0
                      _rr   = round(_t1p / _rp, 2) if _rp else 0
                      _rr_c = ('#FFD700' if _rr >= 2 else '#26A69A' if _rr >= 1.5 else '#ef5350')
                      # tooltip text per quality level
                      _eq_tips = {
                          'OPTIMAL':  'Price is right at structural support — best possible entry. Low risk of stop hunt.',
                          'GOOD':     'Price is near support but slightly extended. Still a valid entry with manageable risk.',
                          'ELEVATED': 'Price has moved away from support. Risk is higher — consider waiting for a pullback.',
                          'CHASING':  'Price is far from support. Entering here risks a large stop or getting caught in a reversal.',
                      }
                      _eq_tip = _eq_tips.get(_eq, '')
                      _eq_html = (
                          f"<div class='lsc-lp' style='color:{_eqc};display:flex;"
                          f"align-items:center;gap:0.2rem;'>"
                          f"{_eq}"
                          f"<span title='{_eq_tip}' style='display:inline-flex;align-items:center;"
                          f"justify-content:center;width:13px;height:13px;border-radius:50%;"
                          f"background:#1e1e1e;border:1px solid #333;color:#555;"
                          f"font-size:0.5rem;font-weight:900;cursor:help;flex-shrink:0;'>?</span>"
                          f"</div>"
                      ) if _eq else ''
                      _ladder = (
                          f"<div class='lsc-ladder'>"
                          f"<div class='lsc-lc'><div class='lsc-lc-bar' style='background:{_eqc};'></div>"
                          f"<div class='lsc-ll'>Entry</div>"
                          f"<div class='lsc-lv' style='color:#64b5f6;'>{_en:.2f}</div>"
                          f"{_eq_html}</div>"
                          f"<div class='lsc-lc'><div class='lsc-lc-bar' style='background:#26A69A;'></div>"
                          f"<div class='lsc-ll'>Target 1</div>"
                          f"<div class='lsc-lv' style='color:#26A69A;'>{_t1:.2f}</div>"
                          f"<div class='lsc-lp' style='color:#26A69A;'>+{_t1p}%</div></div>"
                          f"<div class='lsc-lc'><div class='lsc-lc-bar' style='background:#66bb6a;'></div>"
                          f"<div class='lsc-ll'>Target 2</div>"
                          f"<div class='lsc-lv' style='color:#66bb6a;'>{_t2:.2f}</div>"
                          f"<div class='lsc-lp' style='color:#66bb6a;'>+{_t2p}%</div></div>"
                          f"<div class='lsc-lc'><div class='lsc-lc-bar' style='background:#ef5350;'></div>"
                          f"<div class='lsc-ll'>Stop Loss</div>"
                          f"<div class='lsc-lv' style='color:#ef5350;'>{_sl_p:.2f}</div>"
                          f"<div class='lsc-lp' style='color:#ef5350;'>−{_rp}%</div></div>"
                          f"<div class='lsc-lc' style='border-right:none;'>"
                          f"<div class='lsc-lc-bar' style='background:{_rr_c};'></div>"
                          f"<div class='lsc-ll'>Risk:Reward</div>"
                          f"<div class='lsc-lv' style='color:{_rr_c};'>1 : {_rr}</div>"
                          f"<div class='lsc-lp' style='color:{_rr_c};'>"
                          f"{'★ Great' if _rr >= 2 else 'Good' if _rr >= 1.5 else 'Weak'}"
                          f"</div></div>"
                          f"</div>")
                  except Exception:
                      pass

              # ── Compute "when did this strategy fire" (date + time) ───────
              # Used inline next to the indicators row. No volume/trend/earnings
              # context badges — the user only cares about the signal itself.
              _fire_when_txt = ''
              _fire_when_c   = '#FFD700'
              if _df_f is not None and len(_df_f) >= 21:
                  try:
                      import numpy as _np2
                      from scanner_engine import _build_states as _bs2
                      _st2 = _bs2(_df_f)
                      _N2 = len(_df_f)
                      if _inds and all(k in _st2 for k in _inds):
                          _ca2 = _st2[_inds[0]].copy()
                          for _ik2 in _inds[1:]:
                              _ca2 = _ca2 & _st2[_ik2]
                          _ed2 = _np2.zeros(_N2, dtype=_np2.int8)
                          _ed2[1:] = ((_ca2[1:] == 1) & (_ca2[:-1] == 0)).astype(_np2.int8)
                          _fires2 = _np2.where(_ed2 == 1)[0]
                          if len(_fires2):
                              _last_fire_i = int(_fires2[-1])
                              _bars_ago    = _N2 - 1 - _last_fire_i
                              # daily bars — show date + close-time (15:00 KSA)
                              _fire_ts = (_df_f['Date'].iloc[_last_fire_i]
                                          if 'Date' in _df_f.columns else None)
                              _fire_date_s = (str(_fire_ts)[:10]
                                              if _fire_ts is not None else '')
                              _label = ('Today' if _bars_ago == 0 else
                                        '1 day ago' if _bars_ago == 1 else
                                        f'{_bars_ago} days ago')
                              # KSA market close is 15:00; daily bar closes then
                              _fire_when_txt = (f"{_label} · {_fire_date_s} 15:00"
                                                if _fire_date_s else _label)
                              # Today=green (fresh), 1d=teal, ≤5d=amber, >5d=red
                              _fire_when_c = ('#26A69A' if _bars_ago == 0 else
                                              '#8BC34A' if _bars_ago == 1 else
                                              '#FFC107' if _bars_ago <= 5 else
                                              '#ef5350')
                              # expose bars_ago to outer scope for sorting
                              _row['_lsc_bars_ago'] = _bars_ago
                  except Exception:
                      pass

              # indicator tags
              _ind_tags = "<span class='lsc-ind-plus'>+</span>".join(
                  f"<span class='lsc-ind-tag'>{_IND_SHORT.get(k, k)}</span>"
                  for k in _inds)

              # rank medal color
              # firing-time chip (solid-color filled, dark text)
              _fire_chip = (
                  f"<span style='margin-left:auto;font-size:0.6rem;font-weight:800;"
                  f"padding:0.22rem 0.6rem;border-radius:6px;"
                  f"background:{_fire_when_c};color:#0a0a0a;"
                  f"text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;'>"
                  f"{_fire_when_txt}</span>"
              ) if _fire_when_txt else ''

              # tooltip help text (shared with Scanned Strategies)
              _PF_HELP_L  = ("Profit Factor = total $ won ÷ total $ lost across all past "
                             "signals. 1.0 = breakeven, 2.0+ = strong.")
              _EXP_HELP_L = ("Expectancy = average % return per signal. "
                             "+1.5% means each signal gained 1.5% on average.")

              # ── main card — calm, no gradients/glows, no #rank ────────────
              st.markdown(
                  f"<div style='background:#0c0c0c;border:1px solid #1c1c1c;"
                  f"border-radius:10px;overflow:hidden;margin-bottom:0.1rem;'>"
                  # header row: symbol · name · best-fit pill (color-filled) · price
                  f"<div style='display:flex;align-items:center;gap:0.7rem;"
                  f"padding:0.75rem 0.95rem;border-bottom:1px solid #161616;"
                  f"flex-wrap:nowrap;'>"
                  f"<span style='font-size:1.05rem;font-weight:800;color:#ececec;"
                  f"letter-spacing:-0.2px;white-space:nowrap;'>{_sym_d}</span>"
                  + (f"<span style='font-size:0.65rem;color:#666;font-weight:600;"
                     f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
                     f"max-width:11rem;'>{_sname}</span>" if _sname else '')
                  + f"<span style='font-size:0.6rem;font-weight:800;padding:0.22rem 0.65rem;"
                  f"border-radius:6px;background:{_best_col};color:#0a0a0a;"
                  f"letter-spacing:0.5px;white-space:nowrap;flex-shrink:0;"
                  f"text-transform:uppercase;'>"
                  f"{_best_rname.title()} · Best Fit</span>"
                  + f"<span style='margin-left:auto;font-size:1.05rem;font-weight:800;"
                  f"color:#26A69A;white-space:nowrap;flex-shrink:0;'>{_price:.2f}"
                  f"<span style='font-size:0.55rem;color:#3a6660;font-weight:700;"
                  f"margin-left:0.3rem;letter-spacing:0.5px;'>SAR</span></span>"
                  f"</div>"
                  # Strategy row: label · indicators · firing-time
                  f"<div style='padding:0.65rem 0.95rem;border-bottom:1px solid #161616;"
                  f"display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;'>"
                  f"<span style='font-size:0.6rem;font-weight:700;color:#8a8a8a;"
                  f"text-transform:uppercase;letter-spacing:0.7px;margin-right:0.2rem;"
                  f"display:inline-flex;align-items:center;gap:0.3rem;'>"
                  f"Strategy"
                  f"<span class='sc-help-pill' title='The combination of technical "
                  f"indicators (joined with +) that all must agree before the strategy "
                  f"fires. The chip on the right shows when the most recent fire happened.'>?</span>"
                  f"</span>"
                  f"{_ind_tags}"
                  f"{_fire_chip}"
                  f"</div>"
                  # Stats row: Win Rate · Wins · Losses · Total
                  f"<div style='display:grid;grid-template-columns:repeat(4,1fr);'>"
                  # Win Rate
                  f"<div style='padding:0.85rem 0.5rem 0.8rem;text-align:center;"
                  f"border-right:1px solid #161616;'>"
                  f"<div style='font-size:1.15rem;font-weight:800;line-height:1;"
                  f"color:{_wc};margin-bottom:0.4rem;'>{_wr:.0f}%</div>"
                  f"<div style='font-size:0.6rem;font-weight:700;color:#8a8a8a;"
                  f"text-transform:uppercase;letter-spacing:0.7px;'>Win Rate</div></div>"
                  # Wins
                  f"<div style='padding:0.85rem 0.5rem 0.8rem;text-align:center;"
                  f"border-right:1px solid #161616;'>"
                  f"<div style='font-size:1.15rem;font-weight:800;line-height:1;"
                  f"color:#26A69A;margin-bottom:0.4rem;'>{_wins}</div>"
                  f"<div style='font-size:0.6rem;font-weight:700;color:#8a8a8a;"
                  f"text-transform:uppercase;letter-spacing:0.7px;'>Wins</div></div>"
                  # Losses
                  f"<div style='padding:0.85rem 0.5rem 0.8rem;text-align:center;"
                  f"border-right:1px solid #161616;'>"
                  f"<div style='font-size:1.15rem;font-weight:800;line-height:1;"
                  f"color:#ef5350;margin-bottom:0.4rem;'>{_losses}</div>"
                  f"<div style='font-size:0.6rem;font-weight:700;color:#8a8a8a;"
                  f"text-transform:uppercase;letter-spacing:0.7px;'>Losses</div></div>"
                  # Total
                  f"<div style='padding:0.85rem 0.5rem 0.8rem;text-align:center;'>"
                  f"<div style='font-size:1.15rem;font-weight:800;line-height:1;"
                  f"color:#a0a0a0;margin-bottom:0.4rem;'>{_tot}</div>"
                  f"<div style='font-size:0.6rem;font-weight:700;color:#8a8a8a;"
                  f"text-transform:uppercase;letter-spacing:0.7px;'>Total</div></div>"
                  f"</div>"
                  # Price ladder
                  + (f"<div style='padding:0.65rem 0.8rem;border-top:1px solid #161616;'>"
                     f"{_ladder}</div>" if _ladder else '')
                  + f"</div>",
                  unsafe_allow_html=True)

              # ── chart toggle button ───────────────────────────────────────────
              _chart_key = f"lsc_chart_{_sym_d}"
              _is_open   = st.session_state.lsc_chart_open.get(_chart_key, False)
              st.markdown(
                  "<style>"
                  f"[class*='st-key-lsc_ctoggle_{_sym_d}'] .stButton>button{{"
                  "background:#0d0d0d!important;border:1px solid #1e1e1e!important;"
                  "border-top:none!important;border-radius:0 0 10px 10px!important;"
                  "color:#303030!important;font-size:0.62rem!important;"
                  "font-weight:800!important;width:100%!important;"
                  "min-height:1.6rem!important;padding:0!important;"
                  "letter-spacing:0.5px!important;transition:all .12s!important;}}"
                  f"[class*='st-key-lsc_ctoggle_{_sym_d}'] .stButton>button:hover{{"
                  "border-color:#2a2a2a!important;color:#505050!important;}}"
                  "</style>",
                  unsafe_allow_html=True)
              with st.container(key=f"lsc_ctoggle_{_sym_d}"):
                  if st.button(
                      f"{'▲ Hide Chart' if _is_open else '▼ Show Chart'}",
                      key=f"lsc_chart_btn_{_sym_d}",
                      use_container_width=True):
                      st.session_state.lsc_chart_open[_chart_key] = not _is_open
                      st.rerun()

              # ── chart (shown when open) ───────────────────────────────────────
              if _is_open and _df_f is not None:
                  try:
                      import plotly.graph_objects as go
                      import numpy as _np
                      import pandas as _pd
                      from scanner_engine import _build_states

                      _states_all = _build_states(_df_f)
                      _N = len(_df_f)

                      # Match scanner_engine._eval filters so chart markers count
                      # equals the Wins/Losses/Total numbers in the box:
                      #   1. drop fires too close to the end (need `hold` bars to resolve)
                      #   2. keep only fires that happened in the card's target regime
                      from scanner_engine import _regime_arr as _rg_arr_fn
                      from scanner_engine import _PERIOD_CFG as _pcfg_pre
                      _pcfg_sel_pre = st.session_state.get('sc_period', 'Medium')
                      _, _, _hold_pre, _, _ = _pcfg_pre.get(_pcfg_sel_pre, _pcfg_pre['Medium'])
                      try:
                          _reg_arr_chart = _rg_arr_fn(_df_f)
                      except Exception:
                          _reg_arr_chart = None

                      if _inds and all(k in _states_all for k in _inds):
                          _combo_arr = _states_all[_inds[0]].copy()
                          for _ik in _inds[1:]:
                              _combo_arr = _combo_arr & _states_all[_ik]
                          _edge = _np.zeros(_N, dtype=_np.int8)
                          _edge[1:] = ((_combo_arr[1:] == 1) & (_combo_arr[:-1] == 0)).astype(_np.int8)
                          _raw_idxs = _np.where(_edge == 1)[0]
                          # filter 1: drop fires with < hold bars remaining (can't resolve)
                          _raw_idxs = _raw_idxs[_raw_idxs < _N - _hold_pre]
                          # filter 2: keep only fires in this card's target regime
                          if _reg_arr_chart is not None:
                              _raw_idxs = _np.array([i for i in _raw_idxs
                                                     if i < len(_reg_arr_chart)
                                                     and _reg_arr_chart[i] == _best_rname])
                          _fire_idxs     = set(_raw_idxs.tolist())
                          _cur_firing    = bool(int(_combo_arr[-1]) == 1)
                          _ind_states    = {k: bool(int(_states_all[k][-1]) == 1)
                                            for k in _inds if k in _states_all}
                      else:
                          _fire_idxs  = set()
                          _cur_firing = False
                          _ind_states = {}

                      # Show enough history that every counted signal is visible.
                      # The Total/Wins/Losses numbers in the box come from ALL fires
                      # in the lookback window — so the chart must span at least back
                      # to the earliest fire, plus a small padding for context.
                      _first_fire = (min(_fire_idxs) if _fire_idxs else _N - 60)
                      _tail_min   = max(60, _N - _first_fire + 10)  # at least 60 bars
                      _offset     = max(0, _N - _tail_min)
                      _cdf      = _df_f.iloc[_offset:].copy().reset_index(drop=True)
                      _today_s  = str(_cdf['Date'].iloc[-1])[:10] if 'Date' in _cdf.columns else ''
                      _xd       = (_pd.to_datetime(_cdf['Date'])
                                   if 'Date' in _cdf.columns else list(range(len(_cdf))))

                      fig = go.Figure()
                      fig.add_trace(go.Candlestick(
                          x=_xd,
                          open=_cdf['Open'], high=_cdf['High'],
                          low=_cdf['Low'],   close=_cdf['Close'],
                          increasing_line_color='#26A69A', decreasing_line_color='#ef5350',
                          increasing_fillcolor='rgba(38,166,154,0.15)',
                          decreasing_fillcolor='rgba(239,83,80,0.15)',
                          line_width=1, name=''))

                      # past fires — W/L outcome markers
                      _close_arr = _df_f['Close'].values.astype(float)
                      _high_arr  = _df_f['High'].values.astype(float)
                      _low_arr   = _df_f['Low'].values.astype(float)
                      # get hold/pt/sl for this period
                      from scanner_engine import _PERIOD_CFG as _pcfg
                      _pcfg_sel  = st.session_state.get('sc_period', 'Medium')
                      _, _, _hold_b, _pt_b, _sl_b = _pcfg.get(_pcfg_sel, _pcfg['Medium'])

                      _win_x, _win_y   = [], []
                      _loss_x, _loss_y = [], []

                      for _fi in sorted(_fire_idxs):
                          _ci = _fi - _offset
                          if _ci < 0 or _ci >= len(_cdf):
                              continue
                          _xval = _xd.iloc[_ci] if hasattr(_xd, 'iloc') else _xd[_ci]
                          _yval = float(_cdf['Low'].iloc[_ci]) * 0.991
                          _entry_p = float(_close_arr[_fi])
                          if _entry_p <= 0:
                              continue
                          # Mirror scanner_engine._eval bar-by-bar walk: whichever
                          # barrier hits first chronologically (SL or PT) wins.
                          _outcome = None
                          for _j in range(1, _hold_b + 1):
                              if _fi + _j >= _N:
                                  break
                              # SL check (using close, matching _eval)
                              _g = (_close_arr[_fi + _j] - _entry_p) / _entry_p
                              if _g <= -_sl_b:
                                  _outcome = 'loss'; break
                              if _g >= _pt_b:
                                  _outcome = 'win'; break
                          # end of hold without either: classify by close vs entry
                          if _outcome is None and _fi + _hold_b < _N:
                              _g_end = (_close_arr[_fi + _hold_b] - _entry_p) / _entry_p
                              _outcome = 'win' if _g_end > 0 else 'loss'
                          if _outcome == 'win':
                              _win_x.append(_xval);  _win_y.append(_yval)
                          elif _outcome == 'loss':
                              _loss_x.append(_xval); _loss_y.append(_yval)
                          # else: unresolved (in-progress) — not counted in box either

                      if _win_x:
                          fig.add_trace(go.Scatter(
                              x=_win_x, y=_win_y, mode='markers',
                              marker=dict(symbol='triangle-up', size=11,
                                          color='#26A69A', opacity=1.0,
                                          line=dict(width=1, color='#1a6e64')),
                              hovertemplate='Win ✓<extra></extra>', name='Win'))
                      if _loss_x:
                          fig.add_trace(go.Scatter(
                              x=_loss_x, y=_loss_y, mode='markers',
                              marker=dict(symbol='triangle-up', size=11,
                                          color='#ef5350', opacity=1.0,
                                          line=dict(width=1, color='#8b1c1c')),
                              hovertemplate='Loss ✗<extra></extra>', name='Loss'))

                      # NOW marker
                      _lx  = _xd.iloc[-1] if hasattr(_xd, 'iloc') else _xd[-1]
                      _llo = float(_cdf['Low'].iloc[-1])
                      _lhi = float(_cdf['High'].iloc[-1])
                      if _cur_firing:
                          fig.add_trace(go.Scatter(
                              x=[_lx], y=[_llo * 0.988],
                              mode='markers+text',
                              marker=dict(symbol='triangle-up', size=16,
                                          color='#FFD700', opacity=1.0,
                                          line=dict(width=1, color='#b8860b')),
                              text=['NOW'], textposition='bottom center',
                              textfont=dict(size=8, color='#FFD700'),
                              hovertemplate=f'FIRING NOW — {_today_s}<extra></extra>', name=''))

                      fig.add_annotation(
                          x=_lx, y=_lhi,
                          text=f'<b>{_today_s}</b>',
                          showarrow=True, arrowhead=0, arrowcolor='#333',
                          arrowwidth=1, ax=0, ay=-22,
                          font=dict(size=9, color='#FFD700' if _cur_firing else '#505050'),
                          bgcolor='rgba(8,8,8,0.85)', borderpad=3)

                      # levels
                      if _ladder:
                          for _lval, _lc, _ln, _ld in [
                              (_en,   '#64b5f6', 'Entry', 'dash'),
                              (_t1,   '#26A69A', 'T1',    'dot'),
                              (_t2,   '#66bb6a', 'T2',    'dot'),
                              (_sl_p, '#ef5350', 'Stop',  'dashdot')]:
                              fig.add_hline(
                                  y=_lval, line_color=_lc, line_dash=_ld,
                                  line_width=1.4, opacity=0.9,
                                  annotation_text=f'<b>{_ln}</b> {_lval:.2f}',
                                  annotation_font_color=_lc, annotation_font_size=9,
                                  annotation_bgcolor='rgba(8,8,8,0.85)',
                                  annotation_position='right')

                      fig.update_layout(
                          paper_bgcolor='#080808', plot_bgcolor='#0d0d0d',
                          margin=dict(l=4, r=80, t=10, b=8), height=280,
                          xaxis=dict(showgrid=False, zeroline=False,
                                     rangeslider=dict(visible=False),
                                     type='date', tickformat='%d %b',
                                     tickfont=dict(size=9, color='#484848'), nticks=8),
                          yaxis=dict(showgrid=True, gridcolor='#161616', zeroline=False,
                                     tickfont=dict(size=9, color='#484848'), side='right'),
                          showlegend=False)
                      fig.update_xaxes(showspikes=False)
                      fig.update_yaxes(showspikes=False)

                      # indicator pills
                      _ind_pills = ''.join(
                          f"<span style='display:inline-flex;align-items:center;gap:0.25rem;"
                          f"padding:0.15rem 0.5rem;border-radius:20px;font-size:0.6rem;"
                          f"font-weight:900;"
                          f"background:{'rgba(38,166,154,0.14)' if _ind_states.get(k) else 'rgba(239,83,80,0.08)'};"
                          f"border:1px solid {'rgba(38,166,154,0.4)' if _ind_states.get(k) else 'rgba(239,83,80,0.22)'};"
                          f"color:{'#26A69A' if _ind_states.get(k) else '#ef5350'};'>"
                          f"{'●' if _ind_states.get(k) else '○'}&thinsp;{_IND_SHORT.get(k,k)}</span>"
                          for k in _inds)

                      _fire_lbl = (
                          f"<span style='color:#FFD700;font-weight:900;font-size:0.65rem;'>"
                          f"● FIRING — {_today_s}</span>"
                          if _cur_firing else
                          f"<span style='color:#484848;font-weight:700;font-size:0.65rem;'>"
                          f"last bar: {_today_s}</span>")

                      st.markdown(
                          f"<div style='border:1px solid #1e1e1e;border-radius:0 0 10px 10px;"
                          f"overflow:hidden;background:#080808;'>"
                          f"<div style='padding:0.4rem 0.8rem;border-bottom:1px solid #181818;"
                          f"display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;'>"
                          f"<span style='font-size:0.55rem;font-weight:900;color:#484848;"
                          f"text-transform:uppercase;letter-spacing:1px;'>Signal History</span>"
                          f"<span style='font-size:0.6rem;font-weight:800;color:#26A69A;"
                          f"background:rgba(38,166,154,0.1);border:1px solid rgba(38,166,154,0.25);"
                          f"padding:1px 7px;border-radius:20px;'>▲ Win</span>"
                          f"<span style='font-size:0.6rem;font-weight:800;color:#ef5350;"
                          f"background:rgba(239,83,80,0.1);border:1px solid rgba(239,83,80,0.25);"
                          f"padding:1px 7px;border-radius:20px;'>▲ Loss</span>"
                          f"<span style='margin-left:auto;'>{_fire_lbl}</span></div>"
                          f"<div style='padding:0.35rem 0.8rem;border-bottom:1px solid #161616;"
                          f"display:flex;gap:0.28rem;flex-wrap:wrap;'>{_ind_pills}</div>",
                          unsafe_allow_html=True)
                      st.plotly_chart(fig, use_container_width=True,
                                      config={'displayModeBar': False})
                      st.markdown("</div>", unsafe_allow_html=True)
                  except Exception:
                      pass

              st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
