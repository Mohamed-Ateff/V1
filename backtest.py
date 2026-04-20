"""
Backtest Engine for ACPTS V15
Simulates trades using the same scoring logic to validate signal quality.
"""
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ── Import shared scoring utilities from ACPTS ────────────────────────
from acpts_tab_v2 import normalize, rsi_bell, score_to_probability


def run_backtest(price_data: pd.DataFrame, feature_data: list[dict], config: dict = None) -> dict:
    """
    Run a backtest simulation on historical stock data.

    Args:
        price_data: DataFrame with columns ['Date', 'Close', 'High', 'Low', 'Volume']
                    indexed by date or with a 'Date' column.
        feature_data: List of dicts, each representing a stock snapshot at a point in time.
                      Same format as market_data.run_market_analysis() output.
                      Each dict must have 'date' key (str or datetime).
        config: Optional configuration dict:
            - min_score: Minimum ACPTS score to enter (default 80)
            - stop_loss_pct: Stop loss percentage (default 0.05)
            - take_profit_pct: Take profit percentage (default 0.10)
            - hold_days: Max holding period in days (default 20)
            - initial_capital: Starting capital (default 100000)
            - position_size_pct: Fraction of capital per trade (default 0.10)

    Returns:
        dict with keys:
            - trades: list of trade dicts
            - win_rate: float (0-1)
            - expectancy: average return per trade
            - max_drawdown: maximum drawdown percentage
            - equity_curve: list of (date, equity) tuples
            - total_return: total return percentage
            - sharpe_ratio: annualized Sharpe ratio
            - total_trades: int
            - winning_trades: int
            - losing_trades: int
    """
    cfg = {
        'min_score': 80,
        'stop_loss_pct': 0.05,
        'take_profit_pct': 0.10,
        'hold_days': 20,
        'initial_capital': 100000,
        'position_size_pct': 0.10,
    }
    if config:
        cfg.update(config)

    # Ensure price_data has Date as column
    if isinstance(price_data.index, pd.DatetimeIndex):
        price_data = price_data.reset_index()
    if 'Date' not in price_data.columns:
        price_data.columns = ['Date'] + list(price_data.columns[1:])
    price_data = price_data.sort_values('Date').reset_index(drop=True)
    price_dates = pd.to_datetime(price_data['Date'])

    # Score each snapshot and filter by min_score
    signals = []
    for snap in feature_data:
        score = _quick_score(snap)
        if score >= cfg['min_score']:
            snap_date = pd.to_datetime(snap.get('date', snap.get('Date', None)))
            if snap_date is not None:
                signals.append({
                    'date': snap_date,
                    'score': score,
                    'probability': score_to_probability(score),
                    'snap': snap,
                })

    signals.sort(key=lambda x: x['date'])

    # Simulate trades
    trades = []
    capital = cfg['initial_capital']
    equity_curve = []
    peak_equity = capital

    for sig in signals:
        entry_date = sig['date']

        # Find entry price (next available close after signal date)
        entry_idx = price_dates.searchsorted(entry_date)
        if entry_idx >= len(price_data) - 1:
            continue
        entry_idx = min(entry_idx + 1, len(price_data) - 1)  # enter next day
        entry_price = price_data.loc[entry_idx, 'Close']
        entry_actual_date = price_data.loc[entry_idx, 'Date']

        # Position sizing
        position_value = capital * cfg['position_size_pct']
        shares = int(position_value / entry_price) if entry_price > 0 else 0
        if shares <= 0:
            continue

        stop_price = entry_price * (1 - cfg['stop_loss_pct'])
        target_price = entry_price * (1 + cfg['take_profit_pct'])
        max_exit_idx = min(entry_idx + cfg['hold_days'], len(price_data) - 1)

        # Walk forward to find exit
        exit_price = None
        exit_reason = None
        exit_idx = None

        for i in range(entry_idx + 1, max_exit_idx + 1):
            low = price_data.loc[i, 'Low']
            high = price_data.loc[i, 'High']
            close = price_data.loc[i, 'Close']

            if low <= stop_price:
                exit_price = stop_price
                exit_reason = "Stop Loss"
                exit_idx = i
                break
            elif high >= target_price:
                exit_price = target_price
                exit_reason = "Take Profit"
                exit_idx = i
                break

        # If no stop/target hit, exit at max holding period
        if exit_price is None:
            exit_idx = max_exit_idx
            exit_price = price_data.loc[exit_idx, 'Close']
            exit_reason = "Time Exit"

        exit_actual_date = price_data.loc[exit_idx, 'Date']
        pnl = (exit_price - entry_price) * shares
        pnl_pct = (exit_price - entry_price) / entry_price

        capital += pnl
        peak_equity = max(peak_equity, capital)

        trades.append({
            'entry_date': str(entry_actual_date)[:10],
            'exit_date': str(exit_actual_date)[:10],
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'shares': shares,
            'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct * 100, 2),
            'exit_reason': exit_reason,
            'score': sig['score'],
            'probability': round(sig['probability'] * 100, 1),
        })

        equity_curve.append((str(exit_actual_date)[:10], round(capital, 2)))

    # Calculate statistics
    if not trades:
        return {
            'trades': [],
            'win_rate': 0.0,
            'expectancy': 0.0,
            'max_drawdown': 0.0,
            'equity_curve': [(str(datetime.now().date()), cfg['initial_capital'])],
            'total_return': 0.0,
            'sharpe_ratio': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
        }

    winning = [t for t in trades if t['pnl'] > 0]
    losing = [t for t in trades if t['pnl'] <= 0]
    returns = [t['pnl_pct'] / 100 for t in trades]

    win_rate = len(winning) / len(trades)
    expectancy = sum(t['pnl_pct'] for t in trades) / len(trades)

    # Max drawdown from equity curve
    equities = [cfg['initial_capital']] + [e[1] for e in equity_curve]
    max_dd = 0
    peak = equities[0]
    for eq in equities:
        peak = max(peak, eq)
        dd = (peak - eq) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)

    total_return = (capital - cfg['initial_capital']) / cfg['initial_capital'] * 100

    # Sharpe ratio (annualized, assuming ~252 trading days)
    if len(returns) > 1:
        avg_ret = np.mean(returns)
        std_ret = np.std(returns, ddof=1)
        sharpe = (avg_ret / std_ret) * math.sqrt(252 / max(cfg['hold_days'], 1)) if std_ret > 0 else 0
    else:
        sharpe = 0

    return {
        'trades': trades,
        'win_rate': round(win_rate, 3),
        'expectancy': round(expectancy, 2),
        'max_drawdown': round(max_dd * 100, 2),
        'equity_curve': equity_curve,
        'total_return': round(total_return, 2),
        'sharpe_ratio': round(sharpe, 2),
        'total_trades': len(trades),
        'winning_trades': len(winning),
        'losing_trades': len(losing),
    }


def _quick_score(snap: dict) -> float:
    """
    Simplified scoring using the same V15 logic as _score_stock.
    Uses normalize() for continuous scoring — no hard thresholds.
    """
    score = 0.0

    # 1. Trend (0-30)
    if snap.get('above_ema200', False):
        score += 10
    if snap.get('weekly_bullish', False):
        score += 10
    if snap.get('monthly_bullish', False):
        score += 5
    rp = snap.get('range_pos', 50)
    score += normalize(50 - rp, 0, 50) * 5

    # 2. Momentum (0-20) — NO volume
    adx = snap.get('adx', 0)
    perf_5d = snap.get('perf_5d', 0)
    price_strength = normalize(perf_5d, -3, 10)
    adx_norm = normalize(adx, 10, 40)
    score += (adx_norm * 0.7 + price_strength * 0.3) * 20

    # 3. Sector RS (0-15)
    rs = snap.get('rs_vs_tasi', 0)
    score += normalize(rs, -2, 8) * 15

    # 4. RSI (0-10)
    rsi = snap.get('rsi', 50)
    score += rsi_bell(rsi) * 10

    # 5. Signal (0-10)
    sig_score = snap.get('score', 0)
    score += normalize(sig_score, 0, 18) * 10

    # 6. Macro (0-10)
    regime = snap.get('regime', 'RANGE')
    perf_3m = snap.get('perf_3m', 0)
    if regime != 'VOLATILE':
        score += 5
    score += normalize(perf_3m, -5, 10) * 5

    # 7. Smart Money (0-10)
    vol_ratio = snap.get('volume_ratio', 1)
    obv_rising = snap.get('obv_rising', False)
    sm_score = normalize(vol_ratio, 1.0, 2.5) * 0.6 + (0.4 if obv_rising else 0)
    score += sm_score * 10

    # 8. Penalty
    risk = snap.get('risk', 2)
    eq = snap.get('entry_quality', 'Fair')
    score -= normalize(risk, 2, 6) * 10
    if eq == 'Poor':
        score -= 5
    elif eq == 'Fair':
        score -= 2

    return round(max(0, score), 1)
