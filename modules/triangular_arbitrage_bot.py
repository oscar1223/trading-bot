import os

import time
from dotenv import load_dotenv, find_dotenv
from alpaca.trading.client import TradingClient
import alpaca_trade_api as alpaca
import requests
import asyncio

# Env vars
_ = load_dotenv(find_dotenv())
paper_alpaca_endpoint = os.environ['PAPER_ALPACA_ENDPOINT']
paper_alpaca_key = os.environ['PAPER_ALPACA_KEY']
paper_alpaca_secret_key = os.environ['PAPER_ALPACA_SECRET_KEY']

trading_client = TradingClient(paper_alpaca_key, paper_alpaca_secret_key)

# Get our account information.
account = trading_client.get_account()

# Check if our account is restricted from trading.
if account.trading_blocked:
    print('Account is currently restricted from trading.')

# Check how much money we can use to open new positions.
print('${} is available as buying power.'.format(account.buying_power))

# Check our current balance vs. our balance at the last market close
balance_change = float(account.equity) - float(account.last_equity)
print(f'Today\'s portfolio balance change: ${balance_change}')

'''Triangular Arbitrage trading bot'''

rest_api = alpaca.REST(paper_alpaca_key, paper_alpaca_secret_key, paper_alpaca_endpoint)

# Init vars
waitTime = 3
min_arb_percent = 0.3

client = TradingClient(paper_alpaca_key, paper_alpaca_secret_key, paper=True)
account = dict(client.get_account())
for k,v in account.items():
    print(f"{k:30}{v}")


HEADERS = {'APCA-API-KEY-ID': paper_alpaca_key,
           'APCA-API-SECRET-KEY': paper_alpaca_secret_key}

prices = {
    'ETH/USD': 0,
    'BTC/USD': 0,
    'ETH/BTC': 0
}


async def get_quote(symbol: str):
   #Get quote data from Alpaca API
    try:
        # make the request
        quote = requests.get('{0}/v1beta2/crypto/latest/trades?symbols={1}'.format(paper_alpaca_endpoint, symbol), headers=HEADERS)
        prices[symbol] = quote.json()['trades'][symbol]['p']
        # Status code 200 means the request was successful
        if quote.status_code != 200:
            print("Undesirable response from Alpaca! {}".format(quote.json()))
            return False

    except Exception as e:
        print("There was an issue getting trade quote from Alpaca: {0}".format(e))
        return False

def post_alpaca_order(symbol, qty, side):
    #Post an order to Alpaca
    try:
        order = requests.post(
            '{0}/v2/orders'.format(paper_alpaca_endpoint), headers=HEADERS, json={
                'symbol': symbol,
                'qty': qty,
                'side': side,
                'type': 'market',
                'time_in_force': 'gtc',
            })
        return order
    except Exception as e:
        print("There was an issue posting order to Alpaca: {0}".format(e))
        return False

async def check_arb(spreads=None):
    '''
    Check to see if an arbitrage condition exists
    '''
    ETH = prices['ETH/USD']
    BTC = prices['BTC/USD']
    ETHBTC = prices['ETH/BTC']
    DIV = ETH / BTC
    spread = abs(DIV - ETHBTC)
    BUY_ETH = 1000 / ETH
    BUY_BTC = 1000 / BTC
    BUY_ETHBTC = BUY_BTC / ETHBTC
    SELL_ETHBTC = BUY_ETH / ETHBTC

    if DIV > ETHBTC * (1 + min_arb_percent / 100):
        order1 = post_alpaca_order("BTCUSD", BUY_BTC, "buy")
        if order1.status_code == 200:
            order2 = post_alpaca_order("ETH/BTC", BUY_ETHBTC, "buy")
            if order2.status_code == 200:
                order3 = post_alpaca_order("ETHUSD", BUY_ETHBTC, "sell")
                if order3.status_code == 200:
                    print("Done (type 1) eth: {} btc: {} ethbtc {}".format(ETH, BTC, ETHBTC))
                    print("Spread: +{}".format(spread * 100))
                else:
                    post_alpaca_order("ETH/BTC", BUY_ETHBTC, "sell")
                    print("Bad Order 3")
                    exit()
            else:
                post_alpaca_order("BTCUSD", BUY_BTC, "sell")
                print("Bad Order 2")
                exit()
        else:
            print("Bad Order 1")
            exit()

    # when ETH/USD is cheaper
    elif DIV < ETHBTC * (1 - min_arb_percent / 100):
        order1 = post_alpaca_order("ETHUSD", BUY_ETH, "buy")
        if order1.status_code == 200:
            order2 = post_alpaca_order("ETH/BTC", BUY_ETH, "sell")
            if order2.status_code == 200:
                order3 = post_alpaca_order("BTCUSD", SELL_ETHBTC, "sell")
                if order3.status_code == 200:
                    print("Done (type 2) eth: {} btc: {} ethbtc {}".format(ETH, BTC, ETHBTC))
                    print("Spread: -{}".format(spread * 100))
                else:
                    post_alpaca_order("ETH/BTC", SELL_ETHBTC, "buy")
                    print("Bad Order 3")
                    exit()
            else:
                post_alpaca_order("ETHUSD", BUY_ETH, "sell")
                print("Bad Order 2")
                exit()
        else:
            print("Bad order 1")
            exit()
    else:
        print("No arb opportunity, spread: {}".format(spread * 100))
        spreads.append(spread)


async def main():
    while True:
        task1 = loop.create_task(get_quote("ETH/USD"))
        task2 = loop.create_task(get_quote("BTC/USD"))
        task3 = loop.create_task(get_quote("ETH/BTC"))
        # Wait for the tasks to finish
        await asyncio.wait([task1, task2, task3])
        await check_arb()
        # # Wait for the value of waitTime between each quote request
        await asyncio.sleep(waitTime)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
