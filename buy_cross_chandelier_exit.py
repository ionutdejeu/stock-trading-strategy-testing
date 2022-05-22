import backtrader as bt
import pandas as pd
import yfinance as yf

length = 22
mult = 1
showSellBuyLabels = True
useCloset = True
highlightSate = True


def read_csv(datapath):
    return pd.read_csv(datapath, parse_dates=True, index_col=0)


class ChandelierExitIndicator(bt.Indicator):
    alias = ('CE', 'ChandelierExit',)
    lines = ('long', 'short')
    params = (('period', 1), ('multip', 2),)
    plotinfo = dict(subplot=False)
    plotlines = dict(
        long=dict(_samecolor=True),  # use same color as prev line (dcm)
        short=dict(_samecolor=True),  # use same color as prev line (dch)
    )

    def __init__(self):
        self.heikenAshi = bt.indicators.HeikinAshi(plot=False)
        # self.heikenAshi.plotinfo = dict(style= "candle")

        self.dataclose1 = self.heikenAshi.close
        self.high = self.heikenAshi.high

        highest = bt.ind.Highest(self.high, period=self.p.period, plot=False)
        lowest = bt.ind.Lowest(self.dataclose1, period=self.p.period, plot=False)
        atr = self.p.multip * bt.ind.ATR(self.heikenAshi, period=self.p.period, plot=False)
        self.lines.long = highest - atr
        self.lines.short = lowest + atr

        self.zlsma = bt.indicators.ZeroLagIndicator(period=50, plot=False)


    def next(self):
        print((self.lines.long[0],self.lines.short[0]))


class ChandelierExitStrategy2(bt.SignalStrategy):
    params = (('stake', 100),)

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        self.cdl_exit = ChandelierExitIndicator()
        crossover_long = bt.indicators.CrossDown(self.cdl_exit.zlsma, self.cdl_exit.lines.long)
        crossover_short = bt.indicators.CrossUp(self.cdl_exit.zlsma, self.cdl_exit.lines.short)

        self.signal_add(bt.SIGNAL_LONG, crossover_long)
        self.signal_add(bt.SIGNAL_SHORT, crossover_short)

class ChandelierExitStrategy(bt.Strategy):
    params = (('stake', 100),)

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.heikenAshi = bt.indicators.HeikinAshi(plot=False)
        #self.heikenAshi.plotinfo = dict(style= "candle")

        self.dataclose1 = self.heikenAshi.close
        self.high = self.heikenAshi.high
        self.chan_exit_l = bt.indicators.Highest(self.high, period=22,plot=False,
                                                 plotskip=True) - 3 * bt.indicators.AverageTrueRange(period=3,
                                                                                                     plot=False,
                                                                                                     plotskip=True)

        self.rsa = bt.indicators.RSI_SMA(period=14, plotskip=True)
        self.zlsma = bt.indicators.ZeroLagIndicator(period=50,plot=False)

    def next(self):

        if self.dataclose1[0] < self.chan_exit_l[0] and \
                self.dataclose1[-1] >= self.chan_exit_l[-1] and \
                self.zlsma < self.dataclose1[0]:
            self.buy()


# Create a Stratey
class BuyChandelierStrategy(bt.Strategy):
    params = (('stake', 100),)


    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose1 = self.datas[0].close
        self.high = self.datas[0].high
        self.chan_exit_l = bt.ind.Highest(self.high, period=22) - 3 * bt.ind.ATR(period=22)

        self.rsa = bt.ind.RSI_SMA(period=14)

    def next(self):

        if self.dataclose1[0] < self.chan_exit_l[0] and \
                self.dataclose1[-1] >= self.chan_exit_l[-1] and \
                self.rsa <= 35:
            self.log('BUY CREATE, price=%.2f chan=%.2f  %.2f' % (
                self.dataclose1[0],
                self.chan_exit_l[0],
                self.rsa[0],
            ))

            self.buy()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


def backtest():
    # Read CSV (From Yahoo) to Pandas dataframe

    # Back test the BuyChandelierStrategy with BackTrader
    cerebro = bt.Cerebro()

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.0035)
    cerebro.addindicator(ChandelierExitIndicator)
    cerebro.addstrategy(ChandelierExitStrategy2)
    data = bt.feeds.PandasData(dataname=yf.download('TSLA', '2021-01-01', '2022-10-05'))

    cerebro.adddata(data)
    startValue = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % startValue)

    cerebro.run()

    endValue = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % endValue)

    cerebro.plot()

if __name__ == "__main__":
    backtest()
