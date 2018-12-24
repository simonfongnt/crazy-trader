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
dataset['HSI'] = 'EQ'  # Close, Volume
dataset['PUT'] = 'Custom'  # requires functions
dataset['CALL'] = 'Custom'  # requires functions
dataset['VHSI'] = 'Vol'  # Close
dataset['VIX'] = 'Vol'  # Close
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
        
        vhsi_open = platform.quote['VHSI'].loc[time].Close
        
        prev_vpt = 0                                            # last volume-price trend
        this_vpt = 0                                            # this volume-price trend
        this_vpt_volume = 0                                     # this volume
        prev_vpt_price = platform.quote['HSI'].loc[time].Close  # last VPT price
        this_vpt_price = platform.quote['HSI'].loc[time].Close  # this VPT price
                
        prev_obv = 0                                            # Previous On-Balance Volume
        this_obv = 0                                            # this On-Balance Volume
        
        hsi_vhsi    = None                                      # last VPT price
        
        hsi_rate    = None
        hsi_vhsi    = None
        hsi_pos     = None
        prev_trend   = None
        
        # XRPUSD 
        prev_vix = platform.quote['VIX'].loc[time].Close        # last VPT price
        this_vix = platform.quote['VIX'].loc[time].Close        # last VPT price
        vix_open = platform.quote['VIX'].loc[time].Close        # last VPT price
        xrp_rate    = None
        xrp_vix     = None
        xrp_date    = None
        xrp_delta   = None
        xrp_loss    = 0
        continue

    # Check if EQ market is opened
    if platform.is_eqmktopen(time):

        # Volume-Price Trend: accumulating volume until VPT calcuation
        this_vpt_volume = this_vpt_volume + platform.quote['HSI'].loc[time].Volume

        if time.time() == datetime.time(9, 20, 0):                                        # VIX market open
            vhsi_open = platform.quote['VHSI'].loc[time].Close                            # Capture Open Price

        # Trade conditions
        if (
                time.time() == datetime.time(10, 0, 0)  # One trade per day at 10:00
        ):
            # Calculation VPT once per day      
            # Save the VPT price for VPT calculation
            this_vpt_price = platform.quote['HSI'].loc[time].Close  
            # Calculate VPT
            this_vpt = getvpt(prev_vpt, this_vpt_volume, prev_vpt_price, this_vpt_price)  
            # On Balance Volume
            if this_vpt_price > prev_vpt_price:
                this_obv = prev_obv + this_vpt_volume
            elif this_vpt_price < prev_vpt_price:
                this_obv = prev_obv - this_vpt_volume
            prev_obv = this_obv
            prev_trend = this_vpt_price - prev_vpt_price
            # no position exists and previous VPT exists
            if not platform.has_pos('HSI') and prev_vpt:                                
                # Low Volatility
                if platform.quote['VHSI'].loc[time].Close - vhsi_open < 1.00:           
                    # Trned is upward
                    if this_vpt - prev_vpt > 500:
                        # Short 150 Qty of HSI Future                                                   
                        platform.trade(time, 'HSI', 'LONG', 150)                        
                        hsi_pos = 'LONG'
                    # Trned is downward                        
                    elif this_vpt - prev_vpt < -100:   
                        # Short 150 Qty of HSI Future                                             
                        platform.trade(time, 'HSI', 'SHORT', 150)                       
                        hsi_pos = 'SHORT'
                    # No Trend
                    else:                                                               
                        pass
                # High Volatility     
                else:                            
                    # option maturity                                                
                    option_maturity = time.month         
                    # Trned is upward                           
                    if this_vpt - prev_vpt > 500:
                        # Short 150 Qty of HSI Future                                
                        platform.trade(time, 'HSI', 'LONG', 100)   
                        # option step: 200 - around 400 points from the underlying price
                        option_strike = (int(platform.quote['HSI'].loc[
                                                 time].Close / 200) + 2) * 200          
                        platform.trade(time, 'PUT', 'LONG', 100, option_strike, option_maturity)
                        hsi_pos = 'PUT'
                    # Trned is downward                          
                    elif this_vpt - prev_vpt < -100:
                        # Short 150 Qty of HSI Future                                       
                        platform.trade(time, 'HSI', 'SHORT', 100)   
                        # option step: 200 - around 400 points from the underlying price
                        option_strike = (int(platform.quote['HSI'].loc[
                                                 time].Close / 200) - 2) * 200          
                        platform.trade(time, 'CALL', 'LONG', 100, option_strike, option_maturity)
                        hsi_pos = 'CALL'
                    # No Trend          
                    else:                       
                        # option step: 200 - around 400 points from the underlying price                                        
                        option_strike = (int(platform.quote['HSI'].loc[
                                                 time].Close / 200) - 2) * 200          
                        platform.trade(time, 'CALL', 'LONG', 100, option_strike, option_maturity)
                        # option step: 200 - around 400 points from the underlying price
                        option_strike = (int(platform.quote['HSI'].loc[
                                                 time].Close / 200) + 2) * 200          
                        platform.trade(time, 'PUT', 'LONG', 100, option_strike, option_maturity)
                        hsi_pos = 'BOTH'

            # VPT preparation
            hsi_tvpt = this_vpt
            hsi_pvpt = prev_vpt
            # reset VPT volume for next day accumulation
            this_vpt_volume = 0  
            # Save today's vpt price for next day
            prev_vpt_price = this_vpt_price  
            # Save today's vpt for next day
            prev_vpt = this_vpt  
            
            #stop-loss
            hsi_rate = platform.quote['HSI'].loc[time].Close
            hsi_vhsi = platform.quote['VHSI'].loc[time].Close
            
        # Close conditions
        if (
                # Close everything at 16:10
                time.time() == datetime.time(16, 10, 0)  
        ):
#            if platform.has_pos('HSI'):  # Check if position exists
            # Close HSI Future
            platform.trade(time, 'HSI', 'CLOSE')  
            # Close HSI Call Option
            platform.trade(time, 'CALL', 'CLOSE')  
            # Close HSI Put Option
            platform.trade(time, 'PUT', 'CLOSE')     
            # Clear trade rate                                               
            hsi_rate = None                                                                         
            hsi_pos = None
        
        # Stoploss
        if (    # Check if position exists
                platform.has_pos('HSI')                                                           
            ):
            # calculate loss rate for stoploss
            hsi_loss = float(platform.quote['HSI'].loc[time].Close - hsi_rate) /  hsi_rate        
            if (  # Stoploss: 1%  
                  hsi_loss > 0.01                                                                 
            ):
                # Close HSI Future
                platform.trade(time, 'HSI', 'CLOSE')       
                # Clear trade rate                                       
                hsi_rate = None                                                                   
                hsi_pos = None
                
    # EQ is not in trading hours
    else:
        pass

#    # Check if FX and Crypto markets are opened
#    if platform.is_fxmktopen(time):
#        # Trade HKDTRY - Short Position only based on Event Driven Strategy
#        if (    # Trade on 1st of Sep
#                time.timestamp() == datetime.datetime(2018,  9, 1, 17, 0, 0).timestamp()            
#                ):
#            # Short HKDTRY
#            platform.trade(time, 'HKDTRY', 'SHORT', 3000000)                                        
#        if (    # Trade on 15th of Oct
#                time.timestamp() == datetime.datetime(2018, 10, 15, 17, 0, 0).timestamp()           
#                ):
#            # Close HKDTRY
#            platform.trade(time, 'HKDTRY', 'CLOSE')      
#            # Short HKDTRY                                           
#            platform.trade(time, 'HKDTRY', 'SHORT', 4000000)                                        
#        if (    # Close on 30th of Nov
#                time.timestamp() == datetime.datetime(2018, 11, 30, 17, 0, 0).timestamp()           
#                ):
#            # Close HKDTRY
#            platform.trade(time, 'HKDTRY', 'CLOSE')                                                 
#            
#        # Trade XRPUSD - Short Position only based on VIX
#        # VIX market open
#        if time.time() == datetime.time(15, 16, 0):     
#            # Capture Open Price                                            
#            vix_open = platform.quote['VIX'].loc[time].Close   
#            # no position                                     
#            if not platform.has_pos('XRPUSD'):     
#                # Clear open date for new trade                                                 
#                xrp_date = None      
#        # Capture Current Price                                                               
#        this_vix = platform.quote['VIX'].loc[time].Close                                            
#        
#        if (    # No Position of Ripple
#                not platform.has_pos('XRPUSD')        
#                # No Trade today                                              
#            and not xrp_date           
#                # VIX rises 2 points above open price                                                             
#            and this_vix - vix_open > 2                                                             
#                ):           
#            # Open Short Position
#            platform.trade(time, 'XRPUSD', 'SHORT', 420000)   
#            # Note down trade rate                                      
#            xrp_rate = platform.quote['XRPUSD'].loc[time].Ask    
#            # Note down VIX at trade                                   
#            xrp_vix = platform.quote['VIX'].loc[time].Close     
#            # Note down trade date                                    
#            xrp_date = time                                                                         
#
#        # Close conditions
#        # Trade is done
#        if xrp_date:      
#            # calculate date after open postion                                                                          
#            xrp_delta = xrp_date - time                                                             
#
#        if (    # Check if position exists
#                platform.has_pos('XRPUSD')               
#                # trade date exists                                           
#            and xrp_date                                                                            
#            ):
#            # calculate loss rate for stoploss
#            xrp_loss = float(platform.quote['XRPUSD'].loc[time].Ask - xrp_rate) /  xrp_rate         
#            if (    # 5 days after the trade
#                    xrp_delta.days >= 5         
#                    # VIX drop below VIX at trade                                                    
#                or  vix_open - this_vix > 0                
#                    # Stoploss: 1%                                         
#                or  xrp_loss > 0.01                                                                 
#            ):  # Close XRP Future
#                platform.trade(time, 'XRPUSD', 'CLOSE')     
#                # Clear trade rate                                        
#                xrp_rate = None         
#                # Clear VIX at trade                                                            
#                xrp_vix  = None                                                                     

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


