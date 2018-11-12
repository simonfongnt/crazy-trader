# -*- coding: utf-8 -*-
"""
@author: Crazy Trader

Description:
    This demo shows the simple FX Short Trading during the trading hour
    
    Open USDTRY Short Position with Qty 5000000 on Sep and Close it on Oct
    
    Open XRPUSD Short Position with Qty 100 if VIX increases by 1 point, and Close it if VIX decreases by 1 point
    
    The algorithm restricts only one position per product.
"""
#%% Library & Initialize Dataset and Backtesting Platform
from library.functions import *
dataset = {}
dataset['0005.HK']  = 'EQ'       # Close, Volume
dataset['0700.HK']  = 'EQ'       # Close, Volume
dataset['HSI']      = 'EQ'       # Close, Volume
dataset['PUT']      = 'Custom'   # requires functions
dataset['CALL']     = 'Custom'   # requires functions
dataset['VHSI']     = 'Vol'      # Close
dataset['VIX']      = 'Vol'      # Close
dataset['USDHKD']   = 'FX'       # Bid, Ask
dataset['XAUHKD']   = 'FX'       # Bid, Ask
dataset['HKDTRY']   = 'FX'       # Bid, Ask
dataset['USDTRY']   = 'FX'       # Bid, Ask
dataset['XRPUSD']   = 'FX'       # Bid, Ask
# load dataset and setup initial cash + default handling fee
platform = backtest(10000000, 100, dataset)
#%% Backtest Params
#start   = '2018-09-01 00:00:00'                             # initialize start date
#end     = '2018-11-07 23:59:59'                             # initialize start date
start   = platform.validstart                               # initialize start date
end     = platform.validend                                 # initialize start date
mask = (platform.quote['USDHKD'].index > start) & (platform.quote['USDHKD'].index <= end)
backtestperiod = platform.quote['USDHKD'].loc[mask]
platform.initportfolio(10000000, 100)                       # reset initial cash + default handling fee
#%% Backtesting
prev = None
# start looping every 1 minute
print ('Start Backtesting...')
for time, reference in backtestperiod.iterrows():
    #Examples: 
    if not prev:                                    # skip first loop to record the time
        prev = time
        print (time, 'Avl.Cash:', platform.portfolio['cash'])
        continue
    
    # Check if EQ market is opened
    if platform.is_eqmktopen(time):
        pass
                
    # Check if FX and Crypto markets are opened             
    if platform.is_fxmktopen(time):  
        # Long Crypto conditions
        if platform.quote['VIX'].loc[time].Close - platform.quote['VIX'].loc[prev].Close >= 1:
            if not platform.has_pos('XRPUSD'):                  # Check if no position exists
                platform.trade(time, 'XRPUSD', 'SHORT', 100)
        # Close Crypto conditions
        if platform.quote['VIX'].loc[prev].Close - platform.quote['VIX'].loc[time].Close >= 1:
            if platform.has_pos('XRPUSD'):                      # Check if position exists
                platform.trade(time, 'XRPUSD', 'CLOSE')
        # Long FX conditions
        if time.month == 9:
            if not platform.has_pos('USDTRY'):                  # Check if no position exists
                platform.trade(time, 'USDTRY', 'SHORT', 5000000)
        # Close FX conditions                      
        if time.month == 10 and time.day == 31:
            if platform.has_pos('USDTRY'):                      # Check if position exists
                platform.trade(time, 'USDTRY', 'CLOSE')
                
    prev = time                                                 # Save this time for next loop
    
    # Update position info once a day: Unrealized, realized P&L
    if time.timestamp() % 86400 == 0:
        platform.updatepos(time)
 
#%% Export Portfolio 
tradelog = None
portfolio, tradelog = platform.exporttrades()
for i in range(len(tradelog)): 
    tradelog.loc[i, 'P&L'] = tradelog.loc[i, 'Unrealized P&L'] + tradelog.loc[i, 'Realized P&L']
print ('Activities:')
print (tradelog[['Product', 'Position', 'Open Rate', 'Close Rate', 'P&L']])
print ('Summary:')
print ('Initial Cash:', round(portfolio['initial']), 'Final Cash:', round(portfolio['cash']))
print ('Unrealized P&L:', round(portfolio['Unrealized P&L']), 'Realized P&L:', round(portfolio['Realized P&L']))
print ('Overall P&L:', round(portfolio['P&L']), 'P&L%:', round(portfolio['P&L%']))