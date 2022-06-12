import backtrader as bt
import pandas
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



#Download the Data and Convert to CSV format in Pandas Dataframe
if __name__ == '__main__':


    # Create the Datafeed from the CSV data

    # Declare position of each column in csv file

    frame = pd.read_csv("../TSLA.csv",)
    heikenAshi_close = [0] * len(frame)
    heikenAshi_open = [0] * len(frame)
    heikenAshi_high = [0] * len(frame)
    heikenAshi_low = [0] * len(frame)

    for index in range(len(frame)):
        heikenAshi_close[index] = 0.25*(frame['Open'].loc[index]+
                                frame['Close'].loc[index]+
                                frame['High'].loc[index]+
                                frame['Low'].loc[index])

        heikenAshi_open[index] = 0.5 * (frame['Open'].loc[max(index-1,0)] +
                                  frame['Close'].loc[max(index-1,0)])
        heikenAshi_high[index] = max(frame['High'].loc[index],frame['Open'].loc[index],frame['Close'].loc[index])
        heikenAshi_low[index] = max(frame['Low'].loc[index], frame['Open'].loc[index], frame['Close'].loc[index])

    frame['HEClose'],frame['HEOpen'],frame['HEHigh'],frame['HELow'] = [
        heikenAshi_close,heikenAshi_open,heikenAshi_high,heikenAshi_low]
    print(frame)
