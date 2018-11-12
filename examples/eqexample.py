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
start   = platform.validstart                               # initialize start date
end     = platform.validend                                 # initialize start date
mask = (platform.quote['USDHKD'].index > start) & (platform.quote['USDHKD'].index <= end)
backtestperiod = platform.quote['USDHKD'].loc[mask]
platform.initportfolio(10000000, 100)                       # reset initial cash + default handling fee
#%% Backtesting
prev = None
openrate    = {}
highrate    = {}
lowrate     = {}

openrate['0005.HK']     = None
openrate['0700.HK']     = None
highrate['0005.HK']     = None
highrate['0700.HK']     = None
lowrate['0005.HK']      = None
lowrate['0700.HK']      = None
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
        # initialize Rates
        if not openrate['0005.HK']:
            openrate['0005.HK'] = platform.quote['0005.HK'].loc[time].Close
        if not openrate['0700.HK']:
            openrate['0700.HK'] = platform.quote['0700.HK'].loc[time].Close
        if not highrate['0005.HK'] or platform.quote['0005.HK'].loc[time].Close > highrate['0005.HK']:
            highrate['0005.HK'] = platform.quote['0005.HK'].loc[time].Close
        if not highrate['0700.HK'] or platform.quote['0700.HK'].loc[time].Close > highrate['0700.HK']:
            highrate['0700.HK'] = platform.quote['0700.HK'].loc[time].Close
        if not lowrate['0005.HK'] or platform.quote['0005.HK'].loc[time].Close < lowrate['0005.HK']:
            lowrate['0005.HK']  = platform.quote['0005.HK'].loc[time].Close
        if not lowrate['0700.HK'] or platform.quote['0700.HK'].loc[time].Close < lowrate['0700.HK']:
            lowrate['0700.HK']  = platform.quote['0700.HK'].loc[time].Close
            
        # Long EQ conditions
        if (    platform.quote['0005.HK'].loc[time].Close < (openrate['0005.HK'] + 0.01 * openrate['0005.HK']) # Drop 1%
             or platform.quote['0700.HK'].loc[time].Close < (openrate['0700.HK'] + 0.01 * openrate['0700.HK']) # Drop 1%
             or platform.quote['VHSI'].loc[time].Close - platform.quote['VHSI'].loc[prev].Close >= 1 
             or platform.quote['VIX'].loc[time].Close - platform.quote['VIX'].loc[prev].Close >= 1
             ):
            if not platform.has_pos('HSI'):                     # Check if no position exists
                platform.trade(time, 'HSI',  'SHORT', 100)
                option_maturity     = time.month
                option_strike       = (int(platform.quote['HSI'].loc[time].Close / 200) - 2) * 200      # option step: 200
                platform.trade(time, 'CALL', 'LONG',  20, option_strike, option_maturity)               # Hedging Falling Trend
                platform.trade(time, 'PUT', 'SHORT',  20, option_strike, option_maturity)               # Hedging Falling Trend
                
        # Close EQ conditions
        if (
                platform.quote['VHSI'].loc[prev].Close - platform.quote['VHSI'].loc[time].Close >= 1 
             or platform.quote['VIX'].loc[prev].Close - platform.quote['VIX'].loc[time].Close >= 1
             ):
            if platform.has_pos('HSI'):                         # Check if position exists
                platform.trade(time, 'HSI',  'CLOSE')
                platform.trade(time, 'CALL', 'CLOSE')
                platform.trade(time, 'PUT', 'CLOSE')
    else:
        # Reset rates to None for next day
        openrate['0005.HK']     = None
        openrate['0700.HK']     = None
        highrate['0005.HK']     = None
        highrate['0700.HK']     = None
        lowrate['0005.HK']      = None
        lowrate['0700.HK']      = None
                
    # Check if FX and Crypto markets are opened             
    if platform.is_fxmktopen(time):  
        pass
                
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