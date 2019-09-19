# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 15:22:19 2019

@author: Daniel
"""

import mpt
import pandas as pd
if __name__ == '__main__':
    '''
    data 为DataFrame，必须保证所有的数据都在一个DataFrame上
    '''
    data = pd.read_csv('test_data.csv')
    mpt.Analysis(data,num_portfolios=25000,risk_free_rate=0.0178).result()
