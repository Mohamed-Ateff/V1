import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import warnings
import numpy as np
from plotly.subplots import make_subplots

from auth import auth_wall, show_user_badge, load_favorites, upsert_favorite, delete_favorite, logout
from favorites_tab import favorites_css, render_favorites_panel
from gemini_tab import gemini_tab
from price_action_tab import price_action_analysis_tab

# ── Extracted backend modules ──────────────────────────────────────────────────
from market_data import (
    get_saudi_market_status,
    get_all_tadawul_tickers,
    get_saudi_market_data,
    run_market_analysis,
)
from regime_analyzer import RegimeAnalyzer
from signal_engine import (
    get_stock_name,
    detect_signals,
    evaluate_signal_success,
    find_consensus_signals,
    analyze_indicator_combinations,
    calculate_monthly_performance,
)
from charts import (
    create_price_chart,
    create_regime_distribution_chart,
    create_adx_chart,
    create_rsi_chart,
    create_macd_chart,
    create_bollinger_bands_chart,
    create_volume_chart,
    create_ema_chart,
    create_stochastic_chart,
    create_signal_strength_heatmap,
    create_signal_success_chart,
    create_regime_performance_chart,
    create_monthly_performance_chart,
    render_trading_system_chart,
    create_combo_performance_chart,
    create_combo_regime_chart,
    create_combo_metrics_comparison,
    create_combo_consistency_chart,
    create_consensus_agreement_chart,
    create_consensus_timeline_chart,
    create_consensus_regime_chart,
    placeholder_consensus,
)
from ui_helpers import info_icon, apply_ui_theme

warnings.filterwarnings('ignore')

st.set_page_config(

    page_title="",

    page_icon="S",

    layout="wide",

    initial_sidebar_state="collapsed"

)



# Custom CSS for professional look

st.markdown("""

<style>

    #MainMenu, footer, header,

    [data-testid="stToolbar"], [data-testid="stDecoration"],

    [data-testid="stStatusWidget"], [data-testid="collapsedControl"],

    [data-testid="stHeader"] {

        visibility: hidden !important;

        display: none !important;

    }



    .main-header {

        font-size: 2.5rem;

        font-weight: 700;

        color: white;

        margin-bottom: 0.5rem;

    }

    .sub-header {

        font-size: 1.2rem;

        color: #666;

    }

    .regime-label { margin-top: -0.4rem; font-size: 1.8rem; line-height: 1.2; font-weight: 700; }

    .regime-trend { color: #26A69A; }

    .regime-range { color: #4A9EFF; }

    .regime-volatile { color: #FF6B6B; }

    /* Section styling */

    .section-container { background-color: transparent; margin-bottom: 0; border-radius: 0; padding: 0; }

    .stCheckbox { font-size: 1.1rem !important; }

    .stCheckbox > label { font-size: 1.05rem !important; padding: 0.4rem 0 !important; }

    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }

    h2, h3 { margin-top: 0 !important; margin-bottom: 1rem !important; }

    h4 { margin-top: 0 !important; margin-bottom: 0.8rem !important; font-size: 1.1rem !important; color: #fff !important; }

    .section-title { font-size: 1.5rem !important; font-weight: 700 !important; color: #ffffff !important; margin: 0 0 0.8rem 0 !important; padding: 0 !important; }

    .action-card { background: transparent; padding: 0; border-radius: 0; margin-bottom: 0.5rem; border: none; }

    .warning-card { background: transparent; padding: 0; border-radius: 0; margin-bottom: 0.5rem; border: none; }

    .info-card { background: transparent; padding: 0; border-radius: 0; margin-bottom: 0.5rem; border: none; }

    /* Recommendations tab styling */

    .rec-section { background: transparent; padding: 0; border-radius: 0; margin-bottom: 1rem; border: none; }

    .rec-title { font-size: 1.1rem !important; font-weight: 700 !important; color: #ffffff !important; margin: 0 !important; padding: 0 !important; }

    /* Ensure recommendation section titles have no bottom spacing */

    .rec-section .rec-title, .rec-section h3, .rec-section h4 {

        margin-bottom: 0 !important;

        padding-bottom: 0 !important;

    }

    .rec-good { background: transparent; padding: 0; border-radius: 0; border: none; margin-bottom: 0.5rem; }

    .rec-warning { background: transparent; padding: 0; border-radius: 0; border: none; margin-bottom: 0.5rem; }

    .rec-bad { background: transparent; padding: 0; border-radius: 0; border: none; margin-bottom: 0.5rem; }

    /* Signal analysis styling */

    .signal-card { background: transparent; padding: 0; border-radius: 0; margin-bottom: 1rem; border: none; }

    .success-high { color: #26A69A; font-weight: 700; }

    .success-medium { color: #FFC107; font-weight: 700; }

    .success-low { color: #FF6B6B; font-weight: 700; }

    .metric-box { background: transparent; padding: 0; border-radius: 0; text-align: center; }

    .big-number { font-size: 2rem; font-weight: 700; margin: 0.5rem 0; }

    /* Control layout styling */

    .stButton > button[kind="primary"] {

        background-color: #050505 !important;

        color: white !important;

        border: none !important;

        font-weight: 600 !important;

    }

    .stButton > button[kind="primary"]:hover {

        background-color: #303030 !important;

    }

    .stTextInput > div > div > input {

        background-color: #212121 !important;

        color: #fff !important;

        border: 1px solid #303030 !important;

        border-radius: 0 !important;

    }

    .stDateInput > div > div > input {

        background-color: #212121 !important;

        color: #fff !important;

        border: 1px solid #303030 !important;

        border-radius: 0 !important;

    }

    .stSlider > div > div > div > div {

        color: #888 !important;

    }

    .stMultiSelect > div > div > div {

        background-color: #212121 !important;

        border: 1px solid #303030 !important;

        border-radius: 0 !important;

    }

    /* ?? Tab nav - Box Style ?? */

    div[role="tablist"] {

        display: flex !important;

        gap: 0.5rem !important;

        padding: 0.35rem !important;

        background: #212121 !important;

        border: 1px solid #303030 !important;

        border-radius: 10px !important;

        margin-top: 1.5rem !important;

        margin-bottom: 0.5rem !important;

        width: 100% !important;

    }

    div[role="tablist"] button {

        position: relative !important;

        flex: 1 1 0 !important;

        color: #9e9e9e !important;

        background: transparent !important;

        border: none !important;

        border-radius: 8px !important;

        padding: 0.55rem 0.75rem !important;

        font-size: 0.8rem !important;

        font-weight: 500 !important;

        letter-spacing: 0 !important;

        box-shadow: none !important;

        transition: all 0.15s ease !important;

        white-space: nowrap !important;

        text-transform: none !important;

        text-align: center !important;

    }

    div[role="tablist"] button:hover {

        color: #ffffff !important;

        background: #303030 !important;

    }

    div[role="tablist"] button[aria-selected="true"] {

        color: #ffffff !important;

        background: #303030 !important;

        border: none !important;

        font-weight: 600 !important;

    }

    div[role="tablist"] button[aria-selected="true"]::before {

        display: none !important;

    }

    div[role="tablist"] button[aria-selected="true"]::after,

    div[role="tablist"] button::after { display: none !important; }

    div[data-baseweb="tab-highlight"] { display: none !important; }

    div[data-baseweb="tab-border"]    { display: none !important; }

</style>

""", unsafe_allow_html=True)







def main():

    """Main application."""



    if 'show_results' not in st.session_state:

        st.session_state.show_results = False

    if 'show_market_results' not in st.session_state:

        st.session_state.show_market_results = False

    if 'show_market_pulse' not in st.session_state:

        st.session_state.show_market_pulse = False



    # ?? Load favorites from DB once per session ???????????????????????????

    if 'favorites' not in st.session_state:

        _user = st.session_state.get('auth_username', '')

        st.session_state.favorites = load_favorites(_user) if _user else []



    apply_ui_theme()

    # ── Arabic Language Toggle (Google Translate) ──────────────────────────
    components.html("""
    <script>
    (function() {
        var doc = window.parent.document;
        if (doc.getElementById('translate-fab-btn')) return;

        var style = doc.createElement('style');
        style.textContent = `
            .goog-te-banner-frame { display: none !important; }
            #goog-gt-tt, .goog-te-balloon-frame, .goog-tooltip { display: none !important; }
            body { top: 0 !important; }
            .skiptranslate { display: none !important; }
            #google_translate_element { display: none !important; }

            #translate-fab-btn {
                position: fixed;
                bottom: 24px;
                left: 24px;
                z-index: 999999;
                height: 40px;
                border-radius: 10px;
                background: rgba(255,255,255,0.03);
                border: 1px solid #252b2e;
                color: #6b7a86;
                font-size: 0.77rem;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 0 16px;
                transition: all 0.2s ease;
                font-family: 'Segoe UI', -apple-system, sans-serif;
                line-height: 1;
                letter-spacing: 0.2px;
                white-space: nowrap;
            }
            #translate-fab-btn:hover {
                background: rgba(38,166,154,0.1);
                border-color: rgba(38,166,154,0.3);
                color: #26A69A;
            }
            #translate-fab-btn.active {
                background: rgba(38,166,154,0.07);
                border-color: rgba(38,166,154,0.2);
                color: #26A69A;
            }
            #translate-fab-btn .fab-icon {
                font-size: 16px;
                font-weight: 700;
                line-height: 1;
            }
            #translate-fab-btn .fab-dot {
                width: 5px;
                height: 5px;
                border-radius: 50%;
                background: #333;
                transition: background 0.2s;
            }
            #translate-fab-btn.active .fab-dot {
                background: #26A69A;
                box-shadow: 0 0 6px rgba(38,166,154,0.5);
            }
        `;
        doc.head.appendChild(style);

        var gtDiv = doc.createElement('div');
        gtDiv.id = 'google_translate_element';
        doc.body.appendChild(gtDiv);

        var btn = doc.createElement('button');
        btn.id = 'translate-fab-btn';
        btn.title = 'عربي / English';
        btn.setAttribute('aria-label', 'Translate to Arabic');
        btn.innerHTML = '<span style="font-size:0.72rem;">العربية</span><span class="fab-dot"></span>';
        doc.body.appendChild(btn);

        var isArabic = false;
        var gtLoaded = false;

        window.parent.googleTranslateElementInit = function() {
            new window.parent.google.translate.TranslateElement({
                pageLanguage: 'en',
                includedLanguages: 'ar,en',
                autoDisplay: false
            }, 'google_translate_element');
            gtLoaded = true;
        };

        btn.addEventListener('click', function() {
            if (!gtLoaded) {
                var s = doc.createElement('script');
                s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
                doc.body.appendChild(s);
                var check = setInterval(function() {
                    var sel = doc.querySelector('.goog-te-combo');
                    if (sel) {
                        clearInterval(check);
                        sel.value = 'ar';
                        sel.dispatchEvent(new Event('change'));
                        isArabic = true;
                        btn.classList.add('active');
                        btn.children[0].textContent = 'English';
                    }
                }, 300);
                return;
            }
            var sel = doc.querySelector('.goog-te-combo');
            if (sel) {
                if (isArabic) {
                    sel.value = 'en';
                    sel.dispatchEvent(new Event('change'));
                    isArabic = false;
                    btn.classList.remove('active');
                    btn.children[0].textContent = 'العربية';
                } else {
                    sel.value = 'ar';
                    sel.dispatchEvent(new Event('change'));
                    isArabic = true;
                    btn.classList.add('active');
                    btn.children[0].textContent = 'English';
                }
            }
        });
    })();
    </script>
    """, height=0)

    if not st.session_state.show_results and not st.session_state.show_market_results and not st.session_state.show_market_pulse:

        # CONTROLS PAGE

        control_palette = st.session_state.get('theme_palette', {})

        c_text  = control_palette.get('text',  '#e6edf7')

        c_muted = control_palette.get('muted', '#97a8bf')

        current_theme = st.session_state.get("ui_theme", "dark")

        is_dark_cp = current_theme == "dark"

        cp_bg      = "rgba(9,13,21,0.96)"      if is_dark_cp else "rgba(246,249,255,0.96)"

        cp_border  = "rgba(255,255,255,0.08)"  if is_dark_cp else "rgba(0,0,0,0.09)"

        cp_shadow  = "0 8px 32px rgba(0,0,0,0.45), 0 1px 0 rgba(255,255,255,0.04)" if is_dark_cp else "0 8px 32px rgba(0,0,0,0.12), 0 1px 0 rgba(255,255,255,0.9)"

        cp_inner   = "rgba(255,255,255,0.033)" if is_dark_cp else "rgba(0,0,0,0.025)"

        cp_inner_b = "rgba(255,255,255,0.065)" if is_dark_cp else "rgba(0,0,0,0.08)"

        accent     = "#26A69A"

        # ?? Solid surface palette ??

        cp_s1    = "#212121"  if is_dark_cp else "#f8fafc"

        cp_s2    = "#303030"  if is_dark_cp else "#f1f5f9"

        cp_s3    = "#303030"  if is_dark_cp else "#e9eef5"

        cp_b1    = "#404040"  if is_dark_cp else "#dde3ec"

        cp_b2    = "#303030"  if is_dark_cp else "#edf2f7"

        cp_text1 = "#ffffff"  if is_dark_cp else "#0f172a"

        cp_text2 = "#9e9e9e"  if is_dark_cp else "#64748b"

        cp_text3 = "#757575"  if is_dark_cp else "#94a3b8"



        st.markdown(f"""<style>

        /* ?? Layout ?? */

        html, body {{ overflow: auto !important; }}

        .main .block-container, div.block-container {{

            max-width: 88% !important;

            margin-left: auto !important;

            margin-right: auto !important;

            padding-left: 0 !important;

            padding-right: 0 !important;

            padding-top: 1.4rem !important;

            padding-bottom: 3rem !important;

        }}



        /* ?? Panel grid ?? */

        .st-key-panel_row {{ margin-top: 1.5rem !important; }}

        .st-key-panel_row [data-testid="stHorizontalBlock"] {{

            align-items: flex-start !important;

            gap: 1.25rem !important;

        }}

        .st-key-panel_row [data-testid="stHorizontalBlock"] > [data-testid="column"] {{

            padding: 0 !important;

        }}



        /* ?? Panel cards - Box Style ?? */

        .st-key-stock_analysis_panel, .st-key-market_analysis_panel {{

            background: #212121 !important;

            border: 1px solid #303030 !important;

            border-radius: 16px !important;

            padding: 1.75rem !important;

            box-sizing: border-box !important;

        }}

        .st-key-stock_analysis_panel > div,

        .st-key-market_analysis_panel > div,

        .st-key-stock_analysis_panel [data-testid="stVerticalBlockBorderWrapper"],

        .st-key-market_analysis_panel [data-testid="stVerticalBlockBorderWrapper"],

        .st-key-stock_analysis_panel [data-testid="stVerticalBlock"],

        .st-key-market_analysis_panel [data-testid="stVerticalBlock"] {{

            background: transparent !important;

            background-color: transparent !important;

            border: none !important;

            box-shadow: none !important;

            padding: 0 !important;

        }}

        

        .st-key-left_panel, .st-key-right_panel {{

            background: #212121 !important;

            border: 1px solid #303030 !important;

            border-radius: 16px !important;

            padding: 1.75rem !important;

            box-sizing: border-box !important;

            height: 100% !important;

        }}

        .st-key-left_panel > div,

        .st-key-right_panel > div,

        .st-key-left_panel [data-testid="stVerticalBlockBorderWrapper"],

        .st-key-right_panel [data-testid="stVerticalBlockBorderWrapper"],

        .st-key-left_panel [data-testid="stVerticalBlock"],

        .st-key-right_panel [data-testid="stVerticalBlock"] {{

            background: transparent !important;

            background-color: transparent !important;

            border: none !important;

            box-shadow: none !important;

            padding: 0 !important;

        }}



        /* ?? Panel section header - Box Style ?? */

        .cp-panel-header {{

            display: flex;

            align-items: flex-start;

            gap: 1rem;

            margin-bottom: 1.5rem;

            padding: 0;

            background: transparent;

            border: none;

            border-radius: 0;

        }}

        .cp-panel-text {{ flex: 1; min-width: 0; }}

        .cp-section-title {{

            font-size: 1.1rem;

            font-weight: 600;

            color: #ffffff;

            margin: 0 0 0.25rem 0;

            letter-spacing: -0.3px;

        }}

        .cp-section-sub {{

            font-size: 0.75rem;

            color: #757575;

            margin: 0;

            line-height: 1.4;

            font-weight: 400;

        }}



        /* ?? Strategy Dashboard cards ?? */

        .sdash-empty {{

            display: flex; flex-direction: column;

            align-items: center; justify-content: center;

            gap: 0.8rem; padding: 3.5rem 1rem; text-align: center;

        }}

        .sdash-empty-title {{ font-size: 0.90rem; font-weight: 700; color: {cp_text2}; letter-spacing: 0.2px; }}

        .sdash-empty-sub   {{ font-size: 0.75rem; color: {cp_text3}; line-height: 1.7; max-width: 24rem; }}



        .sdash-card {{

            border: 1px solid #303030;

            border-radius: 14px;

            overflow: hidden;

            margin-bottom: 1rem;

            background: {cp_s1};

            box-shadow: 0 4px 18px rgba(0,0,0,0.30);

        }}

        .sdash-card:last-child {{ margin-bottom: 0; }}



        /* stock header row */

        .sdash-card-head {{

            display: flex;

            align-items: center;

            justify-content: space-between;

            padding: 1rem 1.3rem;

            background: #212121;

            border-bottom: 2px solid #303030;

        }}

        .sdash-card-head-left {{

            display: flex;

            flex-direction: column;

            gap: 0.18rem;

            min-width: 0;

        }}

        .sdash-card-sym {{

            font-size: 1.30rem;

            font-weight: 900;

            color: {accent};

            letter-spacing: 0.5px;

            line-height: 1;

        }}

        .sdash-card-sname {{

            font-size: 0.85rem;

            font-weight: 500;

            color: {cp_text2};

            white-space: nowrap;

            overflow: hidden;

            text-overflow: ellipsis;

            max-width: 240px;

            line-height: 1;

        }}

        .sdash-card-dot {{

            display: none;

        }}

        .sdash-card-regime {{

            flex-shrink: 0;

            font-size: 0.72rem; font-weight: 700;

            text-transform: uppercase; letter-spacing: 0.9px;

            border: 1px solid; border-radius: 20px;

            padding: 0.25rem 0.80rem; white-space: nowrap;

            opacity: 0.90;

        }}

        .sdash-card-tag {{

            font-size: 0.80rem; font-weight: 700;

            color: {accent};

            background: rgba(38,166,154,0.10);

            border: 1px solid rgba(38,166,154,0.25);

            border-radius: 5px;

            padding: 0.18rem 0.60rem;

            white-space: nowrap;

        }}

        .sdash-card-plus {{ font-size: 0.76rem; color: {cp_text3}; font-weight: 600; }}



        /* per-strategy sub-section */

        .sdash-strat {{ border-top: 1px solid #303030; }}

        .sdash-strat-head {{

            display: flex; align-items: center; gap: 0.5rem;

            padding: 0.6rem 1.3rem;

            border-bottom: 1px solid {cp_b2};

            background: {cp_s2};

            flex-wrap: wrap;

        }}



        /* stats grid */

        .sdash-card-body {{

            display: grid;

            grid-template-columns: repeat(3, 1fr);

            background: {cp_s1};

        }}

        .sdash-stat {{

            display: flex; flex-direction: column;

            align-items: flex-start;

            padding: 0.85rem 1rem 0.80rem 1rem;

            border-right: 1px solid {cp_b2};

            border-bottom: 1px solid {cp_b2};

            gap: 0.18rem;

            position: relative;

        }}

        .sdash-stat:nth-child(3n) {{ border-right: none; }}

        .sdash-stat:nth-child(4),

        .sdash-stat:nth-child(5),

        .sdash-stat:nth-child(6) {{ border-bottom: none; }}

        /* coloured top-edge accent per stat type */

        .sdash-stat--wr    {{ border-top: 2px solid {accent}; }}

        .sdash-stat--entry {{ border-top: 2px solid #22c55e; }}

        .sdash-stat--exit  {{ border-top: 2px solid {accent}; }}

        .sdash-stat--sig   {{ border-top: 2px solid {cp_b1}; }}

        .sdash-stat--stop  {{ border-top: 2px solid #ef5350; }}

        .sdash-stat--profit{{ border-top: 2px solid #22c55e; }}

        .sdash-stat-lbl {{

            font-size: 0.68rem; font-weight: 700;

            text-transform: uppercase; letter-spacing: 0.9px;

            color: {cp_text3}; opacity: 0.85;

        }}

        .sdash-stat-val {{

            font-size: 1.05rem; font-weight: 800;

            color: {cp_text1}; line-height: 1;

            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;

            white-space: nowrap;

        }}

        /* win-rate progress bar */

        .sdash-wr-bar-wrap {{

            width: 100%; height: 3px;

            background: rgba(255,255,255,0.07);

            border-radius: 2px; margin-top: 0.32rem;

        }}

        .sdash-wr-bar {{

            height: 100%; border-radius: 2px;

            transition: width 0.4s ease;

        }}



        /* ?? Form labels - Box Style ?? */

        .cp-input-label {{

            font-size: 0.75rem;

            color: #9e9e9e;

            text-transform: none;

            letter-spacing: 0;

            margin-bottom: 0.4rem;

            font-weight: 500;

            display: block;

        }}



        /* ?? Indicators section header - Box Style ?? */

        .cp-ind-hdr {{

            font-size: 0.75rem;

            font-weight: 600;

            text-transform: none;

            letter-spacing: 0;

            color: #ffffff;

            margin: 1.25rem 0 0.75rem 0;

            display: flex;

            align-items: center;

            gap: 0;

        }}

        .cp-ind-hdr::before {{

            display: none;

        }}

        .cp-ind-hdr::after {{

            content: '';

            flex: 1;

            height: 1px;

            background: {cp_b2};

        }}



        /* ?? Category rows ?? */

        .cp-cat {{

            display: flex;

            align-items: center;

            gap: 0.4rem;

            font-size: 0.62rem;

            font-weight: 600;

            text-transform: uppercase;

            letter-spacing: 0.5px;

            margin: 0.8rem 0 0.4rem 0;

            color: #757575;

        }}

        .cp-cat-dot {{

            width: 5px; height: 5px;

            border-radius: 50%;

            flex-shrink: 0;

        }}



        /* ?? Indicator chips ?? */

        .st-key-ind_panel [data-testid="stHorizontalBlock"] {{ gap: 0.35rem !important; }}

        .st-key-ind_panel [data-testid="column"] {{

            padding: 0 !important;

            min-width: 0 !important;

            flex-shrink: 1 !important;

        }}

        .st-key-ind_panel .stCheckbox {{

            width: 100% !important;

            margin: 0 !important;

            padding: 0 !important;

        }}

        .st-key-ind_panel .stCheckbox label[data-testid="stCheckboxWidget"] {{

            display: flex !important;

            justify-content: center !important;

            align-items: center !important;

            width: 100% !important;

            min-height: 2rem !important;

            padding: 0.25rem 0.2rem !important;

            border-radius: 6px !important;

            border: 1px solid #404040 !important;

            background: #303030 !important;

            cursor: pointer !important;

            transition: border-color 0.12s, background 0.12s !important;

            gap: 0 !important;

            box-sizing: border-box !important;

        }}

        .st-key-ind_panel .stCheckbox label[data-testid="stCheckboxWidget"]:hover {{

            border-color: #26A69A !important;

            background: #383838 !important;

        }}

        .st-key-ind_panel .stCheckbox:has(input:checked) label[data-testid="stCheckboxWidget"] {{

            background: rgba(38,166,154,0.2) !important;

            border-color: #26A69A !important;

        }}

        .st-key-ind_panel .stCheckbox label[data-testid="stCheckboxWidget"] > :first-child {{

            display: none !important;

        }}

        .st-key-ind_panel .stCheckbox label[data-testid="stCheckboxWidget"] p,

        .st-key-ind_panel .stCheckbox label[data-testid="stCheckboxWidget"] span {{

            margin: 0 !important;

            font-size: 0.68rem !important;

            font-weight: 600 !important;

            color: #9e9e9e !important;

            text-align: center !important;

            line-height: 1 !important;

            white-space: nowrap !important;

            overflow: hidden !important;

            text-overflow: ellipsis !important;

        }}

        .st-key-ind_panel .stCheckbox:has(input:checked) label[data-testid="stCheckboxWidget"] p,

        .st-key-ind_panel .stCheckbox:has(input:checked) label[data-testid="stCheckboxWidget"] span {{

            color: #4caf50 !important;

            font-weight: 700 !important;

        }}



        /* ?? Inputs - Box Style ?? */

        .stTextInput > div > div > input,

        .stDateInput input,

        .stDateInput [data-baseweb="input"] {{

            background-color: #303030 !important;

            border: 1px solid #404040 !important;

            color: #ffffff !important;

            border-radius: 8px !important;

            min-height: 2.5rem !important;

            font-size: 0.85rem !important;

            padding: 0 0.875rem !important;

        }}

        .stTextInput > div > div > input:focus {{

            background-color: #303030 !important;

            border-color: #26A69A !important;

            box-shadow: none !important;

            outline: none !important;

        }}



        /* ?? Run button - Box Style ?? */

        .cp-run-wrap {{ margin-top: 1.5rem; }}

        .cp-run-wrap .stButton > button {{

            background: #26A69A !important;

            color: #ffffff !important;

            border: none !important;

            border-radius: 8px !important;

            min-height: 44px !important;

            font-size: 0.85rem !important;

            font-weight: 600 !important;

            letter-spacing: 0 !important;

            transition: all 0.15s ease !important;

            width: 100% !important;

        }}

        .cp-run-wrap .stButton > button:hover {{

            background: #2bbc9e !important;

        }}

        .cp-run-wrap .stButton > button:active {{

            background: #219686 !important;

        }}



        /* ?? Favorites panel ?? */

        .st-key-fav_panel_wrap {{

            background: {cp_s1} !important;

            border: 1px solid {cp_b1} !important;

            border-radius: 14px !important;

            padding: 1.4rem 1.8rem 1.6rem 1.8rem !important;

            box-sizing: border-box !important;

            margin-bottom: 1rem !important;

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

        .st-key-fav_close_panel .stButton > button {{

            background: transparent !important;

            border: 1px solid rgba(239,83,80,0.30) !important;

            border-radius: 7px !important;

            color: rgba(239,83,80,0.70) !important;

            height: 2rem !important;

            min-height: 2rem !important;

            font-size: 0.70rem !important;

            font-weight: 700 !important;

            padding: 0 0.85rem !important;

            transition: all 0.12s ease !important;

        }}

        .st-key-fav_close_panel .stButton > button:hover {{

            background: rgba(239,83,80,0.10) !important;

            border-color: rgba(239,83,80,0.60) !important;

            color: #ef5350 !important;

        }}

        [class*="st-key-fav_del_"] .stButton > button {{

            background: transparent !important;

            border: 1px solid rgba(239,83,80,0.22) !important;

            border-radius: 8px !important;

            color: rgba(239,83,80,0.50) !important;

            min-height: 6rem !important;

            height: 100% !important;

            font-size: 1rem !important;

            padding: 0 !important;

            transition: all 0.12s ease !important;

        }}

        [class*="st-key-fav_del_"] .stButton > button:hover {{

            background: rgba(239,83,80,0.10) !important;

            border-color: rgba(239,83,80,0.55) !important;

            color: #ef5350 !important;

        }}

        .fav-hdr {{ display:flex; align-items:center; gap:0.55rem;

                    padding-bottom:0.85rem; margin-bottom:0.85rem;

                    border-bottom:1px solid {cp_b2}; }}

        .fav-hdr-icon {{ font-size:1.1rem; }}

        .fav-hdr-title {{ font-size:0.88rem; font-weight:700; color:{cp_text1};

                          flex:1; letter-spacing:-0.1px; }}

        .fav-hdr-count {{ background:rgba(244,114,182,0.10);

                          border:1px solid rgba(244,114,182,0.25);

                          color:#f472b6; font-size:0.63rem; font-weight:700;

                          border-radius:20px; padding:0.10rem 0.5rem; }}

        .fav-empty {{ display:flex; flex-direction:column; align-items:center;

                      padding:2rem 1rem; gap:0.5rem; }}

        .fav-empty-icon {{ font-size:2.2rem; opacity:0.18; }}

        .fav-empty-txt {{ font-size:0.73rem; color:{cp_text2}; text-align:center;

                          font-weight:500; max-width:320px; line-height:1.7;

                          opacity:0.75; }}

        .fav-card {{

            background: {cp_s2};

            border: 1px solid {cp_b2};

            border-radius: 10px;

            overflow: hidden;

            margin-bottom: 0.5rem;

        }}

        .fav-card-top {{

            display: flex;

            align-items: center;

            gap: 0.65rem;

            padding: 0.8rem 1rem 0.7rem 1rem;

            border-bottom: 1px solid {cp_b2};

            flex-wrap: wrap;

        }}

        .fav-sym {{

            background: rgba(244,114,182,0.10);

            border: 1px solid rgba(244,114,182,0.25);

            border-radius: 6px;

            padding: 0.18rem 0.6rem;

            font-size: 0.76rem; font-weight: 800;

            color: #f472b6; letter-spacing: 0.4px;

        }}

        .fav-sep {{ color:{cp_text3}; opacity:0.40; font-weight:300; font-size:1rem; }}

        .fav-pill {{

            background: rgba(38,166,154,0.10);

            border: 1px solid rgba(38,166,154,0.22);

            border-radius: 5px; padding: 0.13rem 0.5rem;

            font-size: 0.67rem; font-weight: 700; color: #26A69A;

        }}

        .fav-plus {{ font-size:0.63rem; color:{cp_text3}; font-weight:600; }}

        .fav-regime {{

            margin-left: auto;

            font-size: 0.58rem; font-weight: 700;

            text-transform: uppercase; letter-spacing: 0.6px;

            border-radius: 5px; padding: 0.13rem 0.5rem;

            border: 1px solid currentColor; opacity: 0.85;

        }}

        .fav-date {{

            font-size: 0.57rem; color: {cp_text3}; opacity: 0.60;

            margin-left: 0.15rem; align-self: center;

        }}

        .fav-card-bot {{

            display: grid;

            grid-template-columns: repeat(4, 1fr);

            padding: 0.7rem 1rem 0.75rem 1rem;

            gap: 0;

        }}

        .fav-si {{

            display: flex; flex-direction: column;

            align-items: center; justify-content: center;

            padding: 0.18rem 0;

        }}

        .fav-si:not(:last-child) {{

            border-right: 1px solid {cp_b2};

        }}

        .fsl {{

            font-size: 0.51rem; font-weight: 700;

            text-transform: uppercase; letter-spacing: 0.7px;

            color: {cp_text3}; margin-bottom: 0.2rem; opacity: 0.70;

        }}

        .fsv {{

            font-size: 0.90rem; font-weight: 800;

            color: {cp_text1}; line-height: 1;

        }}

        

        /* ??????????????????????????????????????????????????????????????

           DASHBOARD - COMPLETE PREMIUM REDESIGN

           Modern glassmorphism + monochrome + accent colors

           ?????????????????????????????????????????????????????????????? */

        

        /* Main wrapper */

        .dash-main {{

            padding: 0;

        }}

        

        /* Hero Stats Row - Box Style */

        .dash-hero {{

            display: grid;

            grid-template-columns: repeat(4, 1fr);

            gap: 1rem;

            margin-bottom: 2rem;

        }}

        .dash-stat-card {{

            background: #212121;

            border: 1px solid #303030;

            border-radius: 12px;

            padding: 1.25rem 1rem;

            transition: all 0.15s ease;

        }}

        .dash-stat-card:hover {{

            background: #2a2a2a;

            border-color: #404040;

        }}

        

        .dash-stat-label {{

            font-size: 0.7rem;

            font-weight: 500;

            color: #9e9e9e;

            margin-bottom: 0.5rem;

            letter-spacing: 0.1px;

        }}

        .dash-stat-value {{

            font-size: 1.75rem;

            font-weight: 600;

            letter-spacing: -1px;

            line-height: 1;

            margin-bottom: 0.3rem;

        }}

        .dash-stat-value.gain {{ color: #4caf50; }}

        .dash-stat-value.loss {{ color: #f44336; }}

        .dash-stat-value.neutral {{ color: #9e9e9e; }}

        .dash-stat-value.info {{ color: #2196f3; }}

        .dash-stat-sub {{

            font-size: 0.68rem;

            color: #757575;

            font-weight: 400;

        }}

        

        /* Spacer for clean layout */

        .dash-spacer {{

            margin-bottom: 2rem;

        }}

        

        /* Period Tabs - Apple Segmented Control */

        .st-key-dash_period_row [data-testid="stHorizontalBlock"] {{

            gap: 0 !important;

            background: rgba(255,255,255,0.06) !important;

            padding: 0.25rem !important;

            border-radius: 12px !important;

            border: none !important;

            width: fit-content !important;

            margin: 0 auto 2rem auto !important;

        }}

        .st-key-dash_period_row .stButton > button {{

            background: transparent !important;

            border: none !important;

            border-radius: 10px !important;

            color: rgba(255,255,255,0.5) !important;

            font-size: 0.75rem !important;

            font-weight: 500 !important;

            padding: 0.6rem 1.25rem !important;

            min-height: 0 !important;

            letter-spacing: 0 !important;

            transition: all 0.12s ease !important;

        }}

        .st-key-dash_period_row .stButton > button:hover {{

            background: rgba(255,255,255,0.04) !important;

            color: rgba(255,255,255,0.8) !important;

        }}

        [class*="st-key-dash_p_active"] .stButton > button {{

            background: rgba(255,255,255,0.1) !important;

            color: rgba(255,255,255,0.95) !important;

            font-weight: 600 !important;

        }}

        

        /* Status Indicator - Box Style */

        .dash-status {{

            display: inline-flex;

            align-items: center;

            gap: 6px;

            font-size: 0.72rem;

            font-weight: 500;

            letter-spacing: 0.3px;

            padding: 0.45rem 1rem;

            border-radius: 8px;

            background: #212121;

            border: 1px solid #303030;

        }}

        .dash-status.open {{

            color: #4caf50;

        }}

        .dash-status.closed {{

            color: #f44336;

        }}

        .dash-status-dot {{

            width: 6px;

            height: 6px;

            border-radius: 50%;

        }}

        .dash-status.open .dash-status-dot {{ 

            background: #4caf50;

            animation: pulse-dot 2s ease-in-out infinite;

        }}

        .dash-status.closed .dash-status-dot {{ 

            background: #f44336;

        }}

        @keyframes pulse-dot {{

            0%, 100% {{ opacity: 1; }}

            50% {{ opacity: 0.4; }}

        }}

        

        /* Header Bar - Box Style */

        .dash-header {{

            display: flex;

            align-items: center;

            justify-content: space-between;

            margin-bottom: 1.5rem;

            padding: 1.25rem 1.5rem;

            background: #212121;

            border: 1px solid #303030;

            border-radius: 12px;

        }}

        .dash-header-left {{

            display: flex;

            flex-direction: column;

            gap: 0.2rem;

        }}

        .dash-title {{

            font-size: 1.25rem;

            font-weight: 600;

            color: #ffffff;

            letter-spacing: -0.3px;

            line-height: 1.2;

        }}

        .dash-subtitle {{

            font-size: 0.75rem;

            color: #9e9e9e;

            font-weight: 400;

        }}

        .dash-header-right {{

            display: flex;

            align-items: center;

            gap: 1rem;

        }}

        .dash-time {{

            font-size: 0.8rem;

            color: #757575;

            font-weight: 400;

        }}

        

        /* Loading State - Box Style */

        .dash-loading {{

            display: flex;

            flex-direction: column;

            align-items: center;

            justify-content: center;

            padding: 4rem 2rem;

            text-align: center;

            background: #212121;

            border: 1px solid #303030;

            border-radius: 12px;

        }}

        .dash-loading-spinner {{

            width: 28px;

            height: 28px;

            border: 2px solid #303030;

            border-top-color: #26A69A;

            border-radius: 50%;

            animation: spin 0.8s linear infinite;

            margin-bottom: 1rem;

        }}

        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

        .dash-loading-text {{

            font-size: 0.85rem;

            color: #ffffff;

            font-weight: 500;

        }}

        .dash-loading-sub {{

            font-size: 0.72rem;

            color: #757575;

            margin-top: 0.3rem;

        }}

        

        /* Legacy styles - keep for other parts */

        .mkt-wrap {{ display: none; }}

        

        /* Market Analysis Tool CSS */

        .ma-results {{

            margin-top: 1rem;

        }}

        .ma-section {{

            background: #212121;

            border: 1px solid #303030;

            border-radius: 10px;

            margin-bottom: 1rem;

            overflow: hidden;

        }}

        .ma-section-header {{

            padding: 1rem 1.2rem;

            display: flex;

            align-items: center;

            justify-content: space-between;

        }}

        .ma-section-header.buy {{

            background: rgba(38,166,154,0.1);

            border-bottom: 1px solid #303030;

        }}

        .ma-section-header.sell {{

            background: rgba(239,83,80,0.08);

            border-bottom: 1px solid #303030;

        }}

        .ma-section-header.hold {{

            background: rgba(255,193,7,0.08);

            border-bottom: 1px solid #303030;

        }}

        .ma-section-title {{

            font-size: 0.85rem;

            font-weight: 700;

            text-transform: uppercase;

            letter-spacing: 0.5px;

        }}

        .ma-section-title.buy {{ color: #4caf50; }}

        .ma-section-title.sell {{ color: #f44336; }}

        .ma-section-title.hold {{ color: #ff9800; }}

        .ma-section-count {{

            font-size: 0.7rem;

            font-weight: 600;

            padding: 0.25rem 0.6rem;

            border-radius: 6px;

            background: #303030;

            color: #9e9e9e;

        }}

        .ma-stock {{

            padding: 1rem 1.2rem;

            border-bottom: 1px solid #303030;

        }}

        .ma-stock:last-child {{ border-bottom: none; }}

        .ma-stock-top {{

            display: flex;

            align-items: center;

            justify-content: space-between;

            margin-bottom: 0.6rem;

        }}

        .ma-stock-info {{

            display: flex;

            align-items: center;

            gap: 1rem;

        }}

        .ma-stock-ticker {{

            font-size: 0.95rem;

            font-weight: 700;

            color: #2196f3;

        }}

        .ma-stock-price {{

            font-size: 0.85rem;

            font-weight: 600;

            color: #ffffff;

        }}

        .ma-stock-score {{

            font-size: 0.72rem;

            font-weight: 600;

            padding: 0.3rem 0.75rem;

            border-radius: 6px;

        }}

        .ma-stock-score.buy {{

            background: rgba(76,175,80,0.15);

            color: #4caf50;

        }}

        .ma-stock-score.sell {{

            background: rgba(244,67,54,0.12);

            color: #f44336;

        }}

        .ma-signals {{

            display: flex;

            flex-wrap: wrap;

            gap: 0.4rem;

            margin-bottom: 0.8rem;

        }}

        .ma-signal {{

            font-size: 0.62rem;

            font-weight: 600;

            padding: 0.25rem 0.5rem;

            background: #303030;

            border: 1px solid #404040;

            border-radius: 4px;

            color: #9e9e9e;

        }}

        .ma-levels {{

            display: grid;

            grid-template-columns: repeat(4, 1fr);

            gap: 0.5rem;

        }}

        .ma-level {{

            text-align: center;

            padding: 0.5rem;

            background: #303030;

            border-radius: 6px;

        }}

        .ma-level-val {{

            font-size: 0.82rem;

            font-weight: 600;

            color: #ffffff;

        }}

        .ma-level-val.entry {{ color: #2196f3; }}

        .ma-level-val.stop {{ color: #f44336; }}

        .ma-level-val.target {{ color: #4caf50; }}

        .ma-level-val.pot {{ color: #ff9800; }}

        .ma-level-lbl {{

            font-size: 0.55rem;

            font-weight: 600;

            color: #757575;

            text-transform: uppercase;

            margin-top: 0.2rem;

        }}

        

        /* All Stocks Grid */

        .mkt-stocks-header {{

            display: flex;

            justify-content: space-between;

            align-items: center;

            margin-bottom: 0.75rem;

        }}

        .mkt-stocks-title {{

            font-size: 0.8rem;

            font-weight: 700;

            color: {cp_text1};

        }}

        .mkt-stocks-info {{

            font-size: 0.65rem;

            color: {cp_text3};

        }}

        .mkt-grid {{

            display: grid;

            grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));

            gap: 0.5rem;

            max-height: 400px;

            overflow-y: auto;

            padding-right: 0.25rem;

        }}

        .mkt-grid::-webkit-scrollbar {{ width: 4px; }}

        .mkt-grid::-webkit-scrollbar-track {{ background: {cp_b1}; border-radius: 2px; }}

        .mkt-grid::-webkit-scrollbar-thumb {{ background: {cp_b2}; border-radius: 2px; }}

        .mkt-card {{

            background: {cp_s2};

            border: 1px solid {cp_b2};

            border-radius: 6px;

            padding: 0.6rem 0.7rem;

            display: flex;

            justify-content: space-between;

            align-items: center;

            transition: border-color 0.12s, transform 0.1s;

        }}

        .mkt-card:hover {{

            border-color: rgba(74,158,255,0.4);

            transform: translateY(-1px);

        }}

        .mkt-card-ticker {{

            font-size: 0.78rem;

            font-weight: 800;

            color: #4A9EFF;

        }}

        .mkt-card-name {{

            font-size: 0.58rem;

            color: {cp_text3};

            margin-top: 1px;

        }}

        .mkt-card-price {{

            font-size: 0.72rem;

            font-weight: 700;

            color: {cp_text1};

            text-align: right;

        }}

        .mkt-card-chg {{

            font-size: 0.68rem;

            font-weight: 700;

            text-align: right;

        }}

        .mkt-card-chg.up {{ color: #26A69A; }}

        .mkt-card-chg.down {{ color: #ef5350; }}

        </style>""", unsafe_allow_html=True)

        # ??????????????????????????????????????????????????????????????
        # FETCH MARKET DATA FIRST FOR SIDEBAR
        # ══════════════════════════════════════════════════════════════════════
        market_status = get_saudi_market_status()
        if 'mkt_period' not in st.session_state:
            st.session_state.mkt_period = '1d'
        market_data = get_saudi_market_data(period=st.session_state.mkt_period)

        # ══════════════════════════════════════════════════════════════════════
        # CONTROL PANEL - Clean toolbar + Market Cards
        # ══════════════════════════════════════════════════════════════════════
        market_time = market_status.get('saudi_time', '--:--') if market_status else '--:--'
        is_open = market_status.get('is_open', False) if market_status else False
        status_detail = market_status.get('status_detail', '') if market_status else ''
        gainers = market_data.get('gainers', 0) if market_data else 0
        losers = market_data.get('losers', 0) if market_data else 0
        unchanged = market_data.get('unchanged', 0) if market_data else 0
        avg_change = market_data.get('avg_change', 0) if market_data else 0
        sentiment = market_data.get('sentiment', 'NEUTRAL') if market_data else 'NEUTRAL'
        tasi_price = market_data.get('tasi_price', 0) if market_data else 0
        tasi_change = market_data.get('tasi_change', 0) if market_data else 0
        
        perf_color = "#26A69A" if avg_change >= 0 else "#ef5350"
        perf_sign = "+" if avg_change >= 0 else ""
        sent_colors = {"STRONG BUY": "#4caf50", "BULLISH": "#26A69A", "NEUTRAL": "#ffc107", "BEARISH": "#ef5350", "STRONG SELL": "#f44336"}
        sent_color = sent_colors.get(sentiment, "#9e9e9e")
        status_class = "open" if is_open else "closed"
        
        # Theme & favorites state
        current_theme = st.session_state.get("ui_theme", "dark")
        is_dark = current_theme == "dark"
        theme_icon = "☀" if is_dark else "☽"
        fav_count = len(st.session_state.get('favorites', []))
        has_favs = fav_count > 0
        username = st.session_state.auth_username
        
        # User panel toggle
        if 'show_user_panel' not in st.session_state:
            st.session_state.show_user_panel = False
        
        st.markdown(f"""
        <style>
        header[data-testid="stHeader"] {{ display: none !important; }}

        /* ── Two-panel layout ─────────────────────────────────────────────── */
        .st-key-cp_row > div:first-child > [data-testid="stHorizontalBlock"] {{
            align-items: stretch !important;
            gap: 1.4rem !important;
        }}
        .st-key-cp_row > div:first-child > [data-testid="stHorizontalBlock"]
            > [data-testid="column"] {{
            padding: 0 !important;
        }}

        /* ── Left panel (status + buttons) ───────────────────────────────── */
        .st-key-left_panel > div > [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-left_panel > div > [data-testid="stVerticalBlock"] {{
            background: transparent !important;
            border: none !important; box-shadow: none !important; padding: 0 !important;
        }}
        .st-key-left_panel > div:first-child {{
            background: #181c1f !important;
            border: 1px solid #252b2e !important;
            border-radius: 20px !important;
            padding: 1.8rem !important;
            height: 100% !important;
            box-sizing: border-box !important;
        }}

        /* ── Right panel (tabs) ───────────────────────────────────────────── */
        .st-key-right_panel > div > [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-right_panel > div > [data-testid="stVerticalBlock"] {{
            background: transparent !important;
            border: none !important; box-shadow: none !important; padding: 0 !important;
        }}
        .st-key-right_panel > div:first-child {{
            background: #181c1f !important;
            border: 1px solid #252b2e !important;
            border-radius: 20px !important;
            padding: 1.8rem !important;
            height: 100% !important;
            box-sizing: border-box !important;
        }}

        /* ── Tab strip ────────────────────────────────────────────────────── */
        .st-key-right_panel .stTabs [data-baseweb="tab-list"] {{
            background: #0f1214 !important;
            border-radius: 12px !important;
            padding: 4px !important;
            gap: 2px !important;
            border: 1px solid #252b2e !important;
            margin-bottom: 1.4rem !important;
        }}
        .st-key-right_panel .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            color: #5a6470 !important;
            border-radius: 9px !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.3px !important;
            padding: 0.45rem 1.1rem !important;
            border: none !important;
            flex: 1 !important;
            justify-content: center !important;
        }}
        .st-key-right_panel .stTabs [aria-selected="true"] {{
            background: #26A69A !important;
            color: #fff !important;
        }}
        .st-key-right_panel .stTabs [data-baseweb="tab-border"] {{
            display: none !important;
        }}
        .st-key-right_panel .stTabs [data-baseweb="tab-panel"] {{
            padding: 0 !important;
        }}

        /* ── Left panel: zero out inner column padding so buttons stay inside card ── */
        .st-key-left_panel [data-testid="stHorizontalBlock"] {{
            gap: 0.45rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.25rem !important;
        }}
        .st-key-left_panel [data-testid="column"] {{
            padding: 0 !important;
            min-width: 0 !important;
        }}

        /* ── Brand header ───────────────────────────────────────────────────── */
        .lp-brand {{
            font-size: 1.2rem; font-weight: 800; color: #e8e8e8;
            letter-spacing: -0.5px; line-height: 1;
        }}
        .lp-brand span {{ color: #26A69A; }}
        .lp-tagline {{
            font-size: 0.56rem; color: #2e4040; font-weight: 700;
            text-transform: uppercase; letter-spacing: 1.2px; margin-top: 5px;
        }}

        /* ── Action buttons ─────────────────────────────────────────────────── */
        .st-key-btn_saved .stButton > button {{
            background: rgba(38,166,154,0.07) !important;
            border: 1px solid rgba(38,166,154,0.2) !important;
            border-radius: 10px !important;
            color: #26A69A !important;
            font-size: 0.77rem !important; font-weight: 700 !important;
            width: 100% !important; padding: 0.52rem 0.3rem !important;
            height: auto !important; white-space: nowrap !important;
            letter-spacing: 0.2px !important;
        }}
        .st-key-btn_saved .stButton > button:hover {{
            background: rgba(38,166,154,0.15) !important;
            border-color: rgba(38,166,154,0.45) !important;
        }}
        .st-key-btn_user .stButton > button {{
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid #252b2e !important;
            border-radius: 10px !important;
            color: #6b7a86 !important;
            font-size: 0.77rem !important; font-weight: 600 !important;
            width: 100% !important; padding: 0.52rem 0.3rem !important;
            height: auto !important; white-space: nowrap !important;
        }}
        .st-key-btn_user .stButton > button:hover {{
            background: rgba(255,255,255,0.07) !important;
            border-color: #3a4550 !important; color: #c8d6e5 !important;
        }}
        .st-key-btn_pulse .stButton > button {{
            background: rgba(74,158,255,0.07) !important;
            border: 1px solid rgba(74,158,255,0.22) !important;
            border-radius: 10px !important;
            color: #4A9EFF !important;
            font-size: 0.77rem !important; font-weight: 700 !important;
            width: 100% !important; padding: 0.52rem 0.3rem !important;
            height: auto !important; white-space: nowrap !important;
            letter-spacing: 0.2px !important;
        }}
        .st-key-btn_pulse .stButton > button:hover {{
            background: rgba(74,158,255,0.16) !important;
            border-color: rgba(74,158,255,0.5) !important;
        }}

        /* ── User panel ───────────────────────────────────────────────────── */
        .st-key-user_panel_wrap > div:first-child {{
            background: #1a1e21 !important;
            border: 1px solid #252b2e !important;
            border-radius: 14px !important;
            padding: 1.2rem !important;
            max-width: 260px !important;
            margin-bottom: 1rem !important;
        }}
        .user-panel-hdr {{ display:flex; align-items:center; gap:0.8rem;
           padding-bottom:0.9rem; border-bottom:1px solid #252b2e; margin-bottom:0.9rem; }}
        .user-avatar {{ width:42px; height:42px; border-radius:10px;
           background:linear-gradient(135deg,#26A69A,#00897b);
           display:flex; align-items:center; justify-content:center;
           font-size:1.1rem; font-weight:700; color:#fff; flex-shrink:0; }}
        .user-info-name {{ font-size:0.95rem; font-weight:700; color:#fff; }}
        .user-info-role {{ font-size:0.68rem; color:#4a5568; margin-top:2px; }}
        .user-panel-stats {{ display:flex; gap:0.6rem; margin-bottom:0.9rem; }}
        .user-stat {{ flex:1; text-align:center; padding:0.6rem 0.4rem;
           background:#252b2e; border-radius:9px; }}
        .user-stat-value {{ font-size:1rem; font-weight:700; color:#26A69A; }}
        .user-stat-label {{ font-size:0.58rem; color:#4a5568; text-transform:uppercase;
           letter-spacing:0.5px; margin-top:2px; }}
        .st-key-logout_btn .stButton > button {{
            background: rgba(239,83,80,0.07) !important;
            border: 1px solid rgba(239,83,80,0.22) !important;
            border-radius: 9px !important; color: #ef5350 !important;
            font-size:0.8rem !important; font-weight:600 !important;
            width:100% !important; padding:0.55rem !important;
        }}

        /* ── Market stat cards ─────────────────────────────────────────────── */
        .mstat-card {{
            background: #0f1214;
            border: 1px solid #1e2428;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-top: 0.75rem;
        }}
        .mstat-label {{
            font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.8px; color: #3a4550; margin-bottom: 0.5rem;
        }}
        .mstat-value {{ font-size: 1.55rem; font-weight: 800; line-height: 1;
            letter-spacing: -0.5px; color: #e8e8e8; }}
        .mstat-sub {{ font-size: 0.65rem; color: #3a4550; margin-top: 0.35rem; }}
        .mstat-badge-open  {{ display:inline-flex; align-items:center; gap:5px;
            padding:3px 10px; border-radius:999px; font-size:0.6rem; font-weight:700;
            letter-spacing:0.5px; text-transform:uppercase;
            background:rgba(38,166,154,0.12); color:#26A69A; }}
        .mstat-badge-closed {{ display:inline-flex; align-items:center; gap:5px;
            padding:3px 10px; border-radius:999px; font-size:0.6rem; font-weight:700;
            letter-spacing:0.5px; text-transform:uppercase;
            background:rgba(239,83,80,0.12); color:#ef5350; }}
        .mstat-dot {{ width:6px; height:6px; border-radius:50%;
            animation: mstat-pulse 2s ease-in-out infinite; }}
        .mstat-badge-open  .mstat-dot {{ background:#26A69A; }}
        .mstat-badge-closed .mstat-dot {{ background:#ef5350; }}
        @keyframes mstat-pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}
        .mstat-row {{ display:flex; align-items:center;
            justify-content:space-between; gap:0.5rem; }}
        .mstat-breadth {{ margin-top:0.6rem; }}
        .mstat-bar {{ display:flex; border-radius:6px; overflow:hidden;
            height:6px; margin-bottom:0.65rem; gap:2px; }}
        .mstat-bar-up   {{ background:#26A69A; border-radius:6px; }}
        .mstat-bar-down {{ background:#ef5350; border-radius:6px; }}
        .mstat-bar-flat {{ background:#2a3240; border-radius:6px; }}
        .mstat-bcells {{ display:flex; gap:0.5rem; }}

        /* ── Period selector pills ─────────────────────────────────────────── */
        .st-key-prd_row [data-testid="stHorizontalBlock"] {{ gap:0.18rem !important; margin-top:0.55rem !important; margin-bottom:0.2rem !important; }}
        .st-key-prd_row [data-testid="column"] {{ padding:0 !important; min-width:0 !important; }}
        .st-key-mkt_p_1d .stButton > button,
        .st-key-mkt_p_1w .stButton > button,
        .st-key-mkt_p_1m .stButton > button,
        .st-key-mkt_p_3m .stButton > button,
        .st-key-mkt_p_6m .stButton > button,
        .st-key-mkt_p_1y .stButton > button {{
            background: transparent !important;
            border: 1px solid #1e2428 !important;
            color: #4a5568 !important;
            font-size: 0.6rem !important;
            font-weight: 700 !important;
            padding: 0.22rem 0 !important;
            width: 100% !important;
            border-radius: 6px !important;
            letter-spacing: 0.03em !important;
            min-height: 0 !important;
        }}
        .st-key-mkt_p_1d .stButton > button:hover,
        .st-key-mkt_p_1w .stButton > button:hover,
        .st-key-mkt_p_1m .stButton > button:hover,
        .st-key-mkt_p_3m .stButton > button:hover,
        .st-key-mkt_p_6m .stButton > button:hover,
        .st-key-mkt_p_1y .stButton > button:hover {{
            border-color: #26A69A !important;
            color: #26A69A !important;
        }}
        .mstat-bcell {{ flex:1; text-align:center; padding:0.55rem 0.3rem;
            background:#0a0d0f; border:1px solid #1e2428; border-radius:10px; }}
        .mstat-bv {{ font-size:1.15rem; font-weight:800; line-height:1; }}
        .mstat-bl {{ font-size:0.5rem; font-weight:700; color:#3a4550;
            text-transform:uppercase; letter-spacing:0.6px; margin-top:3px; }}

        /* ── Run button ────────────────────────────────────────────────────── */
        .cp-run-wrap {{ margin-top: 1.2rem !important; }}
        .st-key-right_panel .stButton > button[kind="secondary"] {{
            background: transparent !important;
            border: 1px solid #26A69A !important;
            color: #26A69A !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            letter-spacing: 0.3px !important;
            padding: 0.65rem 1rem !important;
            transition: all 0.2s !important;
        }}
        .st-key-right_panel .stButton > button[kind="secondary"]:hover {{
            background: rgba(38,166,154,0.1) !important;
        }}

        /* ── Form inputs ───────────────────────────────────────────────────── */
        .cp-input-label {{
            font-size: 0.68rem; font-weight: 600; color: #4a5568;
            text-transform: uppercase; letter-spacing: 0.6px;
            margin-bottom: 0.3rem; margin-top: 0.85rem;
        }}
        .cp-ind-hdr {{
            font-size: 0.68rem; font-weight: 600; color: #4a5568;
            text-transform: uppercase; letter-spacing: 0.6px;
            margin-top: 1rem; margin-bottom: 0.6rem;
            border-top: 1px solid #1e2428; padding-top: 0.85rem;
        }}
        .cp-cat {{ font-size: 0.72rem; font-weight: 600; margin: 0.5rem 0 0.25rem; display:flex; align-items:center; gap:0.4rem; }}
        .cp-cat-dot {{ width:7px; height:7px; border-radius:50%; display:inline-block; }}

        /* ── Toolbar wrap (no-op — layout handled by left_panel column CSS) ── */
        .st-key-btn_saved, .st-key-btn_user {{ width: 100% !important; }}
        
        /* ═══════════════════════════════════════════════════════════════════
           USER PANEL DROPDOWN - Matches app panel style
           ═══════════════════════════════════════════════════════════════════ */
        .st-key-user_panel_wrap {{
            margin-bottom: 1.25rem !important;
        }}
        .st-key-user_panel_wrap > div:first-child {{
            background: #212121 !important;
            border: 1px solid #303030 !important;
            border-radius: 14px !important;
            padding: 1.25rem !important;
            max-width: 280px !important;
        }}
        .user-panel-hdr {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #303030;
            margin-bottom: 1rem;
        }}
        .user-avatar {{
            width: 46px; height: 46px;
            border-radius: 12px;
            background: linear-gradient(135deg, #26A69A 0%, #00897b 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 700;
            color: #fff;
            flex-shrink: 0;
        }}
        .user-info-name {{
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 2px;
        }}
        .user-info-role {{
            font-size: 0.72rem;
            color: #757575;
        }}
        .user-panel-stats {{
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        .user-stat {{
            flex: 1;
            text-align: center;
            padding: 0.65rem 0.5rem;
            background: #303030;
            border-radius: 10px;
        }}
        .user-stat-value {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #26A69A;
        }}
        .user-stat-label {{
            font-size: 0.62rem;
            color: #757575;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 2px;
        }}
        .st-key-logout_btn .stButton > button {{
            background: rgba(239,83,80,0.08) !important;
            border: 1px solid rgba(239,83,80,0.25) !important;
            border-radius: 10px !important;
            color: #ef5350 !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            width: 100% !important;
            padding: 0.6rem !important;
        }}
        .st-key-logout_btn .stButton > button:hover {{
            background: rgba(239,83,80,0.15) !important;
            border-color: rgba(239,83,80,0.4) !important;
        }}
        
        /* ═══════════════════════════════════════════════════════════════════
           MARKET CARDS - Matching app panel style (#212121, #303030)
           ═══════════════════════════════════════════════════════════════════ */
        .st-key-market_row {{
            margin-bottom: 1.5rem !important;
        }}
        .st-key-market_row [data-testid="stHorizontalBlock"] {{
            gap: 1rem !important;
        }}
        .st-key-mcard_status > div:first-child,
        .st-key-mcard_perf > div:first-child,
        .st-key-mcard_breadth > div:first-child {{
            background: #212121 !important;
            border: 1px solid #303030 !important;
            border-radius: 14px !important;
            padding: 1.25rem !important;
        }}
        .mkt-title {{
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: #757575;
            margin-bottom: 0.75rem;
        }}
        .mkt-main-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
        }}
        .mkt-value {{
            font-size: 1.65rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.5px;
            line-height: 1;
        }}
        .mkt-sub {{
            font-size: 0.72rem;
            color: #757575;
            margin-top: 0.5rem;
        }}
        .mkt-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.4px;
            text-transform: uppercase;
        }}
        .mkt-badge.open {{
            background: rgba(38,166,154,0.12);
            color: #26A69A;
        }}
        .mkt-badge.closed {{
            background: rgba(239,83,80,0.12);
            color: #ef5350;
        }}
        .mkt-dot {{
            width: 7px; height: 7px;
            border-radius: 50%;
            animation: mkt-pulse 2s ease-in-out infinite;
        }}
        .mkt-badge.open .mkt-dot {{ background: #26A69A; }}
        .mkt-badge.closed .mkt-dot {{ background: #ef5350; }}
        @keyframes mkt-pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.35; }}
        }}
        .mkt-sent {{
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.3px;
        }}
        .mkt-breadth-grid {{
            display: flex;
            gap: 0.65rem;
            margin-top: 0.25rem;
        }}
        .mkt-breadth-box {{
            flex: 1;
            text-align: center;
            padding: 0.7rem 0.5rem;
            background: #303030;
            border-radius: 10px;
        }}
        .mkt-breadth-num {{
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1;
        }}
        .mkt-breadth-num.up {{ color: #26A69A; }}
        .mkt-breadth-num.down {{ color: #ef5350; }}
        .mkt-breadth-num.flat {{ color: #757575; }}
        .mkt-breadth-lbl {{
            font-size: 0.62rem;
            color: #757575;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-top: 4px;
        }}
        </style>
        """, unsafe_allow_html=True)

        # ── User panel toggle init ─────────────────────────────────────────
        if 'show_user_panel' not in st.session_state:
            st.session_state.show_user_panel = False

        # ═══════════════════════════════════════════════════════════════════
        # TWO-PANEL LAYOUT
        # ═══════════════════════════════════════════════════════════════════
        # ── Screener auto-navigate: pre-fill symbol_input before widgets render ──
        if st.session_state.get("screener_goto"):
            _goto = st.session_state.pop("screener_goto")
            _clean = _goto.replace(".SR", "") if str(_goto).endswith(".SR") else str(_goto)
            st.session_state["symbol_input"] = _clean
            st.session_state["screener_auto_analyze"] = True

        with st.container(key="cp_row"):
            left_col, right_col = st.columns([1, 1.6], gap="large")

            # ── LEFT PANEL: branding + buttons + market stats ──────────────
            with left_col:
                with st.container(key="left_panel"):

                    # Period state + labels (used throughout left panel)
                    _ap = st.session_state.get('mkt_period', '1d')
                    _period_names = {"1d":"Today","1w":"This Week","1m":"1 Month","3m":"3 Months","6m":"6 Months","1y":"1 Year"}
                    _perf_subtitle = _period_names.get(_ap, "Today")

                    # Brand header
                    st.markdown(
                        f"<div class='lp-brand'>Tadawul<span>AI</span></div>"
                        f"<div class='lp-tagline'>Market Intelligence</div>",
                        unsafe_allow_html=True)

                    # Active period highlight (injected dynamically so only selected pill is teal)
                    st.markdown(
                        f"<style>.st-key-mkt_p_{_ap} .stButton > button "
                        f"{{ background: rgba(38,166,154,0.13) !important; "
                        f"border-color: #26A69A !important; color: #26A69A !important; }}</style>",
                        unsafe_allow_html=True)

                    # Period selector — 6 pill buttons
                    with st.container(key="prd_row"):
                        _pp = st.columns(6, gap="small")
                        for _i, (_pk, _pl) in enumerate({"1d":"1D","1w":"1W","1m":"1M","3m":"3M","6m":"6M","1y":"1Y"}.items()):
                            with _pp[_i]:
                                with st.container(key=f"mkt_p_{_pk}"):
                                    if st.button(_pl, key=f"mkt_prd_{_pk}", width="stretch"):
                                        st.session_state.mkt_period = _pk
                                        st.rerun()

                    # Action buttons — 3 columns: Saved | Pulse | User
                    _b1, _bp, _b2 = st.columns(3, gap="small")
                    with _b1:
                        with st.container(key="btn_saved"):
                            _fav_lbl = f"♡  Saved · {fav_count}" if has_favs else "♡  Saved"
                            if st.button(_fav_lbl, key="toolbar_fav", width="stretch"):
                                st.session_state.show_favorites_panel = not st.session_state.get('show_favorites_panel', False)
                                st.rerun()
                    with _bp:
                        with st.container(key="btn_pulse"):
                            if st.button("📡 Pulse", key="toolbar_pulse", width="stretch"):
                                st.session_state.show_market_pulse = True
                                st.rerun()
                    with _b2:
                        with st.container(key="btn_user"):
                            _usr_lbl = f"◉  {username[:10]}"
                            if st.button(_usr_lbl, key="toolbar_user", width="stretch"):
                                st.session_state.show_user_panel = not st.session_state.show_user_panel
                                st.rerun()

                    # User panel dropdown
                    if st.session_state.show_user_panel:
                        with st.container(key="user_panel_wrap"):
                            st.markdown(
                                f'<div class="user-panel-hdr">'
                                f'<div class="user-avatar">{username[0].upper()}</div>'
                                f'<div><div class="user-info-name">{username}</div>'
                                f'<div class="user-info-role">Premium Member</div></div></div>'
                                f'<div class="user-panel-stats">'
                                f'<div class="user-stat"><div class="user-stat-value">{fav_count}</div>'
                                f'<div class="user-stat-label">Saved</div></div>'
                                f'<div class="user-stat"><div class="user-stat-value">Pro</div>'
                                f'<div class="user-stat-label">Plan</div></div></div>',
                                unsafe_allow_html=True)
                            with st.container(key="logout_btn"):
                                if st.button("Sign Out", key="user_logout"):
                                    logout()
                                    st.rerun()

                    # Market Status card
                    open_badge = (
                        f'<span class="mstat-badge-open"><span class="mstat-dot"></span>OPEN</span>'
                        if is_open else
                        f'<span class="mstat-badge-closed"><span class="mstat-dot"></span>CLOSED</span>'
                    )
                    st.markdown(
                        f'<div class="mstat-card">'
                        f'<div class="mstat-label">Market Status</div>'
                        f'<div class="mstat-row">'
                        f'<div class="mstat-value">{market_time}</div>'
                        f'{open_badge}'
                        f'</div>'
                        f'<div class="mstat-sub">{status_detail}</div>'
                        f'</div>',
                        unsafe_allow_html=True)

                    # Performance card
                    st.markdown(
                        f'<div class="mstat-card">'
                        f'<div class="mstat-label">Performance</div>'
                        f'<div class="mstat-row">'
                        f'<div class="mstat-value" style="color:{perf_color}">'
                        f'{perf_sign}{avg_change:.2f}%</div>'
                        f'<span style="padding:3px 10px;border-radius:8px;font-size:0.65rem;'
                        f'font-weight:700;background:{sent_color}18;color:{sent_color};">'
                        f'{sentiment}</span>'
                        f'</div>'
                        f'<div class="mstat-sub">{_perf_subtitle} · avg of {gainers+losers+unchanged} stocks</div>'
                        f'</div>',
                        unsafe_allow_html=True)

                    # Breadth card
                    _total_b = max(gainers + losers + unchanged, 1)
                    _up_pct   = gainers   / _total_b * 100
                    _dn_pct   = losers    / _total_b * 100
                    _fl_pct   = unchanged / _total_b * 100
                    _tasi_color = "#26A69A" if tasi_change >= 0 else "#ef5350"
                    _tasi_sign = "+" if tasi_change >= 0 else ""
                    st.markdown(
                        f'<div class="mstat-card">'
                        f'<div class="mstat-label">Market Breadth</div>'
                        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.08);">'
                        f'<div style="font-size:0.72rem;color:#9aa0a6;font-weight:600;">TASI</div>'
                        f'<div style="display:flex;align-items:baseline;gap:8px;">'
                        f'<span style="font-size:0.85rem;font-weight:700;color:#e8eaed;">{tasi_price:,.2f}</span>'
                        f'<span style="font-size:0.72rem;font-weight:600;color:{_tasi_color};">{_tasi_sign}{tasi_change:.2f}%</span>'
                        f'</div></div>'
                        f'<div class="mstat-breadth">'
                        f'<div class="mstat-bar">'
                        f'<div class="mstat-bar-up"   style="width:{_up_pct:.1f}%"></div>'
                        f'<div class="mstat-bar-down" style="width:{_dn_pct:.1f}%"></div>'
                        f'<div class="mstat-bar-flat" style="width:{_fl_pct:.1f}%"></div>'
                        f'</div>'
                        f'<div class="mstat-bcells">'
                        f'<div class="mstat-bcell"><div class="mstat-bv" style="color:#26A69A">{gainers}</div><div class="mstat-bl">▲ Up</div></div>'
                        f'<div class="mstat-bcell"><div class="mstat-bv" style="color:#ef5350">{losers}</div><div class="mstat-bl">▼ Down</div></div>'
                        f'<div class="mstat-bcell"><div class="mstat-bv" style="color:#3a4550">{unchanged}</div><div class="mstat-bl">━ Flat</div></div>'
                        f'</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True)

            # ── RIGHT PANEL: 3-tab scanner ─────────────────────────────────
            with right_col:
                with st.container(key="right_panel"):

                    cp_tab0, cp_tab1 = st.tabs([
                        "Stock Symbol",
                        "Scan Market",
                    ])

                    # ── shared indicator block (reused in stock tab) ────────
                    def _render_indicators():
                        selected = []
                        st.markdown("<div class='cp-ind-hdr'>Indicators</div>", unsafe_allow_html=True)
                        with st.container(key="ind_panel"):
                            st.markdown("<div class='cp-cat'><span class='cp-cat-dot' style='background:#4A9EFF;'></span><span style='color:#4A9EFF;'>Trend</span></div>", unsafe_allow_html=True)
                            t = st.columns(5, gap="small")
                            with t[0]: s = st.checkbox("SMA",      value=True, key="ind_sma")
                            with t[1]: e = st.checkbox("EMA",      value=True, key="ind_ema")
                            with t[2]: p = st.checkbox("Par.SAR",  value=True, key="ind_psar")
                            with t[3]: w = st.checkbox("WMA",      value=True, key="ind_wma")
                            with t[4]: ic= st.checkbox("Ichimoku", value=True, key="ind_ichimoku")
                            if s:  selected.append('SMA')
                            if e:  selected.append('EMA')
                            if p:  selected.append('Parabolic SAR')
                            if w:  selected.append('WMA')
                            if ic: selected.append('Ichimoku')

                            st.markdown("<div class='cp-cat'><span class='cp-cat-dot' style='background:#F59E0B;'></span><span style='color:#F59E0B;'>Momentum</span></div>", unsafe_allow_html=True)
                            m = st.columns(6, gap="small")
                            with m[0]: r  = st.checkbox("RSI",   value=True, key="ind_rsi")
                            with m[1]: mc = st.checkbox("MACD",  value=True, key="ind_macd")
                            with m[2]: st_= st.checkbox("Stoch", value=True, key="ind_stoch")
                            with m[3]: ro = st.checkbox("ROC",   value=True, key="ind_roc")
                            with m[4]: cc = st.checkbox("CCI",   value=True, key="ind_cci")
                            with m[5]: wl = st.checkbox("Wm.%R", value=True, key="ind_willr")
                            if r:  selected.append('RSI')
                            if mc: selected.append('MACD')
                            if st_:selected.append('Stochastic')
                            if ro: selected.append('ROC')
                            if cc: selected.append('CCI')
                            if wl: selected.append('Williams %R')

                            st.markdown("<div class='cp-cat'><span class='cp-cat-dot' style='background:#A78BFA;'></span><span style='color:#A78BFA;'>Volatility</span></div>", unsafe_allow_html=True)
                            v = st.columns(4, gap="small")
                            with v[0]: bb = st.checkbox("Bol.Bands", value=True, key="ind_bb")
                            with v[1]: at = st.checkbox("ATR",       value=True, key="ind_atr")
                            with v[2]: ke = st.checkbox("Keltner",   value=True, key="ind_keltner")
                            with v[3]: do = st.checkbox("Donchian",  value=True, key="ind_donchian")
                            if bb: selected.append('Bollinger Bands')
                            if at: selected.append('ATR')
                            if ke: selected.append('Keltner Channel')
                            if do: selected.append('Donchian Channel')

                            st.markdown("<div class='cp-cat'><span class='cp-cat-dot' style='background:#34D399;'></span><span style='color:#34D399;'>Volume</span></div>", unsafe_allow_html=True)
                            u = st.columns(4, gap="small")
                            with u[0]: ob = st.checkbox("OBV",  value=True, key="ind_obv")
                            with u[1]: mf = st.checkbox("MFI",  value=True, key="ind_mfi")
                            with u[2]: cf = st.checkbox("CMF",  value=True, key="ind_cmf")
                            with u[3]: vw = st.checkbox("VWAP", value=True, key="ind_vwap")
                            if ob: selected.append('OBV')
                            if mf: selected.append('MFI')
                            if cf: selected.append('CMF')
                            if vw: selected.append('VWAP')

                            st.markdown("<div class='cp-cat'><span class='cp-cat-dot' style='background:#F97316;'></span><span style='color:#F97316;'>Trend Strength</span></div>", unsafe_allow_html=True)
                            ts = st.columns([1, 2], gap="small")
                            with ts[0]: adx_ = st.checkbox("ADX +DI/-DI", value=True, key="ind_adx")
                            if adx_: selected.append('ADX')
                        return selected

                    # ── Scan parameter block ────────────────────────────────
                    def _render_scan_params(suffix=""):
                        _d1, _d2 = st.columns(2)
                        with _d1:
                            st.markdown("<div class='cp-input-label'>From</div>", unsafe_allow_html=True)
                            sd = st.date_input("From",
                                               value=(datetime.now() - timedelta(days=365)).date(),
                                               min_value=datetime(2002, 1, 1).date(),
                                               key=f"ma_start{suffix}",
                                               label_visibility="collapsed")
                        with _d2:
                            st.markdown("<div class='cp-input-label'>To</div>", unsafe_allow_html=True)
                            ed = st.date_input("To",
                                               value=datetime.now().date(),
                                               min_value=datetime(2002, 1, 1).date(),
                                               key=f"ma_end{suffix}",
                                               label_visibility="collapsed")
                        return sd, ed

                    # ── TAB 0: Stock Symbol ─────────────────────────────────
                    with cp_tab0:
                        st.markdown("<div class='cp-input-label'>Stock Symbol</div>", unsafe_allow_html=True)
                        user_symbol = st.text_input(
                            "Stock Symbol", value="1120", key="symbol_input",
                            label_visibility="collapsed", placeholder="e.g., 4190 or AAPL")
                        symbol_input = (user_symbol.strip() + ".SR"
                                        if user_symbol.strip().isdigit()
                                        else user_symbol.strip())

                        # ── Date range ─────────────────────────────────────
                        _dr1, _dr2 = st.columns(2)
                        with _dr1:
                            st.markdown("<div class='cp-input-label'>From</div>", unsafe_allow_html=True)
                            start_date = st.date_input("From",
                                                       value=(datetime.now() - timedelta(days=730)).date(),
                                                       min_value=datetime(2002, 1, 1).date(),
                                                       key="sa_start_date",
                                                       label_visibility="collapsed")
                        with _dr2:
                            st.markdown("<div class='cp-input-label'>To</div>", unsafe_allow_html=True)
                            end_date = st.date_input("To",
                                                     value=datetime.now().date(),
                                                     min_value=datetime(2002, 1, 1).date(),
                                                     key="sa_end_date",
                                                     label_visibility="collapsed")

                        selected_indicators = _render_indicators()
                        st.session_state.selected_indicators = selected_indicators

                        lookback_period = 30

                        def run_analysis_callback():
                            with st.spinner(f"Analyzing {symbol_input}..."):
                                try:
                                    analyzer = RegimeAnalyzer(
                                        symbol_input,
                                        start_date.strftime('%Y-%m-%d'),
                                        end_date.strftime('%Y-%m-%d'),
                                        selected_indicators)
                                    df = analyzer.download_data()
                                    if df is None:
                                        st.error(f"No data found for '{symbol_input}'")
                                    elif len(df) < 50:
                                        st.error(f"Only {len(df)} data points — try a longer period.")
                                    else:
                                        df = analyzer.classify_regimes(
                                            lookback=lookback_period, adx_threshold=25, atr_threshold=0.03)
                                        st.session_state.df = df
                                        st.session_state.analyzed_symbol = symbol_input
                                        st.session_state.additional_charts = ['ADX','RSI','MACD']

                                        # Pre-warm AI Analysis + Trade Validator caches while
                                        # the spinner is still showing — tabs load instantly on click.
                                        try:
                                            from gemini_tab import (
                                                _ml_predict, _historical_analogy,
                                                _price_predictor, _monte_carlo,
                                            )
                                            _ml_predict(df, horizon=5)
                                            _ml_predict(df, horizon=10)
                                            _ml_predict(df, horizon=20)
                                            _price_predictor(df, horizon=20)
                                            _historical_analogy(df, k=25, horizon=5)
                                            _historical_analogy(df, k=25, horizon=10)
                                            _historical_analogy(df, k=25, horizon=20)
                                            _monte_carlo(df, days=20)
                                        except Exception:
                                            pass
                                        try:
                                            from decision_tab import _score_engine
                                            _cp = float(df["Close"].iloc[-1])
                                            _score_engine(df, _cp)
                                        except Exception:
                                            pass

                                        st.session_state.show_results = True
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")

                        # ── Auto-analyze when navigated from screener ─────
                        if st.session_state.pop("screener_auto_analyze", False):
                            run_analysis_callback()

                        st.markdown("<div class='cp-run-wrap'>", unsafe_allow_html=True)
                        st.button("Analyze Stock", type="secondary", width="stretch",
                                  on_click=run_analysis_callback)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # ── TAB 1: Scan Market (full market OR custom symbols) ──
                    with cp_tab1:
                        _scan_mode = st.radio(
                            "Scan mode",
                            ["Full Market", "Enter Symbols"],
                            horizontal=True,
                            key="scan_mode",
                            label_visibility="collapsed",
                        )

                        # ── Shared filter renderer ──────────────────────────
                        def _render_scan_filters(suffix=""):
                            """Render filter controls and return current values."""
                            _SECTORS = ["All Sectors", "Banks", "Petrochemicals", "Cement",
                                        "Utilities", "Telecom & Tech", "Insurance", "Food & Agri",
                                        "REITs", "Retail", "Healthcare", "Transport", "Real Estate", "Other"]

                            st.markdown("<div class='cp-input-label' style='margin-top:0.7rem;'>Filters</div>", unsafe_allow_html=True)

                            # Signal type
                            st.markdown("<div style='font-size:0.65rem;color:#666;margin-bottom:0.25rem;'>Signal Type</div>", unsafe_allow_html=True)
                            _sig_type = st.radio(
                                "Signal Type", ["All", "Buy Only", "Sell Only"],
                                horizontal=True, key=f"flt_sig_{suffix}",
                                label_visibility="collapsed")

                            # Sector
                            st.markdown("<div style='font-size:0.65rem;color:#666;margin-bottom:0.25rem;margin-top:0.5rem;'>Sector</div>", unsafe_allow_html=True)
                            _sector = st.selectbox(
                                "Sector", _SECTORS, index=0,
                                key=f"flt_sector_{suffix}", label_visibility="collapsed")

                            # Min Score
                            st.markdown("<div style='font-size:0.65rem;color:#666;margin-bottom:0.1rem;margin-top:0.5rem;'>Min Score</div>", unsafe_allow_html=True)
                            _min_score = st.slider(
                                "Min Score", min_value=1, max_value=8, value=1,
                                key=f"flt_score_{suffix}", label_visibility="collapsed")

                            # Min R:R
                            st.markdown("<div style='font-size:0.65rem;color:#666;margin-bottom:0.1rem;margin-top:0.5rem;'>Min R:R Ratio</div>", unsafe_allow_html=True)
                            _min_rr = st.slider(
                                "Min R:R", min_value=0.0, max_value=5.0, value=0.0, step=0.5,
                                key=f"flt_rr_{suffix}", label_visibility="collapsed",
                                format="%.1f×")

                            # Min Conviction
                            st.markdown("<div style='font-size:0.65rem;color:#666;margin-bottom:0.1rem;margin-top:0.5rem;'>Min Conviction %</div>", unsafe_allow_html=True)
                            _min_conv = st.slider(
                                "Min Conviction", min_value=0, max_value=90, value=0, step=5,
                                key=f"flt_conv_{suffix}", label_visibility="collapsed",
                                format="%d%%")

                            return _sig_type, _sector, _min_score, _min_rr, _min_conv

                        if _scan_mode == "Enter Symbols":
                            st.markdown("<div class='cp-input-label'>Stock Symbols (comma separated)</div>", unsafe_allow_html=True)
                            ma_symbols_input = st.text_input(
                                "Symbols",
                                value="1120, 2222, 4190, 2010, 1180, 7010, 2380, 4081",
                                key="ma_symbols_input",
                                label_visibility="collapsed",
                                placeholder="e.g., 1120, 2222, 4190")
                            ma_tickers = [s.strip() + ".SR" if s.strip().isdigit() else s.strip()
                                          for s in ma_symbols_input.split(",") if s.strip()]
                            st.markdown(
                                f"<div style='color:#3a4550;font-size:0.68rem;margin:0.3rem 0 0.8rem;'>"
                                f"{len(ma_tickers)} symbols selected</div>",
                                unsafe_allow_html=True)

                            ma_start_es, ma_end_es = _render_scan_params("_es")
                            _es_sig, _es_sec, _es_sc, _es_rr, _es_cv = _render_scan_filters("es")

                            if 'ma_results' not in st.session_state:
                                st.session_state.ma_results = None

                            def run_market_analysis_callback_es():
                                if not ma_tickers:
                                    st.error("No stocks selected.")
                                    return
                                _sd = st.session_state.get('ma_start_es', (datetime.now() - timedelta(days=365)).date())
                                _ed = st.session_state.get('ma_end_es',   datetime.now().date())
                                with st.spinner(f"Scanning {len(ma_tickers)} stocks…"):
                                    res = run_market_analysis(
                                        tuple(ma_tickers), min_score=1, start=_sd, end=_ed)
                                    st.session_state.ma_results       = res
                                    st.session_state.ma_scanned_count = len(ma_tickers)
                                    st.session_state.ma_scan_params   = {'start': str(_sd), 'end': str(_ed)}
                                    st.session_state.ma_filter_sig    = st.session_state.get('flt_sig_es', 'All')
                                    st.session_state.ma_filter_sector = st.session_state.get('flt_sector_es', 'All Sectors')
                                    st.session_state.ma_filter_score  = st.session_state.get('flt_score_es', 1)
                                    st.session_state.ma_filter_rr     = st.session_state.get('flt_rr_es', 0.0)
                                    st.session_state.ma_filter_conv   = st.session_state.get('flt_conv_es', 0)
                                    st.session_state.show_market_results = True

                            st.markdown("<div class='cp-run-wrap'>", unsafe_allow_html=True)
                            st.button("Run Scan", type="secondary", width="stretch",
                                      on_click=run_market_analysis_callback_es, key="ma_run_btn_es")
                            st.markdown("</div>", unsafe_allow_html=True)

                        else:  # Full Market
                            all_tadawul    = get_all_tadawul_tickers()
                            ma_tickers_all = list(all_tadawul.keys())
                            st.markdown(
                                f"<div style='color:#26A69A;font-size:0.78rem;font-weight:600;"
                                f"margin-bottom:0.8rem;'>"
                                f"{len(ma_tickers_all)} Tadawul stocks ready to scan</div>",
                                unsafe_allow_html=True)

                            st.markdown("<div class='cp-input-label'>Period</div>", unsafe_allow_html=True)
                            _scr_period_lbl = st.selectbox(
                                "Period", ["3 Months", "6 Months", "1 Year", "2 Years"], index=1,
                                key="scr_period_sel", label_visibility="collapsed")
                            st.markdown(
                                "<div style='color:#3a4550;font-size:0.68rem;margin:0.3rem 0 0.8rem;'>"
                                "Full market scan — takes 1-2 minutes.</div>",
                                unsafe_allow_html=True)

                            _all_sig, _all_sec, _all_sc, _all_rr, _all_cv = _render_scan_filters("all")

                            def run_market_analysis_callback_all():
                                _pv = {
                                    "3 Months": "3mo",
                                    "6 Months": "6mo",
                                    "1 Year":   "1y",
                                    "2 Years":  "2y",
                                }.get(st.session_state.get("scr_period_sel", "6 Months"), "6mo")
                                with st.spinner(f"Scanning {len(ma_tickers_all)} stocks…"):
                                    res = run_market_analysis(
                                        tuple(ma_tickers_all), period=_pv, min_score=1)
                                    st.session_state.ma_results          = res
                                    st.session_state.ma_scanned_count    = len(ma_tickers_all)
                                    st.session_state.ma_scan_params      = {
                                        "period": st.session_state.get("scr_period_sel", "6 Months")}
                                    st.session_state.ma_filter_sig    = st.session_state.get('flt_sig_all', 'All')
                                    st.session_state.ma_filter_sector = st.session_state.get('flt_sector_all', 'All Sectors')
                                    st.session_state.ma_filter_score  = st.session_state.get('flt_score_all', 1)
                                    st.session_state.ma_filter_rr     = st.session_state.get('flt_rr_all', 0.0)
                                    st.session_state.ma_filter_conv   = st.session_state.get('flt_conv_all', 0)
                                    st.session_state.show_market_results = True

                            st.markdown("<div class='cp-run-wrap'>", unsafe_allow_html=True)
                            st.button("Run Full Market Scan", type="secondary", width="stretch",
                                      on_click=run_market_analysis_callback_all, key="ma_run_btn_all")
                            st.markdown("</div>", unsafe_allow_html=True)



        # ═══════════════════════════════════════════════════════════════════════
        # Favorites panel (renders when ★ button is toggled)
        # ═══════════════════════════════════════════════════════════════════════

        if st.session_state.get('show_favorites_panel', False):

            favs = st.session_state.get('favorites', [])

            with st.container(key="fav_panel_wrap"):

                hc1, hc2 = st.columns([9, 1])

                with hc1:

                    count_badge = f"<span class='fav-hdr-count'>{len(favs)}</span>" if favs else ""

                    st.markdown(

                        f"<div class='fav-hdr'><span class='fav-hdr-icon'>?</span>"

                        f"<span class='fav-hdr-title'>Saved Strategies</span>{count_badge}</div>",


                        unsafe_allow_html=True)

                with hc2:

                    with st.container(key="fav_close_panel"):

                        if st.button("?  Close", key="fav_close_btn", width="stretch"):

                            st.session_state.show_favorites_panel = False

                            st.rerun()



                if not favs:

                    st.markdown(

                        "<div class='fav-empty'><div class='fav-empty-icon'>&#9825;</div>"

                        "<div class='fav-empty-txt'>No saved strategies yet.<br>"

                        "Run an analysis, open <b>Signal Analysis ? Indicator Combinations</b>, "

                        "and tap <b>? Save Strategy</b> on any combination you like.</div></div>",

                        unsafe_allow_html=True)

                else:

                    _r_colors = {'TREND': '#4A9EFF', 'RANGE': '#FFC107', 'VOLATILE': '#FF6B6B'}

                    for _fi, _fav in enumerate(favs):

                        _parts   = _fav.get('pair', '').split(' + ')

                        _pill_a  = _parts[0] if _parts else ''

                        _pill_b  = _parts[1] if len(_parts) > 1 else ''

                        _regime  = _fav.get('best_regime') or ''

                        _bc      = _r_colors.get(_regime, '#9e9e9e')

                        _wr      = _fav.get('win_rate', 0)

                        _wr_c    = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')

                        _ag      = _fav.get('avg_gain', 0)

                        _al      = _fav.get('avg_loss', 0)

                        _ag_c    = '#26A69A' if _ag >= 1 else ('#FFC107' if _ag > 0 else '#ef5350')

                        _al_c    = '#ef5350' if _al < 0 else '#FFC107'

                        _sym     = _fav.get('symbol', '').replace('.SR', '')

                        _card    = (

                            "<div class='fav-card'>"

                            # ?? top row: symbol · pills · regime · date

                            "<div class='fav-card-top'>"

                            f"<span class='fav-sym'>{_sym}</span>"

                            "<span class='fav-sep'>|</span>"

                            f"<span class='fav-pill'>{_pill_a}</span>"

                            "<span class='fav-plus'>+</span>"

                            f"<span class='fav-pill'>{_pill_b}</span>"

                            + (f"<span class='fav-regime' style='color:{_bc};border-color:{_bc};'>{_regime}</span>" if _regime else '')

                            + f"<span class='fav-date'>{_fav.get('saved_at','')}</span>"

                            "</div>"

                            # ?? bottom row: 4 stats

                            "<div class='fav-card-bot'>"

                            f"<div class='fav-si'><span class='fsl'>Win Rate</span><span class='fsv' style='color:{_wr_c}'>{_wr:.1f}%</span></div>"

                            f"<div class='fav-si'><span class='fsl'>Avg Gain</span><span class='fsv' style='color:{_ag_c}'>+{_ag:.2f}%</span></div>"

                            f"<div class='fav-si'><span class='fsl'>Avg Loss</span><span class='fsv' style='color:{_al_c}'>{_al:.2f}%</span></div>"

                            f"<div class='fav-si'><span class='fsl'>Signals</span><span class='fsv'>{_fav.get('signals',0)}</span></div>"

                            "</div>"

                            "</div>"

                        )

                        _ec1, _ec2 = st.columns([12, 1])

                        with _ec1:

                            st.markdown(_card, unsafe_allow_html=True)

                        with _ec2:

                            if st.button("?", key=f"fav_del_{_fi}", width="stretch"):

                                _user = st.session_state.get('auth_username', '')

                                delete_favorite(_user, _fav.get('id', ''))

                                st.session_state.favorites = [f for f in favs if f.get('id') != _fav.get('id')]

                                st.rerun()



    elif st.session_state.show_market_results:

        apply_ui_theme()

        results     = st.session_state.get('ma_results', {}) or {}
        buy_stocks  = results.get('buy',  [])
        sell_stocks = results.get('sell', [])
        hold_stocks = results.get('hold', [])
        scanned     = st.session_state.get('ma_scanned_count', 0)
        params      = st.session_state.get('ma_scan_params', {})
        all_stocks  = buy_stocks + sell_stocks + hold_stocks

        # ── CSS ────────────────────────────────────────────────────────────────
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        section[data-testid="stMainBlockContainer"] { padding-top:1rem !important; }

        /* KPI bar */
        .msr-kpis { display:grid; grid-template-columns:repeat(6,1fr); gap:0.45rem; margin-bottom:1.1rem; }
        .msr-kpi  { border-radius:10px; padding:0.65rem 0.8rem;
                    background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07);
                    display:flex; flex-direction:column; gap:0.22rem; }
        .msr-kpi-val { font-size:1.35rem; font-weight:800; letter-spacing:-1px; line-height:1; }
        .msr-kpi-lbl { font-size:0.56rem; font-weight:600; color:#505050; text-transform:uppercase; letter-spacing:0.6px; }

        /* Top picks */
        .msr-hline { height:1px; background:rgba(255,255,255,0.07); margin:0.9rem 0 0.8rem; }
        .msr-pick  { border-radius:14px; overflow:hidden; font-family:'Inter',system-ui,sans-serif; }
        .msr-pick.gold   { background:rgba(255,215,0,0.03);  border:1px solid rgba(255,215,0,0.2); }
        .msr-pick.silver { background:rgba(192,192,192,0.025); border:1px solid rgba(192,192,192,0.15); }
        .msr-pick.bronze { background:rgba(205,127,50,0.03);  border:1px solid rgba(205,127,50,0.18); }
        .msr-pick-hd { display:flex; justify-content:space-between; align-items:flex-start; padding:0.75rem 0.9rem 0.35rem; }
        .msr-pick-sym  { font-size:1rem; font-weight:800; }
        .msr-pick-sym.gold   { color:#FFD700; }
        .msr-pick-sym.silver { color:#C0C0C0; }
        .msr-pick-sym.bronze { color:#CD7F32; }
        .msr-pick-name { font-size:0.65rem; color:#565656; margin-top:0.14rem; }
        .msr-pick-badge { font-size:0.58rem; font-weight:700; padding:0.15rem 0.5rem;
                          border-radius:999px; letter-spacing:0.2px; }
        .msr-pick-badge.gold   { color:#FFD700; background:rgba(255,215,0,0.1);  border:1px solid rgba(255,215,0,0.28); }
        .msr-pick-badge.silver { color:#C0C0C0; background:rgba(192,192,192,0.09); border:1px solid rgba(192,192,192,0.22); }
        .msr-pick-badge.bronze { color:#CD7F32; background:rgba(205,127,50,0.09);  border:1px solid rgba(205,127,50,0.22); }
        .msr-pick-conv { padding:0.2rem 0.9rem 0.45rem; }
        .msr-pick-track { height:4px; background:rgba(255,255,255,0.07); border-radius:2px; overflow:hidden; }
        .msr-pick-fill  { height:100%; border-radius:2px; }
        .msr-pick-reason { font-size:0.67rem; color:#787878; padding:0 0.9rem 0.45rem; line-height:1.35; }
        .msr-pick-lvls { display:grid; grid-template-columns:repeat(4,1fr);
                         border-top:1px solid rgba(255,255,255,0.05); }
        .msr-pl { text-align:center; padding:0.5rem 0.2rem;
                  border-right:1px solid rgba(255,255,255,0.045); }
        .msr-pl:last-child { border-right:none; }
        .msr-plv { font-size:0.8rem; font-weight:700; line-height:1; }
        .msr-plv.en { color:#4A9EFF; } .msr-plv.st { color:#ef4444; }
        .msr-plv.t1 { color:#10a37f; } .msr-plv.rr { color:#fbbf24; }
        .msr-pll { font-size:0.48rem; font-weight:600; color:#424242;
                   text-transform:uppercase; letter-spacing:0.5px; margin-top:3px; }

        /* ── Stock cards ─────────────────────────────────────────── */
        .sc { border-radius:14px; overflow:hidden; margin-bottom:0.5rem;
              background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.07);
              font-family:'Inter',system-ui,sans-serif; transition:background 0.15s; }
        .sc:hover { background:rgba(255,255,255,0.038); }

        /* Header */
        .sc-hd { display:flex; align-items:flex-start; justify-content:space-between;
                 padding:0.75rem 1rem 0.45rem 1rem; gap:0.75rem; }
        .sc-left { flex:1; min-width:0; }
        .sc-sym  { font-size:1.05rem; font-weight:800; letter-spacing:-0.2px; line-height:1; }
        .sc-sym.buy  { color:#10a37f; }
        .sc-sym.sell { color:#ef4444; }
        .sc-sym.hold { color:#fbbf24; }
        .sc-nameline { display:flex; align-items:center; gap:0.4rem; flex-wrap:wrap; margin-top:0.3rem; }
        .sc-name { font-size:0.72rem; color:#666; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:200px; }
        .sc-setup-tag { font-size:0.58rem; font-weight:600; padding:0.12rem 0.42rem;
                        border-radius:4px; background:rgba(155,135,194,0.1);
                        color:#9b87c2; border:1px solid rgba(155,135,194,0.2); white-space:nowrap; }
        .sc-right { text-align:right; flex-shrink:0; }
        .sc-price { font-size:0.95rem; font-weight:700; color:#e8e8e8; letter-spacing:-0.2px; }
        .sc-meta  { display:flex; align-items:center; gap:0.38rem; margin-top:0.3rem; justify-content:flex-end; }
        .sc-score { font-size:0.68rem; font-weight:800; padding:0.14rem 0.52rem; border-radius:999px; }
        .sc-score.buy  { color:#10a37f; background:rgba(16,163,127,0.12); border:1px solid rgba(16,163,127,0.25); }
        .sc-score.sell { color:#ef4444; background:rgba(239,68,68,0.12);   border:1px solid rgba(239,68,68,0.25); }
        .sc-score.hold { color:#fbbf24; background:rgba(251,191,36,0.09);  border:1px solid rgba(251,191,36,0.22); }

        /* Thin divider */
        .sc-hr { height:1px; background:rgba(255,255,255,0.055); margin:0 1rem; }

        /* Data row: levels + indicators side by side */
        .sc-data { display:flex; align-items:stretch; }
        .sc-levels { display:flex; flex:1; }
        .sc-lv { flex:1; text-align:center; padding:0.6rem 0.15rem;
                 border-right:1px solid rgba(255,255,255,0.045); }
        .sc-lv-v { font-size:0.9rem; font-weight:800; line-height:1; }
        .sc-lv-l { font-size:0.5rem; font-weight:600; color:#3e3e3e;
                   text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; }
        .sc-div-vert { width:1px; background:rgba(255,255,255,0.07); flex-shrink:0; }
        .sc-inds { display:flex; }
        .sc-ind  { text-align:center; padding:0.6rem 0.6rem;
                   border-right:1px solid rgba(255,255,255,0.04); }
        .sc-ind:last-child { border-right:none; }
        .sc-iv   { font-size:0.82rem; font-weight:700; line-height:1; }
        .sc-il   { font-size:0.47rem; font-weight:600; color:#404040;
                   text-transform:uppercase; letter-spacing:0.4px; margin-top:4px; }

        /* Conviction bar */
        .sc-conv { display:flex; align-items:center; gap:0.55rem;
                   padding:0.38rem 1rem; background:rgba(0,0,0,0.08); }
        .sc-conv-lbl { font-size:0.48rem; font-weight:700; text-transform:uppercase;
                       letter-spacing:0.5px; color:#3a3a3a; flex-shrink:0; }
        .sc-conv-track { flex:1; height:3px; background:rgba(255,255,255,0.07);
                         border-radius:2px; overflow:hidden; }
        .sc-conv-fill  { height:100%; border-radius:2px; }
        .sc-conv-val   { font-size:0.68rem; font-weight:700; flex-shrink:0; width:34px; text-align:right; }

        /* Footer: perf chips + signal tags */
        .sc-foot { display:flex; flex-wrap:wrap; gap:0.26rem;
                   padding:0.45rem 1rem 0.65rem; }
        .sc-chip { font-size:0.62rem; font-weight:600; padding:0.15rem 0.48rem; border-radius:6px; }
        .sc-chip.up   { background:rgba(16,163,127,0.1);  color:#10a37f; border:1px solid rgba(16,163,127,0.18); }
        .sc-chip.dn   { background:rgba(239,68,68,0.1);   color:#ef4444; border:1px solid rgba(239,68,68,0.18); }
        .sc-chip.neut { background:rgba(255,255,255,0.04);color:#666;    border:1px solid rgba(255,255,255,0.07); }
        .sc-dot-sep   { color:#2e2e2e; font-size:0.75rem; display:flex; align-items:center; }
        .sc-tag { font-size:0.6rem; font-weight:400; padding:0.15rem 0.44rem; border-radius:5px;
                  background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); color:#626262; }

        /* Section header */
        .msr-sec-row  { display:flex; align-items:center; gap:0.5rem; margin:0.5rem 0 0.55rem; }
        .msr-sec-dot  { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
        .msr-sec-dot.buy  { background:#10a37f; } .msr-sec-dot.sell { background:#ef4444; }
        .msr-sec-dot.hold { background:#fbbf24; }
        .msr-sec-title { font-size:0.62rem; font-weight:700; letter-spacing:1px; text-transform:uppercase; }
        .msr-sec-title.buy  { color:#10a37f; } .msr-sec-title.sell { color:#ef4444; }
        .msr-sec-title.hold { color:#fbbf24; }
        .msr-sec-count { font-size:0.58rem; padding:0.12rem 0.5rem; border-radius:16px;
                         background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.07); color:#606060; }
        .msr-empty { text-align:center; padding:2.5rem 1rem; color:#444; font-size:0.82rem; }
        </style>""", unsafe_allow_html=True)

        # ── Back button ──────────────────────────────────────────────────────
        _bc, _ = st.columns([1, 6])
        with _bc:
            if st.button("← New Scan", type="secondary", width="stretch", key="ma_back_btn"):
                st.session_state.show_market_results = False
                st.rerun()

        # ── Stats ────────────────────────────────────────────────────────────
        tf_lbl        = params.get('timeframe', '6mo')
        sec_lbl       = params.get('sector', 'All Sectors')
        ms_lbl        = params.get('min_score', 2)
        avg_rr        = (sum(s.get('rr_ratio', 0) for s in buy_stocks) / len(buy_stocks)) if buy_stocks else 0
        best_conv     = max((s.get('conviction', 0) for s in buy_stocks), default=0)

        # ── Hero card matching single-stock analysis style ───────────────────
        _period_info = params.get('period', params.get('start', ''))
        _period_disp = f"Period: {_period_info}" if _period_info else ""

        def _msr_tile(label, value, accent, sub="", val_color=None):
            vc = val_color or "#ffffff"
            return (
                f"<div style='background:#181818;border:1px solid #303030;border-top:2px solid {accent};"
                f"border-radius:8px;padding:1rem 1.1rem;'>"
                f"<div style='font-size:0.68rem;color:#9e9e9e;text-transform:uppercase;"
                f"letter-spacing:0.8px;font-weight:600;margin-bottom:0.4rem;'>{label}</div>"
                f"<div style='font-size:1.15rem;font-weight:700;color:{vc};line-height:1.1;'>{value}</div>"
                f"<div style='font-size:0.72rem;color:#9e9e9e;margin-top:0.35rem;font-weight:600;'>{sub}</div>"
                f"</div>"
            )

        _perfect_list = sorted(
            [s for s in buy_stocks
             if s.get('ind_score', 0) >= 2 and s.get('pa_score', 0) >= 2
             and s.get('score', 0) >= 4 and s.get('rr_ratio', 0) >= 2.0],
            key=lambda x: x.get('priority_score', 0), reverse=True)

        _hit_rate = round(len(buy_stocks) / scanned * 100) if scanned > 0 else 0

        st.markdown(
            f"<div style='background:#212121;border:1px solid #303030;border-radius:12px;"
            f"padding:1.6rem 1.8rem;margin-bottom:1.4rem;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;'>"
            f"<div>"
            f"<div style='font-size:1.3rem;font-weight:700;color:#fff;line-height:1.2;'>Market Scan Results</div>"
            f"<div style='font-size:0.78rem;color:#9e9e9e;margin-top:0.2rem;font-weight:500;'>"
            f"{scanned} stocks scanned &nbsp;·&nbsp; {_period_disp}</div>"
            f"</div>"
            f"<span style='font-size:0.7rem;font-weight:700;padding:0.28rem 0.9rem;"
            f"border-radius:20px;background:rgba(16,163,127,0.12);color:#10a37f;"
            f"border:1px solid rgba(16,163,127,0.3);'>{len(_perfect_list)} Perfect Setups</span>"
            f"</div>"
            f"<div style='border-top:1px solid #303030;margin-bottom:0.9rem;'></div>"
            f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.7rem;'>"
            + _msr_tile("Buy Signals",    str(len(buy_stocks)),     "#10a37f", f"{_hit_rate}% hit rate",             "#10a37f")
            + _msr_tile("Perfect Setups", str(len(_perfect_list)),  "#FFD700", "Ind≥2 · PA≥2 · R:R≥2×",             "#FFD700")
            + _msr_tile("Avoid",          str(len(sell_stocks)),    "#ef4444", "bearish signals",                    "#ef4444")
            + _msr_tile("Avg R:R",        f"{avg_rr:.1f}×",         "#4A9EFF", "on buy signals",                    "#4A9EFF")
            + _msr_tile("Best Conviction",f"{best_conv}%",           "#a78bfa", "highest conviction",                "#a78bfa")
            + "</div></div>",
            unsafe_allow_html=True,
        )

        # ── Sort (always by priority score, no user control needed) ─────────
        def _sorted(lst):
            return sorted(lst, key=lambda x: x.get('priority_score', 0), reverse=True)

        # ── Card renderer ─────────────────────────────────────────────────────
        def _render_card(stock, side):
            sym      = stock['ticker'].replace('.SR', '')
            name     = stock.get('name', sym)
            price    = stock['price']
            score    = stock['score']
            entry    = stock.get('entry', price)
            stop     = stock.get('stop_loss', price)
            t1       = stock.get('target1', price)
            rr       = stock.get('rr_ratio', 0)
            conv     = stock.get('conviction', 50)
            setup    = stock.get('setup_type', '')
            signals  = stock.get('why_reasons') or stock.get('signals', [])
            mtf      = stock.get('mtf_score', 0)
            is_perf  = (stock.get('ind_score', 0) >= 2 and stock.get('pa_score', 0) >= 2
                        and score >= 4 and rr >= 2.0)

            stop_pct = abs(entry - stop) / entry * 100 if entry > 0 else 0
            t1_pct   = abs(t1   - entry) / entry * 100 if entry > 0 else 0
            sdsp     = f"+{score}" if score > 0 else str(score)

            ac = {"buy": "#10a37f", "sell": "#ef4444", "hold": "#fbbf24"}.get(side, "#666")
            cc = "#10a37f" if conv >= 70 else ("#4A9EFF" if conv >= 45 else "#fbbf24")

            star = '<span style="font-size:0.62rem;color:#FFD700;font-weight:700;margin-left:0.3rem;" title="Perfect Setup">⭐</span>' if is_perf else ''

            # MTF badge: 3/3 = all green, 2/3 = amber, 1/3 = red
            if mtf == 3:
                mtf_html = ('<span style="font-size:0.57rem;font-weight:800;background:#4caf5022;'
                            'color:#4caf50;border-radius:4px;padding:1px 6px;margin-left:4px;'
                            'border:1px solid #4caf5044;" title="Daily+Weekly+Monthly aligned">MTF 3/3</span>')
            elif mtf == 2:
                mtf_html = ('<span style="font-size:0.57rem;font-weight:800;background:#ff980022;'
                            'color:#ff9800;border-radius:4px;padding:1px 6px;margin-left:4px;'
                            'border:1px solid #ff980044;" title="2 of 3 timeframes aligned">MTF 2/3</span>')
            elif mtf == 1:
                mtf_html = ('<span style="font-size:0.57rem;font-weight:800;background:#ef444422;'
                            'color:#ef4444;border-radius:4px;padding:1px 6px;margin-left:4px;'
                            'border:1px solid #ef444444;" title="Only daily aligned">MTF 1/3</span>')
            else:
                mtf_html = ''

            why_text = " · ".join(signals[:4]) if signals else (setup if setup else "—")

            st.markdown(
                f'<div class="sc" style="border-left:3px solid {ac};">'
                f'<div class="sc-hd">'
                f'<div class="sc-left">'
                f'<div class="sc-sym {side}">{sym}{star}{mtf_html}</div>'
                f'<div class="sc-nameline">'
                f'<span class="sc-name">{name}</span>'
                f'<span class="sc-setup-tag">{setup}</span>'
                f'</div>'
                f'</div>'
                f'<div class="sc-right">'
                f'<div class="sc-price">SAR {price:.2f}</div>'
                f'<div class="sc-meta">'
                f'<span class="sc-score {side}">{sdsp}</span>'
                f'<span style="font-size:0.7rem;font-weight:700;color:{cc}">{conv}%</span>'
                f'</div>'
                f'</div>'
                f'</div>'
                f'<div class="sc-hr"></div>'
                f'<div class="sc-data">'
                f'<div class="sc-levels">'
                f'<div class="sc-lv"><div class="sc-lv-v" style="color:#4A9EFF">{entry:.2f}</div><div class="sc-lv-l">Entry</div></div>'
                f'<div class="sc-lv"><div class="sc-lv-v" style="color:#ef4444">-{stop_pct:.1f}%</div><div class="sc-lv-l">Stop</div></div>'
                f'<div class="sc-lv"><div class="sc-lv-v" style="color:#10a37f">+{t1_pct:.1f}%</div><div class="sc-lv-l">Target</div></div>'
                f'<div class="sc-lv" style="border-right:1px solid rgba(255,255,255,0.07)"><div class="sc-lv-v" style="color:#fbbf24">{rr:.1f}×</div><div class="sc-lv-l">R:R</div></div>'
                f'</div>'
                f'</div>'
                f'<div style="padding:0.55rem 0.9rem 0.7rem;border-top:1px solid rgba(255,255,255,0.05);'
                f'font-size:0.71rem;color:#9e9e9e;line-height:1.5;">'
                f'<span style="color:#fbbf24;font-weight:700;font-size:0.65rem;text-transform:uppercase;'
                f'letter-spacing:0.7px;margin-right:0.4rem;">Why:</span>{why_text}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Classify stocks ───────────────────────────────────────────────────
        # All bullish stocks (indicators OR price action agree) — sorted by priority
        all_buy = sorted(
            [s for s in all_stocks if s.get('score', 0) > 0
             or s.get('ind_score', 0) > 0 or s.get('pa_score', 0) > 0],
            key=lambda x: x.get('priority_score', 0), reverse=True)

        # Best Picks: strict multi-gate composite score, capped at 10
        def _best_picks_score(s):
            rr   = s.get('rr_ratio', 0)
            conv = s.get('conviction', 0)
            ind  = s.get('ind_score', 0)
            pa   = s.get('pa_score', 0)
            sc   = s.get('score', 0)
            vr   = s.get('vol_ratio', 1)
            rsi  = s.get('rsi', 50)
            rsi_bonus = 0.5 if rsi < 45 else (-0.5 if rsi > 72 else 0)
            return (rr * 2) + (conv / 20) + ind + pa + sc + min(vr, 3) + rsi_bonus

        best_picks = sorted(
            [s for s in all_stocks
             if s.get('ind_score', 0) >= 2
             and s.get('pa_score', 0) >= 2
             and s.get('score', 0) >= 4
             and s.get('rr_ratio', 0) >= 1.8
             and s.get('conviction', 0) >= 45],
            key=_best_picks_score, reverse=True)[:10]

        # ── Search box ───────────────────────────────────────────────────────
        _srch = st.text_input(
            "Search stocks",
            placeholder="Filter by ticker or name…",
            key="ma_search",
            label_visibility="collapsed",
        )

        # Pull active filter settings saved at scan time
        _f_sig    = st.session_state.get('ma_filter_sig',    'All')
        _f_sector = st.session_state.get('ma_filter_sector', 'All Sectors')
        _f_score  = st.session_state.get('ma_filter_score',  1)
        _f_rr     = st.session_state.get('ma_filter_rr',     0.0)
        _f_conv   = st.session_state.get('ma_filter_conv',   0)

        def _filter(lst):
            out = _sorted(lst)
            # Text search
            if _srch:
                q = _srch.strip().lower()
                out = [s for s in out if q in s['ticker'].lower() or q in s.get('name', '').lower()]
            # Sector
            if _f_sector and _f_sector != 'All Sectors':
                out = [s for s in out if s.get('sector', 'Other') == _f_sector]
            # Min score
            if _f_score > 1:
                out = [s for s in out if s.get('score', 0) >= _f_score]
            # Min R:R
            if _f_rr > 0:
                out = [s for s in out if s.get('rr_ratio', 0) >= _f_rr]
            # Min conviction
            if _f_conv > 0:
                out = [s for s in out if s.get('conviction', 0) >= _f_conv]
            return out

        # Signal-type filter splits the raw lists before tab counts
        def _sig_filter(lst, side):
            if _f_sig == 'Buy Only' and side != 'buy':
                return []
            if _f_sig == 'Sell Only' and side != 'sell':
                return []
            return _filter(lst)

        _f_buy_stocks  = _sig_filter(buy_stocks,  'buy')
        _f_sell_stocks = _sig_filter(sell_stocks, 'sell')
        _f_best_picks  = _filter(best_picks) if _f_sig != 'Sell Only' else []
        _f_all_buy     = _sig_filter(all_buy, 'buy')

        # Active filter badge
        _active_filters = []
        if _f_sig    != 'All':          _active_filters.append(_f_sig)
        if _f_sector != 'All Sectors':  _active_filters.append(_f_sector)
        if _f_score  > 1:               _active_filters.append(f"Score≥{_f_score}")
        if _f_rr     > 0:               _active_filters.append(f"R:R≥{_f_rr:.1f}×")
        if _f_conv   > 0:               _active_filters.append(f"Conv≥{_f_conv}%")
        if _active_filters:
            st.markdown(
                "<div style='display:flex;flex-wrap:wrap;gap:0.35rem;margin-bottom:0.6rem;'>"
                + "".join(
                    f"<span style='font-size:0.62rem;font-weight:700;padding:0.18rem 0.55rem;"
                    f"border-radius:999px;background:rgba(251,191,36,0.1);color:#fbbf24;"
                    f"border:1px solid rgba(251,191,36,0.3);'>{f}</span>"
                    for f in _active_filters)
                + "</div>",
                unsafe_allow_html=True,
            )

        # ── 3-tab results layout ──────────────────────────────────────────────
        tab_best, tab_buy, tab_sell = st.tabs([
            f"Best Picks  {len(best_picks)}",
            f"Buy Signals  {len(all_buy)}",
            f"Avoid  {len(sell_stocks)}",
        ])

        with tab_best:
            if not best_picks:
                st.markdown(
                    "<div class='msr-empty'>"
                    "No stocks pass all quality gates right now — check Buy Signals for broader candidates."
                    "</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="background:rgba(255,215,0,0.04);border:1px solid rgba(255,215,0,0.15);'
                    f'border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.9rem;font-size:0.72rem;color:#9e9e9e;line-height:1.5;">'
                    f'<span style="color:#FFD700;font-weight:700;">Best Picks</span> — '
                    f'ranked by a composite of R:R, conviction, indicator strength, price action, and volume. '
                    f'All {len(best_picks)} stocks pass: Indicators ≥2 · Price Action ≥2 · Score ≥4 · R:R ≥1.8× · Conviction ≥45%.'
                    f'</div>',
                    unsafe_allow_html=True)
                for _i, s in enumerate(best_picks):
                    _rank_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                    _rc = _rank_colors[_i] if _i < 3 else "#10a37f"
                    _sym_bp  = s['ticker'].replace('.SR', '')
                    _name_bp = s.get('name', _sym_bp)
                    _p_bp    = s['price']
                    _e_bp    = s.get('entry', _p_bp)
                    _sl_bp   = s.get('stop_loss', _p_bp)
                    _t1_bp   = s.get('target1', _p_bp)
                    _t2_bp   = s.get('target2', _t1_bp)
                    _rr_bp   = s.get('rr_ratio', 0)
                    _conv_bp = s.get('conviction', 0)
                    _up_bp   = abs(_t1_bp - _e_bp) / _e_bp * 100 if _e_bp > 0 else 0
                    _dn_bp   = abs(_e_bp  - _sl_bp) / _e_bp * 100 if _e_bp > 0 else 0
                    _sc_bp   = s.get('score', 0)
                    _setup   = s.get('setup_type', '')
                    _sigs    = s.get('signals', [])
                    _t2_pct  = abs(_t2_bp - _e_bp) / _e_bp * 100 if _e_bp > 0 else 0
                    _cc_bp   = "#10a37f" if _conv_bp >= 70 else ("#4A9EFF" if _conv_bp >= 45 else "#fbbf24")
                    _rank_num = ["#1", "#2", "#3"][_i] if _i < 3 else f"#{_i+1}"
                    _why_bp  = " · ".join(_sigs[:4]) if _sigs else (_setup if _setup else "—")
                    st.markdown(
                        f'<div class="sc" style="border-left:4px solid {_rc};background:rgba(255,255,255,0.025);">'
                        f'<div class="sc-hd">'
                        f'<div class="sc-left">'
                        f'<div style="display:flex;align-items:center;gap:0.5rem;">'
                        f'<span style="font-size:0.62rem;font-weight:700;padding:0.12rem 0.46rem;'
                        f'border-radius:4px;background:rgba(255,215,0,0.08);color:{_rc};'
                        f'border:1px solid {_rc}44;">{_rank_num}</span>'
                        f'<span class="sc-sym buy" style="color:{_rc};">{_sym_bp}</span>'
                        f'</div>'
                        f'<div class="sc-nameline"><span class="sc-name">{_name_bp}</span>'
                        f'<span class="sc-setup-tag">{_setup}</span></div>'
                        f'</div>'
                        f'<div class="sc-right">'
                        f'<div class="sc-price">SAR {_p_bp:.2f}</div>'
                        f'<div class="sc-meta">'
                        f'<span class="sc-score buy">+{_sc_bp}</span>'
                        f'<span style="font-size:0.7rem;font-weight:700;color:{_cc_bp}">{_conv_bp}%</span>'
                        f'</div>'
                        f'</div>'
                        f'</div>'
                        f'<div class="sc-hr"></div>'
                        f'<div style="display:grid;grid-template-columns:repeat(5,1fr);border-bottom:1px solid rgba(255,255,255,0.05);">'
                        f'<div class="sc-lv"><div class="sc-lv-v" style="color:#4A9EFF">{_e_bp:.2f}</div><div class="sc-lv-l">Entry</div></div>'
                        f'<div class="sc-lv"><div class="sc-lv-v" style="color:#ef4444">-{_dn_bp:.1f}%</div><div class="sc-lv-l">Stop</div></div>'
                        f'<div class="sc-lv"><div class="sc-lv-v" style="color:#10a37f">+{_up_bp:.1f}%</div><div class="sc-lv-l">Target 1</div></div>'
                        f'<div class="sc-lv"><div class="sc-lv-v" style="color:#26A69A">+{_t2_pct:.1f}%</div><div class="sc-lv-l">Target 2</div></div>'
                        f'<div class="sc-lv" style="border-right:none"><div class="sc-lv-v" style="color:#fbbf24">{_rr_bp:.1f}×</div><div class="sc-lv-l">R:R</div></div>'
                        f'</div>'
                        f'<div style="padding:0.55rem 0.9rem 0.7rem;font-size:0.71rem;color:#9e9e9e;line-height:1.5;">'
                        f'<span style="color:#fbbf24;font-weight:700;font-size:0.65rem;text-transform:uppercase;'
                        f'letter-spacing:0.7px;margin-right:0.4rem;">Why:</span>{_why_bp}'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        with tab_buy:
            filtered_buy = _f_all_buy
            if not filtered_buy:
                st.markdown("<div class='msr-empty'>No buy signals found — try a wider period or different symbols.</div>", unsafe_allow_html=True)
            else:
                perfect = [s for s in filtered_buy
                           if s.get('ind_score', 0) >= 2 and s.get('pa_score', 0) >= 2
                           and s.get('score', 0) >= 4 and s.get('rr_ratio', 0) >= 2.0]
                regular = [s for s in filtered_buy if s not in perfect]

                if perfect:
                    st.markdown(
                        f'<div class="msr-sec-row"><div class="msr-sec-dot buy"></div>'
                        f'<span class="msr-sec-title buy">Perfect Setups</span>'
                        f'<span class="msr-sec-count">{len(perfect)} stocks</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                    for s in perfect:
                        _render_card(s, 'buy')

                if regular:
                    if perfect:
                        st.markdown('<div class="msr-hline"></div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="msr-sec-row"><div class="msr-sec-dot buy"></div>'
                        f'<span class="msr-sec-title buy">Buy Signals</span>'
                        f'<span class="msr-sec-count">{len(regular)} stocks</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                    for s in regular:
                        _render_card(s, 'buy')

        with tab_sell:
            filtered_sell = _f_sell_stocks
            if filtered_sell:
                st.markdown(
                    f'<div class="msr-sec-row"><div class="msr-sec-dot sell"></div>'
                    f'<span class="msr-sec-title sell">Avoid / Sell Signals</span>'
                    f'<span class="msr-sec-count">{len(filtered_sell)} stocks</span></div>',
                    unsafe_allow_html=True)
                for s in filtered_sell:
                    _render_card(s, 'sell')
            else:
                st.markdown("<div class='msr-empty'>No sell signals found.</div>", unsafe_allow_html=True)

    elif st.session_state.show_market_pulse:

        # ── MARKET PULSE FULL PAGE ─────────────────────────────────────────
        apply_ui_theme()
        st.markdown("""
        <style>
        header[data-testid="stHeader"] { display: none !important; }
        section[data-testid="stMainBlockContainer"] { padding-top: 1rem !important; }
        </style>""", unsafe_allow_html=True)

        # Back button row
        back_col, title_col = st.columns([1, 6], gap="small")
        with back_col:
            if st.button("← Home", key="pulse_back_btn", type="secondary", width="stretch"):
                st.session_state.show_market_pulse = False
                st.rerun()
        with title_col:
            st.markdown(
                "<div style='font-size:1.4rem;font-weight:900;color:#e8e8e8;"
                "letter-spacing:-0.5px;padding-top:0.15rem;'>"
                "📡 Market Pulse <span style='font-size:0.7rem;font-weight:600;"
                "color:#555;'>Saudi Market Command Center</span></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        from market_pulse_tab import render_market_pulse_tab
        render_market_pulse_tab()

    elif st.session_state.show_results:

        # STOCK ANALYSIS RESULTS PAGE

        df = st.session_state.df

        symbol_input = st.session_state.analyzed_symbol

        additional_charts = ['ADX', 'RSI', 'MACD']



        if st.button("? New Analysis", type="secondary", width="stretch"):

            st.session_state.show_results = False

            st.rerun()

        

        # Stock Information Section

        latest = df.iloc[-1]

        first = df.iloc[0]

        

        # Stock name — cached helper avoids slow uncached .info call
        try:
            from signal_engine import get_stock_name as _gsn
            stock_name = _gsn(symbol_input) or symbol_input
        except Exception:
            stock_name = symbol_input
        st.session_state.analyzed_stock_name = stock_name

        # Live price — use already-downloaded Close (no extra network call)
        current_price = float(latest['Close'])


        period_change = ((current_price - first['Close']) / first['Close']) * 100

        period_high = df['High'].max()

        period_low = df['Low'].min()

        avg_volume = df['Volume'].mean() if 'Volume' in df.columns else 0

        price_range = period_high - period_low

        volatility = (price_range / period_low) * 100

        returns = df['Close'].pct_change().dropna()

        annual_vol = returns.std() * np.sqrt(252) * 100 if len(returns) > 1 else 0

        latest_volume = latest.get('Volume', avg_volume)

        regime_color = '#26A69A' if latest['REGIME'] == 'TREND' else '#4A9EFF' if latest['REGIME'] == 'RANGE' else '#FF6B6B'

        if period_change > 0.2:

            delta_color = '#26A69A'

            delta_bg = 'rgba(38,166,154,0.12)'

            delta_label = 'GAIN'

        elif period_change < -0.2:

            delta_color = '#EF5350'

            delta_bg = 'rgba(239,83,80,0.12)'

            delta_label = 'LOSS'

        else:

            delta_color = '#FFC107'

            delta_bg = 'rgba(255,193,7,0.12)'

            delta_label = 'NEUTRAL'

        period_high_color = '#26A69A' if current_price >= period_high * 0.98 else '#cfd6e6'

        period_low_color = '#EF5350' if current_price <= period_low * 1.02 else '#cfd6e6'

        if latest_volume >= avg_volume * 1.2:

            volume_color = '#26A69A'

        elif latest_volume <= avg_volume * 0.8:

            volume_color = '#EF5350'

        else:

            volume_color = '#FFC107'

        annual_vol_color = '#EF5350' if annual_vol >= 45 else '#FFC107' if annual_vol >= 25 else '#26A69A'

        theme_palette = st.session_state.get('theme_palette', {})

        card_bg = theme_palette.get('panel', '#181818')

        hero_bg = theme_palette.get('panel_alt', '#212121')

        card_border = theme_palette.get('border', '#303030')

        text_color = theme_palette.get('text', '#ffffff')

        muted_color = theme_palette.get('muted', '#9e9e9e')



        # ?? tile helpers ???????????????????????????????????????????????????

        def _tile(label, value, sub, accent, val_color=None, sub_color=None, val_size="1.15rem"):

            if val_color is None:

                val_color = text_color

            if sub_color is None:

                sub_color = muted_color

            return (

                f"<div class='cp-theme-tile' style='background:{card_bg}; border:1px solid {card_border};"

                f" border-top:2px solid {accent}; border-radius:8px; padding:1rem 1.1rem;'>"

                f"<div style='font-size:0.68rem; color:{muted_color}; text-transform:uppercase;"

                f" letter-spacing:0.8px; font-weight:600; margin-bottom:0.5rem;'>{label}</div>"

                f"<div style='font-size:{val_size}; font-weight:700; color:{val_color}; line-height:1.1;'>{value}</div>"

                f"<div style='font-size:0.72rem; color:{sub_color}; margin-top:0.35rem; font-weight:600;'>{sub}</div>"

                f"</div>"

            )



        def _arrow(val):

            return "&#8593;" if val >= 0 else "&#8595;"   # ? ?



        def _chg_color(val):

            return "#26A69A" if val >= 0 else "#EF5350"



        # ?? precompute sub values ??????????????????????????????????????????

        high_diff    = (period_high - current_price) / current_price * 100

        low_diff     = (period_low  - current_price) / current_price * 100

        vol_diff_pct = ((latest_volume / avg_volume - 1) * 100) if avg_volume > 0 else 0



        price_sub   = f"{_arrow(period_change)} {period_change:+.2f}%  ·  start {first['Close']:.2f} SAR"

        high_sub    = f"{_arrow(high_diff)} {high_diff:+.1f}% from current"

        low_sub     = f"{_arrow(low_diff)} {low_diff:+.1f}% from current"

        vol_sub     = (f"{_arrow(vol_diff_pct)} {vol_diff_pct:+.0f}% vs avg  ·  latest {latest_volume:,.0f}"

                       if avg_volume > 0 else "-")

        ann_label   = ("&#8595; LOW volatility" if annual_vol < 25

                       else "&#8593; HIGH volatility" if annual_vol >= 45

                       else "~ MID volatility")

        ann_sub_col = annual_vol_color



        tiles_top = (

            _tile("Start Price",

                  f"{first['Close']:.2f} SAR",

                  "First price in analysis period",

                  "#4A9EFF",

                  val_color="#4A9EFF",

                  sub_color="#4A9EFF",

                  val_size="1.5rem")

            + _tile("Current Price",

                  f"{current_price:.2f} SAR",

                  price_sub,

                  delta_color,

                  val_color=delta_color,

                  sub_color=_chg_color(period_change),

                  val_size="1.5rem")

            + _tile("Period High",

                    f"{period_high:.2f} SAR",

                    high_sub,

                    "#26A69A",

                    val_color=text_color,

                    sub_color="#26A69A",

                    val_size="1.5rem")

            + _tile("Period Low",

                    f"{period_low:.2f} SAR",

                    low_sub,

                    "#EF5350",

                    val_color=text_color,

                    sub_color="#EF5350",

                    val_size="1.5rem")

            + _tile("Avg Daily Volume",

                    f"{avg_volume:,.0f}",

                    vol_sub,

                    volume_color,

                    val_color=text_color,

                    sub_color=_chg_color(vol_diff_pct),

                    val_size="1.5rem")

        )



        tiles_bot = (

            _tile("Analysis Period",

                  f"{df.iloc[0]['Date'].strftime('%b %d, %Y')} &#8594; {df.iloc[-1]['Date'].strftime('%b %d, %Y')}",

                  f"{len(df):,} trading days",

                  "#4A9EFF")

            + _tile("Price Range",

                    f"{price_range:.2f} SAR",

                    f"{volatility:.1f}% of period low",

                    "#4A9EFF")

            + _tile("Annualized Volatility",

                    f"{annual_vol:.1f}%",

                    ann_label,

                    annual_vol_color,

                    val_color=annual_vol_color,

                    sub_color=ann_sub_col)

        )



        _period_label = df.iloc[0]['Date'].strftime('%b %Y') + " &#8594; " + df.iloc[-1]['Date'].strftime('%b %Y')

        _regime_pill = (

            f"<span style='font-size:0.68rem; color:{muted_color}; text-transform:uppercase;"

            " letter-spacing:0.8px; font-weight:600; margin-right:0.5rem;'>Regime</span>"

            "<span style='font-size:0.78rem; font-weight:700; color:#fff; background:" + regime_color + ";"

            " padding:0.25rem 0.85rem; border-radius:20px; letter-spacing:0.5px;'>" + latest['REGIME'] + "</span>"

        )

        hero_html = (

            f"<div class='cp-theme-card' style='background:{hero_bg}; border:1px solid {card_border}; border-radius:12px;"

            " padding:1.6rem 1.8rem; margin-bottom:1.4rem;'>"



            "<div style='display:flex; justify-content:space-between; align-items:center;"

            " flex-wrap:wrap; gap:0.6rem; margin-bottom:1.1rem;'>"

            "<div>"

            f"<div style='font-size:1.3rem; font-weight:700; color:{text_color}; line-height:1.2;'>" + stock_name + "</div>"

            f"<div style='font-size:0.8rem; color:{muted_color}; margin-top:0.28rem; font-weight:500;'>"

            + symbol_input + "&nbsp;&nbsp;&#183;&nbsp;&nbsp;" + _period_label +

            "</div>"

            "</div>"

            "<div style='display:flex; align-items:center;'>" + _regime_pill + "</div>"

            "</div>"



            f"<div style='border-top:1px solid {card_border}; margin-bottom:0.9rem;'></div>"



            "<div style='display:grid; grid-template-columns:repeat(5,1fr); gap:0.7rem; margin-bottom:0.7rem;'>"

            + tiles_top +

            "</div>"



            "<div style='display:grid; grid-template-columns:repeat(3,1fr); gap:0.7rem;'>"

            + tiles_bot +

            "</div>"



            "</div>"

        )

        st.markdown(hero_html, unsafe_allow_html=True)

        

        # Calculate metrics for snapshot and recommendations

        current_regime = latest['REGIME']

        last_20_regimes = df.tail(20)['REGIME'].value_counts()

        regime_stability = (last_20_regimes.iloc[0] / 20 * 100) if len(last_20_regimes) > 0 else 0



        # TABS START HERE

        # ?? precompute metrics for gemini_tab ??????????????????????????????

        adx_current    = float(latest.get('ADX_14', 20))

        rsi_current    = float(latest.get('RSI_14', 50))

        _ema20_v       = latest.get('EMA_20',  current_price) or current_price

        _ema200_v      = latest.get('EMA_200', current_price) or current_price

        price_vs_ema20 = (current_price / _ema20_v  - 1) * 100

        price_vs_ema200= (current_price / _ema200_v - 1) * 100

        _n5  = max(len(df) - 6,  0)

        _n20 = max(len(df) - 21, 0)

        recent_5d_change  = ((current_price - df.iloc[_n5]['Close'])  / df.iloc[_n5]['Close'])  * 100 if len(df) >= 2 else 0

        recent_20d_change = ((current_price - df.iloc[_n20]['Close']) / df.iloc[_n20]['Close']) * 100 if len(df) >= 2 else 0

        _atr_raw = latest.get('ATR_14', 0)

        atr_pct  = (_atr_raw / current_price * 100) if current_price > 0 and _atr_raw > 0 else 2.0



        from regime_analysis_tab import render_regime_analysis_tab
        from decision_tab import render_decision_tab

        from signal_analysis_tab import signal_analysis_tab
        from patterns_tab import patterns_tab
        from volume_profile_tab import volume_profile_tab
        from smc_tab import smc_tab
        from trade_validator_tab import trade_validator_tab

        # AI cache pre-warm removed — tabs compute on demand (Streamlit lazy-loads tab content)

        tab_dec, tab0, tab1, tab2, tab_vp, tab_smc, tab4, tab_tv = st.tabs([
            "Decision",
            "Regime",
            "Signals",
            "Patterns & Price Action",
            "Volume Profile",
            "SMC",
            "AI Analysis",
            "Trade Validator",
        ])

        with tab_dec:
            render_decision_tab(df, symbol_input, stock_name, current_price)

        with tab0:
            render_regime_analysis_tab(df, info_icon, create_regime_distribution_chart)
        with tab1:
            signal_analysis_tab(df, info_icon)
        with tab2:
            price_action_analysis_tab(df, info_icon)
            patterns_tab(df)
        with tab_vp:
            volume_profile_tab(df, current_price)
        with tab_smc:
            smc_tab(df, current_price)
        with tab4:
            gemini_tab(

                df, symbol_input, stock_name, latest,

                current_price, period_change, period_high, period_low,

                annual_vol, current_regime, adx_current, rsi_current,

                atr_pct, price_vs_ema20, price_vs_ema200,

                recent_5d_change, recent_20d_change,

            )
        with tab_tv:
            trade_validator_tab(df, latest, current_price)










if __name__ == "__main__":

    if auth_wall():

        main()

