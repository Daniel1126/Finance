# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 13:42:28 2019

@author: Daniel
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import re
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')
mpl.rcParams['font.sans-serif']=['SimHei']
mpl.rcParams['axes.unicode_minus']=False
plt.style.use('fivethirtyeight')
np.random.seed(777)

def basic_analysis(data):
    '''
    data 是包含数据的字典，具体格式如下：
    data = {'symbol':DataFrame}
    DataFrame 至少包含时间,价格和代码 --> columns = ['time','close','symbol']
    '''
    table = basicDataProcessing(data)
    plt.figure(figsize=(14, 7))
    for c in table.columns.values:
        plt.plot(table.index, table[c], lw=3, alpha=0.8,label=c)
    plt.legend(loc='upper left', fontsize=12)
    plt.ylabel('price in $')
    
    returns = table.pct_change()
    plt.figure(figsize=(14, 7))
    for c in returns.columns.values:
        plt.plot(returns.index, returns[c], lw=3, alpha=0.8,label=c)
    plt.legend(loc='upper right', fontsize=12)
    plt.ylabel('daily returns')
    
def basicDataProcessing(data):
    '''
    data 为DataFrame，必须保证所有的数据都在一个DataFrame上
    DataFrame 至少包含时间和价格 --> columns = ['time','close'，'symbol']
    '''
    if not isinstance(data,pd.DataFrame):
        raise TypeError('请输入正确的数据格式 --> DataFrame')
    elif not isinstance(data.time[0],datetime):
        pattern = re.compile('\d+',re.S)
        data.time = data.time.\
        apply(lambda x:datetime.strptime(''.join(re.findall(pattern,x)),'%Y%m%d'))
        
    df = data.set_index('time')
    table = df.pivot(columns='symbol',values='close')
    
    return table
    
class Analysis(object):
    def __init__(self,data,num_portfolios=25000,risk_free_rate=0.0178):
        '''
        data 是包含数据的字典，具体格式如下：
        data = {'symbol':DataFrame}
        DataFrame 至少包含时间和价格 --> columns = ['time','close']
        num_portfolios --> 需要模拟的组合的次数
        risk_free_rate --> 无风险利率
        '''
        self.table = basicDataProcessing(data)
        self._returns = self.table.pct_change()
        self._mean_returns = self._returns.mean()
        self._cov_matrix = self._returns.cov()
        self._num_portfolios = num_portfolios
        self._risk_free_rate = risk_free_rate
    
    def _portfolio_annualised_performance(self,weights):
        returns = np.sum(self._mean_returns*weights ) *252
        std = np.sqrt(np.dot(weights.T, np.dot(self._cov_matrix, weights))) * np.sqrt(252)
        return std, returns
    
    def _random_portfolios(self):
        results = np.zeros((3,self._num_portfolios))  # 三行分别记录 portfolio_std_dev、portfolio_return、portfolio_sharp_ratio
        weights_record = []
        num_target = self.table.shape[1]
        for i in range(self._num_portfolios):
            print('\r' + '分析进度 ' +'#' + '#' * int(i * 10 / self._num_portfolios) + '(%.2f%%   %d/%d)' % (i * 100 / self._num_portfolios,i,self._num_portfolios),end='',flush=True)
            weights = np.random.random(num_target)
            weights /= np.sum(weights)
            weights_record.append(weights)
            portfolio_std_dev, portfolio_return = self._portfolio_annualised_performance(weights)
            results[0,i] = portfolio_std_dev
            results[1,i] = portfolio_return
            results[2,i] = (portfolio_return - self._risk_free_rate) / portfolio_std_dev
        print('\n')
        return results, weights_record
    
    def result(self):
        results, weights = self._random_portfolios()
        
        max_sharpe_idx = np.argmax(results[2])
        sdp, rp = results[0,max_sharpe_idx], results[1,max_sharpe_idx]
        max_sharpe_allocation = pd.DataFrame(weights[max_sharpe_idx],index=self.table.columns,columns=['allocation'])
        max_sharpe_allocation.allocation = [round(i*100,2)for i in max_sharpe_allocation.allocation]
        max_sharpe_allocation = max_sharpe_allocation.T
        
        min_vol_idx = np.argmin(results[0])
        sdp_min, rp_min = results[0,min_vol_idx], results[1,min_vol_idx]
        min_vol_allocation = pd.DataFrame(weights[min_vol_idx],index=self.table.columns,columns=['allocation'])
        min_vol_allocation.allocation = [round(i*100,2)for i in min_vol_allocation.allocation]
        min_vol_allocation = min_vol_allocation.T
        
        print("-"*80)
        print("Maximum Sharpe Ratio Portfolio Allocation\n")
        print("Annualised Return:", round(rp,2))
        print("Annualised Volatility:", round(sdp,2))
        print ("\n")
        print(max_sharpe_allocation)
        print("-"*80)
        print("Minimum Volatility Portfolio Allocation\n")
        print("Annualised Return:", round(rp_min,2))
        print("Annualised Volatility:", round(sdp_min,2))
        print("\n")
        print(min_vol_allocation)
        
        plt.figure(figsize=(15, 9),dpi=300)
        plt.scatter(results[0,:],results[1,:],c=results[2,:],cmap='YlGnBu', marker='o', s=10, alpha=0.3)
        plt.colorbar()
        plt.scatter(sdp,rp,marker='*',color='r',s=500, label='Maximum Sharpe ratio')
        plt.scatter(sdp_min,rp_min,marker='*',color='g',s=500, label='Minimum volatility')
        plt.title('Simulated Portfolio Optimization based on Efficient Frontier')
        plt.xlabel('annualised volatility')
        plt.ylabel('annualised returns')
        plt.legend(labelspacing=0.8)
        
        plt.savefig('MPT_Result.png')
