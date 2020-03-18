# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 09:42:01 2020

@author: Administrator
@content: 目标波动率模型
"""
from scipy.optimize import minimize
import numpy as np
import pandas as pd
from _data import Data  #  这部分属于爬虫，用来获取数据源，与算法无关
from functools import reduce  # 用来把爬虫调取的表格连接起来

def loadData(tickers=['AAPL','FB','BA','NFLX']):  # --->获取数据，并组合成一张透视表
    # 获取数据列表，形式为[DataFrame,DataFrame,DataFrame,DataFrame,]
    def dataTransform(ticker,period='week',begin='20141231',end='20191231'):
        df = Data(symbol=ticker.upper(),period=period,begin=begin,end=end).request()
        df['ticker'] = ticker
        return df
    dataList = [dataTransform(ticker) for ticker in tickers]
    df = reduce(lambda x,y:pd.concat([x,y],ignore_index=True),dataList)
    df = df.set_index('time')
    df = df.pivot(columns='ticker',values='close')  # 组合成一张透视表
    
    return df

def calculatePortfolioSigma(weight,covariance):
    # 计算组合风险的函数,这部分对应的是MRC中的square(sigma_p)
    weight = np.matrix(weight)
    variance = (weight * covariance * weight.T)[0,0]  # 得到所选时间区间内的方差
    sigma = np.sqrt(variance) * 52 ** 0.5   #  因为采用的是周度收益率，随意年华的时候我们默认一年52周
    return sigma

def riskBudgetObjective(weight,covariance,targetVolatility):
    # 该函数的目的是得到最小的 J(x)
    # targetVolatility为目标波动率
    # covariance为各个标的之间的协方差
    # weight为各个标的权重--->我们会使用scipy.optimize中的minimize函数寻找最优的weight
    sigma_p =  calculatePortfolioSigma(weight,covariance) # portfolio sigma
    J = np.square(sigma_p - targetVolatility) * 100 # ssquared error
    return J

def calculateWeight(covariance,targetVolatility):
    # 该函数的输入变量是targetVolatility(目标波动率)
    initialWeight = [1/len(covariance) for _ in range(len(covariance))]
    #initialWeight = [0.25,0.5,0.2,0.25]
    # initialWeight(初始化权重)表示我们初始化各类资产的权重，我们认为刚开始持有各类资产的比重相同
    constrains = ({'type': 'eq', 'fun': lambda x:np.sum(x)-1.0}, # 各类资产总得权重不得超过100%
    {'type': 'ineq', 'fun': lambda x:x - 0})  # 这里的 x-0表示x>0,各类资产只做多
    result= minimize(riskBudgetObjective, initialWeight, args=(covariance,targetVolatility), method='SLSQP',constraints=constrains, options={'disp': True})
    targetWeight = result.x
    return targetWeight


if __name__ == '__main__':
    targetVolatility = 0.30  # 目标波动率我们设定为30%
    # 加载数据,本次调用数据为2014-12-31至2019-12-31
    df = loadData(tickers=['AAPL','FB','BA','NFLX'])
    returns = df.pct_change().dropna(how='all')  # 得到各个标的的收益率
    covariance = np.matrix(returns.cov()) # 得到各个标的的之间的协方差矩阵
    targetWeight = calculateWeight(covariance,targetVolatility)
    print(targetWeight)