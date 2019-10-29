# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 22:42:07 2019

@author: Administrator
"""
import numpy as np
import pandas as pd
from collections.abc import Iterable
def calHurst2(ts):
    if not isinstance(ts,Iterable):
        print('ERROR!!!')
    
    n_min, n_max = 2, len(ts)//3
    RSlist = []
    
    for cut in range(n_min,n_max):
        children = len(ts) // cut
        children_list = [ts[i*children:(i+1)*children] for i in range(cut)]
        L = []
        for a_children in children_list:
            Ma = np.mean(a_children)
            Xta = pd.Series(map(lambda x: x-Ma, a_children)).cumsum()
            Ra = max(Xta) - min(Xta)
            Sa = np.std(a_children)
            rs = Ra / Sa
            L.append(rs)
        RS = np.mean(L)
        RSlist.append(RS)
    return np.polyfit(np.log(range(2+len(RSlist),2,-1)), np.log(RSlist), 1)[0]