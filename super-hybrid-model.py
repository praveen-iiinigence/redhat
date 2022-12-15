
from mplfinance.original_flavor import candlestick_ohlc
import csv
import pandas as pd

import ta
import math
import matplotlib.pyplot as plt
import mplfinance
import matplotlib.dates as mpl_dates
from datetime import datetime
import os
import cv2
from collections import deque
from operator import itemgetter


def plot_graph(data):

    plt.plot(data, 'g-')
    plt.show()


def get_slope(data, i, j):
    return (data.iloc[j]-data.iloc[i])/(j-i)


def is_all_profit(principle):

    for i in range(len(principle)):
        if principle[i] < 100:
            return False
    return True


def accuracy(trade_history):
    pos = 0
    neg = 0
    if len(trade_history) == 0:
        return 0, 0, 0
    for i in range(len(trade_history)):
        if(trade_history[i]['profit']) > 0:
            pos = pos+1
        else:
            neg = neg+1
    return pos, neg, pos/len(trade_history)


def plot_candle_chart(data, trade_history):
    # mplfinance.plot(data, type="candle", style="yahoo")

    _data = []
    for i in range(len(data)):
        _data.append(data.iloc[i][:5])

    plt.style.use('ggplot')
    plt.close('all')
    fig = plt.figure(figsize=(32, 8))
    ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
    ax1.clear()
    candlestick_ohlc(ax1, _data, width=0.8/24,
                     colorup='green', colordown='red', alpha=0.8)
    ax1.xaxis.set_major_formatter(mpl_dates.DateFormatter('%d-%m-%Y'))
    fig.autofmt_xdate()

    # # sort sell and buy orders, put arrows in appropiate order positions
    for i in range(len(trade_history)):
        trade = trade_history[i]
        if trade['position']==0:

            trade_date = data.iloc[trade['entryIndex']]['date']

            high_low = data.iloc[trade['entryIndex']]['low']-10
            ax1.scatter(trade_date, high_low, c='green', label='green',
                        s=120, edgecolors='none', marker="^")

            trade_date_2 = data.iloc[trade['exitIndex']]['date']

            high_low_2 = data.iloc[trade['exitIndex']]['high']+10
            ax1.scatter(trade_date_2, high_low_2, c='red', label='red',
                        s=120, edgecolors='none', marker="v")
        if trade['position']==1:
            #ENTRY            
            trade_date = data.iloc[trade['entryIndex']]['date']

            high_low = data.iloc[trade['entryIndex']]['low']-10
            ax1.scatter(trade_date, high_low, c='purple', label='purple',
                        s=120, edgecolors='none', marker="^")
            #EXIT
            trade_date_2 = data.iloc[trade['exitIndex']]['date']

            high_low_2 = data.iloc[trade['exitIndex']]['high']+10
            ax1.scatter(trade_date_2, high_low_2, c='black', label='black',
                        s=120, edgecolors='none', marker="v")
            
    plt.show()


def timestamp_to_date(data):
    _date = []
    for i in range(len(data)):

        _date.append(mpl_dates.date2num(
            [pd.to_datetime(datetime.fromtimestamp(int(data.iloc[i]/1000)))])[0])

    return _date





# FUNCTION WILL WAIT OR RUSH TO CHANGE THE POSITION

def tradeV5(data, ma_period, lookup_period, faster, stop_loss):
    MA = ta.trend.SMAIndicator(data["close"], ma_period)
    ma = MA.sma_indicator()
    total_profit = 0
    total_loss = 0
    _max = -1
    for i in range(len(ma)):

        if(math.isnan(ma.iloc[i])):
            _max = i
        else:
            break

    if(not (_max == -1)):
        data = data[_max+1:]
        ma = ma[_max+1:]

    pos_slope = 0
    neg_slope = 0

    # lookup
    for i in range(1, lookup_period):
        slope = get_slope(ma, i-1, i)
        if slope > 0:
            pos_slope += slope
        else:
            neg_slope -= slope

    bought = False  # IN A TRADE OR NOT
    position = 0  # CURRENT POSITION 0 - LONG AND 1 - SHORT
    principle = 100
    entry = 0
    trade_history = []
    purchaseIndex = 0
    max_realized = 0

    for i in range(lookup_period, len(data)):

        slope = get_slope(ma, i-1, i)

        if slope > 0:
            pos_slope += slope
        else:
            neg_slope -= slope

        prev_slope = get_slope(ma, i-lookup_period, i-lookup_period+1)

        if prev_slope > 0:
            pos_slope -= prev_slope
        else:
            neg_slope += prev_slope

        if bought == False:
            if pos_slope > neg_slope:
                position = 0
            else:
                position = 1
            bought = True
            entry = data.iloc[i]['close']
            purchaseIndex = i
            max_realized = entry
            continue
        else:
            exit = data.iloc[i]['close']
            if position == 0 and exit > max_realized:
                max_realized = exit

            if position == 1 and exit < max_realized:
                max_realized = exit

            if position == 0 and (pos_slope*(faster/100) < neg_slope or exit <= max_realized*((100-stop_loss)/100)):
                bought = False

                p = (((exit-entry)/entry)*100)-0.15

                principle = principle+((p*principle)/100)
                trade_history.append({'purchase_price': entry, 'selling_price': exit,  'position': position, 'entryIndex': purchaseIndex, "exitIndex": i,
                                      'principl': principle,
                                      'profit': p})
                if p > 0:
                    total_profit += p
                else:
                    total_loss += p

            elif position == 1 and (pos_slope > neg_slope*(faster/100 or exit >= max_realized*((100+stop_loss)/100))):
                bought = False
                p = (((entry-exit)/entry)*100)-0.15
                principle = principle+((p*principle)/100)
                trade_history.append({'purchase_price': entry, 'position': position, 'position': position, 'selling_price': exit, 'entryIndex': purchaseIndex, "exitIndex": i,
                                      'principl': principle,
                                      'profit': p})
                if p > 0:
                    total_profit += p
                else:
                    total_loss += p

            continue
    if bought == True:
        if position == 0:
            bought = False
            exit = data.iloc[-1]['close']
            p = (((exit-entry)/entry)*100)-0.15
            principle = principle+((p*principle)/100)
            trade_history.append({'purchase_price': entry, 'selling_price': exit,  'position': position, 'entryIndex': purchaseIndex, "exitIndex": len(data)-1,
                                  'principl': principle,
                                  'profit': p})

        else:
            bought = False
            exit = data.iloc[-1]['close']
            p = (((entry-exit)/entry)*100)-0.15
            principle = principle+((p*principle)/100)
            trade_history.append({'purchase_price': entry, 'selling_price': exit,  'position': position, 'entryIndex': purchaseIndex, "exitIndex": len(data)-1,
                                  'principl': principle,
                                  'profit': p})

    # plot_graph(ma)
    # print(trade_history,len(trade_history))

    # plot_candle_chart(data, trade_history)
    return principle, trade_history


trading_pair = "bnb"

data = pd.read_csv(trading_pair+'-1h-2018.csv')

trade_period = 8200
ma_period = 10
best_model = pd.DataFrame()

# best_model = pd.read_csv(trading_pair+'-out.csv')

# print(best_model)
for lookup_period in range(84, 241, 12):

    for ma_period in range(6, 481, 6):
        if lookup_period == 84 and ma_period <= 84:
            continue
        print(lookup_period, ma_period)
        for faster in range(80, 151, 10):
            for stoploss in range(2, 16, 1):
                _principle = []

                for i in range(0, len(data), trade_period):
                    if len(data[i:i+trade_period]) == trade_period:
                        principle, trade_history = tradeV5(
                            data[i:i+trade_period], ma_period, lookup_period, faster, stoploss)
                        _principle.append(principle)

                if(is_all_profit(_principle)):

                    print(lookup_period, ma_period, faster, _principle)
                    principle, trade_history = tradeV5(
                        data, ma_period, lookup_period, faster, stoploss)
                    print(principle, len(trade_history),
                          accuracy(trade_history))
                    _new_model = pd.DataFrame(
                        [{'lookup': lookup_period, 'ma': ma_period, 'faster': faster, 'principle': principle, 'stoploss': stoploss}])
                    best_model = pd.concat(
                        [best_model, _new_model], ignore_index=True)

                    best_model.to_csv(trading_pair+'-out-stoploss.csv')
