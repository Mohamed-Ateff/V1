import yfinance as yf
# Check a few 9xxx tickers - are they on main market or NOMU?
test = ["9510.SR", "9653.SR", "9621.SR"]
for c in test:
    try:
        t = yf.Ticker(c)
        info = t.info
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        exchange = info.get("exchange") or info.get("fullExchangeName") or "?"
        name = info.get("shortName") or "?"
        print(f"{c}: {name} | exchange={exchange} | price={price}")
    except Exception as e:
        print(f"{c}: error {e}")
