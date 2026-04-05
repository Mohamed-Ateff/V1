import yfinance as yf

valid_new = ["3002.SR", "3004.SR", "3005.SR", "3008.SR", "3040.SR", "3080.SR",
             "4330.SR", "4331.SR", "4332.SR", "4334.SR", "4335.SR", "4337.SR",
             "4338.SR", "4339.SR", "4340.SR", "4344.SR", "4345.SR", "4346.SR",
             "4348.SR", "4349.SR",
             "4013.SR", "4017.SR", "4061.SR",
             "8030.SR", "8070.SR", "8100.SR", "8120.SR", "8180.SR", "8210.SR", "8260.SR",
             "7201.SR"]

for c in valid_new:
    try:
        t = yf.Ticker(c)
        name = t.info.get("longName") or t.info.get("shortName") or "?"
        print(f'  "{c}": "{name}"')
    except Exception as e:
        print(f'  "{c}": ERROR {e}')
