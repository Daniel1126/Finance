# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 14:40:05 2020

@author: Daniel
"""
# 假设组合有四项资产
# 资产收益率为R
# 资产协方差为V
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


def calculatePortfolioVAR(weight,covariance):
    # 计算组合风险的函数,这部分对应的是MRC中的square(sigma_p)
    weight = np.matrix(weight)
    return (weight * covariance * weight.T)[0,0]

def calculateRiskContribution(weight,covariance):
    # 计算单个资产对总体风险贡献度的函数,计算RC
    weight = np.matrix(weight)
    sigma = np.sqrt(calculatePortfolioVAR(weight,covariance))
    # 边际风险贡献 ----> MRC
    MRC = covariance * weight.T / sigma
    # 风险贡献   -----> RC
    RC = np.multiply(MRC,weight.T) 
    return RC  # ----> 返回风险贡献度

def riskBudgetObjective(weight,covarianceAndRc):
    # 该函数的目的是得到最小的 J(x)
    # rc为风险贡献值，我们希望风险贡献值都相同
    # covariance为各类资产的协方差
    # weight为各类资产的权重--->我们会使用scipy.optimize中的minimize函数寻找最优的weight
    covariance = covarianceAndRc[0];rc = covarianceAndRc[1]
    sigma_p =  np.sqrt(calculatePortfolioVAR(weight,covariance)) # portfolio sigma
    risk_target = np.asmatrix(np.multiply(sigma_p,rc))
    asset_RC = calculateRiskContribution(weight,covariance)
    J = np.sum(sum(np.square(asset_RC-risk_target.T)),axis=1)[0,0] * 100 # sum of squared error
    return J


def calculateWeight(covariance,rc):
    # 该函数的输入变量是rc（RiskContribution）
    initialWeight = [1/len(rc) for _ in range(len(rc))]
    #initialWeight = [0.25,0.5,0.2,0.25]
    # initialWeight(初始化权重)表示我们初始化各类资产的权重，我们认为刚开始持有各类资产的比重相同
    constrains = ({'type': 'eq', 'fun': lambda x:np.sum(x)-1.0}, # 各类资产总得权重不得超过100%
    {'type': 'ineq', 'fun': lambda x:x - 0})  # 这里的 x-0表示x>0,各类资产只做多
    result= minimize(riskBudgetObjective, initialWeight, args=[covariance,rc], method='SLSQP',constraints=constrains, options={'disp': True})
    targetWeight = np.asmatrix(result.x)
    return targetWeight

if __name__ == '__main__':
    # 加载数据,本次调用数据为2014-12-31至2019-12-31
    df = loadData(tickers=['AAPL','FB','BA','NFLX'])
    # 拿到数据之后开始准备计算MRC（资产的边际风险贡献：Margin Risk Contribution）
    # calculateRiskContribution函数计算MRC与RC
    # 首先我们先计算资产之间的协方差矩阵，四类资产暂时以Apple（AAPL）、Facebook（FB）、Boeing（BA）、Netflix（NFLX）为例
    returns = df.pct_change().dropna(how='all')  # 得到各个标的的收益率
    covariance = np.matrix(returns.cov()) # 得到各个标的的之间的协方差矩阵
    rc = [1/len(covariance) for _ in range(len(covariance))]
    #rc = [0.3,0.1,0.5,0.1] #--->rc的值可以自定义，一般风险平价，我们认为是各类资产的风险贡献度是相同的
    targetWeight = calculateWeight(covariance,rc)
    print(targetWeight)
    
    



