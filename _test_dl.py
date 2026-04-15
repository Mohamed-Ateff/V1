import yfinance as yf
import pandas as pd
import time

print("yfinance", yf.__version__)

# Test 1: yf.download with retry
for sym in ["2222.SR", "1120.SR"]:
    for attempt in range(3):
        df = yf.download(sym, period="5d", progress=False)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            last = float(df["Close"].iloc[-1])
            print(f"  {sym}: OK shape={df.shape} last={last}")
            break
        time.sleep(2)
    else:
        print(f"  {sym}: yf.download FAILED")
        # Fallback: Ticker.history
        try:
            t = yf.Ticker(sym)
            df2 = t.history(period="5d")
            if df2 is not None and not df2.empty:
                print(f"  {sym}: Ticker.history OK shape={df2.shape}")
            else:
                print(f"  {sym}: Ticker.history also FAILED")
        except Exception as e:
            print(f"  {sym}: Ticker.history error: {e}")
