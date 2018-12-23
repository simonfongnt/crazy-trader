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
 
    Trading must be within trading hours
    
    Trading must be with sufficnet cash
    
    Option Strike Price is in step of 200
    
There are also assumptions on incurred cost and price calculation as well.
    
Assumptions:
    
    Option premium is calculated by Black-Scholes formula with HSI price, Strike price, maturity, interest rate & dividend yield
    
    Based on HKEX assumption, Interest rate is 0.15% and dividend yield is 4.24%, per year
    
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
    
    Quotation (Forex, Commodity, Crypto):
    
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
    
# Performance
Performance measures the statistic achieved by the trading record. The metrics are average trade, largest win, largest loss, win/loss ratio and max drawdown (MDD) shown as follows:

| Sector         | Return (%)     | Win/Loss Ratio | Largest Win    | Largest Loss   |
| -------------- | -------------- | -------------- | -------------- | -------------- |
| EQ             | 3.08           | 0.76           | 77050          | -107450        |
| FX             | 21.57          | 2/0            | 545200         | N/A            |
| Crypto         | 43.05          | 1.80           | 214162         | -23225         |

|                | Return (%)     | Win/Loss Ratio | Average Trade  | MDD            |
| -------------- | -------------- | -------------- | -------------- | -------------- |
| Portfolio      | 14.47          | 0.84           | 8823           | 1.3%           |

Table 8-1 Detailed Portfolio Performance

With initial 10B HKD investment, the overall return was 1.44B HKD from 1st Sep 2018 to 1st Dec 2018 which is 14.47%. The exposure for HKDTRY Forex was expecting the least return and most of the exposure was focused on equity sector. However, the resultant portfolio was mainly gained from Forex (8% of portfolio) and Crypto sectors (4% of portfolio) and, fortunately, Forex did not require to switch exposure to commodity sector in gold future. 

Since the HSI trading is day trade and the strategies consists of 1% stoploss condition, the drawdown is limited with reasonably profit. Hence the maximum drawdown of the portfolio is 1.3% which is considered to be the worth for investment.

The strategy for HSI derivative trading was not optimized as expected. Although the market view suggested to employ option chain data to indicate the volatility and trend of the HSI future, this function was unable to be implemented because of vast quantity of minutes data of HSI options. The trend and volatility indicators were based on Volume-Price Trends and VHSI respectively. Thereof the performance was not ideal with single indicator for each of them.
 
# Conclusion
The portfolio achieved 14.47% profits with top-down analysis plus numerous trading strategies on various instruments/products. The HSI derivative strategy has to be optimized by employing multiple indicators for trend and volatility indications. There is an idea to utilize the option chain which requires high amount of option chain minutes data for training and a period of time for calibration and backtesting, as the indicators as well. 

|                | Return (%)     | Win/Loss Ratio | Average Trade  | MDD            |
| -------------- | -------------- | -------------- | -------------- | -------------- |
| Portfolio      | 14.47          | 0.84           | 8823           | 1.3%           |

Table 9-1 Portfolio Performance

The global market shall remain bearish next season because of the balance sheet unwinding, US-China trade war and Brexit settlement. The possibility of another rise of tariffs by US on China’s export remains high and there is a sign of hard Brexit between UK and Europe in March. The Hong Kong market will thus continue to be affected by both of the events and in bearish trend as well.

Nonetheless, the performance of this portfolio depends on HSI derivatives trading strategy efficiency, Turkish economic recovery, cryptocurrency market status in near future. Since the HKDTRY forex is approaching to the level of August that before the US tariff sanction, the expected return of this asset may be lower with existing event-driven strategy. After the regulation on cryptocurrency market, the bearish market trend is expected to be continued so the portfolio shall remain efficient in the near future.

