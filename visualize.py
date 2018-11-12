# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 12:02:24 2018

@author: SF
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
#%% Plot the desired products
products = [
        'HSI',
#        'VHSI',
#        '0005.HK',
#        '0700.HK',
        'XAUHKD',
        ]
platform.plot(products)