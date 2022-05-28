import datetime
import os.path
import sys
import pandas as pd
import backtrader as bt
import yfinance as yf


class IndicatorDirection:
    Bullish = 1
    Bearish = -1


class ChandelierIndicatorDev(bt.Indicator):
    alias = ('CE', 'ChandelierExit',)
    lines = ('long', 'short', 'signal')
    params = (('stake', 100), ('period', 1), ('multip', 2), ("useClose", False))
    plotinfo = dict(subplot=True)

    def __init__(self):

        # Keep a reference to the "close" line in the data[0] dataseries
        self.heikenAshi = bt.indicators.HeikinAshi(self.datas[0])
        self.dataclose1 = self.heikenAshi.close
        self.highest = bt.ind.Highest(self.dataclose1, period=self.params.period)
        self.lowest = bt.ind.Lowest(self.dataclose1, period=self.params.period)

        self.atr = bt.ind.ATR(self.datas[0], period=self.params.period, plot=False)
        self.cmp_short = bt.cmp(self.dataclose1, self.lowest(-1))
        self.cmp_long = bt.cmp(self.dataclose1, self.highest(-1))
        self.signal_buy = bt.If(self.cmp_long(-1) < self.cmp_long(0), 0, 1)
        self.signal_sell = bt.If(self.cmp_long(-1) < self.cmp_long(0), 0, 1)

    def next(self):

        self.lines.signal[0] = 0
        if self.cmp_short[0] == -1 and self.cmp_short[-1] == 1:
            self.signal_sell[0] = 1
            self.lines.signal[0] = -1
        else:
            self.signal_sell[0] = 0

        if self.cmp_short[0] == 1 and self.cmp_short[-1] == -1:
            self.signal_buy[0] = 1
            self.lines.signal[0] = 1

        else:
            self.signal_buy[0] = 0



class ChandelierStrategyDev(bt.Strategy):
    params = (('stake', 100),)
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.chandelier_exit = ChandelierIndicatorDev()
        self.zlma = bt.ind.ZeroLagIndicator(self.chandelier_exit.dataclose1, period=50)

    def next(self):
        price_above_zlma = self.chandelier_exit.dataclose1[0] > self.zlma
        price_below_zlma = self.chandelier_exit.dataclose1[0] < self.zlma
        buy_signal = self.chandelier_exit.lines.signal[0] == 1
        print((price_above_zlma, buy_signal))

        sell_signal= self.chandelier_exit.lines.signal[0] > 1
        if buy_signal and price_above_zlma:
            print("buy")
            self.buy()


def backtest():
    # Back test the BuyChandelierStrategy with BackTrader
    cerebro = bt.Cerebro()

    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.0035)
    cerebro.addstrategy(ChandelierStrategyDev)
    yf_data = yf.download('TSLA', '2020-01-01', '2022-05-23')
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
