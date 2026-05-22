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
    # Trend
    'SMA': 'SMA 50/200', 'EMA': 'EMA 20/50', 'WMA': 'WMA 20',
    'PSAR': 'Par.SAR', 'ICHI': 'Ichimoku', 'MACD': 'MACD',
    'SUPER': 'SuperTrend', 'HULL': 'Hull MA',
    # Momentum
    'RSI': 'RSI 14', 'STOCH': 'Stochastic', 'ROC': 'ROC 12',
    'CCI': 'CCI 20', 'WILLR': 'Wm.%R', 'MOM': 'Momentum',
    'TSI': 'TSI', 'PPO': 'PPO', 'ELDER': 'Elder Ray',
    # Volume
    'OBV': 'OBV', 'MFI': 'MFI 14', 'CMF': 'CMF', 'VWAP': 'VWAP',
    'ADLINE': 'A/D Line', 'VOLMA': 'Vol MA', 'FORCE': 'Force Idx',
    'VOLRSI': 'Vol RSI',
    # Volatility
    'BB': 'Bol.Bands', 'ATR': 'ATR', 'KELT': 'Keltner',
    'DONCH': 'Donchian', 'SQZ': 'Squeeze', 'HV': 'Hist.Vol %',
    'STDEV': 'Std.Dev', 'CHAND': 'Chandelier',
    # Support & Resistance
    'PIVOT': 'Pivot Pts', 'FIB': 'Fib Levels', 'ADX': 'ADX',
    'VWAPB': 'VWAP Bands', 'PREVHL': 'Prev Hi/Lo', 'SWINGHL': 'Swing Hi/Lo',
    # Mean Reversion
    'RSIEXT': 'RSI Ext.', 'BBZ': 'BB Z-Score', 'DISTMA': 'Dist. MA',
    'STOCHEXT': 'Stoch Ext.', 'CCIEXT': 'CCI Ext.',
    # Market Regime
    'TASIF': 'TASI Filter', 'SECTORF': 'Sector Filter',
    'RSTASI': 'RS vs TASI', 'RSSECTOR': 'RS vs Sector',
    'ADVDEC': 'Adv/Decline', 'NEWHL': 'New Hi/Lo',
}


def _ind_labels(keys: list[str]) -> str:
    return ' + '.join(_IND_LABEL.get(k, k) for k in keys)


# ── build indicator state arrays ─────────────────────────────────────────────

def _build_states(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Build binary bullish-state arrays for every supported indicator.
    Each state is 1 when that indicator is currently bullish, 0 otherwise."""
    import pandas_ta as ta

    def safe(arr) -> np.ndarray:
        a = np.asarray(arr, dtype=float)
        return np.where(np.isnan(a), 0, a).astype(np.int8)

    c  = df['Close'].astype(float)
    hi = df['High'].astype(float)
    lo = df['Low'].astype(float)
    vo = df['Volume'].astype(float)
    cv = c.values
    hv = hi.values
    lv = lo.values
    vv = vo.values
    n  = len(df)
    s  = {}

    # ── TREND ───────────────────────────────────────────────────────────
    try:
        s50  = c.rolling(50).mean(); s200 = c.rolling(200).mean()
        s['SMA'] = safe(s50 > s200)
    except Exception: pass
    try:
        e20 = ta.ema(c, 20); e50 = ta.ema(c, 50)
        if e20 is not None and e50 is not None:
            s['EMA'] = safe(e20 > e50)
    except Exception: pass
    try:
        wma20 = ta.wma(c, 20)
        if wma20 is not None:
            s['WMA'] = safe(cv > wma20.values)
    except Exception: pass
    try:
        psar = ta.psar(hi, lo, c)
        if psar is not None:
            # bullish when long stop active (PSARl column non-NaN)
            long_col = [col for col in psar.columns if 'PSARl' in col]
            if long_col:
                s['PSAR'] = safe(~psar[long_col[0]].isna())
    except Exception: pass
    try:
        ich = ta.ichimoku(hi, lo, c)
        if ich is not None and isinstance(ich, tuple) and len(ich) >= 1:
            ich_df = ich[0]
            tk = [col for col in ich_df.columns if 'ITS' in col or 'ISA' in col]
            ks = [col for col in ich_df.columns if 'IKS' in col or 'ISB' in col]
            if tk and ks:
                s['ICHI'] = safe(ich_df[tk[0]] > ich_df[ks[0]])
    except Exception: pass
    try:
        m = ta.macd(c)
        if m is not None and len(m.columns) >= 2:
            s['MACD'] = safe(m.iloc[:, 0] > m.iloc[:, 1])
    except Exception: pass
    try:
        st_ = ta.supertrend(hi, lo, c)
        if st_ is not None:
            dir_col = [col for col in st_.columns if 'SUPERTd' in col]
            if dir_col:
                s['SUPER'] = safe(st_[dir_col[0]] > 0)
    except Exception: pass
    try:
        hull = ta.hma(c, 16)
        if hull is not None:
            s['HULL'] = safe(cv > hull.values)
    except Exception: pass

    # ── MOMENTUM ────────────────────────────────────────────────────────
    try:
        rsi = ta.rsi(c, 14)
        if rsi is not None:
            s['RSI'] = safe((rsi > 50) & (rsi < 75))
    except Exception: pass
    try:
        st2 = ta.stoch(hi, lo, c)
        if st2 is not None:
            s['STOCH'] = safe((st2.iloc[:, 0] > 40) & (st2.iloc[:, 0] < 80))
    except Exception: pass
    try:
        roc = ta.roc(c, 12)
        if roc is not None:
            s['ROC'] = safe(roc > 0)
    except Exception: pass
    try:
        cci = ta.cci(hi, lo, c, 20)
        if cci is not None:
            s['CCI'] = safe((cci > 0) & (cci < 150))
    except Exception: pass
    try:
        wr = ta.willr(hi, lo, c, 14)
        if wr is not None:
            s['WILLR'] = safe((wr > -50) & (wr < -20))
    except Exception: pass
    try:
        mom = ta.mom(c, 10)
        if mom is not None:
            s['MOM'] = safe(mom > 0)
    except Exception: pass
    try:
        tsi = ta.tsi(c)
        if tsi is not None:
            tsi_col = tsi.iloc[:, 0] if hasattr(tsi, 'iloc') else tsi
            s['TSI'] = safe(tsi_col > 0)
    except Exception: pass
    try:
        ppo = ta.ppo(c)
        if ppo is not None and ppo.shape[1] >= 2:
            s['PPO'] = safe(ppo.iloc[:, 0] > ppo.iloc[:, 1])
    except Exception: pass
    try:
        # Elder Ray bull power: high - EMA13 > 0
        e13 = ta.ema(c, 13)
        if e13 is not None:
            s['ELDER'] = safe(hv > e13.values)
    except Exception: pass

    # ── VOLUME ──────────────────────────────────────────────────────────
    try:
        obv = ta.obv(c, vo)
        if obv is not None:
            ov = obv.values
            rise = np.zeros(n, dtype=np.int8)
            rise[5:] = ((ov[5:] > ov[:-5]) & (cv[5:] > cv[:-5])).astype(np.int8)
            s['OBV'] = rise
    except Exception: pass
    try:
        mfi = ta.mfi(hi, lo, c, vo, 14)
        if mfi is not None:
            s['MFI'] = safe((mfi > 50) & (mfi < 80))
    except Exception: pass
    try:
        # CMF computed manually (pandas_ta.cmf signature unreliable across versions)
        rng = (hi - lo).replace(0, np.nan)
        mfm = ((c - lo) - (hi - c)) / rng
        mfv = mfm * vo
        cmf_ = mfv.rolling(20).sum() / vo.rolling(20).sum()
        s['CMF'] = safe(cmf_ > 0)
    except Exception: pass
    try:
        tp   = (hi + lo + c) / 3
        vwap = (tp * vo).rolling(20).sum() / vo.rolling(20).sum()
        s['VWAP'] = safe(cv > vwap.values)
    except Exception: pass
    try:
        ad = ta.ad(hi, lo, c, vo)
        if ad is not None:
            adv = ad.values
            rise = np.zeros(n, dtype=np.int8)
            rise[5:] = (adv[5:] > adv[:-5]).astype(np.int8)
            s['ADLINE'] = rise
    except Exception: pass
    try:
        vol_ma = vo.rolling(20).mean()
        s['VOLMA'] = safe(vv > vol_ma.values)
    except Exception: pass
    try:
        # Force Index: close-diff * volume, then EMA13
        fi = (c.diff() * vo).ewm(span=13, adjust=False).mean()
        s['FORCE'] = safe(fi > 0)
    except Exception: pass
    try:
        vol_chg = vo.pct_change().fillna(0)
        vol_rsi = ta.rsi(vol_chg.add(1.0), 14)
        if vol_rsi is not None:
            s['VOLRSI'] = safe(vol_rsi > 50)
    except Exception: pass

    # ── VOLATILITY ──────────────────────────────────────────────────────
    try:
        bb = ta.bbands(c, 20)
        if bb is not None and bb.shape[1] >= 3:
            s['BB'] = safe(cv >= bb.iloc[:, 1].values)
    except Exception: pass
    try:
        atr = ta.atr(hi, lo, c, 14)
        if atr is not None:
            atrp = (atr / c).fillna(0)
            atr_ma = atrp.rolling(20).mean()
            s['ATR'] = safe(atrp > atr_ma)
    except Exception: pass
    try:
        kc = ta.kc(hi, lo, c, 20)
        if kc is not None and kc.shape[1] >= 3:
            s['KELT'] = safe(cv > kc.iloc[:, 1].values)
    except Exception: pass
    try:
        dc_hi = hi.rolling(20).max()
        s['DONCH'] = safe(cv >= dc_hi.values * 0.98)
    except Exception: pass
    try:
        # Squeeze: BB inside KC = consolidating; bullish breakout when close > upper KC
        bb2 = ta.bbands(c, 20); kc2 = ta.kc(hi, lo, c, 20)
        if bb2 is not None and kc2 is not None:
            s['SQZ'] = safe(cv > kc2.iloc[:, 2].values)
    except Exception: pass
    try:
        ret = c.pct_change()
        hv_ = ret.rolling(20).std() * (252 ** 0.5) * 100
        hv_ma = hv_.rolling(20).mean()
        s['HV'] = safe(hv_ > hv_ma)
    except Exception: pass
    try:
        sd = c.rolling(20).std()
        sd_ma = sd.rolling(20).mean()
        s['STDEV'] = safe(sd > sd_ma)
    except Exception: pass
    try:
        # Chandelier exit (long): highest_high(22) - 3 * ATR(22)
        atr22 = ta.atr(hi, lo, c, 22)
        if atr22 is not None:
            chand = hi.rolling(22).max() - 3 * atr22
            s['CHAND'] = safe(cv > chand.values)
    except Exception: pass

    # ── SUPPORT & RESISTANCE ────────────────────────────────────────────
    try:
        # Pivot points: bullish above PP = (H+L+C)/3 of prior bar
        pp = ((hi + lo + c) / 3).shift(1)
        s['PIVOT'] = safe(cv > pp.values)
    except Exception: pass
    try:
        # Fib: 61.8% retracement of 60-bar range
        hh60 = hi.rolling(60).max(); ll60 = lo.rolling(60).min()
        fib_618 = ll60 + 0.618 * (hh60 - ll60)
        s['FIB'] = safe(cv > fib_618.values)
    except Exception: pass
    try:
        adx = ta.adx(hi, lo, c)
        if adx is not None and adx.shape[1] >= 3:
            s['ADX'] = safe((adx.iloc[:, 1] > adx.iloc[:, 2]) & (adx.iloc[:, 0] > 20))
    except Exception: pass
    try:
        tp2 = (hi + lo + c) / 3
        vwap_b = (tp2 * vo).rolling(20).sum() / vo.rolling(20).sum()
        vwap_std = (tp2 - vwap_b).rolling(20).std()
        vwap_upper = vwap_b + vwap_std
        s['VWAPB'] = safe(cv > vwap_upper.values)
    except Exception: pass
    try:
        prev_high = hi.shift(1).rolling(20).max()
        s['PREVHL'] = safe(cv > prev_high.values)
    except Exception: pass
    try:
        # Swing high: most recent local-max-high of 10 bars
        swing = hi.rolling(10).max().shift(1)
        s['SWINGHL'] = safe(cv > swing.values)
    except Exception: pass

    # ── MEAN REVERSION ──────────────────────────────────────────────────
    try:
        rsi2 = ta.rsi(c, 14)
        if rsi2 is not None:
            s['RSIEXT'] = safe(rsi2 < 35)
    except Exception: pass
    try:
        bb3 = ta.bbands(c, 20)
        if bb3 is not None and bb3.shape[1] >= 3:
            mid = bb3.iloc[:, 1]; std = (bb3.iloc[:, 2] - bb3.iloc[:, 1]) / 2.0
            z = (c - mid) / std
            s['BBZ'] = safe(z < -1.5)
    except Exception: pass
    try:
        ma50 = c.rolling(50).mean()
        dist = (c - ma50) / ma50
        s['DISTMA'] = safe(dist < -0.05)
    except Exception: pass
    try:
        st3 = ta.stoch(hi, lo, c)
        if st3 is not None:
            s['STOCHEXT'] = safe(st3.iloc[:, 0] < 20)
    except Exception: pass
    try:
        cci2 = ta.cci(hi, lo, c, 20)
        if cci2 is not None:
            s['CCIEXT'] = safe(cci2 < -100)
    except Exception: pass

    # ── MARKET REGIME (single-stock proxies) ─────────────────────────────
    # Indicators that genuinely need cross-stock data (TASIF, SECTORF, RSTASI,
    # RSSECTOR, ADVDEC, NEWHL) are approximated here using the stock's own
    # series so they can still contribute. Replace with true market data later.
    try:
        # "TASI Filter" proxy: stock above its 50-day MA (long-side filter)
        ma50f = c.rolling(50).mean()
        s['TASIF'] = safe(cv > ma50f.values)
    except Exception: pass
    try:
        # Sector filter proxy: 20-day return positive
        ret20 = c.pct_change(20)
        s['SECTORF'] = safe(ret20 > 0)
    except Exception: pass
    try:
        # RS vs TASI proxy: 60-day return > 0
        ret60 = c.pct_change(60)
        s['RSTASI'] = safe(ret60 > 0)
    except Exception: pass
    try:
        # RS vs Sector proxy: 20d return > 60d-mean-of-20d-returns
        ret20b = c.pct_change(20)
        ret20_ma = ret20b.rolling(60).mean()
        s['RSSECTOR'] = safe(ret20b > ret20_ma)
    except Exception: pass
    try:
        # Adv/Decline proxy: 10-day count of up-days > 5
        up = (c.diff() > 0).astype(int)
        adv = up.rolling(10).sum()
        s['ADVDEC'] = safe(adv > 5)
    except Exception: pass
    try:
        # New Hi/Lo proxy: at or near 60-day high
        hh = hi.rolling(60).max()
        s['NEWHL'] = safe(cv >= hh.values * 0.97)
    except Exception: pass

    return s


# ── regime per bar ────────────────────────────────────────────────────────────

def _regime_arr(df: pd.DataFrame) -> np.ndarray:
    """
    Per-bar regime classifier with FORCED-BALANCED per-stock assignment.

    The naive "ADX > threshold → TREND, ATR > threshold → VOLATILE" approach
    leaves many stocks with one regime massively dominant (e.g. 95% RANGE,
    5% VOLATILE). That makes per-regime strategy stats statistically empty.

    Instead, we score every bar twice — by trend strength (ADX) and by
    volatility (ATR/close) — and FORCE-ASSIGN bars to roughly 30% TREND, 30%
    VOLATILE, 40% RANGE per stock. Every stock gets a meaningful population
    of all three regimes, so combo search has something to work with.

    A small ABSOLUTE-floor guards against calling near-zero ADX bars "TREND";
    those get downgraded to RANGE even if they're in the top quantile.
    """
    n = len(df)
    if n < 30:
        return np.array(['RANGE'] * n, dtype=object)
    try:
        import pandas_ta as ta
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        atr = ta.atr(df['High'], df['Low'], df['Close'], 14)
        if adx is None or atr is None:
            return np.array(['RANGE'] * n, dtype=object)
        av   = adx.iloc[:, 0].fillna(0).values.astype(float)
        atrp = (atr / df['Close']).fillna(0).values.astype(float)

        # Skip warm-up bars when computing per-stock cutoffs
        warm  = max(20, n // 5)
        adx_w = av[warm:]
        atr_w = atrp[warm:]

        # 70th percentile of ADX → TREND cutoff (top 30% of bars are TREND)
        # 65th percentile of ATR/close → VOLATILE cutoff
        adx_cut = float(np.quantile(adx_w[adx_w > 0], 0.70)) if (adx_w > 0).any() else 25.0
        atr_cut = float(np.quantile(atr_w[atr_w > 0], 0.65)) if (atr_w > 0).any() else 0.022

        # Light absolute clamps: never call total noise "TREND", never call
        # a calm stock "VOLATILE" just because its top-decile ATR is tiny.
        adx_cut = max(15.0, min(adx_cut, 35.0))
        atr_cut = max(0.008, min(atr_cut, 0.05))

        out = np.full(n, 'RANGE', dtype=object)
        is_trend = av > adx_cut
        is_vol   = (atrp > atr_cut) & (~is_trend)
        out[is_trend] = 'TREND'
        out[is_vol]   = 'VOLATILE'

        # If any regime is still starved (<15 bars), force-rebalance:
        # promote the closest borderline bars from the dominant regime.
        from collections import Counter as _Counter
        cts = _Counter(out.tolist())
        for target, score in (('TREND', av), ('VOLATILE', atrp)):
            if cts.get(target, 0) >= 15:
                continue
            # bars currently in the most-populated regime, ranked by `score`
            dom = max(cts, key=cts.get)
            if dom == target:
                continue
            candidates = np.where(np.array([o == dom for o in out]))[0]
            if len(candidates) == 0:
                continue
            # take the top (15 - current) bars from `dom` by target's score
            need = 15 - cts.get(target, 0)
            order = sorted(candidates.tolist(), key=lambda i: -float(score[i]))
            promote = order[:need]
            for i in promote:
                # Don't steal from the OTHER non-RANGE regime; only steal
                # from the dominant one (RANGE in most stocks).
                out[i] = target
            cts = _Counter(out.tolist())

        return out
    except Exception:
        pass
    return np.array(['RANGE'] * n, dtype=object)


# ── evaluate an N-indicator combo ─────────────────────────────────────────────

def _eval(states_list: list[np.ndarray], close: np.ndarray,
          hold: int, pt: float, sl: float,
          regime_arr: np.ndarray | None = None,
          target_regime: str | None = None,
          min_signals: int = 5) -> dict | None:
    """
    Evaluate when ALL indicators in states_list are simultaneously bullish.
    If regime_arr + target_regime given, only score signals in that regime.
    Minimum `min_signals` resolved signals required (default 5). Sparse regimes
    can call with min_signals=3 so we still return a real best-fit combo.
    Win rate capped at 85% for realism. Score = win_rate * sqrt(total).
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

    if len(idxs) < min_signals:
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
    if total < min_signals:
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
        'wins':  wins,
        'losses': losses,
        'score': score,
    }


# ── greedy indicator expansion to up to 5 ────────────────────────────────────

def _grow_combo(seed_keys: list[str], all_states: dict[str, np.ndarray],
                close: np.ndarray, regime_arr: np.ndarray,
                hold: int, pt: float, sl: float,
                target_regime: str, max_size: int = 5,
                min_size: int = 3, min_signals: int = 5) -> dict | None:
    """
    Start from seed_keys, greedily add indicators within target_regime.
    Below min_size: pick best-WR addition (even if score drops from lower total)
    so the combo reaches 3+ indicators when possible.
    At/above min_size: only add if score strictly improves.
    """
    remaining = [k for k in all_states if k not in seed_keys]
    current_keys = list(seed_keys)
    current_res  = _eval([all_states[k] for k in current_keys],
                          close, hold, pt, sl, regime_arr, target_regime,
                          min_signals=min_signals)
    if current_res is None:
        return None

    while len(current_keys) < max_size and remaining:
        below_min = len(current_keys) < min_size
        best_add = None
        best_metric = -1.0 if below_min else current_res['score']
        best_res_local = None
        for k in remaining:
            candidate_keys = current_keys + [k]
            res = _eval([all_states[k2] for k2 in candidate_keys],
                         close, hold, pt, sl, regime_arr, target_regime,
                         min_signals=min_signals)
            if res is None:
                continue
            metric = res['win_rate'] if below_min else res['score']
            if metric > best_metric:
                best_metric = metric
                best_add    = k
                best_res_local = res
        if best_add is None:
            break
        current_keys.append(best_add)
        remaining.remove(best_add)
        current_res = best_res_local

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
def scan_stock(symbol: str, period_key: str, _v: int = 8) -> dict | None:
    """
    Single-stock entry — extracts from a pre-built batch cache when available,
    otherwise downloads individually. Cached 20 min.
    """
    return _process_stock_df(symbol, period_key)


@st.cache_data(ttl=1200, show_spinner=False)
def scan_all_stocks(symbols: tuple, period_key: str, _v: int = 18) -> dict:
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
def get_stock_df(symbol: str, period_key: str, _v: int = 8) -> 'pd.DataFrame | None':
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


def _best_combo_for_regime(states: dict, close: np.ndarray,
                            reg_arr: np.ndarray | None,
                            hold: int, pt: float, sl: float,
                            target_regime: str | None,
                            min_signals: int = 5,
                            min_size: int = 3) -> dict | None:
    """Find the best 2..5 indicator combo for a target regime (or overall if None).

    `min_signals` controls the statistical-significance floor. Sparse regimes
    can call with min_signals=3 so we still surface a real best-fit combo.
    `min_size` is the minimum number of indicators in the combo (default 3,
    can be lowered to 2 for sparse regimes where 3-indicator AND-overlaps are
    too rare).
    """
    keys = list(states.keys())
    if len(keys) < 2:
        return None
    ind_scores: list[tuple[float, str]] = []
    ind_results: dict[str, dict] = {}
    for k in keys:
        r = _eval([states[k]], close, hold, pt, sl, reg_arr, target_regime,
                  min_signals=min_signals)
        if r:
            ind_scores.append((r['score'], k))
            ind_results[k] = r
    if not ind_scores:
        return None
    ind_scores.sort(reverse=True)

    # Try greedy expansion from the top-2 seeds when we have enough candidates.
    grown = None
    if len(ind_scores) >= 2:
        seed = [ind_scores[0][1], ind_scores[1][1]]
        if reg_arr is None or target_regime is None:
            dummy_arr = np.array(['ALL'] * len(close), dtype=object)
            grown = _grow_combo(seed, states, close, dummy_arr,
                                hold, pt, sl, 'ALL',
                                max_size=5, min_size=min_size,
                                min_signals=min_signals)
        else:
            grown = _grow_combo(seed, states, close, reg_arr,
                                hold, pt, sl, target_regime,
                                max_size=5, min_size=min_size,
                                min_signals=min_signals)
        if grown is not None:
            return grown

    # Fallback (only reached when min_size <= 2): the top-2 seeds didn't
    # have enough AND-overlap. Brute-force scan all pairs of the top
    # candidates and return the best 2-indicator combo. This is the
    # honest sparse-regime answer — a real 2-indicator strategy, not a
    # 1-indicator "combo" (which isn't a combo at all).
    if min_size <= 2:
        # Brute-force pair search for sparse regimes. We can't rely on the
        # per-indicator score list here — an indicator with 1 in-regime fire
        # got filtered out, but its AND with another indicator might still
        # produce 2+ overlapping fires inside the regime.
        # So we search ALL indicator pairs. _eval is microseconds; for ~45
        # indicators that's ~990 pairs — still trivial.
        all_keys = list(states.keys())
        best_res = None
        best_score = -1.0
        for i in range(len(all_keys)):
            for j in range(i + 1, len(all_keys)):
                ka, kb = all_keys[i], all_keys[j]
                r = _eval([states[ka], states[kb]], close, hold, pt, sl,
                           reg_arr, target_regime, min_signals=min_signals)
                if r is None:
                    continue
                if r['score'] > best_score:
                    best_score = r['score']
                    best_res = (r, [ka, kb])
        if best_res is not None:
            res, keys2 = best_res
            res = dict(res)
            res['indicators'] = keys2
            res['label']      = _ind_labels(keys2)
            # dominant regime among signal bars
            combo_arr = states[keys2[0]] & states[keys2[1]]
            edge = np.zeros(len(combo_arr), dtype=np.int8)
            edge[1:] = ((combo_arr[1:] == 1) & (combo_arr[:-1] == 0)).astype(np.int8)
            idxs = np.where(edge == 1)[0]
            rc = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
            for ix in idxs:
                r2 = str(reg_arr[ix]) if (reg_arr is not None and ix < len(reg_arr)) else 'RANGE'
                if r2 in rc:
                    rc[r2] += 1
            res['best_regime'] = max(rc, key=rc.get)
            res['firing']      = bool(int(combo_arr[-1]) == 1)
            return res
    return None


def _analyse_df(df: pd.DataFrame, hold: int, pt: float, sl: float) -> dict | None:
    """
    Per-regime analysis: for EACH regime (TREND / RANGE / VOLATILE) independently
    search for the best 3..5 indicator combo using ONLY signals that fired while
    the market was in that regime. If a regime has no qualifying combo, that
    slot stays empty — never reuse another regime's combo, that's a lie.
    """
    try:
        price   = float(df['Close'].iloc[-1])
        states  = _build_states(df)
        reg_arr = _regime_arr(df)
        close   = df['Close'].values
        keys    = list(states.keys())

        if len(keys) < 2:
            return None

        best_per_regime: dict[str, dict | None] = {}
        for target_regime in ('TREND', 'RANGE', 'VOLATILE'):
            # Cascade across (min_signals, min_combo_size). Try strict 5-fire
            # 3-indicator combos first (best evidence), then progressively
            # relax to 3-fire 2-indicator combos. Each combo returned is
            # still real — same indicators, same regime filter, same outcome
            # walk; we're only lowering the *minimum sample size* needed to
            # report it. This avoids the alternative of either copying
            # another regime's combo (a lie) or showing empty boxes
            # everywhere (useless).
            grown = None
            cascade = [
                (5, 3), (4, 3), (3, 3),   # ideal: 3+ indicator combos, 5+ signals
                (5, 2), (4, 2), (3, 2),   # 2-indicator combos, 5/4/3 signals
                (2, 2),                   # sparse-regime last resort: 2-ind, 2-signal
            ]
            for _ms, _msz in cascade:
                grown = _best_combo_for_regime(
                    states, close, reg_arr, hold, pt, sl, target_regime,
                    min_signals=_ms, min_size=_msz)
                if grown is not None:
                    grown['min_signals_used'] = _ms
                    grown['min_size_used']    = _msz
                    break
            if grown is None:
                # Regime is genuinely too sparse to find anything real
                # (e.g. 0 bars assigned to it). Stay empty rather than lie.
                best_per_regime[target_regime] = None
                continue
            best_keys = grown['indicators']
            grown['firing']      = all(int(states[k][-1]) == 1 for k in best_keys)
            grown['best_regime'] = target_regime
            best_per_regime[target_regime] = grown

        current_regime = str(reg_arr[-1]) if len(reg_arr) else 'RANGE'
        return {'regimes': best_per_regime, 'price': price,
                'current_regime': current_regime}

    except Exception:
        return None
