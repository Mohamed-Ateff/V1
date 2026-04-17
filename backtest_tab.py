"""
Backtest Tab — Scans past data for what worked, then tells you
if there's a winning trade to take RIGHT NOW.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from signal_engine import detect_signals
from ui_helpers import insight_toggle

# ── Design tokens ─────────────────────────────────────────────────────────────
BULL, BEAR, NEUT, INFO, PURP, GOLD = (
    "#4caf50", "#f44336", "#ff9800", "#2196f3", "#9c27b0", "#FFD700",
)
_IND = {
    "EMA": "EMA 20/50", "SMA": "SMA 50/200", "PSAR": "Parabolic SAR",
    "ICHI": "Ichimoku", "WMA": "WMA 20", "RSI": "RSI",
    "MACD": "MACD", "STOCH": "Stochastic", "ROC": "ROC",
    "CCI": "CCI", "WILLR": "Williams %R", "BB": "Bollinger",
    "KC": "Keltner", "DC": "Donchian", "MFI": "MFI",
    "CMF": "CMF", "VWAP": "VWAP", "OBV": "OBV", "ADX": "ADX/DMI",
}
_CAPITAL    = 100_000
_RISK_PCT   = 2.0
_COMMISSION = 0.12
_MAX_HOLD   = 20
_ATR_TP     = 3.0
_ATR_SL     = 1.5


# ── Helpers ───────────────────────────────────────────────────────────────────
def _sec(title, color):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:0.6rem;"
        f"margin:1.5rem 0 0.6rem;'>"
        f"<div style='width:3px;height:18px;border-radius:2px;"
        f"background:{color};box-shadow:0 0 6px {color}44;'></div>"
        f"<span style='font-size:0.85rem;font-weight:800;color:#e0e0e0;"
        f"text-transform:uppercase;letter-spacing:1px;'>{title}</span></div>",
        unsafe_allow_html=True,
    )

def _glowbar(pct, color, h="5px"):
    return (
        f"<div style='width:100%;height:{h};background:#272727;border-radius:3px;"
        f"overflow:hidden;'>"
        f"<div style='width:{max(0,min(100,pct))}%;height:100%;"
        f"background:linear-gradient(90deg,{color},{color}bb);"
        f"border-radius:3px;box-shadow:0 0 6px {color}44;'></div></div>"
    )

def _pc(v):
    return BULL if v > 0 else (BEAR if v < 0 else "#888")

_TIP_CSS = """<style>
.bt-tip{position:relative;cursor:help;display:inline-flex;align-items:center}
.bt-tip .btt{
    visibility:hidden;opacity:0;position:absolute;bottom:140%;left:50%;
    transform:translateX(-50%);background:#1e1e1e;color:#bbb;border:1px solid #333;
    border-radius:6px;padding:0.4rem 0.6rem;font-size:0.75rem;font-weight:500;
    line-height:1.5;white-space:normal;width:240px;text-align:left;z-index:100;
    pointer-events:none;transition:opacity .15s;box-shadow:0 4px 14px rgba(0,0,0,.5);
    text-transform:none;letter-spacing:0}
.bt-tip .btt::after{content:'';position:absolute;top:100%;left:50%;
    transform:translateX(-50%);border:5px solid transparent;border-top-color:#333}
.bt-tip:hover .btt{visibility:visible;opacity:1}
.bt-q{display:inline-flex;align-items:center;justify-content:center;
    width:14px;height:14px;border-radius:50%;border:1px solid #444;
    font-size:0.5rem;color:#666;font-weight:700;margin-left:0.3rem}
</style>"""

def _tip(label, tooltip):
    """Wrap a label with a hover ? tooltip."""
    return (f"<span class='bt-tip'>{label}"
            f"<span class='bt-q'>?</span>"
            f"<span class='btt'>{tooltip}</span></span>")

def _grade(sharpe, mdd, pf, wr):
    s = min(30, max(0, sharpe * 10)) + min(20, max(0, 20 + mdd)) + \
        min(25, pf * 5 if pf < 100 else 25) + min(25, wr / 4)
    if s >= 85: return "A+", BULL
    if s >= 75: return "A",  BULL
    if s >= 65: return "B+", "#66bb6a"
    if s >= 55: return "B",  NEUT
    if s >= 45: return "C",  NEUT
    if s >= 35: return "D",  BEAR
    return "F", BEAR


# ── Core backtest engine (unchanged) ─────────────────────────────────────────
def _run_bt(df, sdf, inds, require_all=False):
    closes, highs, lows = df["Close"].values, df["High"].values, df["Low"].values
    n = len(df)
    if n < 30:
        return None
    dates = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df["Date"]).values

    if "ATR_14" in df.columns:
        atr = df["ATR_14"].values
    else:
        tr = pd.DataFrame({"hl": highs - lows,
                           "hc": np.abs(highs - np.roll(closes, 1)),
                           "lc": np.abs(lows  - np.roll(closes, 1))}).max(axis=1)
        atr = tr.rolling(14).mean().values

    buy_cols = [f"{i}_Buy" for i in inds if f"{i}_Buy" in sdf.columns]
    if not buy_cols:
        return None
    bm = sdf[buy_cols].values.astype(bool)
    entry = bm.all(axis=1) if require_all else bm.any(axis=1)

    trades, equity = [], _CAPITAL
    eq = np.full(n, _CAPITAL, dtype=float)
    in_t = False
    ep = ei = sh = 0
    for i in range(14, n):
        if not in_t and entry[i]:
            ep = closes[i]
            if ep <= 0:
                eq[i] = equity; continue
            a = atr[i] if not np.isnan(atr[i]) else ep * 0.02
            sd = a * _ATR_SL
            sh = max(1, int(equity * _RISK_PCT / 100 / sd)) if sd > 0 else max(1, int(equity * 0.1 / ep))
            if sh * ep * (1 + _COMMISSION / 100) > equity:
                sh = max(1, int(equity / (ep * (1 + _COMMISSION / 100))))
            in_t, ei = True, i
        if in_t:
            a = atr[i] if not np.isnan(atr[i]) else ep * 0.02
            tp_l, sl_l = ep + a * _ATR_TP, ep - a * _ATR_SL
            days = i - ei
            xr = xp = None
            if highs[i] >= tp_l:   xp, xr = tp_l, "TP"
            elif lows[i] <= sl_l:  xp, xr = sl_l, "SL"
            elif days >= _MAX_HOLD: xp, xr = closes[i], "Max Hold"
            if xr:
                pnl = sh * xp * (1 - _COMMISSION / 100) - sh * ep * (1 + _COMMISSION / 100)
                equity += pnl
                rgm = str(df.iloc[ei].get("REGIME", "N/A")) if "REGIME" in df.columns else "N/A"
                trades.append({"entry_date": dates[ei], "exit_date": dates[i],
                               "entry_price": round(ep, 2), "exit_price": round(xp, 2),
                               "shares": sh, "pnl": round(pnl, 2),
                               "pnl_pct": round((xp / ep - 1) * 100, 2),
                               "days_held": days, "exit_reason": xr, "regime": rgm})
                in_t = False
        eq[i] = equity

    if in_t:
        xp = closes[-1]
        pnl = sh * xp * (1 - _COMMISSION / 100) - sh * ep * (1 + _COMMISSION / 100)
        equity += pnl; eq[-1] = equity
        rgm = str(df.iloc[ei].get("REGIME", "N/A")) if "REGIME" in df.columns else "N/A"
        trades.append({"entry_date": dates[ei], "exit_date": dates[-1],
                       "entry_price": round(ep, 2), "exit_price": round(xp, 2),
                       "shares": sh, "pnl": round(pnl, 2),
                       "pnl_pct": round((xp / ep - 1) * 100, 2),
                       "days_held": n - 1 - ei, "exit_reason": "Open", "regime": rgm})

    if not trades:
        return None

    tdf = pd.DataFrame(trades)
    wins, losses = tdf[tdf["pnl"] > 0], tdf[tdf["pnl"] <= 0]
    total = len(tdf)
    wr = len(wins) / total * 100
    aw = wins["pnl_pct"].mean() if len(wins) else 0
    al = losses["pnl_pct"].mean() if len(losses) else 0
    gp = wins["pnl"].sum() if len(wins) else 0
    gl = abs(losses["pnl"].sum()) if len(losses) else 0
    pf = gp / gl if gl > 0 else 99.99
    ret = (equity - _CAPITAL) / _CAPITAL * 100
    eq_s = pd.Series(eq)
    mdd = ((eq_s - eq_s.cummax()) / eq_s.cummax() * 100).min()
    dr = eq_s.pct_change().dropna()
    sharpe = (dr.mean() / dr.std()) * np.sqrt(252) if len(dr) > 1 and dr.std() > 0 else 0
    expect = (wr / 100 * aw) + ((1 - wr / 100) * al)

    seq = (tdf["pnl"] > 0).astype(int).tolist()
    mws = mls = cw = cl = 0
    for r in seq:
        if r: cw += 1; cl = 0; mws = max(mws, cw)
        else: cl += 1; cw = 0; mls = max(mls, cl)

    tdf["month"] = tdf["exit_date"].astype("datetime64[ns]").dt.to_period("M")
    monthly = tdf.groupby("month")["pnl"].sum()

    rstats = {}
    for rgn in ["TREND", "RANGE", "VOLATILE"]:
        rt = tdf[tdf["regime"] == rgn]
        if len(rt):
            rw = rt[rt["pnl"] > 0]
            rstats[rgn] = {"trades": len(rt), "win_rate": len(rw) / len(rt) * 100,
                           "avg_pnl": rt["pnl_pct"].mean(), "total_pnl": rt["pnl"].sum()}

    score = (sharpe * 0.35 + (wr / 100) * 0.25
             + min(pf, 5) / 5 * 0.25 + max(0, 15 + mdd) / 15 * 0.15)

    return {
        "trades_df": tdf, "equity_curve": eq, "dates": dates,
        "final_equity": round(equity, 2), "net_profit": round(equity - _CAPITAL, 2),
        "total_return": round(ret, 2), "total_trades": total,
        "win_count": len(wins), "loss_count": len(losses),
        "win_rate": round(wr, 1), "avg_win": round(aw, 2), "avg_loss": round(al, 2),
        "avg_hold": round(tdf["days_held"].mean(), 1),
        "max_win": round(tdf["pnl_pct"].max(), 2),
        "max_loss": round(tdf["pnl_pct"].min(), 2),
        "profit_factor": round(pf, 2), "max_drawdown": round(mdd, 2),
        "sharpe": round(sharpe, 2), "expectancy": round(expect, 2),
        "max_win_streak": mws, "max_loss_streak": mls,
        "monthly_pnl": monthly, "regime_stats": rstats,
        "gross_profit": round(gp, 2), "gross_loss": round(gl, 2),
        "score": round(score, 4), "inds": inds,
    }


# ── Check what signals are firing NOW ─────────────────────────────────────────
def _live_signals(sdf, inds):
    """Check last 3 bars for active buy/sell signals from given indicators."""
    if len(sdf) < 3:
        return []
    tail = sdf.tail(3)
    active = []
    for ind in inds:
        bc, sc = f"{ind}_Buy", f"{ind}_Sell"
        for idx in range(len(tail) - 1, -1, -1):
            row = tail.iloc[idx]
            if bc in sdf.columns and row.get(bc, 0) == 1:
                active.append({"ind": ind, "type": "BUY", "bar": len(tail) - 1 - idx})
                break
            if sc in sdf.columns and row.get(sc, 0) == 1:
                active.append({"ind": ind, "type": "SELL", "bar": len(tail) - 1 - idx})
                break
    return active


# ═══════════════════════════════════════════════════════════════════════════════
#  PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def backtest_tab(df: pd.DataFrame, current_price: float):

    # ── Plain-language intro ──────────────────────────────────────────────
    st.markdown(
        "<div style='background:#161616;border:1px solid #272727;border-radius:10px;"
        "padding:0.8rem 1rem;margin-bottom:1rem;'>"
        "<div style='font-size:0.8rem;color:#bbb;line-height:1.7;'>"
        "This tab looks at <strong style='color:#e0e0e0;'>your past data</strong> and tests "
        "every indicator to find which ones <strong style='color:#4caf50;'>actually made money</strong> "
        "in the past. Then it checks if any of those winning indicators are giving a signal "
        "<strong style='color:#FFD700;'>right now</strong>. "
        "If yes → it tells you the trade. If no → it says wait."
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ── Run engine ────────────────────────────────────────────────────────
    with st.spinner("Scanning past data for winning strategies…"):
        sdf = detect_signals(df)
        available = [k for k in _IND if f"{k}_Buy" in sdf.columns]
        if not available:
            st.error("Not enough data to scan for signals.")
            return

        # Test every individual indicator
        all_res = {}
        for ind in available:
            r = _run_bt(df, sdf, [ind])
            if r:
                all_res[ind] = r

        # Top-6 → test all pairs
        top6 = sorted(all_res.values(), key=lambda x: x["score"], reverse=True)[:6]
        tk = [r["inds"][0] for r in top6]
        for i in range(len(tk)):
            for j in range(i + 1, len(tk)):
                pair = [tk[i], tk[j]]
                r = _run_bt(df, sdf, pair, require_all=True)
                if r:
                    all_res[f"{pair[0]}+{pair[1]}"] = r

        if not all_res:
            st.error("No historical trades found. Not enough signal activity.")
            return

    ranked = sorted(all_res.items(), key=lambda x: x[1]["score"], reverse=True)

    # ── Find trade opportunities NOW ──────────────────────────────────────
    # Check which of the top strategies have a signal firing right now
    opportunities = []
    for key, res in ranked[:10]:  # check top 10 strategies
        inds = res["inds"]
        is_combo = len(inds) > 1
        live = _live_signals(sdf, inds)

        buy_hits = [s for s in live if s["type"] == "BUY"]
        sell_hits = [s for s in live if s["type"] == "SELL"]

        if is_combo:
            # For combos, all must fire BUY
            if len(buy_hits) == len(inds):
                sig_type = "BUY"
            elif len(sell_hits) == len(inds):
                sig_type = "SELL"
            else:
                continue
        else:
            if buy_hits:
                sig_type = "BUY"
            elif sell_hits:
                sig_type = "SELL"
            else:
                continue

        # Calculate trade levels using ATR
        atr_val = df["ATR_14"].iloc[-1] if "ATR_14" in df.columns else current_price * 0.02
        if np.isnan(atr_val):
            atr_val = current_price * 0.02

        if sig_type == "BUY":
            entry = current_price
            sl = round(entry - atr_val * _ATR_SL, 2)
            tp = round(entry + atr_val * _ATR_TP, 2)
            rr = round((tp - entry) / (entry - sl), 2) if entry > sl else 0
        else:
            entry = current_price
            sl = round(entry + atr_val * _ATR_SL, 2)
            tp = round(entry - atr_val * _ATR_TP, 2)
            rr = round((entry - tp) / (sl - entry), 2) if sl > entry else 0

        label = " + ".join(_IND.get(i, i) for i in inds)
        opportunities.append({
            "label": label, "key": key, "type": sig_type,
            "entry": entry, "sl": sl, "tp": tp, "rr": rr,
            "res": res, "inds": inds,
        })

    champ_name, champ = ranked[0]
    champ_label = " + ".join(_IND.get(i, i) for i in champ["inds"])
    grade, gcol = _grade(champ["sharpe"], champ["max_drawdown"],
                         champ["profit_factor"], champ["win_rate"])

    # ══════════════════════════════════════════════════════════════════════
    # ── HERO: Trade Opportunity or No Trade ──────────────────────────────
    # ══════════════════════════════════════════════════════════════════════

    # Inject tooltip CSS once
    st.markdown(_TIP_CSS, unsafe_allow_html=True)

    if opportunities:
        opp = opportunities[0]  # best opportunity
        sc = BULL if opp["type"] == "BUY" else BEAR
        bias = opp["type"]
        bias_glow = f"rgba({','.join(str(int(sc[i:i+2], 16)) for i in (1,3,5))},0.08)"
        conf = int(min(99, max(10, opp["res"]["win_rate"])))
        conf_color = BULL if conf >= 60 else (NEUT if conf >= 40 else BEAR)

        # Trade levels with tooltip explanations
        tiles = [
            (_tip("Entry", "The price you would enter the trade at right now."),
             f"{opp['entry']:.2f}", "#e0e0e0"),
            (_tip("Take Profit", "If price reaches this level, you close and collect your profit. Based on 3× the stock's average daily range."),
             f"{opp['tp']:.2f}", BULL),
            (_tip("Stop Loss", "If price drops to this level, you close to limit your loss. Based on 1.5× the stock's average daily range."),
             f"{opp['sl']:.2f}", BEAR),
            (_tip("Risk:Reward", "For every 1 SAR you risk losing, you could gain this many SAR. Higher is better — 1:2+ is good."),
             f"1:{opp['rr']:.1f}", INFO),
            (_tip("Past Win Rate", "Out of all past trades using this strategy, this % were winners. Above 50% means it won more than it lost."),
             f"{opp['res']['win_rate']:.0f}%",
             BULL if opp["res"]["win_rate"] >= 50 else BEAR),
        ]
        tiles_html = "".join(
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.35rem;'>{l}</div>"
            f"<div style='font-size:1.15rem;font-weight:900;color:{c};line-height:1;'>{v}</div></div>"
            for l, v, c in tiles
        )

        st.markdown(
            f"<div style='background:#1b1b1b;border:1px solid #272727;border-radius:14px;"
            f"overflow:hidden;margin-bottom:1.2rem;box-shadow:0 4px 24px rgba(0,0,0,0.3);'>"
            f"<div style='padding:2rem 2.2rem;"
            f"background:linear-gradient(135deg,{bias_glow},transparent);'>"

            # top row
            f"<div style='display:flex;align-items:flex-start;justify-content:space-between;"
            f"margin-bottom:1.6rem;gap:2rem;'>"

            # left
            f"<div style='flex:1;'>"
            f"<div style='font-size:0.57rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:1.5px;font-weight:700;margin-bottom:0.4rem;'>"
            f"Trade Opportunity Found</div>"
            f"<div style='font-size:0.85rem;color:#888;margin-bottom:1.2rem;'>"
            f"This signal won {opp['res']['win_count']} out of {opp['res']['total_trades']} past trades "
            f"using {opp['label']}</div>"

            f"<div style='display:flex;align-items:center;gap:1.2rem;'>"
            f"<div style='background:{bias_glow};border:2px solid {sc};"
            f"border-radius:14px;padding:0.55rem 1.6rem;'>"
            f"<div style='font-size:2.4rem;font-weight:900;color:{sc};"
            f"letter-spacing:2px;line-height:1;text-shadow:0 0 20px {sc}33;'>"
            f"{bias}</div></div>"
            f"<div>"
            f"<div style='font-size:0.7rem;color:#888;font-weight:600;"
            f"margin-bottom:0.15rem;'>{_tip('Signal Trigger', 'This strategy just triggered a signal in the last 1-3 trading days. It means the conditions that led to past winning trades are happening again right now.')}</div>"
            f"<div style='font-size:0.78rem;color:#bbb;'>"
            f"{_tip('Past Return', 'If you followed ONLY this strategy from the start, your 100K would have gained or lost this %. Positive = the strategy made money overall.')} &nbsp;<b style='color:{_pc(opp['res']['total_return'])};"
            f"font-size:0.95rem;'>{opp['res']['total_return']:+.1f}%</b></div>"
            f"</div></div></div>"

            # right: confidence
            f"<div style='text-align:center;background:#161616;border:1px solid #272727;"
            f"border-radius:16px;padding:1.2rem 1.8rem;min-width:110px;flex-shrink:0;'>"
            f"<div style='font-size:0.57rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>"
            f"{_tip('Win Rate', 'How often this strategy won in the past. 60%+ means it won 6 out of every 10 trades — that is strong.')}</div>"
            f"<div style='font-size:2.6rem;font-weight:900;color:{conf_color};"
            f"line-height:1;margin-bottom:0.4rem;text-shadow:0 0 20px {conf_color}33;'>"
            f"{conf}%</div>"
            + _glowbar(conf, conf_color) +
            f"</div></div></div>"

            # bottom tiles — trade levels
            f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.6rem;"
            f"padding:0.9rem 2.2rem 1.2rem;border-top:1px solid #272727;'>"
            f"{tiles_html}</div></div>",
            unsafe_allow_html=True,
        )

        # Insight note — explain the trade card
        insight_toggle(
            "bt_hero_trade",
            "What does this trade card mean?",
            "<p><strong>How to read this:</strong> We tested this indicator on ALL your past data. "
            "Every time it gave a Buy signal in the past, we simulated entering a trade with a stop loss "
            "and take profit. The <strong>Win Rate</strong> shows how often those trades were profitable.</p>"
            "<p><strong>Why a trade now?</strong> This same signal just fired again in the last 1-3 days. "
            "Since it worked well historically, it may work again.</p>"
            "<p><strong>Entry</strong> = current price. <strong>TP</strong> = where to take profit. "
            "<strong>SL</strong> = where to cut your loss. <strong>R:R</strong> = how much you gain vs risk. "
            "A 1:2 R:R means you gain 2 for every 1 you risk.</p>"
            "<p style='color:#ff9800;'>⚠ Past results don't guarantee future wins. Always manage your risk.</p>"
        )

        # If more opportunities exist, show them as smaller cards
        if len(opportunities) > 1:
            _sec("Other Active Signals", NEUT)
            cols = st.columns(min(3, len(opportunities) - 1))
            for idx, op in enumerate(opportunities[1:4]):
                oc = BULL if op["type"] == "BUY" else BEAR
                with cols[idx % 3]:
                    st.markdown(
                        f"<div style='background:#161616;border:1px solid #272727;"
                        f"border-radius:12px;overflow:hidden;'>"
                        f"<div style='height:3px;background:{oc};'></div>"
                        f"<div style='padding:0.7rem;'>"
                        f"<div style='display:flex;justify-content:space-between;"
                        f"align-items:center;margin-bottom:0.4rem;'>"
                        f"<span style='font-size:0.65rem;font-weight:800;color:#e0e0e0;'>"
                        f"{op['label']}</span>"
                        f"<span style='font-size:0.6rem;font-weight:900;color:{oc};"
                        f"background:{oc}15;padding:0.1rem 0.4rem;border-radius:4px;'>"
                        f"{op['type']}</span></div>"
                        f"<div style='display:flex;gap:0.5rem;'>"
                        f"<div style='flex:1;text-align:center;'>"
                        f"<div style='font-size:0.82rem;font-weight:800;color:{BULL};'>"
                        f"{op['tp']:.2f}</div>"
                        f"<div style='font-size:0.35rem;color:#555;text-transform:uppercase;'>"
                        f"TP</div></div>"
                        f"<div style='flex:1;text-align:center;'>"
                        f"<div style='font-size:0.82rem;font-weight:800;color:{BEAR};'>"
                        f"{op['sl']:.2f}</div>"
                        f"<div style='font-size:0.35rem;color:#555;text-transform:uppercase;'>"
                        f"SL</div></div>"
                        f"<div style='flex:1;text-align:center;'>"
                        f"<div style='font-size:0.82rem;font-weight:800;"
                        f"color:{BULL if op['res']['win_rate'] >= 50 else BEAR};'>"
                        f"{op['res']['win_rate']:.0f}%</div>"
                        f"<div style='font-size:0.35rem;color:#555;text-transform:uppercase;'>"
                        f"WR</div></div>"
                        f"</div></div></div>",
                        unsafe_allow_html=True,
                    )

    else:
        # No trade right now
        st.markdown(
            f"<div style='background:#1b1b1b;border:1px solid #272727;border-radius:14px;"
            f"overflow:hidden;margin-bottom:1.2rem;box-shadow:0 4px 24px rgba(0,0,0,0.3);'>"
            f"<div style='padding:2rem 2.2rem;'>"

            f"<div style='display:flex;align-items:flex-start;justify-content:space-between;"
            f"margin-bottom:1.6rem;gap:2rem;'>"
            f"<div style='flex:1;'>"
            f"<div style='font-size:0.57rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:1.5px;font-weight:700;margin-bottom:0.4rem;'>"
            f"Backtest Complete</div>"
            f"<div style='font-size:0.85rem;color:#888;margin-bottom:1.2rem;'>"
            f"Tested {len(ranked)} strategies across all indicators</div>"

            f"<div style='display:flex;align-items:center;gap:1.2rem;'>"
            f"<div style='background:rgba(255,152,0,0.08);border:2px solid {NEUT};"
            f"border-radius:14px;padding:0.55rem 1.6rem;'>"
            f"<div style='font-size:2.4rem;font-weight:900;color:{NEUT};"
            f"letter-spacing:2px;line-height:1;'>WAIT</div></div>"
            f"<div>"
            f"<div style='font-size:0.7rem;color:#888;font-weight:600;"
            f"margin-bottom:0.15rem;'>No Active Signal</div>"
            f"<div style='font-size:0.78rem;color:#bbb;'>"
            f"No winning strategy is firing right now</div>"
            f"</div></div></div>"

            # right: best strategy found
            f"<div style='text-align:center;background:#161616;border:1px solid #272727;"
            f"border-radius:16px;padding:1.2rem 1.8rem;min-width:110px;flex-shrink:0;'>"
            f"<div style='font-size:0.57rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:1px;font-weight:700;margin-bottom:0.5rem;'>Best Found</div>"
            f"<div style='font-size:2.6rem;font-weight:900;color:{gcol};"
            f"line-height:1;margin-bottom:0.4rem;'>{grade}</div>"
            + _glowbar(champ["win_rate"], gcol) +
            f"</div></div></div>"

            # bottom: best strategy stats
            f"<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:0.6rem;"
            f"padding:0.9rem 2.2rem 1.2rem;border-top:1px solid #272727;'>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.35rem;'>Best Strategy</div>"
            f"<div style='font-size:0.82rem;font-weight:800;color:#e0e0e0;'>"
            f"{champ_label}</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.35rem;'>Past Return</div>"
            f"<div style='font-size:1.15rem;font-weight:900;"
            f"color:{_pc(champ['total_return'])};'>"
            f"{champ['total_return']:+.1f}%</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.35rem;'>Win Rate</div>"
            f"<div style='font-size:1.15rem;font-weight:900;"
            f"color:{BULL if champ['win_rate'] >= 50 else BEAR};'>"
            f"{champ['win_rate']:.0f}%</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.35rem;'>Trades</div>"
            f"<div style='font-size:1.15rem;font-weight:900;color:#e0e0e0;'>"
            f"{champ['total_trades']}</div></div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.48rem;color:#606060;text-transform:uppercase;"
            f"letter-spacing:0.8px;font-weight:700;margin-bottom:0.35rem;'>Profit Factor</div>"
            f"<div style='font-size:1.15rem;font-weight:900;"
            f"color:{BULL if champ['profit_factor'] >= 1.5 else NEUT};'>"
            f"{champ['profit_factor']:.2f}</div></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        insight_toggle(
            "bt_hero_wait",
            "Why WAIT?",
            "<p>We tested every indicator on your past data. The best strategy we found is shown above, "
            "but it is <strong>not</strong> giving a buy or sell signal right now.</p>"
            "<p><strong>What should you do?</strong> Wait. When this strategy fires a new signal, "
            "come back and check this tab — it will show you the trade with entry, TP, and SL levels.</p>"
            "<p>The <strong>Grade</strong> shows overall quality: A+ is excellent, C is average, F is bad. "
            "<strong>Win Rate</strong> = how often past trades won. "
            "<strong>Profit Factor</strong> = total profits ÷ total losses (above 1.5 is good).</p>"
        )

    # ══════════════════════════════════════════════════════════════════════
    # ── PROOF: Simple summary of why you should trust this ───────────────
    # ══════════════════════════════════════════════════════════════════════

    best = opportunities[0]["res"] if opportunities else champ
    best_label = opportunities[0]["label"] if opportunities else champ_label

    _sec("The Proof — Why Trust This Signal", INFO)

    # Plain-language summary card
    wr = best["win_rate"]
    total = best["total_trades"]
    wins = best["win_count"]
    losses = best["loss_count"]
    ret = best["total_return"]
    avg_w = best["avg_win"]
    avg_l = best["avg_loss"]
    avg_hold = best["avg_hold"]
    wr_color = BULL if wr >= 50 else BEAR
    ret_color = BULL if ret > 0 else BEAR

    # What happened when this strategy traded in the past
    if ret > 0:
        money_msg = f"turned <strong style='color:{BULL};'>100K into {best['final_equity']:,.0f} SAR</strong> (+{ret:.1f}%)"
    else:
        money_msg = f"would have <strong style='color:{BEAR};'>lost {abs(ret):.1f}%</strong> of your money"

    if wr >= 60:
        trust_msg = f"That's a <strong style='color:{BULL};'>strong win rate</strong> — it wins more often than it loses."
    elif wr >= 50:
        trust_msg = f"That's <strong style='color:{NEUT};'>decent</strong> — it wins slightly more than it loses."
    else:
        trust_msg = f"That's <strong style='color:{BEAR};'>below average</strong> — be careful, it loses more often than it wins."

    st.markdown(
        f"<div style='background:#161616;border:1px solid #272727;border-radius:12px;"
        f"padding:1.2rem 1.4rem;margin-bottom:0.8rem;'>"
        f"<div style='font-size:0.85rem;color:#ccc;line-height:2;'>"

        f"We tested <strong style='color:#e0e0e0;'>{best_label}</strong> on all your past data.<br>"

        f"It made <strong style='color:#e0e0e0;'>{total} trades</strong> in total — "
        f"<strong style='color:{BULL};'>{wins} won</strong> and "
        f"<strong style='color:{BEAR};'>{losses} lost</strong>.<br>"

        f"Win rate: <strong style='color:{wr_color};font-size:1.1rem;'>{wr:.0f}%</strong>. "
        f"{trust_msg}<br>"

        f"When it won, the average gain was <strong style='color:{BULL};'>+{avg_w:.1f}%</strong>. "
        f"When it lost, the average loss was <strong style='color:{BEAR};'>{avg_l:.1f}%</strong>.<br>"

        f"Trades lasted about <strong style='color:#e0e0e0;'>{avg_hold:.0f} days</strong> on average.<br>"

        f"Overall, this strategy {money_msg}."

        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── Simple equity chart — just "did it make money over time?" ──────
    _sec("Money Over Time — Did This Strategy Work?", INFO)

    insight_toggle(
        "bt_equity",
        "How to read this chart?",
        "<p>The blue line starts at 100,000 SAR (imaginary money). "
        "If the line goes <strong>up</strong>, the strategy was making money. "
        "If it goes <strong>down</strong>, it was losing money.</p>"
        "<p>A line that trends upward over time = good strategy. "
        "A line that goes sideways or down = weak strategy.</p>"
    )

    _render_equity_simple(best)


def _render_equity_simple(r):
    """Simple single-line equity chart — just shows if the strategy made money."""
    dates, eq = r["dates"], r["equity_curve"]
    final = eq[-1] if len(eq) else _CAPITAL
    color = BULL if final > _CAPITAL else BEAR

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=eq, mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy",
        fillcolor=f"rgba({','.join(str(int(color[i:i+2], 16)) for i in (1,3,5))},0.06)",
        name="Your Money",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=[_CAPITAL] * len(dates), mode="lines",
        line=dict(color="#555", width=1, dash="dash"),
        name="Starting 100K",
    ))
    fig.update_layout(
        height=300, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
        yaxis=dict(showgrid=True, gridcolor="#1e1e1e",
                   title=dict(text="SAR", font=dict(size=10, color="#555"))),
        xaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True)
