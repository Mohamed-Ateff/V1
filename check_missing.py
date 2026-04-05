import yfinance as yf

# Test tickers we know might be missing
candidates = [
    "3004.SR", "3008.SR", "3080.SR", "3002.SR", "3040.SR", "3005.SR", "3009.SR",
    "4330.SR", "4331.SR", "4332.SR", "4333.SR", "4334.SR", "4335.SR", "4336.SR",
    "4337.SR", "4338.SR", "4339.SR", "4340.SR", "4341.SR", "4342.SR", "4344.SR",
    "4345.SR", "4346.SR", "4347.SR", "4348.SR", "4349.SR",
    "5111.SR", "5112.SR",
    "4013.SR", "4017.SR", "4031.SR", "4061.SR",
    "8030.SR", "8070.SR", "8100.SR", "8110.SR", "8120.SR", "8130.SR", "8140.SR",
    "8180.SR", "8210.SR", "8260.SR", "8270.SR", "8290.SR", "8320.SR",
    "4410.SR", "4411.SR", "4412.SR",
    "1213.SR", "7210.SR", "7201.SR",
]

print("Checking missing candidates...")
for c in candidates:
    try:
        t = yf.Ticker(c)
        info = t.fast_info
        price = info.last_price if hasattr(info, 'last_price') else None
        if price and price > 0:
            print(f"  VALID: {c} = {price}")
        else:
            print(f"  no data: {c}")
    except Exception as e:
        print(f"  error: {c}: {e}")
