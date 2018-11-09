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
Assumptions:
    Open/Close Rate means Bid/Ask for FX, Close for EQ, and Strike for Options
    Option price based on Interest rate is 0.15% and dividend yield is 4.24%, per year
    no overnight fee incurred
Operations:
    Long with Ask
    Short with Bid
"""
#%% Library
from functions import *
#%% Params
dataset = {}
dataset['HSI']     = 'EQ'       # Close, Volume
dataset['VHSI']    = 'Vol'      # Close
dataset['VIX']     = 'Vol'      # Close
dataset['USDHKD']  = 'FX'       # Bid, Ask
dataset['XAUHKD']  = 'FX'       # Bid, Ask
dataset['HKDTRY']  = 'FX'       # Bid, Ask
dataset['USDTRY']  = 'FX'       # Bid, Ask
dataset['XRPUSD']  = 'FX'       # Bid, Ask
initdataset(dataset)            # initialize Dataset
#%%
position = {}                   # NONE, LONG, SHORT
position['HSI']     = 'NONE'    # Close, Volume
position['VHSI']    = 'NONE'    # Close
position['PUT']     = 'NONE'    # 
position['CALL']    = 'NONE'    # 
position['XAUHKD']  = 'NONE'    # Bid, Ask
position['USDTRY']  = 'NONE'    # Bid, Ask
position['XRPUSD']  = 'NONE'    # Bid, Ask
#%%
initportfolio(10000000, 100)                                # initialize Account Cash, service fee
start   = '2018-09-01 00:00:00'                             # initialize start date
end     = '2018-10-31 23:59:59'                             # initialize start date
mask = (quote['USDHKD'].index > start) & (quote['USDHKD'].index <= end)
backtestperiod = quote['USDHKD'].loc[mask]
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
    
    Trading Methods:
    trade(time, 'XRPUSD', 'LONG',  quote['XRPUSD'].loc[time].Ask, 100000)           # LONG FX Order
    trade(time, 'XRPUSD', 'CLOSE', quote['XRPUSD'].loc[time].Bid, 100000)           # CLOSE FX LONG Order
    trade(time, 'XRPUSD', 'SHORT', quote['XRPUSD'].loc[time].Bid, 100000)           # SHORT FX Order
    trade(time, 'XRPUSD', 'CLOSE', quote['XRPUSD'].loc[time].Ask, 100000)           # CLOSE FX SHORT Order
    trade(time, 'HSI',    'SHORT', quote['HSI'].loc[time].Close,  10)               # LONG EQ Order
    trade(time, 'HSI',    'CLOSE', quote['HSI'].loc[time].Close,  10)               # CLOSE EQ LONG Order
    trade(time, 'CALL',   'SHORT', quote['HSI'].loc[time].Close,  100, 26000, 8)    # SHORT EQ CALL Option
    trade(time, 'CALL',   'CLOSE', quote['HSI'].loc[time].Close,  100)              # CLOSE EQ CALL Option
    """ 
    #Examples: 
    if not prev:
        prev = time        
        continue
    
    if is_eqmktopen(time): 
        if quote['VHSI'].loc[time].Close - quote['VHSI'].loc[prev].Close >= 1 or quote['VIX'].loc[time].Close - quote['VIX'].loc[prev].Close >= 1:
            if position['HSI'] is 'NONE':
                trade(time, 'HSI',  'SHORT', quote['HSI'].loc[time].Close, 10)
                option_strike      = (int(quote['HSI'].loc[time].Close / 200) - 2) * 200
                trade(time, 'CALL', 'LONG',  quote['HSI'].loc[time].Close, 10, option_strike, time.month)
                position['HSI'] = 'SHORT'
#                print ('HSI', 'SHORT')
                                
        if quote['VHSI'].loc[prev].Close - quote['VHSI'].loc[time].Close >= 1 or quote['VIX'].loc[prev].Close - quote['VIX'].loc[time].Close >= 1:
            if position['HSI'] is not 'NONE':
                position['HSI']    = trade(time, 'HSI',  'CLOSE', quote['HSI'].loc[time].Close, 10)
                position['CALL']   = trade(time, 'CALL', 'CLOSE', quote['HSI'].loc[time].Close, 10)
                position['HSI'] = 'NONE'
#                print ('HSI', 'CLOSE')
                
    if is_fxmktopen(time):  
        if quote['VIX'].loc[time].Close - quote['VIX'].loc[prev].Close >= 1:
            if position['XRPUSD'] is 'NONE':
                trade(time, 'XRPUSD', 'SHORT', quote['XRPUSD'].loc[time].Bid, 10)
                position['XRPUSD'] = 'SHORT'
#                print ('XRPUSD', 'SHORT')
        
        if quote['VIX'].loc[prev].Close - quote['VIX'].loc[time].Close >= 1:
            if position['XRPUSD'] is not 'NONE':
                trade(time, 'XRPUSD', 'CLOSE', quote['XRPUSD'].loc[time].Ask, 10)
                position['XRPUSD'] = 'NONE'
#                print ('XRPUSD', 'CLOSE')
    prev = time        
    
    ### ADD YOUR CODE HERE ###
    
    ### ADD YOUR CODE HERE ###
    
    # Update position info once a day: Unrealized, realized P&L
    if time.timestamp() % 86400 == 0:
        updatepos(time)
#%% Export Portfolio
portfolio, log = exporttrades()
print (log)
print (portfolio)