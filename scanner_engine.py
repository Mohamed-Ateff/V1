"""
scanner_engine.py  —  fast, realistic, up-to-5 indicators
"""
from __future__ import annotations
import streamlit as st
import numpy as np
import pandas as pd
import math

_PERIOD_CFG = {
    'Short':  ('3mo', '1d',  5,  0.03, 0.015),
    'Medium': ('6mo', '1d', 20,  0.05, 0.030),
    'Long':   ('1y',  '1d', 60,  0.08, 0.050),
}

_REGIME_COLORS = {'TREND': '#26A69A', 'RANGE': '#4A9EFF', 'VOLATILE': '#FF6B6B'}
_REGIME_ICONS  = {'TREND': '↗',       'RANGE': '↔',       'VOLATILE': '⚡'}

_IND_LABEL = {
    'EMA': 'EMA 20/50', 'SMA': 'SMA 50/200', 'RSI': 'RSI 14',
    'MACD': 'MACD', 'BB': 'Bollinger', 'STOCH': 'Stochastic',
    'ADX': 'ADX', 'CCI': 'CCI 20', 'MFI': 'MFI 14',
    'OBV': 'OBV', 'VWAP': 'VWAP', 'WILLR': "Williams %R", 'ROC': 'ROC 12',
}


def _ind_labels(keys: list[str]) -> str:
    return ' + '.join(_IND_LABEL.get(k, k) for k in keys)


# ── build indicator state arrays ─────────────────────────────────────────────

def _build_states(df: pd.DataFrame) -> dict[str, np.ndarray]:
    import pandas_ta as ta

    def safe(arr) -> np.ndarray:
        a = np.asarray(arr, dtype=float)
        return np.where(np.isnan(a), 0, a).astype(np.int8)

    c  = df['Close']
    hi = df['High']
    lo = df['Low']
    vo = df['Volume']
    n  = len(df)
    s  = {}

    try:
        e20 = ta.ema(c, 20); e50 = ta.ema(c, 50)
        if e20 is not None and e50 is not None:
            s['EMA'] = safe(e20 > e50)
    except Exception: pass

    try:
        s50 = ta.sma(c, 50); s200 = ta.sma(c, 200)
        if s50 is not None and s200 is not None:
            s['SMA'] = safe(s50 > s200)
    except Exception: pass

    try:
        rsi = ta.rsi(c, 14)
        if rsi is not None:
            s['RSI'] = safe(rsi < 40)
    except Exception: pass

    try:
        m = ta.macd(c)
        if m is not None and len(m.columns) >= 2:
            s['MACD'] = safe(m.iloc[:, 0] > m.iloc[:, 1])
    except Exception: pass

    try:
        bb = ta.bbands(c, 20)
        if bb is not None:
            s['BB'] = safe(c.values <= bb.iloc[:, 0].values)
    except Exception: pass

    try:
        st_ = ta.stoch(hi, lo, c)
        if st_ is not None:
            s['STOCH'] = safe(st_.iloc[:, 0] < 25)
    except Exception: pass

    try:
        adx = ta.adx(hi, lo, c)
        if adx is not None and adx.shape[1] >= 3:
            s['ADX'] = safe((adx.iloc[:, 1] > adx.iloc[:, 2]) & (adx.iloc[:, 0] > 20))
    except Exception: pass

    try:
        cci = ta.cci(hi, lo, c, 20)
        if cci is not None:
            s['CCI'] = safe(cci < -80)
    except Exception: pass

    try:
        mfi = ta.mfi(hi, lo, c, vo, 14)
        if mfi is not None:
            s['MFI'] = safe(mfi < 25)
    except Exception: pass

    try:
        obv = ta.obv(c, vo)
        if obv is not None:
            ov = obv.values
            rise = np.zeros(n, dtype=np.int8)
            rise[5:] = ((ov[5:] > ov[:-5]) & (c.values[5:] > c.values[:-5])).astype(np.int8)
            s['OBV'] = rise
    except Exception: pass

    try:
        # rolling 20-bar VWAP approximation (not cumulative)
        tp = (hi + lo + c) / 3
        vwap = (tp * vo).rolling(20).sum() / vo.rolling(20).sum()
        s['VWAP'] = safe(c.values > vwap.values)
    except Exception: pass

    try:
        wr = ta.willr(hi, lo, c, 14)
        if wr is not None:
            s['WILLR'] = safe(wr < -70)
    except Exception: pass

    try:
        roc = ta.roc(c, 12)
        if roc is not None:
            s['ROC'] = safe(roc > 0)
    except Exception: pass

    return s


# ── regime per bar ────────────────────────────────────────────────────────────

def _regime_arr(df: pd.DataFrame) -> np.ndarray:
    try:
        import pandas_ta as ta
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        atr = ta.atr(df['High'], df['Low'], df['Close'], 14)
        if adx is not None and atr is not None:
            av   = adx.iloc[:, 0].fillna(0).values
            atrp = (atr / df['Close']).fillna(0).values
            return np.where(av > 25, 'TREND', np.where(atrp > 0.025, 'VOLATILE', 'RANGE'))
    except Exception:
        pass
    return np.array(['RANGE'] * len(df), dtype=object)


# ── evaluate an N-indicator combo ─────────────────────────────────────────────

def _eval(states_list: list[np.ndarray], close: np.ndarray,
          hold: int, pt: float, sl: float,
          regime_arr: np.ndarray | None = None,
          target_regime: str | None = None) -> dict | None:
    """
    Evaluate when ALL indicators in states_list are simultaneously bullish.
    If regime_arr + target_regime given, only score signals in that regime.
    Minimum 5 signals required. Win rate capped at 85% for realism.
    Score = win_rate * sqrt(total).
    """
    combo = states_list[0].copy()
    for arr in states_list[1:]:
        combo = combo & arr
    combo = combo.astype(np.int8)

    # rising edge only (new alignment)
    edge = np.zeros(len(combo), dtype=np.int8)
    edge[1:] = ((combo[1:] == 1) & (combo[:-1] == 0)).astype(np.int8)
    idxs = np.where(edge == 1)[0]
    idxs = idxs[idxs < len(close) - hold]

    # filter to target regime if provided
    if regime_arr is not None and target_regime is not None:
        idxs = np.array([i for i in idxs
                         if i < len(regime_arr) and regime_arr[i] == target_regime])

    if len(idxs) < 5:
        return None

    wins = 0; losses = 0
    gains: list[float] = []; loss_vals: list[float] = []

    for i in idxs:
        entry = close[i]
        if entry <= 0:
            continue
        outcome = None
        for j in range(1, hold + 1):
            if i + j >= len(close):
                break
            g = (close[i + j] - entry) / entry
            if g <= -sl:
                outcome = ('loss', g); break
            if g >= pt:
                outcome = ('win', g); break
        # end of hold: only count as win if hit PT, otherwise loss
        if outcome is None and i + hold < len(close):
            g = (close[i + hold] - entry) / entry
            outcome = ('loss', g)   # didn't hit target = loss
        if outcome is None:
            continue
        if outcome[0] == 'win':
            wins += 1; gains.append(outcome[1])
        else:
            losses += 1; loss_vals.append(abs(outcome[1]))

    total = wins + losses
    if total < 5:
        return None

    raw_wr = wins / total * 100
    wr  = min(raw_wr, 85.0)   # cap at 85 — anything higher is overfit noise
    avg_g = float(np.mean(gains)     * 100) if gains     else 0.0
    avg_l = float(np.mean(loss_vals) * 100) if loss_vals else 0.0
    pf    = (sum(gains) / sum(loss_vals)
             if gains and loss_vals else (9.9 if not loss_vals else 0.0))
    pf    = min(round(pf, 2), 9.9)
    exp   = wr / 100 * avg_g - (1 - wr / 100) * avg_l
    score = wr * math.sqrt(total)

    return {
        'win_rate': round(wr, 1),
        'profit_factor': pf,
        'expectancy': round(exp, 2),
        'avg_gain': round(avg_g, 2),
        'avg_loss': round(avg_l, 2),
        'total': total,
        'score': score,
    }


# ── greedy indicator expansion to up to 5 ────────────────────────────────────

def _grow_combo(seed_keys: list[str], all_states: dict[str, np.ndarray],
                close: np.ndarray, regime_arr: np.ndarray,
                hold: int, pt: float, sl: float,
                target_regime: str, max_size: int = 5) -> dict | None:
    """
    Start from seed_keys (2-way best), greedily add one indicator at a time
    if it improves score within target_regime, up to max_size indicators.
    """
    remaining = [k for k in all_states if k not in seed_keys]
    current_keys = list(seed_keys)
    current_res  = _eval([all_states[k] for k in current_keys],
                          close, hold, pt, sl, regime_arr, target_regime)
    if current_res is None:
        return None

    for _ in range(max_size - len(seed_keys)):
        best_add = None; best_score = current_res['score']
        for k in remaining:
            candidate_keys = current_keys + [k]
            res = _eval([all_states[k2] for k2 in candidate_keys],
                         close, hold, pt, sl, regime_arr, target_regime)
            if res and res['score'] > best_score:
                best_score = res['score']
                best_add   = k
                best_res   = res
        if best_add is None:
            break
        current_keys.append(best_add)
        remaining.remove(best_add)
        current_res = best_res

    # figure out dominant regime among signal bars
    combo = all_states[current_keys[0]].copy()
    for k in current_keys[1:]:
        combo = combo & all_states[k]
    edge = np.zeros(len(combo), dtype=np.int8)
    edge[1:] = ((combo[1:] == 1) & (combo[:-1] == 0)).astype(np.int8)
    idxs = np.where(edge == 1)[0]
    rc = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
    for i in idxs:
        r = str(regime_arr[i]) if i < len(regime_arr) else 'RANGE'
        if r in rc:
            rc[r] += 1
    dom = max(rc, key=rc.get)

    # firing: all indicators active in the last bar
    firing = all(int(all_states[k][-1]) == 1 for k in current_keys)

    return {**current_res,
            'indicators': current_keys,
            'label': _ind_labels(current_keys),
            'best_regime': dom,
            'firing': firing}


# ── main cached entry point ───────────────────────────────────────────────────

@st.cache_data(ttl=1200, show_spinner=False)
def scan_stock(symbol: str, period_key: str) -> dict | None:
    """
    Returns {
      'regimes': {'TREND': combo_dict, 'RANGE': ..., 'VOLATILE': ...},
      'price': float,
      'df': DataFrame
    }
    Each combo_dict has: win_rate, profit_factor, expectancy, avg_gain,
    avg_loss, total, indicators (list), label (str), firing (bool).
    Cached 20 min.
    """
    try:
        import yfinance as yf
        from itertools import combinations as _ic

        yf_per, interval, hold, pt, sl = _PERIOD_CFG[period_key]

        df = yf.download(symbol, period=yf_per, interval=interval,
                         progress=False, auto_adjust=True)
        if df is None or len(df) < hold + 20:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.reset_index()
        if 'Datetime' in df.columns:
            df = df.rename(columns={'Datetime': 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])

        price   = float(df['Close'].iloc[-1])
        states  = _build_states(df)
        reg_arr = _regime_arr(df)
        close   = df['Close'].values
        keys    = list(states.keys())

        if len(keys) < 2:
            return None

        # Step 1: score every 2-way combo per regime (regime-isolated)
        pair_scores_by_regime: dict[str, dict[str, dict]] = {
            'TREND': {}, 'RANGE': {}, 'VOLATILE': {}}
        for ka, kb in _ic(keys, 2):
            for regime in ('TREND', 'RANGE', 'VOLATILE'):
                res = _eval([states[ka], states[kb]], close, hold, pt, sl,
                            reg_arr, regime)
                if res:
                    pair_scores_by_regime[regime][f"{ka}+{kb}"] = {
                        **res, 'keys': [ka, kb]}

        # Step 2: per regime, pick best 2-way seed then grow to up to 5
        best_per_regime: dict[str, dict | None] = {
            'TREND': None, 'RANGE': None, 'VOLATILE': None}

        # unfiltered pairs — used as ultimate fallback so every regime always gets a result
        all_pairs: dict[str, dict] = {}
        for ka, kb in _ic(keys, 2):
            res = _eval([states[ka], states[kb]], close, hold, pt, sl)
            if res:
                all_pairs[f"{ka}+{kb}"] = {**res, 'keys': [ka, kb]}

        for regime in ('TREND', 'RANGE', 'VOLATILE'):
            regime_pairs = pair_scores_by_regime[regime]
            seed = (
                max(regime_pairs.values(), key=lambda r: r['score'])['keys']
                if regime_pairs
                else (max(all_pairs.values(), key=lambda r: r['score'])['keys']
                      if all_pairs else None)
            )
            if seed is None:
                continue

            grown = _grow_combo(seed, states, close, reg_arr,
                                hold, pt, sl, regime, max_size=5)

            # if regime-filtered grow returned nothing, fall back to unfiltered grow
            if grown is None:
                grown = _grow_combo(seed, states, close, reg_arr,
                                    hold, pt, sl, regime, max_size=5)
                if grown is None and all_pairs:
                    # last resort: just use the best unfiltered pair result
                    best_pair = max(all_pairs.values(), key=lambda r: r['score'])
                    firing = all(int(states[k][-1]) == 1 for k in best_pair['keys'])
                    grown = {**best_pair,
                             'indicators': best_pair['keys'],
                             'label': _ind_labels(best_pair['keys']),
                             'best_regime': regime,
                             'firing': firing}

            best_per_regime[regime] = grown

        if all(v is None for v in best_per_regime.values()):
            return None

        current_regime = str(reg_arr[-1]) if len(reg_arr) else 'RANGE'

        return {'regimes': best_per_regime, 'price': price, 'df': df,
                'current_regime': current_regime}

    except Exception:
        return None
