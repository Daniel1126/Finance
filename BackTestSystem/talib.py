# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 11:10:26 2019

@author: Daniel
"""
import numpy as np
from collections import OrderedDict
from math import floor
import pandas as pd

class Indicator:
    def __init__(self,df):
        self.df = df
        
    def sma(self,period=[10,20]):
        # 默认采用的使10个交易日和20个交易日
        df = self.df.copy()
        for item in period:
            df['sma_%s'%item] = df.close.rolling(item).mean()
        
        return df
    
    def ema(self,period=[10,20]):
        # 默认采用的使10个交易日和20个交易日
        df = self.df.copy()
        for item in period:
            df['ema_%s'%item] = df.close.ewm(span=item).mean()
        
        return df

class Evaluation():
    def __init__(self,df):
        '''
        至少包括年华收益、年华波动、最大回撤(MDD)、各个月和周的收益率、日均交易次数、胜率
        '''
        self.df = df
    
    def evaluation(self):
        df = self.df.copy()
        result_dic = dict()
        # ================================================================== #
        trading_times =len(df[df.position - df.position.shift(1) != 0][1:])
        holding_period = len(df) / trading_times 
        result_dic['平均持仓时间'] = round(holding_period,2)
        # ================================================================== #
        year = (df.time[len(df)-1] - df.time[0]).days / 365
        annual_return_rate = round((df.npv[len(df) - 1] )**(1/year) - 1,4)
        result_dic['年华收益率'] = annual_return_rate
        # ================================================================== #
        npv_pct = df.npv.pct_change(); npv_pct.fillna(0,inplace=True)
        annual_std = round(npv_pct.std()*250**0.5,4)
        result_dic['年华波动率'] = annual_std
        # ================================================================== #
        # 计算滚动最大值df.npv.expanding().max()
        #  计算资金曲线在滚动最高值之后所回撤的百分比
        mdd = (df.npv.expanding().max() - df.npv) / df.npv.expanding().max(); mdd = round(mdd.max(),4)
        result_dic['最大回撤率'] = mdd
        # ================================================================== #
        #  目前还存在问题
        key_index = df[df.position - df.position.shift(1) != 0].index[1:] - 1
        key_df = df.loc[key_index,'npv']
        trading_result = (key_df - key_df.shift(1)).fillna(0)
        trading_win = key_df[trading_result > 0].count()
        trading_lose = key_df[trading_result < 0].count()
        win_rate = trading_win / (trading_win + trading_lose)
        result_dic['胜率'] = round(win_rate,4)
        
        return result_dic
    

class PositionManagement():
    def __init__(self,df):
        self.df = df

class BackTestFrame():
    def __init__(self,df,log=False):
        '''
        run_us 函数只能测试美股股票，或者ETF
        '''
        self.df = df
        self.commission = 0.0003 # 万3佣金
        self.slippage = 0.002    # 千2滑点
        self.investment = 1000000 # 初始投资本金为100万
        self.log = log
    
    def close_process(self):
        df = self.df.copy()
        df.loc[0,'percent'] = 0
        df.close = (1 + df.percent / 100).cumprod() * df.close[0]
        
        return df
        
        
    
    def run_us(self):
        df = self.close_process()
        #df['pct'] = df.close.pct_change()
        #df['profit'] = df.pct * df.position
        #key_index_commission = df[df.position != df.position.shift(1)].index[1:]
        log = OrderedDict()  # 需要记录时间、操作、原因
        log['time'],log['operation'],log['reason'],log['detail'] = [],[],[],[]
        df['commission'] = np.nan
        df.loc[0,'portfolio_value'] = self.investment 
        df.loc[0,'number'] = 0
        length = len(df)
        df['delta'] = np.nan
        '''
        考虑所有仓位变化的情况
        0 --> positive,0 --> negative ==  0 -- > position
        positive --> 0, negative --> 0  ==  position --> 0
        positive --> positive, negative --> negative  == same symbpl position --> same symbpl position
        positive --> negative, negative --> positive  == opposite symbol position --> opposite symbol position
        '''
        for i in range(1,length):
            if df.loc[i,'position'] != df.loc[i-1,'position']:
                if df.loc[i-1,'position'] == 0:
                    '''
                    记录本次操作的时间、方式、原因
                    开仓操作，必然产生交易费
                    '''
                    log['time'].append(df.loc[i,'time'])
                    log['operation'].append('开仓，0 --> %s'%(df.loc[i,'position']))
                    log['reason'].append('产生开仓信号，需要建立头寸')
                    
                    df.loc[i,'delta'] = df.loc[i,'close'] - df.loc[i-1,'close'] * (1 + self.slippage)
                    position = abs(df.loc[i,'position'])
                    number =  position *  df.loc[i - 1,'portfolio_value'] / (df.loc[i - 1,'close']*(1 + self.slippage));number = floor(number)
                    df.loc[i,'number'] = number 
                    commission_all = number * df.loc[i,'close'] * (1 + self.slippage) * self.commission
                    df.loc[i - 1,'commission'] = commission_all
                    if df.loc[i,'position'] > 0:
                        sign = 1
                    else:
                        sign = -1
                    df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value'] - commission_all + number * df.loc[i,'delta'] * sign
                    log['detail'].append('本次操作产生佣金%.2f,交易标的份额为%.2f'%(commission_all,number))
                    
                elif df.loc[i,'position'] == 0:
                    '''
                    记录本次操作的时间、方式、原因
                    清仓操作，必然不会产生交易费
                    此时操作只需要对i-1,i-2数据进行修改 -- 滑点
                    '''
                    log['time'].append(df.loc[i,'time'])
                    log['operation'].append('开仓，0 --> %s'%(df.loc[i,'position']))
                    log['reason'].append('产生清仓信号，需要清空现有头寸')
                    
                    position = abs(df.loc[i - 1,'position'])  # 这里采用的是上一时刻的仓位，因为只有上一时刻才有仓位
                    df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value'] - df.loc[i-1,'number'] * df.loc[i-1,'close'] * self.slippage
                    log['detail'].append('清空仓位，交易标的份额为%.2f'%(df.loc[i-1,'number']))
                
                elif df.loc[i,'position'] * df.loc[i-1,'position'] > 0:
                    '''
                    记录本次操作的时间、方式、原因
                    换仓操作，需要判断加减仓才能确定交易费的产生与否
                    '''
                    log['time'].append(df.loc[i,'time'])
                    # 仓位在同号[position <--> position]之间进行变化
                    if abs(df.loc[i,'position']) > abs(df.loc[i-1,'position']):
                        # i时刻position > i-1时刻position --> 属于加仓操作，有commission
                        log['operation'].append('加仓，%s --> %s'%(df.loc[i-1,'position'],df.loc[i,'position']))
                        log['reason'].append('产生加仓信号，需要增加现有头寸')
                        
                        df.loc[i,'delta'] = df.loc[i,'close'] - df.loc[i-1,'close']
                        position = abs(df.loc[i,'position'])
                        number =  position *  df.loc[i - 1,'portfolio_value'] / (df.loc[i - 1,'close']);number = floor(number)
                        number_delta = abs(number - df.loc[i-1,'number'])
                        slippage_cost = number_delta * self.slippage * df.loc[i-1,'close']
                        df.loc[i,'number'] = number 
                        commission_all = number_delta * df.loc[i,'close'] * (1 + self.slippage) * self.commission
                        df.loc[i - 1,'commission'] = commission_all
                        if df.loc[i,'position'] > 0:
                            sign = 1
                        else:
                            sign = -1
                        df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value'] - commission_all + number * df.loc[i,'delta'] * sign - slippage_cost
                        log['detail'].append('本次操作产生佣金%.2f,交易标的份额为%.2f'%(commission_all,number))
                        
                    elif abs(df.loc[i,'position']) < abs(df.loc[i-1,'position']):
                        # i时刻position < i-1时刻position --> 属于减仓操作，无commission
                        log['operation'].append('减仓，%s --> %s'%(df.loc[i-1,'position'],df.loc[i,'position']))
                        log['reason'].append('产生减仓信号，需要减少现有头寸')
                        
                        df.loc[i,'delta'] = df.loc[i,'close'] - df.loc[i-1,'close']
                        position = abs(df.loc[i,'position'])
                        number =  position *  df.loc[i - 1,'portfolio_value'] / (df.loc[i - 1,'close']);number = floor(number)
                        number_delta = abs(number - df.loc[i-1,'number'])
                        slippage_cost = number_delta * self.slippage * df.loc[i-1,'close']
                        df.loc[i,'number'] = number 
                        if df.loc[i,'position'] > 0:
                            sign = 1
                        else:
                            sign = -1
                        df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value'] + number * df.loc[i,'delta'] * sign - slippage_cost
                        log['detail'].append('本次操作产生佣金%.2f,交易标的份额为%.2f'%(commission_all,number))
                        
                elif df.loc[i,'position'] * df.loc[i-1,'position'] < 0:
                    # 这种情况相当于先清仓再加仓，清仓不需要手续费，加仓需要手续费
                    # commission我们只需要考虑加仓部分即可
                    '''
                    记录本次操作的时间、方式、原因
                    换仓操作，由于时多空转变因此必然产生交易费
                    '''
                    log['time'].append(df.loc[i,'time'])
                    log['operation'].append('换仓，%s --> %s'%(df.loc[i-1,'position'],df.loc[i,'position']))
                    log['reason'].append('产生换仓信号,进行换仓')
                    
                    # 先做清仓操作
                    slippage_cost = df.loc[i-1,'number'] * df.loc[i-1,'close'] * self.slippage
                    portfolio_temp = df.loc[i - 1,'portfolio_value'] - slippage_cost
                    # 再做加仓操作
                    df.loc[i,'delta'] = df.loc[i,'close'] - df.loc[i-1,'close'] * (1 + self.slippage)
                    position = abs(df.loc[i,'position'])
                    number =  position *  portfolio_temp / (df.loc[i - 1,'close'] * (1 + self.slippage))
                    number = floor(number)
                    df.loc[i,'number'] = number 
                    commission_all = number * df.loc[i,'close'] * (1 + self.slippage) * self.commission
                    df.loc[i - 1,'commission'] = commission_all
                    if df.loc[i,'position'] > 0:
                        sign = 1
                    else:
                        sign = -1
                    df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value'] - commission_all + number * df.loc[i,'delta'] * sign
                    log['detail'].append('本次操作产生佣金%.2f,清空标的份额%.2f,另外交易标的份额为%.2f'%(commission_all,df.loc[i-1,'number'],number))         
            else:
                # 我们先考虑空仓的情况
                if df.loc[i,'position'] == 0:
                    df.loc[i,'delta'] = df.loc[i,'close'] - df.loc[i-1,'close']
                    df.loc[i,'number'] = 0
                    df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value']
                    
                elif df.loc[i,'position'] != 0:
                    df.loc[i,'delta'] = df.loc[i,'close'] - df.loc[i-1,'close']
                    df.loc[i,'number'] = df.loc[i - 1,'number']
                    df.loc[i,'portfolio_value'] = df.loc[i - 1,'portfolio_value'] + \
                                                  df.loc[i,'number'] * df.loc[i,'delta'] * df.loc[i,'position']
                    
        df['npv'] = df.portfolio_value / self.investment
        df.drop(columns=['number','delta','portfolio_value'],inplace=True)
        if self.log:
            df_log = pd.DataFrame(log)
            df_log.to_excel('log.xlsx',index=False)
        
        '''
        # 画图模板，可直接移植到策略框架里
        plt.figure(figsize=(15,9),dpi=300)
        plt.plot(range(len(df.npv)),df.npv)
        plt.savefig('result_stock.png')
        plt.show()
        '''
        return df