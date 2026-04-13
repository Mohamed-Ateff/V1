import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

@st.cache_data(show_spinner=False, ttl=3600)

def get_stock_name(symbol: str) -> str:

    """Return the long name for a symbol via yfinance (cached)."""

    try:

        info = yf.Ticker(symbol).info

        return info.get('longName') or info.get('shortName') or ''

    except Exception:

        return ''





@st.cache_data(show_spinner=False, ttl=300)

def detect_signals(_df):

    """Detect buy/sell signals from all indicators."""

    # Coerce all non-date/non-string columns to numeric to avoid None comparison errors

    # from pandas_ta returning mixed types

    df = _df.copy()

    skip_cols = {'Date', 'REGIME'}

    for col in df.columns:

        if col not in skip_cols and df[col].dtype == object:

            df[col] = pd.to_numeric(df[col], errors='coerce')



    signals_df = pd.DataFrame(index=df.index)

    signals_df['Date'] = df['Date']

    signals_df['Close'] = df['Close']

    signals_df['Regime'] = df.get('REGIME', 'UNKNOWN')



    # ?? 1?? Trend (Direction) ?????????????????????????????????????????????



    # EMA (20/50) Crossover

    if 'EMA_20' in df.columns and 'EMA_50' in df.columns:

        ema_cross_up   = (df['EMA_20'] > df['EMA_50']) & (df['EMA_20'].shift(1) <= df['EMA_50'].shift(1))

        ema_cross_down = (df['EMA_20'] < df['EMA_50']) & (df['EMA_20'].shift(1) >= df['EMA_50'].shift(1))

        signals_df['EMA_Buy']  = ema_cross_up.astype(int)

        signals_df['EMA_Sell'] = ema_cross_down.astype(int)



    # SMA (50/200) Golden / Death Cross

    if 'SMA_50' in df.columns and 'SMA_200' in df.columns:

        sma_cross_up   = (df['SMA_50'] > df['SMA_200']) & (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1))

        sma_cross_down = (df['SMA_50'] < df['SMA_200']) & (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1))

        signals_df['SMA_Buy']  = sma_cross_up.astype(int)

        signals_df['SMA_Sell'] = sma_cross_down.astype(int)



    # Parabolic SAR  (PSARl = long dots appear ? buy flip)

    psar_long_col  = next((c for c in df.columns if c.startswith('PSARl')), None)

    psar_short_col = next((c for c in df.columns if c.startswith('PSARs')), None)

    if psar_long_col and psar_short_col:

        psar_buy  = (~df[psar_long_col].isna()  & df[psar_long_col].shift(1).isna()).astype(int)

        psar_sell = (~df[psar_short_col].isna() & df[psar_short_col].shift(1).isna()).astype(int)

        signals_df['PSAR_Buy']  = psar_buy

        signals_df['PSAR_Sell'] = psar_sell



    # Ichimoku - price crosses above/below cloud (Span A & B)

    isa_col = next((c for c in df.columns if c.startswith('ISA_')), None)

    isb_col = next((c for c in df.columns if c.startswith('ISB_')), None)

    if isa_col and isb_col:

        cloud_top    = df[[isa_col, isb_col]].max(axis=1)

        cloud_bottom = df[[isa_col, isb_col]].min(axis=1)

        ichi_buy  = ((df['Close'] > cloud_top)  & (df['Close'].shift(1) <= cloud_top.shift(1))).astype(int)

        ichi_sell = ((df['Close'] < cloud_bottom) & (df['Close'].shift(1) >= cloud_bottom.shift(1))).astype(int)

        signals_df['ICHI_Buy']  = ichi_buy

        signals_df['ICHI_Sell'] = ichi_sell



    # WMA - price crosses WMA_20

    if 'WMA_20' in df.columns:

        wma_buy  = ((df['Close'] > df['WMA_20']) & (df['Close'].shift(1) <= df['WMA_20'].shift(1))).astype(int)

        wma_sell = ((df['Close'] < df['WMA_20']) & (df['Close'].shift(1) >= df['WMA_20'].shift(1))).astype(int)

        signals_df['WMA_Buy']  = wma_buy

        signals_df['WMA_Sell'] = wma_sell



    # ?? 2?? Momentum (Entry Timing) ??????????????????????????????????????



    # RSI (14)

    if 'RSI_14' in df.columns:

        signals_df['RSI_Buy']  = (df['RSI_14'] < 30).astype(int)

        signals_df['RSI_Sell'] = (df['RSI_14'] > 70).astype(int)



    # MACD crossover

    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:

        macd_cross_up   = (df['MACD_12_26_9'] > df['MACDs_12_26_9']) & (df['MACD_12_26_9'].shift(1) <= df['MACDs_12_26_9'].shift(1))

        macd_cross_down = (df['MACD_12_26_9'] < df['MACDs_12_26_9']) & (df['MACD_12_26_9'].shift(1) >= df['MACDs_12_26_9'].shift(1))

        signals_df['MACD_Buy']  = macd_cross_up.astype(int)

        signals_df['MACD_Sell'] = macd_cross_down.astype(int)



    # Stochastic

    if 'STOCHk_14_3_3' in df.columns:

        signals_df['STOCH_Buy']  = (df['STOCHk_14_3_3'] < 20).astype(int)

        signals_df['STOCH_Sell'] = (df['STOCHk_14_3_3'] > 80).astype(int)



    # ROC (12) - zero-line crossover

    if 'ROC_12' in df.columns:

        roc_buy  = ((df['ROC_12'] > 0) & (df['ROC_12'].shift(1) <= 0)).astype(int)

        roc_sell = ((df['ROC_12'] < 0) & (df['ROC_12'].shift(1) >= 0)).astype(int)

        signals_df['ROC_Buy']  = roc_buy

        signals_df['ROC_Sell'] = roc_sell



    # CCI (20) - oversold/overbought

    if 'CCI_20' in df.columns:

        signals_df['CCI_Buy']  = (df['CCI_20'] < -100).astype(int)

        signals_df['CCI_Sell'] = (df['CCI_20'] >  100).astype(int)



    # Williams %R (14)

    if 'WILLR_14' in df.columns:

        signals_df['WILLR_Buy']  = (df['WILLR_14'] < -80).astype(int)

        signals_df['WILLR_Sell'] = (df['WILLR_14'] > -20).astype(int)



    # ?? 3?? Volatility (Breakouts & Risk) ????????????????????????????????



    # Bollinger Bands

    if 'BBL_20_2.0' in df.columns and 'BBU_20_2.0' in df.columns:

        signals_df['BB_Buy']  = (df['Close'] <= df['BBL_20_2.0']).astype(int)

        signals_df['BB_Sell'] = (df['Close'] >= df['BBU_20_2.0']).astype(int)



    # Keltner Channel - price touches/crosses lower/upper band

    kc_lower = next((c for c in df.columns if c.startswith('KCLe')), None)

    kc_upper = next((c for c in df.columns if c.startswith('KCUe')), None)

    if kc_lower and kc_upper:

        signals_df['KC_Buy']  = (df['Close'] <= df[kc_lower]).astype(int)

        signals_df['KC_Sell'] = (df['Close'] >= df[kc_upper]).astype(int)



    # Donchian Channel (20) - breakout

    dc_lower = next((c for c in df.columns if c.startswith('DCL')), None)

    dc_upper = next((c for c in df.columns if c.startswith('DCU')), None)

    if dc_lower and dc_upper:

        dc_buy  = ((df['Close'] >= df[dc_upper]) & (df['Close'].shift(1) < df[dc_upper].shift(1))).astype(int)

        dc_sell = ((df['Close'] <= df[dc_lower]) & (df['Close'].shift(1) > df[dc_lower].shift(1))).astype(int)

        signals_df['DC_Buy']  = dc_buy

        signals_df['DC_Sell'] = dc_sell



    # ?? 4?? Volume (Smart Money Confirmation) ?????????????????????????????



    # MFI (14) - oversold/overbought

    if 'MFI_14' in df.columns:

        signals_df['MFI_Buy']  = (df['MFI_14'] < 20).astype(int)

        signals_df['MFI_Sell'] = (df['MFI_14'] > 80).astype(int)



    # CMF (20) - zero-line crossover

    if 'CMF_20' in df.columns:

        cmf_buy  = ((df['CMF_20'] > 0) & (df['CMF_20'].shift(1) <= 0)).astype(int)

        cmf_sell = ((df['CMF_20'] < 0) & (df['CMF_20'].shift(1) >= 0)).astype(int)

        signals_df['CMF_Buy']  = cmf_buy

        signals_df['CMF_Sell'] = cmf_sell



    # VWAP - price crosses VWAP

    if 'VWAP' in df.columns:

        vwap = pd.to_numeric(df['VWAP'], errors='coerce')

        vwap_buy  = ((df['Close'] > vwap) & (df['Close'].shift(1) <= vwap.shift(1))).astype(int)

        vwap_sell = ((df['Close'] < vwap) & (df['Close'].shift(1) >= vwap.shift(1))).astype(int)

        signals_df['VWAP_Buy']  = vwap_buy.fillna(0).astype(int)

        signals_df['VWAP_Sell'] = vwap_sell.fillna(0).astype(int)



    # OBV - rising OBV with rising price (confirmation buy)

    if 'OBV' in df.columns:

        obv_rising   = df['OBV'] > df['OBV'].shift(5)

        price_rising = df['Close'] > df['Close'].shift(5)

        obv_falling  = df['OBV'] < df['OBV'].shift(5)

        price_falling = df['Close'] < df['Close'].shift(5)

        signals_df['OBV_Buy']  = (obv_rising  & price_rising).astype(int)

        signals_df['OBV_Sell'] = (obv_falling & price_falling).astype(int)



    # ?? 5?? Trend Strength - ADX +DI / -DI crossover ?????????????????????

    dmp_col = next((c for c in df.columns if c.startswith('DMP_')), None)

    dmn_col = next((c for c in df.columns if c.startswith('DMN_')), None)

    adx_col = next((c for c in df.columns if c.startswith('ADX_')), None)

    if dmp_col and dmn_col and adx_col:

        adx_active   = df[adx_col] > 20

        adx_buy  = ((df[dmp_col] > df[dmn_col]) & (df[dmp_col].shift(1) <= df[dmn_col].shift(1)) & adx_active).astype(int)

        adx_sell = ((df[dmp_col] < df[dmn_col]) & (df[dmp_col].shift(1) >= df[dmn_col].shift(1)) & adx_active).astype(int)

        signals_df['ADX_Buy']  = adx_buy

        signals_df['ADX_Sell'] = adx_sell



    # ── REGIME-AWARE SIGNAL FILTERING ─────────────────────────────────────

    # Suppress signals from indicators that are unreliable in the current regime.

    # This prevents false signals (e.g. RSI oversold buys in strong downtrends,

    # or EMA crossover buys in choppy range-bound markets).

    #

    # TREND  → trust: EMA, SMA, PSAR, ICHI, WMA, MACD, ADX, DC, OBV, CMF

    #          suppress: RSI, STOCH, BB, KC, CCI, WILLR (mean-reversion traps)

    # RANGE  → trust: RSI, STOCH, BB, KC, CCI, WILLR, MFI, VWAP

    #          suppress: EMA, SMA, PSAR, ICHI, WMA, MACD, ADX, DC (whipsaw)

    # VOLATILE → trust: BB, KC, DC, OBV, MFI, CMF, VWAP (breakout & volume)

    #          suppress: EMA, SMA, PSAR, RSI, STOCH, CCI, WILLR (noisy)

    _suppress_map = {

        "TREND":    {"RSI", "STOCH", "BB", "KC", "CCI", "WILLR"},

        "RANGE":    {"EMA", "SMA", "PSAR", "ICHI", "WMA", "MACD", "ADX", "DC"},

        "VOLATILE": {"EMA", "SMA", "PSAR", "RSI", "STOCH", "CCI", "WILLR"},

    }

    regime_col = signals_df['Regime']

    for regime_val, suppressed_indicators in _suppress_map.items():

        regime_mask = (regime_col == regime_val)

        if not regime_mask.any():

            continue

        for ind in suppressed_indicators:

            buy_col  = f"{ind}_Buy"

            sell_col = f"{ind}_Sell"

            if buy_col in signals_df.columns:

                signals_df.loc[regime_mask, buy_col] = 0

            if sell_col in signals_df.columns:

                signals_df.loc[regime_mask, sell_col] = 0



    return signals_df





@st.cache_data(show_spinner=False, ttl=300)

def evaluate_signal_success(_df, _signals_df, profit_target=0.05, holding_period=20, stop_loss=0.03):

    """Evaluate success of each signal with detailed metrics (dynamic - all indicators)."""



    signals_df = _signals_df



    # Discover all indicators that have a _Buy column

    indicators = [col.replace('_Buy', '') for col in signals_df.columns if col.endswith('_Buy')]



    empty_stats = lambda: {

        'total_signals': 0, 'successful': 0, 'failed': 0,

        'success_rate': 0, 'avg_gain': 0, 'avg_loss': 0,

        'profit_factor': 0, 'avg_hold_time': 0, 'max_gain': 0, 'max_loss': 0,

        'regime_performance': {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}

    }

    results = {ind: empty_stats() for ind in indicators}



    successful_signals = []

    all_signal_details = []



    # Pre-extract numpy arrays - eliminates per-row .iloc overhead

    close_arr  = signals_df['Close'].values

    date_arr   = signals_df['Date'].values

    regime_arr = signals_df['Regime'].values

    n          = len(signals_df)



    for indicator in indicators:

        buy_col = f'{indicator}_Buy'

        if buy_col not in signals_df.columns:

            continue



        wins = []

        losses = []

        hold_times = []



        buy_arr = signals_df[buy_col].values

        for i in np.where(buy_arr == 1)[0]:

            if i >= n - holding_period:

                continue

            results[indicator]['total_signals'] += 1



            entry_price  = close_arr[i]

            entry_date   = date_arr[i]

            entry_regime = regime_arr[i]

            success      = False

            actual_gain  = 0.0

            days_held    = 0

            exit_reason  = 'Timeout'



            for j in range(1, holding_period + 1):

                if i + j >= n:

                    break



                future_price = close_arr[i + j]

                gain = (future_price - entry_price) / entry_price



                if gain <= -stop_loss:

                    results[indicator]['failed'] += 1

                    losses.append(gain)

                    actual_gain = gain

                    days_held   = j

                    exit_reason = 'Stop Loss'

                    break



                if gain >= profit_target:

                    results[indicator]['successful'] += 1

                    wins.append(gain)

                    success     = True

                    actual_gain = gain

                    days_held   = j

                    exit_reason = 'Profit Target'



                    successful_signals.append({

                        'date': entry_date, 'indicator': indicator,

                        'entry_price': entry_price, 'exit_price': future_price,

                        'gain': gain * 100, 'days_held': j, 'regime': entry_regime

                    })



                    if entry_regime in results[indicator]['regime_performance']:

                        results[indicator]['regime_performance'][entry_regime] += 1

                    hold_times.append(j)

                    break



            if not success and days_held == 0 and i + holding_period < n:

                final_price = close_arr[i + holding_period]

                final_gain  = (final_price - entry_price) / entry_price

                actual_gain = final_gain

                days_held   = holding_period

                if final_gain > 0:

                    results[indicator]['successful'] += 1

                    wins.append(final_gain)

                    hold_times.append(holding_period)

                else:

                    results[indicator]['failed'] += 1

                    losses.append(final_gain)



            all_signal_details.append({

                'date': entry_date, 'indicator': indicator,

                'entry_price': entry_price,

                'exit_price': entry_price * (1 + actual_gain),

                'gain': actual_gain * 100,

                'days_held': days_held,

                'success': success or (actual_gain > 0),

                'exit_reason': exit_reason,

                'regime': entry_regime

            })



        if results[indicator]['total_signals'] > 0:

            results[indicator]['success_rate'] = (

                results[indicator]['successful'] / results[indicator]['total_signals']

            ) * 100

            if wins:

                results[indicator]['avg_gain'] = np.mean(wins) * 100

                results[indicator]['max_gain'] = max(wins) * 100

            if losses:

                results[indicator]['avg_loss'] = np.mean(losses) * 100

                results[indicator]['max_loss'] = min(losses) * 100

            if wins and losses:

                results[indicator]['profit_factor'] = sum(wins) / abs(sum(losses))

            if hold_times:

                results[indicator]['avg_hold_time'] = np.mean(hold_times)



    return results, successful_signals, all_signal_details





@st.cache_data(show_spinner=False, ttl=300)

def find_consensus_signals(_signals_df):

    """Find signals where multiple indicators agreed."""

    signals_df = _signals_df

    buy_cols = [col for col in signals_df.columns if col.endswith('_Buy')]

    if not buy_cols:

        return []



    buy_matrix  = signals_df[buy_cols].values          # (n_rows, n_indicators)

    row_counts  = buy_matrix.sum(axis=1)

    close_arr   = signals_df['Close'].values

    date_arr    = signals_df['Date'].values

    regime_arr  = signals_df['Regime'].values

    ind_names   = [c.replace('_Buy', '') for c in buy_cols]



    consensus = []

    for i in np.where(row_counts >= 2)[0]:

        active_indicators = [ind_names[k] for k in np.where(buy_matrix[i] == 1)[0]]

        consensus.append({

            'date':       date_arr[i],

            'price':      close_arr[i],

            'indicators': active_indicators,

            'count':      len(active_indicators),

            'regime':     regime_arr[i],

        })



    return consensus





@st.cache_data(show_spinner=False, ttl=300)

def analyze_indicator_combinations(_signals_df, _df, profit_target=0.05, holding_period=20, stop_loss=0.03, max_combo_size=4):

    """Analyse ALL indicator combinations from 2-way pairs up to max_combo_size-way.

    Each combination fires only when ALL its indicators signal a buy on the same bar.
    Results are sorted by combo size so the caller can group/filter by size.
    """

    from itertools import combinations as _ic

    signals_df = _signals_df

    buy_indicators = [col.replace('_Buy', '') for col in signals_df.columns if col.endswith('_Buy')]



    # Pre-extract numpy arrays once - avoids .iloc overhead in hot loops

    close_arr  = signals_df['Close'].values

    regime_arr = signals_df['Regime'].values

    date_arr   = signals_df.index

    n          = len(signals_df)

    buy_arrays = {ind: signals_df[f'{ind}_Buy'].values for ind in buy_indicators}



    combo_results = {}



    # Exhaustive combinations: 2-way, 3-way, … up to max_combo_size-way

    for combo_size in range(2, min(max_combo_size + 1, len(buy_indicators) + 1)):

        for combo_inds in _ic(buy_indicators, combo_size):

            # Fast numpy AND — all indicators must fire on the same bar

            combined = buy_arrays[combo_inds[0]].copy()

            for _ind in combo_inds[1:]:

                combined = combined & buy_arrays[_ind]



            both  = np.where(combined == 1)[0]

            both  = both[both < n - holding_period]

            total = len(both)

            if total == 0:

                continue



            combo_name = " + ".join(combo_inds)



            successful = 0

            failed = 0

            gains = []

            losses = []

            hold_times = []

            regime_wins   = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}

            regime_totals = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}

            signal_records = []



            for k in both:

                entry_price = close_arr[k]

                regime = regime_arr[k]

                entry_date = str(date_arr[k])[:10]



                if regime in regime_totals:

                    regime_totals[regime] += 1



                hit_target = False

                days_held = 0

                exit_price = entry_price

                result = 'timeout'



                for m in range(1, holding_period + 1):

                    if k + m >= n:

                        break



                    future_price = close_arr[k + m]

                    gain = (future_price - entry_price) / entry_price



                    if gain <= -stop_loss:

                        failed += 1

                        losses.append(gain * 100)

                        days_held = m

                        exit_price = future_price

                        result = 'stop_loss'

                        break



                    if gain >= profit_target:

                        successful += 1

                        gains.append(gain * 100)

                        hit_target = True

                        days_held = m

                        exit_price = future_price

                        result = 'profit'

                        if regime in regime_wins:

                            regime_wins[regime] += 1

                        break



                if not hit_target and days_held == 0:

                    days_held = holding_period

                    final_price = close_arr[k + holding_period]

                    final_gain = (final_price - entry_price) / entry_price

                    exit_price = final_price

                    if final_gain > 0:

                        successful += 1

                        gains.append(final_gain * 100)

                        result = 'timeout_profit'

                        if regime in regime_wins:

                            regime_wins[regime] += 1

                    else:

                        failed += 1

                        losses.append(final_gain * 100)

                        result = 'timeout_loss'



                hold_times.append(days_held)

                signal_records.append({

                    'date':        entry_date,

                    'entry_price': round(float(entry_price), 2),

                    'exit_price':  round(float(exit_price), 2),

                    'gain':        round((exit_price - entry_price) / entry_price * 100, 2),

                    'days_held':   days_held,

                    'regime':      regime,

                    'result':      result,

                })



            avg_gain = float(np.mean(gains)) if gains else 0

            avg_loss = float(np.mean(losses)) if losses else 0

            win_rate = (successful / total) * 100

            expectancy = (win_rate / 100) * avg_gain + (1 - win_rate / 100) * avg_loss

            profit_factor = abs(sum(gains) / sum(losses)) if losses and sum(losses) != 0 else 0

            avg_hold = float(np.mean(hold_times)) if hold_times else 0

            # ── Advanced metrics ───────────────────────────────────────────────
            # Streak analysis
            _cw = 0; _cl = 0; _max_cw = 0; _max_cl = 0
            for _rec in signal_records:
                if _rec['gain'] > 0:
                    _cw += 1; _cl = 0
                else:
                    _cl += 1; _cw = 0
                if _cw > _max_cw: _max_cw = _cw
                if _cl > _max_cl: _max_cl = _cl

            # Signal frequency per 100 bars
            signal_freq = round(total / n * 100, 2)

            # Monthly consistency: std-dev of per-month win rates (lower = more reliable)
            _m_wins = {}; _m_tots = {}
            for _rec in signal_records:
                _mo = _rec['date'][:7]
                _m_tots[_mo] = _m_tots.get(_mo, 0) + 1
                if _rec['gain'] > 0:
                    _m_wins[_mo] = _m_wins.get(_mo, 0) + 1
            _m_rates = {m: (_m_wins.get(m, 0) / _m_tots[m] * 100) for m in _m_tots}
            monthly_win_rates = dict(sorted(_m_rates.items()))
            if len(_m_rates) > 1:
                _mv = list(_m_rates.values())
                _mm = sum(_mv) / len(_mv)
                monthly_consistency = round((sum((_v - _mm)**2 for _v in _mv) / (len(_mv) - 1))**0.5, 1)
            else:
                monthly_consistency = 0.0

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

                'signals': signal_records,

                'combo_size': combo_size,

                'max_consecutive_wins': _max_cw,

                'max_consecutive_losses': _max_cl,

                'signal_frequency': signal_freq,

                'monthly_consistency': monthly_consistency,

                'monthly_win_rates': monthly_win_rates,

                'regime_performance': {

                    regime: (regime_wins[regime] / regime_totals[regime] * 100) if regime_totals[regime] > 0 else 0

                    for regime in regime_totals

                }

            }



    return combo_results





@st.cache_data(show_spinner=False, ttl=300)

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





