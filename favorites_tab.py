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
        border:1px solid #1e1e1e;
        border-radius:12px;
        margin-bottom:0.7rem;
        overflow:hidden;
        background:#141414;
    }
    .ss-stock-row:hover { border-color:#282828; }

    /* stock label strip */
    .ss-stock-label {
        display:flex; align-items:center; gap:0.65rem;
        padding:0.6rem 1rem 0.55rem;
        background:#191919;
        border-bottom:1px solid #1e1e1e;
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
        font-size:0.75rem; font-weight:700; color:#888;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        flex:1; min-width:0; line-height:1.3;
    }
    .ss-chip-wr {
        font-size:0.72rem; font-weight:800;
        white-space:nowrap; flex-shrink:0; padding-right:0.1rem;
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

    # ── render one row per stock ──────────────────────────────────────────────
    _gidx = 0
    for _sym, _sdata in sorted(_by_stock.items()):
        _sname   = _sdata['sname']
        _periods = _sdata['periods']
        _strat_n = sum(len(v) for v in _periods.values())
        _sym_disp = _sym.replace('.SR', '')

        # build the 3-column period grid as one HTML block + Streamlit buttons
        # We render the outer chrome as HTML and inject Streamlit buttons per chip

        # stock label
        st.markdown(
            f"<div class='ss-stock-row'>"
            f"<div class='ss-stock-label'>"
            f"<span class='ss-stock-sym'>{_sym_disp}</span>"
            + (f"<span class='ss-stock-name'>{_sname}</span>" if _sname else "")
            + f"<span class='ss-stock-count'>{_strat_n} saved</span>"
            f"</div>"
            f"<div class='ss-period-grid'>",
            unsafe_allow_html=True)

        _col_s, _col_m, _col_l = st.columns(3, gap="small")
        _pcols = {'Short (5d)': _col_s, 'Medium (63d)': _col_m, 'Long (252d)': _col_l}

        for _pl3, _col in _pcols.items():
            _strats_p = _periods.get(_pl3, [])
            _lbl3, _days3 = _PERIOD_SHORT[_pl3]
            with _col:
                # period label
                st.markdown(
                    f"<div class='ss-period-title'>"
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

                    _c_chip, _c_del = st.columns([18, 1])
                    with _c_chip:
                        st.markdown(
                            f"<div class='ss-chip'>"
                            f"<div class='ss-chip-bar' style='background:{_rc}'></div>"
                            f"<div class='ss-chip-body'>"
                            f"<span class='ss-chip-regime' style='background:{_rc};color:#0a0a0a;'>"
                            f"{_ri}&nbsp;{_rlbl}</span>"
                            f"<span class='ss-chip-name' title='{_combo}'>{_combo}</span>"
                            f"<span class='ss-chip-wr' style='color:{_wc}'>{_wr:.0f}%</span>"
                            f"</div></div>",
                            unsafe_allow_html=True)
                    with _c_del:
                        with st.container(key=_rmkey):
                            st.button("✕", key=f"btn_{_rmkey}",
                                      use_container_width=True,
                                      on_click=_rc_toggle, args=(_fid, None))
                    _gidx += 1

        # close the HTML wrappers opened above
        st.markdown("</div></div>", unsafe_allow_html=True)

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
def _fetch_signals_cached(symbol: str, yf_period: str):
    """Fetch OHLCV + compute indicators + detect signals. Cached 5 min."""
    try:
        import yfinance as yf
        import pandas as pd
        import pandas_ta as ta
        from signal_engine import detect_signals

        _df = yf.download(symbol, period=yf_period, interval='1d', progress=False, auto_adjust=True)
        if _df is None or len(_df) < 20:
            return None, None
        _df.columns = [c[0] if isinstance(c, tuple) else c for c in _df.columns]
        _df = _df.reset_index()
        if 'Date' not in _df.columns and 'Datetime' in _df.columns:
            _df = _df.rename(columns={'Datetime': 'Date'})
        _df['Date'] = pd.to_datetime(_df['Date'])

        # compute indicators that signal_engine needs
        _c = _df['Close']
        _df['EMA_20']  = ta.ema(_c, length=20)
        _df['EMA_50']  = ta.ema(_c, length=50)
        _df['EMA_200'] = ta.ema(_c, length=200)
        _df['SMA_50']  = ta.sma(_c, length=50)
        _df['SMA_200'] = ta.sma(_c, length=200)
        _df['RSI_14']  = ta.rsi(_c, length=14)

        macd = ta.macd(_c)
        if macd is not None:
            for col in macd.columns:
                _df[col] = macd[col]

        bb = ta.bbands(_c, length=20)
        if bb is not None:
            for col in bb.columns:
                _df[col] = bb[col]

        stoch = ta.stoch(_df['High'], _df['Low'], _c)
        if stoch is not None:
            for col in stoch.columns:
                _df[col] = stoch[col]

        adx = ta.adx(_df['High'], _df['Low'], _c)
        if adx is not None:
            for col in adx.columns:
                _df[col] = adx[col]

        roc  = ta.roc(_c, length=12);  _df['ROC_12'] = roc if roc is not None else 0
        cci  = ta.cci(_df['High'], _df['Low'], _c, length=20); _df['CCI_20'] = cci if cci is not None else 0
        willr = ta.willr(_df['High'], _df['Low'], _c, length=14); _df['WILLR_14'] = willr if willr is not None else 0
        mfi  = ta.mfi(_df['High'], _df['Low'], _c, _df['Volume'], length=14); _df['MFI_14'] = mfi if mfi is not None else 0
        cmf  = ta.cmf(_df['High'], _df['Low'], _c, _df['Volume'], length=20); _df['CMF_20'] = cmf if cmf is not None else 0
        obv  = ta.obv(_c, _df['Volume']); _df['OBV'] = obv if obv is not None else 0
        wma  = ta.wma(_c, length=20); _df['WMA_20'] = wma if wma is not None else _c

        psar = ta.psar(_df['High'], _df['Low'], _c)
        if psar is not None:
            for col in psar.columns:
                _df[col] = psar[col]

        ichi = ta.ichimoku(_df['High'], _df['Low'], _c)
        if ichi is not None and isinstance(ichi, tuple):
            for part in ichi:
                if hasattr(part, 'columns'):
                    for col in part.columns:
                        _df[col] = part[col]

        _df['REGIME'] = 'TREND'

        # vwap approximation (daily: just use typical price ratio trend)
        _df['VWAP'] = ((_df['High'] + _df['Low'] + _df['Close']) / 3 * _df['Volume']).cumsum() / _df['Volume'].cumsum()

        kc = ta.kc(_df['High'], _df['Low'], _c)
        if kc is not None:
            for col in kc.columns:
                _df[col] = kc[col]

        dc = ta.donchian(_df['High'], _df['Low'])
        if dc is not None:
            for col in dc.columns:
                _df[col] = dc[col]

        sigs = detect_signals(_df)
        price = float(_df['Close'].iloc[-1])
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


def _render_live_signals(rc_favs: list) -> None:
    """Render the Live Signals section below the saved strategies grid."""
    if not rc_favs:
        return

    # Live Signal Check section divider — same dark style as the rest of the page
    st.markdown(
        "<div class='ss-section-divider'>"
        "<div class='ss-section-line'></div>"
        "<div class='ss-section-lbl'>"
        "<div class='ss-section-dot' style='background:#26A69A'></div>"
        "⚡&nbsp;Live Signal Check"
        "</div>"
        "<div class='ss-section-line'></div>"
        "</div>"
        "<div style='font-size:0.65rem;color:#3e3e3e;margin:-0.4rem 0 1.1rem;line-height:1.7;'>"
        "Each saved strategy is checked against fresh market data. "
        "A strategy <span style='color:#26A69A;font-weight:700;'>fires</span> "
        "when all its indicators show a buy signal within the last 3 bars."
        "</div>",
        unsafe_allow_html=True)

    # group by symbol so we only fetch price once per symbol
    _sym_groups: dict = {}
    for _f in rc_favs:
        _s = _f.get('symbol', '')
        _sym_groups.setdefault(_s, []).append(_f)

    _firing_cards = []
    _quiet_cards  = []

    for _sym, _strats in sorted(_sym_groups.items()):
        # pick the longest period saved for this stock (more data = better signal detection)
        _yf_period = '1y'
        with st.spinner(f"Checking {_sym}…"):
            _sig_df, _price = _fetch_signals_cached(_sym, _yf_period)

        for _f in _strats:
            _combo   = _f.get('combo_indicators', '')
            _keys    = _combo_display_to_keys(_combo)
            _sw      = int(_f.get('signal_window', 3) or 3)
            _check   = _check_strategy_firing(_sig_df, _keys, window=max(_sw, 3))
            _rv      = float(_f.get('risk_val', 1)   or 1)
            _rw      = float(_f.get('reward_val', 2) or 2)
            _rk      = _f.get('best_regime', 'TREND')
            _pl      = _f.get('period_label', '')
            _wr      = float(_f.get('win_rate', 0) or 0)
            _pf      = float(_f.get('profit_factor', 0) or 0)

            _entry  = _price or 0
            _sl_pct = 0.02 * _rv
            _tp_pct = _sl_pct * (_rw / _rv)
            _stop   = round(_entry * (1 - _sl_pct), 2)  if _entry else 0
            _target = round(_entry * (1 + _tp_pct), 2)  if _entry else 0
            _risk_sar    = round(_entry - _stop,  2) if _entry else 0
            _reward_sar  = round(_target - _entry, 2) if _entry else 0

            _card = {
                'sym': _sym, 'combo': _combo, 'keys': _keys,
                'check': _check, 'price': _entry,
                'stop': _stop, 'target': _target,
                'risk_sar': _risk_sar, 'reward_sar': _reward_sar,
                'sl_pct': _sl_pct * 100, 'tp_pct': _tp_pct * 100,
                'regime': _rk, 'period': _pl, 'win_rate': _wr, 'pf': _pf,
                'rv': int(_rv), 'rw': int(_rw),
            }
            if _check['firing']:
                _firing_cards.append(_card)
            else:
                _quiet_cards.append(_card)

    # ── firing signals ───────────────────────────────────────────────────────
    if _firing_cards:
        st.markdown(
            f"<div style='font-size:0.6rem;font-weight:800;color:#26A69A;text-transform:uppercase;"
            f"letter-spacing:1px;margin-bottom:0.55rem;'>"
            f"⚡&nbsp; Firing Now &nbsp;<span style='color:#1e3d30;'>({len(_firing_cards)})</span>"
            f"</div>",
            unsafe_allow_html=True)

        for _c in _firing_cards:
            _rc = _REGIME_COLORS.get(_c['regime'], '#a78bfa')
            _ri = _REGIME_ICONS.get(_c['regime'], '★')
            _wc = '#26A69A' if _c['win_rate'] >= 55 else ('#FFC107' if _c['win_rate'] >= 45 else '#ef5350')

            _pill_html = ''.join(
                f"<span class='ls-pill' style='"
                f"color:{'#26A69A' if k in _c['check']['active'] else '#252525'};"
                f"border-color:{'#26A69A33' if k in _c['check']['active'] else '#1a1a1a'};"
                f"background:{'#26A69A0D' if k in _c['check']['active'] else '#0a0a0a'};'>"
                f"{'✓' if k in _c['check']['active'] else '○'}&nbsp;{k}</span>"
                for k in _c['keys']
            )

            st.markdown(
                f"<div class='ls-card ls-card-fire'>"
                f"<div class='ls-top'>"
                f"<span class='ls-sym'>{_c['sym'].replace('.SR','')}</span>"
                f"<span class='ls-tag' style='background:{_rc};color:#0a0a0a;'>"
                f"{_ri}&nbsp;{_c['regime'].title()}</span>"
                f"<span class='ls-tag' style='background:#252525;color:#888;'>"
                f"{_c['period'].split('(')[0].strip()}</span>"
                f"<span class='ls-combo-name' title='{_c['combo']}'>{_c['combo']}</span>"
                f"<span class='ls-badge-fire'>⚡ Firing</span>"
                f"</div>"
                f"<div class='ls-pills'>{_pill_html}</div>"
                f"<div class='ls-ladder'>"
                # entry
                f"<div class='ls-cell'>"
                f"<div class='ls-cell-top' style='background:#4A9EFF'></div>"
                f"<div class='ls-cell-lbl'>Entry Price</div>"
                f"<div class='ls-cell-val' style='color:#c0c0c0'>{_c['price']:.2f}</div>"
                f"<div class='ls-cell-sub'>Current market price</div>"
                f"</div>"
                # target
                f"<div class='ls-cell'>"
                f"<div class='ls-cell-top' style='background:#26A69A'></div>"
                f"<div class='ls-cell-lbl'>Take Profit</div>"
                f"<div class='ls-cell-val' style='color:#26A69A'>{_c['target']:.2f}</div>"
                f"<div class='ls-cell-sub' style='color:#1e4a3a'>+{_c['tp_pct']:.1f}% &nbsp;·&nbsp; "
                f"+{_c['reward_sar']:.2f}</div>"
                f"</div>"
                # stop
                f"<div class='ls-cell'>"
                f"<div class='ls-cell-top' style='background:#ef5350'></div>"
                f"<div class='ls-cell-lbl'>Stop Loss</div>"
                f"<div class='ls-cell-val' style='color:#ef5350'>{_c['stop']:.2f}</div>"
                f"<div class='ls-cell-sub' style='color:#4a1e1e'>-{_c['sl_pct']:.1f}% &nbsp;·&nbsp; "
                f"-{_c['risk_sar']:.2f}</div>"
                f"</div>"
                # r:r + stats
                f"<div class='ls-cell'>"
                f"<div class='ls-cell-top' style='background:{_wc}'></div>"
                f"<div class='ls-cell-lbl'>R:R &nbsp;·&nbsp; Win Rate</div>"
                f"<div class='ls-cell-val' style='color:{_wc}'>"
                f"{_c['rv']}:{_c['rw']} &nbsp;<span style='font-size:0.82rem;color:{_wc};opacity:0.7;'>"
                f"{_c['win_rate']:.0f}%</span></div>"
                f"<div class='ls-cell-sub'>PF &nbsp;{_c['pf']:.2f}</div>"
                f"</div>"
                f"</div></div>",
                unsafe_allow_html=True)

    # ── watching / not firing ────────────────────────────────────────────────
    if _quiet_cards:
        st.markdown(
            f"<div style='font-size:0.65rem;font-weight:800;color:#555;text-transform:uppercase;"
            f"letter-spacing:1px;margin:0.9rem 0 0.45rem;display:flex;align-items:center;gap:0.5rem;'>"
            f"<span style='display:inline-block;width:5px;height:5px;border-radius:50%;background:#333;flex-shrink:0;'></span>"
            f"Watching &nbsp;<span style='color:#383838;font-weight:600;'>({len(_quiet_cards)})</span>"
            f"</div>",
            unsafe_allow_html=True)

        for _c in _quiet_cards:
            _rc  = _REGIME_COLORS.get(_c['regime'], '#a78bfa')
            _ri  = _REGIME_ICONS.get(_c['regime'], '★')
            _an  = len(_c['check']['active'])
            _tn  = len(_c['keys'])
            _prog = f"{_an}/{_tn}" if _tn else "—"

            _pill_html = ''.join(
                f"<span class='ls-pill' style='"
                f"color:{'#4A9EFF' if k in _c['check']['active'] else '#1e1e1e'};"
                f"border-color:{'#4A9EFF22' if k in _c['check']['active'] else '#181818'};"
                f"background:transparent;'>"
                f"{'✓' if k in _c['check']['active'] else '○'}&nbsp;{k}</span>"
                for k in _c['keys']
            )

            st.markdown(
                f"<div class='ls-quiet'>"
                f"<span class='ls-quiet-sym'>{_c['sym'].replace('.SR','')}</span>"
                f"<span class='ls-tag' style='background:{_rc}22;color:{_rc}88;font-size:0.58rem;font-weight:800;padding:0.12rem 0.42rem;border-radius:20px;text-transform:uppercase;letter-spacing:0.3px;white-space:nowrap;'>"
                f"{_ri}&nbsp;{_c['regime'].title()}</span>"
                f"<span style='font-size:0.58rem;color:#2e2e2e;white-space:nowrap;'>"
                f"{_c['period'].split('(')[0].strip()}</span>"
                f"<span class='ls-quiet-combo' title='{_c['combo']}'>{_c['combo']}</span>"
                f"<div style='display:flex;gap:0.25rem;flex-wrap:wrap;'>{_pill_html}</div>"
                f"<span class='ls-quiet-prog'>{_prog} active</span>"
                f"</div>",
                unsafe_allow_html=True)
