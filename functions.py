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

pd.set_option('display.float_format', lambda x: '%.1f' % x)

np.set_printoptions(suppress=True, formatter={'float_kind':'{:0.1f}'.format})  #float, 2 units, precision right, 0 on left
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
#%% classes
class backtest():
    def __init__(self, cash, fee, dataset):
        self.datainfo = {}
        self.quote = {}
        self.portfolio = {}
        self.logcols = ['Product', 'Strike', 'Maturity', 'Position', 'Open Date', 'Open Rate', 'Qty', 'Close Date', 'Close Rate', 'Handling', 'Unrealized P&L', 'Realized P&L', 'P&L%']
        self.initportfolio(cash, fee)    
        self.initdataset(dataset)
        
    def initportfolio(self, cash, fee):
        self.portfolio['initial']       = cash      #HKD
        self.portfolio['fee']           = fee       #HKD
        self.portfolio['cash']          = cash      #HKD
        self.portfolio['incurred fee']  = 0         #HKD
        self.portfolio['P&L']           = (self.portfolio['cash'] - self.portfolio['initial']) / self.portfolio['initial']     #%
        self.trading_log                = pd.DataFrame(columns=self.logcols)                 # initialize trading log
    
    def initdataset(self, dataset):
        self.datainfo = dataset
        valid_start = None
        valid_end   = None
        for key, data in self.datainfo.items():
            if data is not 'Custom':
                # determine valid start and end of dataset
                data = pd.read_excel(key + '.xlsx')
                if not valid_start or valid_start < min(data['Local Time']):
                    valid_start = min(data['Local Time'])
                if not valid_end or valid_end > max(data['Local Time']):
                    valid_end   = max(data['Local Time'])
                days            = pd.date_range(min(data['Local Time']), max(data['Local Time']), freq='min')
                # create dataset for each item
                quoteref = pd.DataFrame({'Local Time': days})
                quoteref = quoteref.set_index('Local Time')
                self.quote[key] = quoteref
                data            = data.set_index('Local Time')                 
                self.quote[key] = pd.merge(self.quote[key], data, left_index=True, how='left', right_index=True)
            #    market[key].plot(y='Bid', use_index=True)
                self.quote[key].fillna(method='ffill', inplace=True)
                self.quote[key].fillna(method='bfill', inplace=True)
        # Custom dataset
        self.quote['PUT']        = self.quote['HSI']
        self.quote['CALL']       = self.quote['HSI']
        print ('Dataset Range:', 'from', valid_start, 'to', valid_end)
        
    def is_eqmktopen(self, time):
        second = time.timestamp() % 86400
        if time.weekday() < 6:
            if second < 3600:
                return True
            if second >= 33300 and second < 43200:
                return True
            if second >= 46800 and second < 59700:
                return True
            if second >= 62100:
                return True
        return False
    
    def is_fxmktopen(self, time):
        if time.weekday() < 6:
            return True
        return False
    
    def norm_cdf(self, x):
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
            return 1.0 - self.norm_cdf(-x)
    
    #IV Assumptions: [ Interest rate is 0.15% and dividend yield is 4.24%, per year.]
    def option(self, time, option_type, S, K, month, r = 0.0015, v = 0.25, d = 0.0424):
        start   = time.date()
        end     = BMonthEnd().rollforward(datetime.date(time.year, month, 1)).date()
        T       = np.busday_count(start, end)
        # espired
        if T <= 0:
            return 0
        
        if K % 200 != 0: 
            error (time, 'Strike Price is in step of 200')
        # params
        Tt      = T / 365.0     # float for 2.7
        
        d1      = (log (S / (K * exp(-r * Tt))) / (v * sqrt(Tt))) + 0.5 * v * sqrt(Tt)
        d2      = d1 - v * sqrt(Tt)
        
        callp   = S * exp(-1 * d * Tt) * self.norm_cdf( 1 * d1) - K * exp(-1 * r * Tt) * self.norm_cdf( 1 * d2)
        putp    = K * exp(-1 * r * Tt) * self.norm_cdf(-1 * d2) - S * exp(-1 * d * Tt) * self.norm_cdf(-1 * d1)
        
        if option_type == 'CALL':
            premium = callp
        else:
            premium = putp
        
        if premium <= 0:
            return 0
        else:
            return premium
        
    # convert product rate to HKD    
    def forextohkd(self, time, product, rate):
    #    datainfo['HSI']     = 'EQ'  # Close, Volume
    #    datainfo['VHSI']    = 'Vol' # Close
    #    datainfo['VIX']     = 'Vol' # Close
    #    datainfo['USDHKD']  = 'FX'  # Bid, Ask
    #    datainfo['XAUHKD']  = 'FX'  # Bid, Ask
    #    datainfo['HKDTRY']  = 'FX'  # Bid, Ask
    #    datainfo['USDTRY']  = 'FX'  # Bid, Ask
    #    datainfo['XRPUSD']  = 'FX'  # Bid, Ask
        if   product.startswith('USD'):             # Change to HKDXXX
            return (self.quote['USDHKD'].loc[time].Ask / rate)
        elif product.startswith('HKD'):
            return (1 / rate)
        elif product.endswith  ('USD'):            # Change to XXXHKD
            return (rate * self.quote['USDHKD'].loc[time].Bid)
        else:
            return rate
    
    def getrate(self, time, product, pos):
        if self.datainfo[product] is not 'FX':
            rate = self.quote[product].loc[time].Close
        elif pos == 'LONG':
            rate = self.quote[product].loc[time].Ask
        else:
            rate = self.quote[product].loc[time].Bid
        return rate
    
    def has_pos(self, product):     
        # Existing Order?
        for i in range(len(self.trading_log)):
            if self.trading_log.loc[i, 'Product'] == product and not self.trading_log.loc[i, 'Close Date']:
                return True
        return False
    
    def opencheck(self, time, product, pos, qty, K, T, cash): 
        strike      = K
        maturity    = T               
        # Existing Order?
        for i in range(len(self.trading_log)):
            if self.trading_log.loc[i, 'Product'] == product and not self.trading_log.loc[i, 'Close Date']:
                error (time, 'Please close existing position...')
        # Param Check
        if qty <= 0:
            error (time, 'Invalid Long/Short Quantity')      
        # Option
        if (product == 'PUT' or product == 'CALL'):
            if strike and maturity:                
                if time.month > maturity:
                    error (time, 'invalid Option month...')
            else:
                error ('Option Strike or Maturity Missing...')
        # Enough $?
        if self.portfolio['cash'] <= 0:
            error (time, 'Out of Cash...')
        
    def closecheck(self, time, cash):
        # Enough $?
        if self.portfolio['cash'] <= 0:
            error (time, 'Out of Cash...')
    
    def trade(self, time, product, pos, qty = 0, K = None, T = None):
        strike      = K
        maturity    = T
        # Long / Short Position
        if pos == 'LONG' or pos == 'SHORT':  
            handling                                            = self.portfolio['fee']
            # Option
            if (product == 'PUT' or product == 'CALL'):
                if strike and maturity and time.month <= maturity:
                    rate                                        = self.option(time, product, self.quote['HSI'].loc[time].Close, strike, maturity)
            else:                
                rate = self.getrate(time, product, pos)  
            # Available Cash
            self.portfolio['cash']                              = self.portfolio['cash'] - qty * self.forextohkd(time, product, rate) - handling
            # Report
            if (product == 'PUT' or product == 'CALL'):
                print (time, 'Avl.Cash:', round(self.portfolio['cash']), product, '(', K, T, ')', pos, qty, '@', round(rate, 2))
            else:
                print (time, 'Avl.Cash:', round(self.portfolio['cash']), product, pos, qty, '@', round(rate, 2))
            # Open Restriction
            self.opencheck(time, product, pos, qty, K, T, self.portfolio['cash'])
            # Append to trading log
            self.trading_log.loc[len(self.trading_log)]         = [product, strike, maturity, pos, time, rate, qty, None, None, handling, 0, 0, 0]
            
        # Close Position - ignore QTY
        else:
            for i in range(len(self.trading_log)):
                if self.trading_log.loc[i, 'Product'] == product and not self.trading_log.loc[i, 'Close Date']:
                    self.trading_log.loc[i, 'Close Date']       = time
                    self.trading_log.loc[i, 'Handling']         = self.trading_log.loc[i, 'Handling'] + self.portfolio['fee']
                                        
                    # Get rate at time
                    if (product == 'PUT' or product == 'CALL'):
                        self.trading_log.loc[i, 'Close Rate']   = self.option(time, self.trading_log.loc[i, 'Product'], self.quote['HSI'].loc[time].Close, self.trading_log.loc[i, 'Strike'], self.trading_log.loc[i, 'Maturity'])
                    else:
                        self.trading_log.loc[i, 'Close Rate']   = self.getrate(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Position'])
                        
                    self.trading_log.loc[i, 'Unrealized P&L']   = 0
                    
                    if self.trading_log.loc[i, 'Position'] == 'LONG':
                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, self.trading_log.loc[i, 'Product'], (self.trading_log.loc[i, 'Close Rate'] - self.trading_log.loc[i, 'Open Rate'])) - self.trading_log.loc[i, 'Handling']
                    else:
                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, self.trading_log.loc[i, 'Product'], (self.trading_log.loc[i, 'Open Rate'] - self.trading_log.loc[i, 'Close Rate'])) - self.trading_log.loc[i, 'Handling']
                    
                    self.trading_log.loc[i, 'P&L%']             = int((self.trading_log.loc[i, 'Unrealized P&L'] + self.trading_log.loc[i, 'Realized P&L']) / (self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Open Rate'])) * 100)

                    # Get Cash        
                    self.portfolio['cash']                      = self.portfolio['cash'] + (self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Open Rate']) * self.trading_log.loc[i, 'Qty']) - self.portfolio['fee']
                    self.portfolio['cash']                      = self.portfolio['cash'] + self.trading_log.loc[i, 'Realized P&L']                    
                    # Report
                    print (time, 'Avl.Cash:', round(self.portfolio['cash']), product, pos, self.trading_log.loc[i, 'Qty'], '@', round(self.trading_log.loc[i, 'Close Rate'], 2))
                    # Close Restriction
                    self.closecheck(time, self.portfolio['cash'])
        
    def updatepos(self, time):
        for i in range(len(self.trading_log)):        
            product = self.trading_log.loc[i, 'Product']            
            rate                                                = self.getrate(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Position'])
            if (product == 'PUT' or product == 'CALL'):
                rate                                            = self.option(time, product, self.quote['HSI'].loc[time].Close, self.trading_log.loc[i, 'Strike'], self.trading_log.loc[i, 'Maturity'])
                if time.month > self.trading_log.loc[i, 'Maturity'] and not self.trading_log.loc[i, 'Close Date']:
                    self.trading_log.loc[i, 'Close Date']       = time        
                    self.trading_log.loc[i, 'Close Rate']       = rate
                    self.trading_log.loc[i, 'Unrealized P&L']   = 0
                    
                    if self.trading_log.loc[i, 'Position'] == 'LONG':
                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, (self.trading_log.loc[i, 'Close Rate'] - self.trading_log.loc[i, 'Open Rate'])) - self.trading_log.loc[i, 'Handling']
                    else:
                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, (self.trading_log.loc[i, 'Open Rate'] - self.trading_log.loc[i, 'Close Rate'])) - self.trading_log.loc[i, 'Handling']
                    
                    self.trading_log.loc[i, 'P&L%']             = int((self.trading_log.loc[i, 'Unrealized P&L'] + self.trading_log.loc[i, 'Realized P&L']) / (self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate'])) * 100)
                    
                    # Get Cash        
                    self.portfolio['cash']                      = self.portfolio['cash'] + (self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate']) * self.trading_log.loc[i, 'Qty']) - self.portfolio['fee']
                    self.portfolio['cash']                      = self.portfolio['cash'] + self.trading_log.loc[i, 'Realized P&L']
                    # Enough $?
                    if self.portfolio['cash'] <= 0:
                        error (time, 'No more Money...')
                    
            if not self.trading_log.loc[i, 'Close Date']:
                
                self.trading_log.loc[i, 'Realized P&L']          = 0
                
                if self.trading_log.loc[i, 'Position'] == 'LONG':
                    self.trading_log.loc[i, 'Unrealized P&L']    = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, (rate - self.trading_log.loc[i, 'Open Rate'])) - self.trading_log.loc[i, 'Handling'] * 2
                else:
                    self.trading_log.loc[i, 'Unrealized P&L']    = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, (self.trading_log.loc[i, 'Open Rate'] - rate)) - self.trading_log.loc[i, 'Handling'] * 2
                
                self.trading_log.loc[i, 'P&L%']                  = (self.trading_log.loc[i, 'Unrealized P&L'] + self.trading_log.loc[i, 'Realized P&L']) / (self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate']))
        
    def exporttrades(self):            
        # Plot the Graph
        for key, datatype in self.datainfo.items():
            if datatype is not 'Custom':
                plt.figure() #to let the index start at 1
                if datatype == 'EQ' or datatype == 'Vol':        
                    plt.plot(self.quote[key].index,    self.quote[key].Close, label = key)
                else:
                    plt.plot(self.quote[key].index,    self.quote[key].Bid, label = key)
                    plt.plot(self.quote[key].index,    self.quote[key].Ask, label = key)
                df = self.trading_log.loc[(self.trading_log['Product'] == key) & (self.trading_log['Position'] == 'LONG')]
                plt.plot(df['Open Date'],       df['Open Rate'],    '^', markersize=10, color='g')
                plt.plot(df['Close Date'],      df['Close Rate'],   '^', markersize=10, color='g', markerfacecolor='white', )
                df = self.trading_log.loc[(self.trading_log['Product'] == key) & (self.trading_log['Position'] == 'SHORT')]
                plt.plot(df['Open Date'],       df['Open Rate'],    'v', markersize=10, color='r')
                plt.plot(df['Close Date'],      df['Close Rate'],   'v', markersize=10, color='r', markerfacecolor='white', )
                plt.title(key)
                plt.ylabel('Rate')
                plt.xlabel('Date')
        plt.show()
        # Calculate portfolio
        self.portfolio['incurred fee']   = self.trading_log['Handling'].sum()
        self.portfolio['Unrealized P&L'] = self.trading_log['Unrealized P&L'].sum()
        self.portfolio['Realized P&L']   = self.trading_log['Realized P&L'].sum()
        self.portfolio['P&L']            = self.portfolio['Unrealized P&L'] + self.portfolio['Realized P&L']
        self.portfolio['P&L%']           = self.portfolio['P&L'] / self.portfolio['initial'] * 100
        return self.portfolio, self.trading_log