import os
import time
from dotenv import load_dotenv, find_dotenv
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

# Env vars
_ = load_dotenv(find_dotenv())
paper_alpaca_endpoint = os.environ['PAPER_ALPACA_ENDPOINT']
paper_alpaca_key = os.environ['PAPER_ALPACA_KEY']
paper_alpaca_secret_key = os.environ['PAPER_ALPACA_SECRET_KEY']

ALPACA_CONFIG = {
     "API_KEY": paper_alpaca_key,
     "API_SECRET": paper_alpaca_secret_key,
     "ENDPOINT": paper_alpaca_endpoint
 }


# A simple strategy that buys AAPL on the first day and hold it
class MyStrategy(Strategy):
   def on_trading_iteration(self):
      if self.first_iteration:
            aapl_price = self.get_last_price("AAPL")
            quantity = self.portfolio_value // aapl_price
            order = self.create_order("AAPL", quantity, "buy")
            self.submit_order(order)


trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
strategy = MyStrategy(broker=broker)

# Run the strategy live
trader.add_strategy(strategy)
trader.run_all()

