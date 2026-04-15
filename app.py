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
from favorites_tab import favorites_css, render_favorites_panel, render_saved_page
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
from ui_helpers import info_icon, apply_ui_theme, insight_toggle

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

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    .stApp, .stApp * { font-family: 'Inter', system-ui, -apple-system, sans-serif !important; }

    #MainMenu, footer, header,

    [data-testid="stToolbar"], [data-testid="stDecoration"],

    [data-testid="stStatusWidget"],

    [data-testid="stHeader"],

    [data-testid="collapsedControl"] {

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

    /* ── Hero info card design system ───────────────────────────────── */
    .hero-wrap { background:#1b1b1b; border:1px solid #272727; border-radius:14px;
                 overflow:hidden; margin-bottom:1.4rem; box-shadow:0 4px 24px rgba(0,0,0,0.3); }
    .hero-inner { padding:1.6rem 1.8rem; }
    .hero-hdr { display:flex; justify-content:space-between; align-items:center;
                flex-wrap:wrap; gap:0.6rem; margin-bottom:1.1rem; }
    .hero-name { font-size:1.5rem; font-weight:800; color:#e0e0e0; line-height:1.2; }
    .hero-sub { font-size:0.78rem; color:#606060; margin-top:0.28rem; font-weight:600; }
    .hero-divider { border-top:1px solid #272727; margin-bottom:0.9rem; }
    .hero-grid5 { display:grid; grid-template-columns:repeat(5,1fr); gap:0.7rem; margin-bottom:0.7rem; }
    .hero-grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:0.7rem; }
    .hero-tile { background:#161616; border:1px solid #272727; border-radius:10px;
                 padding:1rem 1.1rem; overflow:hidden; }
    .hero-tile-lbl { font-size:0.62rem; color:#606060; text-transform:uppercase;
                     letter-spacing:1px; font-weight:700; margin-bottom:0.5rem;
                     display:flex; align-items:center; }
    .hero-tile-val { font-size:1.15rem; font-weight:800; color:#e0e0e0; line-height:1.1; }
    .hero-tile-val.lg { font-size:1.5rem; }
    .hero-tile-sub { font-size:0.68rem; margin-top:0.35rem; font-weight:600; }
    .hero-tip { display:inline-flex; align-items:center; justify-content:center;
                width:14px; height:14px; border-radius:50%; background:#272727; color:#606060;
                font-size:0.48rem; font-weight:700; margin-left:0.4rem; cursor:help; }

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

        position: sticky !important;

        top: 0 !important;

        z-index: 9999 !important;

        backdrop-filter: blur(12px) !important;

        -webkit-backdrop-filter: blur(12px) !important;

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

    /* ── Save-button footer panels (attached to indicator/combo cards) ── */

    /* Remove the gap/margin on the element container that wraps the save button container */
    [class*="st-key-ind_save_wrap_"],
    [class*="st-key-ind-save-wrap-"],
    [class*="st-key-combo_save_wrap_"],
    [class*="st-key-combo-save-wrap-"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }

    [class*="st-key-ind_save_wrap_"] > div[data-testid="stVerticalBlock"],
    [class*="st-key-ind-save-wrap-"] > div[data-testid="stVerticalBlock"] {

        background: #181818 !important;

        border: 1px solid #2d2d2d !important;

        border-top: none !important;

        border-radius: 0 0 14px 14px !important;

        padding: 0.35rem 1.4rem 0.6rem !important;

        margin-top: 0 !important;

        margin-bottom: 1.2rem !important;

    }

    [class*="st-key-ind_save_wrap_"] > div[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
    [class*="st-key-ind-save-wrap-"] > div[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
    [class*="st-key-combo_save_wrap_"] > div[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
    [class*="st-key-combo-save-wrap-"] > div[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Full-width button inside save wrappers */
    [class*="st-key-ind_save_wrap_"] .stButton > button,
    [class*="st-key-ind-save-wrap-"] .stButton > button,
    [class*="st-key-combo_save_wrap_"] .stButton > button,
    [class*="st-key-combo-save-wrap-"] .stButton > button {
        width: 100% !important;
        border-radius: 0 0 14px 14px !important;
        background: #0f1214 !important;
        border: none !important;
        border-top: 1px solid #252b2e !important;
        color: #5a6470 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
        letter-spacing: 0.3px !important;
        transition: background 0.15s ease, color 0.15s ease !important;
    }

    [class*="st-key-ind_save_wrap_"] .stButton > button:hover,
    [class*="st-key-ind-save-wrap-"] .stButton > button:hover,
    [class*="st-key-combo_save_wrap_"] .stButton > button:hover,
    [class*="st-key-combo-save-wrap-"] .stButton > button:hover {
        background: #26A69A !important;
        color: #fff !important;
        border-top-color: #26A69A !important;
    }

    [class*="st-key-combo_save_wrap_"] > div[data-testid="stVerticalBlock"],
    [class*="st-key-combo-save-wrap-"] > div[data-testid="stVerticalBlock"] {

        background: #1a1a1a !important;

        border: 1px solid #2d2d2d !important;

        border-top: none !important;

        border-radius: 0 0 14px 14px !important;

        padding: 0 !important;

        margin-top: 0 !important;

        margin-bottom: 1rem !important;

    }

    /* ── Main tab-list: cohesive dark design ── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: #1b1b1b !important;
        border-radius: 12px !important;
        padding: 0.2rem 0.25rem !important;
        gap: 0 !important;
        border: 1px solid #272727 !important;
        margin-bottom: 1.5rem !important;
        min-height: auto !important;
        box-shadow: 0 2px 16px rgba(0,0,0,0.25) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background: transparent !important;
        color: #555 !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.25px !important;
        padding: 0.55rem 1.2rem !important;
        border: none !important;
        margin: 0.2rem 0.1rem !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        color: #999 !important;
        background: rgba(255,255,255,0.03) !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(135deg,rgba(38,166,154,0.12),rgba(33,150,243,0.06)) !important;
        color: #e0e0e0 !important;
        border: 1px solid rgba(38,166,154,0.25) !important;
        font-weight: 700 !important;
        box-shadow: 0 0 12px rgba(38,166,154,0.08) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-border"],
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-panel"] {
        padding: 0 !important;
    }

    /* ── Sidebar premium nav ── */
    [data-testid="stSidebar"] {
        background: #0d1013 !important;
        border-right: 1px solid #1a1f23 !important;
        min-width: 210px !important;
        max-width: 210px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.4rem 0.85rem 1.4rem 0.85rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 4px !important;
        flex-direction: column !important;
        display: flex !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.2px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background: transparent !important;
        color: #5a6470 !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.9rem !important;
        cursor: pointer !important;
        transition: background 0.12s, color 0.12s !important;
        display: flex !important;
        align-items: center !important;
        gap: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: #1a1f23 !important;
        color: #c8cdd2 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] input:checked ~ div {
        background: #26A69A !important;
        color: #fff !important;
        border-color: #26A69A !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] [data-baseweb="radio"] {
        display: none !important;
    }
    /* hide actual radio circle indicator */
    [data-testid="stSidebar"] [data-testid="stRadio"] span[data-baseweb="radio"] {
        display: none !important;
    }

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

    if 'show_macro' not in st.session_state:

        st.session_state.show_macro = False

    if 'show_saved_page' not in st.session_state:

        st.session_state.show_saved_page = False



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

        // Pre-load Google Translate script immediately so first click is instant
        (function() {
            var s = doc.createElement('script');
            s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
            doc.body.appendChild(s);
        })();

        function _doTranslate() {
            var sel = doc.querySelector('.goog-te-combo');
            if (!sel) {
                // Widget not ready yet — retry in 200ms
                setTimeout(_doTranslate, 200);
                return;
            }
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

        btn.addEventListener('click', function() {
            _doTranslate();
        });
    })();
    // ── Icons on original tabs + ghost sticky bar ──
    (function() {
        var doc = window.parent.document;
        var win = window.parent;
        var GHO = 'sqnb_ghost';
        var NH  = 54;
        var cssOk = false, moOk = false, scrollOk = false;
        var tabsTop = 9999;

        var TABS = [
            {l:'Decision',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>'},
            {l:'Regime',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'},
            {l:'Signals',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'},
            {l:'Patterns',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'},
            {l:'Volume',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="6" x2="16" y2="6"/><line x1="4" y1="10" x2="20" y2="10"/><line x1="4" y1="14" x2="12" y2="14"/><line x1="4" y1="18" x2="18" y2="18"/></svg>'},
            {l:'SMC',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'},
            {l:'Elliott Wave',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="2 17 6 9 10 13 14 5 18 11 22 3"/></svg>',
             badge:'NEW'},
            {l:'AI Analysis',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.636 5.636l1.414 1.414M16.95 16.95l1.414 1.414M5.636 18.364l1.414-1.414M16.95 7.05l1.414-1.414"/></svg>'},
            {l:'Validator',
             v:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>'},
        ];

        function getTL() {
            var tls = doc.querySelectorAll('div[role="tablist"]');
            for (var i = 0; i < tls.length; i++) {
                if (tls[i].querySelectorAll('button').length >= 6) return tls[i];
            }
            return null;
        }
        function getActiveIdx() {
            var tl = getTL(); if (!tl) return 0;
            var bs = tl.querySelectorAll('button');
            for (var i = 0; i < bs.length; i++) {
                if (bs[i].getAttribute('aria-selected') === 'true') return i;
            }
            return 0;
        }

        function makeButtons(ai) {
            var h = '';
            TABS.forEach(function(tab, i) {
                var on = (i === ai);
                var bg  = on
                    ? 'linear-gradient(135deg,rgba(38,166,154,0.22),rgba(33,150,243,0.12))'
                    : 'transparent';
                var bdr = on
                    ? '1px solid rgba(38,166,154,0.4)'
                    : '1px solid transparent';
                var col = on ? '#e2e8f0' : '#4a5568';
                var fw  = on ? '650' : '500';
                h += '<button class="sqnb-btn" data-i="' + i + '" style="' +
                    'display:flex;align-items:center;gap:7px;padding:0 1.1rem;margin:0 3px;' +
                    'background:' + bg + ';' +
                    'border:' + bdr + ';' +
                    'border-radius:10px;' +
                    'color:' + col + ';' +
                    'font-size:.8rem;font-weight:' + fw + ';' +
                    'cursor:pointer;white-space:nowrap;' +
                    'height:calc(100% - 16px);align-self:center;flex-shrink:0;letter-spacing:.2px;' +
                    'transition:color .2s,background .2s,border-color .2s,transform .15s;">' +
                    '<span class="sqnb-ico" style="display:inline-flex;align-items:center;opacity:' + (on ? '1' : '.45') + ';transition:opacity .2s;pointer-events:none;">' + tab.v + '</span>' +
                    '<span>' + tab.l + '</span>' +
                    (tab.badge ? '<span style="margin-left:5px;padding:1px 6px;border-radius:8px;font-size:0.5rem;font-weight:800;letter-spacing:0.5px;background:rgba(76,175,80,0.15);color:#4caf50;border:1px solid rgba(76,175,80,0.35);text-transform:uppercase;line-height:1.4;">' + tab.badge + '</span>' : '') +
                    '</button>';
            });
            return h;
        }

        // Inject SVG icons into Streamlit's own buttons (re-added after React re-renders via MO)
        function addIcons() {
            var tl = getTL(); if (!tl) return;
            tl.querySelectorAll('button').forEach(function(b, i) {
                if (i >= TABS.length) return;
                if (b.querySelector('.sqnb-ico')) return;
                var sp = doc.createElement('span');
                sp.className = 'sqnb-ico';
                sp.innerHTML = TABS[i].v;
                var isOn = b.getAttribute('aria-selected') === 'true';
                sp.style.cssText = 'display:inline-flex;align-items:center;margin-right:6px;' +
                    'vertical-align:middle;pointer-events:none;opacity:' + (isOn ? '1' : '.45') + ';transition:opacity .2s;';
                b.insertBefore(sp, b.firstChild);
                // NEW badge
                if (TABS[i].badge && !b.querySelector('.sqnb-badge')) {
                    var bd = doc.createElement('span');
                    bd.className = 'sqnb-badge';
                    bd.textContent = TABS[i].badge;
                    bd.style.cssText = 'display:inline-flex;align-items:center;margin-left:6px;padding:1px 6px;' +
                        'border-radius:8px;font-size:0.5rem;font-weight:800;letter-spacing:0.5px;' +
                        'background:rgba(76,175,80,0.15);color:#4caf50;border:1px solid rgba(76,175,80,0.35);' +
                        'text-transform:uppercase;line-height:1.4;pointer-events:none;';
                    b.appendChild(bd);
                }
            });
        }

        function injectCSS() {
            if (cssOk) return; cssOk = true;
            var s = doc.createElement('style');
            s.textContent =
                '#' + GHO + '::-webkit-scrollbar{display:none}' +
                '.sqnb-btn:hover{color:#a0aec0 !important;background:rgba(255,255,255,0.05) !important;transform:translateY(-1px)}' +
                '.sqnb-btn:hover .sqnb-ico{opacity:.8 !important}' +
                '.sqnb-btn{transition:color .2s,background .2s,border-color .2s,transform .15s !important}';
            doc.head.appendChild(s);
        }

        function buildGhost() {
            if (doc.getElementById(GHO)) return;
            injectCSS();
            var g = doc.createElement('div');
            g.id = GHO;
            g.style.cssText =
                'position:fixed;top:0;left:0;right:0;height:' + NH + 'px;z-index:999999;' +
                'background:rgba(14,17,22,.97);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);' +
                'border-bottom:1px solid rgba(38,166,154,0.12);' +
                'box-shadow:0 1px 0 rgba(38,166,154,0.08),0 8px 32px rgba(0,0,0,.6);' +
                'display:flex;align-items:center;padding:0 0.75rem;gap:2px;' +
                'overflow-x:auto;overflow-y:hidden;scrollbar-width:none;-ms-overflow-style:none;' +
                'opacity:0;pointer-events:none;transition:opacity .22s cubic-bezier(.4,0,.2,1),transform .22s cubic-bezier(.4,0,.2,1);' +
                'transform:translateY(-6px);';
            g.innerHTML = makeButtons(getActiveIdx());
            g.querySelectorAll('.sqnb-btn').forEach(function(b) {
                b.addEventListener('click', function() {
                    var idx = parseInt(b.getAttribute('data-i'));
                    var tl = getTL();
                    if (tl) { var ob = tl.querySelectorAll('button')[idx]; if (ob) ob.click(); }
                });
            });
            doc.body.appendChild(g);
        }

        function showGhost(show) {
            var g = doc.getElementById(GHO); if (!g) return;
            g.style.opacity       = show ? '1' : '0';
            g.style.pointerEvents = show ? 'auto' : 'none';
            g.style.transform     = show ? 'translateY(0)' : 'translateY(-6px)';
        }

        function syncAll() {
            var ai = getActiveIdx();
            var g = doc.getElementById(GHO);
            if (g) {
                g.querySelectorAll('.sqnb-btn').forEach(function(b, i) {
                    var on = (i === ai);
                    b.style.background   = on
                        ? 'linear-gradient(135deg,rgba(38,166,154,0.22),rgba(33,150,243,0.12))'
                        : 'transparent';
                    b.style.border       = on
                        ? '1px solid rgba(38,166,154,0.4)'
                        : '1px solid transparent';
                    b.style.color        = on ? '#e2e8f0' : '#4a5568';
                    b.style.fontWeight   = on ? '650' : '500';
                    var ic = b.querySelector('.sqnb-ico');
                    if (ic) ic.style.opacity = on ? '1' : '.45';
                });
            }
            var tl = getTL();
            if (tl) {
                tl.querySelectorAll('button').forEach(function(b, i) {
                    var ic = b.querySelector('.sqnb-ico');
                    if (ic) ic.style.opacity = (i === ai) ? '1' : '.45';
                });
            }
        }

        function recordTabsTop() {
            var tl = getTL(); if (!tl) return;
            var rect = tl.getBoundingClientRect();
            var measured = rect.top + (win.pageYOffset || win.scrollY || 0);
            if (measured > 50) tabsTop = measured;
        }

        function setupScroll() {
            if (scrollOk) return; scrollOk = true;
            win.addEventListener('scroll', function() {
                var scrolled = win.pageYOffset || win.scrollY || 0;
                showGhost(scrolled > tabsTop - 20);
            }, {passive: true});
        }

        function setupMO() {
            if (moOk) return; moOk = true;
            new MutationObserver(function() {
                addIcons();
                syncAll();
            }).observe(doc.body, {subtree:true, childList:true, attributes:true, attributeFilter:['aria-selected']});
        }

        function run() {
            addIcons();
            buildGhost();
            recordTabsTop();
            setupScroll();
            setupMO();
            syncAll();
        }

        run();
        [200, 500, 1000, 2000, 4000].forEach(function(t) { setTimeout(run, t); });

        var iv = setInterval(function() { addIcons(); syncAll(); }, 900);
        setTimeout(function() { clearInterval(iv); }, 120000);
    })();
    </script>
    """, height=0)

    if not st.session_state.show_results and not st.session_state.show_market_results and not st.session_state.show_market_pulse and not st.session_state.show_macro and not st.session_state.show_saved_page:

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

        /* ── Brand header ──────────────────────────────────────────────── */
        .lp-brand {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 0.5px;
            text-align: center;
            padding: 0.4rem 0;
            margin: 0;
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
        # ── Handle ?goto=TICKER from card "Open Analysis" anchor links ────
        _qp_goto = st.query_params.get("goto", "")
        if _qp_goto:
            _qp_sym = str(_qp_goto).replace(".SR", "")
            st.query_params.clear()
            st.session_state["symbol_input"] = _qp_sym
            st.session_state["screener_auto_analyze"] = True
            st.rerun()

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

                    # Brand header
                    st.markdown('<div class="lp-brand">Tadawul</div>', unsafe_allow_html=True)

                    # Period state + labels (used throughout left panel)
                    _ap = st.session_state.get('mkt_period', '1d')
                    _period_names = {"1d":"Today","1w":"This Week","1m":"1 Month","3m":"3 Months","6m":"6 Months","1y":"1 Year"}
                    _perf_subtitle = _period_names.get(_ap, "Today")


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

                    # Action buttons — 2 columns: Saved | User
                    _b1, _b2 = st.columns(2, gap="small")
                    with _b1:
                        with st.container(key="btn_saved"):
                            _fav_lbl = f"♡  Saved · {fav_count}" if has_favs else "♡  Saved"
                            if st.button(_fav_lbl, key="toolbar_fav", width="stretch"):
                                st.session_state.show_saved_page = True
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

                    # ── Tomorrow Forecast ──────────────────────────────────
                    _breadth_ratio = gainers / max(losers, 1)
                    _adv_pct = gainers / max(gainers + losers + unchanged, 1) * 100
                    _dec_pct = losers / max(gainers + losers + unchanged, 1) * 100

                    # Momentum score (−100 to +100)
                    _mom_score = 0
                    # Breadth component (max ±35)
                    if _breadth_ratio > 2.0:
                        _mom_score += 35
                    elif _breadth_ratio > 1.3:
                        _mom_score += 20
                    elif _breadth_ratio > 0.9:
                        _mom_score += 5
                    elif _breadth_ratio > 0.5:
                        _mom_score -= 20
                    else:
                        _mom_score -= 35

                    # TASI change component (max ±35)
                    if tasi_change > 1.0:
                        _mom_score += 35
                    elif tasi_change > 0.3:
                        _mom_score += 20
                    elif tasi_change > -0.3:
                        _mom_score += 0
                    elif tasi_change > -1.0:
                        _mom_score -= 20
                    else:
                        _mom_score -= 35

                    # Avg change component (max ±30)
                    if avg_change > 1.0:
                        _mom_score += 30
                    elif avg_change > 0.3:
                        _mom_score += 15
                    elif avg_change > -0.3:
                        _mom_score += 0
                    elif avg_change > -1.0:
                        _mom_score -= 15
                    else:
                        _mom_score -= 30

                    _mom_score = max(-100, min(100, _mom_score))

                    if _mom_score >= 50:
                        _fc_label, _fc_color, _fc_icon = 'LIKELY UP', '#26A69A', '▲'
                    elif _mom_score >= 15:
                        _fc_label, _fc_color, _fc_icon = 'LEAN BULLISH', '#66bb6a', '↗'
                    elif _mom_score >= -15:
                        _fc_label, _fc_color, _fc_icon = 'NEUTRAL', '#ffc107', '→'
                    elif _mom_score >= -50:
                        _fc_label, _fc_color, _fc_icon = 'LEAN BEARISH', '#ff7043', '↘'
                    else:
                        _fc_label, _fc_color, _fc_icon = 'LIKELY DOWN', '#ef5350', '▼'

                    _fc_bar_w = abs(_mom_score)
                    _fc_bar_side = 'right' if _mom_score >= 0 else 'left'
                    st.markdown(
                        f'<div class="mstat-card">'
                        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;">'
                        f'<div class="mstat-label" style="margin:0;">Tomorrow Forecast</div>'
                        f'<span style="font-size:0.52rem;font-weight:700;color:#26A69A;background:rgba(38,166,154,0.13);'
                        f'border:1px solid rgba(38,166,154,0.3);border-radius:99px;padding:1px 7px;letter-spacing:0.3px;">NEW</span>'
                        f'<span style="margin-left:auto;display:flex;align-items:baseline;gap:3px;">'
                        f'<span style="font-size:1.1rem;font-weight:900;color:{_fc_color};">{_mom_score:+d}</span>'
                        f'<span style="font-size:0.6rem;font-weight:600;color:#505050;">/100</span>'
                        f'<span title="Momentum Score (-100 to +100). Combines three signals: Breadth ratio (how many stocks are up vs down), TASI index movement, and average stock performance. Above +50 = likely up day, below -50 = likely down day." '
                        f'style="display:inline-flex;align-items:center;justify-content:center;width:13px;height:13px;'
                        f'border-radius:50%;background:rgba(255,255,255,0.06);font-size:0.45rem;color:#888;cursor:help;'
                        f'font-weight:800;margin-left:2px;">?</span>'
                        f'</span>'
                        f'</div>'
                        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
                        f'<span style="font-size:1.4rem;line-height:1;color:{_fc_color};">{_fc_icon}</span>'
                        f'<span style="font-size:1rem;font-weight:800;color:{_fc_color};letter-spacing:-0.3px;">{_fc_label}</span>'
                        f'</div>'
                        f'<div style="position:relative;height:6px;background:rgba(255,255,255,0.06);border-radius:3px;margin-bottom:10px;">'
                        f'<div style="position:absolute;top:0;{_fc_bar_side}:50%;height:100%;'
                        f'width:{_fc_bar_w/2:.1f}%;background:{_fc_color};border-radius:3px;'
                        f'box-shadow:0 0 8px {_fc_color}44;"></div>'
                        f'<div style="position:absolute;top:-2px;left:calc(50% - 1px);width:2px;height:10px;'
                        f'background:rgba(255,255,255,0.25);border-radius:1px;"></div>'
                        f'</div>'
                        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;">'
                        f'<div style="text-align:center;padding:5px;background:rgba(255,255,255,0.025);border-radius:6px;position:relative;">'
                        f'<div style="font-size:0.62rem;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">'
                        f'Breadth <span title="Ratio of advancing stocks to declining stocks. Above 1.0 = more stocks rising than falling." '
                        f'style="display:inline-flex;align-items:center;justify-content:center;width:12px;height:12px;'
                        f'border-radius:50%;background:rgba(255,255,255,0.06);font-size:0.45rem;color:#888;cursor:help;'
                        f'font-weight:800;vertical-align:middle;">?</span></div>'
                        f'<div style="font-size:0.82rem;font-weight:700;color:{"#26A69A" if _breadth_ratio > 1 else "#ef5350"};">{_breadth_ratio:.2f}</div></div>'
                        f'<div style="text-align:center;padding:5px;background:rgba(255,255,255,0.025);border-radius:6px;">'
                        f'<div style="font-size:0.62rem;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">'
                        f'Advancers <span title="Percentage of stocks that closed higher today." '
                        f'style="display:inline-flex;align-items:center;justify-content:center;width:12px;height:12px;'
                        f'border-radius:50%;background:rgba(255,255,255,0.06);font-size:0.45rem;color:#888;cursor:help;'
                        f'font-weight:800;vertical-align:middle;">?</span></div>'
                        f'<div style="font-size:0.82rem;font-weight:700;color:#26A69A;">{_adv_pct:.0f}%</div></div>'
                        f'<div style="text-align:center;padding:5px;background:rgba(255,255,255,0.025);border-radius:6px;">'
                        f'<div style="font-size:0.62rem;color:#505050;text-transform:uppercase;letter-spacing:0.5px;">'
                        f'Decliners <span title="Percentage of stocks that closed lower today." '
                        f'style="display:inline-flex;align-items:center;justify-content:center;width:12px;height:12px;'
                        f'border-radius:50%;background:rgba(255,255,255,0.06);font-size:0.45rem;color:#888;cursor:help;'
                        f'font-weight:800;vertical-align:middle;">?</span></div>'
                        f'<div style="font-size:0.82rem;font-weight:700;color:#ef5350;">{_dec_pct:.0f}%</div></div>'
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
                        if "symbol_input" not in st.session_state:
                            st.session_state["symbol_input"] = "1120"
                        user_symbol = st.text_input(
                            "Stock Symbol", key="symbol_input",
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

                            _fmd1, _fmd2 = st.columns(2)
                            with _fmd1:
                                st.markdown("<div class='cp-input-label'>From</div>", unsafe_allow_html=True)
                                _fm_start = st.date_input("From",
                                    value=(datetime.now() - timedelta(days=180)).date(),
                                    min_value=datetime(2002, 1, 1).date(),
                                    key="scr_fm_start",
                                    label_visibility="collapsed")
                            with _fmd2:
                                st.markdown("<div class='cp-input-label'>To</div>", unsafe_allow_html=True)
                                _fm_end = st.date_input("To",
                                    value=datetime.now().date(),
                                    min_value=datetime(2002, 1, 1).date(),
                                    key="scr_fm_end",
                                    label_visibility="collapsed")
                            st.markdown(
                                "<div style='color:#3a4550;font-size:0.68rem;margin:0.3rem 0 0.8rem;'>"
                                "Full market scan — takes 1-2 minutes.</div>",
                                unsafe_allow_html=True)

                            def run_market_analysis_callback_all():
                                _sd = st.session_state.get("scr_fm_start", (datetime.now() - timedelta(days=180)).date())
                                _ed = st.session_state.get("scr_fm_end", datetime.now().date())
                                with st.spinner(f"Scanning {len(ma_tickers_all)} stocks…"):
                                    res = run_market_analysis(
                                        tuple(ma_tickers_all), min_score=1, start=_sd, end=_ed)
                                    st.session_state.ma_results          = res
                                    st.session_state.ma_scanned_count    = len(ma_tickers_all)
                                    st.session_state.ma_scan_params      = {'start': str(_sd), 'end': str(_ed)}
                                    st.session_state.show_market_results = True

                            st.markdown("<div class='cp-run-wrap'>", unsafe_allow_html=True)
                            st.button("Run Full Market Scan", type="secondary", width="stretch",
                                      on_click=run_market_analysis_callback_all, key="ma_run_btn_all")
                            st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.show_saved_page:

        apply_ui_theme()

        render_saved_page()

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
        .msr-pick  { border-radius:14px; overflow:hidden; }
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
              transition:background 0.15s; }
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
        .sc-lv-l { font-size:0.54rem; font-weight:700; color:#686868;
                   text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; }
        .sc-div-vert { width:1px; background:rgba(255,255,255,0.07); flex-shrink:0; }
        .sc-inds { display:flex; }
        .sc-ind  { text-align:center; padding:0.6rem 0.6rem;
                   border-right:1px solid rgba(255,255,255,0.04); }
        .sc-ind:last-child { border-right:none; }
        .sc-iv   { font-size:0.82rem; font-weight:700; line-height:1; }
        .sc-il   { font-size:0.5rem; font-weight:600; color:#686868;
                   text-transform:uppercase; letter-spacing:0.4px; margin-top:4px; }

        /* Conviction bar */
        .sc-conv { display:flex; align-items:center; gap:0.55rem;
                   padding:0.38rem 1rem; background:rgba(0,0,0,0.08); }
        .sc-conv-lbl { font-size:0.52rem; font-weight:700; text-transform:uppercase;
                       letter-spacing:0.5px; color:#686868; flex-shrink:0; }
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
        .msr-sec-row  { display:flex; align-items:center; gap:0.6rem; margin:0.8rem 0 0.7rem; padding:0.5rem 0.8rem; background:#1a1a1a; border-radius:8px; border:1px solid #252525; }
        .msr-sec-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
        .msr-sec-dot.buy  { background:#10a37f; } .msr-sec-dot.sell { background:#ef4444; }
        .msr-sec-dot.hold { background:#fbbf24; }
        .msr-sec-title { font-size:0.75rem; font-weight:800; letter-spacing:0.8px; text-transform:uppercase; }
        .msr-sec-title.buy  { color:#10a37f; } .msr-sec-title.sell { color:#ef4444; }
        .msr-sec-title.hold { color:#fbbf24; }
        .msr-sec-count { font-size:0.68rem; padding:0.14rem 0.6rem; border-radius:16px;
                         background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1); color:#888; margin-left:auto; }
        .msr-empty { text-align:center; padding:2.5rem 1rem; color:#555; font-size:0.88rem; }
        /* Streamlit tab buttons — bigger, readable */
        div[data-baseweb="tab"] button p {
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.2px;
        }
        /* Kill default Streamlit page top padding so New Scan button sits flush */
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stToolbar"]      { display: none !important; }
        .block-container { padding-top: 0.4rem !important; margin-top: 0 !important; }
        section[data-testid="stMainBlockContainer"] { padding-top: 0.4rem !important; }
        </style>""", unsafe_allow_html=True)

        # ── Back button ──────────────────────────────────────────────────────
        if st.button("← New Scan", type="secondary", use_container_width=True, key="ma_back_btn"):
                st.session_state.show_market_results = False
                st.rerun()

        # ── Stats ────────────────────────────────────────────────────────────
        tf_lbl        = params.get('timeframe', '6mo')
        sec_lbl       = params.get('sector', 'All Sectors')
        ms_lbl        = params.get('min_score', 2)

        # Pre-compute all_buy early — require real quality gates so count is meaningful
        # Score >= 3 (not just any spark), conviction >= 25, R:R >= 0.8
        all_buy = sorted(
            [s for s in all_stocks
             if s.get('score', 0) >= 3
             and s.get('conviction', 0) >= 25
             and s.get('rr_ratio', 0) >= 0.8],
            key=lambda x: x.get('priority_score', 0), reverse=True)

        avg_rr        = (sum(s.get('rr_ratio', 0) for s in all_buy) / len(all_buy)) if all_buy else 0
        best_conv     = max((s.get('conviction', 0) for s in all_buy), default=0)

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
            [s for s in all_buy
             if s.get('score', 0) >= 7
             and s.get('rr_ratio', 0) >= 1.8
             and s.get('conviction', 0) >= 50],
            key=lambda x: x.get('priority_score', 0), reverse=True)

        _hit_rate = round(len(all_buy) / scanned * 100) if scanned > 0 else 0

        # Useful stats for summary
        _avg_rr_ps = (sum(s.get('rr_ratio', 0) for s in _perfect_list) / len(_perfect_list)) if _perfect_list else 0
        _avg_upside_ps = (sum(abs(s.get('target1', s['price']) - s.get('entry', s['price'])) / s.get('entry', s['price']) * 100 for s in _perfect_list if s.get('entry', 0) > 0) / len(_perfect_list)) if _perfect_list else 0
        _top_conv = max((s.get('conviction', 0) for s in _perfect_list), default=0)

        # ── Market Scan Results Box — Premium Macro Intelligence ───────────────
        try:
            from macro_data import get_macro_snapshot, compute_macro_health, get_saudi_news_headlines
            _msnap  = get_macro_snapshot()
            _mscore, _mlabel, _mcolor, _mbg, _mfactors = compute_macro_health(_msnap) if _msnap else (0, "N/A", "#888", "#1a1a1a", [])
            _news   = get_saudi_news_headlines()
        except Exception:
            _msnap = {}; _mscore = 0; _mlabel = "N/A"; _mcolor = "#888"; _mbg = "#1a1a1a"; _mfactors = []; _news = []

        # ── plain-English score zone ──
        if _mscore >= 7:
            _zone_label = "IDEAL CONDITIONS"
            _zone_desc  = "Everything is aligned in your favor. Oil is strong, global markets are calm, Saudi stocks have room to run. Buy your best setups at full size with confidence."
            _zone_col   = '#10a37f'
        elif _mscore >= 3:
            _zone_label = "GOOD TIME TO BUY"
            _zone_desc  = "Conditions are supportive. No major red flags—oil is healthy and markets are stable. Invest normally in your high-conviction setups."
            _zone_col   = '#4A9EFF'
        elif _mscore >= -2:
            _zone_label = "NEUTRAL — MIXED SIGNALS"
            _zone_desc  = "Some things look good, some look worrying. Trade normally but use tighter stop-losses and don't put all your money into one trade."
            _zone_col   = '#fbbf24'
        elif _mscore >= -5:
            _zone_label = "BE CAREFUL"
            _zone_desc  = "Markets have headwinds—oil may be falling or global fear is rising. Only trade your absolute best setups and cut your position size in half."
            _zone_col   = '#f97316'
        else:
            _zone_label = "STAY OUT FOR NOW"
            _zone_desc  = "Oil is dropping, global markets are panicking, or there is a major geopolitical shock. Do NOT open new positions. Wait for things to stabilize first."
            _zone_col   = '#ef4444'

        # ── playbook (concise action line for the bar) ──
        _pb_lines = {
            6:  ("Buy strong setups at full size — tailwinds are working in your favour.",      '#10a37f'),
            2:  ("Normal position sizes — conditions are healthy with no major warning signs.", '#4A9EFF'),
           -2:  ("Trade only your best setups — reduce each position size by 25–30%.",         '#fbbf24'),
           -5:  ("High risk environment — max half-size positions with very tight stop-losses.",'#f97316'),
        }
        _pb_msg, _pb_col = next(
            ((m, c) for thresh, (m, c) in sorted(_pb_lines.items(), reverse=True) if _mscore >= thresh),
            ("Do not buy anything right now. Sit in cash and wait for oil and markets to recover.", '#ef4444')
        )

        # ── score bar fill 0–100% maps -10 → +10 ──
        _bar_pct = int((_mscore + 10) / 20 * 100)

        # ── instrument cards (all 8) — no emoji, label only ──
        _INST_LABELS = {
            'brent':  'BRENT OIL',
            'aramco': 'ARAMCO',
            'usd':    'USD',
            'gold':   'GOLD',
        }
        _inst_html = ""
        for _ikey in ['brent', 'aramco', 'usd', 'gold']:
            _d = (_msnap or {}).get(_ikey)
            if not _d:
                continue
            _ip, _ic1, _ic5, _ibu = _d['price'], _d['chg_1d'], _d['chg_5d'], _d['bullish_up']
            _ic1_col = '#10a37f' if (_ic1 >= 0) == _ibu else '#ef4444'
            _ic5_col = '#10a37f' if (_ic5 >= 0) == _ibu else '#ef4444'
            _is1 = '+' if _ic1 >= 0 else ''
            _is5 = '+' if _ic5 >= 0 else ''
            _unit = _d.get('unit', '')
            if _unit in ('$/bbl', '$/MMBtu'):
                _ipf = f"${_ip:.1f}"
            elif _unit == '$/oz':
                _ipf = f"${_ip:,.0f}"
            elif _unit == 'SAR':
                _ipf = f"SAR {_ip:.2f}"
            elif _unit == '$':
                _ipf = f"${_ip:.2f}"
            else:
                _ipf = f"{_ip:.1f}"
            _ilbl = _INST_LABELS.get(_ikey, _ikey.upper())
            _card_top_col = _ic5_col
            _inst_html += (
                f'<div style="background:#191919;border:1px solid #222;'
                f'border-top:3px solid {_card_top_col};border-radius:10px;'
                f'padding:0.85rem 1rem;min-width:110px;flex:1 1 110px;">'
                f'<div style="font-size:0.64rem;color:#888;font-weight:800;text-transform:uppercase;'
                f'letter-spacing:0.9px;margin-bottom:0.5rem;">{_ilbl}</div>'
                f'<div style="font-size:1.15rem;font-weight:900;color:#f0f0f0;'
                f'margin-bottom:0.55rem;white-space:nowrap;">{_ipf}</div>'
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'margin-bottom:0.22rem;">'
                f'<span style="font-size:0.66rem;color:#666;text-transform:uppercase;'
                f'letter-spacing:0.5px;">Today</span>'
                f'<span style="font-size:0.84rem;font-weight:800;color:{_ic1_col};">'
                f'{_is1}{_ic1:.1f}%</span></div>'
                f'<div style="display:flex;align-items:center;justify-content:space-between;">'
                f'<span style="font-size:0.66rem;color:#666;text-transform:uppercase;'
                f'letter-spacing:0.5px;">5 Days</span>'
                f'<span style="font-size:0.84rem;font-weight:800;color:{_ic5_col};">'
                f'{_is5}{_ic5:.1f}%</span></div>'
                f'</div>'
            )

        # ── macro factors ──
        _factors_html = ""
        for _fem, _ftitle, _fdetail, _fcolor in _mfactors:
            _factors_html += (
                f'<div style="border-left:3px solid {_fcolor};background:{_fcolor}0a;'
                f'border-radius:0 8px 8px 0;padding:0.65rem 0.85rem;margin-bottom:0.5rem;">'
                f'<div style="font-size:0.86rem;font-weight:800;color:{_fcolor};'
                f'line-height:1.35;margin-bottom:0.3rem;">{_ftitle}</div>'
                f'<div style="font-size:0.8rem;color:#909090;line-height:1.65;">{_fdetail}</div>'
                f'</div>'
            )
        if not _factors_html:
            _factors_html = (
                '<div style="font-size:0.85rem;color:#555;padding:0.8rem 0;">'
                'No significant macro drivers detected — markets are calm.</div>'
            )

        # ── news: filter to only market-moving headlines ──
        # Keywords that make a headline relevant to Saudi trading decisions
        _NEWS_CATS = [
            # (category_label, color, keywords_in_title_lower, why_it_matters_to_you)
            ('GEOPOLITICAL', '#ef4444',
             ['war','attack','conflict','military','strike','hamas','hezbollah','iran','russia',
              'ukraine','middle east','gaza','israel','missile','sanction','coup','troops',
              'escalat','tension','nuclear','rebel','terror','bomb','explosion','oil field'],
             'Middle East conflict or sanctions directly impact oil supply and cause market panic.'),
            ('OIL & ENERGY', '#f97316',
             ['oil','crude','brent','wti','opec','barrel','petroleum','energy price',
              'gas price','lng','natural gas','fuel','refin','oil output','production cut',
              'oil supply','oil demand','oil market','energy market'],
             'Oil price is the #1 driver of Saudi stocks. Any oil news moves the whole market.'),
            ('TRUMP / US', '#fbbf24',
             ['trump','tariff','trade war','us sanction','white house','executive order',
              'biden','us president','pentagon','washington','us economy','us trade',
              'us policy','us market','american'],
             'US decisions move global money flows. Tariffs or sanctions ripple into Saudi.'),
            ('FED & RATES', '#a78bfa',
             ['fed ','federal reserve','powell','interest rate','rate cut','rate hike',
              'inflation','monetary','central bank','quantitative','gdp','recession'],
             'Interest rate decisions globally redirect investment money into or out of markets like Saudi.'),
            ('SAUDI DIRECT', '#4A9EFF',
             ['saudi','aramco','tasi','vision 2030','riyadh','mbs','sabic','maaden',
              'neom','kingdom','dirham','alrajhi','snb','riyad bank','saudi economy'],
             'This directly impacts Saudi companies and investor confidence on Tadawul.'),
            ('GLOBAL MARKET', '#10a37f',
             ['market crash','stock market','sell-off','rally','global economy','imf',
              'world bank','china economy','emerging market','commodity','volatility',
              'risk-off','risk off','capital flow'],
             'Global market moves trigger international investors to move money in or out of Saudi.'),
        ]

        _filtered_news = []
        for _nh in (_news or []):
            _ttl_lower = _nh['title'].lower()
            for _cat_label, _cat_col, _cat_kws, _cat_why in _NEWS_CATS:
                if any(_kw in _ttl_lower for _kw in _cat_kws):
                    _filtered_news.append({**_nh, '_cat': _cat_label, '_col': _cat_col, '_why': _cat_why})
                    break   # one category per headline

        # sort: GEOPOLITICAL and OIL first, then others
        _cat_priority = {'GEOPOLITICAL': 0, 'OIL & ENERGY': 1, 'TRUMP / US': 2,
                         'FED & RATES': 3, 'SAUDI DIRECT': 4, 'GLOBAL MARKET': 5}
        _filtered_news.sort(key=lambda x: _cat_priority.get(x['_cat'], 9))

        _news_html = ""
        for _nh in _filtered_news[:7]:
            _nsc  = _nh['_col']
            _ndt  = _nh.get('date', '')[:10]
            _news_html += (
                f'<a href="{_nh["link"]}" target="_blank" style="text-decoration:none;display:block;">'
                f'<div style="border-left:3px solid {_nsc};background:{_nsc}08;'
                f'border-radius:0 8px 8px 0;padding:0.75rem 0.9rem;margin-bottom:0.55rem;">'
                # row 1: category badge + date + read arrow
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.35rem;">'
                f'<span style="font-size:0.66rem;font-weight:900;text-transform:uppercase;'
                f'letter-spacing:0.6px;padding:0.18rem 0.6rem;border-radius:4px;'
                f'background:{_nsc}22;color:{_nsc};flex-shrink:0;">{_nh["_cat"]}</span>'
                f'<span style="font-size:0.68rem;color:#383838;">{_ndt}</span>'
                f'<span style="margin-left:auto;font-size:0.7rem;color:{_nsc};'
                f'font-weight:800;flex-shrink:0;">READ &rarr;</span>'
                f'</div>'
                # row 2: headline
                f'<div style="font-size:0.9rem;color:#e0e0e0;line-height:1.55;'
                f'font-weight:600;margin-bottom:0.35rem;">{_nh["title"]}</div>'
                # row 3: why it matters
                f'<div style="font-size:0.74rem;color:#585858;line-height:1.5;">'
                f'WHY IT MATTERS &rarr; {_nh["_why"]}</div>'
                f'</div></a>'
            )

        if not _news_html:
            _news_html = (
                f'<div style="background:#1a1a1a;border-radius:10px;padding:1.2rem;'
                f'text-align:center;">'
                f'<div style="font-size:0.95rem;font-weight:700;color:#555;'
                f'margin-bottom:0.4rem;">No Major Alerts Right Now</div>'
                f'<div style="font-size:0.8rem;color:#3a3a3a;line-height:1.6;">'
                f'No geopolitical events, oil shocks, or major policy news detected. '
                f'This is actually a good sign — calm news = stable markets.</div>'
                f'</div>'
            )

        st.markdown(
            # ── outer container ──
            f'<div style="border:1px solid #222;border-left:4px solid {_mcolor};'
            f'border-radius:14px;background:#141414;padding:1.6rem 1.8rem;'
            f'margin-bottom:1.2rem;box-shadow:0 6px 40px #00000060;">'

            # ══ HEADER ROW ══
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'flex-wrap:wrap;gap:0.8rem;margin-bottom:1.5rem;">'
            f'<div>'
            f'<div style="font-size:1.5rem;font-weight:900;color:#f2f2f2;'
            f'letter-spacing:-0.5px;line-height:1.1;margin-bottom:0.45rem;">'
            f'Market Scan Results</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:0.55rem;align-items:center;">'
            f'<span style="font-size:0.77rem;color:#444;">{scanned} tickers &middot; {_period_disp}</span>'
            f'<span style="background:#FFD70012;color:#FFD700;border:1px solid #FFD70028;'
            f'font-size:0.77rem;font-weight:800;padding:0.2rem 0.7rem;border-radius:6px;">'
            f'{len(_perfect_list)} Perfect Setups</span>'
            f'<span style="background:#10a37f12;color:#10a37f;border:1px solid #10a37f28;'
            f'font-size:0.77rem;font-weight:800;padding:0.2rem 0.7rem;border-radius:6px;">'
            f'{len(all_buy)} Buy Signals</span>'
            f'</div></div>'
            f'<div style="text-align:center;">'
            f'<div style="background:{_mcolor}18;color:{_mcolor};border:1px solid {_mcolor}35;'
            f'font-size:0.84rem;font-weight:900;padding:0.45rem 1.3rem;border-radius:20px;'
            f'white-space:nowrap;letter-spacing:0.3px;margin-bottom:0.3rem;">{_mlabel}</div>'
            f'<div style="font-size:0.64rem;color:#303030;font-weight:700;">'
            f'Score {_mscore:+d} / 10</div>'
            f'</div>'
            f'</div>'

            # ══ MARKET CONDITIONS SCORE ══
            f'<div style="background:#191919;border:1px solid #202020;border-radius:12px;'
            f'padding:1.1rem 1.3rem;margin-bottom:1.3rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'margin-bottom:0.7rem;">'
            f'<span style="font-size:0.7rem;color:#3c3c3c;font-weight:800;'
            f'text-transform:uppercase;letter-spacing:1px;">Market Conditions Today</span>'
            f'<span style="font-size:0.95rem;font-weight:900;color:{_zone_col};">'
            f'{_zone_label}</span>'
            f'</div>'
            # bar + live position dot
            f'<div style="position:relative;height:18px;margin-bottom:0.55rem;">'
            f'<div style="position:absolute;top:4px;left:0;right:0;height:10px;'
            f'background:#1e1e1e;border-radius:8px;overflow:hidden;">'
            f'<div style="height:100%;width:{_bar_pct}%;border-radius:8px;'
            f'background:linear-gradient(90deg,#ef4444,#f97316,#fbbf24,#4A9EFF,#10a37f);"></div>'
            f'</div>'
            f'<div style="position:absolute;top:0;left:clamp(8px,{_bar_pct}%,calc(100% - 8px));'
            f'transform:translateX(-50%);width:18px;height:18px;border-radius:50%;'
            f'background:{_zone_col};border:3px solid #191919;'
            f'box-shadow:0 0 12px {_zone_col}bb;z-index:2;"></div>'
            f'</div>'
            # zone labels
            f'<div style="display:grid;grid-template-columns:repeat(5,1fr);text-align:center;">'
            f'<span style="font-size:0.6rem;color:#ef4444;font-weight:700;">STAY OUT</span>'
            f'<span style="font-size:0.6rem;color:#f97316;font-weight:700;">BE CAREFUL</span>'
            f'<span style="font-size:0.6rem;color:#fbbf24;font-weight:700;">NEUTRAL</span>'
            f'<span style="font-size:0.6rem;color:#4A9EFF;font-weight:700;">GOOD TIME</span>'
            f'<span style="font-size:0.6rem;color:#10a37f;font-weight:700;">IDEAL</span>'
            f'</div>'
            f'</div>'

            # ══ INSTRUMENT GRID ══
            f'<div style="display:flex;gap:0.5rem;flex-wrap:wrap;">'
            f'{_inst_html}'
            f'</div>'

            f'</div>',  # end outer box
            unsafe_allow_html=True,
        )


        # ── Sort (always by priority score, no user control needed) ─────────
        def _sorted(lst):
            return sorted(lst, key=lambda x: x.get('priority_score', 0), reverse=True)

        # ── Card renderer — full Perfect-Setup style, shared by both tabs ────
        _SETUP_BADGE_COLORS = {
            'Golden Cross':       ('#fbbf24', '#2a2410'),
            'Oversold Reversal':  ('#60a5fa', '#101828'),
            'BB Bounce':          ('#a78bfa', '#1a1228'),
            '52W Breakout':       ('#10a37f', '#0a1f1a'),
            'Deep Value':         ('#f97316', '#1f1208'),
            'Trend Continuation': ('#34d399', '#0a1f14'),
            'Stoch Reversal':     ('#e879f9', '#1f0a22'),
            'Volume Spike':       ('#fb923c', '#1f1008'),
        }
        _SETUP_LABELS = {
            'Golden Cross': 'Moving averages crossed up — bullish trend starting',
            'Death Cross': 'Trend weakening',
            'Oversold Reversal': 'Price was oversold — bounce expected',
            'BB Bounce': 'Hit lower Bollinger Band — bounce expected',
            '52W Breakout': 'Breaking above 52-week high — strong momentum',
            'Deep Value': 'Deeply undervalued — potential recovery',
            'Trend Continuation': 'Strong uptrend still going',
            'Stoch Reversal': 'Stochastic oversold — reversal expected',
            'Volume Spike': 'Unusual buying volume — big institutional interest',
        }

        def _render_card(stock, side, tier_color=None, rank_num=None):
            sym    = stock['ticker'].replace('.SR', '')
            name   = stock.get('name', sym)
            price  = stock['price']
            score  = stock.get('score', 0)
            entry  = stock.get('entry', price)
            stop   = stock.get('stop_loss', price)
            t1     = stock.get('target1', price)
            t2     = stock.get('target2', price)
            rr     = stock.get('rr_ratio', 0)
            conv   = stock.get('conviction', 50)
            setup  = stock.get('setup_type', '')
            raw_why = stock.get('why_reasons') or stock.get('signals', [])
            mtf    = stock.get('mtf_score', 0)
            sector = stock.get('sector', 'Other')

            ac = tier_color or {"buy": "#10a37f", "sell": "#ef4444", "hold": "#fbbf24"}.get(side, "#10a37f")
            sc_color = "#10a37f" if score >= 12 else ("#4A9EFF" if score >= 7 else "#fbbf24")
            cc_color = "#10a37f" if conv >= 70 else ("#4A9EFF" if conv >= 45 else "#fbbf24")

            dn_pct = (entry - stop) / entry * 100 if entry > 0 else 0
            up_pct = (t1   - entry) / entry * 100  if entry > 0 else 0
            t2_pct = (t2   - entry) / entry * 100  if entry > 0 else 0
            rr_val = (t1 - entry) / (entry - stop)  if (entry - stop) > 0 else rr

            # ── Per-stock market context ─────────────────────────────────────
            # Determine which macro signals and news categories matter for this stock
            _name_lower = name.lower()
            _sym_lower  = sym.lower()

            # Sector → primary macro drivers
            # Each entry: (news_cats_to_show, macro_snapshot_keys, sector_label, sector_color)
            _SEC_PROFILE = {
                'Banks': {
                    'label': 'Banks & Finance', 'color': '#4A9EFF',
                    'news_cats': ('FED & RATES', 'SAUDI DIRECT', 'TRUMP / US', 'GLOBAL MARKET'),
                    'snap_keys': ('vix',),
                    'why': 'Banks profit from interest rates and credit demand. Rate cuts squeeze margins; market panic dries up lending.',
                },
                'Petrochemicals': {
                    'label': 'Petrochemicals', 'color': '#f97316',
                    'news_cats': ('OIL & ENERGY', 'GEOPOLITICAL', 'TRUMP / US'),
                    'snap_keys': ('brent', 'gas'),
                    'why': 'Feedstock costs track oil and gas prices directly. Geopolitical disruption hits supply chains.',
                },
                'Utilities': {
                    'label': 'Utilities', 'color': '#a78bfa',
                    'news_cats': ('OIL & ENERGY', 'SAUDI DIRECT', 'FED & RATES'),
                    'snap_keys': ('brent',),
                    'why': 'Regulated revenue but fuel costs track oil/gas. Rate changes affect project financing costs.',
                },
                'Telecom & Tech': {
                    'label': 'Telecom & Tech', 'color': '#60a5fa',
                    'news_cats': ('FED & RATES', 'GLOBAL MARKET', 'TRUMP / US'),
                    'snap_keys': ('vix', 'sp500'),
                    'why': 'Growth stocks are rate-sensitive. Global risk-off hurts tech valuations rapidly.',
                },
                'Insurance': {
                    'label': 'Insurance', 'color': '#34d399',
                    'news_cats': ('FED & RATES', 'SAUDI DIRECT', 'GEOPOLITICAL'),
                    'snap_keys': ('vix',),
                    'why': 'Investment returns tie to interest rates. Geopolitical shocks can spike claims.',
                },
                'Cement': {
                    'label': 'Cement', 'color': '#fbbf24',
                    'news_cats': ('SAUDI DIRECT', 'OIL & ENERGY'),
                    'snap_keys': ('brent',),
                    'why': 'Cement demand driven by Saudi government spending, which depends on oil revenue.',
                },
                'Food & Agri': {
                    'label': 'Food & Agriculture', 'color': '#10a37f',
                    'news_cats': ('GEOPOLITICAL', 'SAUDI DIRECT', 'TRUMP / US'),
                    'snap_keys': ('usd',),
                    'why': 'Import-dependent. Trade wars and USD strength directly raise input costs.',
                },
                'REITs': {
                    'label': 'REITs', 'color': '#e879f9',
                    'news_cats': ('FED & RATES', 'SAUDI DIRECT'),
                    'snap_keys': ('usd', 'vix'),
                    'why': 'Real estate investment trusts are highly rate-sensitive. Higher rates reduce valuations and distribution yields.',
                },
                'Retail': {
                    'label': 'Retail', 'color': '#fb923c',
                    'news_cats': ('SAUDI DIRECT', 'GLOBAL MARKET', 'TRUMP / US'),
                    'snap_keys': ('vix',),
                    'why': 'Consumer spending tracks Saudi income levels, which are tied to oil revenue and government salaries.',
                },
                'Healthcare': {
                    'label': 'Healthcare', 'color': '#38bdf8',
                    'news_cats': ('SAUDI DIRECT', 'FED & RATES'),
                    'snap_keys': ('vix',),
                    'why': 'Defensive sector. Less oil-sensitive but affected by government healthcare contracts and Vision 2030 spending.',
                },
                'Transport': {
                    'label': 'Transport', 'color': '#94a3b8',
                    'news_cats': ('OIL & ENERGY', 'GEOPOLITICAL', 'SAUDI DIRECT'),
                    'snap_keys': ('brent',),
                    'why': 'Fuel costs are the biggest expense. Oil spikes squeeze margins; geopolitical conflicts disrupt routes.',
                },
                'Real Estate': {
                    'label': 'Real Estate', 'color': '#e879f9',
                    'news_cats': ('FED & RATES', 'SAUDI DIRECT'),
                    'snap_keys': ('usd', 'vix'),
                    'why': 'Rate-sensitive sector. Vision 2030 projects drive demand; foreign capital flows track USD and global risk.',
                },
            }

            # Auto-detect oil/energy exposure by ticker/name even outside Petrochemicals
            _is_oil_linked = (
                sector in ('Petrochemicals',)
                or any(kw in _name_lower for kw in ('aramco', 'oil', 'petro', 'chemical', 'refin', 'gas', 'energy'))
                or any(kw in _sym_lower  for kw in ('2222', 'petro', 'sahara', 'yanbu', 'jubail'))
            )
            _is_bank = (
                sector == 'Banks'
                or any(kw in _name_lower for kw in ('bank', 'riyad', 'rajhi', 'snb', 'alinma', 'alawwal', 'bsf', 'anb'))
            )

            _sprof = _SEC_PROFILE.get(sector, {
                'label': sector or 'General', 'color': '#888',
                'news_cats': ('GEOPOLITICAL', 'OIL & ENERGY', 'SAUDI DIRECT', 'TRUMP / US', 'FED & RATES'),
                'snap_keys': ('brent', 'vix'),
                'why': 'Saudi stocks broadly track oil revenue and global market sentiment.',
            })

            # Override for oil-linked stocks in non-petrochem sectors
            if _is_oil_linked and sector not in ('Petrochemicals',):
                _sprof = _SEC_PROFILE['Petrochemicals']

            _ctx_stock = []   # (label, color, text) rows for this card

            # 1. Oil price vs breakeven — if oil-relevant
            if _is_oil_linked or 'brent' in _sprof['snap_keys']:
                _bs = (_msnap or {}).get('brent')
                if _bs:
                    try:
                        from macro_data import _SAUDI_OIL_BREAKEVEN
                        _op = _bs['price']; _oc5 = _bs['chg_5d']
                        _gap = _op - _SAUDI_OIL_BREAKEVEN
                        _os  = ('+' if _oc5 >= 0 else '') + f'{_oc5:.1f}%'
                        _oil_metric = f'${_op:.1f}  {_os}'
                        if _op < _SAUDI_OIL_BREAKEVEN - 10:
                            _ctx_stock.append(("OIL CRITICAL", "#ef4444",
                                f"Brent ${_op:.1f} — ${abs(_gap):.0f} below the ${_SAUDI_OIL_BREAKEVEN:.0f} Saudi budget breakeven ({_os} this week). "
                                f"{'Aramco dividends and Saudi revenues are under severe pressure. Direct risk to stock.' if _is_oil_linked else 'Government spending cuts likely — sector contract flow at risk.'}",
                                'bear', _oil_metric))
                        elif _op < _SAUDI_OIL_BREAKEVEN:
                            _ctx_stock.append(("OIL BELOW BREAKEVEN", "#f97316",
                                f"Brent ${_op:.1f} ({_os} this week), ${abs(_gap):.0f} below budget breakeven. "
                                f"{'Oil-linked product pricing under pressure — watch margins closely.' if _is_oil_linked else 'Fiscal pressure building — watch for delayed government contracts.'}",
                                'watch', _oil_metric))
                        elif _oc5 > 2:
                            _ctx_stock.append(("OIL TAILWIND", "#10a37f",
                                f"Brent ${_op:.1f}, up {_os} this week — ${_gap:.0f} above Saudi breakeven. "
                                f"{'Strong feedstock cost environment. Aramco dividends and sector revenue supported.' if _is_oil_linked else 'Rising oil strengthens Saudi fiscal position — positive backdrop for government-linked spending.'}",
                                'bull', _oil_metric))
                        elif _oc5 < -3:
                            _ctx_stock.append(("OIL DECLINING", "#f97316",
                                f"Brent ${_op:.1f}, down {_os} this week. "
                                f"{'Product pricing may compress even as feedstock drops — net margin impact uncertain.' if sector == 'Petrochemicals' else 'Weakening oil signals Saudi revenue headwind — monitor closely.'}",
                                'watch', _oil_metric))
                    except Exception:
                        pass

            # 2. VIX — global fear gauge
            if 'vix' in _sprof['snap_keys'] or _is_bank:
                _vs = (_msnap or {}).get('vix')
                if _vs:
                    _vp = _vs['price']
                    _vix_metric = f'VIX {_vp:.0f}'
                    if _vp > 35:
                        _ctx_stock.append(("EXTREME FEAR", "#ef4444",
                            f"VIX at {_vp:.0f} — panic-level volatility. Foreign capital is exiting emerging markets aggressively. "
                            f"{'Credit demand collapses in crises — loan growth stalls, default risk rises.' if _is_bank else 'International investors are unwinding Saudi positions to cover losses elsewhere. Risk is elevated.'}",
                            'bear', _vix_metric))
                    elif _vp > 25:
                        _ctx_stock.append(("ELEVATED FEAR", "#f97316",
                            f"VIX at {_vp:.0f} — markets anxious. Risk-off flows can hit Tadawul as foreign money retreats. "
                            f"{'Banks face wider credit spreads and tighter lending conditions.' if _is_bank else 'Reduce position sizing — volatility makes entries less reliable.'}",
                            'watch', _vix_metric))
                    elif _vp < 16:
                        _ctx_stock.append(("LOW VOLATILITY", "#10a37f",
                            f"VIX at {_vp:.0f} — market calm. Risk appetite is healthy, capital flows are supportive. "
                            f"{'Banks can grow loan books freely; appetite for credit is strong.' if _is_bank else 'Good conditions for momentum trades — low fear means fewer sudden reversals.'}",
                            'bull', _vix_metric))

            # 3. Interest rates
            if 'FED & RATES' in _sprof['news_cats']:
                _rate_metric = f'Macro {_mscore:+d}'
                if _mscore <= -3:
                    _ctx_stock.append(("RATE HEADWIND", "#f97316",
                        f"Rate macro score {_mscore}/10 — conditions are a headwind. "
                        f"{'Higher-for-longer rates compress net interest margins on new loans.' if _is_bank else 'Elevated rates raise financing costs and pressure growth valuations in this sector.'}",
                        'watch', _rate_metric))
                elif _mscore >= 5:
                    _ctx_stock.append(("RATES EASING", "#10a37f",
                        f"Rate macro score {_mscore}/10 — easing conditions are a tailwind. "
                        f"{'Lower rates stimulate credit demand and expand bank margins.' if _is_bank else 'Falling rates reduce sector financing costs and lift asset valuations.'}",
                        'bull', _rate_metric))

            # 4. Relevant news headlines
            _news_for_stock = [n for n in _filtered_news if n.get('_cat') in _sprof['news_cats']]
            for _ni, _nn in enumerate(_news_for_stock[:2]):
                _ncat = _nn['_cat']
                _nwhy = {
                    'OIL & ENERGY':   f"Oil moves directly affect {'revenues and feedstock costs' if _is_oil_linked else 'Saudi government spending and market sentiment'}.",
                    'GEOPOLITICAL':   "Middle East tensions can disrupt supply routes and trigger rapid selling on Tadawul.",
                    'TRUMP / US':     "US trade and sanctions policy redirects global capital — Saudi assets included.",
                    'FED & RATES':    f"{'Fed decisions hit bank lending margins directly.' if _is_bank else 'Rate moves shift global capital allocation — Saudi included.'}",
                    'SAUDI DIRECT':   "This directly involves Saudi policy or companies in your sector.",
                    'GLOBAL MARKET':  "Global risk-off events pull foreign investors out of emerging markets like Saudi Arabia.",
                }.get(_ncat, "This event may affect your trade.")
                _ctx_stock.append((_ncat, _nn['_col'],
                    f"{_nn['title']} — {_nwhy}",
                    'news', ''))

            # 5. Fallback
            if not _ctx_stock:
                _ctx_stock.append(("NO ACTIVE ALERTS", "#484848",
                    f"No major macro events flagged for {_sprof['label']} right now. "
                    f"{_sprof['why']}",
                    'neutral', ''))

            # ── Context HTML builder ──────────────────────────────────────
            _CTX_ICONS = {
                'bull':    ('&#9650;', '#10a37f'),   # ▲
                'bear':    ('&#9660;', '#ef4444'),   # ▼
                'watch':   ('&#9670;', '#f97316'),   # ◆
                'neutral': ('&#9679;', '#484848'),   # ●
                'news':    ('&#8594;', None),        # →  (uses item color)
            }
            def _ctx_item_html(entry):
                _cl, _cc, _ct = entry[0], entry[1], entry[2]
                _imp = entry[3] if len(entry) > 3 else 'neutral'
                _met = entry[4] if len(entry) > 4 else ''
                _icon_char, _icon_col = _CTX_ICONS.get(_imp, ('&#9679;', _cc))
                _ic = _icon_col if _icon_col else _cc
                _metric_html = (
                    f'<span style="font-size:0.65rem;font-weight:800;color:{_cc};'
                    f'background:{_cc}18;padding:0.1rem 0.45rem;border-radius:4px;'
                    f'font-family:monospace;white-space:nowrap;letter-spacing:0.3px;">{_met}</span>'
                    if _met else ''
                )
                return (
                    f'<div style="border-radius:8px;border:1px solid {_cc}20;'
                    f'background:{_cc}0a;padding:0.6rem 0.8rem;margin-bottom:0.45rem;'
                    f'border-left:3px solid {_cc};">'
                    f'<div style="display:flex;align-items:center;'
                    f'justify-content:space-between;margin-bottom:0.3rem;">'
                    f'<div style="display:flex;align-items:center;gap:0.35rem;">'
                    f'<span style="font-size:0.65rem;font-weight:900;color:{_ic};line-height:1;">{_icon_char}</span>'
                    f'<span style="font-size:0.58rem;font-weight:900;letter-spacing:1.2px;'
                    f'color:{_cc};text-transform:uppercase;">{_cl}</span>'
                    f'</div>'
                    f'{_metric_html}'
                    f'</div>'
                    f'<div style="font-size:0.88rem;color:#b8b8b8;line-height:1.6;'
                    f'padding-left:1.1rem;">{_ct}</div>'
                    f'</div>'
                )
            _stock_ctx_html = "".join(_ctx_item_html(e) for e in _ctx_stock)

            dn_pct = (entry - stop) / entry * 100 if entry > 0 else 0
            up_pct = (t1   - entry) / entry * 100  if entry > 0 else 0
            t2_pct = (t2   - entry) / entry * 100  if entry > 0 else 0
            rr_val = (t1 - entry) / (entry - stop)  if (entry - stop) > 0 else rr

            # MTF badge
            # MTF = Multi-Timeframe alignment (how many timeframes agree: Daily, Weekly, Monthly)
            if mtf == 3:
                mtf_badge = ('<span style="font-size:0.67rem;font-weight:700;background:#4caf5018;'
                             'color:#4caf50;border-radius:4px;padding:3px 8px;'
                             'border:1px solid #4caf5040;white-space:nowrap;'
                             'title="All 3 timeframes (daily, weekly, monthly) agree — strongest signal">'
                             '&#10003; All Timeframes Agree</span>')
            elif mtf == 2:
                mtf_badge = ('<span style="font-size:0.67rem;font-weight:700;background:#ff980018;'
                             'color:#ff9800;border-radius:4px;padding:3px 8px;'
                             'border:1px solid #ff980040;white-space:nowrap;'
                             'title="2 of 3 timeframes agree">'
                             '2 of 3 Timeframes Agree</span>')
            elif mtf == 1:
                mtf_badge = ('<span style="font-size:0.67rem;font-weight:700;background:#88888818;'
                             'color:#888;border-radius:4px;padding:3px 8px;'
                             'border:1px solid #88888835;white-space:nowrap;'
                             'title="Only 1 timeframe agrees — weaker signal">'
                             '1 of 3 Timeframes</span>')
            else:
                mtf_badge = ''

            # ── Setup badge ──────────────────────────────────────────────
            _sb_color, _sb_bg = _SETUP_BADGE_COLORS.get(setup, ('#10a37f', '#10a37f18'))

            # ── Sector label ─────────────────────────────────────────────
            _sprof_label = _sprof.get('label', sector) if sector and sector not in ('', 'Other') else ''

            # ── Why bullets ──────────────────────────────────────────────
            bullets = [_clean_why(r) for r in raw_why[:5] if r]
            if not bullets and setup:
                bullets = [_SETUP_LABELS.get(setup, setup)]
            bullet_html = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:0.6rem;padding:0.38rem 0;'
                f'border-bottom:1px solid rgba(255,255,255,0.04);">'
                f'<span style="color:#10a37f;font-size:0.82rem;line-height:1.4;flex-shrink:0;">&#10003;</span>'
                f'<span style="font-size:0.92rem;color:#d0d0d0;line-height:1.55;">{b}</span>'
                f'</div>'
                for b in bullets
            ) if bullets else '<span style="color:#484848;font-size:0.82rem;">No specific signals recorded</span>'

            # ── Score / confidence colors ─────────────────────────────────
            _sc2 = '#10a37f' if score >= 12 else ('#4A9EFF' if score >= 7 else '#fbbf24')
            _cc2 = '#10a37f' if conv >= 70 else ('#4A9EFF' if conv >= 45 else '#fbbf24')

            # ── MTF badge data ─────────────────────────────────────────
            if mtf == 3:
                _mtf_color, _mtf_label = '#4caf50', 'All timeframes agree'
            elif mtf == 2:
                _mtf_color, _mtf_label = '#ff9800', '2 of 3 timeframes'
            elif mtf == 1:
                _mtf_color, _mtf_label = '#666666', '1 of 3 timeframes'
            else:
                _mtf_color, _mtf_label = '', ''
            _mtf_txt = _mtf_label  # kept for any legacy references

            # ── Rank number (big, for Perfect Setups only) ────────────────
            _rank_html = (
                f'<div style="font-size:0.6rem;font-weight:800;color:#444;'
                f'letter-spacing:2px;text-transform:uppercase;margin-bottom:0.1rem;">RANK</div>'
                f'<div style="font-size:2rem;font-weight:900;color:#10a37f;'
                f'line-height:1;">{rank_num}</div>'
            ) if rank_num else ''

            # ── Render card ──────────────────────────────────────────────
            st.markdown(
                f'<div style="border:1px solid #242424;border-top:3px solid {ac};'
                f'border-radius:14px;background:#181818;margin-bottom:1.6rem;overflow:hidden;">'

                # ╔══ HEADER ═════════════════════════════════════════════╗
                f'<div style="display:flex;align-items:stretch;background:#1e1e1e;">'

                # LEFT — rank column (only for Perfect Setups)
                + (
                    f'<div style="display:flex;flex-direction:column;align-items:center;'
                    f'justify-content:center;padding:1.4rem 1.1rem;'
                    f'border-right:1px solid #262626;min-width:4.5rem;text-align:center;'
                    f'background:#ffffff03;">'
                    f'<div style="font-size:0.48rem;font-weight:800;color:#383838;'
                    f'letter-spacing:2.5px;text-transform:uppercase;margin-bottom:0.2rem;">RANK</div>'
                    f'<div style="font-size:2rem;font-weight:900;color:#10a37f;line-height:1;">{rank_num}</div>'
                    f'</div>'
                    if rank_num else
                    f'<div style="width:0;"></div>'
                ) +

                # MAIN — all content
                f'<div style="flex:1;padding:1.3rem 1.5rem 1.2rem;'
                f'display:flex;flex-direction:column;gap:0;min-width:0;">'

                # ── Main row: LEFT (ticker+name / pills) ── RIGHT (3 boxes) ─
                f'<div style="display:flex;align-items:stretch;gap:1rem;">'

                # LEFT — ticker·name on top, pills below
                f'<div style="flex:1;display:flex;flex-direction:column;'
                f'justify-content:space-between;gap:0.55rem;min-width:0;">'

                # ticker · name
                f'<div style="display:flex;align-items:center;gap:0.45rem;min-width:0;">'
                f'<span style="font-size:1.3rem;font-weight:900;color:#ffffff;'
                f'letter-spacing:-0.2px;line-height:1;white-space:nowrap;">{sym}</span>'
                f'<span style="color:#2a2a2a;font-size:0.9rem;flex-shrink:0;">&#8231;</span>'
                f'<span style="font-size:1.3rem;font-weight:400;color:#7a7a7a;'
                f'line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
                f'min-width:0;">{name}</span>'
                f'</div>'

                # pills
                f'<div style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;">'
                + (
                    f'<span style="font-size:0.7rem;font-weight:700;'
                    f'padding:0.2rem 0.65rem;border-radius:5px;'
                    f'background:{_sb_bg};color:{_sb_color};'
                    f'border:1px solid {_sb_color}40;white-space:nowrap;">{setup}</span>'
                    if setup else ''
                ) + (
                    f'<span style="display:inline-flex;align-items:center;gap:0.3rem;'
                    f'font-size:0.7rem;font-weight:600;padding:0.2rem 0.65rem;border-radius:5px;'
                    f'background:{_mtf_color}14;color:{_mtf_color};'
                    f'border:1px solid {_mtf_color}38;white-space:nowrap;">'
                    f'<span style="font-size:0.45rem;line-height:1;">&#9679;</span>'
                    f'{_mtf_label}</span>'
                    if _mtf_label else ''
                ) + (
                    f'<span style="font-size:0.7rem;font-weight:500;'
                    f'padding:0.2rem 0.65rem;border-radius:5px;'
                    f'background:#1e1e1e;color:#545454;'
                    f'border:1px solid #2a2a2a;white-space:nowrap;">{_sprof_label}</span>'
                    if _sprof_label else ''
                ) +
                f'</div>'  # end pills

                f'</div>'  # end left col

                # RIGHT — 3 boxes, stretch to full row height
                f'<div style="display:flex;align-items:stretch;gap:0.4rem;flex-shrink:0;">'

                # Price box
                f'<div style="background:#ffffff08;border:1px solid #2a2a2a;'
                f'border-radius:8px;padding:0.6rem 1rem;text-align:right;min-width:5.5rem;'
                f'display:flex;flex-direction:column;justify-content:space-between;">'
                f'<div style="font-size:0.62rem;font-weight:700;color:#525252;'
                f'white-space:nowrap;margin-bottom:0.3rem;">Price · SAR</div>'
                f'<div style="font-size:1.4rem;font-weight:900;color:#e0e0e0;'
                f'line-height:1;letter-spacing:-0.5px;white-space:nowrap;">{price:.2f}</div>'
                f'</div>'

                # Score box
                f'<div style="background:{_sc2}0e;border:1px solid {_sc2}30;'
                f'border-radius:8px;padding:0.6rem 1rem;text-align:right;min-width:5.5rem;'
                f'display:flex;flex-direction:column;justify-content:space-between;">'
                f'<div style="font-size:0.62rem;font-weight:700;color:{_sc2}99;'
                f'white-space:nowrap;margin-bottom:0.3rem;">Signal Score</div>'
                f'<div style="font-size:1.4rem;font-weight:900;color:{_sc2};'
                f'line-height:1;white-space:nowrap;">'
                f'{score}<span style="font-size:0.75rem;color:{_sc2}66;font-weight:600;">/20</span>'
                f'</div>'
                f'</div>'

                # Confidence box
                f'<div style="background:{_cc2}0e;border:1px solid {_cc2}30;'
                f'border-radius:8px;padding:0.6rem 1rem;text-align:right;min-width:5.5rem;'
                f'display:flex;flex-direction:column;justify-content:space-between;">'
                f'<div style="font-size:0.62rem;font-weight:700;color:{_cc2}99;'
                f'white-space:nowrap;margin-bottom:0.3rem;">Confidence</div>'
                f'<div style="font-size:1.4rem;font-weight:900;color:{_cc2};'
                f'line-height:1;white-space:nowrap;">'
                f'{conv}<span style="font-size:0.75rem;color:{_cc2}66;font-weight:600;">%</span>'
                f'</div>'
                f'</div>'

                f'</div>'  # end right boxes
                f'</div>'  # end main row

                f'</div>'  # end main content

                f'</div>'  # end header flex
                # ╚══ END HEADER ═════════════════════════════════════════╝

                # ── PRICE LADDER ──
                f'<div style="background:#141414;border-top:1px solid #2a2a2a;border-bottom:1px solid #2a2a2a;'
                f'padding:1rem 1.5rem;">'
                f'<div style="font-size:0.72rem;color:#909090;text-transform:uppercase;letter-spacing:1.2px;'
                f'font-weight:800;margin-bottom:0.8rem;">Your Trading Plan</div>'
                f'<div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr auto 1fr;'
                f'align-items:center;width:100%;gap:0.3rem;">'

                f'<div style="text-align:center;background:#1e2a3a;border:1px solid #1e3a5f;'
                f'border-radius:10px;padding:0.75rem 0.5rem;">'
                f'<div style="font-size:1.15rem;font-weight:800;color:#4A9EFF;">{entry:.2f}</div>'
                f'<div style="font-size:0.7rem;color:#4A9EFF;margin-top:3px;font-weight:700;">ENTRY</div>'
                f'</div>'
                f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'
                f'<div style="text-align:center;background:#2a1a1a;border:1px solid #5f1e1e;'
                f'border-radius:10px;padding:0.75rem 0.5rem;">'
                f'<div style="font-size:1.15rem;font-weight:800;color:#ef4444;">{stop:.2f}</div>'
                f'<div style="font-size:0.7rem;color:#ef4444;margin-top:3px;font-weight:700;">STOP &nbsp;−{dn_pct:.1f}%</div>'
                f'</div>'
                f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'
                f'<div style="text-align:center;background:#1a2a1e;border:1px solid #1e5f2a;'
                f'border-radius:10px;padding:0.75rem 0.5rem;">'
                f'<div style="font-size:1.15rem;font-weight:800;color:#10a37f;">{t1:.2f}</div>'
                f'<div style="font-size:0.7rem;color:#10a37f;margin-top:3px;font-weight:700;">TARGET 1 &nbsp;+{up_pct:.1f}%</div>'
                f'</div>'
                f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'
                f'<div style="text-align:center;background:#1a2a28;border:1px solid #1e4f4a;'
                f'border-radius:10px;padding:0.75rem 0.5rem;">'
                f'<div style="font-size:1.15rem;font-weight:800;color:#26A69A;">{t2:.2f}</div>'
                f'<div style="font-size:0.7rem;color:#26A69A;margin-top:3px;font-weight:700;">TARGET 2 &nbsp;+{t2_pct:.1f}%</div>'
                f'</div>'
                f'<div style="text-align:center;color:#444;font-size:1.3rem;padding:0 0.2rem;">›</div>'
                f'<div style="text-align:center;background:#2a2410;border:1px solid #5f5010;'
                f'border-radius:10px;padding:0.75rem 0.5rem;">'
                f'<div style="font-size:1.35rem;font-weight:900;color:#fbbf24;">1 : {rr_val:.1f}</div>'
                f'<div style="font-size:0.7rem;color:#888;margin-top:3px;font-weight:700;">RISK / REWARD</div>'
                f'</div>'

                f'</div>'
                f'</div>'

                # ── 2-COL BOTTOM: WHY + MARKET CONTEXT ──
                f'<div style="display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #222;">'
                f'<div style="padding:1.1rem 1.4rem;border-right:1px solid #1e1e1e;">'
                f'<div style="font-size:0.7rem;color:#707070;font-weight:900;text-transform:uppercase;'
                f'letter-spacing:1.2px;margin-bottom:0.65rem;padding-bottom:0.32rem;'
                f'border-bottom:1px solid #222;">WHY THIS STOCK?</div>'
                + bullet_html +
                f'</div>'
                f'<div style="padding:1.1rem 1.3rem 1.2rem;background:#0d0d0d;">'
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'margin-bottom:0.7rem;padding-bottom:0.4rem;border-bottom:1px solid #1e1e1e;">'
                f'<span style="font-size:0.7rem;color:#606060;font-weight:900;'
                f'text-transform:uppercase;letter-spacing:1.5px;">Market Context</span>'
                f'<span style="font-size:0.58rem;font-weight:700;'
                f'color:{_sprof.get("color","#888")};'
                f'background:{_sprof.get("color","#888")}18;'
                f'padding:0.12rem 0.55rem;border-radius:4px;'
                f'border:1px solid {_sprof.get("color","#888")}35;'
                f'white-space:nowrap;">{_sprof.get("label", sector or "General")}</span>'
                f'</div>'
                + _stock_ctx_html +
                f'</div>'
                f'</div>'

                f'</div>',
                unsafe_allow_html=True,
            )

        # ── Classify stocks ───────────────────────────────────────────────────
        # all_buy already computed above for hero tiles

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
             if s.get('score', 0) >= 4
             and s.get('rr_ratio', 0) >= 1.8
             and s.get('conviction', 0) >= 45],
            key=_best_picks_score, reverse=True)

        _srch = ""

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

        # Shared helpers — used by both Perfect Setups and Buy Signals cards
        import re as _re
        def _clean_why(reason):
            r = _re.sub(r'\s*\[.*?\]', '', reason)
            if ' \u2014 ' in r:   r = r.split(' \u2014 ', 1)[1]
            elif ' - ' in r and len(r.split(' - ', 1)[1]) > 15: r = r.split(' - ', 1)[1]
            r = _re.sub(r'\s*\([^)]{1,6}\)', '', r)
            r = _re.sub(r'^Regime:\s*', '', r)
            return r.strip().rstrip('.')

        # Market context rows — built once, shared across all cards
        _brent_snap = (_msnap or {}).get('brent')
        _vix_snap   = (_msnap or {}).get('vix')
        _oil_p  = _brent_snap['price']  if _brent_snap else None
        _vix_p  = _vix_snap['price']    if _vix_snap  else None
        _oil_c5 = _brent_snap['chg_5d'] if _brent_snap else 0
        _ctx_rows = []
        if _mscore <= -5:
            _ctx_rows.append(("DANGER ZONE", "#ef4444",
                f"Markets are in extreme distress (score {_mscore}/10). "
                f"Even strong technical setups are failing right now. Consider staying out."))
        elif _mscore <= -2:
            _ctx_rows.append(("CAUTION", "#f97316",
                f"Market headwinds are active (score {_mscore}/10). "
                f"Use half your normal position size and keep stops tight."))
        elif _mscore >= 6:
            _ctx_rows.append(("IDEAL CONDITIONS", "#10a37f",
                f"Strong tailwinds — oil healthy, markets calm, money flowing into Saudi. "
                f"Good time to run full-size positions on quality setups."))
        if _oil_p is not None:
            from macro_data import _SAUDI_OIL_BREAKEVEN
            _gap = _oil_p - _SAUDI_OIL_BREAKEVEN
            _oil_s = ('+' if _oil_c5 >= 0 else '') + f'{_oil_c5:.1f}%'
            if _oil_p < _SAUDI_OIL_BREAKEVEN - 10:
                _ctx_rows.append(("OIL CRITICAL", "#ef4444",
                    f"Brent at ${_oil_p:.1f} — ${abs(_gap):.0f} BELOW Saudi budget breakeven (${_SAUDI_OIL_BREAKEVEN:.0f}). "
                    f"This week: {_oil_s}. Saudi govt revenue under serious pressure."))
            elif _oil_p < _SAUDI_OIL_BREAKEVEN:
                _ctx_rows.append(("OIL BELOW BREAKEVEN", "#f97316",
                    f"Brent at ${_oil_p:.1f} — ${abs(_gap):.0f} below Saudi budget breakeven (${_SAUDI_OIL_BREAKEVEN:.0f}). "
                    f"Fiscal pressure building — watch for market weakness."))
            elif _oil_p >= _SAUDI_OIL_BREAKEVEN and _oil_c5 > 3:
                _ctx_rows.append(("OIL SUPPORTIVE", "#10a37f",
                    f"Brent at ${_oil_p:.1f} — ${_gap:.0f} above budget breakeven. "
                    f"Rising {_oil_s} this week. Saudi revenues healthy."))
        if _vix_p is not None:
            if _vix_p > 35:
                _ctx_rows.append(("MARKET PANIC", "#ef4444",
                    f"VIX at {_vix_p:.0f} — panic territory. Foreign investors fleeing ALL emerging markets. "
                    f"Stocks can drop 10–20% in days during spikes like this."))
            elif _vix_p > 25:
                _ctx_rows.append(("HIGH FEAR", "#f97316",
                    f"VIX at {_vix_p:.0f} — above normal anxiety levels. "
                    f"Use smaller position sizes until VIX drops below 20."))
            elif _vix_p < 16:
                _ctx_rows.append(("MARKETS CALM", "#10a37f",
                    f"VIX at {_vix_p:.0f} — very low fear globally. Good for Saudi stocks."))
        _high_impact_cats = ('GEOPOLITICAL', 'OIL & ENERGY', 'TRUMP / US', 'FED & RATES')
        _card_news = [n for n in _filtered_news if n.get('_cat') in _high_impact_cats]
        for _cn in _card_news[:3]:
            _impact_why = {
                'GEOPOLITICAL': 'Conflict or sanctions can halt oil flows and trigger panic selling in Saudi.',
                'OIL & ENERGY': 'Oil news directly moves Saudi stocks — Aramco, banks & petrochemicals react first.',
                'TRUMP / US':   'US policy shifts redirect global capital flows into or out of markets like Saudi.',
                'FED & RATES':  'Rate decisions move investment money — lower rates = more money into EM.',
            }.get(_cn['_cat'], 'This event could affect your trade.')
            _ctx_rows.append((_cn['_cat'], _cn['_col'], f"{_cn['title']} — {_impact_why}"))
        _alert_rows_html = "".join(
            f'<div style="border-left:3px solid {_ac};background:{_ac}09;'
            f'border-radius:0 7px 7px 0;padding:0.55rem 0.75rem;margin-bottom:0.3rem;">'
            f'<div style="font-size:0.66rem;font-weight:900;text-transform:uppercase;'
            f'letter-spacing:0.7px;color:{_ac};margin-bottom:0.2rem;">{_at}</div>'
            f'<div style="font-size:0.8rem;color:#bbb;line-height:1.55;">{_ad}</div>'
            f'</div>'
            for _at, _ac, _ad in _ctx_rows
        ) if _ctx_rows else (
            '<div style="font-size:0.82rem;color:#484848;line-height:1.7;padding:0.4rem 0;">'
            'No major market alerts right now. Conditions appear neutral — normal position sizing applies.</div>'
        )

        tab_best, tab_buy = st.tabs([
            f"Perfect Setups  {len(_perfect_list)}",
            f"Buy Signals  {len(all_buy)}",
        ])

        with tab_best:
            if not _perfect_list:
                st.markdown(
                    "<div class='msr-empty'>"
                    "No stocks pass all quality gates right now — check Buy Signals for broader candidates."
                    "</div>",
                    unsafe_allow_html=True)
            else:
                _rank_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
                for _i, s in enumerate(_perfect_list):
                    _rc       = _rank_colors[_i] if _i < 3 else "#10a37f"
                    _rank_num = ["#1", "#2", "#3"][_i] if _i < 3 else f"#{_i+1}"
                    _render_card(s, 'buy', tier_color=_rc, rank_num=_rank_num)

        with tab_buy:
            filtered_buy = _f_all_buy
            if not filtered_buy:
                st.markdown(
                    "<div class='msr-empty'>No buy signals found — "
                    "the scanner requires Score ≥ 3, Conviction ≥ 25% and R:R ≥ 0.8×.<br>"
                    "Try a wider period or run a full market scan.</div>",
                    unsafe_allow_html=True)
            else:
                # ── 3-tier quality split ─────────────────────────────────────
                # Tier 1 — STRONG BUY: high conviction, great R:R, strong technicals
                _t1 = [s for s in filtered_buy
                       if s.get('score', 0) >= 7
                       and s.get('rr_ratio', 0) >= 1.5
                       and s.get('conviction', 0) >= 65]
                # Tier 2 — BUY: solid setup but not quite elite
                _t2 = [s for s in filtered_buy
                       if s not in _t1
                       and s.get('score', 0) >= 5
                       and s.get('rr_ratio', 0) >= 1.2
                       and s.get('conviction', 0) >= 40]
                # Tier 3 — WATCHLIST: passed basic gates, worth watching
                _t3 = [s for s in filtered_buy if s not in _t1 and s not in _t2]

                # ── Quality summary banner ───────────────────────────────────
                st.markdown(
                    f'<div style="background:#141414;border:1px solid #222;border-radius:10px;'
                    f'padding:0.85rem 1.2rem;margin-bottom:1rem;display:flex;'
                    f'flex-wrap:wrap;gap:1.5rem;align-items:center;">'
                    f'<div style="font-size:0.7rem;color:#505050;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:0.8px;">Quality Filter</div>'
                    # gates
                    f'<div style="display:flex;gap:0.9rem;flex-wrap:wrap;">'
                    f'<span style="font-size:0.74rem;color:#666;">Score ≥ 3</span>'
                    f'<span style="color:#282828;">|</span>'
                    f'<span style="font-size:0.74rem;color:#666;">Conviction ≥ 25%</span>'
                    f'<span style="color:#282828;">|</span>'
                    f'<span style="font-size:0.74rem;color:#666;">R:R ≥ 0.8×</span>'
                    f'</div>'
                    f'<div style="margin-left:auto;display:flex;gap:0.6rem;flex-shrink:0;">'
                    f'<span style="font-size:0.74rem;font-weight:800;padding:0.22rem 0.75rem;'
                    f'border-radius:6px;background:#10a37f18;color:#10a37f;border:1px solid #10a37f30;">'
                    f'Strong Buy {len(_t1)}</span>'
                    f'<span style="font-size:0.74rem;font-weight:800;padding:0.22rem 0.75rem;'
                    f'border-radius:6px;background:#4A9EFF18;color:#4A9EFF;border:1px solid #4A9EFF30;">'
                    f'Buy {len(_t2)}</span>'
                    f'<span style="font-size:0.74rem;font-weight:800;padding:0.22rem 0.75rem;'
                    f'border-radius:6px;background:#fbbf2418;color:#fbbf24;border:1px solid #fbbf2430;">'
                    f'Watchlist {len(_t3)}</span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # ── Tier 1: STRONG BUY ───────────────────────────────────────
                if _t1:
                    st.markdown(
                        f'<div class="msr-sec-row"><div class="msr-sec-dot buy"></div>'
                        f'<span class="msr-sec-title buy">STRONG BUY</span>'
                        f'<span style="font-size:0.68rem;color:#555;margin-left:0.3rem;">'
                        f'Score ≥ 7 · R:R ≥ 1.5× · Conviction ≥ 65%</span>'
                        f'<span class="msr-sec-count">{len(_t1)} stocks</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                    for s in _t1:
                        _render_card(s, 'buy', tier_color='#10a37f')

                # ── Tier 2: BUY ─────────────────────────────────────────────
                if _t2:
                    st.markdown(
                        f'<div class="msr-sec-row" style="border-left:3px solid #4A9EFF22;">'
                        f'<div class="msr-sec-dot" style="background:#4A9EFF;"></div>'
                        f'<span class="msr-sec-title" style="color:#4A9EFF;">BUY</span>'
                        f'<span style="font-size:0.68rem;color:#555;margin-left:0.3rem;">'
                        f'Score ≥ 5 · R:R ≥ 1.2× · Conviction ≥ 40%</span>'
                        f'<span class="msr-sec-count">{len(_t2)} stocks</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                    for s in _t2:
                        _render_card(s, 'buy', tier_color='#4A9EFF')

                # ── Tier 3: WATCHLIST ────────────────────────────────────────
                if _t3:
                    st.markdown(
                        f'<div class="msr-sec-row" style="border-left:3px solid #fbbf2422;">'
                        f'<div class="msr-sec-dot" style="background:#fbbf24;"></div>'
                        f'<span class="msr-sec-title" style="color:#fbbf24;">WATCHLIST</span>'
                        f'<span style="font-size:0.68rem;color:#555;margin-left:0.3rem;">'
                        f'Passes basic gates — monitor before entering</span>'
                        f'<span class="msr-sec-count">{len(_t3)} stocks</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                    for s in _t3:
                        _render_card(s, 'buy', tier_color='#fbbf24')



    elif st.session_state.show_macro:

        # ── MACRO INTELLIGENCE FULL PAGE ──────────────────────────────────────
        apply_ui_theme()
        st.markdown("""
        <style>
        header[data-testid="stHeader"] { display: none !important; }
        section[data-testid="stMainBlockContainer"] { padding-top: 1rem !important; }
        </style>""", unsafe_allow_html=True)

        back_col, title_col = st.columns([1, 6], gap="small")
        with back_col:
            if st.button("← Home", key="macro_back_btn", type="secondary", width="stretch"):
                st.session_state.show_macro = False
                st.rerun()
        with title_col:
            st.markdown(
                "<div style='font-size:1.4rem;font-weight:900;color:#e8e8e8;"
                "letter-spacing:-0.5px;padding-top:0.15rem;'>"
                "🌍 Macro Intelligence "
                "<span style='font-size:0.7rem;font-weight:600;color:#555;'>"
                "Global factors affecting Saudi stocks</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        from macro_tab import render_macro_tab
        render_macro_tab()

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



        # -- tile helpers ------------------------------------------------

        def _tile(label, value, sub, accent, val_color=None, sub_color=None, val_size="1.15rem", tooltip=None):

            if val_color is None:

                val_color = "#e0e0e0"

            if sub_color is None:

                sub_color = "#888"

            tip_html = (
                f"<span title='{tooltip}' class='hero-tip'>?</span>"
            ) if tooltip else ""

            _lg = " lg" if val_size == "1.5rem" else ""

            return (

                f"<div class='hero-tile'>"

                f"<div class='hero-tile-lbl'>{label}{tip_html}</div>"

                f"<div class='hero-tile-val{_lg}' style='color:{val_color};"

                f" text-shadow:0 0 18px {accent}33;'>{value}</div>"

                f"<div class='hero-tile-sub' style='color:{sub_color};'>{sub}</div>"

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



        price_sub   = f"{_arrow(period_change)} {period_change:+.2f}% since start"

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

                    val_size="1.5rem",

                    tooltip="Average number of shares traded per day over the analysis period")

        )



        tiles_bot = (

            _tile("Analysis Period",

                  f"{df.iloc[0]['Date'].strftime('%b %d, %Y')} &#8594; {df.iloc[-1]['Date'].strftime('%b %d, %Y')}",

                  f"{len(df):,} trading days",

                  "#4A9EFF")

            + _tile("Price Range",

                    f"{price_range:.2f} SAR",

                    f"{volatility:.1f}% of period low",

                    "#4A9EFF",

                    tooltip="Difference between the highest and lowest price during the analysis period")

            + _tile("Annualized Volatility",

                    f"{annual_vol:.1f}%",

                    ann_label,

                    annual_vol_color,

                    val_color=annual_vol_color,

                    sub_color=ann_sub_col,

                    tooltip="Standard deviation of daily returns scaled to one year — measures price uncertainty")

        )



        _period_label = df.iloc[0]['Date'].strftime('%b %Y') + " &#8594; " + df.iloc[-1]['Date'].strftime('%b %Y')

        _regime_pill = (

            "<span style='font-size:0.62rem; color:#606060; text-transform:uppercase;"

            " letter-spacing:1px; font-weight:700; margin-right:0.5rem;'>Regime</span>"

            "<span style='font-size:0.78rem; font-weight:700; color:#fff; background:" + regime_color + ";"

            " padding:0.25rem 0.85rem; border-radius:20px; letter-spacing:0.5px;"

            " box-shadow:0 0 12px " + regime_color + "44;'>" + latest['REGIME'] + "</span>"

        )


        hero_html = (

            "<div class='hero-wrap'>"



            "<div class='hero-inner'>"



            "<div class='hero-hdr'>"

            "<div>"

            "<div class='hero-name'>" + stock_name + "</div>"

            "<div class='hero-sub'>"

            + symbol_input + "&nbsp;&nbsp;&#183;&nbsp;&nbsp;" + _period_label +

            "</div>"

            "</div>"

            "<div style='display:flex; align-items:center;'>" + _regime_pill + "</div>"

            "</div>"



            "<div class='hero-divider'></div>"



            "<div class='hero-grid5'>"

            + tiles_top +

            "</div>"



            "<div class='hero-grid3'>"

            + tiles_bot +

            "</div>"



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
        from elliott_wave_tab import elliott_wave_tab

        # AI cache pre-warm removed — tabs compute on demand (Streamlit lazy-loads tab content)

        tab_dec, tab0, tab1, tab2, tab_vp, tab_smc, tab_ew, tab4, tab_tv = st.tabs([
            "Decision",
            "Regime",
            "Signals",
            "Patterns & Price Action",
            "Volume Profile",
            "SMC",
            "Elliott Wave",
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

        with tab_ew:
            elliott_wave_tab(df, current_price)

        with tab4:
            insight_toggle(
                "ai_analysis_info",
                "How AI Analysis works",
                "<p>This tab uses a <strong>12-factor scoring engine</strong> to evaluate the current market setup.</p>"
                "<p><strong>AI Score (0–100):</strong> Every factor — momentum, trend strength, RSI positioning, MACD divergence, "
                "Bollinger Band compression, volume dynamics, ATR volatility, support/resistance proximity — casts a bullish or bearish vote. "
                "The score aggregates them. <strong style='color:#4caf50'>70+</strong> = bullish setup, "
                "<strong style='color:#f44336'>30−</strong> = bearish, <strong style='color:#ff9800'>30–70</strong> = neutral/wait.</p>"
                "<p><strong>Trade Setups:</strong> Entry, stop loss, and profit target are calculated from current ATR and nearest support/resistance levels. "
                "Risk/reward ratios are computed for each setup.</p>"
                "<p><strong>ML Predictions:</strong> Three independent models forecast 5-day, 10-day, and 20-day price moves using historical pattern matching "
                "and feature regression on hundreds of prior similar market conditions.</p>"
                "<p><strong>Historical Analogies:</strong> Searches for the 25 most similar past price patterns and shows their average forward return.</p>"
                "<p style='color:#9e9e9e;font-size:0.85em'>Analysis tool only — not financial advice. Always apply your own risk management.</p>",
            )
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

