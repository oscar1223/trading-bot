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


'''
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
'''

class LongShort:
    def __init__(self):
        self.alpaca = tradeapi.REST(key_id=paper_alpaca_key, secret_key=paper_alpaca_secret_key, base_url=paper_alpaca_endpoint)

        stockUniverse = ['TSLA', 'NVDA', 'AMZN', 'META']

        # Format the allStock variable for use in the class.
        self.allStock = []
        for stock in stockUniverse:
            self.allStock.append([stock, 0])

        self.long = []
        self.short = []
        self.qShort = None
        self.qLong = None
        self.adjustedQLong = None
        self.adjustedQShort = None
        self.blacklist = set()
        self.longAmount = 0
        self.shortAmount = 0
        self.timeToClose = None

    def run(self):
        # First, cancel any existing orders so they don't impact our buying power.

        orders = self.alpaca.list_orders(status='open')
        for order in orders:
            self.alpaca.cancel_order(order.id)

        # Wait for market to open




