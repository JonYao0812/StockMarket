#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 19:18:18 2019

@author: chengzhongito
"""

import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import style
import pandas as pd
import pandas_datareader.data as web
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates

style.use('ggplot')


def read_data(company):
    
    start = dt.datetime(2015, 1, 1)
    end = dt.datetime.now()
    
    df = web.DataReader(company, 'yahoo', start, end)
    df.reset_index(inplace=True)
    df.set_index("Date", inplace=True)
    df.to_csv('{}.csv'.format(company))
    
    visualize_data(df)

def visualize_data(company_df):
    
    df_adjClose = company_df[['Adj Close']]
    company_df['20ma'] = df_adjClose.rolling(20).mean()
    company_df['60ma'] = df_adjClose.rolling(60).mean()
    
    df_volume = company_df['Volume']
    df_ohlc = company_df.drop(['Adj Close','Volume'], axis=1)
    df_ohlc.reset_index(inplace=True)
    df_ohlc=df_ohlc[['Date','Open','High','Low','Close']]

#Set up graph
    df_ohlc['Date'] = df_ohlc['Date'].map(mdates.date2num)
    ax1 = plt.subplot2grid((6,1), (0,0), rowspan=5, colspan=1)
    ax2 = plt.subplot2grid((6,1), (5,0), rowspan=1, colspan=1, sharex=ax1)
    #ax1.xaxis_date()
   
    ax1.set_xticklabels([])
    ax1.plot(company_df['20ma'],linewidth = 0.4, label='20MA')  
    ax1.plot(company_df['60ma'],linewidth = 0.4, color = 'b',label='60MA')
    ax2.set_xlim([dt.datetime(2019, 1, 1), dt.datetime.now()])
    
#Set bar colors
    up_index = company_df['Open'] - company_df['Close'] > 0 
    down_index = company_df['Open'] - company_df['Close'] < 0 
    ax2.bar(company_df.index[up_index], df_volume[up_index],color = 'g',label='Volume')
    ax2.bar(company_df.index[down_index], df_volume[down_index],color='r', label='Volume')

#Volume MA
    company_df['volume_20ma'] = df_volume.rolling(20).mean()
    company_df['volume_60ma'] = df_volume.rolling(60).mean()
    ax2.plot(company_df['volume_20ma'],linewidth = 0.4)  
    ax2.plot(company_df['volume_60ma'],linewidth = 0.4, color = 'b')
    
    candlestick_ohlc(ax1, df_ohlc.values, width=0.2, colorup='r',colordown='g')
    plt.xticks(rotation=45)
    
    
    ax1.legend()
    leg = ax1.legend(loc=2,prop={'size':11})
    leg.get_frame().set_alpha(0.4)
    
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.show()
    
    
read_data('APT.AX')
    