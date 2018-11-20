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
#%% Functions
def getvpt(prev_vpt, volume, prev_close, this_close):
    this_vpt = prev_vpt + volume * (this_close - prev_close ) / prev_close
    return this_vpt
#%% Backtest Params
start   = platform.validstart                                   # initialize start date
end     = platform.validend                                     # initialize start date
mask = (platform.quote['USDHKD'].index > start) & (platform.quote['USDHKD'].index <= end)
backtestperiod = platform.quote['USDHKD'].loc[mask]
platform.initportfolio(10000000, 100)                           # reset initial cash + default handling fee
#%% Backtesting
prev            = None                                          # for accessing last minute quotation
# start looping every 1 minute
print ('Start Backtesting...')
for time, reference in backtestperiod.iterrows():
    #Examples: 
    if not prev:                                                # skip first loop to record the time
        # initialize params
        prev = time
        prev_vpt        = 0                                     # last volume-price trend
        this_vpt        = 0                                     # this volume-price trend
        this_vpt_volume = 0                                     # this volume
        prev_vpt_price  = platform.quote['HSI'].loc[time].Close # last VPT price
        this_vpt_price  = platform.quote['HSI'].loc[time].Close # this VPT price
        print (time, 'Avl.Cash:', platform.portfolio['cash'])
        continue
    
    # Check if EQ market is opened
    if platform.is_eqmktopen(time):
        
        # Volume-Price Trend: accumulating volume until VPT calcuation
        this_vpt_volume = this_vpt_volume + platform.quote['HSI'].loc[time].Volume
            
        # Trade conditions
        if (    
                time.time() == datetime.time(10, 0, 0)                                              # One trade per day at 10:00
             ):
            
            # Calculation VPT once per day
            this_vpt_price = platform.quote['HSI'].loc[time].Close                                  # Save the VPT price for VPT calculation
            this_vpt = getvpt(prev_vpt, this_vpt_volume, prev_vpt_price, this_vpt_price)            # Calculate VPT
            
            if (    
                    not platform.has_pos('HSI')                                                     # no position exists
                and this_vpt < prev_vpt                                                             # Trned is downward
                and platform.quote['VHSI'].loc[time].Close < 20                                     # Volatility is low (e.g. 20 is arbitary value)
                ):
                
                platform.trade(time, 'HSI',  'SHORT', 100)                                          # Short 100 Qty of HSI Future
                option_maturity     = time.month                                                    # option maturity
                option_strike       = (int(platform.quote['HSI'].loc[time].Close / 200) - 2) * 200  # option step: 200 - around 400 points from the underlying price    
                platform.trade(time, 'CALL', 'LONG',  20, option_strike, option_maturity)           # Hedging Falling Trend 
#                platform.trade(time, 'PUT', 'SHORT',  20, option_strike, option_maturity)           # Hedging Falling Trend        
                
            # VPT preparation
            this_vpt_volume = 0                                                                     # reset VPT volume for next day accumulation
            prev_vpt_price  = this_vpt_price                                                        # Save today's vpt price for next day
            prev_vpt        = this_vpt                                                              # Save today's vpt for next day
                
        # Close conditions 
        if (
                time.time() == datetime.time(16, 10, 0)                                             # Close everything at 16:10
             ):
            if platform.has_pos('HSI'):                                                             # Check if position exists
                platform.trade(time, 'HSI',  'CLOSE')                                               # Close HSI Future
                platform.trade(time, 'CALL', 'CLOSE')                                               # Close HSI Call Option
#                platform.trade(time, 'PUT', 'CLOSE')                                                # Close HSI Put Option
    # EQ is not in trading hours
    else:
        pass
    
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