import backtrader as bt
import yfinance as yf

if __name__ == '__main__':
    # Back test the BuyChandelierStrategy with BackTrader
    cerebro = bt.Cerebro()

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.0035)
    #cerebro.addindicator(ChandelierExitIndicator)
    #cerebro.addstrategy(ChandelierExitStrategy2)
    data = bt.feeds.PandasData(dataname=yf.download('AAPL', '2021-01-01', '2022-10-05'))

    cerebro.adddata(data)

    startValue = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % startValue)

    cerebro.run()

    endValue = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % endValue)

    cerebro.plot()