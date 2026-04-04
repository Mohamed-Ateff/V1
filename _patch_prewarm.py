with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

OLD = (
    '                                        st.session_state.df = df\n'
    '                                        st.session_state.analyzed_symbol = symbol_input\n'
    "                                        st.session_state.additional_charts = ['ADX','RSI','MACD']\n"
    '                                        st.session_state.show_results = True'
)

NEW = (
    '                                        st.session_state.df = df\n'
    '                                        st.session_state.analyzed_symbol = symbol_input\n'
    "                                        st.session_state.additional_charts = ['ADX','RSI','MACD']\n"
    '\n'
    '                                        # Pre-warm AI Analysis + Trade Validator caches while\n'
    '                                        # the spinner is still showing — tabs load instantly on click.\n'
    '                                        try:\n'
    '                                            from gemini_tab import (\n'
    '                                                _ml_predict, _historical_analogy,\n'
    '                                                _price_predictor, _monte_carlo,\n'
    '                                            )\n'
    '                                            _ml_predict(df, horizon=5)\n'
    '                                            _ml_predict(df, horizon=10)\n'
    '                                            _ml_predict(df, horizon=20)\n'
    '                                            _price_predictor(df, horizon=20)\n'
    '                                            _historical_analogy(df, k=25, horizon=5)\n'
    '                                            _historical_analogy(df, k=25, horizon=10)\n'
    '                                            _historical_analogy(df, k=25, horizon=20)\n'
    '                                            _monte_carlo(df, days=20)\n'
    '                                        except Exception:\n'
    '                                            pass\n'
    '                                        try:\n'
    '                                            from decision_tab import _score_engine\n'
    '                                            _cp = float(df["Close"].iloc[-1])\n'
    '                                            _score_engine(df, _cp)\n'
    '                                        except Exception:\n'
    '                                            pass\n'
    '\n'
    '                                        st.session_state.show_results = True'
)

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('DONE')
else:
    print('NOT FOUND')
