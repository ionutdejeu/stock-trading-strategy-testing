import datetime
import os.path
import sys
import pandas as pd
import backtrader as bt
import yfinance as yf

class IndicatorDirection:
    Bullish=1
    Bearish=-1

class ChandelierIndicatorDev(bt.Indicator):
    alias = ('CE', 'ChandelierExit',)
    lines = ('long', 'short')
    params = (('stake', 100), ('period', 1), ('multip', 2),("useClose",False))
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose1 = self.datas[0].close
        self.highest = bt.ind.Highest(self.datas[0].close, period=self.params.period)
        self.lowest = bt.ind.Lowest(self.datas[0].close, period=self.params.period)

        self.atr = bt.ind.ATR(self.datas[0], period=self.params.period, plot=False)

    def next(self):
        self.lines.short[0] =1
        self.lines.long[0] = 1


class ChandelierStrategyDev(bt.Strategy):
    alias = ('CE', 'ChandelierExit',)
    lines = ('long', 'short')
    params = (('stake', 100), ('period', 1), ('multip', 2),("useClose",False))
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose1 = self.datas[0].close
        self.highest = bt.ind.Highest(self.datas[0].close, period=self.params.period)
        self.lowest = bt.ind.Lowest(self.datas[0].close, period=self.params.period)

        self.atr = bt.ind.ATR(self.datas[0], period=self.params.period, plot=False)
        #self.highest_close = bt.ind.Highest(self.datas[0].close)
        #self.long_stop = (self.params.useClose?)

    def next(self):
        longStopSignalValue,shortStopSignalValue = (0,0)

        if self.datas[-1].close > self.highest[-1]:
            longStopSignalValue = max(self.datas[-1].close,self.highest[-1])
        else:
            longStopSignalValue = self.highest[0]

        if self.datas[-1].close < self.highest[-1]:
            shortStopSignalValue = min(self.datas[-1].close, self.lowest[-1])
        else:
            shortStopSignalValue = self.highest[0]

        print((shortStopSignalValue,longStopSignalValue))

        currentDirection = 1
        if self.datas[0].close > shortStopSignalValue:
            self.direction = IndicatorDirection.Bullish
        if self.datas[0].close < longStopSignalValue:
            self.direction = IndicatorDirection.Bearish
        else:
            currentDirection = self.direction


# Create a Stratey
class BuySellChandelierStrategy(bt.Strategy):
    alias = ('CE', 'ChandelierExit',)
    lines = ('long', 'short')
    params = (('stake', 100), ('period', 1), ('multip', 2),)
    plotinfo = dict(subplot=True)


    def __ini2t__(self):
        self.sizer.setsizing(self.params.stake)

        self.heikenAshi = bt.indicators.HeikinAshi(plot=False)

        self.dataclose1 = self.heikenAshi.close

        #self.high = self.heikenAshi.high

        # Keep a reference to the "close" line in the data[0] dataseries
        self.highest = bt.ind.Highest(self.heikenAshi, period=self.params.period)
        self.atr = bt.ind.ATR(self.highest, period=self.params.period, plot=False)

        self.chan_exit_l = self.heikenAshi - self.params.multip * self.atr

    def __init__(self):
        self.sizer.setsizing(self.params.stake)

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose1 = self.datas[0].close
        self.high = self.datas[0].high
        self.chan_exit_l = bt.ind.Highest(self.high, period=self.params.period,subplot=False) - self.params.multip * bt.ind.ATR(period=self.params.period)
        self.zlsma = bt.indicators.ZeroLagIndicator(period=self.params.period, plot=True,subplot=False)


    def next(self):

        print( self.zlsma[0],self.zlsma[-1])
        if self.dataclose1[0] < self.chan_exit_l[0] and \
                self.dataclose1[-1] >= self.chan_exit_l[-1] and \
                self.zlsma[0] >= self.chan_exit_l[0]:
            self.buy()

        #if self.dataclose1[0] < self.chan_exit_l[0] and self.dataclose1[-1] >= self.chan_exit_l[-1] and \
        #        self.zlsma[0] < self.dataclose1[0]:
        #    print('buy')
        #    self.buy()

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.myind = bt.indicators.ZeroLagIndicator(period=2, plot=True)

    def next(self):
        print(self.myind)

def backtest():
    # Back test the BuyChandelierStrategy with BackTrader
    cerebro = bt.Cerebro()

    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.0035)
    cerebro.addstrategy(ChandelierStrategyDev)
    yf_data = yf.download('TSLA', '2022-01-01', '2022-05-23')
    data = bt.feeds.PandasData(dataname=yf_data)

    cerebro.adddata(data)
    startValue = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % startValue)

    cerebro.run()

    endValue = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % endValue)

    cerebro.plot(style="candle")


if __name__ == "__main__":
    backtest()
