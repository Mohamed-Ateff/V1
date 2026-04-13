import ast
files = ['decision_tab.py','signal_analysis_tab.py','volume_profile_tab.py','smc_tab.py','regime_analysis_tab.py','trade_validator_tab.py','price_action_tab.py']
for f in files:
    txt = open(f, encoding='utf-8-sig').read()
    c = txt.count('insight_toggle(')
    try:
        ast.parse(txt)
        print(f'{f}: {c} toggle(s) - syntax OK')
    except SyntaxError as e:
        print(f'{f}: {c} toggle(s) - SYNTAX ERROR: {e}')
