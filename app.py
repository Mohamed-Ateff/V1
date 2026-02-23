import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
import numpy as np
from plotly.subplots import make_subplots
warnings.filterwarnings('ignore')


# Page configuration
st.set_page_config(
    page_title="",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional look
st.markdown("""
<style>
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
        background-color: #1a1a1a !important;
    }
    .stTextInput > div > div > input {
        background-color: #262730 !important;
        color: #fff !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 0 !important;
    }
    .stDateInput > div > div > input {
        background-color: #262730 !important;
        color: #fff !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 0 !important;
    }
    .stSlider > div > div > div > div {
        color: #888 !important;
    }
    .stMultiSelect > div > div > div {
        background-color: #262730 !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 0 !important;
    }
    /* Sub-tabs styling (Signal Analysis) */
    div[role="tablist"] {
        margin-top: 1.6rem !important;
        margin-bottom: 0.15rem !important;
        gap: 0.5rem !important;
        padding: 0.35rem 0.4rem !important;
        background: #0b0b14 !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 14px !important;
    }
    div[role="tablist"] button {
        color: #cfd6e6 !important;
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.05rem !important;
        margin-right: 0 !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.2px !important;
        box-shadow: none !important;
    }
    div[role="tablist"] button[aria-selected="true"] {
        color: #ffffff !important;
        background: #1b1b2c !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.35) !important;
        transform: translateY(-1px);
    }
    div[role="tablist"] button:hover {
        border-color: rgba(255,255,255,0.3) !important;
        background: #161626 !important;
    }
</style>
""", unsafe_allow_html=True)


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
            df = yf.download(self.symbol, start=self.start_date, end=self.end_date, progress=False)
        except Exception as e:
            print(f"Download error for {self.symbol}: {e}")
            return None
        
        if df is None or df.empty:
            return None
        
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
        if 'EMA' in self.selected_indicators:
            df['EMA_20'] = ta.ema(df['Close'], length=20)
            df['EMA_50'] = ta.ema(df['Close'], length=50)
            df['EMA_200'] = ta.ema(df['Close'], length=200)
        
        if 'SMA' in self.selected_indicators:
            df['SMA_20'] = ta.sma(df['Close'], length=20)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
        
        if 'ADX' in self.selected_indicators:
            adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
            if adx is not None:
                df = pd.concat([df, adx], axis=1)
        
        if 'ATR' in self.selected_indicators:
            df['ATR_14'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        if 'Bollinger Bands' in self.selected_indicators:
            bbands = ta.bbands(df['Close'], length=20)
            if bbands is not None:
                df = pd.concat([df, bbands], axis=1)
        
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
            adx = self.df.iloc[i].get('ADX_14', 20)
            atr = self.df.iloc[i].get('ATR_14', 0)
            bb_upper = self.df.iloc[i].get('BBU_20_2.0', price * 1.02)
            bb_lower = self.df.iloc[i].get('BBL_20_2.0', price * 0.98)
            
            above_ema200 = (recent['Close'] > recent.get('EMA_200', price)).sum() / len(recent) if 'EMA_200' in recent.columns else 0.5
            ema_slope = (self.df.iloc[i].get('EMA_20', price) - self.df.iloc[i-10].get('EMA_20', price)) / self.df.iloc[i-10].get('EMA_20', price) if i >= 10 else 0
            atr_pct = (atr / price) if price > 0 and atr > 0 else 0.02
            bb_width = (bb_upper - bb_lower) / price if price > 0 else 0.05
            
            regime = "RANGE"
            
            if (above_ema200 > 0.7 or above_ema200 < 0.3) and adx > adx_threshold and abs(ema_slope) > 0.02:
                regime = "TREND"
            elif atr_pct > atr_threshold or bb_width > 0.08:
                regime = "VOLATILE"
            elif adx < 20 and atr_pct < 0.02:
                regime = "RANGE"
            
            regimes.append(regime)
        
        self.df = self.df.iloc[lookback:].copy()
        self.df['REGIME'] = regimes
        self.df.reset_index(drop=True, inplace=True)
        
        return self.df


def detect_signals(df):
    """Detect buy/sell signals from all indicators."""
    signals_df = pd.DataFrame(index=df.index)
    signals_df['Date'] = df['Date']
    signals_df['Close'] = df['Close']
    signals_df['Regime'] = df.get('REGIME', 'UNKNOWN')
    
    # RSI Signals
    if 'RSI_14' in df.columns:
        signals_df['RSI_Buy'] = (df['RSI_14'] < 30).astype(int)
        signals_df['RSI_Sell'] = (df['RSI_14'] > 70).astype(int)
    
    # MACD Signals
    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
        macd_cross_up = (df['MACD_12_26_9'] > df['MACDs_12_26_9']) & (df['MACD_12_26_9'].shift(1) <= df['MACDs_12_26_9'].shift(1))
        macd_cross_down = (df['MACD_12_26_9'] < df['MACDs_12_26_9']) & (df['MACD_12_26_9'].shift(1) >= df['MACDs_12_26_9'].shift(1))
        signals_df['MACD_Buy'] = macd_cross_up.astype(int)
        signals_df['MACD_Sell'] = macd_cross_down.astype(int)
    
    # Bollinger Bands Signals
    if 'BBL_20_2.0' in df.columns and 'BBU_20_2.0' in df.columns:
        bb_buy = (df['Close'] <= df['BBL_20_2.0']).astype(int)
        bb_sell = (df['Close'] >= df['BBU_20_2.0']).astype(int)
        signals_df['BB_Buy'] = bb_buy
        signals_df['BB_Sell'] = bb_sell
    
    # Stochastic Signals
    if 'STOCHk_14_3_3' in df.columns:
        signals_df['STOCH_Buy'] = (df['STOCHk_14_3_3'] < 20).astype(int)
        signals_df['STOCH_Sell'] = (df['STOCHk_14_3_3'] > 80).astype(int)
    
    # EMA Crossover Signals
    if 'EMA_20' in df.columns and 'EMA_50' in df.columns:
        ema_cross_up = (df['EMA_20'] > df['EMA_50']) & (df['EMA_20'].shift(1) <= df['EMA_50'].shift(1))
        ema_cross_down = (df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1))
        signals_df['EMA_Buy'] = ema_cross_up.astype(int)
        signals_df['EMA_Sell'] = ema_cross_down.astype(int)
    
    return signals_df


def evaluate_signal_success(df, signals_df, profit_target=0.05, holding_period=20, stop_loss=0.03):
    """Evaluate success of each signal with detailed metrics."""
    results = {
        'RSI': {'total_signals': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'avg_gain': 0, 'avg_loss': 0, 'profit_factor': 0, 'avg_hold_time': 0, 'max_gain': 0, 'max_loss': 0, 'regime_performance': {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}},
        'MACD': {'total_signals': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'avg_gain': 0, 'avg_loss': 0, 'profit_factor': 0, 'avg_hold_time': 0, 'max_gain': 0, 'max_loss': 0, 'regime_performance': {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}},
        'BB': {'total_signals': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'avg_gain': 0, 'avg_loss': 0, 'profit_factor': 0, 'avg_hold_time': 0, 'max_gain': 0, 'max_loss': 0, 'regime_performance': {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}},
        'STOCH': {'total_signals': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'avg_gain': 0, 'avg_loss': 0, 'profit_factor': 0, 'avg_hold_time': 0, 'max_gain': 0, 'max_loss': 0, 'regime_performance': {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}},
        'EMA': {'total_signals': 0, 'successful': 0, 'failed': 0, 'success_rate': 0, 'avg_gain': 0, 'avg_loss': 0, 'profit_factor': 0, 'avg_hold_time': 0, 'max_gain': 0, 'max_loss': 0, 'regime_performance': {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}}
    }
    
    successful_signals = []
    all_signal_details = []
    
    indicators = ['RSI', 'MACD', 'BB', 'STOCH', 'EMA']
    
    for indicator in indicators:
        buy_col = f'{indicator}_Buy'
        if buy_col not in signals_df.columns:
            continue
        
        wins = []
        losses = []
        hold_times = []
        
        for i in range(len(signals_df) - holding_period):
            if signals_df.iloc[i][buy_col] == 1:
                results[indicator]['total_signals'] += 1
                
                entry_price = signals_df.iloc[i]['Close']
                entry_date = signals_df.iloc[i]['Date']
                entry_regime = signals_df.iloc[i]['Regime']
                success = False
                actual_gain = 0
                days_held = 0
                exit_reason = 'Timeout'
                
                # Check next holding_period days
                for j in range(1, holding_period + 1):
                    if i + j >= len(signals_df):
                        break
                    
                    future_price = signals_df.iloc[i + j]['Close']
                    gain = (future_price - entry_price) / entry_price
                    
                    # Check stop loss
                    if gain <= -stop_loss:
                        results[indicator]['failed'] += 1
                        losses.append(gain)
                        actual_gain = gain
                        days_held = j
                        exit_reason = 'Stop Loss'
                        break
                    
                    # Check profit target
                    if gain >= profit_target:
                        results[indicator]['successful'] += 1
                        wins.append(gain)
                        success = True
                        actual_gain = gain
                        days_held = j
                        exit_reason = 'Profit Target'
                        
                        successful_signals.append({
                            'date': entry_date,
                            'indicator': indicator,
                            'entry_price': entry_price,
                            'exit_price': future_price,
                            'gain': gain * 100,
                            'days_held': j,
                            'regime': entry_regime
                        })
                        
                        # Track regime performance
                        if entry_regime in results[indicator]['regime_performance']:
                            results[indicator]['regime_performance'][entry_regime] += 1
                        
                        hold_times.append(j)
                        break
                
                # If neither stop loss nor profit target hit
                if not success and days_held == 0 and i + holding_period < len(signals_df):
                    final_price = signals_df.iloc[i + holding_period]['Close']
                    final_gain = (final_price - entry_price) / entry_price
                    actual_gain = final_gain
                    days_held = holding_period
                    
                    if final_gain > 0:
                        results[indicator]['successful'] += 1
                        wins.append(final_gain)
                        hold_times.append(holding_period)
                    else:
                        results[indicator]['failed'] += 1
                        losses.append(final_gain)
                
                # Store all signal details
                all_signal_details.append({
                    'date': entry_date,
                    'indicator': indicator,
                    'entry_price': entry_price,
                    'exit_price': entry_price * (1 + actual_gain),
                    'gain': actual_gain * 100,
                    'days_held': days_held,
                    'success': success or (actual_gain > 0),
                    'exit_reason': exit_reason,
                    'regime': entry_regime
                })
        
        # Calculate metrics
        if results[indicator]['total_signals'] > 0:
            results[indicator]['success_rate'] = (results[indicator]['successful'] / results[indicator]['total_signals']) * 100
            
            if len(wins) > 0:
                results[indicator]['avg_gain'] = np.mean(wins) * 100
                results[indicator]['max_gain'] = max(wins) * 100
            
            if len(losses) > 0:
                results[indicator]['avg_loss'] = np.mean(losses) * 100
                results[indicator]['max_loss'] = min(losses) * 100
            
            if len(wins) > 0 and len(losses) > 0:
                total_wins = sum(wins)
                total_losses = abs(sum(losses))
                results[indicator]['profit_factor'] = total_wins / total_losses if total_losses > 0 else 0
            
            if len(hold_times) > 0:
                results[indicator]['avg_hold_time'] = np.mean(hold_times)
    
    return results, successful_signals, all_signal_details


def find_consensus_signals(signals_df):
    """Find signals where multiple indicators agreed."""
    consensus = []
    
    buy_indicators = [col for col in signals_df.columns if col.endswith('_Buy')]
    
    for i in range(len(signals_df)):
        active_indicators = []
        for col in buy_indicators:
            if signals_df.iloc[i][col] == 1:
                indicator_name = col.replace('_Buy', '')
                active_indicators.append(indicator_name)
        
        if len(active_indicators) >= 2:
            consensus.append({
                'date': signals_df.iloc[i]['Date'],
                'price': signals_df.iloc[i]['Close'],
                'indicators': active_indicators,
                'count': len(active_indicators),
                'regime': signals_df.iloc[i]['Regime']
            })
    
    return consensus


def analyze_indicator_combinations(signals_df, df, profit_target=0.05, holding_period=20, stop_loss=0.03):
    """Analyze performance of indicator combinations with advanced metrics."""
    buy_indicators = [col.replace('_Buy', '') for col in signals_df.columns if col.endswith('_Buy')]
    
    combo_results = {}
    
    # 2-indicator combinations
    for i in range(len(buy_indicators)):
        for j in range(i+1, len(buy_indicators)):
            ind1, ind2 = buy_indicators[i], buy_indicators[j]
            combo_name = f"{ind1} + {ind2}"
            
            successful = 0
            failed = 0
            total = 0
            gains = []
            losses = []
            hold_times = []
            regime_wins = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
            regime_totals = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
            
            for k in range(len(signals_df) - holding_period):
                if signals_df.iloc[k][f'{ind1}_Buy'] == 1 and signals_df.iloc[k][f'{ind2}_Buy'] == 1:
                    total += 1
                    entry_price = signals_df.iloc[k]['Close']
                    regime = signals_df.iloc[k].get('Regime', 'UNKNOWN')
                    
                    if regime in regime_totals:
                        regime_totals[regime] += 1
                    
                    hit_target = False
                    days_held = 0
                    
                    for m in range(1, holding_period + 1):
                        if k + m >= len(signals_df):
                            break
                        
                        future_price = signals_df.iloc[k + m]['Close']
                        gain = (future_price - entry_price) / entry_price
                        
                        if gain <= -stop_loss:
                            failed += 1
                            losses.append(gain * 100)
                            days_held = m
                            break
                        
                        if gain >= profit_target:
                            successful += 1
                            gains.append(gain * 100)
                            hit_target = True
                            days_held = m
                            if regime in regime_wins:
                                regime_wins[regime] += 1
                            break
                    
                    if not hit_target and days_held == 0:
                        days_held = holding_period
                        final_price = signals_df.iloc[k + holding_period]['Close']
                        final_gain = (final_price - entry_price) / entry_price
                        if final_gain > 0:
                            successful += 1
                            gains.append(final_gain * 100)
                            if regime in regime_wins:
                                regime_wins[regime] += 1
                        else:
                            failed += 1
                            losses.append(final_gain * 100)
                    
                    hold_times.append(days_held)
            
            if total > 0:
                avg_gain = float(np.mean(gains)) if gains else 0
                avg_loss = float(np.mean(losses)) if losses else 0
                win_rate = (successful / total) * 100
                expectancy = (win_rate / 100) * avg_gain + (1 - win_rate / 100) * avg_loss
                profit_factor = abs(sum(gains) / sum(losses)) if losses and sum(losses) != 0 else 0
                avg_hold = float(np.mean(hold_times)) if hold_times else 0
                
                combo_results[combo_name] = {
                    'total': total,
                    'successful': successful,
                    'failed': failed,
                    'success_rate': win_rate,
                    'avg_gain': avg_gain,
                    'avg_loss': avg_loss,
                    'expectancy': expectancy,
                    'profit_factor': profit_factor,
                    'avg_hold': avg_hold,
                    'max_gain': max(gains) if gains else 0,
                    'max_loss': min(losses) if losses else 0,
                    'regime_performance': {
                        regime: (regime_wins[regime] / regime_totals[regime] * 100) if regime_totals[regime] > 0 else 0
                        for regime in regime_totals
                    }
                }
    
    return combo_results


def calculate_monthly_performance(all_signal_details):
    """Calculate performance by month."""
    if not all_signal_details:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_signal_details)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    monthly = df.groupby('month').agg({
        'success': ['sum', 'count'],
        'gain': 'mean'
    }).reset_index()
    
    monthly.columns = ['month', 'successful', 'total', 'avg_gain']
    monthly['success_rate'] = (monthly['successful'] / monthly['total'] * 100).round(1)
    monthly['month'] = monthly['month'].astype(str)
    
    return monthly


def create_signal_timeline_chart(df, all_signal_details, selected_indicators):
    """Create interactive chart with signals marked."""
    fig = go.Figure()
    
    # Add candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#26A69A',
        increasing_fillcolor='#26A69A',
        decreasing_line_color='#EF5350',
        decreasing_fillcolor='#EF5350'
    ))
    
    # Add signals
    if all_signal_details:
        signals_df = pd.DataFrame(all_signal_details)
        
        for indicator in selected_indicators:
            indicator_signals = signals_df[signals_df['indicator'] == indicator]
            
            if len(indicator_signals) > 0:
                # Successful signals
                successful = indicator_signals[indicator_signals['success'] == True]
                if len(successful) > 0:
                    fig.add_trace(go.Scatter(
                        x=successful['date'],
                        y=successful['entry_price'],
                        mode='markers',
                        name=f'{indicator} Success',
                        marker=dict(size=10, color='#26A69A', symbol='triangle-up'),
                        hovertemplate='<b>%{text}</b><br>Entry: %{y:.2f}<extra></extra>',
                        text=[f"{indicator} +{g:.1f}%" for g in successful['gain']]
                    ))
                
                # Failed signals
                failed = indicator_signals[indicator_signals['success'] == False]
                if len(failed) > 0:
                    fig.add_trace(go.Scatter(
                        x=failed['date'],
                        y=failed['entry_price'],
                        mode='markers',
                        name=f'{indicator} Failed',
                        marker=dict(size=10, color='#FF6B6B', symbol='triangle-down'),
                        hovertemplate='<b>%{text}</b><br>Entry: %{y:.2f}<extra></extra>',
                        text=[f"{indicator} {g:.1f}%" for g in failed['gain']]
                    ))
    
    fig.update_layout(
        title='Signal Timeline - All Trades',
        yaxis_title='Price (SAR)',
        xaxis_title='',
        height=600,
        hovermode='closest',
        xaxis_rangeslider_visible=False,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01)
    )
    
    return fig


def create_price_chart(df, chart_indicators, chart_type='Candlestick'):
    """Create modern, clear price chart with multiple chart types."""
    
    fig = go.Figure()
    
    # Add price chart based on selected type
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26A69A',
            increasing_fillcolor='#26A69A',
            decreasing_line_color='#EF5350',
            decreasing_fillcolor='#EF5350'
        ))
    elif chart_type == 'Line':
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Close'],
            name='Price',
            line=dict(color='#FFC107', width=2),
            mode='lines',
            hovertemplate='Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
        ))
    elif chart_type == 'Area':
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Close'],
            name='Price',
            line=dict(color='#4A9EFF', width=2),
            fill='tozeroy',
            fillcolor='rgba(74, 158, 255, 0.2)',
            mode='lines',
            hovertemplate='Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
        ))
    
    # Modern color palette
    indicator_colors = {
        'EMA 20': '#FF6B6B',
        'EMA 50': '#4ECDC4',
        'EMA 200': '#FFD93D',
        'SMA 20': '#95E1D3',
        'BB': '#B0B0B0'
    }
    
    if 'EMA 20' in chart_indicators and 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_20'],
            name='EMA 20',
            line=dict(color=indicator_colors['EMA 20'], width=2.5),
            opacity=0.9
        ))
    
    if 'EMA 50' in chart_indicators and 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_50'],
            name='EMA 50',
            line=dict(color=indicator_colors['EMA 50'], width=2.5),
            opacity=0.9
        ))
    
    if 'EMA 200' in chart_indicators and 'EMA_200' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_200'],
            name='EMA 200',
            line=dict(color=indicator_colors['EMA 200'], width=3, dash='dot'),
            opacity=0.8
        ))
    
    if 'SMA 20' in chart_indicators and 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['SMA_20'],
            name='SMA 20',
            line=dict(color=indicator_colors['SMA 20'], width=2),
            opacity=0.9
        ))
    
    if 'Bollinger Bands' in chart_indicators:
        if 'BBU_20_2.0' in df.columns and 'BBL_20_2.0' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['BBU_20_2.0'],
                name='BB Upper',
                line=dict(color=indicator_colors['BB'], width=1, dash='dash'),
                opacity=0.5,
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['BBL_20_2.0'],
                name='Bollinger Bands',
                line=dict(color=indicator_colors['BB'], width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(176, 176, 176, 0.1)',
                opacity=0.5
            ))
    
    fig.update_layout(
        title=dict(
            text='Price Chart with Market Regimes',
            font=dict(size=20, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='Price (SAR)',
        xaxis_title='',
        height=600,
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(
            gridcolor='#2A2A2A',
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor='#2A2A2A',
            showgrid=True,
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11)
        ),
        margin=dict(t=80, b=40, l=60, r=40)
    )
    
    return fig


def create_regime_distribution_chart(regime_counts):
    """Create modern pie chart."""
    
    labels = ['TREND', 'RANGE', 'VOLATILE']
    colors = ['#26A69A', '#4A9EFF', '#FF6B6B']
    values = [regime_counts.get(label, 0) for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(color='#1E1E1E', width=3)
        ),
        hole=0.5,
        textinfo='label+percent',
        textfont=dict(size=14, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
        insidetextorientation='horizontal',
        hovertemplate='<b>%{label}</b><br>Days: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text='Market Regime Distribution',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        height=400,
        showlegend=False,
        paper_bgcolor='#262730',
        plot_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
        margin=dict(t=60, b=20, l=20, r=20)
    )
    
    return fig


def create_adx_chart(df):
    """Create modern ADX chart."""
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df.get('ADX_14', [20]*len(df)),
        name='ADX',
        line=dict(color='#A78BFA', width=3),
        fill='tozeroy',
        fillcolor='rgba(167, 139, 250, 0.2)',
        hovertemplate='Date: %{x}<br>ADX: %{y:.2f}<extra></extra>'
    ))
    
    fig.add_hline(
        y=25,
        line_dash="dash",
        line_color="#26A69A",
        line_width=2,
        annotation_text="Strong Trend (25)",
        annotation_position="right",
        annotation_font=dict(size=11, color="#26A69A")
    )
    fig.add_hline(
        y=20,
        line_dash="dash",
        line_color="#FFB74D",
        line_width=2,
        annotation_text="Weak Trend (20)",
        annotation_position="right",
        annotation_font=dict(size=11, color="#FFB74D")
    )
    
    fig.update_layout(
        title=dict(
            text='Average Directional Index (ADX)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='ADX Value',
        xaxis_title='',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=60, r=100)
    )
    
    return fig


def create_rsi_chart(df):
    """Create modern RSI chart."""
    
    fig = go.Figure()
    
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['RSI'],
            name='RSI',
            line=dict(color='#A78BFA', width=3),
            fill='tozeroy',
            fillcolor='rgba(167, 139, 250, 0.15)',
            hovertemplate='Date: %{x}<br>RSI: %{y:.2f}<extra></extra>'
        ))
        
        fig.add_hrect(
            y0=70, y1=100,
            fillcolor="#FF6B6B", opacity=0.1,
            layer="below", line_width=0
        )
        fig.add_hrect(
            y0=0, y1=30,
            fillcolor="#26A69A", opacity=0.1,
            layer="below", line_width=0
        )
        
        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="#FF6B6B",
            line_width=2,
            annotation_text="Overbought (70)",
            annotation_position="right",
            annotation_font=dict(size=11, color="#FF6B6B")
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="#26A69A",
            line_width=2,
            annotation_text="Oversold (30)",
            annotation_position="right",
            annotation_font=dict(size=11, color="#26A69A")
        )
    
    fig.update_layout(
        title=dict(
            text='Relative Strength Index (RSI)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='RSI Value',
        xaxis_title='',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True, range=[0, 100]),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=60, r=100)
    )
    
    return fig


def create_macd_chart(df):
    """Create modern MACD chart."""
    
    fig = go.Figure()
    
    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MACD_12_26_9'],
            name='MACD',
            line=dict(color='#4A9EFF', width=2.5),
            hovertemplate='MACD: %{y:.3f}<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MACDs_12_26_9'],
            name='Signal',
            line=dict(color='#FFB74D', width=2.5),
            hovertemplate='Signal: %{y:.3f}<extra></extra>'
        ))
        
        if 'MACDh_12_26_9' in df.columns:
            colors = ['#26A69A' if val >= 0 else '#FF6B6B' for val in df['MACDh_12_26_9']]
            fig.add_trace(go.Bar(
                x=df['Date'],
                y=df['MACDh_12_26_9'],
                name='Histogram',
                marker_color=colors,
                opacity=0.6,
                hovertemplate='Histogram: %{y:.3f}<extra></extra>'
            ))
        
        fig.add_hline(y=0, line_color='#666666', line_width=1, line_dash='solid')
    
    fig.update_layout(
        title=dict(
            text='MACD (Moving Average Convergence Divergence)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='MACD Value',
        xaxis_title='',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11)
        ),
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    return fig


def create_bollinger_bands_chart(df):
    """Create modern Bollinger Bands chart with price."""
    
    fig = go.Figure()
    
    # Price candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='#26A69A',
        decreasing_line_color='#FF6B6B'
    ))
    
    # Upper band
    if 'BBU_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['BBU_20_2.0'],
            name='Upper Band',
            line=dict(color='#FF6B6B', width=1, dash='dash'),
            hovertemplate='Upper: %{y:.2f}<extra></extra>'
        ))
    
    # Middle band (SMA 20)
    if 'BBM_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['BBM_20_2.0'],
            name='SMA 20',
            line=dict(color='#FFB74D', width=2),
            fill=None,
            hovertemplate='SMA20: %{y:.2f}<extra></extra>'
        ))
    
    # Lower band
    if 'BBL_20_2.0' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['BBL_20_2.0'],
            name='Lower Band',
            line=dict(color='#26A69A', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(38, 166, 154, 0.1)',
            hovertemplate='Lower: %{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text='Bollinger Bands (Volatility & Overbought/Oversold)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='Price',
        xaxis_title='',
        height=450,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    return fig


def create_volume_chart(df):
    """Create volume analysis chart with moving average."""
    
    fig = go.Figure()
    
    if 'Volume' in df.columns:
        # Volume bars - color by price direction
        colors = ['#26A69A' if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else '#FF6B6B' 
                  for i in range(len(df))]
        
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7,
            hovertemplate='Volume: %{y:,.0f}<extra></extra>'
        ))
        
        # Volume SMA 20
        vol_sma = df['Volume'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=vol_sma,
            name='Vol SMA 20',
            line=dict(color='#FFB74D', width=2.5),
            hovertemplate='Vol MA: %{y:,.0f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text='Volume Analysis (Confirmation Strength)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='Volume',
        xaxis_title='',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    return fig


def create_ema_chart(df):
    """Create Moving Averages trend chart (EMA 20/50/200)."""
    
    fig = go.Figure()
    
    # Price
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Close'],
        name='Price',
        line=dict(color='#FFFFFF', width=2),
        hovertemplate='Price: %{y:.2f}<extra></extra>'
    ))
    
    # EMA 20
    if 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_20'],
            name='EMA 20',
            line=dict(color='#4A9EFF', width=2),
            hovertemplate='EMA20: %{y:.2f}<extra></extra>'
        ))
    
    # EMA 50
    if 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_50'],
            name='EMA 50',
            line=dict(color='#FFB74D', width=2),
            hovertemplate='EMA50: %{y:.2f}<extra></extra>'
        ))
    
    # EMA 200
    if 'EMA_200' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_200'],
            name='EMA 200',
            line=dict(color='#FF6B6B', width=2.5),
            hovertemplate='EMA200: %{y:.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text='Exponential Moving Averages (Trend Confirmation)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='Price',
        xaxis_title='',
        height=450,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    return fig


def create_stochastic_chart(df):
    """Create Stochastic Oscillator chart (momentum reversal signals)."""
    
    fig = go.Figure()
    
    # Calculate Stochastic if not present
    if 'Stoch_K' not in df.columns:
        # Calculate K% = (Close - Low14) / (High14 - Low14) * 100
        low14 = df['Low'].rolling(window=14).min()
        high14 = df['High'].rolling(window=14).max()
        k_percent = ((df['Close'] - low14) / (high14 - low14) * 100).fillna(50)
        d_percent = k_percent.rolling(window=3).mean()
    else:
        k_percent = df.get('Stoch_K', [50]*len(df))
        d_percent = df.get('Stoch_D', [50]*len(df))
    
    # %K line
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=k_percent,
        name='%K',
        line=dict(color='#4A9EFF', width=2.5),
        hovertemplate='%K: %{y:.2f}<extra></extra>'
    ))
    
    # %D line (signal)
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=d_percent,
        name='%D (Signal)',
        line=dict(color='#FFB74D', width=2.5),
        hovertemplate='%D: %{y:.2f}<extra></extra>'
    ))
    
    # Overbought zone (80)
    fig.add_hrect(
        y0=80, y1=100,
        fillcolor="#FF6B6B", opacity=0.1,
        layer="below", line_width=0
    )
    
    # Oversold zone (20)
    fig.add_hrect(
        y0=0, y1=20,
        fillcolor="#26A69A", opacity=0.1,
        layer="below", line_width=0
    )
    
    fig.add_hline(y=80, line_dash="dash", line_color="#FF6B6B", line_width=1.5,
                 annotation_text="Overbought (80)", annotation_position="right",
                 annotation_font=dict(size=10, color="#FF6B6B"))
    fig.add_hline(y=20, line_dash="dash", line_color="#26A69A", line_width=1.5,
                 annotation_text="Oversold (20)", annotation_position="right",
                 annotation_font=dict(size=10, color="#26A69A"))
    fig.add_hline(y=50, line_color="#666666", line_width=1, line_dash="dot")
    
    fig.update_layout(
        title=dict(
            text='Stochastic Oscillator (Momentum & Reversal Signals)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='Stochastic Value',
        xaxis_title='',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True, range=[0, 100]),
        hovermode='x unified',
        margin=dict(t=60, b=40, l=60, r=100)
    )
    
    return fig


def create_signal_strength_heatmap(df, latest):
    """Create signal strength heatmap showing indicator alignment."""
    
    # Calculate signal strengths (0-100 scale)
    signals = {}
    
    # ADX - Trend strength
    adx = latest.get('ADX_14', 20)
    signals['TREND'] = min(100, (adx / 30) * 100)  # Normalize to 100
    
    # RSI - Momentum
    rsi = latest.get('RSI', 50)
    if rsi > 70 or rsi < 30:
        signals['MOMENTUM'] = 100  # Strong signal
    elif rsi > 60 or rsi < 40:
        signals['MOMENTUM'] = 75
    else:
        signals['MOMENTUM'] = 50
    
    # MACD - Trend confirmation
    macd = latest.get('MACD_12_26_9', 0)
    macd_signal = latest.get('MACDs_12_26_9', 0)
    if macd > macd_signal:
        signals['MACD'] = 80
    elif macd < macd_signal:
        signals['MACD'] = 20
    else:
        signals['MACD'] = 50
    
    # Bollinger Bands - Volatility
    bb_upper = latest.get('BBU_20_2.0', latest['Close'] * 1.02)
    bb_lower = latest.get('BBL_20_2.0', latest['Close'] * 0.98)
    bb_pos = ((latest['Close'] - bb_lower) / (bb_upper - bb_lower) * 100) if bb_upper != bb_lower else 50
    signals['VOLATILITY'] = bb_pos
    
    # Volume - Confirmation
    if 'Volume' in df.columns and len(df) > 20:
        avg_vol = df.tail(20)['Volume'].mean()
        curr_vol = latest.get('Volume', avg_vol)
        signals['VOLUME'] = min(100, (curr_vol / avg_vol) * 100)
    else:
        signals['VOLUME'] = 50
    
    # Create heatmap
    signal_names = list(signals.keys())
    signal_values = list(signals.values())
    
    # Color code: Red (0-40) -> Yellow (40-60) -> Green (60-100)
    colors = []
    for val in signal_values:
        if val < 40:
            colors.append('#FF6B6B')  # Red
        elif val < 60:
            colors.append('#FFB74D')  # Yellow
        else:
            colors.append('#26A69A')  # Green
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=signal_names,
        x=signal_values,
        orientation='h',
        marker=dict(color=colors),
        text=[f'{v:.0f}%' for v in signal_values],
        textposition='auto',
        hovertemplate='%{y}: %{x:.0f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='Signal Strength Alignment (Accuracy Gauge)',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='Strength %',
        yaxis_title='Indicator',
        height=320,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=True, range=[0, 100]),
        showlegend=False,
        margin=dict(t=60, b=40, l=120, r=40)
    )
    
    return fig


def create_signal_success_chart(results):
    """Create chart showing signal success rates."""
    indicators = []
    success_rates = []
    colors = []
    
    for indicator, data in results.items():
        if data['total_signals'] > 0:
            indicators.append(indicator)
            success_rates.append(data['success_rate'])
            
            if data['success_rate'] >= 60:
                colors.append('#26A69A')
            elif data['success_rate'] >= 40:
                colors.append('#FFC107')
            else:
                colors.append('#FF6B6B')
    
    fig = go.Figure(data=[go.Bar(
        x=indicators,
        y=success_rates,
        marker_color=colors,
        text=[f"{rate:.1f}%" for rate in success_rates],
        textposition='auto',
        textfont=dict(size=14, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
        hovertemplate='<b>%{x}</b><br>Success Rate: %{y:.1f}%<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(
            text='Signal Success Rate by Indicator',
            font=dict(size=18, color='#FFFFFF', family='Inter, -apple-system, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        yaxis_title='Success Rate (%)',
        xaxis_title='',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=False),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True, range=[0, 100]),
        margin=dict(t=60, b=40, l=60, r=40)
    )
    
    return fig


def create_regime_performance_chart(results):
    """Create chart showing performance by regime."""
    fig = go.Figure()
    
    regimes = ['TREND', 'RANGE', 'VOLATILE']
    
    for indicator, data in results.items():
        if data['total_signals'] > 0:
            values = [data['regime_performance'].get(regime, 0) for regime in regimes]
            fig.add_trace(go.Bar(
                name=indicator,
                x=regimes,
                y=values,
                text=values,
                textposition='auto'
            ))
    
    fig.update_layout(
        title='Successful Signals by Market Regime',
        yaxis_title='Number of Successful Signals',
        barmode='group',
        height=400,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12),
        xaxis=dict(gridcolor='#2A2A2A', showgrid=False),
        yaxis=dict(gridcolor='#2A2A2A', showgrid=True)
    )
    
    return fig


def create_monthly_performance_chart(monthly_df):
    """Create chart showing monthly performance."""
    if monthly_df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Success Rate', 'Monthly Average Gain'),
        vertical_spacing=0.15
    )
    
    colors = ['#26A69A' if rate >= 50 else '#FF6B6B' for rate in monthly_df['success_rate']]
    
    fig.add_trace(
        go.Bar(x=monthly_df['month'], y=monthly_df['success_rate'], 
               marker_color=colors, name='Success Rate',
               text=[f"{rate:.1f}%" for rate in monthly_df['success_rate']],
               textposition='auto'),
        row=1, col=1
    )
    
    gain_colors = ['#26A69A' if gain >= 0 else '#FF6B6B' for gain in monthly_df['avg_gain']]
    
    fig.add_trace(
        go.Bar(x=monthly_df['month'], y=monthly_df['avg_gain'],
               marker_color=gain_colors, name='Avg Gain',
               text=[f"{gain:.2f}%" for gain in monthly_df['avg_gain']],
               textposition='auto'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=False,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#FFFFFF', family='Inter, -apple-system, sans-serif', size=12)
    )
    
    fig.update_xaxes(gridcolor='#2A2A2A', showgrid=False)
    fig.update_yaxes(gridcolor='#2A2A2A', showgrid=True)
    
    return fig


def render_trading_system_chart(df, current_regime, cp, atr_pct, regime_stability):
    """Render the trading system forecast chart and metrics."""
    st.markdown("<div style='font-size:1rem; font-weight:700; color:#fff; margin:0 0 0.6rem 0;'>Trading System — Key Levels & Forecast</div>", unsafe_allow_html=True)

    fc_col1, fc_col2 = st.columns([1.2, 1.1], gap="small")
    with fc_col1:
        pred_horizon = st.slider("Forecast Horizon (trading days)", 5, 60, 20, key="ts_fc_horizon")
    with fc_col2:
        band_width = st.selectbox("Forecast Band", ["50% range", "80% range"], key="ts_fc_band")

    # Historical pattern analysis (regime-based)
    pattern_gains = []
    _reg_series = df['REGIME'].values
    _close_series = df['Close'].values
    _i = 0
    while _i < len(_reg_series) - 5:
        if _reg_series[_i] == current_regime:
            _start = _i
            while _i < len(_reg_series) and _reg_series[_i] == current_regime:
                _i += 1
            _dur = _i - _start
            if _dur >= 5 and _i + 20 < len(_close_series):
                _entry = _close_series[_start]
                _future = _close_series[min(_i + 20, len(_close_series) - 1)]
                _g = (_future - _entry) / _entry * 100
                pattern_gains.append(_g)
        else:
            _i += 1

    avg_pattern_gain = np.mean(pattern_gains) if pattern_gains else 0

    # Recent momentum trajectory (5-day slope of close)
    if len(df) >= 10:
        _slope_prices = df.tail(10)['Close'].values
        _slope_x = np.arange(len(_slope_prices))
        _slope_coef = np.polyfit(_slope_x, _slope_prices, 1)[0]
        price_slope_daily = _slope_coef
    else:
        price_slope_daily = 0

    if pattern_gains:
        p25 = np.percentile(pattern_gains, 25) * (pred_horizon / 20)
        p75 = np.percentile(pattern_gains, 75) * (pred_horizon / 20)
        p10 = np.percentile(pattern_gains, 10) * (pred_horizon / 20)
        p90 = np.percentile(pattern_gains, 90) * (pred_horizon / 20)
    else:
        p25 = -atr_pct
        p75 = atr_pct
        p10 = -atr_pct * 1.5
        p90 = atr_pct * 1.5

    band_low_pct = p25 if band_width == "50% range" else p10
    band_high_pct = p75 if band_width == "50% range" else p90

    trend_pct = (price_slope_daily * pred_horizon / cp * 100) if cp else 0
    regime_pct = avg_pattern_gain * (pred_horizon / 20)

    returns = np.log(df["Close"] / df["Close"].shift(1)).dropna()
    returns = returns.tail(min(90, len(returns))) if len(returns) > 0 else returns
    mu = returns.mean() if len(returns) > 0 else 0
    sigma = returns.std() if len(returns) > 1 else 0
    drift_pct = (np.exp(mu * pred_horizon) - 1) * 100
    z = 0.674 if band_width == "50% range" else 1.282
    drift_low_pct = (np.exp((mu - z * sigma) * pred_horizon) - 1) * 100
    drift_high_pct = (np.exp((mu + z * sigma) * pred_horizon) - 1) * 100

    if current_regime == "TREND":
        weights = np.array([0.5, 0.35, 0.15])
    elif current_regime == "RANGE":
        weights = np.array([0.1, 0.3, 0.6])
    else:
        weights = np.array([0.1, 0.6, 0.3])
    proj_pct = (weights[0] * trend_pct) + (weights[1] * drift_pct) + (weights[2] * regime_pct)
    band_low = (drift_low_pct + band_low_pct) / 2
    band_high = (drift_high_pct + band_high_pct) / 2

    proj_price = cp * (1 + proj_pct / 100)
    band_low_price = cp * (1 + band_low / 100)
    band_high_price = cp * (1 + band_high / 100)

    size_score = min(30, len(pattern_gains) * 2)
    stability_score = min(30, regime_stability * 0.3)
    vol_penalty = min(30, atr_pct * 6)
    confidence = max(25, min(85, 40 + size_score + stability_score - vol_penalty))

    summary_col1, summary_col2, summary_col3 = st.columns(3, gap="small")
    with summary_col1:
        st.metric("Projected Return", f"{proj_pct:+.1f}%")
    with summary_col2:
        st.metric("Forecast Price", f"{proj_price:.2f} SAR")
    with summary_col3:
        st.metric("Confidence", f"{confidence:.0f}%")
    st.caption("Model: Adaptive blend of trend, statistical drift, and regime history.")

    forecast_dates = pd.date_range(start=df.iloc[-1]['Date'], periods=pred_horizon + 1, freq='B')
    forecast_prices = [cp + (proj_price - cp) * (i / pred_horizon) for i in range(pred_horizon + 1)]
    fc_lower = [cp + (band_low_price - cp) * (i / pred_horizon) for i in range(pred_horizon + 1)]
    fc_upper = [cp + (band_high_price - cp) * (i / pred_horizon) for i in range(pred_horizon + 1)]

    hist_90 = df.tail(90)
    rc = go.Figure()
    rc.add_trace(go.Candlestick(
        x=hist_90['Date'], open=hist_90['Open'], high=hist_90['High'],
        low=hist_90['Low'], close=hist_90['Close'], name='Price',
        increasing_line_color='#26A69A', increasing_fillcolor='rgba(38,166,154,0.8)',
        decreasing_line_color='#EF5350', decreasing_fillcolor='rgba(239,83,80,0.8)'
    ))
    if 'EMA_20' in hist_90.columns:
        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['EMA_20'],
            name='EMA 20', line=dict(color='#FF6B6B', width=1.5, dash='dot'), opacity=0.9))
    if 'EMA_50' in hist_90.columns:
        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['EMA_50'],
            name='EMA 50', line=dict(color='#4ECDC4', width=1.5, dash='dot'), opacity=0.9))
    if 'EMA_200' in hist_90.columns:
        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['EMA_200'],
            name='EMA 200', line=dict(color='#FFD93D', width=2, dash='dash'), opacity=0.9))
    if 'BBU_20_2.0' in hist_90.columns and 'BBL_20_2.0' in hist_90.columns:
        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['BBU_20_2.0'],
            line=dict(color='rgba(160,160,160,0.3)', width=1), showlegend=False))
        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['BBL_20_2.0'],
            line=dict(color='rgba(160,160,160,0.3)', width=1), name='BB Bands',
            fill='tonexty', fillcolor='rgba(160,160,160,0.04)'))
    rc.add_trace(go.Scatter(x=list(forecast_dates), y=fc_upper,
        mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
    rc.add_trace(go.Scatter(x=list(forecast_dates), y=fc_lower,
        mode='lines', line=dict(width=0), fill='tonexty',
        fillcolor='rgba(74,158,255,0.08)', name='Forecast Band', hoverinfo='skip'))
    rc.add_trace(go.Scatter(x=list(forecast_dates), y=forecast_prices,
        mode='lines+markers', name=f'{pred_horizon}D Forecast',
        line=dict(color='#4A9EFF', width=2, dash='dot'),
        marker=dict(size=3), hovertemplate='%{y:.2f} SAR<extra>Forecast</extra>'))
    rc.update_layout(
        xaxis_rangeslider_visible=False, height=480,
        plot_bgcolor='#0e0e18', paper_bgcolor='#0e0e18',
        font=dict(color='#FFFFFF', family='Inter, sans-serif', size=11),
        xaxis=dict(gridcolor='#1a1a2a', showgrid=True),
        yaxis=dict(gridcolor='#1a1a2a', showgrid=True),
        legend=dict(orientation='h', y=1.02, x=1, xanchor='right',
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
        hovermode='x unified', margin=dict(t=20, b=30, l=60, r=110)
    )
    st.plotly_chart(rc, use_container_width=True, key="ts_price_chart")


def create_combo_performance_chart(combo_data):
    """Create performance breakdown chart for a combination."""
    try:
        # Ensure we have the required keys
        total = combo_data.get('total', 0)
        successful = combo_data.get('successful', 0)
        failed = combo_data.get('failed', 0)
        
        # Fallback: calculate from success_rate if individual counts missing
        if (successful == 0 and failed == 0) and total > 0:
            success_rate = combo_data.get('success_rate', 50)
            successful = int(total * (success_rate / 100))
            failed = total - successful
        
        # Ensure we have valid numbers
        if successful < 0:
            successful = 0
        if failed < 0:
            failed = 0
        
        # If both are 0, use dummy data
        if successful == 0 and failed == 0:
            successful, failed = 1, 1
        
        fig = go.Figure(data=[
            go.Pie(
                labels=['Wins', 'Losses'],
                values=[successful, failed],
                marker=dict(colors=['#26A69A', '#EF5350']),
                textinfo='label+percent',
                hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=dict(text='Win / Loss Distribution', font=dict(size=14, color='#fff')),
            height=280,
            plot_bgcolor='#262730',
            paper_bgcolor='#262730',
            font=dict(color='#ffffff', size=11),
            showlegend=True,
            margin=dict(t=40, b=20, l=20, r=20)
        )
        return fig
    except Exception as e:
        # Return an empty error figure if something goes wrong
        import traceback
        print(f"Error in create_combo_performance_chart: {e}\n{traceback.format_exc()}")
        raise


def create_combo_regime_chart(regime_perf):
    """Create regime performance breakdown for a combination."""
    try:
        regimes = ['TREND', 'RANGE', 'VOLATILE']
        values = [regime_perf.get(r, 0) if regime_perf else 0 for r in regimes]
        colors = ['#26A69A', '#FFC107', '#EF5350']
        
        # Ensure all values are valid numbers
        values = [float(v) if v is not None else 0 for v in values]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=regimes,
            y=values,
            marker=dict(color=colors),
            text=[f'{v:.0f}%' if v else '0%' for v in values],
            textposition='auto',
            hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(text='Performance by Regime', font=dict(size=14, color='#fff')),
            height=280,
            plot_bgcolor='#262730',
            paper_bgcolor='#262730',
            font=dict(color='#ffffff', size=11),
            xaxis_title='Market Regime',
            yaxis_title='Win Rate %',
            yaxis=dict(range=[0, 100]),
            showlegend=False,
            margin=dict(t=40, b=40, l=50, r=20)
        )
        return fig
    except Exception as e:
        # Return error details if something goes wrong
        import traceback
        print(f"Error in create_combo_regime_chart: {e}\n{traceback.format_exc()}")
        raise


def create_combo_metrics_comparison(sorted_combos):
    """Create comparison chart of top 5 combos across key metrics."""
    combo_names = [c[0] for c in sorted_combos[:5]]
    win_rates = [c[1]['success_rate'] for c in sorted_combos[:5]]
    expectancies = [c[1]['expectancy'] for c in sorted_combos[:5]]
    profit_factors = [c[1]['profit_factor'] for c in sorted_combos[:5]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Win Rate %', x=combo_names, y=win_rates, marker_color='#26A69A'))
    fig.add_trace(go.Bar(name='Expectancy %', x=combo_names, y=expectancies, marker_color='#FFC107'))
    fig.add_trace(go.Bar(name='Profit Factor', x=combo_names, y=profit_factors, marker_color='#A78BFA'))
    
    fig.update_layout(
        title=dict(text='Top 5 Combinations - Metrics Comparison', font=dict(size=15, color='#fff')),
        height=350,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#ffffff', size=11),
        barmode='group',
        xaxis_tickangle=-45,
        margin=dict(t=50, b=80, l=60, r=20)
    )
    return fig


def create_combo_consistency_chart(sorted_combos):
    """Create risk/reward profile chart."""
    combo_names = [c[0] for c in sorted_combos[:5]]
    avg_gains = [max(c[1]['avg_gain'], 0.01) for c in sorted_combos[:5]]
    avg_losses = [abs(min(c[1]['avg_loss'], -0.01)) for c in sorted_combos[:5]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Avg Gain %', x=combo_names, y=avg_gains, marker_color='#26A69A'))
    fig.add_trace(go.Bar(name='Avg Loss %', x=combo_names, y=avg_losses, marker_color='#EF5350'))
    
    fig.update_layout(
        title=dict(text='Risk/Reward Profile', font=dict(size=14, color='#fff')),
        height=320,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#ffffff', size=11),
        barmode='group',
        xaxis_tickangle=-45,
        yaxis_title='Percentage %',
        margin=dict(t=50, b=80, l=60, r=20)
    )
    return fig


def info_icon(tooltip_text):
    """Create a small help icon with tooltip explanation."""
    return f'<span title="{tooltip_text}" style="color: #6366F1; font-weight: bold; cursor: help; margin-left: 0.3rem;">?</span>'


def main():
    """Main application."""
    
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    
    if not st.session_state.show_results:
        # CONTROLS PAGE
        # CSS styling for input fields and selectors
        st.markdown("""
        <style>
        input[type="text"], input[type="date"], .stMultiSelect {
            background-color: #262730 !important;
            border: 1px solid #3a3a42 !important;
            color: #fff !important;
            border-radius: 0 !important;
        }
        
        .stMultiSelect label {
            color: #fff !important;
        }
        
        [data-baseweb="select"] {
            background-color: #262730 !important;
            border-radius: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)

        # Center the control panel with proper spacing
        col_left, col_center, col_right = st.columns([1.5, 2, 1.5])
        
        with col_center:
            # Main control container with centered layout
            st.markdown("""
            <div style="display: flex; flex-direction: column; gap: 0.9rem; padding: 0;">
            """, unsafe_allow_html=True)
            
            # Stock Symbol - Text input
            st.markdown("<div style='font-size: 0.8rem; color: #AAA; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; font-weight: 600;'>Stock Symbol</div>", unsafe_allow_html=True)
            user_symbol = st.text_input(
                "Stock Symbol",
                value="1120",
                key="symbol_input",
                label_visibility="collapsed",
                placeholder="e.g., 4190 or AAPL"
            )
            
            # Automatically append .SR if user enters only numbers
            if user_symbol.strip().isdigit():
                symbol_input = user_symbol.strip() + ".SR"
            else:
                symbol_input = user_symbol.strip()
            
            st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            
            # Start Date
            st.markdown("<div style='font-size: 0.8rem; color: #AAA; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; font-weight: 600;'>Start Date</div>", unsafe_allow_html=True)
            start_date = st.date_input(
                "From",
                value=datetime(2020, 1, 1),
                key="start_date",
                label_visibility="collapsed"
            )
            
            st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            
            # End Date
            st.markdown("<div style='font-size: 0.8rem; color: #AAA; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; font-weight: 600;'>End Date</div>", unsafe_allow_html=True)
            end_date = st.date_input(
                "To",
                value=datetime.now(),
                key="end_date",
                label_visibility="collapsed"
            )
            
            st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
            
            # Indicators to Calculate
            st.markdown("<div style='font-size: 0.8rem; color: #AAA; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; font-weight: 600;'>Indicators to Calculate</div>", unsafe_allow_html=True)
            selected_indicators = st.multiselect(
                "Technical Indicators",
                options=['EMA', 'SMA', 'ADX', 'ATR', 'RSI', 'MACD', 'Bollinger Bands', 'Stochastic'],
                default=['EMA', 'SMA', 'ADX', 'ATR', 'RSI', 'MACD', 'Bollinger Bands', 'Stochastic'],
                label_visibility="collapsed",
                key="indicators_select"
            )
            st.session_state.selected_indicators = selected_indicators
            
            st.markdown("<div style='margin: 0.7rem 0 1rem 0;'></div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Button in center - styled and positioned closer
        _, center_button_col, _ = st.columns([1.5, 2, 1.5])
        
        with center_button_col:
            # Custom button styling
            st.markdown("""
            <style>
            .stButton > button {
                background-color: #26A69A !important;
                color: #FFFFFF !important;
                border: none !important;
                min-height: 45px !important;
                font-size: 0.95rem !important;
                font-weight: 600 !important;
                letter-spacing: 0.3px !important;
                border-radius: 0 !important;
                transition: all 0.2s ease !important;
            }
            
            .stButton > button:hover {
                background-color: #1f8a7f !important;
                box-shadow: 0 0 15px rgba(38, 166, 154, 0.4) !important;
            }
            
            .stButton > button:active {
                background-color: #177d73 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            lookback_period = 30
            
            def run_analysis_callback():
                with st.spinner(f"Analyzing {symbol_input}..."):
                    try:
                        analyzer = RegimeAnalyzer(symbol_input, start_date.strftime('%Y-%m-%d'), 
                                                 end_date.strftime('%Y-%m-%d'), selected_indicators)
                        df = analyzer.download_data()
                        
                        if df is None:
                            st.error(f"No data found for symbol '{symbol_input}'")
                            st.info("Please verify the stock symbol is correct and try again.")
                        elif len(df) < 50:
                            st.error(f"Insufficient data: Only {len(df)} data points available")
                            st.info(f"Need at least 50 data points. Try extending the date range or checking the stock symbol.")
                        else:
                            df = analyzer.classify_regimes(lookback=lookback_period, 
                                                           adx_threshold=25, 
                                                           atr_threshold=0.03)
                            
                            st.session_state.df = df
                            st.session_state.analyzed_symbol = symbol_input
                            st.session_state.additional_charts = ['ADX', 'RSI', 'MACD']
                            st.session_state.show_results = True
                            
                    except Exception as e:
                        error_msg = str(e).lower()
                        if 'no data' in error_msg or 'invalid' in error_msg:
                            st.error(f"Invalid stock symbol: '{symbol_input}'")
                            st.info("Please select a valid stock from the dropdown list.")
                        else:
                            st.error(f"Error during analysis: {str(e)}")
                            st.info("Please check the stock symbol and date range, then try again.")
            
            st.button("Run Analysis", type="secondary", use_container_width=True, on_click=run_analysis_callback)
    
    else:
        # RESULTS PAGE
        df = st.session_state.df
        symbol_input = st.session_state.analyzed_symbol
        additional_charts = ['ADX', 'RSI', 'MACD']
        
        # Add spacing at top of results page
        st.markdown("<div style='margin-top: 4rem;'></div>", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns(2, gap="medium")
        
        with btn_col1:
            if st.button("← New Analysis", type="secondary", use_container_width=True):
                st.session_state.show_results = False
                st.rerun()
        
        with btn_col2:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Analysis (CSV)",
                data=csv,
                file_name=f"regime_analysis_{symbol_input}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary",
                key="download_analysis_btn"
            )
        
        # Stock Information Section
        latest = df.iloc[-1]
        first = df.iloc[0]
        
        # Fetch stock name dynamically from Yahoo Finance
        try:
            stock_info = yf.Ticker(symbol_input)
            stock_name = stock_info.info.get('longName', stock_info.info.get('shortName', symbol_input))
        except:
            stock_name = symbol_input
        
        current_price = latest['Close']
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

        st.markdown(f"""
        <div style='background:linear-gradient(135deg, #0e0e1a 0%, #12121f 100%); border:1px solid rgba(255,255,255,0.12); border-radius:16px; padding:2rem 2.2rem; margin-bottom:1.5rem; box-shadow:0 8px 32px rgba(0,0,0,0.4);'>
            <div style='display:flex; justify-content:space-between; align-items:center; gap:2rem; flex-wrap:wrap; margin-bottom:1.8rem;'>
                <div>
                    <div style='font-size:2.2rem; font-weight:800; color:#fff; line-height:1.1; letter-spacing:-0.5px;'>{stock_name}</div>
                    <div style='font-size:1.05rem; color:#8a95a8; margin-top:0.5rem; font-weight:500;'>Symbol: <span style='color:#fff; font-weight:700; letter-spacing:0.5px;'>{symbol_input}</span></div>
                </div>
                <div style='text-align:right; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:1rem 1.4rem;'>
                    <div style='font-size:0.75rem; color:#8a95a8; text-transform:uppercase; letter-spacing:1.2px; font-weight:600;'>Current Market</div>
                    <div style='font-size:1.8rem; font-weight:800; color:{regime_color}; margin-top:0.3rem; letter-spacing:0.5px;'>{latest['REGIME']}</div>
                </div>
            </div>
            <div style='display:grid; grid-template-columns:repeat(4, 1fr); gap:1.2rem; margin-bottom:1.2rem;'>
                <div style='background:linear-gradient(135deg, {delta_bg} 0%, #13131f 100%); border:1px solid rgba(255,255,255,0.18); border-left:4px solid {delta_color}; border-radius:14px; padding:1.3rem 1.2rem; box-shadow:0 6px 20px rgba(0,0,0,0.25);'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Current Price</div>
                    <div style='font-size:2.2rem; font-weight:900; color:{delta_color}; margin-top:0.5rem; line-height:1;'>{current_price:.2f}</div>
                    <div style='font-size:0.85rem; color:#8a95a8; margin-top:0.2rem; font-weight:500;'>SAR</div>
                    <div style='display:flex; align-items:center; gap:0.6rem; margin-top:0.6rem;'>
                        <span style='font-size:0.7rem; background:{delta_color}; color:#fff; padding:0.3rem 0.6rem; border-radius:6px; font-weight:700; letter-spacing:0.5px;'>{delta_label}</span>
                        <span style='font-size:1.15rem; color:{delta_color}; font-weight:800;'>{period_change:+.2f}%</span>
                    </div>
                    <div style='font-size:0.75rem; color:#8a95a8; margin-top:0.5rem; font-weight:500;'>Period Start: {first['Close']:.2f} SAR</div>
                </div>
                <div style='background:linear-gradient(135deg, rgba(38,166,154,0.08) 0%, #13131f 100%); border:1px solid rgba(38,166,154,0.25); border-left:3px solid #26A69A; border-radius:14px; padding:1.3rem 1.2rem; box-shadow:0 4px 16px rgba(38,166,154,0.1);'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Period High</div>
                    <div style='font-size:1.85rem; font-weight:800; color:#26A69A; margin-top:0.5rem; line-height:1;'>{period_high:.2f}</div>
                    <div style='font-size:0.85rem; color:#8a95a8; margin-top:0.2rem; font-weight:500;'>SAR</div>
                    <div style='font-size:0.75rem; color:#26A69A; margin-top:0.5rem; font-weight:600;'>+{((period_high - current_price) / current_price * 100):.1f}% from current</div>
                </div>
                <div style='background:linear-gradient(135deg, rgba(239,83,80,0.08) 0%, #13131f 100%); border:1px solid rgba(239,83,80,0.25); border-left:3px solid #EF5350; border-radius:14px; padding:1.3rem 1.2rem; box-shadow:0 4px 16px rgba(239,83,80,0.1);'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Period Low</div>
                    <div style='font-size:1.85rem; font-weight:800; color:#EF5350; margin-top:0.5rem; line-height:1;'>{period_low:.2f}</div>
                    <div style='font-size:0.85rem; color:#8a95a8; margin-top:0.2rem; font-weight:500;'>SAR</div>
                    <div style='font-size:0.75rem; color:#EF5350; margin-top:0.5rem; font-weight:600;'>{(((period_low - current_price) / current_price * 100)):.1f}% from current</div>
                </div>
                <div style='background:linear-gradient(135deg, rgba(74,158,255,0.06) 0%, #13131f 100%); border:1px solid rgba(255,255,255,0.12); border-left:3px solid {volume_color}; border-radius:14px; padding:1.3rem 1.2rem; box-shadow:0 4px 16px rgba(0,0,0,0.2);'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Avg Daily Volume</div>
                    <div style='font-size:1.85rem; font-weight:800; color:{volume_color}; margin-top:0.5rem; line-height:1;'>{avg_volume:,.0f}</div>
                    <div style='font-size:0.75rem; color:{volume_color}; margin-top:0.5rem; font-weight:600;'>Latest: {latest_volume:,.0f} ({((latest_volume / avg_volume - 1) * 100):+.0f}%)</div>
                </div>
            </div>
            <div style='display:grid; grid-template-columns:repeat(3, 1fr); gap:1.2rem;'>
                <div style='background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.1rem 1.2rem;'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Analysis Period</div>
                    <div style='font-size:1.05rem; font-weight:600; color:#cfd6e6; margin-top:0.4rem; line-height:1.4;'>{df.iloc[0]['Date'].strftime('%Y-%m-%d')} → {df.iloc[-1]['Date'].strftime('%Y-%m-%d')}</div>
                </div>
                <div style='background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.1rem 1.2rem;'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Price Range</div>
                    <div style='font-size:1.4rem; font-weight:700; color:#cfd6e6; margin-top:0.4rem; line-height:1;'>{price_range:.2f} <span style='font-size:0.85rem; color:#8a95a8; font-weight:500;'>SAR</span></div>
                </div>
                <div style='background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.1rem 1.2rem;'>
                    <div style='font-size:0.7rem; color:#8a95a8; text-transform:uppercase; letter-spacing:0.8px; font-weight:600;'>Annualized Volatility</div>
                    <div style='font-size:1.4rem; font-weight:700; color:{annual_vol_color}; margin-top:0.4rem; line-height:1;'>{annual_vol:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Calculate metrics for snapshot and recommendations
        current_regime = latest['REGIME']
        adx_current = latest.get('ADX_14', 0)
        rsi_current = latest.get('RSI', 0)
        atr_current = latest.get('ATR', 0)
        atr_pct = (atr_current / latest['Close']) * 100 if atr_current > 0 else 0
        price_vs_ema20 = ((latest['Close'] - latest.get('EMA_20', latest['Close'])) / latest.get('EMA_20', latest['Close'])) * 100
        price_vs_ema200 = ((latest['Close'] - latest.get('EMA_200', latest['Close'])) / latest.get('EMA_200', latest['Close'])) * 100
        recent_5d_change = ((latest['Close'] - df.iloc[-6]['Close']) / df.iloc[-6]['Close'] * 100) if len(df) > 6 else 0
        recent_20d_change = ((latest['Close'] - df.iloc[-21]['Close']) / df.iloc[-21]['Close'] * 100) if len(df) > 21 else 0
        last_20_regimes = df.tail(20)['REGIME'].value_counts()
        regime_stability = (last_20_regimes.iloc[0] / 20 * 100) if len(last_20_regimes) > 0 else 0

        # TABS START HERE
        tab0, tab1, tab2, tab3 = st.tabs([
            "Regime Analysis",
            "Price Action Analysis",
            "Signal Analysis",
            "Patterns"
        ])
        
        with tab0:
            # Price Chart + Regime Distribution
            # First, recalculate needed variables for this tab
            latest = df.iloc[-1]
            current_price = latest['Close']
            current_regime = latest['REGIME']
            rsi_current = latest.get('RSI_14', 50)
            
            # Volume analysis
            recent_vol = latest.get('Volume', 0)
            avg_vol_20 = df.tail(20)['Volume'].mean()
            vol_ratio = (recent_vol / avg_vol_20) if avg_vol_20 > 0 else 1
            
            # Support/Resistance
            recent_50 = df.tail(50)
            resistance_1 = recent_50['High'].max()
            support_1 = recent_50['Low'].min()
            
            st.markdown(f"### Regime Distribution {info_icon('Shows % of time market was in TREND (up/down), RANGE (sideways), or VOLATILE (jumpy) - pie chart')}" , unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1], vertical_alignment="center")
            
            regime_counts = df['REGIME'].value_counts()
            
            with col1:
                pie_chart = create_regime_distribution_chart(regime_counts)
                st.plotly_chart(pie_chart, use_container_width=True, key="regime_pie_chart")
            
            with col2:
                timeline_df = df.tail(120).copy()
                regime_color_map = {"TREND": "#26A69A", "RANGE": "#4A9EFF", "VOLATILE": "#FF6B6B"}
                timeline_df["Color"] = timeline_df["REGIME"].map(regime_color_map).fillna("#888888")

                timeline_fig = go.Figure()
                timeline_fig.add_trace(go.Scatter(
                    x=timeline_df["Date"],
                    y=[1] * len(timeline_df),
                    mode="markers",
                    marker=dict(size=10, color=timeline_df["Color"]),
                    hovertemplate="%{x|%Y-%m-%d}<br>%{text}<extra></extra>",
                    text=timeline_df["REGIME"],
                    showlegend=False
                ))
                timeline_fig.update_layout(
                    title=dict(
                        text="Regime Timeline (Last 120 Days)",
                        font=dict(size=16, color="#FFFFFF", family="Inter, -apple-system, sans-serif"),
                        x=0.5,
                        xanchor="center"
                    ),
                    height=400,
                    plot_bgcolor="#262730",
                    paper_bgcolor="#262730",
                    font=dict(color="#FFFFFF", family="Inter, -apple-system, sans-serif", size=12),
                    xaxis=dict(gridcolor="#2A2A2A", showgrid=True),
                    yaxis=dict(visible=False),
                    margin=dict(t=60, b=40, l=20, r=20)
                )
                st.plotly_chart(timeline_fig, use_container_width=True, key="regime_timeline_chart")
        
        with tab1:
            st.markdown('<div class="section-container" style="padding: 2rem;">', unsafe_allow_html=True)
            st.markdown("### Price Action Analysis", unsafe_allow_html=True)
            
            # Parameters
            pa_col1, pa_col2, pa_col3 = st.columns(3)
            with pa_col1:
                st.markdown(f"Lookback Period {info_icon('Number of recent candles to analyze for support/resistance zones and market structure. Higher = more historical data, Lower = more recent focus')}", unsafe_allow_html=True)
                lookback_period = st.slider("Lookback Period", 10, 100, 50, key="pa_lookback", label_visibility="collapsed")
            with pa_col2:
                st.markdown(f"Zone Width (pts) {info_icon('How wide the support/resistance zones are in price points. Wider zones = more touches detected but less precise, Narrower zones = more precise but may miss nearby reactions')}", unsafe_allow_html=True)
                zone_width = st.slider("Zone Width (pts)", 0.5, 3.0, 1.5, step=0.5, key="zone_width", label_visibility="collapsed")
            with pa_col3:
                st.markdown(f"MA Period {info_icon('Moving Average period used in price action charts. Lower = responds faster to price changes, Higher = smoother but slower to react')}", unsafe_allow_html=True)
                ma_period = st.slider("MA Period", 5, 50, 20, key="pa_ma", label_visibility="collapsed")
            
            recent_df = df.tail(lookback_period).copy()
            current_price = recent_df['Close'].iloc[-1]
            recent_20 = df.tail(20)
            
            # ========== MARKET STRUCTURE ==========
            st.markdown(f"### Market Structure {info_icon('Where price is + direction + last break = structure context')}", unsafe_allow_html=True)
            
            swing_high = recent_20['High'].max()
            swing_low = recent_20['Low'].min()
            higher_high = recent_df['High'].iloc[-5:].max() > recent_df['High'].iloc[-15:-5].max()
            higher_low = recent_df['Low'].iloc[-5:].min() > recent_df['Low'].iloc[-15:-5].min()
            lower_low = recent_df['Low'].iloc[-5:].min() < recent_df['Low'].iloc[-15:-5].min()
            lower_high = recent_df['High'].iloc[-5:].max() < recent_df['High'].iloc[-15:-5].max()
            
            if higher_high and higher_low:
                trend = "UPTREND"
                trend_color = "#00D084"
            elif lower_low and lower_high:
                trend = "DOWNTREND"
                trend_color = "#FF4444"
            else:
                trend = "SIDEWAYS"
                trend_color = "#FFB81C"
            
            break_dist = ((current_price - swing_high) / current_price * 100) if current_price > swing_high else ((swing_low - current_price) / current_price * 100)
            
            st.markdown(
                f"""
                <div style='display: grid; grid-template-columns: 1.1fr 1fr 1fr 1fr; gap: 0.9rem; margin-top: 0.6rem;'>
                    <div style='background: rgba({trend_color[1:3]}, {trend_color[3:5]}, {trend_color[5:7]}, 0.12); border-left: 4px solid {trend_color}; padding: 1rem; border-radius: 8px;'>
                        <div style='color: #9AA0A6; font-size: 0.75rem; letter-spacing: 0.4px;'>TREND</div>
                        <div style='color: {trend_color}; font-weight: 700; font-size: 1.2rem; margin-top: 0.4rem;'>{trend}</div>
                    </div>
                    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;'>
                        <div style='color: #9AA0A6; font-size: 0.75rem; letter-spacing: 0.4px;'>SWING HIGH</div>
                        <div style='font-weight: 600; font-size: 1.1rem; margin-top: 0.4rem;'>${swing_high:.2f}</div>
                    </div>
                    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;'>
                        <div style='color: #9AA0A6; font-size: 0.75rem; letter-spacing: 0.4px;'>SWING LOW</div>
                        <div style='font-weight: 600; font-size: 1.1rem; margin-top: 0.4rem;'>${swing_low:.2f}</div>
                    </div>
                    <div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;'>
                        <div style='color: #9AA0A6; font-size: 0.75rem; letter-spacing: 0.4px;'>VS STRUCTURE</div>
                        <div style='font-weight: 600; font-size: 1.1rem; margin-top: 0.4rem;'>{break_dist:+.2f}%</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:1rem 0;'>", unsafe_allow_html=True)
            
            # Price action levels for this tab
            recent_50 = df.tail(50)
            resistance_1 = recent_50['High'].max()
            resistance_2 = recent_50['High'].nlargest(2).iloc[-1] if len(recent_50) >= 2 else resistance_1
            support_1 = recent_50['Low'].min()
            support_2 = recent_50['Low'].nsmallest(2).iloc[-1] if len(recent_50) >= 2 else support_1
            recent_day = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
            pivot = (recent_day['High'] + recent_day['Low'] + recent_day['Close']) / 3
            r1 = 2 * pivot - recent_day['Low']
            r2 = pivot + (recent_day['High'] - recent_day['Low'])
            s1 = 2 * pivot - recent_day['High']
            s2 = pivot - (recent_day['High'] - recent_day['Low'])
            
            trend_bias = "BUY" if trend == "UPTREND" else "SELL" if trend == "DOWNTREND" else "HOLD"
            if trend_bias == "BUY":
                entry_point_1 = min(current_price * 0.99, s1)
                entry_point_2 = support_1 * 1.01
                exit_target = min(r1, resistance_1)
                stop_loss_price = max(support_1, current_price * 0.95)
            elif trend_bias == "SELL":
                entry_point_1 = max(current_price * 1.01, r1)
                entry_point_2 = resistance_1 * 0.99
                exit_target = max(s1, support_1)
                stop_loss_price = min(resistance_1, current_price * 1.05)
            else:
                entry_point_1 = s1
                entry_point_2 = support_1
                exit_target = r1
                stop_loss_price = support_1
            
            # SUPPORT & RESISTANCE - LARGE & CLEAR
            st.markdown("<div style='font-size:1.2rem; font-weight:700; color:#fff; margin-bottom:1.5rem;'>Key Price Levels</div>", unsafe_allow_html=True)
            
            levels_cols = st.columns(6)
            level_data = [
                ("R2", resistance_2, "#EF5350", "Resistance 2"),
                ("R1", resistance_1, "#FF6B6B", "Resistance 1"),
                ("Pivot", pivot, "#FFC107", "Pivot Point"),
                ("S1", support_1, "#4CAF50", "Support 1"),
                ("S2", support_2, "#26A69A", "Support 2"),
                ("Now", current_price, "#4A9EFF", "Current Price")
            ]
            
            for label, price, color, full_name in level_data:
                distance = ((price / current_price - 1) * 100)
                col = levels_cols[level_data.index((label, price, color, full_name))]
                col.markdown(f"""
                <div style='background:#0e0e1a; border-top:4px solid {color}; border-radius:10px; padding:1.2rem;'>
                    <div style='font-size:0.7rem; color:#999; margin-bottom:0.3rem; text-transform:uppercase; letter-spacing:0.5px;'>{label}</div>
                    <div style='font-size:1.8rem; font-weight:800; color:{color}; margin:0.6rem 0;'>{price:.2f}</div>
                    <div style='font-size:0.7rem; color:#888; margin-top:0.2rem;'>{distance:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin:2.5rem 0;'></div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:1rem 0;'>", unsafe_allow_html=True)
            
            # ========== STRONG SUPPORT & RESISTANCE ZONES ==========
            st.markdown(f"### Key Reaction Zones {info_icon('These are price zones (ranges), not single lines, where price repeatedly reacts. A touch means the high/low enters the zone. More touches = stronger zone: 1-2 weak, 3-4 moderate, 5+ strong. Zones are built from recent 50 candles using the highest high (resistance) and lowest low (support), then widened by the zone width setting.')}", unsafe_allow_html=True)
            
            # Calculate zones
            recent_50 = df.tail(50)
            r1_level = recent_50['High'].max()
            s1_level = recent_50['Low'].min()
            r1_zone_high = r1_level + zone_width
            r1_zone_low = r1_level - zone_width
            s1_zone_high = s1_level + zone_width
            s1_zone_low = s1_level - zone_width
            
            # Count touches
            r1_touches = len(recent_50[recent_50['High'] >= r1_zone_low]) if len(recent_50) > 0 else 0
            s1_touches = len(recent_50[recent_50['Low'] <= s1_zone_high]) if len(recent_50) > 0 else 0
            
            def get_zone_strength(touches):
                if touches >= 5:
                    return "STRONG", "#00D084"
                elif touches >= 3:
                    return "MODERATE", "#FFB81C"
                else:
                    return "WEAK", "#888888"
            
            r1_strength, r1_color = get_zone_strength(r1_touches)
            s1_strength, s1_color = get_zone_strength(s1_touches)
            
            in_r1 = "IN ZONE" if (current_price >= r1_zone_low and current_price <= r1_zone_high) else "OUTSIDE"
            in_s1 = "IN ZONE" if (current_price >= s1_zone_low and current_price <= s1_zone_high) else "OUTSIDE"
            
            zone_col1, zone_col2 = st.columns(2, gap="large")
            with zone_col1:
                st.markdown(
                    f"""
                    <div style='background: rgba(255, 68, 68, 0.08); border-left: 4px solid #FF4444; padding: 1.2rem; border-radius: 8px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;'>
                            <div style='color: #9AA0A6; font-size: 0.75rem; letter-spacing: 0.4px;'>RESISTANCE ZONE</div>
                            <div style='font-size: 0.7rem; color: #FFB81C; border: 1px solid rgba(255, 184, 28, 0.35); padding: 0.15rem 0.5rem; border-radius: 999px;'>
                                {in_r1}
                            </div>
                        </div>
                        <div style='font-weight: 700; font-size: 1.3rem; margin-bottom: 0.4rem;'>${r1_level:.2f}</div>
                        <div style='color: #C7CDD4; font-size: 0.9rem; margin-bottom: 0.8rem;'>± ${zone_width:.2f} band</div>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <div style='color: #9AA0A6; font-size: 0.75rem;'>STRENGTH</div>
                                <div style='color: {r1_color}; font-weight: 600; margin-top: 0.2rem;'>{r1_strength}</div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='color: #9AA0A6; font-size: 0.75rem;'>TOUCHES</div>
                                <div style='color: #FFB81C; font-weight: 700; font-size: 1.2rem; margin-top: 0.2rem;'>{r1_touches}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with zone_col2:
                st.markdown(
                    f"""
                    <div style='background: rgba(0, 208, 132, 0.08); border-left: 4px solid #00D084; padding: 1.2rem; border-radius: 8px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;'>
                            <div style='color: #9AA0A6; font-size: 0.75rem; letter-spacing: 0.4px;'>SUPPORT ZONE</div>
                            <div style='font-size: 0.7rem; color: #00D084; border: 1px solid rgba(0, 208, 132, 0.35); padding: 0.15rem 0.5rem; border-radius: 999px;'>
                                {in_s1}
                            </div>
                        </div>
                        <div style='font-weight: 700; font-size: 1.3rem; margin-bottom: 0.4rem;'>${s1_level:.2f}</div>
                        <div style='color: #C7CDD4; font-size: 0.9rem; margin-bottom: 0.8rem;'>± ${zone_width:.2f} band</div>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <div style='color: #9AA0A6; font-size: 0.75rem;'>STRENGTH</div>
                                <div style='color: {s1_color}; font-weight: 600; margin-top: 0.2rem;'>{s1_strength}</div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='color: #9AA0A6; font-size: 0.75rem;'>TOUCHES</div>
                                <div style='color: #00D084; font-weight: 700; font-size: 1.2rem; margin-top: 0.2rem;'>{s1_touches}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:1rem 0;'>", unsafe_allow_html=True)
            
            
            # ========== PRICE ACTION CHART ==========
            st.markdown(
                f"""
                <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem;'>
                    <div style='font-size: 1.2rem; font-weight: 600;'>Price Action Chart {info_icon('Zones highlighted. Watch bounces off support/resistance')}</div>
                    <div style='color: #9AA0A6; font-size: 0.8rem;'>Candles + MA + Zones</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<div style='margin: 0.6rem 0 1rem 0; height: 1px; background: rgba(255,255,255,0.08);'></div>", unsafe_allow_html=True)
            
            fig = go.Figure()
            
            # Candlesticks
            fig.add_trace(go.Candlestick(
                x=recent_df.index, open=recent_df['Open'], high=recent_df['High'],
                low=recent_df['Low'], close=recent_df['Close'], name='Price',
                increasing_line_color='#00D084', decreasing_line_color='#FF4444'
            ))
            
            # Zones with fill
            fig.add_hrect(y0=r1_zone_low, y1=r1_zone_high, fillcolor="#FF4444", opacity=0.12, layer="below", annotation_text="Resistance", annotation_position="right")
            fig.add_hrect(y0=s1_zone_low, y1=s1_zone_high, fillcolor="#00D084", opacity=0.12, layer="below", annotation_text="Support", annotation_position="right")
            
            # Moving average
            ma = recent_df['Close'].rolling(window=ma_period).mean()
            fig.add_trace(go.Scatter(x=recent_df.index, y=ma, name=f'{ma_period}-MA', line=dict(color='#FFD700', width=2.5)))
            
            fig.update_layout(
                title="", height=520, plot_bgcolor='#262730', paper_bgcolor='#262730',
                font=dict(color='#ffffff', family='Arial, sans-serif'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.08)', showline=False, zeroline=False),
                yaxis=dict(gridcolor='rgba(255,255,255,0.08)', showline=False, zeroline=False),
                hovermode='x unified', xaxis_rangeslider=dict(visible=False),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(t=10, b=10, l=40, r=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab2:
            st.subheader("Advanced Signal Analysis")

            param_col1, param_col2, param_col3 = st.columns(3)
            with param_col1:
                st.markdown(f"Profit Target (%) {info_icon('The profit percentage at which a successful trade exits. Example: 5% means if you buy at 100 SAR, you sell at 105 SAR for profit')}", unsafe_allow_html=True)
                profit_target = st.slider("Profit Target (%)", 1.0, 15.0, 5.0, step=0.5, label_visibility="collapsed") / 100
            with param_col2:
                st.markdown(f"Stop Loss (%) {info_icon('The loss percentage at which a losing trade exits to limit damage. Example: 3% means if you buy at 100 SAR, you automatically sell at 97 SAR to prevent bigger losses')}", unsafe_allow_html=True)
                stop_loss = st.slider("Stop Loss (%)", 1.0, 12.0, 3.0, step=0.5, label_visibility="collapsed") / 100
            with param_col3:
                st.markdown(f"Holding Period (days) {info_icon('Maximum number of days to hold a trade before exiting. If neither profit target nor stop loss is hit within this period, the trade closes automatically')}", unsafe_allow_html=True)
                holding_period = st.slider("Holding Period (days)", 5, 60, 20, label_visibility="collapsed")

            with st.spinner("Analyzing signals for selected date range..."):
                signals_df = detect_signals(df)
                results, successful_signals, all_signal_details = evaluate_signal_success(
                    df, signals_df, profit_target, holding_period, stop_loss
                )
                consensus_signals = find_consensus_signals(signals_df)
                combo_results = analyze_indicator_combinations(signals_df, df, profit_target, holding_period, stop_loss)
                monthly_performance = calculate_monthly_performance(all_signal_details)
            
            # Overview metrics
            st.markdown(f"### Performance Overview {info_icon('High-level summary of all signals: total signals generated, success rate, average profit/loss, and profit factor (total gains ÷ total losses)')}", unsafe_allow_html=True)
            
            total_signals = sum([data['total_signals'] for data in results.values()])
            total_successful = sum([data['successful'] for data in results.values()])
            overall_success = (total_successful / total_signals * 100) if total_signals > 0 else 0
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, rgba(74, 158, 255, 0.1) 0%, rgba(74, 158, 255, 0.05) 100%);
                    border-left: 3px solid #4A9EFF;
                    border-radius: 8px;
                    padding: 1.2rem 1rem;
                    backdrop-filter: blur(10px);
                '>
                    <div style='
                        font-size: 0.85rem;
                        color: #888;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 0.8rem;
                        font-weight: 500;
                    '> Total Signals</div>
                    <div style='
                        font-size: 2rem;
                        font-weight: 700;
                        color: #4A9EFF;
                        margin: 0;
                    '>{total_signals}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_col2:
                success_color = "#26A69A"
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, rgba(38, 166, 154, 0.1) 0%, rgba(38, 166, 154, 0.05) 100%);
                    border-left: 3px solid #26A69A;
                    border-radius: 8px;
                    padding: 1.2rem 1rem;
                    backdrop-filter: blur(10px);
                '>
                    <div style='
                        font-size: 0.85rem;
                        color: #888;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 0.8rem;
                        font-weight: 500;
                    '>Successful</div>
                    <div style='
                        font-size: 2rem;
                        font-weight: 700;
                        color: #26A69A;
                        margin: 0;
                    '>{total_successful}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_col3:
                success_color = '#26A69A' if overall_success >= 50 else '#FF6B6B'
                status_icon = "" if overall_success >= 50 else "v"
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, rgba({int('38' if overall_success >= 50 else '255')}, {int('166' if overall_success >= 50 else '107')}, {int('154' if overall_success >= 50 else '107')}, 0.1) 0%, rgba({int('38' if overall_success >= 50 else '255')}, {int('166' if overall_success >= 50 else '107')}, {int('154' if overall_success >= 50 else '107')}, 0.05) 100%);
                    border-left: 3px solid {success_color};
                    border-radius: 8px;
                    padding: 1.2rem 1rem;
                    backdrop-filter: blur(10px);
                '>
                    <div style='
                        font-size: 0.85rem;
                        color: #888;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 0.8rem;
                        font-weight: 500;
                    '>{status_icon} Success Rate</div>
                    <div style='
                        font-size: 2rem;
                        font-weight: 700;
                        color: {success_color};
                        margin: 0;
                    '>{overall_success:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_col4:
                best_combo = max(combo_results.items(), key=lambda x: x[1]['success_rate']) if combo_results else ("N/A", {'success_rate': 0})
                st.markdown(f"""
                <div style='
                    background: linear-gradient(135deg, rgba(167, 139, 250, 0.1) 0%, rgba(167, 139, 250, 0.05) 100%);
                    border-left: 3px solid #A78BFA;
                    border-radius: 8px;
                    padding: 1.2rem 1rem;
                    backdrop-filter: blur(10px);
                '>
                    <div style='
                        font-size: 0.85rem;
                        color: #888;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        margin-bottom: 0.8rem;
                        font-weight: 500;
                    '>Best Combo</div>
                    <div style='
                        font-size: 2rem;
                        font-weight: 700;
                        color: #A78BFA;
                        margin: 0;
                    '>{best_combo[1]['success_rate']:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Create sub-tabs for different analyses
            analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
                "Indicator Analysis",
                "Indicator Combinations",
                "Signal Timeline & History"
            ])
            
            with analysis_tab1:
                st.markdown('<div class="section-container" style="padding: 2rem;">', unsafe_allow_html=True)

                # ==================== BUILD INDICATOR PERFORMANCE DATA ====================
                indicator_map = {
                    "EMA": ("EMA 20/50/200", "Trend Following", "Identifies and follows directional trends with multiple EMAs", create_ema_chart),
                    "ADX": ("ADX (14)", "Trend Strength", "Measures trend intensity and momentum directionality", create_adx_chart),
                    "RSI": ("RSI (14)", "Momentum", "Detects overbought/oversold conditions and reversals", create_rsi_chart),
                    "MACD": ("MACD (12/26/9)", "Momentum Confirmation", "Confirms trend changes and momentum shifts", create_macd_chart),
                    "BB": ("Bollinger Bands", "Volatility and Support", "Shows volatility levels and potential support or resistance", create_bollinger_bands_chart),
                    "STOCH": ("Stochastic", "Reversal Signals", "Identifies potential reversal points in the market", create_stochastic_chart),
                }

                # Calculate all metrics
                perf_rows = []
                regime_rows = []
                indicator_performance = []
                
                for key, (name, desc, detail, chart_func) in indicator_map.items():
                    if key not in results:
                        continue
                    data = results[key]
                    total = data.get("total_signals", 0)
                    if total <= 0:
                        continue
                    
                    win_rate = data.get('success_rate', 0)
                    avg_gain = data.get('avg_gain', 0)
                    avg_loss = data.get('avg_loss', 0)
                    expectancy = (win_rate / 100) * avg_gain + (1 - win_rate / 100) * avg_loss
                    
                    regime_perf = data.get("regime_performance", {})
                    best_regime_for_ind = max(regime_perf, key=regime_perf.get) if regime_perf else ""
                    
                    indicator_signals = [s for s in all_signal_details if s['indicator'] == key]
                    indicator_signals = sorted(indicator_signals, key=lambda s: pd.to_datetime(s['date']))
                    
                    win_days = [s['days_held'] for s in indicator_signals if s['success']]
                    loss_days = [s['days_held'] for s in indicator_signals if not s['success']]
                    med_win_days = float(np.median(win_days)) if win_days else 0.0
                    med_loss_days = float(np.median(loss_days)) if loss_days else 0.0

                    for regime in ["TREND", "RANGE", "VOLATILE"]:
                        regime_signals = [s for s in indicator_signals if s.get('regime') == regime]
                        if not regime_signals:
                            continue
                        regime_returns = [s['gain'] / 100 for s in regime_signals]
                        regime_wins = [s for s in regime_signals if s['success']]
                        regime_win_rate = (len(regime_wins) / len(regime_signals)) * 100
                        regime_avg_gain = float(np.mean([r for r in regime_returns if r > 0])) * 100 if regime_returns else 0
                        regime_avg_loss = float(np.mean([r for r in regime_returns if r < 0])) * 100 if regime_returns else 0
                        regime_expect = (regime_win_rate / 100) * regime_avg_gain + (1 - regime_win_rate / 100) * regime_avg_loss
                        regime_rows.append({
                            "Indicator": key,
                            "Regime": regime,
                            "Signals": len(regime_signals),
                            "Win %": regime_win_rate,
                            "Expectancy %": regime_expect,
                        })

                    perf_rows.append({
                        "indicator": key,
                        "total": total,
                        "win_rate": win_rate,
                        "avg_gain": avg_gain,
                        "avg_loss": avg_loss,
                        "profit_factor": data.get('profit_factor', 0),
                        "avg_hold": data.get('avg_hold_time', 0),
                        "expectancy": expectancy,
                        "med_win_days": med_win_days,
                        "med_loss_days": med_loss_days,
                    })
                    
                    indicator_performance.append({
                        "key": key,
                        "name": name,
                        "desc": desc,
                        "detail": detail,
                        "accuracy": win_rate,
                        "win_rate": win_rate,
                        "total_signals": total,
                        "avg_gain": avg_gain,
                        "avg_loss": avg_loss,
                        "profit_factor": data.get('profit_factor', 0),
                        "best_regime": best_regime_for_ind,
                        "regime_performance": regime_perf,
                        "chart_func": chart_func,
                        "max_gain": data.get("max_gain", 0),
                        "max_loss": data.get("max_loss", 0),
                    })

                indicator_performance.sort(key=lambda x: (x["accuracy"], x["total_signals"]), reverse=True)
                top_indicators = indicator_performance[:4]

                # ==================== TOP 4 INDICATORS - HERO CARDS ====================
                st.markdown("### ⭐ Top Performing Indicators")
                if not top_indicators:
                    st.info("No indicator signals available to analyze.")
                else:
                    rank_cols = st.columns(len(top_indicators), gap="small")
                    for idx, (col, ind) in enumerate(zip(rank_cols, top_indicators)):
                        with col:
                            if ind["accuracy"] >= 60:
                                color = "#26A69A"
                                badge = "EXCELLENT"
                            elif ind["accuracy"] >= 50:
                                color = "#4CAF50"
                                badge = "GOOD"
                            elif ind["accuracy"] >= 40:
                                color = "#FFB74D"
                                badge = "FAIR"
                            else:
                                color = "#FF6B6B"
                                badge = "WEAK"

                            rank_html = f"""
                            <div style='background: linear-gradient(135deg, {color}10 0%, {color}05 100%);
                                        border: 2px solid {color}60; border-radius: 12px; padding: 1.2rem 0.8rem;
                                        text-align: center; backdrop-filter: blur(10px);'>
                                <div style='font-size: 0.65rem; color: {color}; text-transform: uppercase;
                                            letter-spacing: 1.2px; font-weight: 800; margin-bottom: 0.3rem;'>
                                    #{idx+1} {badge}
                                </div>
                                <div style='font-size: 0.95rem; font-weight: 900; color: #fff; margin: 0.6rem 0;'>
                                    {ind["name"]}
                                </div>
                                <div style='font-size: 0.7rem; color: #aaa; margin-bottom: 0.8rem; line-height: 1.3;'>
                                    {ind["desc"]}
                                </div>
                                <div style='background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
                                            border-radius: 6px; padding: 0.6rem; margin-bottom: 0.6rem;'>
                                    <div style='font-size: 2rem; font-weight: 900; color: #fff; line-height: 1;'>
                                        {ind["accuracy"]:.0f}%
                                    </div>
                                </div>
                                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; font-size: 0.7rem;'>
                                    <div style='background: #ffffff05; border-radius: 4px; padding: 0.3rem;'>
                                        <div style='color: #888;'>Signals</div>
                                        <div style='color: #fff; font-weight: 700;'>{ind["total_signals"]}</div>
                                    </div>
                                    <div style='background: #ffffff05; border-radius: 4px; padding: 0.3rem;'>
                                        <div style='color: #888;'>Profit Factor</div>
                                        <div style='color: {color}; font-weight: 700;'>{ind["profit_factor"]:.2f}x</div>
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(rank_html, unsafe_allow_html=True)

                    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

                    # ==================== DETAILED ANALYSIS ====================
                    st.markdown("### Detailed Analysis")

                    for rank_idx, indicator in enumerate(top_indicators):
                        with st.expander(f"#{rank_idx+1} {indicator['name']} ({indicator['accuracy']:.0f}% Win Rate)", expanded=(rank_idx == 0)):
                            expectancy = (indicator['win_rate'] / 100) * indicator['avg_gain'] + (1 - indicator['win_rate'] / 100) * indicator['avg_loss']
                            regime_perf = indicator.get('regime_performance', {})
                            best_regime = max(regime_perf, key=regime_perf.get) if regime_perf else "N/A"
                            worst_regime = min(regime_perf, key=regime_perf.get) if regime_perf else "N/A"

                            if indicator['accuracy'] >= 60:
                                tier_color = "#26A69A"
                                tier_label = "ELITE"
                            elif indicator['accuracy'] >= 50:
                                tier_color = "#4CAF50"
                                tier_label = "STRONG"
                            elif indicator['accuracy'] >= 40:
                                tier_color = "#FFB74D"
                                tier_label = "SOLID"
                            else:
                                tier_color = "#FF6B6B"
                                tier_label = "WEAK"

                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, {tier_color}15 0%, #0e0e18 60%);
                                        border: 2px solid {tier_color}50; border-radius: 12px; padding: 1.4rem; margin-bottom: 1rem;'>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <div>
                                        <div style='font-size: 0.7rem; letter-spacing: 1.2px; color: {tier_color}; font-weight: 800;'>
                                            {tier_label} TIER
                                        </div>
                                        <div style='font-size: 1.4rem; font-weight: 800; color: #fff; margin-top: 0.3rem;'>
                                            {indicator['name']}
                                        </div>
                                        <div style='font-size: 0.85rem; color: #9aa0a6; margin-top: 0.3rem;'>
                                            {indicator['desc']}
                                        </div>
                                    </div>
                                    <div style='text-align: right;'>
                                        <div style='font-size: 2.4rem; font-weight: 900; color: {tier_color}; line-height: 1;'>
                                            {indicator['accuracy']:.0f}%
                                        </div>
                                        <div style='font-size: 0.7rem; color: #9aa0a6; text-transform: uppercase;'>Win Rate</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                            kpi_col1.metric("Profit Factor", f"{indicator['profit_factor']:.2f}x")
                            kpi_col2.metric("Expectancy", f"{expectancy:+.2f}%")
                            kpi_col3.metric("Signals", indicator['total_signals'])
                            kpi_col4.metric("Best Regime", best_regime)

                            indicator_signals = [
                                s for s in all_signal_details
                                if indicator['key'] in s.get('indicator', '').upper()
                            ]
                            signals_total = len(indicator_signals)
                            signals_wins = sum(1 for s in indicator_signals if s.get('success'))
                            signals_losses = signals_total - signals_wins
                            avg_hold_days = float(np.mean([s.get('days_held', 0) for s in indicator_signals])) if indicator_signals else 0.0

                            st.markdown("<div style='margin: 0.6rem 0;'></div>", unsafe_allow_html=True)

                            sig_col1, sig_col2, sig_col3, sig_col4 = st.columns(4)
                            sig_col1.metric("Total Signals", signals_total)
                            sig_col2.metric("Winners", signals_wins)
                            sig_col3.metric("Losers", signals_losses)
                            sig_col4.metric("Avg Hold (days)", f"{avg_hold_days:.1f}")

                            st.markdown("<div style='margin: 0.8rem 0;'></div>", unsafe_allow_html=True)

                            info_col1, info_col2 = st.columns([1.05, 1], gap="large")

                            with info_col1:
                                st.markdown(f"""
                                <div style='background: #0e0e1a; border-radius: 10px; padding: 1.3rem;'>
                                    <div style='font-size: 0.9rem; color: #999; margin-bottom: 0.8rem; font-weight: 700;'>
                                        Indicator Summary
                                    </div>
                                    <div style='font-size: 1rem; color: #ccc; line-height: 1.5;'>
                                        {indicator['detail']}
                                    </div>
                                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-top: 1.2rem;'>
                                        <div style='background: #26A69A15; border-left: 3px solid #26A69A; padding: 0.8rem; border-radius: 6px;'>
                                            <div style='font-size: 0.7rem; color: #888; text-transform: uppercase;'>Best Regime</div>
                                            <div style='font-size: 1.05rem; font-weight: 700; color: #26A69A; margin-top: 0.2rem;'>
                                                {best_regime}
                                            </div>
                                        </div>
                                        <div style='background: #FF6B6B15; border-left: 3px solid #FF6B6B; padding: 0.8rem; border-radius: 6px;'>
                                            <div style='font-size: 0.7rem; color: #888; text-transform: uppercase;'>Worst Regime</div>
                                            <div style='font-size: 1.05rem; font-weight: 700; color: #FF6B6B; margin-top: 0.2rem;'>
                                                {worst_regime}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            with info_col2:
                                st.markdown("""
                                <div style='background: #0e0e1a; border-radius: 10px; padding: 1.3rem;'>
                                    <div style='font-size: 0.9rem; color: #999; margin-bottom: 0.8rem; font-weight: 700;'>
                                        Performance Snapshot
                                    </div>
                                """, unsafe_allow_html=True)

                                snap_col1, snap_col2 = st.columns(2)
                                with snap_col1:
                                    st.metric("Avg Gain", f"{indicator['avg_gain']:.2f}%")
                                with snap_col2:
                                    st.metric("Avg Loss", f"{indicator['avg_loss']:.2f}%")

                                snap_col3, snap_col4 = st.columns(2)
                                with snap_col3:
                                    st.metric("Max Gain", f"+{indicator['max_gain']:.2f}%")
                                with snap_col4:
                                    st.metric("Max Loss", f"{indicator['max_loss']:.2f}%")

                                st.markdown("</div>", unsafe_allow_html=True)

                            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

                            st.markdown("""
                            <div style='background: #0e0e1a; border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem;'>
                                <div style='font-size: 0.9rem; color: #999; margin-bottom: 0.8rem; font-weight: 700;'>
                                    Regime Performance
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            if regime_perf:
                                regimes_list = [("TREND", "#26A69A"), ("RANGE", "#FFC107"), ("VOLATILE", "#EF5350")]
                                for regime, r_color in regimes_list:
                                    win_rate_reg = regime_perf.get(regime, 0)
                                    bar_width = max(6, min(100, win_rate_reg))
                                    st.markdown(f"""
                                    <div style='margin-bottom: 0.6rem;'>
                                        <div style='display: flex; justify-content: space-between; margin-bottom: 0.3rem;'>
                                            <div style='font-size: 0.85rem; font-weight: 700; color: #fff;'>{regime}</div>
                                            <div style='font-size: 0.85rem; font-weight: 800; color: {r_color};'>{win_rate_reg:.1f}%</div>
                                        </div>
                                        <div style='background: rgba(100,100,100,0.2); border-radius: 4px; height: 20px; overflow: hidden;'>
                                            <div style='background: linear-gradient(90deg, {r_color}, {r_color}dd); width: {bar_width}%; height: 100%;'></div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.info("No regime performance data available for this indicator.")

                            st.markdown("<div style='margin: 1.4rem 0;'></div>", unsafe_allow_html=True)
                            st.markdown("### Price Chart with Signals")

                            try:
                                chart = indicator["chart_func"](df)
                                st.plotly_chart(chart, use_container_width=True, key=f"chart_{indicator['key']}_{rank_idx}")
                            except Exception as e:
                                st.error(f"Could not render {indicator['name']}: {str(e)}")

                    # ==================== FULL PERFORMANCE TABLE ====================
                    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                    st.markdown("### All Indicators Summary")
                    if perf_rows:
                        perf_df = pd.DataFrame(perf_rows)
                        perf_df = perf_df[[
                            "indicator", "total", "win_rate", "avg_gain", "avg_loss",
                            "profit_factor", "avg_hold", "expectancy", "med_win_days", "med_loss_days"
                        ]].rename(columns={
                            "indicator": "Indicator",
                            "total": "# Trades",
                            "win_rate": "Win Rate %",
                            "avg_gain": "Avg Win %",
                            "avg_loss": "Avg Loss %",
                            "profit_factor": "Gain/Loss Ratio",
                            "avg_hold": "Avg Days Held",
                            "expectancy": "Avg Return %",
                            "med_win_days": "Typical Win Duration (days)",
                            "med_loss_days": "Typical Loss Duration (days)",
                        })
                        st.dataframe(
                            perf_df.sort_values(["Win Rate %", "# Trades"], ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )

                    # ==================== PERFORMANCE BY MARKET CONDITION ====================
                    if regime_rows:
                        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                        st.markdown("### Performance by Market Condition")
                        regime_df = pd.DataFrame(regime_rows).sort_values(["Indicator", "Regime"], ascending=True)
                        
                        viz_col1, viz_col2 = st.columns([1.2, 1], gap="large")
                        
                        with viz_col1:
                            fig_win = go.Figure()
                            
                            for regime in ["TREND", "RANGE", "VOLATILE"]:
                                regime_data = regime_df[regime_df["Regime"] == regime]
                                color = "#26A69A" if regime == "TREND" else "#FFC107" if regime == "RANGE" else "#EF5350"
                                fig_win.add_trace(go.Bar(
                                    name=regime,
                                    x=regime_data["Indicator"],
                                    y=regime_data["Win %"],
                                    marker_color=color,
                                    text=regime_data["Win %"].round(1),
                                    textposition="auto",
                                    hovertemplate="<b>%{x}</b> (%{name})<br>Win Rate: %{y:.1f}%<extra></extra>"
                                ))
                            
                            fig_win.update_layout(
                                title="Win Rate in Different Market Conditions",
                                xaxis_title="Indicator",
                                yaxis_title="Win Rate (%)",
                                barmode="group",
                                height=400,
                                plot_bgcolor="#0e0e18",
                                paper_bgcolor="#0e0e18",
                                font=dict(color="#fff", size=11),
                                hovermode="x unified",
                                xaxis=dict(gridcolor="#1a1a2a"),
                                yaxis=dict(gridcolor="#1a1a2a"),
                                legend=dict(orientation="h", y=1.15, x=0, bgcolor="rgba(0,0,0,0)")
                            )
                            st.plotly_chart(fig_win, use_container_width=True)
                        
                        with viz_col2:
                            fig_exp = go.Figure()
                            
                            for regime in ["TREND", "RANGE", "VOLATILE"]:
                                regime_data = regime_df[regime_df["Regime"] == regime]
                                color = "#26A69A" if regime == "TREND" else "#FFC107" if regime == "RANGE" else "#EF5350"
                                fig_exp.add_trace(go.Scatter(
                                    name=regime,
                                    mode="markers",
                                    x=regime_data["Win %"],
                                    y=regime_data["Expectancy %"],
                                    marker=dict(
                                        size=regime_data["Signals"] / 5,
                                        color=color,
                                        opacity=0.7,
                                        line=dict(width=1, color="white")
                                    ),
                                    text=regime_data["Indicator"],
                                    hovertemplate="<b>%{text}</b><br>Win Rate: %{x:.1f}%<br>Avg Return: %{y:.2f}%<extra></extra>"
                                ))
                            
                            fig_exp.update_layout(
                                title="Accuracy vs Average Return",
                                xaxis_title="Win Rate (%)",
                                yaxis_title="Average Return (%)",
                                height=400,
                                plot_bgcolor="#0e0e18",
                                paper_bgcolor="#0e0e18",
                                font=dict(color="#fff", size=11),
                                hovermode="closest",
                                xaxis=dict(gridcolor="#1a1a2a"),
                                yaxis=dict(gridcolor="#1a1a2a"),
                                legend=dict(orientation="v", y=0.99, x=0.01, bgcolor="rgba(0,0,0,0)")
                            )
                            st.plotly_chart(fig_exp, use_container_width=True)

                st.markdown("</div>", unsafe_allow_html=True)

            with analysis_tab2:
                st.markdown('<div class="section-container">', unsafe_allow_html=True)
                
                # Top 5 breakdown - Redesigned for smooth, cohesive layout
                if combo_results:
                    sorted_combos = sorted(combo_results.items(), key=lambda x: x[1]['success_rate'], reverse=True)
                    
                    # Create tabs for each top combination with color coding
                    if sorted_combos:
                        tab_labels = []
                        tab_colors = ["#26A69A", "#4A9EFF", "#FFC107", "#FF9800", "#9C27B0"]  # Teal, Blue, Yellow, Orange, Purple
                        
                        for i, (name, _) in enumerate(sorted_combos[:5]):
                            color = tab_colors[i % len(tab_colors)]
                            tab_labels.append(f"#{i+1} - {name}")
                        
                        combo_tabs = st.tabs(tab_labels)
                        
                        for tab_idx, (combo_name, combo_data) in enumerate(sorted_combos[:5]):
                            with combo_tabs[tab_idx]:
                                success_rate = combo_data['success_rate']
                                
                                # Determine performance tier
                                if success_rate >= 60:
                                    tier_color = "#26A69A"
                                    tier_text = "ELITE"
                                    tier_bg = "#26A69A15"
                                elif success_rate >= 50:
                                    tier_color = "#4CAF50"
                                    tier_text = "STRONG"
                                    tier_bg = "#4CAF5015"
                                elif success_rate >= 40:
                                    tier_color = "#FFC107"
                                    tier_text = "SOLID"
                                    tier_bg = "#FFC10715"
                                else:
                                    tier_color = "#FF6B6B"
                                    tier_text = "CAUTION"
                                    tier_bg = "#FF6B6B15"
                                
                                # Hero Banner with Key Stats
                                st.markdown(f"""
                                <div style='background: {tier_bg}; border: 2px solid {tier_color}; 
                                            border-radius: 12px; padding: 1.8rem; margin-bottom: 2rem;'>
                                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;'>
                                        <div style='flex: 1;'>
                                            <div style='display: inline-block; background: {tier_color}; color: #000; 
                                                        padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.7rem; 
                                                        font-weight: 800; letter-spacing: 1.5px; margin-bottom: 0.8rem;'>
                                                {tier_text} TIER
                                            </div>
                                            <div style='font-size: 1.7rem; font-weight: 800; color: #fff; line-height: 1.2;'>
                                                {combo_name}
                                            </div>
                                        </div>
                                        <div style='text-align: right; padding-left: 2rem;'>
                                            <div style='font-size: 3rem; font-weight: 900; color: {tier_color}; line-height: 1;'>
                                                {success_rate:.1f}%
                                            </div>
                                            <div style='font-size: 0.75rem; color: #999; text-transform: uppercase; margin-top: 0.3rem;'>
                                                Success Rate
                                            </div>
                                        </div>
                                    </div>
                                    <div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; 
                                                border-top: 1px solid {tier_color}40; padding-top: 1.2rem;'>
                                        <div style='text-align: center;'>
                                            <div style='font-size: 0.7rem; color: #999; margin-bottom: 0.3rem;'>TOTAL SIGNALS</div>
                                            <div style='font-size: 1.4rem; font-weight: 700; color: #fff;'>{int(combo_data['total'])}</div>
                                        </div>
                                        <div style='text-align: center;'>
                                            <div style='font-size: 0.7rem; color: #999; margin-bottom: 0.3rem;'>SIGNAL WINNERS</div>
                                            <div style='font-size: 1.4rem; font-weight: 700; color: #26A69A;'>{int(combo_data["total"] * combo_data["success_rate"] / 100)}</div>
                                            <div style='font-size: 0.65rem; color: #26A69A; margin-top: 0.2rem;'>{combo_data["success_rate"]:.0f}% Win</div>
                                        </div>
                                        <div style='text-align: center;'>
                                            <div style='font-size: 0.7rem; color: #999; margin-bottom: 0.3rem;'>SIGNAL LOSERS</div>
                                            <div style='font-size: 1.4rem; font-weight: 700; color: #EF5350;'>{int(combo_data["total"] * (100 - combo_data["success_rate"]) / 100)}</div>
                                            <div style='font-size: 0.65rem; color: #EF5350; margin-top: 0.2rem;'>{(100 - combo_data["success_rate"]):.0f}% Loss</div>
                                        </div>
                                        <div style='text-align: center;'>
                                            <div style='font-size: 0.7rem; color: #999; margin-bottom: 0.3rem;'>AVG HOLD</div>
                                            <div style='font-size: 1.4rem; font-weight: 700; color: #4A9EFF;'>{combo_data['avg_hold']:.0f}d</div>
                                        </div>
                                        <div style='text-align: center;'>
                                            <div style='font-size: 0.7rem; color: #999; margin-bottom: 0.3rem;'>AVG RETURN</div>
                                            <div style='font-size: 1.4rem; font-weight: 700; color: {"#26A69A" if combo_data["expectancy"] > 0 else "#EF5350"};'>{combo_data['expectancy']:+.2f}%</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Two-Column Layout for Performance Details
                                perf_col1, perf_col2 = st.columns(2, gap="large")
                                
                                with perf_col1:
                                    # Return Performance Card - Redesigned
                                    st.markdown(f"""
                                    <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                                                border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;
                                                border-left: 4px solid #26A69A; box-shadow: 0 4px 12px rgba(0,0,0,0.3);'>
                                        <div style='font-size: 1.2rem; font-weight: 800; color: #fff; margin-bottom: 1.2rem;'>
                                            Return Performance
                                        </div>
                                        <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;'>
                                            <div style='background: rgba(38, 166, 154, 0.1); padding: 1rem; border-radius: 8px; 
                                                        border-left: 3px solid #26A69A;'>
                                                <div style='font-size: 0.75rem; color: #999; font-weight: 600; margin-bottom: 0.4rem;'>Avg Gain</div>
                                                <div style='font-size: 1.6rem; font-weight: 800; color: #26A69A;'>+{combo_data['avg_gain']:.2f}%</div>
                                            </div>
                                            <div style='background: rgba(76, 175, 80, 0.1); padding: 1rem; border-radius: 8px; 
                                                        border-left: 3px solid #4CAF50;'>
                                                <div style='font-size: 0.75rem; color: #999; font-weight: 600; margin-bottom: 0.4rem;'>Max Gain</div>
                                                <div style='font-size: 1.6rem; font-weight: 800; color: #4CAF50;'>+{combo_data['max_gain']:.2f}%</div>
                                            </div>
                                            <div style='background: rgba(239, 83, 80, 0.1); padding: 1rem; border-radius: 8px; 
                                                        border-left: 3px solid #EF5350;'>
                                                <div style='font-size: 0.75rem; color: #999; font-weight: 600; margin-bottom: 0.4rem;'>Avg Loss</div>
                                                <div style='font-size: 1.6rem; font-weight: 800; color: #EF5350;'>{combo_data.get('avg_loss', 0):.2f}%</div>
                                            </div>
                                            <div style='background: rgba(255, 152, 0, 0.1); padding: 1rem; border-radius: 8px; 
                                                        border-left: 3px solid #FF9800;'>
                                                <div style='font-size: 0.75rem; color: #999; font-weight: 600; margin-bottom: 0.4rem;'>Max Loss</div>
                                                <div style='font-size: 1.6rem; font-weight: 800; color: #FF9800;'>{combo_data['max_loss']:.2f}%</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                
                                with perf_col2:
                                    # Performance by Regime - Redesigned
                                    regime_perf = combo_data.get('regime_performance', {})
                                    st.markdown("""
                                    <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                                                border-radius: 10px; padding: 1.5rem; margin-bottom: 1.5rem;
                                                border-left: 4px solid #FF9800; box-shadow: 0 4px 12px rgba(0,0,0,0.3);'>
                                        <div style='font-size: 1.2rem; font-weight: 800; color: #fff; margin-bottom: 1.2rem;'>
                                            Performance by Regime
                                        </div>
                                        <div style='display: flex; flex-direction: column; gap: 0.8rem;'>
                                    """, unsafe_allow_html=True)
                                    
                                    regimes_list = [('TREND', '#26A69A'), ('RANGE', '#FFC107'), ('VOLATILE', '#EF5350')]
                                    
                                    for regime, r_color in regimes_list:
                                        win_rate = regime_perf.get(regime, 0)
                                        rating = "Excellent" if win_rate >= 60 else "Good" if win_rate >= 50 else "Fair" if win_rate >= 40 else "Poor"
                                        bar_width = (win_rate / 100) * 100
                                        
                                        st.markdown(f"""
                                        <div style='margin-bottom: 0.8rem;'>
                                            <div style='display: flex; justify-content: space-between; margin-bottom: 0.4rem;'>
                                                <div style='font-size: 0.85rem; font-weight: 700; color: #fff;'>{regime}</div>
                                                <div style='font-size: 0.85rem; font-weight: 800; color: {r_color};'>{win_rate:.1f}%</div>
                                            </div>
                                            <div style='background: rgba(100,100,100,0.2); border-radius: 4px; height: 24px; overflow: hidden;'>
                                                <div style='background: linear-gradient(90deg, {r_color}, {r_color}dd); 
                                                            width: {bar_width}%; height: 100%; border-radius: 4px;
                                                            display: flex; align-items: center; justify-content: flex-end;
                                                            padding-right: 0.5rem; font-size: 0.7rem; color: #fff; font-weight: 700;'>
                                                    {rating}
                                                </div>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    st.markdown("</div></div>", unsafe_allow_html=True)

                                
                                # Define tab color for styling
                                tab_colors = ["#26A69A", "#4A9EFF", "#FFC107", "#FF9800", "#9C27B0"]
                                tab_color = tab_colors[tab_idx % len(tab_colors)]
                                
                                # Find signals belonging to this combination
                                try:
                                    # Split the combination name to get individual indicators
                                    indicators = [ind.strip() for ind in combo_name.split(' + ')]
                                    
                                    # Get all signals from each component indicator
                                    signals_by_indicator = {}
                                    for ind in indicators:
                                        signals_by_indicator[ind] = [s for s in all_signal_details if ind.upper() in s.get('indicator', '').upper()]
                                    
                                    # Find signals that occurred on the same date/time (combination signals)
                                    combo_signals = []
                                    if all(signals_by_indicator.get(ind) for ind in indicators):
                                        # For each signal from first indicator, check if other indicators have signals on same date
                                        for sig1 in signals_by_indicator[indicators[0]]:
                                            date1 = sig1.get('date')
                                            # Check if ALL other indicators have signals on same date
                                            if all(any(s.get('date') == date1 for s in signals_by_indicator[ind]) for ind in indicators[1:]):
                                                # Mark this as a combination signal
                                                combo_signals.append({
                                                    **sig1,
                                                    'combo_indicator': combo_name
                                                })
                                    
                                    if combo_signals:
                                        # Sort by date descending
                                        combo_signals = sorted(combo_signals, key=lambda x: x['date'], reverse=True)
                                        
                                        # Quick Stats Summary Cards
                                        wins = sum(1 for s in combo_signals if s.get('success'))
                                        losses = len(combo_signals) - wins
                                        avg_hold = np.mean([s.get('days_held', 0) for s in combo_signals]) if combo_signals else 0
                                        avg_return = np.mean([s.get('gain', 0) for s in combo_signals]) if combo_signals else 0
                                        
                                        # Create display dataframe with combination details
                                        display_df = []
                                        for sig in combo_signals:
                                            date_val = sig.get('date')
                                            
                                            # Find companion signals from other indicators on same date
                                            companion_indicators = []
                                            for ind in indicators:
                                                if ind.upper() not in sig.get('indicator', '').upper():
                                                    # Find signals from this indicator on same date
                                                    matches = [s for s in all_signal_details 
                                                              if s.get('date') == date_val and 
                                                              ind.upper() in s.get('indicator', '').upper()]
                                                    if matches:
                                                        companion_indicators.append(ind)
                                            
                                            display_df.append({
                                                'Date': date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val),
                                                'Entry': f"{sig.get('entry_price', 0):.2f}",
                                                'Exit': f"{sig.get('exit_price', 0):.2f}",
                                                'Return %': sig.get('gain', 0),
                                                'Days': int(sig.get('days_held', 0)),
                                                'Result': 'WIN' if sig.get('success') else 'LOSS',
                                                'Regime': sig.get('regime', 'UNKNOWN'),
                                                'Co-Signals': ', '.join(companion_indicators) if companion_indicators else 'None'
                                            })
                                        
                                        signals_df = pd.DataFrame(display_df)
                                        
                                        # Display with enhanced styling in card
                                        st.markdown(f"""
                                        <div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                                                    border: 1px solid {tab_color}20; border-radius: 10px; padding: 1.5rem; 
                                                    margin-top: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);'>
                                        """, unsafe_allow_html=True)
                                        
                                        st.dataframe(
                                            signals_df,
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                'Date': st.column_config.TextColumn(
                                                    width="medium",
                                                    help="Signal trigger date"
                                                ),
                                                'Entry': st.column_config.TextColumn(
                                                    width="small",
                                                    help="Entry price (SAR)"
                                                ),
                                                'Exit': st.column_config.TextColumn(
                                                    width="small",
                                                    help="Exit price (SAR)"
                                                ),
                                                'Return %': st.column_config.NumberColumn(
                                                    width="small",
                                                    format="%.2f%%",
                                                    help="Trade return percentage"
                                                ),
                                                'Days': st.column_config.NumberColumn(
                                                    width="small",
                                                    help="Days held"
                                                ),
                                                'Result': st.column_config.TextColumn(
                                                    width="small",
                                                    help="WIN = Profitable | LOSS = Unprofitable"
                                                ),
                                                'Regime': st.column_config.TextColumn(
                                                    width="small",
                                                    help="Market regime during signal"
                                                ),
                                                'Co-Signals': st.column_config.TextColumn(
                                                    width="medium",
                                                    help="Other indicators signaling at same time"
                                                )
                                            }
                                        )
                                        
                                        st.markdown("</div>", unsafe_allow_html=True)
                                        
                                    else:
                                        st.markdown(f"""
                                        <div style='background: #FFC10715; border: 1px solid #FFC10740; border-radius: 8px; 
                                                    padding: 1.5rem; text-align: center;'>
                                            <div style='font-size: 1.1rem; color: #FFC107;'>No combination signals found</div>
                                            <div style='font-size: 0.85rem; color: #999; margin-top: 0.5rem;'>
                                                {combo_name} did not generate any signals in the selected period
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                except Exception as e:
                                    st.markdown(f"""
                                    <div style='background: #EF535015; border: 1px solid #EF535040; border-radius: 8px; 
                                                padding: 1.5rem; text-align: center;'>
                                        <div style='font-size: 1.1rem; color: #EF5350;'>Error loading signal history</div>
                                        <div style='font-size: 0.85rem; color: #999; margin-top: 0.5rem;'>{str(e)}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                
                else:
                    st.info("Not enough data for combination analysis")
                
                st.markdown("</div>", unsafe_allow_html=True)
            
            with analysis_tab3:
                st.markdown('<div class="section-container" style="padding: 2rem;">', unsafe_allow_html=True)
                
                if all_signal_details:
                    history_df = pd.DataFrame(all_signal_details)
                    history_df['date'] = pd.to_datetime(history_df['date'])
                    
                    # ==================== REGIME PERFORMANCE BREAKDOWN ====================
                    st.markdown("## Signals by Market Regime")
                    
                    regime_stats = []
                    for regime in history_df['regime'].unique():
                        regime_data = history_df[history_df['regime'] == regime]
                        regime_total = len(regime_data)
                        regime_wins = len(regime_data[regime_data['success']])
                        regime_wr = (regime_wins / regime_total * 100) if regime_total > 0 else 0
                        regime_avg_gain = regime_data['gain'].mean()
                        
                        regime_stats.append({
                            'regime': regime,
                            'total': regime_total,
                            'wins': regime_wins,
                            'losses': regime_total - regime_wins,
                            'win_rate': regime_wr,
                            'avg_gain': regime_avg_gain
                        })
                    
                    regime_df = pd.DataFrame(regime_stats).sort_values('win_rate', ascending=False)
                    
                    regime_cols = st.columns(len(regime_df))
                    for idx, (col, (_, row)) in enumerate(zip(regime_cols, regime_df.iterrows())):
                        with col:
                            regime_color = "🟢" if row['win_rate'] >= 55 else "🟡" if row['win_rate'] >= 45 else "🔴"
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.05); padding: 1.25rem; border-radius: 0.75rem; border-left: 3px solid {'#10b981' if row['win_rate'] >= 55 else '#f59e0b' if row['win_rate'] >= 45 else '#ef4444'}">
                                <h4 style="margin: 0 0 0.75rem 0; font-size: 1rem;">{regime_color} {row['regime']}</h4>
                                <div style="display: grid; gap: 0.5rem; font-size: 0.875rem;">
                                    <div><strong>Signals:</strong> {int(row['total'])}</div>
                                    <div><strong>Win Rate:</strong> <span style="color: {'#10b981' if row['win_rate'] >= 55 else '#f59e0b' if row['win_rate'] >= 45 else '#ef4444'};">{row['win_rate']:.1f}%</span></div>
                                    <div><strong>W/L:</strong> {int(row['wins'])}W / {int(row['losses'])}L</div>
                                    <div><strong>Avg Return:</strong> {row['avg_gain']:.2f}%</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:1.5rem 0;'>", unsafe_allow_html=True)
                    
                    # ==================== TOP & BOTTOM PERFORMERS ====================
                    st.markdown("## Best & Worst Signals")
                    
                    top_col1, top_col2 = st.columns(2)
                    
                    with top_col1:
                        st.markdown("### 🏆 Best 5 Signals")
                        top_5 = history_df.nlargest(5, 'gain')[['date', 'indicator', 'regime', 'gain', 'days_held']]
                        top_5['date'] = top_5['date'].dt.strftime('%Y-%m-%d')
                        
                        for idx, (_, row) in enumerate(top_5.iterrows(), 1):
                            st.markdown(f"""
                            <div style="background: rgba(16, 185, 129, 0.1); padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid #10b981;">
                                <strong>#{idx}</strong> {row['indicator']} in {row['regime']}<br>
                                <span style="color: #10b981;">+{row['gain']:.2f}%</span> • {row['date']} • Held {int(row['days_held'])} days
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with top_col2:
                        st.markdown("### 📉 Worst 5 Signals")
                        worst_5 = history_df.nsmallest(5, 'gain')[['date', 'indicator', 'regime', 'gain', 'days_held']]
                        worst_5['date'] = worst_5['date'].dt.strftime('%Y-%m-%d')
                        
                        for idx, (_, row) in enumerate(worst_5.iterrows(), 1):
                            st.markdown(f"""
                            <div style="background: rgba(239, 68, 68, 0.1); padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem; border-left: 3px solid #ef4444;">
                                <strong>#{idx}</strong> {row['indicator']} in {row['regime']}<br>
                                <span style="color: #ef4444;">{row['gain']:.2f}%</span> • {row['date']} • Held {int(row['days_held'])} days
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("<hr style='border:none; border-top:1px solid rgba(255,255,255,0.1); margin:1.5rem 0;'>", unsafe_allow_html=True)
                    
                    # ==================== DETAILED SIGNAL TABLE ====================
                    st.markdown("## Signal Details Table")
                    
                    # Filters
                    table_col1, table_col2, table_col3 = st.columns(3)
                    with table_col1:
                        filter_indicator = st.multiselect(
                            "Filter by Indicator",
                            options=sorted(history_df['indicator'].unique().tolist()),
                            default=sorted(history_df['indicator'].unique().tolist()),
                            key="table_indicator_filter"
                        )
                    with table_col2:
                        filter_success = st.selectbox(
                            "Filter by Result",
                            options=['All', 'Winners Only', 'Losers Only'],
                            key="table_success_filter"
                        )
                    with table_col3:
                        filter_regime = st.multiselect(
                            "Filter by Regime",
                            options=sorted(history_df['regime'].unique().tolist()),
                            default=sorted(history_df['regime'].unique().tolist()),
                            key="table_regime_filter"
                        )
                    
                    # Apply filters
                    filtered_df = history_df.copy()
                    filtered_df = filtered_df[filtered_df['indicator'].isin(filter_indicator)]
                    filtered_df = filtered_df[filtered_df['regime'].isin(filter_regime)]
                    if filter_success == 'Winners Only':
                        filtered_df = filtered_df[filtered_df['success']]
                    elif filter_success == 'Losers Only':
                        filtered_df = filtered_df[~filtered_df['success']]
                    
                    # Sort by return
                    filtered_df = filtered_df.sort_values('gain', ascending=False)
                    
                    # Prepare display dataframe
                    display_df = filtered_df[['date', 'indicator', 'entry_price', 'exit_price', 'gain', 'days_held', 'success', 'regime']].copy()
                    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:.2f}")
                    display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:.2f}")
                    display_df['gain'] = display_df['gain'].apply(lambda x: f"{x:+.2f}%")
                    display_df['days_held'] = display_df['days_held'].astype(int)
                    display_df['success'] = display_df['success'].apply(lambda x: "✓ Win" if x else "✗ Loss")
                    
                    display_df = display_df.rename(columns={
                        'date': 'Date',
                        'indicator': 'Indicator',
                        'entry_price': 'Entry',
                        'exit_price': 'Exit',
                        'gain': 'Return',
                        'days_held': 'Hold (Days)',
                        'success': 'Result',
                        'regime': 'Regime'
                    })
                    
                    st.markdown(f"**Showing {len(filtered_df)} of {len(history_df)} signals**")
                    st.dataframe(display_df, use_container_width=True, height=600)
                    
                    # Download button
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Signal History (CSV)",
                        data=csv,
                        file_name=f"signal_history_{symbol_input}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="hist_download_button"
                    )
                else:
                    st.info("No signal data available. Run an analysis first.")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        with tab3:
            # ============================================================
            # ENHANCED PATTERNS TAB - PATTERN INTELLIGENCE
            # ============================================================
            
            # Advanced Pattern Detection Functions
            def detect_support_resistance(df, window=20):
                """Detect support and resistance levels."""
                levels = []
                prices = df['Close'].values
                
                for i in range(window, len(df) - window):
                    # Resistance (local maxima)
                    if prices[i] == max(prices[i-window:i+window]):
                        levels.append({'price': prices[i], 'type': 'resistance', 'date': df.iloc[i]['Date']})
                    
                    # Support (local minima)
                    if prices[i] == min(prices[i-window:i+window]):
                        levels.append({'price': prices[i], 'type': 'support', 'date': df.iloc[i]['Date']})
                
                # Cluster nearby levels
                clustered = []
                tolerance = df['Close'].mean() * 0.015  # 1.5% tolerance
                
                for level in levels:
                    found = False
                    for cluster in clustered:
                        if abs(cluster['price'] - level['price']) < tolerance and cluster['type'] == level['type']:
                            cluster['count'] += 1
                            cluster['price'] = (cluster['price'] + level['price']) / 2
                            found = True
                            break
                    if not found:
                        clustered.append({**level, 'count': 1})
                
                # Filter to significant levels (touched at least 2 times)
                return [l for l in clustered if l['count'] >= 2]
            
            def detect_candlestick_patterns_advanced(df):
                """Advanced candlestick pattern detection."""
                patterns = []
                
                for i in range(5, len(df) - 3):
                    o, h, l, c = df.iloc[i]['Open'], df.iloc[i]['High'], df.iloc[i]['Low'], df.iloc[i]['Close']
                    o1, h1, l1, c1 = df.iloc[i+1]['Open'], df.iloc[i+1]['High'], df.iloc[i+1]['Low'], df.iloc[i+1]['Close']
                    o2, h2, l2, c2 = df.iloc[i+2]['Open'], df.iloc[i+2]['High'], df.iloc[i+2]['Low'], df.iloc[i+2]['Close']
                    
                    prev_trend_down = df.iloc[i-5:i]['Close'].is_monotonic_decreasing
                    prev_trend_up = df.iloc[i-5:i]['Close'].is_monotonic_increasing
                    
                    body = abs(c - o)
                    body1 = abs(c1 - o1)
                    body2 = abs(c2 - o2)
                    
                    # Bullish Engulfing (improved with trend context)
                    if c < o and c1 > o1 and c1 > o and o1 < c and body1 > body * 1.5 and prev_trend_down:
                        patterns.append({
                            'date': df.iloc[i+1]['Date'],
                            'pattern': 'Bullish Engulfing',
                            'category': 'Candlestick',
                            'type': 'Bullish',
                            'confidence': 'Very High',
                            'strength': 85,
                            'price': c1,
                            'signal': 'BUY',
                            'description': 'Strong bullish reversal after downtrend - previous downtrend reversing'
                        })
                    
                    # Bearish Engulfing
                    if c > o and c1 < o1 and c1 < o and o1 > c and body1 > body * 1.5 and prev_trend_up:
                        patterns.append({
                            'date': df.iloc[i+1]['Date'],
                            'pattern': 'Bearish Engulfing',
                            'category': 'Candlestick',
                            'type': 'Bearish',
                            'confidence': 'Very High',
                            'strength': 85,
                            'price': c1,
                            'signal': 'SELL',
                            'description': 'Strong bearish reversal after uptrend - previous uptrend reversing'
                        })
                    
                    # Morning Star
                    if c < o and abs(c1 - o1) < body * 0.3 and c2 > o2 and c2 > (o + c) / 2:
                        patterns.append({
                            'date': df.iloc[i+2]['Date'],
                            'pattern': 'Morning Star',
                            'category': 'Candlestick',
                            'type': 'Bullish',
                            'confidence': 'Very High',
                            'strength': 90,
                            'price': c2,
                            'signal': 'STRONG BUY',
                            'description': 'Very strong 3-candle bullish reversal - bottom formation complete'
                        })
                    
                    # Evening Star
                    if c > o and abs(c1 - o1) < body * 0.3 and c2 < o2 and c2 < (o + c) / 2:
                        patterns.append({
                            'date': df.iloc[i+2]['Date'],
                            'pattern': 'Evening Star',
                            'category': 'Candlestick',
                            'type': 'Bearish',
                            'confidence': 'Very High',
                            'strength': 90,
                            'price': c2,
                            'signal': 'STRONG SELL',
                            'description': 'Very strong 3-candle bearish reversal - top formation complete'
                        })
                    
                    # Three White Soldiers
                    o_2, c_2 = df.iloc[i-2]['Open'], df.iloc[i-2]['Close']
                    o_1, c_1 = df.iloc[i-1]['Open'], df.iloc[i-1]['Close']
                    if c_2 > o_2 and c_1 > o_1 and c > o and c > c_1 > c_2:
                        patterns.append({
                            'date': df.iloc[i]['Date'],
                            'pattern': 'Three White Soldiers',
                            'category': 'Candlestick',
                            'type': 'Bullish',
                            'confidence': 'High',
                            'strength': 80,
                            'price': c,
                            'signal': 'BUY',
                            'description': 'Strong bullish continuation - three consecutive green candles'
                        })
                    
                    # Three Black Crows
                    if c_2 < o_2 and c_1 < o_1 and c < o and c < c_1 < c_2:
                        patterns.append({
                            'date': df.iloc[i]['Date'],
                            'pattern': 'Three Black Crows',
                            'category': 'Candlestick',
                            'type': 'Bearish',
                            'confidence': 'High',
                            'strength': 80,
                            'price': c,
                            'signal': 'SELL',
                            'description': 'Strong bearish continuation - three consecutive red candles'
                        })
                    
                    # Hammer
                    lower_shadow = min(o, c) - l
                    body_size = max(abs(c - o), 0.001)
                    upper_shadow = h - max(o, c)
                    if lower_shadow > body_size * 2.5 and upper_shadow < body_size * 0.5:
                        patterns.append({
                            'date': df.iloc[i]['Date'],
                            'pattern': 'Hammer',
                            'category': 'Candlestick',
                            'type': 'Bullish',
                            'confidence': 'Medium',
                            'strength': 65,
                            'price': c,
                            'signal': 'BUY',
                            'description': 'Bullish reversal - buyers rejected lower prices'
                        })
                    
                    # Inverted Hammer
                    if upper_shadow > body_size * 2.5 and lower_shadow < body_size * 0.5 and c > o:
                        patterns.append({
                            'date': df.iloc[i]['Date'],
                            'pattern': 'Inverted Hammer',
                            'category': 'Candlestick',
                            'type': 'Bullish',
                            'confidence': 'Medium',
                            'strength': 60,
                            'price': c,
                            'signal': 'BUY',
                            'description': 'Potential bullish reversal - needs confirmation'
                        })
                    
                    # Shooting Star
                    if upper_shadow > body_size * 2.5 and lower_shadow < body_size * 0.5:
                        patterns.append({
                            'date': df.iloc[i]['Date'],
                            'pattern': 'Shooting Star',
                            'category': 'Candlestick',
                            'type': 'Bearish',
                            'confidence': 'Medium',
                            'strength': 65,
                            'price': c,
                            'signal': 'SELL',
                            'description': 'Bearish reversal - sellers rejected higher prices'
                        })
                
                return patterns
            
            def detect_chart_patterns_advanced(df):
                """Advanced chart pattern detection."""
                patterns = []
                prices = df['Close'].values
                highs = df['High'].values
                lows = df['Low'].values
                dates = df['Date'].values
                volumes = df['Volume'].values if 'Volume' in df.columns else None
                
                for i in range(60, len(df) - 10):
                    current = prices[i]
                    
                    # Head and Shoulders (bearish)
                    if i > 80:
                        left_shoulder_idx = i - 60
                        head_idx = i - 30
                        right_shoulder_idx = i - 10
                        
                        left_shoulder = highs[left_shoulder_idx]
                        head = highs[head_idx]
                        right_shoulder = highs[right_shoulder_idx]
                        
                        # Check if head is highest and shoulders are similar
                        if (head > left_shoulder * 1.05 and head > right_shoulder * 1.05 and 
                            abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                            patterns.append({
                                'date': dates[i],
                                'pattern': 'Head & Shoulders',
                                'category': 'Chart',
                                'type': 'Bearish',
                                'confidence': 'Very High',
                                'strength': 95,
                                'price': current,
                                'signal': 'STRONG SELL',
                                'description': 'Major bearish reversal pattern - expect significant decline'
                            })
                    
                    # Inverse Head and Shoulders (bullish)
                    if i > 80:
                        left_shoulder_idx = i - 60
                        head_idx = i - 30
                        right_shoulder_idx = i - 10
                        
                        left_shoulder = lows[left_shoulder_idx]
                        head = lows[head_idx]
                        right_shoulder = lows[right_shoulder_idx]
                        
                        if (head < left_shoulder * 0.95 and head < right_shoulder * 0.95 and 
                            abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                            patterns.append({
                                'date': dates[i],
                                'pattern': 'Inverse H&S',
                                'category': 'Chart',
                                'type': 'Bullish',
                                'confidence': 'Very High',
                                'strength': 95,
                                'price': current,
                                'signal': 'STRONG BUY',
                                'description': 'Major bullish reversal pattern - expect significant rally'
                            })
                    
                    # Double Bottom (bullish)
                    if i > 50:
                        prev_low_idx = i - 40
                        prev_low = min(lows[prev_low_idx-5:prev_low_idx+5])
                        curr_low = min(lows[i-10:i])
                        
                        if (abs(prev_low - curr_low) / prev_low < 0.03 and 
                            current > curr_low * 1.02):
                            patterns.append({
                                'date': dates[i],
                                'pattern': 'Double Bottom',
                                'category': 'Chart',
                                'type': 'Bullish',
                                'confidence': 'High',
                                'strength': 85,
                                'price': current,
                                'signal': 'BUY',
                                'description': 'Support tested twice and held - bullish breakout likely'
                            })
                    
                    # Double Top (bearish)
                    if i > 50:
                        prev_high_idx = i - 40
                        prev_high = max(highs[prev_high_idx-5:prev_high_idx+5])
                        curr_high = max(highs[i-10:i])
                        
                        if (abs(prev_high - curr_high) / prev_high < 0.03 and 
                            current < curr_high * 0.98):
                            patterns.append({
                                'date': dates[i],
                                'pattern': 'Double Top',
                                'category': 'Chart',
                                'type': 'Bearish',
                                'confidence': 'High',
                                'strength': 85,
                                'price': current,
                                'signal': 'SELL',
                                'description': 'Resistance tested twice and rejected - bearish breakdown likely'
                            })
                    
                    # Cup and Handle (bullish)
                    if i > 70:
                        cup_prices = prices[i-70:i-10]
                        if len(cup_prices) > 30:
                            cup_low = min(cup_prices)
                            cup_high_left = max(prices[i-70:i-60])
                            cup_high_right = max(prices[i-20:i-10])
                            
                            if (abs(cup_high_left - cup_high_right) / cup_high_left < 0.05 and
                                cup_low < cup_high_left * 0.88 and current > cup_high_right * 0.98):
                                patterns.append({
                                    'date': dates[i],
                                    'pattern': 'Cup & Handle',
                                    'category': 'Chart',
                                    'type': 'Bullish',
                                    'confidence': 'High',
                                    'strength': 88,
                                    'price': current,
                                    'signal': 'BUY',
                                    'description': 'Classic continuation pattern - strong bullish signal'
                                })
                    
                    # Ascending Triangle (bullish)
                    recent_highs = [highs[j] for j in range(i-30, i, 5) if j >= 0]
                    recent_lows = [lows[j] for j in range(i-30, i, 5) if j >= 0]
                    
                    if len(recent_highs) >= 4 and len(recent_lows) >= 4:
                        highs_flat = (max(recent_highs) - min(recent_highs)) < max(recent_highs) * 0.02
                        lows_rising = len([recent_lows[j] < recent_lows[j+1] for j in range(len(recent_lows)-1) if recent_lows[j] < recent_lows[j+1]]) >= 2
                        
                        if highs_flat and lows_rising:
                            patterns.append({
                                'date': dates[i],
                                'pattern': 'Ascending Triangle',
                                'category': 'Chart',
                                'type': 'Bullish',
                                'confidence': 'Medium',
                                'strength': 75,
                                'price': current,
                                'signal': 'BUY',
                                'description': 'Bullish continuation - breakout above resistance expected'
                            })
                    
                    # Descending Triangle (bearish)
                    if len(recent_highs) >= 4 and len(recent_lows) >= 4:
                        lows_flat = (max(recent_lows) - min(recent_lows)) < max(recent_lows) * 0.02
                        highs_falling = len([recent_highs[j] > recent_highs[j+1] for j in range(len(recent_highs)-1) if recent_highs[j] > recent_highs[j+1]]) >= 2
                        
                        if lows_flat and highs_falling:
                            patterns.append({
                                'date': dates[i],
                                'pattern': 'Descending Triangle',
                                'category': 'Chart',
                                'type': 'Bearish',
                                'confidence': 'Medium',
                                'strength': 75,
                                'price': current,
                                'signal': 'SELL',
                                'description': 'Bearish continuation - breakdown below support expected'
                            })
                    
                    # Bull Flag (bullish continuation)
                    if i > 25:
                        pole_start = i - 25
                        pole_end = i - 10
                        flag_section = prices[pole_end:i]
                        
                        pole_gain = (prices[pole_end] - prices[pole_start]) / prices[pole_start]
                        if pole_gain > 0.05:  # Strong upward pole
                            flag_slope = (flag_section[-1] - flag_section[0]) / max(flag_section[0], 0.001)
                            if -0.03 < flag_slope < 0.01:  # Slight downward or flat consolidation
                                patterns.append({
                                    'date': dates[i],
                                    'pattern': 'Bull Flag',
                                    'category': 'Chart',
                                    'type': 'Bullish',
                                    'confidence': 'High',
                                    'strength': 80,
                                    'price': current,
                                    'signal': 'BUY',
                                    'description': 'Bullish continuation - expect upside breakout soon'
                                })
                    
                    # Bear Flag (bearish continuation)
                    if i > 25:
                        pole_start = i - 25
                        pole_end = i - 10
                        flag_section = prices[pole_end:i]
                        
                        pole_loss = (prices[pole_start] - prices[pole_end]) / prices[pole_start]
                        if pole_loss > 0.05:  # Strong downward pole
                            flag_slope = (flag_section[-1] - flag_section[0]) / max(flag_section[0], 0.001)
                            if -0.01 < flag_slope < 0.03:  # Slight upward or flat consolidation
                                patterns.append({
                                    'date': dates[i],
                                    'pattern': 'Bear Flag',
                                    'category': 'Chart',
                                    'type': 'Bearish',
                                    'confidence': 'High',
                                    'strength': 80,
                                    'price': current,
                                    'signal': 'SELL',
                                    'description': 'Bearish continuation - expect downside breakdown soon'
                                })
                
                return patterns
            
            # Detect all patterns
            candlestick_patterns = detect_candlestick_patterns_advanced(df)
            chart_patterns = detect_chart_patterns_advanced(df)
            support_resistance = detect_support_resistance(df)
            all_patterns = candlestick_patterns + chart_patterns
            
            # Sort patterns by date (most recent first)
            all_patterns = sorted(all_patterns, key=lambda x: pd.to_datetime(x['date']), reverse=True)
            
            # ============================================================
            # SECTION 1: CURRENT PATTERN (Happening NOW)
            # ============================================================
            st.markdown("### CURRENT PATTERN", unsafe_allow_html=True)
            
            # Get patterns from last 3 days
            latest_date = df['Date'].max()
            cutoff_date = latest_date - pd.Timedelta(days=3)
            current_patterns = [p for p in all_patterns if pd.to_datetime(p['date']) >= cutoff_date]
            
            if current_patterns:
                # Show the strongest current pattern
                strongest_current = max(current_patterns, key=lambda x: x['strength'])
                
                # Create alert box
                alert_color = "#26A69A" if strongest_current['type'] == 'Bullish' else "#EF5350"
                st.markdown(f"""
                <div style='background:rgba({int(alert_color[1:3], 16)}, {int(alert_color[3:5], 16)}, {int(alert_color[5:7], 16)}, 0.15); 
                            border-left:5px solid {alert_color}; border-radius:8px; padding:1.5rem; margin-bottom:1.5rem;'>
                    <div style='display:grid; grid-template-columns: 1fr 1fr 1fr; gap:1rem;'>
                        <div>
                            <div style='font-size:0.8rem; color:#999; margin-bottom:0.3rem;'>PATTERN</div>
                            <div style='font-size:1.5rem; font-weight:700; color:{alert_color};'>{strongest_current['pattern']}</div>
                            <div style='font-size:0.75rem; color:#bbb; margin-top:0.3rem;'>{strongest_current['category']}</div>
                        </div>
                        <div>
                            <div style='font-size:0.8rem; color:#999; margin-bottom:0.3rem;'>SIGNAL</div>  
                            <div style='font-size:1.3rem; font-weight:700; color:{alert_color};'>{strongest_current['signal']}</div>
                            <div style='font-size:0.75rem; color:#bbb; margin-top:0.3rem;'>Strength: {strongest_current['strength']}%</div>
                        </div>
                        <div>
                            <div style='font-size:0.8rem; color:#999; margin-bottom:0.3rem;'>DETECTED</div>
                            <div style='font-size:1.1rem; font-weight:600; color:#fff;'>{strongest_current['date']}</div>
                            <div style='font-size:0.75rem; color:#bbb; margin-top:0.3rem;'>Price: {strongest_current['price']:.2f} SAR</div>
                        </div>
                    </div>
                    <div style='margin-top:1rem; padding-top:1rem; border-top:1px solid rgba(255,255,255,0.1);'>
                        <div style='font-size:0.85rem; color:#ddd;'><b>What This Means:</b> {strongest_current['description']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show all current patterns if multiple
                if len(current_patterns) > 1:
                    st.markdown(f"<div style='font-size:0.9rem; color:#bbb; margin-bottom:0.8rem;'>{len(current_patterns)} patterns detected in last 3 days</div>", unsafe_allow_html=True)
                    cols = st.columns(min(len(current_patterns), 3))
                    for idx, pattern in enumerate(current_patterns[:3]):
                        with cols[idx]:
                            color = "#26A69A" if pattern['type'] == 'Bullish' else "#EF5350"
                            st.markdown(f"""
                            <div style='background:#0e0e1a; border-top:3px solid {color}; border-radius:6px; padding:1rem;'>
                                <div style='font-size:0.85rem; font-weight:600; color:{color};'>{pattern['pattern']}</div>
                                <div style='font-size:0.7rem; color:#999; margin-top:0.3rem;'>{pattern['signal']}</div>
                                <div style='font-size:0.7rem; color:#bbb; margin-top:0.3rem;'>Strength: {pattern['strength']}%</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.warning("No pattern currently forming. Market in consolidation or between patterns.")
            
            st.markdown("<div style='margin:2rem 0;'></div>", unsafe_allow_html=True)
            
            # ============================================================
            # SECTION 2: PATTERN FORECAST (What's Next)
            # ============================================================
            st.markdown("### PATTERN FORECAST", unsafe_allow_html=True)
            
            # Analyze pattern sequences to predict what's next
            if len(all_patterns) >= 5:
                # Get last 5 patterns to analyze trend
                last_5 = all_patterns[:5]
                
                bullish_momentum = len([p for p in last_5 if p['type'] == 'Bullish'])
                bearish_momentum = len([p for p in last_5 if p['type'] == 'Bearish'])
                
                # Calculate price momentum
                recent_price_data = df.tail(10)
                price_change = (recent_price_data['Close'].iloc[-1] - recent_price_data['Close'].iloc[0]) / recent_price_data['Close'].iloc[0] * 100
                
                # Determine forecast
                if bullish_momentum >= 4:
                    forecast_direction = "CONTINUED UPTREND"
                    forecast_confidence = "High"
                    forecast_desc = "Multiple consecutive bullish patterns suggest strong upward momentum"
                    forecast_color = "#26A69A"
                    next_action = "Look for pullbacks to add long positions. Set trailing stops to protect profits"
                elif bearish_momentum >= 4:
                    forecast_direction = "CONTINUED DOWNTREND"
                    forecast_confidence = "High"
                    forecast_desc = "Multiple consecutive bearish patterns suggest strong downward pressure"
                    forecast_color = "#EF5350"
                    next_action = "Avoid buying. Wait for reversal signals or consider short positions"
                elif bullish_momentum > bearish_momentum and price_change > 2:
                    forecast_direction = "BULLISH BREAKOUT LIKELY"
                    forecast_confidence = "Medium"
                    forecast_desc = "Bullish patterns dominating with positive price action"
                    forecast_color = "#26A69A"
                    next_action = "Watch for breakout above resistance. Enter on confirmation with volume"
                elif bearish_momentum > bullish_momentum and price_change < -2:
                    forecast_direction = "BEARISH BREAKDOWN LIKELY"
                    forecast_confidence = "Medium"
                    forecast_desc = "Bearish patterns dominating with negative price action"
                    forecast_color = "#EF5350"
                    next_action = "Watch for breakdown below support. Exit longs and wait for stability"
                elif abs(price_change) < 1:
                    forecast_direction = "CONSOLIDATION EXPECTED"
                    forecast_confidence = "Medium"
                    forecast_desc = "Mixed pattern signals and sideways price action suggest range-bound trading"
                    forecast_color = "#FFC107"
                    next_action = "Wait for clear breakout direction. Trade the range until pattern emerges"
                else:
                    forecast_direction = "REVERSAL POSSIBLE"
                    forecast_confidence = "Low"
                    forecast_desc = "Conflicting pattern signals suggest potential trend reversal or uncertainty"
                    forecast_color = "#FF6B6B"
                    next_action = "Reduce position sizes. Wait for clearer signals before taking new positions"
                
                # Clean forecast layout matching hero section - Using Streamlit columns for reliability
                st.markdown(f"""
                <div style='background:#0e0e1a;border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1.4rem 1.6rem;margin-bottom:0.5rem;'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;'>
                        <div style='flex:1;'>
                            <div style='font-size:0.7rem;color:#9aa3b2;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem;'>FORECAST DIRECTION</div>
                            <div style='font-size:1.6rem;font-weight:800;color:{forecast_color};margin-bottom:0.5rem;'>{forecast_direction}</div>
                            <div style='font-size:0.95rem;color:#cfd6e6;line-height:1.5;'>{forecast_desc}</div>
                        </div>
                        <div style='text-align:right;padding-left:2rem;'>
                            <div style='font-size:0.7rem;color:#9aa3b2;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem;'>CONFIDENCE</div>
                            <div style='font-size:1.6rem;font-weight:800;color:#fff;'>{forecast_confidence}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Metrics in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div style='background:#10101b;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1rem;'>
                        <div style='font-size:0.65rem;color:#9aa3b2;text-transform:uppercase;letter-spacing:0.7px;'>Bullish Patterns</div>
                        <div style='font-size:1.4rem;font-weight:700;color:#26A69A;margin-top:0.25rem;'>{bullish_momentum}/5</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style='background:#10101b;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1rem;'>
                        <div style='font-size:0.65rem;color:#9aa3b2;text-transform:uppercase;letter-spacing:0.7px;'>Bearish Patterns</div>
                        <div style='font-size:1.4rem;font-weight:700;color:#EF5350;margin-top:0.25rem;'>{bearish_momentum}/5</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style='background:#10101b;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1rem;'>
                        <div style='font-size:0.65rem;color:#9aa3b2;text-transform:uppercase;letter-spacing:0.7px;'>Price Change (10D)</div>
                        <div style='font-size:1.4rem;font-weight:700;color:{forecast_color};margin-top:0.25rem;'>{price_change:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Recommended action
                st.markdown(f"""
                <div style='background:#0b0b14;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:1rem;margin-top:0.5rem;margin-bottom:1.2rem;'>
                    <div style='font-size:0.7rem;color:#9aa3b2;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.4rem;'>RECOMMENDED ACTION</div>
                    <div style='font-size:1rem;font-weight:600;color:#fff;line-height:1.5;'>{next_action}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Not enough pattern data to generate forecast. Need at least 5 historical patterns.")
            
            st.markdown("<div style='margin:2rem 0;'></div>", unsafe_allow_html=True)
            
            # ============================================================
            # SECTION 4: HISTORICAL PATTERN PERFORMANCE
            # ============================================================
            st.markdown("### PATTERN PERFORMANCE - Which Patterns Work Best", unsafe_allow_html=True)
            
            if len(all_patterns) >= 3:
                # Analyze pattern frequency and types
                pattern_frequency = {}
                pattern_types = {}
                
                for p in all_patterns:
                    name = p['pattern']
                    ptype = p['type']
                    
                    if name not in pattern_frequency:
                        pattern_frequency[name] = 0
                        pattern_types[name] = ptype
                    pattern_frequency[name] += 1
                
                # Sort by frequency
                sorted_patterns = sorted(pattern_frequency.items(), key=lambda x: x[1], reverse=True)[:8]
                
                # Create performance visualization
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Bar chart of pattern frequency
                    fig = go.Figure()
                    
                    pattern_names = [p[0] for p in sorted_patterns]
                    pattern_counts = [p[1] for p in sorted_patterns]
                    pattern_colors = ['#26A69A' if pattern_types[p[0]] == 'Bullish' else '#EF5350' for p in sorted_patterns]
                    
                    fig.add_trace(go.Bar(
                        x=pattern_counts,
                        y=pattern_names,
                        orientation='h',
                        marker=dict(color=pattern_colors),
                        text=pattern_counts,
                        textposition='auto',
                        hovertemplate='<b>%{y}</b><br>Occurrences: %{x}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=dict(text='Most Frequent Patterns in This Stock', font=dict(size=14, color='#fff')),
                        height=350,
                        plot_bgcolor='#262730',
                        paper_bgcolor='#262730',
                        font=dict(color='#ffffff', size=11),
                        showlegend=False,
                        margin=dict(t=40, b=40, l=150, r=20),
                        xaxis=dict(title='Occurrences', gridcolor='rgba(255,255,255,0.1)'),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("<div style='font-size:0.95rem; color:#fff; font-weight:600; margin-bottom:1rem;'>Pattern Insights</div>", unsafe_allow_html=True)
                    
                    # Most common pattern
                    most_common = sorted_patterns[0]
                    most_common_type = pattern_types[most_common[0]]
                    
                    st.markdown(f"""
                    <div style='background:#0e0e1a; border-radius:8px; padding:1rem; margin-bottom:1rem;'>
                        <div style='font-size:0.7rem; color:#999;'>MOST FREQUENT</div>
                        <div style='font-size:1.1rem; font-weight:600; color:{'#26A69A' if most_common_type == 'Bullish' else '#EF5350'}; margin-top:0.3rem;'>
                            {most_common[0]}
                        </div>
                        <div style='font-size:0.75rem; color:#bbb; margin-top:0.3rem;'>
                            Appeared {most_common[1]} times
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Total patterns
                    total_unique = len(pattern_frequency)
                    total_occurrences = sum(pattern_frequency.values())
                    
                    st.markdown(f"""
                    <div style='background:#0e0e1a; border-radius:8px; padding:1rem;'>
                        <div style='font-size:0.7rem; color:#999;'>TOTAL PATTERNS</div>
                        <div style='font-size:1.1rem; font-weight:600; color:#fff; margin-top:0.3rem;'>
                            {total_unique} unique patterns
                        </div>
                        <div style='font-size:0.75rem; color:#bbb; margin-top:0.3rem;'>
                            {total_occurrences} total occurrences
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📊 Not enough historical patterns to analyze performance.")



def create_consensus_agreement_chart(consensus_signals):
    """Create agreement level distribution chart."""
    agreement_counts = {2: 0, 3: 0, 4: 0, 5: 0}
    for signal in consensus_signals:
        count = signal['count']
        if count in agreement_counts:
            agreement_counts[count] += 1
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(agreement_counts.keys()),
        y=list(agreement_counts.values()),
        marker=dict(color=['#FFC107', '#26A69A', '#4CAF50', '#0D7377']),
        text=list(agreement_counts.values()),
        textposition='auto',
        hovertemplate='%{x} indicators: %{y} signals<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text='Consensus Agreement Distribution', font=dict(size=14, color='#fff')),
        xaxis_title='Number of Agreeing Indicators',
        yaxis_title='Number of Signals',
        height=300,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#ffffff', size=11),
        showlegend=False,
        margin=dict(t=40, b=40, l=60, r=20)
    )
    return fig


def create_consensus_timeline_chart(consensus_signals):
    """Create timeline of consensus signals."""
    if not consensus_signals:
        return None
    
    dates = [pd.to_datetime(s['date']) for s in consensus_signals]
    agreements = [s['count'] for s in consensus_signals]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=agreements,
        mode='markers+lines',
        marker=dict(
            size=10,
            color=agreements,
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title='Agreement'),
            line=dict(width=1, color='white')
        ),
        line=dict(color='rgba(100,200,150,0.3)', width=1),
        hovertemplate='Date: %{x|%Y-%m-%d}<br>Agreement: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text='Consensus Signals Over Time', font=dict(size=14, color='#fff')),
        xaxis_title='Date',
        yaxis_title='Number of Agreeing Indicators',
        height=320,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#ffffff', size=11),
        xaxis=dict(gridcolor='#2A2A2A'),
        yaxis=dict(gridcolor='#2A2A2A', range=[0, 6]),
        margin=dict(t=40, b=40, l=60, r=20)
    )
    return fig


def create_consensus_regime_chart(consensus_signals):
    """Create regime breakdown for consensus signals."""
    regime_counts = {}
    for s in consensus_signals:
        regime = s.get('regime', 'UNKNOWN')
        regime_counts[regime] = regime_counts.get(regime, 0) + 1
    
    regimes = list(regime_counts.keys())
    counts = list(regime_counts.values())
    colors = {'TREND': '#26A69A', 'RANGE': '#FFC107', 'VOLATILE': '#EF5350'}
    colors_list = [colors.get(r, '#888888') for r in regimes]
    
    fig = go.Figure(data=[
        go.Pie(
            labels=regimes,
            values=counts,
            marker=dict(colors=colors_list),
            textinfo='label+percent',
            hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(text='Consensus Signals by Market Regime', font=dict(size=14, color='#fff')),
        height=300,
        plot_bgcolor='#262730',
        paper_bgcolor='#262730',
        font=dict(color='#ffffff', size=11),
        margin=dict(t=40, b=20, l=20, r=20)
    )
    return fig


def placeholder_consensus():
    """Placeholder function."""
    pass


if __name__ == "__main__":
    main()
