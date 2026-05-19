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
    """Build binary indicator state arrays. Uses native pandas where ta.sma is slow."""
    import pandas_ta as ta

    def safe(arr) -> np.ndarray:
        a = np.asarray(arr, dtype=float)
        return np.where(np.isnan(a), 0, a).astype(np.int8)

    c  = df['Close'].astype(float)
    hi = df['High'].astype(float)
    lo = df['Low'].astype(float)
    vo = df['Volume'].astype(float)
    cv = c.values
    n  = len(df)
    s  = {}

    try:
        e20 = ta.ema(c, 20); e50 = ta.ema(c, 50)
        if e20 is not None and e50 is not None:
            s['EMA'] = safe(e20 > e50)
    except Exception: pass

    try:
        # use pandas rolling — ta.sma has 100ms JIT penalty on first call per series
        s50  = c.rolling(50).mean()
        s200 = c.rolling(200).mean()
        s['SMA'] = safe(s50 > s200)
    except Exception: pass

    try:
        rsi = ta.rsi(c, 14)
        if rsi is not None:
            s['RSI'] = safe((rsi > 50) & (rsi < 75))
    except Exception: pass

    try:
        m = ta.macd(c)
        if m is not None and len(m.columns) >= 2:
            s['MACD'] = safe(m.iloc[:, 0] > m.iloc[:, 1])
    except Exception: pass

    try:
        bb = ta.bbands(c, 20)
        if bb is not None and bb.shape[1] >= 3:
            s['BB'] = safe(cv >= bb.iloc[:, 1].values)
    except Exception: pass

    try:
        st_ = ta.stoch(hi, lo, c)
        if st_ is not None:
            s['STOCH'] = safe((st_.iloc[:, 0] > 40) & (st_.iloc[:, 0] < 80))
    except Exception: pass

    try:
        adx = ta.adx(hi, lo, c)
        if adx is not None and adx.shape[1] >= 3:
            s['ADX'] = safe((adx.iloc[:, 1] > adx.iloc[:, 2]) & (adx.iloc[:, 0] > 20))
    except Exception: pass

    try:
        cci = ta.cci(hi, lo, c, 20)
        if cci is not None:
            s['CCI'] = safe((cci > 0) & (cci < 150))
    except Exception: pass

    try:
        mfi = ta.mfi(hi, lo, c, vo, 14)
        if mfi is not None:
            s['MFI'] = safe((mfi > 50) & (mfi < 80))
    except Exception: pass

    try:
        obv = ta.obv(c, vo)
        if obv is not None:
            ov = obv.values
            rise = np.zeros(n, dtype=np.int8)
            rise[5:] = ((ov[5:] > ov[:-5]) & (cv[5:] > cv[:-5])).astype(np.int8)
            s['OBV'] = rise
    except Exception: pass

    try:
        tp   = (hi + lo + c) / 3
        vwap = (tp * vo).rolling(20).sum() / vo.rolling(20).sum()
        s['VWAP'] = safe(cv > vwap.values)
    except Exception: pass

    try:
        wr = ta.willr(hi, lo, c, 14)
        if wr is not None:
            s['WILLR'] = safe((wr > -50) & (wr < -20))
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
        # end of hold without hitting PT or SL: use actual return
        if outcome is None and i + hold < len(close):
            g = (close[i + hold] - entry) / entry
            outcome = ('win', g) if g > 0 else ('loss', g)
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
    _sum_gains = sum(gains) if gains else 0.0
    _sum_losses = sum(loss_vals) if loss_vals else 0.0
    if _sum_losses > 0 and _sum_gains > 0:
        pf = _sum_gains / _sum_losses
    elif _sum_losses == 0 and _sum_gains > 0:
        pf = 9.9
    else:
        pf = 0.0
    pf = min(round(pf, 2), 9.9)
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
def scan_stock(symbol: str, period_key: str, _v: int = 2) -> dict | None:
    """
    Single-stock entry — extracts from a pre-built batch cache when available,
    otherwise downloads individually. Cached 20 min.
    """
    return _process_stock_df(symbol, period_key)


@st.cache_data(ttl=1200, show_spinner=False)
def scan_all_stocks(symbols: tuple, period_key: str, _v: int = 2) -> dict:
    """
    Batch-download all symbols in one yfinance call, then process each.
    Returns {symbol: result_dict_or_None}.  Cached 20 min.
    """
    import yfinance as yf

    yf_per, interval, hold, pt, sl = _PERIOD_CFG[period_key]
    sym_list = list(symbols)

    try:
        raw = yf.download(
            sym_list, period=yf_per, interval=interval,
            progress=False, auto_adjust=True, group_by='ticker',
            threads=True,
        )
    except Exception:
        raw = None

    out: dict = {}
    for sym in sym_list:
        try:
            if raw is None:
                out[sym] = None
                continue
            # extract per-symbol slice from multi-ticker download
            if isinstance(raw.columns, pd.MultiIndex):
                if sym not in raw.columns.get_level_values(0):
                    out[sym] = None
                    continue
                df = raw[sym].copy()
            else:
                # single ticker fallback (unlikely here but safe)
                df = raw.copy()
            df = df.dropna(how='all').reset_index()
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            df['Date'] = pd.to_datetime(df['Date'])
            if len(df) < hold + 20:
                out[sym] = None
                continue
            out[sym] = _analyse_df(df, hold, pt, sl)
        except Exception:
            out[sym] = None
    return out


def _process_stock_df(symbol: str, period_key: str) -> dict | None:
    """Download + analyse a single symbol (fallback path)."""
    try:
        import yfinance as yf
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
        return _analyse_df(df, hold, pt, sl)
    except Exception:
        return None


@st.cache_data(ttl=1200, show_spinner=False)
def get_stock_df(symbol: str, period_key: str, _v: int = 2) -> 'pd.DataFrame | None':
    """Fetch OHLCV df for a single symbol — used for price ladder / charts."""
    try:
        import yfinance as yf
        yf_per, interval, hold, pt, sl = _PERIOD_CFG[period_key]
        df = yf.download(symbol, period=yf_per, interval=interval,
                         progress=False, auto_adjust=True)
        if df is None or len(df) < 5:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.reset_index()
        if 'Datetime' in df.columns:
            df = df.rename(columns={'Datetime': 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception:
        return None


def _analyse_df(df: pd.DataFrame, hold: int, pt: float, sl: float) -> dict | None:
    """
    Fast analysis: score each indicator once (no regime split during scan),
    greedily build best combo, then tag it to all three regime slots.
    Per-regime detail is computed lazily when the user drills into a card.
    """
    try:
        price   = float(df['Close'].iloc[-1])
        states  = _build_states(df)
        reg_arr = _regime_arr(df)
        close   = df['Close'].values
        keys    = list(states.keys())

        if len(keys) < 2:
            return None

        # --- 1. Score each indicator individually (regime-agnostic) ---
        ind_scores: list[tuple[float, str]] = []
        for k in keys:
            r = _eval([states[k]], close, hold, pt, sl)
            if r:
                ind_scores.append((r['score'], k))

        if len(ind_scores) < 2:
            return None

        ind_scores.sort(reverse=True)

        # --- 2. Greedy combo build from top seed ---
        current_keys = [ind_scores[0][1], ind_scores[1][1]]
        current_res  = _eval([states[k] for k in current_keys], close, hold, pt, sl)
        if current_res is None:
            return None

        for _, k in ind_scores[2:]:
            if len(current_keys) >= 5:
                break
            candidate = current_keys + [k]
            res = _eval([states[ck] for ck in candidate], close, hold, pt, sl)
            if res and res['score'] > current_res['score']:
                current_keys = candidate
                current_res  = res

        # --- 3. Dominant regime among signal bars ---
        combo = states[current_keys[0]].copy()
        for k in current_keys[1:]:
            combo = combo & states[k]
        edge = np.zeros(len(combo), dtype=np.int8)
        edge[1:] = ((combo[1:] == 1) & (combo[:-1] == 0)).astype(np.int8)
        idxs = np.where(edge == 1)[0]
        rc = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
        for i in idxs:
            r2 = str(reg_arr[i]) if i < len(reg_arr) else 'RANGE'
            if r2 in rc:
                rc[r2] += 1
        dom = max(rc, key=rc.get)
        firing = all(int(states[k][-1]) == 1 for k in current_keys)

        result = {
            **current_res,
            'indicators': current_keys,
            'label': _ind_labels(current_keys),
            'best_regime': dom,
            'firing': firing,
        }

        # --- 4. Populate all three regime slots with same result ---
        current_regime = str(reg_arr[-1]) if len(reg_arr) else 'RANGE'
        best_per_regime = {
            'TREND':    result,
            'RANGE':    result,
            'VOLATILE': result,
        }

        return {'regimes': best_per_regime, 'price': price,
                'current_regime': current_regime}

    except Exception:
        return None
