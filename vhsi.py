# -*- coding: utf-8 -*-
"""
@author: Crazy Trader
Description:
    This demo shows the simple EQ Short Trading with open price, high price and low price repeatedly captured during the trading hour

    Open HSI Short Position with Qty 100, Long Call with Qty 20 and Short Put with Qty 20 if either one of the conditions is matched:
        - 0005.HK drops 1% from the open price
        - 0700.HK drops 1% from the open price
        - VHSI increases by 1 point
        - VIX increases by 1 point

    The algorithm restricts only one position per product.

    Close all Positions if either one of the condtions is matched:
        - VHSI decreases by 1 point
        - VIX decreases by 1 point
"""
# %% Library & Initialize Dataset and Backtesting Platform
from library.functions import *

dataset = {}
#dataset['0005.HK'] = 'EQ'  # Close, Volume
#dataset['0700.HK'] = 'EQ'  # Close, Volume
#dataset['HSI'] = 'EQ'  # Close, Volume
#dataset['PUT'] = 'Custom'  # requires functions
#dataset['CALL'] = 'Custom'  # requires functions
dataset['VHSI'] = 'Vol'  # Close
#dataset['VIX'] = 'Vol'  # Close
dataset['USDHKD'] = 'FX'  # Bid, Ask
#dataset['XAUHKD'] = 'FX'  # Bid, Ask
#dataset['HKDTRY'] = 'FX'  # Bid, Ask
#dataset['USDTRY'] = 'FX'  # Bid, Ask
#dataset['XRPUSD'] = 'FX'  # Bid, Ask
# load dataset and setup initial cash + default handling fee
platform = backtest(10000000, 100, dataset)
# %% Functions
def getvpt(prev_vpt, volume, prev_close, this_close):
    this_vpt = prev_vpt + volume * (this_close - prev_close) / prev_close
    return this_vpt
# %% Backtest Params
start = platform.validstart  # initialize start date
end = platform.validend  # initialize start date
start = datetime.datetime(2018, 9, 1, 0, 0, 0)  # initialize start date
end = datetime.datetime(2018, 12, 1, 0, 0, 0)  # initialize start date
mask = (platform.quote['USDHKD'].index > start) & (platform.quote['USDHKD'].index <= end)
backtestperiod = platform.quote['USDHKD'].loc[mask]
platform.initportfolio(10000000, 100)  # reset initial cash + default handling fee
# %% Backtesting
prev = None  # for accessing last minute quotation
# start looping every 1 minute
print('Start Backtesting...')
for time, reference in backtestperiod.iterrows():
    # Examples:
    if not prev:  # skip first loop to record the time
        # HSI derivatives
        prev = time
        continue

    # Check if EQ market is opened
    if platform.is_eqmktopen(time):

        # Trade conditions
        if (    # One trade per day at 16:10
                time.time() == datetime.time(16, 10, 0)  
        ):
            # Close Existing Position
            # High Volatility
            if platform.quote['VHSI'].loc[time].Close > 16:
                if platform.has_pos('VHSI') is not 'SHORT':                    
                    if platform.has_pos('VHSI'):
                        platform.trade(time, 'VHSI', 'CLOSE')  
                    platform.trade(time, 'VHSI', 'SHORT', 5000)
            # Low Volatility
            elif platform.quote['VHSI'].loc[time].Close < 16:  
                if platform.has_pos('VHSI') is not 'LONG':                      
                    if platform.has_pos('VHSI'):
                        platform.trade(time, 'VHSI', 'CLOSE')  
                    platform.trade(time, 'VHSI', 'LONG', 5000)
                
    # EQ is not in trading hours
    else:
        pass                                             

    prev = time  # Save this time for next loop

    # Update position info once a day: Unrealized, realized P&L
    if time.timestamp() % 86400 == 0:
        platform.updatepos(time)

# %% Export Portfolio
tradelog = None
portfolio, tradelog = platform.exporttrades()
for i in range(len(tradelog)):
    tradelog.loc[i, 'P&L'] = tradelog.loc[i, 'Unrealized P&L'] + tradelog.loc[i, 'Realized P&L']
print('Activities:')
print(tradelog[['Product', 'Position', 'Open Rate', 'Close Rate', 'P&L']])
print('Summary:')
print('Initial Cash:', round(portfolio['initial']), 'Final Cash:', round(portfolio['cash']))
print('Unrealized P&L:', round(portfolio['Unrealized P&L']), 'Realized P&L:', round(portfolio['Realized P&L']))
print('Overall P&L:', round(portfolio['P&L']), 'P&L%:', portfolio['P&L%'])

# %% insert
tradelog.to_excel('df1.xlsx')


