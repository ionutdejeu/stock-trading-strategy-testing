import datetime
import backtrader as bt
class CustomIndicator(bt.Indicator):
    lines = ('overunder',)
    def __init__(self):
        sma1 = bt.ind.SMA(period=30)
        sma2 = bt.ind.SMA(period=100)
        sma3 = bt.ind.SMA(period=200)

        self.l.overunder = bt.cmp(sma1,sma2) + bt.cmp(sma1,sma3)

class SmaCross(bt.SignalStrategy):
    def __init__(self):
        sma1,sma2 = bt.indicators.SMA(period=10), bt.indicators.SMA(period=30)
        crossover = bt.indicators.CrossOver(sma1,sma2)
        self.signal_add(bt.SIGNAL_LONG,crossover)


class CustomSmaCross(bt.SignalStrategy):
    def __init__(self):
        myIndicator = CustomIndicator()
        self.signal_add(bt.SIGNAL_LONG,myIndicator)
