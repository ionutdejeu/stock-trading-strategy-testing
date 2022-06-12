import datetime

import pandas
import yfinance as yf
import pandas as pd

if __name__ == '__main__':

    stock_list = ['TSLA']
    print('stock_list:', stock_list)
    data = yf.download(stock_list, '2020-01-01', '2022-05-23')
    data.to_csv("TSLA.csv")
