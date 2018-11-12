# -*- coding: utf-8 -*-
"""
@author: Crazy Trader
Trading Hours (HKT Timezone) Mon - Fri: 
    HSI Derivatives(Day Session)    : 09:15 - 12:00, 13:00 - 16:30
                   (Night Session)  : 17:15 - 01:00
    HK Equities    (Auction Session): 09:00 - 09:30
                   (Day Session)    : 09:30 - 12:00, 13:00 - 16:08
    US Equities                     : 22:30 - 05:00
    Forex                           : 00:00 - 23:59
Restrictions:
    Trading must be in trading hours
    Trading must be in sufficnet cash
    Option Strike Price is in step of 200
    Backtest would be stopped with restriction
Assumptions:
    Open/Close Rate means Bid/Ask for FX, Close for EQ, and Strike for Options
    Option price based on Interest rate is 0.15% and dividend yield is 4.24%, per year
    no overnight fee incurred
Operations:
    Long with Ask Price
    Short with Bid Price
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
    """ 
    Read-Only Params:
    platform.quote['HSI'].loc[time].Close
    platform.quote['HSI'].loc[time].Volume
    platform.quote['VIX'].loc[time].Close
    platform.quote['VHSI'].loc[time].Close
    platform.quote['XAUHKD'].loc[time].Bid
    platform.quote['XAUHKD'].loc[time].Ask
    platform.quote['USDTRY'].loc[time].Bid
    platform.quote['USDTRY'].loc[time].Ask
    platform.quote['XRPUSD'].loc[time].Bid
    platform.quote['XRPUSD'].loc[time].Ask
    
    Paper Trade Methods:
    trade(time, 'XRPUSD', 'LONG',  100000)          # LONG FX Order
    trade(time, 'XRPUSD', 'CLOSE')                  # CLOSE FX LONG Order
    trade(time, 'XRPUSD', 'SHORT', 100000)          # SHORT FX Order
    trade(time, 'XRPUSD', 'CLOSE')                  # CLOSE FX SHORT Order
    trade(time, 'HSI',    'SHORT', 10)              # LONG EQ Order
    trade(time, 'HSI',    'CLOSE')                  # CLOSE EQ LONG Order
    trade(time, 'CALL',   'SHORT', 100, 26000, 8)   # SHORT EQ CALL Option
    trade(time, 'CALL',   'CLOSE')                  # CLOSE EQ CALL Option
    
    Other Methods:
    platform.portfolio['cash']                      # Available Cash
    platform.has_pos('HSI')                         # Check if trading log already ahs HSI positio
    """ 
    #Examples: 
    if not prev:                                    # skip first loop to record the time
        prev = time
        print (time, 'Avl.Cash:', platform.portfolio['cash'])
        continue
    # Check if EQ market is opened
    if platform.is_eqmktopen(time): 
        ### ADD YOUR CODE HERE ###
        
        ### ADD YOUR CODE HERE ###
                
    # Check if FX and Crypto markets are opened             
    if platform.is_fxmktopen(time):  
        ### ADD YOUR CODE HERE ###
        
        ### ADD YOUR CODE HERE ###
                
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