import datetime

import backtrader as bt
import yfinance as yf



class BaseStrategy(bt.Strategy):
    params = dict(
        fast_ma=10,
        slow_ma=20,
    )

    def __init__(self):
        # omitting a data implies self.datas[0] (aka self.data and self.data0)
        fast_ma = bt.ind.EMA(period=self.p.fast_ma)
        slow_ma = bt.ind.EMA(period=self.p.slow_ma)
        # our entry point
        self.crossup = bt.ind.CrossUp(fast_ma, slow_ma)


class ManualStopOrStopTrail(BaseStrategy):
    params = dict(
        stop_loss=0.02,  # price is 2% less than the entry point
        trail=False,
    )

    def notify_order(self, order):
        if not order.status == order.Completed:
            return  # discard any other notification

        if not self.position:  # we left the market
            print("SL hit")
            print(f'SELL@price: {order.executed.price}, exectype = {bt.Order.ExecTypes[order.exectype]}')
            return

        # We have entered the market
        #print('BUY @price: {:.2f}'.format(order.executed.price))
        print(f'BUY @price: {order.executed.price}, exectype = {bt.Order.ExecTypes[order.exectype]}')

        if not self.p.trail:
            stop_price = order.executed.price * (1.0 - self.p.stop_loss)
            self.sell(exectype=bt.Order.Stop, price=stop_price)
        else:
            self.sell(exectype=bt.Order.StopTrail, trailamount=self.p.stop_loss)

    def next(self):
        if not self.position and self.crossup > 0:
            # not in the market and signal triggered
            print("Bought new position")
            self.buy()


class ManualStopOrStopTrailCheat(BaseStrategy):
    params = dict(
        stop_loss=0.02,  # price is 2% less than the entry point
        trail=False,
    )

    def __init__(self):
        super().__init__()
        self.broker.set_coc(True)

    def notify_order(self, order):
        if not order.status == order.Completed:
            return  # discard any other notification

        if not self.position:  # we left the market
            print('SELL@price: {:.2f}'.format(order.executed.price))
            return

        # We have entered the market
        print('BUY @price: {:.2f}'.format(order.executed.price))

    def next(self):
        if not self.position and self.crossup > 0:
            # not in the market and signal triggered
            self.buy()

            if not self.p.trail:
                stop_price = self.data.close[0] * (1.0 - self.p.stop_loss)
                self.sell(exectype=bt.Order.Stop, price=stop_price)
            else:
                self.sell(exectype=bt.Order.StopTrail,
                          trailamount=self.p.trail)


class AutoStopOrStopTrail(BaseStrategy):
    params = dict(
        stop_loss=0.02,  # price is 2% less than the entry point
        trail=2,
        buy_limit=False,
    )

    buy_order = None  # default value for a potential buy_order

    def notify_order(self, order):
        if order.status == order.Cancelled:
            print('CANCEL@price: {:.2f} {}'.format(
                order.executed.price, 'buy' if order.isbuy() else 'sell'))
            return

        if not order.status == order.Completed:
            return  # discard any other notification

        if not self.position:  # we left the market
            print('SELL@price: {:.2f}'.format(order.executed.price))
            return

        # We have entered the market
        print('BUY @price: {:.2f}'.format(order.executed.price))

    def next(self):
        if not self.position and self.crossup > 0:
            if self.buy_order:  # something was pending
                self.cancel(self.buy_order)

            # not in the market and signal triggered
            if not self.p.buy_limit:
                self.buy_order = self.buy(transmit=False)
            else:
                price = self.data.close[0] * (1.0 - self.p.buy_limit)

                # transmit = False ... await child order before transmission
                self.buy_order = self.buy(price=price, exectype=bt.Order.Limit,
                                          transmit=False)

            # Setting parent=buy_order ... sends both together
            if not self.p.trail:
                stop_price = self.data.close[0] * (1.0 - self.p.stop_loss)
                self.sell(exectype=bt.Order.Stop, price=stop_price,
                          parent=self.buy_order)
            else:
                self.sell(exectype=bt.Order.StopTrail,
                          trailamount=self.p.trail,
                          parent=self.buy_order)


if __name__ == '__main__':
    # Back test the BuyChandelierStrategy with BackTrader
    cerebro = bt.Cerebro()

    cerebro.broker.setcash(100000.0)
    #cerebro.broker.setcommission(commission=0.0035)
    #cerebro.addindicator(ChandelierExitIndicator)
    cerebro.addstrategy(ManualStopOrStopTrail)
    data = bt.feeds.PandasData(dataname=yf.download('AAPL', '2021-01-01', '2022-10-05'))

    cerebro.adddata(data)

    startValue = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % startValue)

    cerebro.run()

    endValue = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % endValue)

    cerebro.plot()