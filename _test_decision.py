import traceback
try:
    from regime_analyzer import RegimeAnalyzer
    a = RegimeAnalyzer('1120.SR', '2024-04-15', '2026-04-16', ['EMA','RSI','MACD'])
    df = a.download_data()
    df = a.classify_regimes(lookback=30, adx_threshold=25, atr_threshold=0.03)
    cp = float(df.iloc[-1]['Close'])
    from decision_tab import _score_engine, _probability_engine
    d = _score_engine(df, cp)
    print('Verdict:', d['verdict'], 'Conf:', d['confidence'])
    print('Pct:', d['pct'], 'RR1:', d['rr1'], 'RR quality:', d['rr_quality'])
    print('Factors:')
    for f in d['factors']:
        print(f"  {f['dir']:+d} {f['pts']:+d}/{f['max']} {f['cat']}: {f['name']}")
    prob = _probability_engine(df, d)
    p10 = prob.get(10, {})
    print('Win prob 10d:', p10.get('prob_up'), 'N analogs:', p10.get('n_analogs'), 'EV:', p10.get('ev'))
    print('ALL OK')
except Exception:
    traceback.print_exc()
