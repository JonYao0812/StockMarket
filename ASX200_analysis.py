import bs4 as bs
import pickle
import requests
import pandas as pd
import datetime as dt
import os
import pandas_datareader.data as web
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
from collections import Counter

from sklearn import svm, neighbors
from sklearn.ensemble import VotingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split



def save_asx200_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/S%26P/ASX_200')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'wikitable sortable'})
    
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        ticker = ticker.strip("\n")+".AX"
        tickers.append(ticker)
    
    tickers.remove('MYO.AX')
        
    with open("asx200tickers.pickle","wb") as f:
        pickle.dump(tickers,f)

    return tickers

#save_asx200_tickers()

def get_data_from_yahoo(relod_asx200=False):
    if relod_asx200:
        tickers = save_asx200_tickers()
    else:
        with open("/Users/chengzhongito/Desktop/python-finance/asx200tickers.pickle","rb") as f:
            tickers = pickle.load(f)

    if not os.path.exists('stock_dfs'):
        os.makedirs('stock_dfs')

    start = dt.date(2015,6,30)
    end = dt.date(2019,6,30)
    
    for ticker in tickers:
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)):
            df = web.DataReader(ticker, 'yahoo', start, end)
            df.reset_index(inplace=True)
            df.set_index("Date", inplace=True)
            df.to_csv('stock_dfs/{}.csv'.format(ticker))
        else:
            print('Already have {}'.format(ticker))


#get_data_from_yahoo()


def compile_data():
    with open('asx200tickers.pickle','rb') as f:
        tickers = pickle.load(f)
        
    main_df = pd.DataFrame()
        
    for count,ticker in enumerate(tickers):
        df = pd.read_csv('stock_dfs/{}.csv'.format(ticker))
        df.set_index('Date', inplace = True)
        
        df.rename(columns = {'Adj Close':ticker}, inplace = True)
        df.drop(['Open','High','Close','Low','Volume'],axis=1,inplace=True)
        
        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how='outer')
            
        if count%10 == 0:
            print(count)
            
    print(main_df.head())
    main_df.to_csv('asx200_joined_closes.csv')
        
##compile_data()

style.use('ggplot')

def visualise_data():
    df = pd.read_csv('asx200_joined_closes.csv')
#    df["APT.AX"].plot()
#    plt.legend()
#    plt.show()
    # df = df[["APT.AX"]]
    df_corr = df.corr()
#    print(df_corr.head())

    data = df_corr.values
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    heatmap = ax.pcolor(data, cmap=plt.cm.RdYlGn)
    fig.colorbar(heatmap)
    
    ax.set_xticks(np.arange(data.shape[0]) + 0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[1]) + 0.5, minor=False)
    
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    
    column_labels = df_corr.columns
    row_labels = df_corr.index
    
    ax.set_xticklabels(column_labels)
    ax.set_yticklabels(row_labels)
    
    plt.xticks(rotation=90)
    heatmap.set_clim(-1,1)
    plt.tight_layout()
    plt.show()

    
def process_data_for_labels(ticker):
    
    hm_days = 7
    df = pd.read_csv('asx200_joined_closes.csv', index_col = 0)
    tickers = df.columns.values.tolist()
    df.fillna(0, inplace=True)

    for i in range(1,hm_days+1):
        df['{}_{}d'.format(ticker,i)] = (df[ticker].shift(-i) - df[ticker]) / df[ticker]

    df.fillna(0, inplace=True)
    print(df)
    return tickers, df

def buy_sell_hold(*args):
    cols = [c for c in args]
    requirement = 0.03
    
    for col in cols:
        if col>0.03:
            return 1
        if col < -0.15:
            return -1
        
    return 0

def extract_featuresets(ticker):
    tickers, df = process_data_for_labels(ticker)

    df['{}_target'.format(ticker)] = list(map( buy_sell_hold,
                                               df['{}_1d'.format(ticker)],
                                               df['{}_2d'.format(ticker)],
                                               df['{}_3d'.format(ticker)],
                                               df['{}_4d'.format(ticker)],
                                               df['{}_5d'.format(ticker)],
                                               df['{}_6d'.format(ticker)],
                                               df['{}_7d'.format(ticker)] ))
    vals = df['{}_target'.format(ticker)].values.tolist()
    str_vals = [str(i) for i in vals]
    print('Data spread:',Counter(str_vals))
    
    df.fillna(0, inplace=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    df.dropna(inplace=True)
    
    df_vals = df[[ticker for ticker in tickers]].pct_change()
    df_vals = df_vals.replace([np.inf, -np.inf], 0)
    df_vals.fillna(0, inplace=True)

    ticker_feature = df_vals.values
    ticker_target = df['{}_target'.format(ticker)].values
    return ticker_feature, ticker_target, df



def execute_ml(ticker):
    ticker_feature, ticker_target, df = extract_featuresets(ticker)
    ticker_feature_train, ticker_feature_test, ticker_target_train, ticker_target_test = train_test_split(ticker_feature, ticker_target, test_size=0.25, random_state=42)
    #clf = neighbors.KNeighborsClassifier()
    clf = VotingClassifier([('lsvc',svm.LinearSVC()),
                            ('knn',neighbors.KNeighborsClassifier()),
                            ('rfor',RandomForestClassifier())])
    
    clf.fit(ticker_feature_train, ticker_target_train)
    confidence = clf.score(ticker_feature_test, ticker_target_test)
    print('Accuracy: ',confidence)
    prediction = clf.predict(ticker_feature_test)
    print('Predicted spread: ', Counter(prediction))
    
    return confidence

#execute_ml('APT.AX')
#visualise_data()  
extract_featuresets('APT.AX')  
    
    
