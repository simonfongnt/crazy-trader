# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 00:06:55 2018

@author: SF
"""

#%% lLibrary
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import dataset
import os
import sys
import re
import pandas as pd
import numpy as np
import time
import datetime

import math
from math import exp, log, pi, sqrt
from scipy.stats import norm

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
        self.datainfo   = {}
        self.quote      = {}
        self.portfolio  = {}
        self.validstart = None
        self.validend   = None
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
        for key, data in self.datainfo.items():
            if data is not 'Custom':
                # determine valid start and end of dataset
                data = pd.read_excel('dataset/' + key + '.xlsx')
                if not self.validstart or self.validstart < min(data['Local Time']):
                    self.validstart = min(data['Local Time'])
                if not self.validend or self.validend > max(data['Local Time']):
                    self.validend   = max(data['Local Time'])
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
                print ('Dataset', key, 'is loaded')
        # Option dataset        
        self.quote['PUT']        = {}
        self.quote['CALL']       = {}        
        for file in os.listdir('dataset/options/day'):
            if file.endswith(".csv"):
                date                = datetime.date(2000 + int(file[-10:-8]), int(file[-8:-6]), int(file[-6:-4]))
                thismonth           = date.strftime('%b-%y').upper()
                if date.month == 12:
                    nextmonth       = datetime.date(date.year + 1, 1, 1).strftime('%b-%y').upper()
                else:
                    nextmonth       = datetime.date(date.year, date.month + 1, 1).strftime('%b-%y').upper()
                df                  = pd.read_csv('dataset/options/day/' + file)
                df.rename(columns={'STRIKE PRICE':'K', '*OPENING PRICE.1':'OPENING PRICE'}, inplace=True)
                self.quote['PUT'] [date] = {
                        'DAY': {
                                thismonth: df.loc[(df['CONTRACT MONTH'] == thismonth) & (df['C/P'] == 'C')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                                nextmonth: df.loc[(df['CONTRACT MONTH'] == nextmonth) & (df['C/P'] == 'C')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                                },
                        'NIGHT': None
                        }
                self.quote['CALL'][date] = {
                        'DAY': {
                                thismonth: df.loc[(df['CONTRACT MONTH'] == thismonth) & (df['C/P'] == 'P')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                                nextmonth: df.loc[(df['CONTRACT MONTH'] == nextmonth) & (df['C/P'] == 'P')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                                },
                        'NIGHT': None
                        }   
        for file in os.listdir('dataset/options/night'):
            if file.endswith(".csv"):
                date                = datetime.date(2000 + int(file[-10:-8]), int(file[-8:-6]), int(file[-6:-4]))
                thismonth           = date.strftime('%b-%y').upper()
                if date.month == 12:
                    nextmonth       = datetime.date(date.year + 1, 1, 1).strftime('%b-%y').upper()
                else:
                    nextmonth       = datetime.date(date.year, date.month + 1, 1).strftime('%b-%y').upper()
                df                  = pd.read_csv('dataset/options/night/' + file)
                df.rename(columns={'STRIKE PRICE':'K', '*OPENING PRICE':'OPENING PRICE'}, inplace=True)
                self.quote['PUT'] [date]['NIGHT'] = {
                                thismonth: df.loc[(df['CONTRACT MONTH'] == thismonth) & (df['C/P'] == 'C')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                                nextmonth: df.loc[(df['CONTRACT MONTH'] == nextmonth) & (df['C/P'] == 'C')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                        }
                self.quote['CALL'][date]['NIGHT'] = {
                                thismonth: df.loc[(df['CONTRACT MONTH'] == thismonth) & (df['C/P'] == 'P')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                                nextmonth: df.loc[(df['CONTRACT MONTH'] == nextmonth) & (df['C/P'] == 'P')][['K', 'OPENING PRICE']].copy().reset_index(drop=True),
                        }
        # Report Valid Date
        print ('Dataset Range:', 'from', self.validstart, 'to', self.validend)
    
    
    # for option implied vol calcuation
    def d(self, sigma, S, K, r, t):
        d1 = 1 / (sigma * sqrt(t)) * ( log(S/K) + (r + sigma**2/2) * t)
        d2 = d1 - sigma * sqrt(t)
        return d1, d2

    def call_price(self, sigma, S, K, r, t, d, d1, d2):
        C = norm.cdf( d1) *  S  * exp(-d * t) + norm.cdf( d2) * -K * exp(-r * t)
        return C
    
    def put_price(self, sigma, S, K, r, t, d, d1, d2):
        C = norm.cdf(-d1) * -S  * exp(-d * t) + norm.cdf(-d2) *  K * exp(-r * t)
        return C
    
    def option_vol(self, time, option_type, S, K, C0, r = 0.0015, d = 0.0424):
        
        start   = time.date()
        end     = BMonthEnd().rollforward(start).date()
        t = (end-start).days/365.0        
        #  We need a starting guess for the implied volatility.  We chose 0.5
        #  arbitrarily.
        vol = 0.5
        
        epsilon = 1.0  #  Define variable to check stopping conditions
        abstol = 1e-4  #  Stop calculation when abs(epsilon) < this number
        
        i = 0   #  Variable to count number of iterations
        max_iter = 1e3  #  Max number of iterations before aborting
        
        while epsilon > abstol:
            #  if-statement to avoid getting stuck in an infinite loop.
            if i > max_iter:
                break        
            i = i + 1
            orig = vol
            d1, d2 = self.d(vol, S, K, r, t)
            if option_type == 'CALL':
                function_value = self.call_price(vol, S, K, r, t, d, d1, d2) - C0
            else:
                function_value = self.put_price (vol, S, K, r, t, d, d1, d2) - C0
            vega = S * norm.pdf(d1) * sqrt(t)
            vol = -function_value/vega + vol
            epsilon = abs(function_value)
        return vol
    
    def eqmkttrend(self, time, bear_margin = 0.02, bull_margin = 0.02):
        trend = None
        # check if data exists in dataset
        if time.date() not in self.quote['PUT']:
            return None
        # check if bullish or bearish market
        second = (time.timestamp() + 8 * 3600) % 86400
        # Month Symbol
        thismonth = time.strftime('%b-%y').upper()
        if time.month == 12:
            nextmonth       = datetime.date(time.year + 1, 1, 1).strftime('%b-%y').upper()
        else:
            nextmonth       = datetime.date(time.year, time.month + 1, 1).strftime('%b-%y').upper()
        # Trading Session
        if (second >= (9 * 3600 + 20 * 60)) and (second < (17 * 3600 + 15 * 60)):           # Day Session
            # HSI Underlying Price
            open_time  = datetime.datetime(time.year, time.month, time.day, 9, 15, 0)  
            session = 'DAY'
        else:                                                                               # Night Session
            open_time = datetime.datetime(time.year, time.month, time.day, 15, 15, 0) 
            session = 'NIGHT'
            
        # Option (around) ATM        
        open_price = self.quote['HSI'].loc[open_time].Close
        ref_price = 200 * int(open_price / 200) 
            
        # ATM exists
        if  ref_price == open_price:
            # Truncated Price
            put         = self.quote['PUT'][time.date()][session][thismonth]
            put_price   = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
            put_vol     = self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            put         = self.quote['PUT'][time.date()][session][thismonth]
            put_price   = int(put.loc[put['K'] == str(ref_price - 200)].iloc[0]['OPENING PRICE'])
            put_vol     = put_vol + self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            
#            put         = self.quote['PUT'][time.date()][session][nextmonth]
#            put_price   = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
#            put_vol     = put_vol + self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            
            call        = self.quote['CALL'][time.date()][session][thismonth]
            call_price  = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
            call_vol    = self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            call        = self.quote['CALL'][time.date()][session][thismonth]
            call_price  = int(put.loc[put['K'] == str(ref_price + 200)].iloc[0]['OPENING PRICE'])
            call_vol    = call_vol + self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            
#            call        = self.quote['CALL'][time.date()][session][nextmonth]
#            call_price  = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
#            call_vol    = call_vol + self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            # Decision
            if   put_vol > call_vol + bear_margin:
                trend = 'Bearish'
            elif put_vol + bull_margin < call_vol:
                trend = 'Bullish'
        # ATM not exists
        else:
            # Truncated Price
            put         = self.quote['PUT'][time.date()][session][thismonth]
            put_price   = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
            put_vol     = self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            put_price   = int(put.loc[put['K'] == str(ref_price - 200)].iloc[0]['OPENING PRICE'])
            put_vol     = put_vol + self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            put_price   = int(put.loc[put['K'] == str(ref_price - 400)].iloc[0]['OPENING PRICE'])
            put_vol     = put_vol + self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            
#            put         = self.quote['PUT'][time.date()][session][nextmonth]
#            put_price   = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
#            put_vol     = put_vol + self.option_vol(time, 'PUT', open_price, ref_price, put_price)
            
            ref_price   = ref_price + 200 # Truncated Price
            call        = self.quote['CALL'][time.date()][session][thismonth]
            call_price  = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
            call_vol    = self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            call_price  = int(put.loc[put['K'] == str(ref_price + 200)].iloc[0]['OPENING PRICE'])
            call_vol    = call_vol + self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            call_price  = int(put.loc[put['K'] == str(ref_price + 400)].iloc[0]['OPENING PRICE'])
            call_vol    = call_vol + self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            
#            call        = self.quote['CALL'][time.date()][session][nextmonth]
#            call_price  = int(put.loc[put['K'] == str(ref_price)].iloc[0]['OPENING PRICE'])
#            call_vol    = call_vol + self.option_vol(time, 'CALL', open_price, ref_price, put_price)
            print (put_vol, call_vol)
            # Decision
            if   put_vol > call_vol + bear_margin:
                trend = 'Bearish'
            elif put_vol + bull_margin < call_vol:
                trend = 'Bullish'
        
        print (session, put_vol, call_vol, trend)
        
        put         = self.quote['PUT'][time.date()][session][thismonth]
        put_vol     = {}
        for i in range(len(put)):
#                dates   = list(D.keys())           # list() needed for python 3.x
#                prices  = list(D.values())        # ditto
            put_price   = float(put.loc[i, 'OPENING PRICE'])
            put_vol[int(put.loc[i, 'K'])] = self.option_vol(time, 'PUT', open_price, ref_price, put_price)
        
        call        = self.quote['CALL'][time.date()][session][thismonth]
        call_vol    = {}
        for i in range(len(call)):
#                dates   = list(D.keys())           # list() needed for python 3.x
#                prices  = list(D.values())        # ditto
            call_price   = float(call.loc[i, 'OPENING PRICE'])
            call_vol[int(call.loc[i, 'K'])] = self.option_vol(time, 'CALL', open_price, ref_price, call_price)

        fig = plt.figure()
        
        plt.scatter(put_vol.keys(),  put_vol.values(),  label='put')
        plt.scatter(call_vol.keys(), call_vol.values(), label='call')
        plt.axvline(x = open_price)
        plt.legend(loc='best')
        plt.show()
        
        return trend
    
    # EQ Market Open Hours: 09:15 - 12:00, 13:00 - 16:30, 17:15 - 01:00    
    def is_eqmktopen(self, time):
        second = (time.timestamp() + 8 * 3600) % 86400
        if time.weekday() < 5:
            if second < 3600:
                return True
            if second >= 33600 and second < 43200:
                return True
            if second >= 46800 and second < 59700:
                return True
            if second >= 62100:
                return True
        return False
    
    # FX Market Open Hours: 00:00 - 23:59 Mon - Fri
    def is_fxmktopen(self, time):
        second = (time.timestamp() + 8 * 3600) % 86400
        if second >= 3601 and second <= 86100:
                return True
        return False
#        if time.weekday() < 5:
#            return True
#        return False
    
    # Commodity Market Open Hours: 01:01 - 23:55 Mon - Fri
    def is_commmktopen(self, time):
        second = (time.timestamp() + 8 * 3600) % 86400
        if time.weekday() < 5:
            if second >= 3601 and second <= 86100:
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
    def getoption(self, time, option_type, S, K, month, r = 0.0015, v = 0.25, d = 0.0424):
        # initialize call & put options
        template  = {
                'Premium'   : 0,
                'Delta'     : 0,
                'Theta'     : 0,
                'Gamma'     : 0,
                'Vega'      : 0,
                'Rho'       : 0,
                }
        call    = template
        put     = template
        # Days to Maturity
        start   = time.date()
        if month != 1:  # Jan Option is probably next year
            end     = BMonthEnd().rollforward(datetime.date(time.year, month, 1)).date()
        else:
            end     = BMonthEnd().rollforward(datetime.date(time.year + 1, month, 1)).date()
#        T           = np.busday_count(start, end)
        T           = (end - start).days
        # espired
        if T <= 0:
            return template        
        if K % 200 != 0: 
            error (time, 'Strike Price is in step of 200')
        # Time to expired
        Tt      = T / 365.0     # float for 2.7
        # Black Scholes d1 & d2
        d1      = (log (S / (K * exp(-r * Tt))) / (v * sqrt(Tt))) + 0.5 * v * sqrt(Tt)
        d2      = d1 - v * sqrt(Tt)
        # Premium = f
        call['Premium'] =  1.0 * S * exp(-1.0 * d * Tt) * self.norm_cdf( 1.0 * d1) - 1.0 * K * exp(-1.0 * r * Tt) * self.norm_cdf( 1.0 * d2)
        put['Premium']  = -1.0 * S * exp(-1.0 * d * Tt) * self.norm_cdf(-1.0 * d1) + 1.0 * K * exp(-1.0 * r * Tt) * self.norm_cdf(-1.0 * d2)
        # Delta = df / dS
        call['Delta']   =  1.0 * exp(-1.0 * d * Tt) * self.norm_cdf( 1.0 * d1)
        put['Delta']    = -1.0 * exp(-1.0 * d * Tt) * self.norm_cdf(-1.0 * d1)
        # Gamma = d2f/dS2
        call['Gamma']   = (((1.0 / sqrt(2*pi)) * exp(((-1 * pow(d1, 2)) / 2))) * exp(-1 * Tt * d)) / (S * v * sqrt(Tt))
        put['Gamma']    = call['Gamma']
        # Theta 
        call['Theta']   = ((((-1.0*((((S*((1.0/sqrt((2.0*pi)))*exp(((-1.0*pow(d1,2))/2.0))))*v)*exp(((-1.0*Tt)*d)))/(2.0*sqrt(Tt))))+((d*S)*call['Delta']))-(((r*K)*exp(((-1*r)*Tt)))*self.norm_cdf(d2))))/365.0
        put['Theta']    = (((((-1.0*((((S*((1.0/sqrt((2.0*pi)))*exp(((-1.0*pow(d1,2))/2.0))))*v)*exp(((-1.0*Tt)*d)))))/(2.0*sqrt(Tt)))-(((d*S)*self.norm_cdf((-1.0*d1)))*exp(((-1.0*Tt)*d))))+(((r*K)*exp(((-1.0*r)*Tt)))*self.norm_cdf((-1.0*d2)))))/365.0
        # Vega
        call['Vega']    = (((((1.0/sqrt((2.0*pi)))*exp(((-1.0*pow(d1,2))/2.0)))*exp(((-1.0*Tt)*d)))*S)*sqrt(Tt))/100.0
        put['Vega']     = call['Vega']
        # Rho
        call['Rho']     = ((((K*Tt)*exp(((-1.0*r)*Tt)))*self.norm_cdf(d2))*exp(((-1.0*d)*Tt)))/100.0
        put['Rho']      = (((((-1.0*K)*Tt)*exp(((-1.0*r)*Tt)))*self.norm_cdf((-1.0*d2)))*exp(((-1.0*d)*Tt)))/100.0
        
        if option_type == 'CALL':
            option = call
        else:
            option = put
        return option
    
#        if option['Premium'] <= 0.0:
#            return 0.0
#        else:
#            return option
        
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
        if rate == 0:                                   # Avoid Zero Division
            return 0
        elif product.startswith('USD'):                 # Change to HKDXXX
            return (self.quote['USDHKD'].loc[time].Ask / rate)
        elif product.startswith('HKD'):
#            return (1 / rate)
            return (rate / self.quote[product].loc[time].Bid)
        elif product.endswith  ('USD'):                 # Change to XXXHKD
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
    
    def opencheck(self, time, product, pos, qty, K, T, rate, cash): 
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
                if rate == 0:
                    error (time, 'Cannot purchase option on last date: 0 value')
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
                    rate                                        = self.getoption(time, product, self.quote['HSI'].loc[time].Close, strike, maturity)['Premium']
                    if rate == 0:                                                                                                               # probably last date of month, Switch to next month option
                        if maturity < 12:                                                                                                       # increment if not Dec
                            maturity                            = maturity + 1
                        else:                                                                                                                   # set to Jan otherwise
                            maturity                            = 1
                        rate                                    = self.getoption(time, product, self.quote['HSI'].loc[time].Close, strike, maturity)['Premium']
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
            self.opencheck(time, product, pos, qty, K, T, rate, self.portfolio['cash'])
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
                        self.trading_log.loc[i, 'Close Rate']   = self.getoption(time, self.trading_log.loc[i, 'Product'], self.quote['HSI'].loc[time].Close, self.trading_log.loc[i, 'Strike'], self.trading_log.loc[i, 'Maturity'])['Premium']
                    else:
                        self.trading_log.loc[i, 'Close Rate']   = self.getrate(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Position'])
                        
                    self.trading_log.loc[i, 'Unrealized P&L']   = 0
                    
                    if self.trading_log.loc[i, 'Position'] == 'LONG':
                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, self.trading_log.loc[i, 'Product'], (self.trading_log.loc[i, 'Close Rate'] - self.trading_log.loc[i, 'Open Rate'])) - self.trading_log.loc[i, 'Handling']
#                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * (self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Close Rate']) - self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Open Rate'])) - self.trading_log.loc[i, 'Handling']
                    else:
                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, self.trading_log.loc[i, 'Product'], (self.trading_log.loc[i, 'Open Rate'] - self.trading_log.loc[i, 'Close Rate'])) - self.trading_log.loc[i, 'Handling']
#                        self.trading_log.loc[i, 'Realized P&L'] = self.trading_log.loc[i, 'Qty'] * (self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Open Rate']) - self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Close Rate'])) - self.trading_log.loc[i, 'Handling']
                    
                    self.trading_log.loc[i, 'P&L%']             = float((self.trading_log.loc[i, 'Unrealized P&L'] + self.trading_log.loc[i, 'Realized P&L']) / (self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Open Rate'])) * 100)

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
            if (product == 'PUT' or product == 'CALL'):
                rate                                            = self.getoption(time, product, self.quote['HSI'].loc[time].Close, self.trading_log.loc[i, 'Strike'], self.trading_log.loc[i, 'Maturity'])['Premium']
                last_option_date = BMonthEnd().rollforward(datetime.date(time.year, time.month, 1)).date()
                if time.month == self.trading_log.loc[i, 'Maturity'] and time.date() == last_option_date and not self.trading_log.loc[i, 'Close Date']:  
                    self.trading_log.loc[i, 'Close Date']       = time        
                    self.trading_log.loc[i, 'Close Rate']       = rate
                    self.trading_log.loc[i, 'Unrealized P&L']   = 0                    
                    # Long Position - throw the option away
                    premium = 0     # Cost of Option
                    skdelta = 0     # Difference between Strike and Current Prices
                    if self.trading_log.loc[i, 'Position'] == 'LONG':
                        premium = self.forextohkd(time, product, (self.trading_log.loc[i, 'Close Rate'] - self.trading_log.loc[i, 'Open Rate']))
                        if self.trading_log.loc[i, 'Product'] == 'PUT':
                            # Option is valid
                            if self.trading_log.loc[i, 'Strike'] > self.quote['HSI'].loc[time].Close:
                                skdelta = self.trading_log.loc[i, 'Strike'] - self.quote['HSI'].loc[time].Close
                        else:
                            # Option is valid
                            if self.trading_log.loc[i, 'Strike'] < self.quote['HSI'].loc[time].Close:
                                skdelta = self.quote['HSI'].loc[time].Close - self.trading_log.loc[i, 'Strike']
                    # Short Position - Obligation if pay for incurred loss
                    else:
                        premium = self.forextohkd(time, product, (self.trading_log.loc[i, 'Open Rate'] - self.trading_log.loc[i, 'Close Rate']))
                        if self.trading_log.loc[i, 'Product'] == 'PUT':
                            # if Option is valid
                            if self.trading_log.loc[i, 'Strike'] > self.quote['HSI'].loc[time].Close:
                                skdelta = self.quote['HSI'].loc[time].Close - self.trading_log.loc[i, 'Strike']
                        else:
                            # if Option is valid
                            if self.trading_log.loc[i, 'Strike'] < self.quote['HSI'].loc[time].Close:
                                skdelta = self.trading_log.loc[i, 'Strike'] - self.quote['HSI'].loc[time].Close
                    self.trading_log.loc[i, 'Realized P&L']     = self.trading_log.loc[i, 'Qty'] * (premium + skdelta) - self.trading_log.loc[i, 'Handling']
                    self.trading_log.loc[i, 'P&L%']             = float((self.trading_log.loc[i, 'Unrealized P&L'] + self.trading_log.loc[i, 'Realized P&L']) / (self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate'])) * 100)
                    # Get Cash        
                    self.portfolio['cash']                      = self.portfolio['cash'] + (self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate']) * self.trading_log.loc[i, 'Qty']) - self.portfolio['fee']
                    self.portfolio['cash']                      = self.portfolio['cash'] + self.trading_log.loc[i, 'Realized P&L']                  
                    # Report
                    print (time, 'Avl.Cash:', round(self.portfolio['cash']), self.trading_log.loc[i, 'Product'], 'CLOSE', self.trading_log.loc[i, 'Qty'], 'Mature @', self.quote['HSI'].loc[time].Close)
                    # Enough $?
                    if self.portfolio['cash'] <= 0:
                        error (time, 'No more Money...')
            else:                
                rate                                            = self.getrate(time, self.trading_log.loc[i, 'Product'], self.trading_log.loc[i, 'Position'])
                    
            if not self.trading_log.loc[i, 'Close Date']:
                
                self.trading_log.loc[i, 'Realized P&L']         = 0
                
                if self.trading_log.loc[i, 'Position'] == 'LONG':
                    self.trading_log.loc[i, 'Unrealized P&L']   = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, (rate - self.trading_log.loc[i, 'Open Rate'])) - self.trading_log.loc[i, 'Handling'] * 2
#                    self.trading_log.loc[i, 'Unrealized P&L']   = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, rate) - self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate']) - self.trading_log.loc[i, 'Handling'] * 2
                else:
                    self.trading_log.loc[i, 'Unrealized P&L']   = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, (self.trading_log.loc[i, 'Open Rate'] - rate)) - self.trading_log.loc[i, 'Handling'] * 2
#                    self.trading_log.loc[i, 'Unrealized P&L']   = self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate']) - self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, rate) - self.trading_log.loc[i, 'Handling'] * 2
                
                self.trading_log.loc[i, 'P&L%']                 = (self.trading_log.loc[i, 'Unrealized P&L'] + self.trading_log.loc[i, 'Realized P&L']) / (self.trading_log.loc[i, 'Qty'] * self.forextohkd(time, product, self.trading_log.loc[i, 'Open Rate']))
        
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
        # Deep Copy to avoid retest tendence
        return self.portfolio.copy(), self.trading_log.copy()
    
    def plot(self, products):  
        has_volume = False
        color = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']
        ln = None
        ax = {}
        ln = {}
        fig = plt.figure()
        #ax1 = fig.add_subplot(111)
        ax[products[0]] = fig.add_subplot(111)
        for i in range(len(products)):
            if i > 0:
                ax[products[i]] = ax[products[0]].twinx()  # instantiate a second axes that shares the same x-axis
            ax[products[i]].set_xlabel('time (s)')
            ax[products[i]].set_ylabel(products[i], color=color[i])
            if self.datainfo[products[i]] == 'FX':
                ln[products[i]] = ax[products[i]].plot(self.quote[products[i]].index, self.quote[products[i]].Bid, color=color[i], label = products[i])
            elif self.datainfo[products[i]] == 'EQ' and has_volume == False:
                has_volume = True
                ln[products[i]] = ax[products[i]].plot(self.quote[products[i]].index, self.quote[products[i]].Volume, color=color[i], label = products[i])
            else:
                ln[products[i]] = ax[products[i]].plot(self.quote[products[i]].index, self.quote[products[i]].Close, color=color[i], label = products[i])
            ax[products[i]].tick_params(axis='y', labelcolor=color[i])
            if i > 0:
                lns = lns + ln[products[i]]
            else:
                lns = ln[products[0]]
        #lns = ln1+ln2+ln3+ln4
        labs = [l.get_label() for l in lns]
        ax[products[0]].legend(lns, labs, loc='best')
        plt.show()