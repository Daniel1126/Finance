# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 16:27:10 2020
@author: Administrator
@content:日品数据
"""
import urllib
from http import cookiejar
import pandas as pd
import time
import json
from datetime import datetime

class Data(object):
    def __init__(self,symbol='SH510050',period='day',begin='20101231',end='20181231'):
        """
        调用方式：df = Data(symbol='SH510050',period='day',begin='20101231',end='20181231').request()
        ::symbol --> SH510050
        ::begin  --> 20101231
        ::end    --> 20181231
        """
        self.opener = self._opener_build()
        self.symbol = symbol.upper()
        self.period = period
        self.begin = str(int(time.mktime(time.strptime(begin,'%Y%m%d')) * 1000))
        self.end = str(int(time.mktime(time.strptime(end,'%Y%m%d')) * 1000))
        self.url = self._url_build()
        
    def _opener_build(self):
        cj = cookiejar.CookieJar()
        handler = urllib.request.HTTPCookieProcessor(cj)
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [('User-Agent','Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.71 Safari/537.36')]
        opener.open('https://xueqiu.com/')
        
        return opener
        
    def _url_build(self):
        api = 'https://stock.xueqiu.com/v5/stock/chart/kline.json?'
        data = {
                'symbol':self.symbol,
                'begin':self.begin,
                'end':self.end,
                'period':self.period,
                'type':'before',
                'indicator':'kline'
                }
        url = api + urllib.parse.urlencode(data)
        
        return url
    
    def request(self):
        webdata = json.loads(self.opener.open(self.url).read().decode('utf-8'))['data']
        columns = webdata['column']
        items = webdata['item']
        df = pd.DataFrame(items,columns=columns)
        df = df.rename({'timestamp':'time'},axis='columns')
        df.time = df.time.apply(lambda x:datetime.fromtimestamp(x/1000))
        
        return df

    
    
    
    
    
        