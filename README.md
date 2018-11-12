# Crazy Trader Backtest Platform
 This platform aimed to offer backtesting to verify the trading strategy. Limited minute-based dataset are provided in the this project. This backtest algorithm assumes that trading activities are operated in Hong Kong such that the trading hour is referred in Hong Kong Time Zone as follows:
 Trading Hours (HKT Timezone) Mon - Fri: 
     HSI Derivatives(Day Session)    : 09:15 - 12:00, 13:00 - 16:30
    
                   (Night Session)  : 17:15 - 01:00
                   
    HK Equities    (Auction Session): 09:00 - 09:30
    
                   (Day Session)    : 09:30 - 12:00, 13:00 - 16:08
                   
    US Equities                     : 22:30 - 05:00
    
    Forex                           : 00:00 - 23:59
    
During the backtesting, the algorithm restricts to ensure the following measures are not violated. Backtest would be otherwise be terminated.
 Restrictions:
     Trading must be in trading hours
    
    Trading must be in sufficnet cash
    
    Option Strike Price is in step of 200
    
There are also assumptions on incurred cost and price calculation as well.
    
Assumptions:
    
    Option price based on Interest rate is 0.15% and dividend yield is 4.24%, per year
    
    no overnight fee incurred
    
In order to utilize the algorithm, dataset in excel format should be prepared with label named for code usage. Before loading the dataset, it has to be defined as 
     'EQ' (able to access Close, Volume values) e.g. HSI index, 
     'Vol' (able to access Close value) e.g. VHSI and VIX, 
     'FX' (able to access Bid, Ask values) which covers cryptos, Forex, commidities 
     'Custom' (custom defined params) e.g. HSI options
     e.g. HSI.xls allows to use 'HSI' in functions such as platform.quote['HSI'].loc[time].Close
 Functions (Long with Ask Price, Short with Bid Price):
     Quotation and Volume (EQ):
    
    quote['HSI'].loc[time].Close
    
    quote['HSI'].loc[time].Volume
    
    Quotation (Vol):
    
    quote['VHSI'].loc[time].Close
    
    quote['VIX'].loc[time].Close
    
    Quotation (FX):
    
    quote['XAUHKD'].loc[time].Bid
    
    quote['XAUHKD'].loc[time].Ask
    
    Open Order: trade(time, product, position, quantity, strike(for option), maturity(for option)
    
    trade(time, 'XRPUSD', 'LONG',  100000)          # LONG FX Order
    
    trade(time, 'CALL',   'SHORT', 100, 26000, 8)   # SHORT EQ CALL Option
    
    Close Order: trade(time, product, position)
    
    trade(time, 'HSI',    'CLOSE')                  # CLOSE EQ LONG Order
    
    trade(time, 'CALL',   'CLOSE')                  # CLOSE EQ CALL Option
    
    Statuses:
    
    platform.portfolio['cash']                      # Available Cash
    
    platform.has_pos('HSI')                         # Check if trading log already ahs HSI positio
    
and so on....
