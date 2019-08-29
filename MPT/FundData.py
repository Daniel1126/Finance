# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 21:43:15 2019

@author: Administrator
"""

import urllib
from http import cookiejar
import pandas as pd
import json
from functools import reduce
import threading
import warnings
warnings.filterwarnings('ignore')

def opener_build():
    cj = cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(handler)
    opener.addheaders = [('User-Agent','Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36')]
    
    return opener

def url_build(code):
    api = 'https://danjuanapp.com/djapi/fund/nav/history/{code}?size=9999'
    url = api.format(code=code)
    
    return url

def data_processing(webdata):
    webdata = webdata['data']['items']
    webdata = [pd.DataFrame(item,index=[1,]) for item in webdata]
    data = reduce(lambda x,y: pd.concat([x,y],ignore_index=True) ,webdata)
    return data

def request(code):
    opener = opener_build()
    url = url_build(code)
    URL = urllib.request.Request(url)
    webdata = json.loads(opener.open(URL).read().decode('utf-8'))
    data = data_processing(webdata)
    
    return data

def multi_request(codes):
    threads = list();lst = list()
    def _request(code,lst):
        opener = opener_build()
        url = url_build(code)
        URL = urllib.request.Request(url)
        webdata = json.loads(opener.open(URL).read().decode('utf-8'))
        data = data_processing(webdata)
        data['code'] = code
        lst.append(data)
    
    for code in codes:
        thread = threading.Thread(target=_request,args=(code,lst))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    
    df = reduce(lambda x,y: pd.concat([x,y],ignore_index=True),lst)
    return df