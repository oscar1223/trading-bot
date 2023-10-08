# Bot for trading algorithm.

import os
from dotenv import load_dotenv, find_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

_ = load_dotenv(find_dotenv())
paper_alpaca_key = os.environ['PAPER_ALPACA_KEY']
paper_alpaca_secret_key = os.environ['PAPER_ALPACA_SECRET_KEY']


trading_client = TradingClient(paper_alpaca_key, paper_alpaca_secret_key, paper=True)

# preparing market order
market_order_data = MarketOrderRequest(
                    symbol="SPY",
                    qty=0.023,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY
                    )

# Market order
market_order = trading_client.submit_order(
                order_data=market_order_data
               )

# preparing limit order
limit_order_data = LimitOrderRequest(
                    symbol="BTC/USD",
                    limit_price=17000,
                    notional=4000,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.FOK
                   )

# Limit order
'''
limit_order = trading_client.submit_order(
                order_data=limit_order_data
              )
'''