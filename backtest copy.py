import datetime

import backtrader as bt
import pandas as pd
import quantstats

from strategies import *

# Instantiate Cerebro engine
cerebro = bt.Cerebro()

# Set data parameters and add to Cerebro
# First data feed - BTC Price Data
data1 = bt.feeds.YahooFinanceCSVData(
    dataname='TSLA.csv',
    fromdate=datetime.datetime(2018, 1, 1),
    todate=datetime.datetime(2020, 1, 1),
    timeframe=bt.TimeFrame.Weeks,
)
cerebro.adddata(data1)

# Second data feed - BTC Google Trends Data
data2 = bt.feeds.GenericCSVData(
    dataname='BTC_Gtrends.csv',
    fromdate=datetime.datetime(2018, 1, 1),
    todate=datetime.datetime(2020, 1, 1),
    nullvalue=0.0,
    dtformat=('%Y-%m-%d'),
    datetime=0,
    time=-1,
    high=-1,
    low=-1,
    open=-1,
    close=1,
    volume=-1,
    openinterest=-1,
    timeframe=bt.TimeFrame.Weeks,
)
cerebro.adddata(data2)

# Add Strategy
cerebro.addstrategy(BtcSentiment)

# Add commission rate of 0.1% per trade
cerebro.broker.setcommission(commission=0.0025)

# Add analyzers
cerebro.addanalyzer(bt.analyzers.PyFolio, _name='PyFolio')

if __name__ == '__main__':

	start_portfolio_value = cerebro.broker.getvalue()
	results = cerebro.run()
	strat = results[0]
	end_portfolio_value = cerebro.broker.getvalue()
	pnl = end_portfolio_value - start_portfolio_value

	print(f'Starting Portfolio Value: {start_portfolio_value:2f}')
	print(f'Final Portfolio Value: {end_portfolio_value:2f}')
	print(f'PnL: {pnl:.2f}')

	portfolio_stats = strat.analyzers.getbyname('PyFolio')
	returns, positions, transactions, gross_lev = portfolio_stats.get_pf_items()
	returns.index = returns.index.tz_convert(None)

	quantstats.reports.html(returns, output='stats.html', title='BTC Sentiment')