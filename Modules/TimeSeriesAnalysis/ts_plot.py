# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 22:02:02 2019

@author: Administrator
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import scipy.stats as scs
import statsmodels.tsa.api as smt
import statsmodels.api as sm

mpl.rcParams['font.sans-serif']=['SimHei']
mpl.rcParams['axes.unicode_minus']=False

def plot(data,lags=None,title='',dpi=80):
    if not isinstance(data,pd.Series):
        data = pd.Series(data)
    with plt.style.context('ggplot'):
        plt.figure(figsize=(10,8),dpi=dpi)
        layout = (3,2)   #   布局为3行2列
        ts_ax = plt.subplot2grid(layout,(0,0))
        acf_ax = plt.subplot2grid(layout,(1,0))
        pacf_ax = plt.subplot2grid(layout,(1,1))
        qq_ax = plt.subplot2grid(layout,(2,0))
        pp_ax = plt.subplot2grid(layout,(2,1))
        
        data.plot(ax = ts_ax)
        ts_ax.set_title(title + '时序图')
        smt.graphics.plot_acf(data,lags=lags,ax=acf_ax,alpha=0.5)
        acf_ax.set_title('自相关系数')
        smt.graphics.plot_pacf(data,ax=pacf_ax,lags=lags,alpha=0.5)
        pacf_ax.set_title('偏自相关系数')
        sm.qqplot(data, line = 's',ax = qq_ax)
        qq_ax.set_title('QQ 图')
        scs.probplot(data, plot = pp_ax)
        pp_ax.set_title('PP 图')
        plt.tight_layout()
        
        
        