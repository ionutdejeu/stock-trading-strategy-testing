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
    params = (
        ('stake', 100),
        ('stoploss', 0.001),
        ('profit_mult', 2),
        ('prdata', True),
        ('prtrade', True),
        ('prorder', True),
    )
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.sizer.setsizing(self.params.stake)
        # Keep a reference to the "close" line in the data[0] dataseries
        self.chandelier_exit = ChandelierIndicatorDev()
        self.zlma = bt.ind.ZeroLagIndicator(self.chandelier_exit.dataclose1, period=50,plot=True,subplot=False)

        self.trades = 0
        self.order = None
        self.order_dict = {}

    def start(self):
        self.trades = 0

    def notify_order(self, order):
        # import ipdb; ipdb.set_trace()
        if order.status in [order.Margin, order.Rejected]:
            pass
        elif order.status == order.Cancelled:
            if self.p.prorder:
                print(','.join(map(str, [
                    'CANCELL', order.info['OCO'], order.ref,
                    self.data.num2date(order.executed.dt).date().isoformat(),
                    order.executed.price,
                    order.executed.size,
                    order.executed.comm,
                ]
                )))
        elif order.status == order.Completed:
            if 'name' in order.info:
                self.broker.cancel(self.order_dict[order.ref])
                self.order = None
                if self.p.prorder:
                    print("%s: %s %s %.2f %.2f %.2f" %
                        (order.info['name'], order.ref,
                        self.data.num2date(order.executed.dt).date().isoformat(),
                        order.executed.price,
                        order.executed.size,
                        order.executed.comm))
            else:
                if order.isbuy():
                    stop_loss = order.executed.price*(1.0 - (self.p.stoploss))
                    take_profit = order.executed.price*(1.0 + self.p.profit_mult*(self.p.stoploss))

                    sl_ord = self.sell(exectype=bt.Order.Stop,
                                       price=stop_loss)
                    sl_ord.addinfo(name="Stop")

                    tkp_ord = self.sell(exectype=bt.Order.Limit,
                                        price=take_profit)
                    tkp_ord.addinfo(name="Prof")

                    self.order_dict[sl_ord.ref] = tkp_ord
                    self.order_dict[tkp_ord.ref] = sl_ord

                    if self.p.prorder:
                        print("SignalPrice: %.2f Buy: %.2f, Stop: %.2f, Prof: %.2f"
                              % (self.last_sig_price,
                                 order.executed.price,
                                 stop_loss,
                                 take_profit))

                elif order.issell():
                    stop_loss = order.executed.price*(1.0 + (self.p.stoploss))
                    take_profit = order.executed.price*(1.0 - 3*(self.p.stoploss))

                    sl_ord = self.buy(exectype=bt.Order.Stop,
                                      price=stop_loss)
                    sl_ord.addinfo(name="Stop")

                    tkp_ord = self.buy(exectype=bt.Order.Limit,
                                        price=take_profit)
                    tkp_ord.addinfo(name="Prof")

                    self.order_dict[sl_ord.ref] = tkp_ord
                    self.order_dict[tkp_ord.ref] = sl_ord

                if self.p.prorder:
                    print("Open: %s %s %.2f %.2f %.2f" %
                        (order.ref,
                         self.data.num2date(order.executed.dt).date().isoformat(),
                        order.executed.price,
                        order.executed.size,
                        order.executed.comm))

    def next(self):
        price_above_zlma = self.chandelier_exit.dataclose1[0] > self.zlma
        price_below_zlma = self.chandelier_exit.dataclose1[0] < self.zlma
        buy_signal = self.chandelier_exit.lines.signal[0] == 1

        sell_signal= self.chandelier_exit.lines.signal[0] > 1
        shouldBuy = buy_signal and price_above_zlma
        shouldSell = sell_signal and price_below_zlma

        #if buy_signal and price_above_zlma:
        #    print("buy")
        #    self.buy()
        print((shouldBuy,shouldSell,self.position))

        if shouldBuy and not self.position:
            self.buy(exectype=bt.Order.Market)
            self.last_sig_price = self.data.close[0]
            self.trades += 1

        elif shouldSell and self.position:
            self.sell(exextype=bt.Order.Market)
            self.trades += 1
            self.position = None

            if self.p.prdata:
                print(','.join(str(x) for x in
                ['DATA', 'OPEN',
                    self.data.datetime.date().isoformat(),
                    self.data.close[0],
                    self.buy_sig[0]]))

    def notify_trade(self, trade):
        # import ipdb; ipdb.set_trace()
        if self.p.prtrade:
            if trade.isclosed:
                print('TRADE PROFIT, GROSS %.2f, NET %.2f' %
                    (trade.pnl, trade.pnlcomm))
            elif trade.justopened:
                        print(','.join(map(str, [
                            'TRADE', 'OPEN',
                            self.data.num2date(trade.dtopen).date().isoformat(),
                            trade.value,
                            trade.pnl,
                            trade.commission,
                        ]
                        )))

    def stop(self):
        print('(Stop Loss Pct: %2f, S/P Multiplier: %2f) Ending Value %.2f (Num Trades: %d)' %
                 (self.params.stoploss, self.params.profit_mult, self.broker.getvalue(), self.trades))

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
