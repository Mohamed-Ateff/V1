import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import math
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


@st.cache_data(ttl=300, show_spinner=False)
def _cached_download(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    """Cached yfinance download with retry — Yahoo/curl_cffi can fail on first attempt."""
    for _attempt in range(3):
        try:
            df = yf.download(symbol, start=start, end=end, progress=False)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except Exception:
            pass
    return None


def _drop_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep the first copy of each column name so row.get() returns scalars, not Series."""
    if df.columns.is_unique:
        return df

    keep_positions = []
    seen = set()
    for pos, col in enumerate(df.columns):
        name = str(col)
        if name in seen:
            continue
        seen.add(name)
        keep_positions.append(pos)
    return df.iloc[:, keep_positions].copy()


def _coerce_scalar(value, default):
    """Collapse duplicated-column lookups to one scalar value."""
    if isinstance(value, pd.DataFrame):
        if value.empty:
            return default
        value = value.iloc[0, 0]
    elif isinstance(value, pd.Series):
        if value.empty:
            return default
        value = value.iloc[0]

    try:
        if value is None or pd.isna(value):
            return default
    except Exception:
        return default

    return value


def _first_series(df: pd.DataFrame, col_name: str) -> pd.Series | None:
    """Return the first matching column as a Series even if duplicates exist."""
    matches = [col for col in df.columns if str(col) == col_name]
    if not matches:
        return None
    series = df.loc[:, matches[0]]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return pd.to_numeric(series, errors='coerce')


def _add_regime_core_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the minimum indicator set required for stable regime detection."""
    df = df.copy()

    df['EMA_20'] = ta.ema(df['Close'], length=20)
    df['EMA_200'] = ta.ema(df['Close'], length=200)
    df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

    bbands = ta.bbands(df['Close'], length=20)
    if bbands is not None:
        df = pd.concat([df, bbands], axis=1)

    adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    if adx is not None:
        df = pd.concat([df, adx], axis=1)

    return _drop_duplicate_columns(df)


class RegimeAnalyzer:

    """Backend analyzer for web interface."""

    

    def __init__(self, symbol, start_date, end_date, selected_indicators):

        self.symbol = symbol

        self.start_date = start_date

        self.requested_start_date = start_date

        self.end_date = end_date

        self.requested_end_date = end_date

        self.selected_indicators = selected_indicators

        self.df = None

        

    def download_data(self):

        """Download and prepare data."""

        try:

            _requested_start = datetime.strptime(self.requested_start_date, '%Y-%m-%d')

            _download_start = max(datetime(2002, 1, 1), _requested_start - timedelta(days=420))

            _end_exclusive = (datetime.strptime(self.end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

            df = _cached_download(self.symbol, _download_start.strftime('%Y-%m-%d'), _end_exclusive)

        except Exception as e:

            print(f"Download error for {self.symbol}: {e}")

            return None

        

        if df is None or len(df) == 0:

            return None

        df = df.copy()  # don't mutate the cached object

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = df.columns.get_level_values(0)

        df.columns = [str(col).strip() for col in df.columns]

        

        # Ensure we have the required columns

        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

        for col in required_cols:

            if col not in df.columns:

                return None

        # Regime detection must not depend on whatever optional indicators the user selected.
        # Always compute the core features needed by classify_regimes().
        df = _add_regime_core_indicators(df)

        

        # Add indicators based on selection



        # ?? 1?? Trend (Direction) ??????????????????????????????????????????

        if 'EMA' in self.selected_indicators:

            df['EMA_20'] = ta.ema(df['Close'], length=20)

            df['EMA_50'] = ta.ema(df['Close'], length=50)

            df['EMA_200'] = ta.ema(df['Close'], length=200)



        if 'SMA' in self.selected_indicators:

            df['SMA_50'] = ta.sma(df['Close'], length=50)

            df['SMA_200'] = ta.sma(df['Close'], length=200)



        if 'Parabolic SAR' in self.selected_indicators:

            psar = ta.psar(df['High'], df['Low'], df['Close'])

            if psar is not None:

                df = pd.concat([df, psar], axis=1)



        if 'Ichimoku' in self.selected_indicators:

            try:

                ichi_df, _ = ta.ichimoku(df['High'], df['Low'], df['Close'])

                if ichi_df is not None:

                    df = pd.concat([df, ichi_df], axis=1)

            except Exception:

                pass



        if 'WMA' in self.selected_indicators:

            df['WMA_20'] = ta.wma(df['Close'], length=20)



        # ?? 2?? Momentum (Entry Timing) ???????????????????????????????????

        if 'RSI' in self.selected_indicators:

            df['RSI_14'] = ta.rsi(df['Close'], length=14)



        if 'MACD' in self.selected_indicators:

            macd = ta.macd(df['Close'])

            if macd is not None:

                df = pd.concat([df, macd], axis=1)



        if 'Stochastic' in self.selected_indicators:

            stoch = ta.stoch(df['High'], df['Low'], df['Close'])

            if stoch is not None:

                df = pd.concat([df, stoch], axis=1)



        if 'ROC' in self.selected_indicators:

            df['ROC_12'] = ta.roc(df['Close'], length=12)



        if 'CCI' in self.selected_indicators:

            df['CCI_20'] = ta.cci(df['High'], df['Low'], df['Close'], length=20)



        if 'Williams %R' in self.selected_indicators:

            df['WILLR_14'] = ta.willr(df['High'], df['Low'], df['Close'], length=14)



        # ?? 3?? Volatility (Breakouts & Risk) ????????????????????????????

        if 'Bollinger Bands' in self.selected_indicators:

            bbands = ta.bbands(df['Close'], length=20)

            if bbands is not None:

                df = pd.concat([df, bbands], axis=1)



        if 'ATR' in self.selected_indicators:

            df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)



        if 'Keltner Channel' in self.selected_indicators:

            kc = ta.kc(df['High'], df['Low'], df['Close'])

            if kc is not None:

                df = pd.concat([df, kc], axis=1)



        if 'Donchian Channel' in self.selected_indicators:

            dc = ta.donchian(df['High'], df['Low'], length=20)

            if dc is not None:

                df = pd.concat([df, dc], axis=1)

        # ?? 4?? Volume (Smart Money Confirmation) ?????????????????????????

        if 'OBV' in self.selected_indicators:

            df['OBV'] = ta.obv(df['Close'], df['Volume'])



        if 'MFI' in self.selected_indicators:

            df['MFI_14'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=14)



        if 'CMF' in self.selected_indicators:

            df['CMF_20'] = ta.cmf(df['High'], df['Low'], df['Close'], df['Volume'], length=20)



        if 'VWAP' in self.selected_indicators:

            try:

                # Ensure index is a sorted DatetimeIndex for VWAP calculation

                if isinstance(df.index, pd.DatetimeIndex):

                    df_sorted = df.sort_index()

                    df['VWAP'] = pd.to_numeric(

                        ta.vwap(df_sorted['High'], df_sorted['Low'], df_sorted['Close'], df_sorted['Volume']),

                        errors='coerce'

                    )

            except Exception:

                pass



        # ?? 5?? Trend Strength (Regime Detection) ?????????????????????????

        if 'ADX' in self.selected_indicators:

            adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)

            if adx is not None:

                df = pd.concat([df, adx], axis=1)

        # ── NEW: Trend indicators ──────────────────────────────────────────
        if 'SuperTrend' in self.selected_indicators:
            try:
                st_df = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3.0)
                if st_df is not None:
                    df = pd.concat([df, st_df], axis=1)
            except Exception:
                pass

        if 'Hull MA' in self.selected_indicators:
            df['HMA_20'] = ta.hma(df['Close'], length=20)

        # ── NEW: Momentum indicators ──────────────────────────────────────
        if 'Momentum' in self.selected_indicators:
            df['MOM_10'] = ta.mom(df['Close'], length=10)

        if 'TSI' in self.selected_indicators:
            try:
                tsi = ta.tsi(df['Close'])
                if tsi is not None:
                    df = pd.concat([df, tsi], axis=1)
            except Exception:
                pass

        if 'PPO' in self.selected_indicators:
            try:
                ppo = ta.ppo(df['Close'])
                if ppo is not None:
                    df = pd.concat([df, ppo], axis=1)
            except Exception:
                pass

        if 'Elder Ray' in self.selected_indicators:
            _ema13 = ta.ema(df['Close'], length=13)
            if _ema13 is not None:
                df['ELDER_BULL'] = df['High'] - _ema13
                df['ELDER_BEAR'] = df['Low']  - _ema13

        # ── NEW: Volume indicators ─────────────────────────────────────────
        if 'A/D Line' in self.selected_indicators:
            try:
                df['ADL'] = ta.ad(df['High'], df['Low'], df['Close'], df['Volume'])
            except Exception:
                pass

        if 'Volume MA' in self.selected_indicators:
            df['VOL_MA_20'] = df['Volume'].rolling(window=20).mean()

        if 'Force Index' in self.selected_indicators:
            df['FORCE_2']  = ta.efi(df['Close'], df['Volume'], length=2)
            df['FORCE_13'] = ta.efi(df['Close'], df['Volume'], length=13)

        if 'Volume RSI' in self.selected_indicators:
            df['VOL_RSI_14'] = ta.rsi(df['Volume'].astype(float), length=14)

        # ── NEW: Volatility indicators ─────────────────────────────────────
        if 'Squeeze Momentum' in self.selected_indicators:
            try:
                sqz = ta.squeeze(df['High'], df['Low'], df['Close'], df['Volume'])
                if sqz is not None:
                    df = pd.concat([df, sqz], axis=1)
            except Exception:
                pass

        if 'Historical Volatility' in self.selected_indicators:
            df['HIST_VOL_20'] = df['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100

        if 'Standard Deviation' in self.selected_indicators:
            df['STDDEV_20'] = df['Close'].rolling(20).std()

        if 'Chandelier Exit' in self.selected_indicators:
            try:
                _atr22 = ta.atr(df['High'], df['Low'], df['Close'], length=22)
                if _atr22 is not None:
                    df['CHANDELIER_LONG']  = df['High'].rolling(22).max() - 3 * _atr22
                    df['CHANDELIER_SHORT'] = df['Low'].rolling(22).min()  + 3 * _atr22
            except Exception:
                pass

        # ── NEW: Support & Resistance ──────────────────────────────────────
        if 'Pivot Points' in self.selected_indicators:
            df['PIVOT']   = (df['High'] + df['Low'] + df['Close']) / 3
            df['PIVOT_R1'] = 2 * df['PIVOT'] - df['Low']
            df['PIVOT_S1'] = 2 * df['PIVOT'] - df['High']

        if 'Fibonacci Levels' in self.selected_indicators:
            _roll_high = df['High'].rolling(50).max()
            _roll_low  = df['Low'].rolling(50).min()
            _fib_range = _roll_high - _roll_low
            df['FIB_382'] = _roll_high - 0.382 * _fib_range
            df['FIB_500'] = _roll_high - 0.500 * _fib_range
            df['FIB_618'] = _roll_high - 0.618 * _fib_range

        if 'VWAP Bands' in self.selected_indicators:
            try:
                _vwap_raw = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
                if _vwap_raw is not None:
                    _tp_std = ((df['High'] + df['Low'] + df['Close']) / 3).rolling(20).std()
                    df['VWAP_UPPER1'] = _vwap_raw + 1 * _tp_std
                    df['VWAP_LOWER1'] = _vwap_raw - 1 * _tp_std
                    df['VWAP_UPPER2'] = _vwap_raw + 2 * _tp_std
                    df['VWAP_LOWER2'] = _vwap_raw - 2 * _tp_std
            except Exception:
                pass

        if 'Prev High/Low' in self.selected_indicators:
            df['PREV_HIGH'] = df['High'].shift(1)
            df['PREV_LOW']  = df['Low'].shift(1)

        if 'Swing High/Low' in self.selected_indicators:
            _n = 5
            df['SWING_HIGH'] = df['High'].where(
                df['High'] == df['High'].rolling(_n * 2 + 1, center=True).max())
            df['SWING_LOW'] = df['Low'].where(
                df['Low'] == df['Low'].rolling(_n * 2 + 1, center=True).min())

        # ── NEW: Mean Reversion indicators ────────────────────────────────
        if 'RSI Extremes' in self.selected_indicators:
            if 'RSI_14' not in df.columns:
                df['RSI_14'] = ta.rsi(df['Close'], length=14)

        if 'BB Z-Score' in self.selected_indicators:
            _bb_mid = df['Close'].rolling(20).mean()
            _bb_std = df['Close'].rolling(20).std()
            df['BB_ZSCORE'] = (df['Close'] - _bb_mid) / _bb_std.replace(0, np.nan)

        if 'Distance from MA' in self.selected_indicators:
            _ma50 = ta.sma(df['Close'], length=50)
            if _ma50 is not None:
                df['DIST_MA_PCT'] = (df['Close'] - _ma50) / _ma50.replace(0, np.nan) * 100

        if 'Stochastic Extreme' in self.selected_indicators:
            if 'STOCHk_14_3_3' not in df.columns:
                _stoch = ta.stoch(df['High'], df['Low'], df['Close'])
                if _stoch is not None:
                    df = pd.concat([df, _stoch], axis=1)

        if 'CCI Extreme' in self.selected_indicators:
            if 'CCI_20' not in df.columns:
                df['CCI_20'] = ta.cci(df['High'], df['Low'], df['Close'], length=20)

        # ── NEW: Market Regime & Breadth ──────────────────────────────────
        if 'TASI Filter' in self.selected_indicators or 'Sector Filter' in self.selected_indicators:
            try:
                _tasi = _cached_download('TASI.SR', _download_start.strftime('%Y-%m-%d'), _end_exclusive)
                if _tasi is not None and not _tasi.empty:
                    if isinstance(_tasi.columns, pd.MultiIndex):
                        _tasi.columns = _tasi.columns.get_level_values(0)
                    _tasi = _tasi.reset_index()
                    _tasi.columns = [str(c).strip() for c in _tasi.columns]
                    _tasi_close = pd.to_numeric(_tasi['Close'], errors='coerce')
                    _tasi_ema50 = _tasi_close.ewm(span=50, adjust=False).mean()
                    df['TASI_ABOVE_EMA50'] = (_tasi_close.values[:len(df)] > _tasi_ema50.values[:len(df)]).astype(int) if len(_tasi_close) >= len(df) else 0
            except Exception:
                df['TASI_ABOVE_EMA50'] = 1

        if 'RS vs TASI' in self.selected_indicators:
            try:
                _tasi2 = _cached_download('TASI.SR', _download_start.strftime('%Y-%m-%d'), _end_exclusive)
                if _tasi2 is not None and not _tasi2.empty:
                    if isinstance(_tasi2.columns, pd.MultiIndex):
                        _tasi2.columns = _tasi2.columns.get_level_values(0)
                    _tasi2 = _tasi2.reset_index()
                    _tasi_c = pd.to_numeric(_tasi2['Close'], errors='coerce')
                    _min_len = min(len(df), len(_tasi_c))
                    _stock_ret = df['Close'].iloc[:_min_len].pct_change(20)
                    _tasi_ret  = _tasi_c.iloc[:_min_len].pct_change(20)
                    df['RS_TASI'] = (_stock_ret.values - _tasi_ret.values)
            except Exception:
                pass

        df = _drop_duplicate_columns(df)

        

# Replace None indicator columns with NaN so comparisons don't crash
        for col in df.columns:
            if col in ['Date']:
                continue
            try:
                if df[col].dtype == object or df[col].isnull().all():
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass

        # Only drop rows with missing core price data, keep others for partial indicators

        df = df.dropna(subset=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

        df.reset_index(drop=True, inplace=True)

        

        self.df = df

        return df

    

    def classify_regimes(self, lookback=30, adx_threshold=25, atr_threshold=0.03):

        """Classify regimes."""

        if self.df is None or len(self.df) == 0:
            return self.df

        effective_lookback = min(lookback, max(len(self.df) - 1, 1))

        regimes = []

        

        for i in range(effective_lookback, len(self.df)):

            recent = self.df.iloc[i-effective_lookback:i+1]
            row = self.df.iloc[i]

            

            price = float(_coerce_scalar(row.get('Close', np.nan), np.nan))

            ema200 = float(_coerce_scalar(row.get('EMA_200', price), price))

            adx = float(_coerce_scalar(row.get('ADX_14', 20), 20))

            atr = float(_coerce_scalar(row.get('ATR_14', 0), 0))

            bb_upper = float(_coerce_scalar(row.get('BBU_20_2.0', price * 1.02), price * 1.02))

            bb_lower = float(_coerce_scalar(row.get('BBL_20_2.0', price * 0.98), price * 0.98))

            

            recent_ema200 = _first_series(recent, 'EMA_200')
            if recent_ema200 is not None and recent_ema200.notna().any():
                close_series = pd.to_numeric(recent['Close'], errors='coerce')
                above_ema200 = (close_series > recent_ema200.fillna(price)).sum() / len(recent)
            else:
                above_ema200 = 0.5

            try:
                ema20_now = float(_coerce_scalar(row.get('EMA_20', None), np.nan))
                ema20_prev = float(_coerce_scalar(self.df.iloc[i-10].get('EMA_20', None), np.nan)) if i >= 10 else np.nan
                if not math.isnan(ema20_now) and not math.isnan(ema20_prev) and ema20_prev != 0:
                    ema_slope = (ema20_now - ema20_prev) / ema20_prev
                else:
                    ema_slope = 0
            except Exception:
                ema_slope = 0

            atr_pct = (atr / price) if price > 0 and atr > 0 else 0.02

            bb_width = (bb_upper - bb_lower) / price if price > 0 else 0.05

            

            regime = "RANGE"

            

            if adx > adx_threshold and abs(ema_slope) > 0.015:
                # Clear directional momentum → TREND (regardless of ATR size)
                regime = "TREND"

            elif (atr_pct > atr_threshold or bb_width > 0.07) and adx < adx_threshold:
                # High volatility WITHOUT an established trend → choppy / VOLATILE
                regime = "VOLATILE"

            elif adx < 20 and atr_pct < 0.025:
                # Low ADX + tight ATR → quiet RANGE
                regime = "RANGE"

            

            regimes.append(regime)

        

        self.df = self.df.iloc[effective_lookback:].copy()

        self.df['REGIME'] = regimes

        requested_dates = pd.to_datetime(self.df['Date'], errors='coerce')
        try:
            if requested_dates.dt.tz is not None:
                requested_dates = requested_dates.dt.tz_localize(None)
        except Exception:
            pass
        try:
            requested_dates = requested_dates.dt.normalize()
        except Exception:
            pass

        requested_start = pd.Timestamp(self.requested_start_date).normalize()
        requested_end = pd.Timestamp(self.requested_end_date).normalize()

        visible_mask = (requested_dates >= requested_start) & (requested_dates <= requested_end)
        visible_df = self.df.loc[visible_mask].copy()
        fallback_gap_days = 5

        # If the user picked a weekend/holiday or a one-day window, snap to the nearest
        # recent trading bars instead of failing with an empty or one-row visible slice.
        if len(visible_df) == 0:
            fallback_mask = requested_dates.notna() & (requested_dates <= requested_end)
            fallback_df = self.df.loc[fallback_mask].copy()
            fallback_dates = requested_dates.loc[fallback_mask]
            if not fallback_df.empty:
                last_visible_date = fallback_dates.iloc[-1]
                gap_days = (requested_end - last_visible_date).days
                if 0 <= gap_days <= fallback_gap_days:
                    visible_df = fallback_df.tail(2).copy()
        elif len(visible_df) == 1:
            single_index = visible_df.index[0]
            single_date = requested_dates.loc[single_index]
            history_mask = requested_dates.notna() & (requested_dates <= single_date)
            history_df = self.df.loc[history_mask].copy()
            history_dates = requested_dates.loc[history_mask]
            if len(history_df) >= 2:
                gap_days = (single_date - history_dates.iloc[-2]).days
                if 0 <= gap_days <= fallback_gap_days:
                    visible_df = history_df.tail(2).copy()

        self.df = visible_df.copy()

        self.df.reset_index(drop=True, inplace=True)

        

        return self.df

