import backtrader as bt
from backtrader.feeds import GenericCSVData
from nsepy import get_history
from datetime import date
import pandas as pd

#Create Buy and Sell Signal Observers

class BuySellSignal(bt.observers.BuySell):
    plotlines = dict(
        buy=dict(marker='$\u21E7$', markersize=12.0),
        sell=dict(marker='$\u21E9$', markersize=12.0)
    )


# Create a Trading Strategy

class SmaCross(bt.Strategy):
    alias = ('SMA_CrossOver',)

    # list of parameters which are configurable for the strategy
    params = dict(
        pfast=10,  # period for the fast moving average
        pslow=30  # period for the slow moving average
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # fast moving average
        sma2 = bt.ind.SMA(period=self.p.pslow)  # slow moving average
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # crossover signal
        self.log(f'Initial portfolio value of {self.broker.get_value():.2f}\n')

    def next(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                self.buy()  # enter long
                self.log(f'BUY {self.getsizing()} shares of {self.data._name} at {self.data.close[0]}')

        elif self.crossover < 0:  # in the market & cross to the downside
            self.sell()  # exit long
            self.log(f'CLOSE LONG position of {self.position.size} shares '
                     f'of {self.data._name} at {self.data.close[0]:.2f}')


#Download the Data and Convert to CSV format in Pandas Dataframe
if __name__ == '__main__':

    try:
        data = pd.read_csv('INFY.csv')
    except:
        data = get_history(symbol="INFY", start=date(2020,1,1), end=date(2021,2,16))
        data.to_csv('INFY.csv')
    # Create the Datafeed from the CSV data

    # Declare position of each column in csv file

    btdata = GenericCSVData(dataname='INFY.csv',
                            dtformat=('%Y-%m-%d'),
                            datetime=0,
                            high=5,
                            low=6,
                            open=4,
                            close=8,
                            volume=10,
                            openinterest=-1,
                            # fromdate=date(2021, 2, 16),
                            # todate=date(2021, 2, 16)
                            )

    # Create cerebro Engine
    cerebro = bt.Cerebro()

    # Set Fixed Position Sizing
    cerebro.addsizer(bt.sizers.SizerFix, stake=20)

    # Add datafeed to Cerebro Engine
    cerebro.adddata(btdata)

    # Set Initial Trading Capital and Trading Commissions
    cerebro.broker.setcash(300000.0)
    cerebro.broker.setcommission(commission=0.002)

    # Add Trading Strategy to Cerebro
    cerebro.addstrategy(SmaCross)

    # Add Buy Sell Signals Observer to Cerebro
    cerebro.addobserver(bt.observers.Value)

    # Add Trading Statistics Analyzer
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')

    bt.observers.BuySell = BuySellSignal

    # Run Cerebro Engine

    start_portfolio_value = cerebro.broker.getvalue()

    cerebro.run()

    # Plot the Line Chart with Buy or Sell Signals
    cerebro.plot()

    end_portfolio_value = cerebro.broker.getvalue()
    pnl = end_portfolio_value - start_portfolio_value