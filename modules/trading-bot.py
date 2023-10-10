# Bot for trading algorithm.

import os
import threading
from dotenv import load_dotenv, find_dotenv
import alpaca_trade_api as tradeapi
import matplotlib.pyplot as plt
import datetime
import time

_ = load_dotenv(find_dotenv())
paper_alpaca_endpoint = os.environ['PAPER_ALPACA_ENDPOINT']
paper_alpaca_key = os.environ['PAPER_ALPACA_KEY']
paper_alpaca_secret_key = os.environ['PAPER_ALPACA_SECRET_KEY']

api = tradeapi.REST(key_id=paper_alpaca_key, secret_key=paper_alpaca_secret_key, base_url=paper_alpaca_endpoint)

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
        print('Waiting for the market to open...')
        tAMO = threading.Thread(target=self.awaitMarketOpen)
        tAMO.start()
        tAMO.join()
        print('Marked opened.')

        # Rebalance the portfolio every minute, making necessary trades.
        while True:

            # Figure out when the market will close  so we can prepare to sell beforehand.
            clock = self.alpaca.get_clock()
            closingTime = clock.next_close.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            self.timeToClose = closingTime - currTime

            if(self.timeToClose < (60*15)):
                # Close all positions when 15min til market close
                print('Market closing soon. Closing positions.')

                positions = self.alpaca.list_positions()
                for position in positions:
                    if(position.side == 'long'):
                        orderSide = 'sell'
                    else:
                        orderSide = 'buy'

                    qty = abs(int(float(position.qty)))
                    respSO = []
                    tSubmitOrder = threading.Thread(target=self.submitOrder(qty, position.symbol, orderSide, respSO))
                    tSubmitOrder.start()
                    tSubmitOrder.join()

                print('Sleeping until market close (15 minutes).')
                time.sleep(60 * 15)
            else:
                # Rebalance the portfolio.
                tRebalance = threading.Thread(target=self.rebalance)
                tRebalance.start()
                tRebalance.join()
                time.sleep(60)


    def awaitMarketOpen(self):
        # Wait for the market to open.
        isOpen = self.alpaca.get_clock().is_open

        while(not isOpen):
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=datetime.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            print(str(timeToOpen) + 'minutes til market open.')
            time.sleep(60)
            isOpen = self.alpaca.get_clock().is_open

    def rebalance(self):
        tRerank = threading.Thread(target=self.rerank)
        tRerank.start()
        tRerank.join()

        # Clear existing orders again.
        orders = self.alpaca.list_orders(status='open')
        for order in orders:
            self.alpaca.cancel_order(order.id)

        print('We are taking a long position in: '+str(self.long))
        print('We are taking a short position in '+str(self.short))
        # Remove posiotns that are no longer in the short or long
        # list, and make a list of positions that do not need to change.
        # Adjust position quantities if needed.
        executed = [[], []]
        positions = self.alpaca.list_positions()
        self.blacklist.clear()
        for position in positions:
            if(self.long.count(position.symbol) == 0):
                # Position is not in long list
                if(self.short.count(position.symbol) == 0):
                    # Position is not in short list either. Clear position.
                    if(position.side == 'long'):
                        side = 'sell'
                    else:
                        side = 'buy'
                    respSO = []
                    tSO = threading.Thread(target=self.submitOrder,
                                           args= [int(float(position.qty)), position.symbol, side, respSO])
                    tSO.start()
                    tSO.join()
                else:
                    # Position in short list.
                    if(position.side == 'long'):
                        # Position changed from long to short. Clear long
                        # position to prepare for short position.
                        side = 'sell'
                        respSO = []
                        tSO = threading.Thread(target=self.submitOrder,
                                               args=[int(float(position.qty)), position.symbol, side, respSO])
                        tSO.start()
                        tSO.join()
                    else:
                        if(abs(int(float(position.qty))) == self.qShort):
                            # Position is where we want it. Pass for now.
                            pass
                        else:
                            # Need to adjust position amunt
                            diff = abs(int(float(position.qty))) - self.qShort
                            if(diff > 0):
                                # To many short positions. Buy some back to rebalance.
                                side = 'buy'
                            else:
                                # Too little short positions. Sell some more.
                                side = 'sell'
                                respSO = []
                                tSO = threading.Thread(target=self.submitOrder,
                                                       args=[abs(diff), position.symbol, side, respSO])
                                tSO.start()
                                tSO.join()
                            executed[1].append(position.symbol)
                            self.blacklist.add(position.symbol)
            else:
                # Position in long list
                if(position.side == 'short'):
                    # Position changed from short to long. Clear short position to prepear for long position.
                    respSO = []
                    tSO = threading.Thread(target=self.submitOrder,
                                           args=[abs(int(float(position.qty))), position.symbol, 'buy', respSO])
                    tSO.start()
                    tSO.join()
                else:
                    if(int(float(position.qty)) == self.qLong):
                        # Position is where we want it. Pass for now.
                        pass
                    else:
                        # Need to adjust position amunt
                        diff = abs(int(float(position.qty))) - self.qShort
                        if (diff > 0):
                            # To many short positions. Buy some back to rebalance.
                            side = 'sell'
                        else:
                            # Too little short positions. Sell some more.
                            side = 'buy'
                            respSO = []
                            tSO = threading.Thread(target=self.submitOrder,
                                                   args=[abs(diff), position.symbol, side, respSO])
                            tSO.start()
                            tSO.join()
                        executed[1].append(position.symbol)
                        self.blacklist.add(position.symbol)

        # Send orders to all remaining stocks in the long and short list.
        respSendBOLong = []
        tSendBOLong = threading.Thread(target=self.sendBatchOrder, args=[self.qLong, self.long, 'buy', respSendBOLong])
        tSendBOLong.start()
        tSendBOLong.join()
        respSendBOLong[0][0] += executed[0]
        if(len(respSendBOLong[0][1]) > 0):
            # Handle rejected/incomplete orders and determine new quantities to purchase.
            respGetTPLong = []
            tGetTPLong = threading.Thread(target=self.getTotalPrice, args=[respSendBOLong[0][0], respGetTPLong])
            tGetTPLong.start()
            tGetTPLong.join()
            if(respGetTPLong[0] > 0):
                self.adjustedQLong = self.longAmount // respGetTPLong[0]
            else:
                self.adjustedQLong = -1
        else:
            self.adjustedQLong = -1

        respSendBOShort = []
        tSendBOShort = threading.Thread(target=self.sendBatchOrder, args=[self.qShort, self.short, 'sell', respSendBOShort])
        tSendBOShort.start()
        tSendBOShort.join()
        respSendBOShort[0][0] += executed[1]
        if (len(respSendBOShort[0][1]) > 0):
            # Handle rejected/incomplete orders and determine new quantities to purchase.
            respGetTPShort = []
            tGetTPShort = threading.Thread(target=self.getTotalPrice, args=[respSendBOShort[0][0], respGetTPShort])
            tGetTPShort.start()
            tGetTPShort.join()
            if (respGetTPShort[0] > 0):
                self.adjustedQShort = self.shortAmount // respGetTPShort[0]
            else:
                self.adjustedQShort = -1
        else:
            self.adjustedQShort = -1

        # Reorder stock that didn't throw an error so that the equity quota is reached.
        if(self.adjustedQLong > -1):
            self.qLong = int(self.adjustedQLong - self.qLong)
            for stock in respSendBOLong[0][0]:
                respResendBOLong = []
                tResendBOLong = threading.Thread(target=self.submitOrder, args=[self.qLong, stock, 'buy', respResendBOLong])
                tResendBOLong.start()
                tResendBOLong.join()

        if (self.adjustedQShort > -1):
            self.qShort = int(self.adjustedQShort - self.qShort)
            for stock in respSendBOShort[0][0]:
                respResendBOShort = []
                tResendBOShort = threading.Thread(target=self.submitOrder,
                                                 args=[self.qShort, stock, 'sell', respResendBOShort])
                tResendBOShort.start()
                tResendBOShort.join()

    def rerank(self):
        # Rerank all stocks to adjust long and shorts.
        pass




















