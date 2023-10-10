# Bot for trading algorithm.

import os
from dotenv import load_dotenv, find_dotenv
import alpaca_trade_api as tradeapi
import matplotlib.pyplot as plt

_ = load_dotenv(find_dotenv())
paper_alpaca_endpoint = os.environ['PAPER_ALPACA_ENDPOINT']
paper_alpaca_key = os.environ['PAPER_ALPACA_KEY']
paper_alpaca_secret_key = os.environ['PAPER_ALPACA_SECRET_KEY']

api = tradeapi.REST(key_id=paper_alpaca_key, secret_key=paper_alpaca_secret_key, base_url=paper_alpaca_endpoint)

# Define los parametros para la consulta de cotizaciones del stock
symbol = 'AAPL'
timeframe = '1Day'
start = '2022-01-01'
end = '2023-01-01'

# Realiza la consulta de cotización
bars = api.get_bars(symbol, timeframe, start=start, end=end)

# Imprime la cotizacion en consola
for bar in bars:
    print(f"{bar.t} - Open: {bar.o}, High: {bar.h}, Low: {bar.l}, Close: {bar.c}", flush=True)
