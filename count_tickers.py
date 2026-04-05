import re
with open('market_data.py', encoding='utf-8') as f:
    content = f.read()
start = content.index('def get_all_tadawul_tickers():')
end = content.index('\ndef ', start + 10)
block = content[start:end]
import re
tickers = re.findall(r'"(\d{4}\.SR)"', block)
unique = set(tickers)
print(f'Unique tickers: {len(unique)}')
print(f'Total entries: {len(tickers)}')
dups = [t for t in unique if tickers.count(t) > 1]
if dups:
    print(f'Duplicates: {dups}')
else:
    print('No duplicates')
