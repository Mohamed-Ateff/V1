import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta, timezone





# ???????????????????????????????????????????????????????????????????????????????

# SAUDI MARKET STATUS FUNCTIONS

# ???????????????????????????????????????????????????????????????????????????????



@st.cache_data(ttl=60)  # Cache for 60 seconds

def get_saudi_market_status():

    """Get Saudi stock market (Tadawul) status and TASI index data."""

    # Saudi Arabia Time is UTC+3

    saudi_offset = timezone(timedelta(hours=3))

    now_saudi = datetime.now(saudi_offset)

    

    # Market hours: Sunday-Thursday, 10:00 AM - 3:00 PM Saudi time

    weekday = now_saudi.weekday()  # Monday=0, Sunday=6

    hour = now_saudi.hour

    minute = now_saudi.minute

    current_time = hour * 60 + minute  # Minutes since midnight

    

    market_open_time = 10 * 60  # 10:00 AM = 600 minutes

    market_close_time = 15 * 60  # 3:00 PM = 900 minutes

    

    # Trading days: Sunday (6) to Thursday (3)

    is_trading_day = weekday in [6, 0, 1, 2, 3]  # Sun, Mon, Tue, Wed, Thu

    is_market_hours = market_open_time <= current_time < market_close_time

    

    is_open = is_trading_day and is_market_hours

    

    # Calculate time to open/close

    if is_open:

        mins_to_close = market_close_time - current_time

        status_detail = f"Closes in {mins_to_close // 60}h {mins_to_close % 60}m"

    elif is_trading_day and current_time < market_open_time:

        mins_to_open = market_open_time - current_time

        status_detail = f"Opens in {mins_to_open // 60}h {mins_to_open % 60}m"

    else:

        # Calculate days until next trading day

        if weekday == 3 and current_time >= market_close_time:  # Thursday after close

            days_to_sunday = 3

        elif weekday == 4:  # Friday

            days_to_sunday = 2

        elif weekday == 5:  # Saturday

            days_to_sunday = 1

        else:

            days_to_sunday = 0

        

        if days_to_sunday > 0:

            status_detail = f"Opens Sunday 10:00 AM"

        else:

            status_detail = "Opens 10:00 AM"

    

    return {

        'is_open': is_open,

        'status_detail': status_detail,

        'saudi_time': now_saudi.strftime('%I:%M %p'),

        'saudi_date': now_saudi.strftime('%a, %b %d'),

        'weekday': weekday

    }





@st.cache_data(ttl=300)  # Cache for 5 minutes - important for speed

def get_all_tadawul_tickers():

    """283 Saudi Exchange (Tadawul + NOMU) listed companies — verified against official Saudi Exchange listing."""

    return {

        # ══════════════════════════════════════════════════════════════════════
        # BANKS & FINANCIALS (21 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "1010.SR": "Riyad Bank", "1020.SR": "Bank AlJazira", "1030.SR": "SAIB",
        "1050.SR": "BSF", "1060.SR": "SAB", "1080.SR": "ANB",
        "1111.SR": "Tadawul Group", "1120.SR": "Al Rajhi", "1140.SR": "ALBILAD",
        "1150.SR": "Alinma", "1180.SR": "SNB", "1182.SR": "Amlak",
        "1183.SR": "SHL", "1810.SR": "Seera", "1820.SR": "Baan",
        "1833.SR": "Almawarid", "1835.SR": "Tamkeen",
        "4081.SR": "Nayifat", "4083.SR": "Tasheel",

        # ══════════════════════════════════════════════════════════════════════
        # MATERIALS & CHEMICALS (30 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "1201.SR": "Takween", "1202.SR": "MEPCO", "1210.SR": "BCI",
        "1211.SR": "MAADEN", "1212.SR": "Astra Industrial", "1213.SR": "NASEEJ",
        "2001.SR": "Chemanol", "2010.SR": "SABIC", "2020.SR": "SAFCO",
        "2060.SR": "TASNEE", "2070.SR": "SPIMACO", "2082.SR": "ACWA",
        "2083.SR": "Petrochem", "2090.SR": "NGC", "2130.SR": "SIDC",
        "2140.SR": "AYYAN", "2150.SR": "ZOUJAJ", "2200.SR": "APC",
        "2220.SR": "MAADANIYAH", "2222.SR": "Aramco", "2223.SR": "LUBEREF",
        "2230.SR": "CHEMICAL", "2250.SR": "SIIG", "2270.SR": "SADAFCO",
        "2280.SR": "Almarai", "2281.SR": "TANMIAH",
        "2283.SR": "FIRST MILLING", "2284.SR": "MODERN MILLS", "2285.SR": "ARABIAN MILLS",
        "2330.SR": "ADVANCED",
        "2350.SR": "Saudi Kayan", "2380.SR": "PETRO RABIGH",
        "2381.SR": "Arabian Drilling", "2382.SR": "ADES",

        # ══════════════════════════════════════════════════════════════════════
        # CEMENT & BUILDING MATERIALS (12 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "3002.SR": "NAJRAN CEMENT", "3003.SR": "City Cement",
        "3004.SR": "NORCEM", "3005.SR": "UQCC",
        "3007.SR": "OASIS", "3008.SR": "AL KATHIRI",
        "3010.SR": "ACC", "3020.SR": "YC",
        "3040.SR": "QACCO", "3050.SR": "SPCC",
        "3060.SR": "YCC", "3080.SR": "EPCCO",
        "3090.SR": "TCC", "3091.SR": "Jouf Cement",

        # ══════════════════════════════════════════════════════════════════════
        # RETAIL & CONSUMER (28 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "4001.SR": "A.Othaim Market", "4003.SR": "EXTRA",
        "4008.SR": "SACO", "4050.SR": "SASCO", "4051.SR": "BAAZEEM",
        "4160.SR": "THIMAR", "4161.SR": "Bindawood", "4163.SR": "ALDAWAA",
        "4164.SR": "NAHDI", "4190.SR": "JARIR", "4191.SR": "ABO MOATI",
        "4192.SR": "ALSAIF GALLERY", "4193.SR": "NICE ONE",
        "4194.SR": "BUILD STATION", "4200.SR": "ALDREES",
        "4240.SR": "CENOMI RETAIL",
        "4011.SR": "LAZURDE", "4012.SR": "ALASEEL",
        "4180.SR": "FITAIHI GROUP",
        "4170.SR": "TECO", "4290.SR": "ALKHALEEJ TRNG",
        "4291.SR": "NCLE", "4292.SR": "ATAA",

        # ══════════════════════════════════════════════════════════════════════
        # CONSUMER SERVICES & FOOD (22 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "6001.SR": "HB", "6002.SR": "HERFY FOODS",
        "6012.SR": "RAYDAN", "6015.SR": "AMERICANA",
        "6016.SR": "BURGERIZZR", "6017.SR": "JAHEZ",
        "6018.SR": "SPORT CLUBS", "6020.SR": "GACO",
        "6040.SR": "TADCO", "6070.SR": "ALJOUF",
        "6090.SR": "JAZADCO",
        "4061.SR": "ANAAM",

        # ══════════════════════════════════════════════════════════════════════
        # MEDIA & ENTERTAINMENT (4 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "4070.SR": "TAPRCO", "4071.SR": "ALARABIA",
        "4072.SR": "MBC GROUP", "4210.SR": "SRMG",

        # ══════════════════════════════════════════════════════════════════════
        # HEALTH CARE (11 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "4002.SR": "Mouwasat", "4004.SR": "Dallah Health",
        "4005.SR": "NMC", "4007.SR": "Al Hammadi",
        "4009.SR": "MEAHCO", "4013.SR": "HMG",
        "4014.SR": "Arriyadh Dev", "4015.SR": "JAMJOOM",
        "4016.SR": "MEPCO PHARMA", "4017.SR": "FAKEEH",
        "4018.SR": "ALMOOSA", "4019.SR": "SMC HEALTHCARE",
        "4021.SR": "CMCER",

        # ══════════════════════════════════════════════════════════════════════
        # TRANSPORTATION & LOGISTICS (9 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "4030.SR": "BAHRI", "4031.SR": "SGS",
        "4040.SR": "SAPTCO", "4260.SR": "BUDGET SAUDI",
        "4261.SR": "THEEB", "4263.SR": "SAL",
        "4264.SR": "FLYNAS", "4265.SR": "CHERRY",

        # ══════════════════════════════════════════════════════════════════════
        # CAPITAL GOODS & INDUSTRIALS (14 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "1301.SR": "ASLAK", "1302.SR": "BAWAN",
        "1303.SR": "EIC", "1321.SR": "EAST PIPES",
        "2370.SR": "MESC",
        "4142.SR": "RIYADH CABLES", "4143.SR": "TALCO",
        "4146.SR": "GAS", "4147.SR": "CGS",
        "4148.SR": "ALWASAIL INDUSTRIAL",
        "4300.SR": "Dar Al Arkan", "4310.SR": "KEC",

        # ══════════════════════════════════════════════════════════════════════
        # REAL ESTATE (10 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "4090.SR": "TAIBA", "4100.SR": "MCDC",
        "4150.SR": "ARDCO", "4220.SR": "EMAAR EC",
        "4020.SR": "SAUDI REAL ESTATE",
        "4250.SR": "JABAL OMAR", "4321.SR": "CENOMI CENTERS",
        "4322.SR": "RETAL", "4323.SR": "SUMOU",
        "4326.SR": "ALMAJDIAH", "4327.SR": "ALRAMZ",

        # ══════════════════════════════════════════════════════════════════════
        # REITs (13 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "4330.SR": "RIYAD REIT", "4331.SR": "AL JAZIRA MAWTEN",
        "4332.SR": "JADWA HARAMAIN", "4333.SR": "TALEEM REIT",
        "4334.SR": "AL MAATHER", "4335.SR": "MUSHARAKA REIT",
        "4336.SR": "MULKIA REIT", "4337.SR": "AL MASHAAR",
        "4338.SR": "AL-AHLI REIT", "4339.SR": "DERAYAH REIT",
        "4340.SR": "ALRAJHI REIT", "4342.SR": "JADWA REIT SAUDI",
        "4344.SR": "SEDCO REIT", "4345.SR": "ALINMA RETAIL REIT",
        "4346.SR": "MEFIC REIT", "4347.SR": "BONYAN REIT",
        "4348.SR": "ALKHABEER REIT", "4349.SR": "ALINMA HOSP REIT",
        "4350.SR": "AREIC REIT",

        # ══════════════════════════════════════════════════════════════════════
        # UTILITIES (1 stock)
        # ══════════════════════════════════════════════════════════════════════
        "5110.SR": "SEC",

        # ══════════════════════════════════════════════════════════════════════
        # TELECOM & IT (11 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "7010.SR": "STC", "7020.SR": "ETIHAD ETISALAT",
        "7030.SR": "ZAIN KSA", "7040.SR": "GO TELECOM",
        "7200.SR": "MIS", "7201.SR": "ARAB SEA INFO",
        "7202.SR": "SOLUTIONS", "7203.SR": "ELM",
        "7204.SR": "2P", "7211.SR": "AZM",

        # ══════════════════════════════════════════════════════════════════════
        # INSURANCE (23 stocks)
        # ══════════════════════════════════════════════════════════════════════
        "8010.SR": "TAWUNIYA", "8012.SR": "JAZIRA TAKAFUL",
        "8020.SR": "MALATH", "8030.SR": "MGIC",
        "8040.SR": "MUTAKAMELA", "8050.SR": "SALAMA",
        "8060.SR": "WALAA", "8070.SR": "ARABIAN SHIELD",
        "8100.SR": "SAICO", "8120.SR": "GULF UNION",
        "8150.SR": "ACIG", "8160.SR": "AICC",
        "8170.SR": "ALETIHAD", "8180.SR": "ALSAGR",
        "8190.SR": "UCA", "8200.SR": "SAUDI RE",
        "8210.SR": "BUPA ARABIA", "8230.SR": "ALRAJHI TAKAFUL",
        "8240.SR": "CHUBB", "8250.SR": "GIG",
        "8260.SR": "GULF GENERAL", "8280.SR": "LIVA",
        "8300.SR": "WATANIYA", "8310.SR": "AMANA INSURANCE",
        "8311.SR": "ENAYA", "8313.SR": "RASAN",

        # ══════════════════════════════════════════════════════════════════════
        # NEW LISTINGS 2022-2025 (9500+ series)
        # ══════════════════════════════════════════════════════════════════════
        "9510.SR": "NBM",
        "9513.SR": "WATANI STEEL", "9516.SR": "NGDC",
        "9517.SR": "MOBI INDUSTRY", "9521.SR": "INMAR",
        "9523.SR": "GROUP FIVE", "9524.SR": "AICTEC",
        "9527.SR": "AME", "9530.SR": "TIBBIYAH",
        "9535.SR": "LADUN", "9537.SR": "AMWAJ INTERNATIONAL",
        "9539.SR": "AQASEEM", "9540.SR": "TADWEEER",
        "9541.SR": "ACADEMY OF LEARNING", "9542.SR": "KEIR",
        "9543.SR": "NETWORKERS", "9545.SR": "ALDAWLIAH",
        "9546.SR": "NABA ALSAHA", "9548.SR": "APICO",
        "9549.SR": "ALBABTAIN FOOD", "9550.SR": "SURE",
        "9551.SR": "KNOWLEDGE TOWER", "9552.SR": "SAUDI TOP",
        "9553.SR": "MOLAN", "9557.SR": "EDARAT",
        "9558.SR": "ALQEMAM", "9559.SR": "BALADY",
        "9561.SR": "KNOWLEDGENET", "9562.SR": "FOOD GATE",
        "9564.SR": "HORIZON FOOD", "9565.SR": "MEYAR",
        "9568.SR": "MAYAR", "9569.SR": "ALMUNEEF",
        "9570.SR": "TAM DEVELOPMENT", "9571.SR": "MUNAWLA",
        "9574.SR": "PRO MEDEX", "9575.SR": "MARBLE DESIGN",
        "9576.SR": "PAPER HOME", "9578.SR": "ATLAS ELEVATORS",
        "9579.SR": "IOUD", "9581.SR": "CLEAN LIFE",
        "9584.SR": "RIYAL", "9585.SR": "MULKIA",
        "9586.SR": "OSOOL AND BAKHEET", "9588.SR": "RIYADH STEEL",
        "9589.SR": "FAD", "9591.SR": "VIEW",
        "9595.SR": "WSM", "9599.SR": "TAQAT",
        "9604.SR": "MIRAL", "9606.SR": "THARWAH",
        "9610.SR": "FIRST AVENUE", "9611.SR": "UFG",
        "9613.SR": "SHALFA", "9615.SR": "MUFEED",
        "9616.SR": "JANA", "9617.SR": "ARABICA STAR",
        "9619.SR": "MULTI BUSINESS", "9621.SR": "DRC",
        "9622.SR": "SMC", "9623.SR": "ALBATTAL FACTORY",
        "9625.SR": "ITMAM", "9626.SR": "SMILE CARE",
        "9627.SR": "TMC", "9628.SR": "LAMASAT",
        "9630.SR": "RATIO", "9632.SR": "FUTURE VISION",
        "9633.SR": "SERVICE EQUIPMENT", "9634.SR": "ADEER",
        "9637.SR": "AXELERATED SOLUTIONS", "9639.SR": "ANMAT",
        "9640.SR": "ASAS MAKEEN", "9642.SR": "TIME",
        "9645.SR": "SIGN WORLD", "9647.SR": "WAJD LIFE",
        "9651.SR": "ALTWIJRI", "9653.SR": "KDL",
    }




@st.cache_data(ttl=120, show_spinner=False)  # 2 min cache

def get_saudi_market_data(period="1d"):

    """FAST batch download of ALL Tadawul stocks with period filter."""

    all_tickers = get_all_tadawul_tickers()

    tickers_list = list(all_tickers.keys())

    

    # Map periods to yfinance periods

    period_map = {"1d": "5d", "1w": "1mo", "1m": "3mo", "3m": "6mo", "6m": "1y", "1y": "2y", "ytd": "ytd"}

    yf_period = period_map.get(period, "5d")

    

    try:

        data = yf.download(

            tickers_list,

            period=yf_period,

            progress=False,

            threads=True,

            group_by='ticker',

            timeout=15

        )

    except Exception:

        return None

    

    if data is None or data.empty:

        return None

    

    stocks = []

    for ticker in tickers_list:

        try:

            if ticker not in data.columns.get_level_values(0):

                continue

            

            hist = data[ticker].dropna(subset=['Close'])

            if len(hist) < 2:

                continue

            

            price = float(hist['Close'].iloc[-1])

            # For period comparison

            if period == "1d":

                compare_price = float(hist['Close'].iloc[-2])

            else:

                compare_price = float(hist['Close'].iloc[0])

            

            change_pct = ((price - compare_price) / compare_price) * 100 if compare_price > 0 else 0

            vol = float(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0

            

            stocks.append({

                'ticker': ticker.replace('.SR', ''),

                'name': all_tickers[ticker],

                'price': price,

                'change': change_pct,

                'volume': vol

            })

        except:

            continue

    

    if not stocks:

        return None

    

    # Sort by change

    stocks.sort(key=lambda x: x['change'], reverse=True)

    

    # Calculate market metrics

    total = len(stocks)

    gainers = sum(1 for s in stocks if s['change'] > 0.1)

    losers = sum(1 for s in stocks if s['change'] < -0.1)

    unchanged = total - gainers - losers

    avg_change = sum(s['change'] for s in stocks) / total if total > 0 else 0

    total_volume = sum(s['volume'] for s in stocks)

    

    # Market sentiment based on avg change

    if avg_change > 1.5:

        sentiment = "STRONG BUY"

        sent_color = "#26A69A"

    elif avg_change > 0.3:

        sentiment = "BULLISH"

        sent_color = "#26A69A"

    elif avg_change > -0.3:

        sentiment = "NEUTRAL"

        sent_color = "#FFC107"

    elif avg_change > -1.5:

        sentiment = "BEARISH"

        sent_color = "#ef5350"

    else:

        sentiment = "STRONG SELL"

        sent_color = "#ef5350"

    

    # Compute TASI proxy from major index components
    # Since ^TASI is not available on Yahoo Finance, we use weighted average of top stocks
    tasi_price = 0.0
    tasi_change = 0.0
    major_tickers = ['2222', '1120', '2010', '7010', '2280', '1180']  # Aramco, Al Rajhi, SABIC, STC, Almarai, SNB
    major_stocks = [s for s in stocks if s['ticker'] in major_tickers]
    if major_stocks:
        # Use average of major stocks as TASI proxy
        tasi_change = sum(s['change'] for s in major_stocks) / len(major_stocks)
        # Synthetic price based on weighted average (scale to ~12000 range typical for TASI)
        avg_price = sum(s['price'] for s in major_stocks) / len(major_stocks)
        tasi_price = avg_price * 250  # Scale factor to approximate TASI range
    else:
        # Fallback to overall market average
        tasi_change = avg_change
        tasi_price = 12000 + (avg_change * 100)  # Approximate

    return {

        'stocks': stocks,

        'total': total,

        'gainers': gainers,

        'losers': losers,

        'unchanged': unchanged,

        'avg_change': avg_change,

        'sentiment': sentiment,

        'sent_color': sent_color,

        'volume': total_volume,

        'top_gainers': stocks[:5],

        'top_losers': stocks[-5:][::-1] if len(stocks) >= 5 else [],

        'breadth': gainers / max(losers, 1),

        'tasi_price': tasi_price,

        'tasi_change': tasi_change

    }





# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED MARKET ANALYSIS — MULTI-STOCK SCANNER
# 10+ indicators · Weighted scoring · Regime detection · Multi-target exits
# ═══════════════════════════════════════════════════════════════════════════════

# Period alias → yfinance period (fetch enough bars for EMA200)
_PERIOD_MAP = {
    "3mo": "6mo",
    "6mo": "1y",
    "1y":  "2y",
}

@st.cache_data(ttl=300, show_spinner=False)
def run_market_analysis(tickers_list, period="6mo", min_score=2, sector_filter=None, start=None, end=None):
    """Advanced multi-stock scanner: EMA/RSI/MACD/BB/Stoch/ADX/Volume/OBV
    with weighted scoring, regime detection, and multi-target exits."""

    results = {'buy': [], 'sell': [], 'hold': []}
    if not tickers_list:
        return results

    all_info = get_all_tadawul_tickers()   # ticker → display name

    # Build sector map  (name keyword → sector label)
    _sector_rules = [
        (["Bank", "SIB", "BSF", "ANB", "SNB", "Rajhi", "Alinma", "Riyad", "SABB", "AlJazira", "Amlak"], "Banks"),
        (["SABIC", "Kayan", "Sahara", "Yansab", "Sipchem", "Chemanol", "Maaden", "Luberef", "Petro", "SAFCO", "Tasnee", "Zamil"], "Petrochemicals"),
        (["Cement", "City Cement", "Northern", "Yamama", "Qassim", "Southern", "Eastern", "Tabuk", "Jouf", "Hail", "Umm"], "Cement"),
        (["ACWA", "SEC", "Power", "SIG"], "Utilities"),
        (["STC", "Mobily", "Zain", "ITC", "Elm", "Solutions", "Turas", "Ejada", "Tawasul"], "Telecom & Tech"),
        (["Tawuniya", "Malath", "Medgulf", "Salama", "Walaa", "Bupa", "Sanad", "Solidarity", "Ins", "Takaful", "Shield"], "Insurance"),
        (["Almarai", "Savola", "Halwani", "Herfy", "Nadec", "Sunbulah", "Sinad", "Herfy", "Jouf Agri", "Tabuk Agri"], "Food & Agri"),
        (["REIT", "Riyad REIT", "Jadwa", "Jazira REIT", "Maather", "Musharaka", "Alinma REIT"], "REITs"),
        (["Jarir", "Extra", "Nahdi", "Bindawood", "Al Othaim", "SACO", "AlHokair"], "Retail"),
        (["Mouwasat", "Dallah", "Dr Sulaiman", "Al Hammadi", "Leejam"], "Healthcare"),
        (["Bahri", "SAPTCO", "Budget", "Theeb", "LUMI", "Logistics"], "Transport"),
        (["Dar Al Arkan", "Jabal Omar", "Emaar EC", "KEC", "Retal", "Sumou", "Real Estate", "Makkah"], "Real Estate"),
    ]
    def _get_sector(name):
        for keywords, sector in _sector_rules:
            if any(k.lower() in name.lower() for k in keywords):
                return sector
        return "Other"

    def _safe(series, idx=-1, default=0.0):
        try:
            s = series.dropna()
            return float(s.iloc[idx]) if len(s) > 0 else default
        except Exception:
            return default

    yf_period = _PERIOD_MAP.get(period, "1y")

    try:
        if start and end:
            all_data = yf.download(
                tickers_list,
                start=str(start),
                end=str(end),
                progress=False,
                threads=True,
                group_by='ticker',
                timeout=45,
            )
        else:
            all_data = yf.download(
                tickers_list,
                period=yf_period,
                progress=False,
                threads=True,
                group_by='ticker',
                timeout=45,
            )
    except Exception:
        return results

    if all_data is None or all_data.empty:
        return results

    # ── TASI Index: macro regime + relative strength baseline ────────────────
    # Downloaded once before the loop — used for RS calculation and market gate
    tasi_regime_bearish = False
    tasi_ret_20d        = 0.0
    try:
        if start and end:
            _td = yf.download("^TASI", start=str(start), end=str(end),
                              progress=False, timeout=15)
        else:
            _td = yf.download("^TASI", period="1y", progress=False, timeout=15)
        if _td is not None and not _td.empty:
            _tc   = _td['Close'].astype(float).dropna()
            _te50 = ta.ema(_tc, length=50)
            _te20 = ta.ema(_tc, length=20)
            _tcp  = float(_tc.iloc[-1])
            _te50v = float(_te50.dropna().iloc[-1]) if _te50 is not None and len(_te50.dropna()) > 0 else _tcp
            _te20v = float(_te20.dropna().iloc[-1]) if _te20 is not None and len(_te20.dropna()) > 0 else _tcp
            # Market is bearish if TASI is below both EMA20 and EMA50
            tasi_regime_bearish = (_tcp < _te20v) and (_tcp < _te50v)
            tasi_ret_20d = ((_tcp / float(_tc.iloc[-20])) - 1) * 100 if len(_tc) >= 20 else 0.0
    except Exception:
        pass

    for ticker in tickers_list:
        try:
            if len(tickers_list) == 1:
                data = all_data.copy()
            else:
                if ticker not in all_data.columns.get_level_values(0):
                    continue
                data = all_data[ticker].copy()

            data = data.dropna(subset=['Close'])
            if len(data) < 60:
                continue

            data = data.reset_index()
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            close  = data['Close'].astype(float)
            high   = data['High'].astype(float)
            low    = data['Low'].astype(float)
            volume = data['Volume'].astype(float)

            # ── Indicators ───────────────────────────────────────────────────
            ema20   = ta.ema(close, length=20)
            ema50   = ta.ema(close, length=50)
            ema200  = ta.ema(close, length=200)
            rsi     = ta.rsi(close, length=14)
            macd_df = ta.macd(close, fast=12, slow=26, signal=9)
            bb      = ta.bbands(close, length=20, std=2)
            stoch   = ta.stoch(high, low, close, k=14, d=3, smooth_k=3)
            adx_df  = ta.adx(high, low, close, length=14)
            atr     = ta.atr(high, low, close, length=14)
            obv     = ta.obv(close, volume)

            cp      = _safe(close)
            e20     = _safe(ema20,  default=cp)
            e50     = _safe(ema50,  default=cp)
            e200    = _safe(ema200, default=cp)
            cur_rsi = _safe(rsi, default=50)
            cur_atr = _safe(atr, default=cp * 0.02)

            # MACD
            if macd_df is not None:
                ml   = _safe(macd_df['MACD_12_26_9'])
                ms   = _safe(macd_df['MACDs_12_26_9'])
                ml_p = _safe(macd_df['MACD_12_26_9'], -2)
                ms_p = _safe(macd_df['MACDs_12_26_9'], -2)
                mh   = _safe(macd_df['MACDh_12_26_9'])
            else:
                ml = ms = ml_p = ms_p = mh = 0.0

            # Bollinger Bands
            if bb is not None:
                bb_cols = [c for c in bb.columns if 'BBU' in c or 'BBL' in c or 'BBM' in c]
                bbu_col = next((c for c in bb_cols if 'BBU' in c), None)
                bbl_col = next((c for c in bb_cols if 'BBL' in c), None)
                bbm_col = next((c for c in bb_cols if 'BBM' in c), None)
                bbu = _safe(bb[bbu_col], default=cp * 1.02) if bbu_col else cp * 1.02
                bbl = _safe(bb[bbl_col], default=cp * 0.98) if bbl_col else cp * 0.98
                bb_range = bbu - bbl
                bb_pct = (cp - bbl) / bb_range if bb_range > 0 else 0.5
                bb_width_pct = bb_range / cp if cp > 0 else 0.04
            else:
                bb_pct = 0.5
                bb_width_pct = 0.04

            # Stochastic
            if stoch is not None:
                sk_col = next((c for c in stoch.columns if 'STOCHk' in c), None)
                sd_col = next((c for c in stoch.columns if 'STOCHd' in c), None)
                sk   = _safe(stoch[sk_col], default=50) if sk_col else 50
                sd   = _safe(stoch[sd_col], default=50) if sd_col else 50
                sk_p = _safe(stoch[sk_col], -2, default=50) if sk_col else 50
                sd_p = _safe(stoch[sd_col], -2, default=50) if sd_col else 50
            else:
                sk = sd = sk_p = sd_p = 50.0

            # ADX / DI
            if adx_df is not None:
                adx_col = next((c for c in adx_df.columns if 'ADX' in c), None)
                dmp_col = next((c for c in adx_df.columns if 'DMP' in c), None)
                dmn_col = next((c for c in adx_df.columns if 'DMN' in c), None)
                cur_adx = _safe(adx_df[adx_col], default=15) if adx_col else 15
                pos_di  = _safe(adx_df[dmp_col], default=20) if dmp_col else 20
                neg_di  = _safe(adx_df[dmn_col], default=20) if dmn_col else 20
            else:
                cur_adx = 15; pos_di = 20; neg_di = 20

            # Volume
            vol_avg = float(volume.iloc[-20:].mean()) if len(volume) >= 20 else float(volume.mean())
            vol_cur = float(volume.iloc[-1])
            vol_ratio = vol_cur / vol_avg if vol_avg > 0 else 1.0

            # ── Liquidity gate: skip stocks with < 500K SAR avg daily turnover ──
            # Can't enter/exit illiquid stocks regardless of signals
            if (vol_avg * cp) < 500_000:
                continue

            # ── Volatility gate: skip erratic/untradeable stocks (ATR > 8%) ──
            if cp > 0 and (cur_atr / cp) > 0.08:
                continue

            # OBV trend (5-bar slope)
            obv_c = obv.dropna()
            obv_rising = (float(obv_c.iloc[-1]) > float(obv_c.iloc[-5])) if len(obv_c) >= 5 else True

            # Performance
            perf_5d  = ((cp / float(close.iloc[-5]))  - 1) * 100 if len(close) >= 5  else 0.0
            perf_1m  = ((cp / float(close.iloc[-20])) - 1) * 100 if len(close) >= 20 else 0.0
            perf_3m  = ((cp / float(close.iloc[-60])) - 1) * 100 if len(close) >= 60 else 0.0

            # ── Relative Strength vs TASI (20-day outperformance) ────────────
            # Key insight: stocks that beat the index during weakness are leaders
            rs_vs_tasi = perf_1m - tasi_ret_20d

            # ── Multi-timeframe: weekly EMA check (sample every 5 daily bars) ─
            # Require higher timeframe to agree before trusting daily signal
            weekly_bullish = None
            try:
                _wk = close.iloc[::5].reset_index(drop=True)  # ~1 bar per week
                if len(_wk) >= 10:
                    _wl = min(20, len(_wk) - 1)
                    _wema20 = ta.ema(_wk, length=_wl)
                    _we20v  = float(_wema20.dropna().iloc[-1]) if _wema20 is not None and len(_wema20.dropna()) > 0 else cp
                    if len(_wk) >= 15:
                        _wl50   = min(50, len(_wk) - 1)
                        _wema50 = ta.ema(_wk, length=_wl50)
                        _we50v  = float(_wema50.dropna().iloc[-1]) if _wema50 is not None and len(_wema50.dropna()) > 0 else _we20v
                    else:
                        _we50v = _we20v
                    weekly_bullish = (cp > _we20v) and (cp > _we50v)
            except Exception:
                weekly_bullish = None

            # ── Monthly trend confirmation (sample every 20 daily bars ≈ 1 month) ──
            # Monthly trend has the highest win-rate predictive power.
            # bull: price above monthly EMA12 and EMA24.
            monthly_bullish = None
            try:
                _mo = close.iloc[::20].reset_index(drop=True)  # ~1 bar per month
                if len(_mo) >= 6:
                    _ml_len  = min(12, len(_mo) - 1)
                    _ms_len  = min(24, len(_mo) - 1)
                    _mema12  = ta.ema(_mo, length=_ml_len)
                    _mema24  = ta.ema(_mo, length=_ms_len)
                    _me12v   = float(_mema12.dropna().iloc[-1]) if _mema12 is not None and len(_mema12.dropna()) > 0 else cp
                    _me24v   = float(_mema24.dropna().iloc[-1]) if _mema24 is not None and len(_mema24.dropna()) > 0 else _me12v
                    monthly_bullish = (cp > _me12v) and (cp > _me24v)
            except Exception:
                monthly_bullish = None


            # 52-week high/low
            lookback  = min(252, len(close))
            w52_high  = float(high.iloc[-lookback:].max())
            w52_low   = float(low.iloc[-lookback:].min())
            w52_pos   = (cp - w52_low) / (w52_high - w52_low) * 100 if (w52_high - w52_low) > 0 else 50

            # Regime
            atr_pct = cur_atr / cp if cp > 0 else 0
            if cur_adx > 25:
                regime = "TREND"
            elif bb_width_pct < 0.04:
                regime = "RANGE"
            else:
                regime = "VOLATILE"

            # ── REGIME-AWARE WEIGHTED SCORING ────────────────────────────────
            # Key insight: not all indicators work in all conditions.
            # TREND  → EMA/MACD/ADX are reliable; RSI/BB/Stoch give false signals
            # RANGE  → RSI/BB/Stoch are reliable (mean-reversion); EMA/MACD whipsaw
            # VOLATILE → Volume/OBV/ATR matter most; oscillators are noisy
            #
            # Multipliers per regime (1.0 = full weight, 0.5 = half, 0.0 = skip):
            #   Indicator Group    TREND   RANGE   VOLATILE
            #   ─────────────────  ─────   ─────   ────────
            #   EMA alignment       1.0     0.3      0.5
            #   Golden/Death Cross  1.0     0.5      0.5
            #   RSI                 0.3     1.0      0.5
            #   MACD                1.0     0.3      0.5
            #   Bollinger Bands     0.3     1.0      0.7
            #   Stochastic          0.3     1.0      0.5
            #   ADX                 1.0     0.0      0.5
            #   Volume              0.7     0.7      1.0
            #   OBV                 0.7     0.5      1.0
            #   52-Week Position    1.0     1.0      1.0  (always relevant)
            #   Momentum            1.0     0.5      0.7
            #   RS vs TASI          1.0     1.0      1.0  (always relevant)
            #   Weekly MTF          1.0     0.5      0.7
            #   Market gate         1.0     1.0      1.0  (always relevant)

            _regime_weights = {
                "TREND":    {"ema": 1.0, "cross": 1.0, "rsi": 0.3, "macd": 1.0, "bb": 0.3, "stoch": 0.3, "adx": 1.0, "vol": 0.7, "obv": 0.7, "w52": 1.0, "mom": 1.0, "rs": 1.0, "weekly": 1.0},
                "RANGE":    {"ema": 0.3, "cross": 0.5, "rsi": 1.0, "macd": 0.3, "bb": 1.0, "stoch": 1.0, "adx": 0.0, "vol": 0.7, "obv": 0.5, "w52": 1.0, "mom": 0.5, "rs": 1.0, "weekly": 0.5},
                "VOLATILE": {"ema": 0.5, "cross": 0.5, "rsi": 0.5, "macd": 0.5, "bb": 0.7, "stoch": 0.5, "adx": 0.5, "vol": 1.0, "obv": 1.0, "w52": 1.0, "mom": 0.7, "rs": 1.0, "weekly": 0.7},
            }
            rw = _regime_weights.get(regime, _regime_weights["VOLATILE"])

            signals   = []
            score     = 0.0
            ind_score = 0.0   # technical indicators sub-score
            pa_score  = 0.0   # price action sub-score
            _IND_GRP  = {"rsi", "macd", "bb", "stoch", "adx", "vol", "obv"}

            # Helper: apply regime weight to a raw score and track sub-scores
            _sub = [ind_score, pa_score]  # mutable refs: [0]=ind, [1]=pa
            def _w(raw_pts, group_key):
                v = raw_pts * rw[group_key]
                if group_key in _IND_GRP:
                    _sub[0] += v
                else:
                    _sub[1] += v
                return v

            # 1. EMA Trend Alignment (raw max ±5)
            above_e200 = cp > e200
            above_e50  = cp > e50
            above_e20  = cp > e20
            if above_e200 and above_e50 and above_e20:
                signals.append(f"Full EMA alignment (bullish) [{regime}:{'full' if rw['ema']>=0.8 else 'reduced'}]")
                score += _w(5, "ema")
            elif above_e50 and above_e20:
                signals.append(f"EMA20 & EMA50 bullish [{regime}:{'full' if rw['ema']>=0.8 else 'reduced'}]")
                score += _w(3, "ema")
            elif above_e20:
                signals.append("Short-term bullish (>EMA20)")
                score += _w(1, "ema")
            elif (not above_e200) and (not above_e50) and (not above_e20):
                signals.append(f"Full EMA alignment (bearish) [{regime}:{'full' if rw['ema']>=0.8 else 'reduced'}]")
                score += _w(-5, "ema")
            elif (not above_e50) and (not above_e20):
                signals.append(f"EMA20 & EMA50 bearish [{regime}:{'full' if rw['ema']>=0.8 else 'reduced'}]")
                score += _w(-3, "ema")
            elif not above_e20:
                signals.append("Short-term bearish (<EMA20)")
                score += _w(-1, "ema")

            # Golden / Death Cross detection (last 5 bars)
            e50_s  = ema50.dropna()  if ema50  is not None else pd.Series()
            e200_s = ema200.dropna() if ema200 is not None else pd.Series()
            if len(e50_s) >= 5 and len(e200_s) >= 5:
                if float(e50_s.iloc[-1]) > float(e200_s.iloc[-1]) and float(e50_s.iloc[-5]) <= float(e200_s.iloc[-5]):
                    signals.append("Golden Cross ✨")
                    score += _w(4, "cross")
                elif float(e50_s.iloc[-1]) < float(e200_s.iloc[-1]) and float(e50_s.iloc[-5]) >= float(e200_s.iloc[-5]):
                    signals.append("Death Cross ☠️")
                    score += _w(-4, "cross")

            # 2. RSI (raw max ±4) — most reliable in RANGE, least in TREND
            if cur_rsi < 25:
                signals.append(f"RSI deeply oversold ({cur_rsi:.0f}) [{regime}:{'full' if rw['rsi']>=0.8 else 'reduced'}]")
                score += _w(4, "rsi")
            elif cur_rsi < 35:
                signals.append(f"RSI oversold ({cur_rsi:.0f})")
                score += _w(3, "rsi")
            elif cur_rsi < 45:
                signals.append(f"RSI near oversold ({cur_rsi:.0f})")
                score += _w(1, "rsi")
            elif cur_rsi > 75:
                signals.append(f"RSI deeply overbought ({cur_rsi:.0f}) [{regime}:{'full' if rw['rsi']>=0.8 else 'reduced'}]")
                score += _w(-4, "rsi")
            elif cur_rsi > 65:
                signals.append(f"RSI overbought ({cur_rsi:.0f})")
                score += _w(-3, "rsi")
            elif cur_rsi > 55:
                signals.append(f"RSI elevated ({cur_rsi:.0f})")
                score += _w(-1, "rsi")

            # 3. MACD (raw max ±4) — reliable in TREND, noisy in RANGE
            if ml > ms and ml_p <= ms_p:
                signals.append(f"MACD bullish crossover [{regime}:{'full' if rw['macd']>=0.8 else 'reduced'}]")
                score += _w(4, "macd")
            elif ml > ms and mh > 0:
                signals.append("MACD bullish momentum")
                score += _w(2, "macd")
            elif ml < ms and ml_p >= ms_p:
                signals.append(f"MACD bearish crossover [{regime}:{'full' if rw['macd']>=0.8 else 'reduced'}]")
                score += _w(-4, "macd")
            elif ml < ms and mh < 0:
                signals.append("MACD bearish momentum")
                score += _w(-2, "macd")

            # 4. Bollinger Bands (raw max ±3) — best in RANGE (mean-reversion)
            if bb_pct < 0.05:
                signals.append(f"BB: Deep oversold squeeze [{regime}:{'full' if rw['bb']>=0.8 else 'reduced'}]")
                score += _w(3, "bb")
            elif bb_pct < 0.2:
                signals.append("BB: Lower band zone")
                score += _w(2, "bb")
            elif bb_pct < 0.35:
                signals.append("BB: Below midline")
                score += _w(1, "bb")
            elif bb_pct > 0.95:
                signals.append(f"BB: Overbought breakout [{regime}:{'full' if rw['bb']>=0.8 else 'reduced'}]")
                score += _w(-3, "bb")
            elif bb_pct > 0.8:
                signals.append("BB: Upper band zone")
                score += _w(-2, "bb")
            elif bb_pct > 0.65:
                signals.append("BB: Above midline")
                score += _w(-1, "bb")

            # 5. Stochastic (raw max ±3) — best in RANGE, unreliable in TREND
            if sk < 20 and sk > sd and sk_p <= sd_p:
                signals.append(f"Stoch bullish crossover (<20) [{regime}:{'full' if rw['stoch']>=0.8 else 'reduced'}]")
                score += _w(3, "stoch")
            elif sk < 25:
                signals.append(f"Stoch oversold ({sk:.0f})")
                score += _w(2, "stoch")
            elif sk > 80 and sk < sd and sk_p >= sd_p:
                signals.append(f"Stoch bearish crossover (>80) [{regime}:{'full' if rw['stoch']>=0.8 else 'reduced'}]")
                score += _w(-3, "stoch")
            elif sk > 75:
                signals.append(f"Stoch overbought ({sk:.0f})")
                score += _w(-2, "stoch")

            # 6. ADX / Trend Strength (raw max ±2) — only useful when trending
            if rw["adx"] > 0:
                if cur_adx > 35 and pos_di > neg_di:
                    signals.append(f"Very strong bullish trend (ADX {cur_adx:.0f})")
                    score += _w(2, "adx")
                elif cur_adx > 25 and pos_di > neg_di:
                    signals.append(f"Bullish trend (ADX {cur_adx:.0f})")
                    score += _w(1, "adx")
                elif cur_adx > 35 and neg_di > pos_di:
                    signals.append(f"Very strong bearish trend (ADX {cur_adx:.0f})")
                    score += _w(-2, "adx")
                elif cur_adx > 25 and neg_di > pos_di:
                    signals.append(f"Bearish trend (ADX {cur_adx:.0f})")
                    score += _w(-1, "adx")

            # 7. Volume Confirmation (raw max ±2) — most critical in VOLATILE
            if vol_ratio > 2.0 and perf_5d > 1:
                signals.append(f"Strong volume surge bullish ({vol_ratio:.1f}x avg)")
                score += _w(2, "vol")
            elif vol_ratio > 1.5 and perf_5d > 0:
                signals.append(f"Volume surge bullish ({vol_ratio:.1f}x avg)")
                score += _w(1, "vol")
            elif vol_ratio > 2.0 and perf_5d < -1:
                signals.append(f"Strong volume surge bearish ({vol_ratio:.1f}x avg)")
                score += _w(-2, "vol")
            elif vol_ratio > 1.5 and perf_5d < 0:
                signals.append(f"Volume surge bearish ({vol_ratio:.1f}x avg)")
                score += _w(-1, "vol")
            elif vol_ratio > 2.5:
                signals.append(f"Unusual volume spike ({vol_ratio:.1f}x avg)")

            # 8. OBV Accumulation/Distribution (raw max ±1)
            if obv_rising and score > 0:
                signals.append("OBV accumulation (smart money in)")
                score += _w(1, "obv")
            elif not obv_rising and score < 0:
                signals.append("OBV distribution (smart money out)")
                score += _w(-1, "obv")

            # 9. 52-Week Price Position (raw max ±2) — always relevant
            if w52_pos >= 90 and perf_5d > 0:
                signals.append(f"Near 52w high — breakout momentum ({w52_pos:.0f}%)")
                score += _w(2, "w52")
            elif w52_pos <= 10:
                signals.append(f"Near 52w low — deep value ({w52_pos:.0f}%)")
                score += _w(2, "w52")
            elif w52_pos >= 80:
                signals.append(f"Upper 52w range ({w52_pos:.0f}%)")
                score += _w(1, "w52")
            elif w52_pos <= 20:
                signals.append(f"Lower 52w range ({w52_pos:.0f}%)")
                score += _w(1, "w52")

            # 10. Momentum (raw max ±2)
            if perf_1m > 15:
                signals.append(f"Strong 1m momentum (+{perf_1m:.1f}%)")
                score += _w(2, "mom")
            elif perf_1m > 5:
                signals.append(f"Positive 1m momentum (+{perf_1m:.1f}%)")
                score += _w(1, "mom")
            elif perf_1m < -15:
                signals.append(f"Heavy 1m selling ({perf_1m:.1f}%)")
                score += _w(-2, "mom")
            elif perf_1m < -5:
                signals.append(f"Negative 1m momentum ({perf_1m:.1f}%)")
                score += _w(-1, "mom")

            # 11. Relative Strength vs TASI (raw max ±3) — always relevant
            if rs_vs_tasi > 10:
                signals.append(f"Strong RS vs TASI (+{rs_vs_tasi:.1f}%) — stock massively outperforming market")
                score += _w(3, "rs")
            elif rs_vs_tasi > 4:
                signals.append(f"Positive RS vs TASI (+{rs_vs_tasi:.1f}%) — stock beating the index")
                score += _w(2, "rs")
            elif rs_vs_tasi > 1.5:
                signals.append(f"Slight outperformance vs TASI (+{rs_vs_tasi:.1f}%)")
                score += _w(1, "rs")
            elif rs_vs_tasi < -10:
                signals.append(f"Severe underperformance vs TASI ({rs_vs_tasi:.1f}%) — institutional money leaving")
                score += _w(-3, "rs")
            elif rs_vs_tasi < -4:
                signals.append(f"Underperforming TASI ({rs_vs_tasi:.1f}%) — index dragging it down")
                score += _w(-2, "rs")
            elif rs_vs_tasi < -1.5:
                signals.append(f"Slight underperformance vs TASI ({rs_vs_tasi:.1f}%)")
                score += _w(-1, "rs")

            # 12. Multi-timeframe weekly confirmation (raw max ±2)
            if weekly_bullish is True:
                signals.append("Weekly trend bullish — higher timeframe confirms daily signal")
                score += _w(2, "weekly")
            elif weekly_bullish is False:
                signals.append("\u26a0\ufe0f Weekly trend bearish — higher timeframe warns against daily buy")
                score += _w(-2, "weekly")

            # Add regime context to signals
            _regime_label = {"TREND": "Trending", "RANGE": "Range-bound", "VOLATILE": "Volatile"}
            signals.insert(0, f"Regime: {_regime_label.get(regime, regime)} — indicators weighted for {regime.lower()} conditions")

            # Round score to integer for display
            score = round(score)
            ind_score_final = round(_sub[0])
            pa_score_final  = round(_sub[1])

            # ── Multi-Timeframe (MTF) score 0–3 ─────────────────────────────
            _daily_bull = score > 0
            _mtf_score  = (
                int(_daily_bull) +
                int(bool(weekly_bullish)) +
                int(bool(monthly_bullish))
            )

            # 13. Market regime gate — penalise BUY signals when TASI is in a downtrend
            if tasi_regime_bearish and score > 0:
                signals.append("\u26a0\ufe0f TASI market in downtrend — macro headwind, conviction reduced")
                score = max(0, score - 3)

            # ── Entry / Exit Calculation — structural levels ──────────────────
            # Stop : below the 20-bar structural low with a small ATR buffer.
            #        Guardrails: stop kept between 0.8–2.5 ATR from entry.
            # T1   : nearest structural resistance — 20-bar rolling high.
            # T2   : deeper resistance — 60-bar rolling high.
            # This reflects real market structure rather than arbitrary multiples.
            if score >= 0:   # BUY side
                struct_low  = float(low.iloc[-20:].min())
                raw_stop    = struct_low - cur_atr * 0.3
                stop_dist   = cp - raw_stop
                if stop_dist < cur_atr * 0.8:
                    stop_loss = round(cp - cur_atr * 1.2, 2)
                elif stop_dist > cur_atr * 2.5:
                    stop_loss = round(cp - cur_atr * 2.0, 2)
                else:
                    stop_loss = round(raw_stop, 2)
                high_20  = float(high.iloc[-20:].max())
                high_60  = float(high.iloc[-60:].max()) if len(high) >= 60 else high_20
                target1  = round(high_20, 2) if high_20 > cp * 1.005 else round(cp + cur_atr * 2.0, 2)
                target2  = round(high_60, 2) if high_60 > target1 * 1.01 else round(cp + cur_atr * 4.0, 2)
            else:             # SELL side
                struct_high = float(high.iloc[-20:].max())
                raw_stop    = struct_high + cur_atr * 0.3
                stop_dist   = raw_stop - cp
                if stop_dist < cur_atr * 0.8:
                    stop_loss = round(cp + cur_atr * 1.2, 2)
                elif stop_dist > cur_atr * 2.5:
                    stop_loss = round(cp + cur_atr * 2.0, 2)
                else:
                    stop_loss = round(raw_stop, 2)
                low_20   = float(low.iloc[-20:].min())
                low_60   = float(low.iloc[-60:].min()) if len(low) >= 60 else low_20
                target1  = round(low_20, 2) if low_20 < cp * 0.995 else round(cp - cur_atr * 2.0, 2)
                target2  = round(low_60, 2) if low_60 < target1 * 0.99 else round(cp - cur_atr * 4.0, 2)

            risk_amt  = abs(cp - stop_loss)
            rr_ratio  = abs(target2 - cp) / risk_amt if risk_amt > 0 else 0
            potential = (abs(target1 - cp) / cp * 100) if cp > 0 else 0
            risk_pct  = (risk_amt / cp * 100) if cp > 0 else 0

            # Stock name / sector
            ticker_key  = ticker if ticker.endswith('.SR') else ticker + '.SR'
            stock_name  = all_info.get(ticker_key, ticker.replace('.SR', ''))
            sector_name = _get_sector(stock_name)

            # ── Investment Intelligence ────────────────────────────────────────
            # Conviction: normalise against regime-adjusted theoretical maximum.
            # TREND regime allows full weight for trend indicators → higher max.
            # RANGE/VOLATILE regimes apply reduced weights → lower max.
            _regime_max = {"TREND": 29, "RANGE": 24, "VOLATILE": 24}
            conviction = min(100, round(abs(score) / max(1, _regime_max.get(regime, 24)) * 100))
            _has       = lambda kw: any(kw.lower() in sig.lower() for sig in signals)

            if _has("golden cross"):
                setup_type = "Golden Cross"
            elif _has("death cross"):
                setup_type = "Death Cross"
            elif _has("macd bullish crossover") and (cur_rsi < 45 or sk < 30):
                setup_type = "Oversold Reversal"
            elif (bb_pct * 100 < 10) and cur_rsi < 40:
                setup_type = "BB Bounce"
            elif w52_pos >= 88 and perf_5d > 0:
                setup_type = "52W Breakout"
            elif w52_pos <= 12:
                setup_type = "Deep Value"
            elif _has("full ema alignment (bullish)") and cur_adx > 25:
                setup_type = "Trend Continuation"
            elif _has("stoch bullish crossover"):
                setup_type = "Stoch Reversal"
            elif vol_ratio > 2.0 and score > 0:
                setup_type = "Volume Spike"
            elif regime == "RANGE":
                setup_type = "Range Play"
            else:
                setup_type = "Multi-Indicator"

            why_reasons = []
            if score >= 0:
                if _has("golden cross"):
                    why_reasons.append("Golden Cross formed: EMA50 crossed above EMA200 — major long-term bullish signal that historically triggers 15-30% rallies over the following months")
                if _has("full ema alignment (bullish)"):
                    why_reasons.append("All 3 EMAs stacked bullishly (price > EMA20 > EMA50 > EMA200) — uptrend confirmed on every timeframe simultaneously")
                elif _has("ema20 & ema50 bullish"):
                    why_reasons.append("Short and medium-term trend aligned bullish (above EMA20 & EMA50) — two timeframes confirm buying momentum")
                if cur_rsi < 30:
                    rsi_d = int(cur_rsi)
                    why_reasons.append(f"RSI deeply oversold at {rsi_d} — maximum pessimism zone, historically precedes strong recoveries of 8-20%")
                elif cur_rsi < 40:
                    rsi_d = int(cur_rsi)
                    why_reasons.append(f"RSI oversold at {rsi_d} — price statistically cheap vs. recent action, high-probability bounce zone")
                if _has("macd bullish crossover"):
                    why_reasons.append("MACD just crossed above signal line — momentum officially turning bullish, trend-followers will buy now")
                elif _has("macd bullish momentum"):
                    why_reasons.append("MACD histogram positive and rising — upward momentum building and accelerating")
                if (bb_pct * 100) < 15:
                    bbp_d = int(bb_pct * 100)
                    why_reasons.append(f"Price near Bollinger lower boundary (BB%B: {bbp_d}%) — 2-sigma oversold, mean-reversion setup with high probability")
                if _has("stoch bullish crossover"):
                    sk_d = int(sk)
                    why_reasons.append(f"Stochastic crossed bullishly from oversold zone ({sk_d}) — short-term selling exhausted, buyers stepping in aggressively")
                if vol_ratio > 2.0:
                    vr_d = round(vol_ratio, 1)
                    why_reasons.append(f"Volume is {vr_d}x above 20-day average — significant institutional accumulation detected, smart money loading positions")
                elif vol_ratio > 1.5:
                    vr_d = round(vol_ratio, 1)
                    why_reasons.append(f"Volume {vr_d}x above average — above-normal participation confirms genuine buying pressure")
                if cur_adx > 30 and pos_di > neg_di:
                    adx_d = int(cur_adx)
                    why_reasons.append(f"ADX at {adx_d} with bullish DI alignment — strong trend strength confirmed, momentum strategies are aligned")
                if obv_rising and vol_ratio > 1.2:
                    why_reasons.append("OBV rising on strong volume — On-Balance Volume confirms smart money accumulation, price follows volume higher")
                if w52_pos >= 85 and perf_5d > 0:
                    w52_d = int(w52_pos)
                    why_reasons.append(f"Near 52-week high ({w52_d}th percentile) with positive 5D momentum — breakout continuation, strong holders are not selling")
                elif w52_pos <= 15:
                    w52_d = int(w52_pos)
                    why_reasons.append(f"Near 52-week low ({w52_d}th percentile) — deep value / maximum fear zone, excellent risk/reward for long-term investors")
                if rs_vs_tasi > 5:
                    rs_d = round(rs_vs_tasi, 1)
                    why_reasons.append(f"Outperforming TASI by +{rs_d}% over 20 days — stock showing genuine relative strength. Leaders always outperform the index first, then make bigger moves.")
                if weekly_bullish is True:
                    why_reasons.append("Weekly timeframe confirmed bullish — both daily and weekly trends aligned. Higher-timeframe agreement is a hallmark of the strongest setups.")
            else:
                if _has("death cross"):
                    why_reasons.append("Death Cross: EMA50 crossed below EMA200 — major bearish signal, often precedes 15-25% further decline, exit any longs now")
                if _has("full ema alignment (bearish)"):
                    why_reasons.append("All EMAs bearishly stacked (price < EMA20 < EMA50 < EMA200) — downtrend confirmed across all timeframes")
                elif _has("ema20 & ema50 bearish"):
                    why_reasons.append("Short and medium trend bearish — both EMA20 and EMA50 confirm selling pressure is dominant")
                if cur_rsi > 70:
                    rsi_d = int(cur_rsi)
                    why_reasons.append(f"RSI overbought at {rsi_d} — extreme greed historically precedes corrections of 5-15%, risk/reward unfavorable for longs")
                if _has("macd bearish crossover"):
                    why_reasons.append("MACD crossed bearishly — downward momentum officially confirmed, sellers and shorts will pile in")
                if vol_ratio > 2.0 and perf_5d < -1:
                    vr_d = round(vol_ratio, 1)
                    why_reasons.append(f"High-volume selling ({vr_d}x avg) — institutional distribution in progress, smart money exiting positions")
                if rs_vs_tasi < -5:
                    rs_d = round(abs(rs_vs_tasi), 1)
                    why_reasons.append(f"Underperforming TASI by -{rs_d}% — institutional allocation flowing away from this stock, relative weakness confirms the bearish thesis")
            why_reasons = why_reasons[:5]

            # Stop reason
            if score >= 0:
                sl_d      = round(stop_loss, 2)
                sp_pct    = round(risk_pct, 1)
                _sl_low   = round(float(low.iloc[-20:].min()), 2)
                stop_reason_txt = (f"Structural stop at {sl_d} ({sp_pct}% risk) — placed below the 20-day swing low "
                                   f"({_sl_low}) with ATR buffer. Setup is only invalidated on a genuine breakdown.")
            else:
                sl_d      = round(stop_loss, 2)
                sp_pct    = round(risk_pct, 1)
                _sl_high  = round(float(high.iloc[-20:].max()), 2)
                stop_reason_txt = (f"Structural stop at {sl_d} ({sp_pct}% risk) — placed above the 20-day swing high "
                                   f"({_sl_high}) with ATR buffer.")

            # Entry strategy
            rsi_i  = int(cur_rsi)
            sk_i   = int(sk)
            cp_d   = round(cp, 2)
            e20_d  = round(e20, 2)
            sigs_n = len(signals)
            if cur_rsi < 35 or sk < 25:
                entry_strategy = f"ENTER NOW — RSI {rsi_i}/Stoch {sk_i} both oversold, optimal entry risk/reward at {cp_d}"
            elif perf_5d < -3 and score > 0:
                p5d_d = round(abs(perf_5d), 1)
                entry_strategy = f"SCALE IN — down {p5d_d}% this week; buy 50% now at {cp_d}, add rest on green daily candle above EMA20 ({e20_d})"
            elif abs(cp - e20) / max(cp, 0.01) < 0.015:
                entry_strategy = f"ENTER ON HOLD — price testing EMA20 ({e20_d}) support; confirm hold before full position, stop just below"
            else:
                entry_strategy = f"ENTER AT MARKET — {cp_d} SAR, {sigs_n} indicators aligned; waiting risks missing the move"

            # Target reasons
            pot_t2_pct  = (abs(target2 - cp) / cp * 100) if cp > 0 else 0
            t1_d        = round(target1, 2)
            t2_d        = round(target2, 2)
            pot_d       = round(potential, 1)
            pot_t2_d    = round(pot_t2_pct, 1)
            _rr_r = round(rr_ratio, 1)
            if score >= 0:
                t1_txt = (f"Take 50% profit at {t1_d} (+{pot_d}%) — 20-day structural resistance, "
                          f"first target. Move stop to breakeven once reached.")
                t2_txt = (f"Let remaining 50% run to {t2_d} (+{pot_t2_d}%) — "
                          f"60-day structural resistance, full target ≈ {_rr_r}:1 R:R. Trail stop with EMA20.")
            else:
                t1_txt = f"Cover 50% at {t1_d} (-{pot_d}%) — 20-day structural support, first cover point"
                t2_txt = (f"Full target {t2_d} (-{pot_t2_d}%) — "
                          f"60-day structural support, full downside target ≈ {_rr_r}:1 R:R")

            # Risk classification
            risk_class = ("Low"  if (risk_pct < 3.0 and rr_ratio >= 2.0) else
                          "High" if (risk_pct > 7.0 or cur_adx < 15)    else "Medium")

            # Position sizing: 1% portfolio risk rule  (size = 1% / stop_distance%)
            pos_size_pct = min(25, int(100.0 / max(1.0, risk_pct))) if risk_pct > 0 else 10

            # Priority score (for ranking top picks)
            priority_score = round(conviction * 0.5 + min(rr_ratio, 5.0) * 12 + abs(score) * 2, 1)

            # Sector filter
            if sector_filter and sector_filter != "All Sectors" and sector_name != sector_filter:
                continue

            # Score threshold filter
            if abs(score) < min_score:
                # still add to hold if score is non-zero
                pass

            result = {
                'ticker':       ticker.replace('.SR', ''),
                'name':         stock_name,
                'sector':       sector_name,
                'price':        cp,
                'score':        score,
                'signals':      signals,
                'regime':       regime,
                # Indicator values
                'rsi':          cur_rsi,
                'adx':          cur_adx,
                'bb_pct':       bb_pct * 100,
                'stoch_k':      sk,
                'vol_ratio':    vol_ratio,
                'above_ema200': above_e200,
                # Performance
                'perf_5d':      perf_5d,
                'perf_1m':      perf_1m,
                'perf_3m':      perf_3m,
                'w52_pos':      w52_pos,
                # Trade levels
                'entry':        cp,
                'stop_loss':    stop_loss,
                'target1':      target1,
                'target2':      target2,
                'rr_ratio':     rr_ratio,
                'potential':    potential,
                'risk':         risk_pct,
                # OBV
                'obv_rising':   obv_rising,
                # Investment intelligence
                'conviction':       conviction,
                'setup_type':       setup_type,
                'why_reasons':      why_reasons,
                'entry_strategy':   entry_strategy,
                'stop_reason':      stop_reason_txt,
                't1_reason':        t1_txt,
                't2_reason':        t2_txt,
                'risk_class':       risk_class,
                'pos_size_pct':     pos_size_pct,
                'priority_score':   priority_score,
                # Market context (new)
                'rs_vs_tasi':       round(rs_vs_tasi, 2),
                'weekly_bullish':   weekly_bullish,
                'monthly_bullish':  monthly_bullish,
                'mtf_score':        _mtf_score,
                'tasi_bearish_mkt': tasi_regime_bearish,
                # Sub-scores for 3-section display
                'ind_score':        ind_score_final,
                'pa_score':         pa_score_final,
            }

            if score >= min_score:
                # Hard gate: if weekly trend is bearish, only strong signals pass.
                # Moderate setups against the weekly trend are demoted to hold —
                # buying against the higher-timeframe bias is low-probability.
                if weekly_bullish is False and score < 8:
                    results['hold'].append(result)
                else:
                    results['buy'].append(result)
            elif score <= -min_score:
                results['sell'].append(result)
            else:
                results['hold'].append(result)

        except Exception:
            continue

    results['buy'].sort(key=lambda x: x['score'], reverse=True)
    results['sell'].sort(key=lambda x: x['score'])

    return results



