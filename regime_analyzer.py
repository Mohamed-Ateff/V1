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


class RegimeAnalyzer:

    """Backend analyzer for web interface."""

    

    def __init__(self, symbol, start_date, end_date, selected_indicators):

        self.symbol = symbol

        self.start_date = start_date

        self.end_date = end_date

        self.selected_indicators = selected_indicators

        self.df = None

        

    def download_data(self):

        """Download and prepare data."""

        try:

            _end_exclusive = (datetime.strptime(self.end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

            df = _cached_download(self.symbol, self.start_date, _end_exclusive)

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

        regimes = []

        

        for i in range(lookback, len(self.df)):

            recent = self.df.iloc[i-lookback:i+1]

            

            price = self.df.iloc[i]['Close']

            ema200 = self.df.iloc[i].get('EMA_200', price)
            if ema200 is None or (isinstance(ema200, float) and math.isnan(ema200)):
                ema200 = price

            adx = self.df.iloc[i].get('ADX_14', 20)
            if adx is None or (isinstance(adx, float) and math.isnan(adx)):
                adx = 20

            atr = self.df.iloc[i].get('ATR_14', 0)
            if atr is None or (isinstance(atr, float) and math.isnan(atr)):
                atr = 0

            bb_upper = self.df.iloc[i].get('BBU_20_2.0', price * 1.02)
            if bb_upper is None or (isinstance(bb_upper, float) and math.isnan(bb_upper)):
                bb_upper = price * 1.02

            bb_lower = self.df.iloc[i].get('BBL_20_2.0', price * 0.98)
            if bb_lower is None or (isinstance(bb_lower, float) and math.isnan(bb_lower)):
                bb_lower = price * 0.98

            

            if 'EMA_200' in recent.columns and recent['EMA_200'].notna().any():
                above_ema200 = (recent['Close'] > recent['EMA_200'].fillna(price)).sum() / len(recent)
            else:
                above_ema200 = 0.5

            try:
                ema20_now = self.df.iloc[i].get('EMA_20', None)
                ema20_prev = self.df.iloc[i-10].get('EMA_20', None) if i >= 10 else None
                if ema20_now is not None and ema20_prev is not None and not (isinstance(ema20_now, float) and math.isnan(ema20_now)) and not (isinstance(ema20_prev, float) and math.isnan(ema20_prev)) and ema20_prev != 0:
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

        

        self.df = self.df.iloc[lookback:].copy()

        self.df['REGIME'] = regimes

        self.df.reset_index(drop=True, inplace=True)

        

        return self.df

