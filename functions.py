# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 00:06:55 2018

@author: SF
"""

#%% lLibrary
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import sys
import re
import pandas as pd
import numpy as np
import time
import datetime

import math
from math import exp, log, log1p, pi, sqrt

from pandas.tseries.offsets import BMonthEnd

import matplotlib.pyplot as plt
#%% Consts
datainfo = {}
datainfo['HSI']     = 'EQ'  # Close, Volume
datainfo['VHSI']    = 'Vol' # Close
datainfo['VIX']     = 'Vol' # Close
datainfo['USDHKD']  = 'FX'  # Bid, Ask
datainfo['XAUHKD']  = 'FX'  # Bid, Ask
datainfo['HKDTRY']  = 'FX'  # Bid, Ask
datainfo['USDTRY']  = 'FX'  # Bid, Ask
datainfo['XRPUSD']  = 'FX'  # Bid, Ask
#%% Params
quote = {}
portfolio = {}
logcols = ['Product', 'Strike', 'Maturity', 'Position', 'Open Date', 'Open Rate', 'Qty', 'Close Date', 'Close Rate', 'Handling', 'Unrealized P&L', 'Realized P&L', 'P&L%']
trading_log = pd.DataFrame(columns=logcols)                 # initialize trading log
#%% Dataset
def initdataset():
    start_day           = datetime.datetime(2018, 8,  7,  1,  1,  0) 
    end_day             = datetime.datetime(2018, 10, 31, 23, 59, 0)
    days = pd.date_range(start_day, end_day, freq='min')
    quoteref = pd.DataFrame({'Local Time': days})
    quoteref = quoteref.set_index('Local Time')
    for key, data in datainfo.items():
        quote[key] = quoteref
        data = pd.read_excel(key + '.xlsx')
        data = data.set_index('Local Time') 
        quote[key] = pd.merge(quote[key], data, left_index=True, how='left', right_index=True)
    #    market[key].plot(y='Bid', use_index=True)
        quote[key].fillna(method='ffill', inplace=True)
        quote[key].fillna(method='bfill', inplace=True)
    quote['PUT']        = quote['HSI']
    quote['CALL']       = quote['HSI']
    #    print (key, market[key].isna().sum())
#%% Functions
# ------------------------------------------------------------------
# Reset so get full traceback next time you run the script and a "real"
# exception occurs
if hasattr (sys, 'tracebacklimit'):
    del sys.tracebacklimit

# ------------------------------------------------------------------
# Raise this class for "soft halt" with minimum traceback.
class Stop (Exception):
    def __init__ (self):
        sys.tracebacklimit = 0

def error(time, text):
    print (time, text)
    raise Stop ()

def norm_cdf(x):
    """
    An approximation to the cumulative distribution
    function for the standard normal distribution:
    N(x) = \frac{1}{sqrt(2*\pi)} \int^x_{-\infty} e^{-\frac{1}{2}s^2} ds
    """
    k = 1.0/(1.0+0.2316419*x)
    k_sum = k * (0.319381530 + k * (-0.356563782 + \
        k * (1.781477937 + k * (-1.821255978 + 1.330274429 * k))))

    if x >= 0.0:
        return (1.0 - (1.0 / ((2 * pi)**0.5)) * exp(-0.5 * x * x) * k_sum)
    else:
        return 1.0 - norm_cdf(-x)

#IV Assumptions: [ Interest rate is 0.15% and dividend yield is 4.24%, per year.]
def option(time, option_type, S, K, month, r = 0.0015, v = 0.25, d = 0.0424):
    start   = time.date()
    end     = BMonthEnd().rollforward(datetime.date(time.year, month, 1))
    T = np.busday_count(start, end)
    # espired
    if T <= 0:
        return 0
    
    if K % 200 != 0: 
        error (time, 'Strike Price is in step of 200')
    # params
    Tt      = T / 365
    
    d1      = (log (S / (K * exp(-r * Tt))) / (v * sqrt(Tt))) + 0.5 * v * sqrt(Tt)
    d2      = d1 - v * sqrt(Tt)
    
    callp   = S * exp(-1 * d * Tt) * norm_cdf( 1 * d1) - K * exp(-1 * r * Tt) * norm_cdf( 1 * d2)
    putp    = K * exp(-1 * r * Tt) * norm_cdf(-1 * d2) - S * exp(-1 * d * Tt) * norm_cdf(-1 * d1)
    
    if option_type == 'CALL':
        premium = callp
    else:
        premium = putp
    
    if premium <= 0:
        return 0
    else:
        return premium
    
# convert product rate to HKD    
def forextohkd(time, product, rate):
#    datainfo['HSI']     = 'EQ'  # Close, Volume
#    datainfo['VHSI']    = 'Vol' # Close
#    datainfo['VIX']     = 'Vol' # Close
#    datainfo['USDHKD']  = 'FX'  # Bid, Ask
#    datainfo['XAUHKD']  = 'FX'  # Bid, Ask
#    datainfo['HKDTRY']  = 'FX'  # Bid, Ask
#    datainfo['USDTRY']  = 'FX'  # Bid, Ask
#    datainfo['XRPUSD']  = 'FX'  # Bid, Ask
    if product == 'USDTRY':
        return 1 / rate * quote['USDHKD'].loc[time].Bid
    elif product == 'HKDTRY':
        return 1 / rate
    elif product == 'XRPUSD':
        return rate * quote['USDHKD'].loc[time].Bid
    else:
        return rate    
    
def trade(time, product, pos, rate, qty, K = None, T = None):
    strike      = K
    maturity    = T
    # Long / Short Position
    if pos == 'LONG' or pos == 'SHORT': 
        # Existing Order?
        for i in range(len(trading_log)):
            if trading_log.loc[i, 'Product'] == product and not trading_log.loc[i, 'Close Date']:
                error (time, 'Please close existing position...')
        # Trade Order
        handling    = portfolio['fee']
        # Option
        if (product == 'PUT' or product == 'CALL'):
            if rate and strike and maturity:                
                if time.month > maturity:
                    error (time, 'invalid Option month...')
                rate = option(time, product, rate, strike, maturity)
            else:
                error ('Option Strike or Maturity Missing...')
        
        # Append to trading log
        trading_log.loc[len(trading_log)] = [product, strike, maturity, pos, time, rate, qty, None, None, handling, 0, 0, 0]
        
        # Enough $?
        if portfolio['cash'] < qty * forextohkd(time, product, rate) + handling:
            error (time, 'Not Enough Cash for trading...')
        portfolio['cash']                       = portfolio['cash'] - qty * forextohkd(time, product, rate) - portfolio['fee']
        
    # Close Position - ignore QTY
    else:
        for i in range(len(trading_log)):
            if trading_log.loc[i, 'Product'] == product and not trading_log.loc[i, 'Close Date']:
                trading_log.loc[i, 'Close Date']        = time
                trading_log.loc[i, 'Handling']          = trading_log.loc[i, 'Handling'] + portfolio['fee']
                
                if (product == 'PUT' or product == 'CALL'):
                    trading_log.loc[i, 'Close Rate']    = option(time, product, rate, trading_log.loc[i, 'Strike'], trading_log.loc[i, 'Maturity'])
                else:
                    trading_log.loc[i, 'Close Rate']    = rate
                
                trading_log.loc[i, 'Unrealized P&L']    = 0
                
                if trading_log.loc[i, 'Position'] == 'LONG':
                    trading_log.loc[i, 'Realized P&L']  = trading_log.loc[i, 'Qty'] * forextohkd(time, product, (trading_log.loc[i, 'Close Rate'] - trading_log.loc[i, 'Open Rate'])) - trading_log.loc[i, 'Handling']
                else:
                    trading_log.loc[i, 'Realized P&L']  = trading_log.loc[i, 'Qty'] * forextohkd(time, product, (trading_log.loc[i, 'Open Rate'] - trading_log.loc[i, 'Close Rate'])) - trading_log.loc[i, 'Handling']
                
                trading_log.loc[i, 'P&L%']              = (trading_log.loc[i, 'Unrealized P&L'] + trading_log.loc[i, 'Realized P&L']) / (trading_log.loc[i, 'Qty'] * forextohkd(time, product, trading_log.loc[i, 'Open Rate']))
                
                # Get Cash        
                portfolio['cash']                       = portfolio['cash'] + (forextohkd(time, product, trading_log.loc[i, 'Open Rate']) * trading_log.loc[i, 'Qty']) - portfolio['fee']
                portfolio['cash']                       = portfolio['cash'] + trading_log.loc[i, 'Realized P&L']
                # Enough $?
                if portfolio['cash'] <= 0:
                    error (time, 'No more Money...')
                
#    print (portfolio['cash'])
    
def updatepos(time):
    for i in range(len(trading_log)):        
        product = trading_log.loc[i, 'Product']
        if (product == 'PUT' or product == 'CALL'):
            rate                                        = option(time, product, quote['HSI'].loc[time].Close, trading_log.loc[i, 'Strike'], trading_log.loc[i, 'Maturity'])
            if time.month > trading_log.loc[i, 'Maturity'] and not trading_log.loc[i, 'Close Date']:
                trading_log.loc[i, 'Close Date']        = time        
                trading_log.loc[i, 'Close Rate']        = rate
                trading_log.loc[i, 'Unrealized P&L']    = 0
                
                if trading_log.loc[i, 'Position'] == 'LONG':
                    trading_log.loc[i, 'Realized P&L']  = trading_log.loc[i, 'Qty'] * forextohkd(time, product, (trading_log.loc[i, 'Close Rate'] - trading_log.loc[i, 'Open Rate'])) - trading_log.loc[i, 'Handling']
                else:
                    trading_log.loc[i, 'Realized P&L']  = trading_log.loc[i, 'Qty'] * forextohkd(time, product, (trading_log.loc[i, 'Open Rate'] - trading_log.loc[i, 'Close Rate'])) - trading_log.loc[i, 'Handling']
                
                trading_log.loc[i, 'P&L%']              = (trading_log.loc[i, 'Unrealized P&L'] + trading_log.loc[i, 'Realized P&L']) / (trading_log.loc[i, 'Qty'] * forextohkd(time, product, trading_log.loc[i, 'Open Rate']))
                
                # Get Cash        
                portfolio['cash']                       = portfolio['cash'] + (forextohkd(time, product, trading_log.loc[i, 'Open Rate']) * trading_log.loc[i, 'Qty']) - portfolio['fee']
                portfolio['cash']                       = portfolio['cash'] + trading_log.loc[i, 'Realized P&L']
                # Enough $?
                if portfolio['cash'] <= 0:
                    error (time, 'No more Money...')
                                    
        elif datainfo[product] == 'EQ' or datainfo[product] == 'Vol':
            rate                                        = quote[product].loc[time].Close
        elif datainfo[product] == 'FX':
            if trading_log.loc[i, 'Position'] == 'LONG':
                rate                                    = quote[product].loc[time].Bid
            else:
                rate                                    = quote[product].loc[time].Ask
        else:
            error ('row', i, 'product does not exist...')
                
        if not trading_log.loc[i, 'Close Date']:
            
            trading_log.loc[i, 'Realized P&L']          = 0
            
            if trading_log.loc[i, 'Position'] == 'LONG':
                trading_log.loc[i, 'Unrealized P&L']    = trading_log.loc[i, 'Qty'] * forextohkd(time, product, (rate - trading_log.loc[i, 'Open Rate'])) - trading_log.loc[i, 'Handling'] * 2
            else:
                trading_log.loc[i, 'Unrealized P&L']    = trading_log.loc[i, 'Qty'] * forextohkd(time, product, (trading_log.loc[i, 'Open Rate'] - rate)) - trading_log.loc[i, 'Handling'] * 2
            
            trading_log.loc[i, 'P&L%']                  = (trading_log.loc[i, 'Unrealized P&L'] + trading_log.loc[i, 'Realized P&L']) / (trading_log.loc[i, 'Qty'] * forextohkd(time, product, trading_log.loc[i, 'Open Rate']))
        
def initportfolio(cash, fee):
    global trading_log
    portfolio['initial']        = cash      #HKD
    portfolio['fee']            = fee       #HKD
    portfolio['cash']           = cash      #HKD
    portfolio['incurred fee']   = 0         #HKD
    portfolio['P&L']            = (portfolio['cash'] - portfolio['initial']) / portfolio['initial']     #%
    trading_log = pd.DataFrame(columns=logcols)                 # initialize trading log

def exporttrades():
#    plt.plot(quote['HSI'].index,    quote['HSI'].Close, label='HSI')
#    df = trading_log.loc[(trading_log['Product'] == 'HSI') & (trading_log['Position'] == 'LONG')]
#    plt.plot(df['Open Date'],       df['Open Rate'],    '^', markersize=10, color='g')
#    plt.plot(df['Close Date'],      df['Close Rate'],   '^', markersize=10, color='g', markerfacecolor='white', )
#    df = trading_log.loc[(trading_log['Product'] == 'HSI') & (trading_log['Position'] == 'SHORT')]
#    plt.plot(df['Open Date'],       df['Open Rate'],    'v', markersize=10, color='r')
#    plt.plot(df['Close Date'],      df['Close Rate'],   'v', markersize=10, color='r', markerfacecolor='white', )
    for key, datatype in datainfo.items():        
        plt.figure() #to let the index start at 1
        if datatype == 'EQ' or datatype == 'Vol':        
            plt.plot(quote[key].index,    quote[key].Close, label = key)
        else:
            plt.plot(quote[key].index,    quote[key].Bid, label = key)
            plt.plot(quote[key].index,    quote[key].Ask, label = key)
        df = trading_log.loc[(trading_log['Product'] == key) & (trading_log['Position'] == 'LONG')]
        plt.plot(df['Open Date'],       df['Open Rate'],    '^', markersize=10, color='g')
        plt.plot(df['Close Date'],      df['Close Rate'],   '^', markersize=10, color='g', markerfacecolor='white', )
        df = trading_log.loc[(trading_log['Product'] == key) & (trading_log['Position'] == 'SHORT')]
        plt.plot(df['Open Date'],       df['Open Rate'],    'v', markersize=10, color='r')
        plt.plot(df['Close Date'],      df['Close Rate'],   'v', markersize=10, color='r', markerfacecolor='white', )
        plt.ylabel('Rate')
        plt.xlabel('Date')
        plt.legend(loc=0)
    plt.show()
    
    portfolio['incurred fee']   = trading_log['Handling'].sum()
    portfolio['P&L']            = (portfolio['cash'] - portfolio['initial']) / portfolio['initial']     #%
    return portfolio, trading_log
#    plt.plot(sells.index,           data.ix[sells.index]['Settle'], 'v', markersize=10, color='r')

##    print (quote)
#    print (trading_log)
#    print (portfolio)    