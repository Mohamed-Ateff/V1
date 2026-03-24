import streamlit as st

def info_icon(tooltip_text):

    """Create a small help icon with tooltip explanation."""

    return f'<span title="{tooltip_text}" style="color: #6366F1; font-weight: bold; cursor: help; margin-left: 0.3rem;">?</span>'





def apply_ui_theme():

    """Apply global UI theme (light/dark) with high contrast readability."""

    if 'ui_theme' not in st.session_state:

        st.session_state.ui_theme = 'dark'



    theme = st.session_state.ui_theme



    if theme == 'light':

        bg = '#f5f7fb'

        bg_grad_1 = 'rgba(255,255,255,0.88)'

        bg_grad_2 = 'rgba(236,241,249,0.92)'

        panel = '#ffffff'

        panel_alt = '#f9fbff'

        text = '#1f2a3a'

        muted = '#5f6f86'

        border = '#d7deea'

        input_bg = '#ffffff'

        input_border = '#cfd8e6'

        tab_bg = '#eaf0f8'

        tab_text = '#5a6f8f'

        tab_active_bg = '#ffffff'

        tab_active_text = '#1f2a3a'

        metric_bg = '#ffffff'

    else:

        bg = '#181818'

        bg_grad_1 = '#181818'

        bg_grad_2 = '#181818'

        panel = '#212121'

        panel_alt = '#212121'

        text = '#ffffff'

        muted = '#9e9e9e'

        border = '#303030'

        input_bg = '#303030'

        input_border = '#404040'

        tab_bg = '#212121'

        tab_text = '#9e9e9e'

        tab_active_bg = '#303030'

        tab_active_text = '#ffffff'

        metric_bg = '#212121'



    st.session_state.theme_palette = {

        'panel': panel,

        'panel_alt': panel_alt,

        'text': text,

        'muted': muted,

        'border': border,

        'metric_bg': metric_bg,

    }



    st.markdown(f"""

    <style>

    .stApp, [data-testid="stAppViewContainer"] {{

        background: {bg} !important;

        color: {text} !important;

    }}



    section[data-testid="stMain"],

    section[data-testid="stMain"] > div,

    .main .block-container,

    [data-testid="stVerticalBlock"],

    [data-testid="stVerticalBlockBorderWrapper"] > div {{

        color: {text} !important;

    }}



    .stMarkdown, .stMarkdown p, .stText, p, span, label,

    h1, h2, h3, h4, h5, h6,

    .section-title, .rec-title {{

        color: {text} !important;

    }}



    [data-testid="stAlert"] {{

        background: {panel_alt} !important;

        border-color: {border} !important;

        color: {text} !important;

    }}



    [data-testid="stMetric"],

    [data-testid="stMetric"] > div {{

        background: {metric_bg} !important;

        border-color: {border} !important;

        color: {text} !important;

        border-radius: 10px !important;

    }}

    [data-testid="stMetricLabel"],

    [data-testid="stMetricValue"],

    [data-testid="stMetricDelta"] {{

        color: {text} !important;

    }}



    .cp-controls-card {{

        background: linear-gradient(160deg, {bg_grad_1} 0%, {bg_grad_2} 100%) !important;

        border-color: {border} !important;

    }}

    .cp-feature {{

        background: {panel_alt} !important;

        border-color: {border} !important;

    }}

    .cp-title, .cp-feature h4 {{ color: {text} !important; }}

    .cp-sub, .cp-kicker, .cp-feature p, .cp-input-label {{ color: {muted} !important; }}



    .stTextInput > div > div > input,

    .stNumberInput input,

    .stTextArea textarea,

    .stDateInput input,

    .stDateInput [data-baseweb="input"],

    .stSelectbox [data-baseweb="select"],

    .stMultiSelect [data-baseweb="select"],

    .stMultiSelect [data-baseweb="tag"] {{

        background: {input_bg} !important;

        border-color: {input_border} !important;

        color: {text} !important;

    }}



    .stSelectbox div,

    .stMultiSelect div,

    .stDateInput div,

    .stTextInput div,

    .stNumberInput div,

    .stTextArea div,

    .stRadio label,

    .stCheckbox label,

    .stSlider label {{

        color: {text} !important;

    }}



    .stButton > button,

    .stDownloadButton > button {{

        background: {panel_alt} !important;

        color: {text} !important;

        border: 1px solid {border} !important;

    }}



    .stButton > button:hover,

    .stDownloadButton > button:hover {{

        border-color: {input_border} !important;

    }}



    div[data-baseweb="popover"],

    div[data-baseweb="menu"],

    ul[role="listbox"],

    li[role="option"] {{

        background: {panel} !important;

        color: {text} !important;

        border-color: {border} !important;

    }}



    .stDataFrame, .stDataEditor, .stTable {{

        border-color: {border} !important;

        color: {text} !important;

    }}



    div[data-testid="stDataFrame"],

    div[data-testid="stTable"],

    div[data-testid="stDataEditor"] {{

        background: {panel} !important;

        border: 1px solid {border} !important;

        border-radius: 10px !important;

    }}



    .stTable table,

    .stTable thead tr,

    .stTable tbody tr,

    .stTable th,

    .stTable td,

    div[data-testid="stDataFrame"] table,

    div[data-testid="stDataFrame"] th,

    div[data-testid="stDataFrame"] td,

    div[data-testid="stDataEditor"] table,

    div[data-testid="stDataEditor"] th,

    div[data-testid="stDataEditor"] td {{

        background: {panel} !important;

        color: {text} !important;

        border-color: {border} !important;

    }}



    div[role="tablist"] {{

        background: rgba(255,255,255,0.06) !important;

        border: none !important;

        box-shadow: none !important;

    }}

    div[role="tablist"] button {{

        color: rgba(255,255,255,0.55) !important;

    }}

    div[role="tablist"] button:hover {{

        color: rgba(255,255,255,0.8) !important;

        background: rgba(255,255,255,0.04) !important;

    }}

    div[role="tablist"] button[aria-selected="true"] {{

        background: rgba(255,255,255,0.12) !important;

        color: rgba(255,255,255,0.95) !important;

        border: none !important;

        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;

    }}



    .stExpander {{

        background: {panel_alt} !important;

        border-color: {border} !important;

    }}

    .stExpander details summary,

    .stCheckbox label {{

        color: {text} !important;

    }}



    .auth-header-left {{

        background: {panel_alt} !important;

        border-color: {border} !important;

    }}

    .auth-header-left span:first-child {{ color: {muted} !important; }}

    .auth-header-left span:last-child {{ color: {text} !important; }}



    .cp-theme-card,

    .cp-theme-tile {{

        background: {panel} !important;

        border-color: {border} !important;

        color: {text} !important;

    }}



    [style*='background:#0d1117'],

    [style*='background:#0a0d14'],

    [style*='background:#10151f'],

    [style*='background:#151c28'],

    [style*='background:#131929'],

    [style*='background:#1a2035'],

    [style*='background:#12151e'],

    [style*='background:#0f1522'],

    [style*='background:#111725'] {{

        background: {panel_alt} !important;

    }}



    [style*='border:1px solid #1e2535'],

    [style*='border:1px solid #1e2330'],

    [style*='border:1px solid #22304a'],

    [style*='border:1px solid #1a2035'],

    [style*='border:1px solid #2a3350'] {{

        border-color: {border} !important;

    }}



    [style*='color:#e8eaf0'],

    [style*='color:#dce6f7'],

    [style*='color:#dce5f2'],

    [style*='color:#e5ebf6'],

    [style*='color:#ffffff'],

    [style*='color:#fff'] {{

        color: {text} !important;

    }}



    [style*='color:#8fa8c8'],

    [style*='color:#8a95a8'],

    [style*='color:#9ab0c8'],

    [style*='color:#8892a4'],

    [style*='color:#8fa0b8'],

    [style*='color:#9ca9bc'],

    [style*='color:#a7b2c5'] {{

        color: {muted} !important;

    }}



    .js-plotly-plot .plotly .bg {{

        fill: {panel} !important;

    }}

    .js-plotly-plot .plotly .gtitle,

    .js-plotly-plot .plotly .xtick text,

    .js-plotly-plot .plotly .ytick text,

    .js-plotly-plot .plotly .legendtext,

    .js-plotly-plot .plotly .annotation-text,

    .js-plotly-plot .plotly .ytitle,

    .js-plotly-plot .plotly .xtitle {{

        fill: {text} !important;

    }}

    .js-plotly-plot .plotly .gridlayer path {{

        stroke: {border} !important;

        stroke-opacity: 0.65 !important;

    }}



    ::placeholder {{ color: {muted} !important; opacity: 1 !important; }}

    </style>

    """, unsafe_allow_html=True)





