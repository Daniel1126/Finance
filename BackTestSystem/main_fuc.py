# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 09:14:35 2019

@author: Daniel
"""
from data import Crawler
from talib import Indicator,BackTestFrame,Evaluation
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

class Strategy:
    def __init__(self,df):
        self.df = df
    
    def ema_strategy(self):
        df = self.df.copy()
        ema_list = [8,21]
        df = Indicator(df).ema(period=ema_list)
        df['signal'] = np.nan
        df['signal'][df['ema_%s'%min(ema_list)] > df['ema_%s'%max(ema_list)]] = 1
        df['signal'][df['ema_%s'%min(ema_list)] < df['ema_%s'%max(ema_list)]] = -1
        df['position'] = df.signal.shift(1)
        df.position.fillna(0,inplace=True)
        df = BackTestFrame(df).run_us()  # 调用回测框架，回测过程中的滑点和佣金均需要再框架中自己修改
        evaluation = Evaluation(df).evaluation()
        plt.figure(figsize=(15,9),dpi=300)
        plt.plot(range(len(df.time)),df.npv,label='npv')
        plt.plot(range(len(df.time)),df.close / df.loc[0,'close'],label='close')
        plt.title('trading strategy test')
        plt.legend()
        plt.grid(True)
        plt.savefig('result_stock.png')
        plt.show()
        for k,v in evaluation.items():
            print(k,':',v)
        
        return df
    
    def ma_std_break(self):
        df = self.df
        df['ma_10'] = df.close.rolling(10).mean()
        df['std_10'] = df.close.rolling(10).std()
        df = df.loc[9:,:]
        df.reset_index(inplace=True)
        df = df.drop('index',axis=1)
        df['signal'] = np.nan
        df['signal'][df.close -  (df.ma_10+ df.std_10) > 0] = -1
        df['signal'][df.close -  (df.ma_10 - df.std_10) < 0] = 1
        df['signal'][(df.close < df.ma_10 + 0.2 * df.std_10) & \
                     (df.close > df.ma_10 - 0.2 * df.std_10)] = 0
        df.signal.fillna(method = 'ffill',inplace=True)
        df['position'] = df.signal.shift(1)
        df.position.fillna(0,inplace=True)
        df['pct'] = df.close.pct_change()
        
        df = BackTestFrame(df).run_us()  # 调用回测框架，回测过程中的滑点和佣金均需要再框架中自己修改
        evaluation = Evaluation(df).evaluation()
        plt.figure(figsize=(15,9),dpi=300)
        plt.plot(range(len(df.time)),df.npv,label='npv')
        plt.plot(range(len(df.time)),df.close / df.loc[0,'close'],label='close')
        plt.title('trading strategy test')
        plt.legend()
        plt.grid(True)
        plt.savefig('result_stock.png')
        plt.show()
        for k,v in evaluation.items():
            print(k,':',v)
        
        return df
    
if __name__ == '__main__':
    df = Crawler(symbol='fb',begin='20190719',period='day',type_='before',count=1000,indicator='').request()   
    df = Strategy(df).ema_strategy()