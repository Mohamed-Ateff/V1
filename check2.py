import yfinance as yf

# Check more potential missing ones
more = ["8020.SR", "8045.SR", "8160.SR", "8301.SR", "8302.SR",
        "4343.SR", "4350.SR", "4351.SR",
        "1060.SR", "1070.SR", "1100.SR",
        "2283.SR", "2284.SR", "2285.SR",
        "4015.SR", "4016.SR", "4018.SR", "4020.SR",
        "1040.SR", "1030.SR"]

for c in more:
    try:
        t = yf.Ticker(c)
        price = t.fast_info.last_price
        if price and price > 0:
            name = t.info.get("shortName") or "?"
            print(f"  VALID: {c} = {name}")
        else:
            print(f"  no data: {c}")
    except Exception as e:
        print(f"  no data: {c}")
