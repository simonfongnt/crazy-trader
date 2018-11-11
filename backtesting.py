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
from functions import *
dataset = {}
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
#%% Backtesting
start   = '2018-09-01 00:00:00'                             # initialize start date
end     = '2018-10-31 23:59:59'                             # initialize start date
mask = (platform.quote['USDHKD'].index > start) & (platform.quote['USDHKD'].index <= end)
backtestperiod = platform.quote['USDHKD'].loc[mask]
platform.initportfolio(10000000, 100)                       # 
# start looping every 1 minute
prev = None
for time, reference in backtestperiod.iterrows():
    """ 
    Read-Only Params:
    quote['HSI'].loc[time].Close
    quote['HSI'].loc[time].Volume
    quote['VIX'].loc[time].Close
    quote['VHSI'].loc[time].Close
    quote['XAUHKD'].loc[time].Bid
    quote['XAUHKD'].loc[time].Ask
    quote['USDTRY'].loc[time].Bid
    quote['USDTRY'].loc[time].Ask
    quote['XRPUSD'].loc[time].Bid
    quote['XRPUSD'].loc[time].Ask
    
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
        # Long EQ conditions
        if platform.quote['VHSI'].loc[time].Close - platform.quote['VHSI'].loc[prev].Close >= 1 or platform.quote['VIX'].loc[time].Close - platform.quote['VIX'].loc[prev].Close >= 1:
            if not platform.has_pos('HSI'):                     # Check if no position exists
                platform.trade(time, 'HSI',  'SHORT', 100)
                option_strike      = (int(platform.quote['HSI'].loc[time].Close / 200) - 2) * 200
                platform.trade(time, 'CALL', 'LONG',  20, option_strike, time.month)
        # Close EQ conditions
        if platform.quote['VHSI'].loc[prev].Close - platform.quote['VHSI'].loc[time].Close >= 1 or platform.quote['VIX'].loc[prev].Close - platform.quote['VIX'].loc[time].Close >= 1:
            if platform.has_pos('HSI'):                         # Check if position exists
                platform.trade(time, 'HSI',  'CLOSE')
                platform.trade(time, 'CALL', 'CLOSE')
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
    
    ### ADD YOUR CODE HERE ###
    
    ### ADD YOUR CODE HERE ###
    
    # Update position info once a day: Unrealized, realized P&L
    if time.timestamp() % 86400 == 0:
        platform.updatepos(time)
 
#%%
# Copy Unrealized P&L to Realized P&L       
portfolio, tradelog = platform.exporttrades()
temp_log = tradelog
for i in range(len(temp_log)): 
    temp_log.loc[i, 'P&L'] = temp_log.loc[i, 'Unrealized P&L'] + temp_log.loc[i, 'Realized P&L']

print (tradelog[['Product', 'Position', 'Open Rate', 'Close Rate', 'P&L']])
print ('Initial:', round(portfolio['initial']), 'Final:', round(portfolio['cash']), 'P&L%:', round(portfolio['P&L'] * 100))