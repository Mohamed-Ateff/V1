import re
with open("market_data.py", encoding="utf-8") as f:
    content = f.read()
start = content.index("def get_all_tadawul_tickers():")
end = content.index("\ndef ", start + 10)
block = content[start:end]
import re
pattern = '"([0-9][0-9][0-9][0-9][.]SR)"'
tickers = re.findall(pattern, block)
unique = sorted(set(tickers))
print("Total:", len(unique))
groups = {}
for t in unique:
    k = int(t[:4]) // 1000
    groups.setdefault(k, []).append(t[:4])
for k in sorted(groups):
    print(str(k)+"xxx ("+str(len(groups[k]))+"):", groups[k])
