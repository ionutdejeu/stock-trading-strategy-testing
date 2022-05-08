import pandas
import yfinance as yf
import pandas as pd

if __name__ == '__main__':

    stock_list = ['INFY']
    print('stock_list:', stock_list)
    data = yf.download(stock_list, start="2015-01-01", end="2020-02-21")
    print('data fields downloaded:', set(data.columns.get_level_values(0)))
    #tickerlist = [yf.Ticker.url for url in stock_list]
    for url in stock_list:
        tickerTag = yf.Ticker(url)
        tickerTag.actions.to_csv("{}.csv".format(url))