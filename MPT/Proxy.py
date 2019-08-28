import urllib
from http import cookiejar
from lxml import etree
from threading import Thread
import pickle

class ProxyIp():
    def __init__(self):
        '''
        调用方法
        ls = ProxyIp().get(num=1,update=True)
        num：表示抓取代理的单位，1代表100条代理，因为该模块中带有验证功能，实际得到的可以满足使用需求的IP代理<=100
        update：表示是否更新代理，默认为False 不更新，初次使用该模块推荐True参数
        运行程序时，本地文件夹会产生一个proxy.pkl文件，该文件存储代理
        '''
        self.api = 'https://www.xicidaili.com/nn/{}'
        self.verify_url = 'https://xueqiu.com/'
        self.ls  = list()

    def url_build(self,num):
        return [self.api.format(i+1) for i in range(num)]

    def opener_build(self):
        cj = cookiejar.CookieJar()
        handler = urllib.request.HTTPCookieProcessor(cj)
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [('user-agent','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0')]

        return opener

    def data_processing(self,webdata):
        data = etree.HTML(webdata)
        data = [item.getchildren() for item in data.xpath('//tr')]
        headers = [item.text for item in data[0]]
        content = [dict(zip(headers,[i.text for i in item])) for item in data[1:]]
        dic = [{item['类型']:item['IP地址']+':'+item['端口']} for item in content]
        dic = self.verify(dic)
        self.ls.extend(dic)
    
    def proxy_request(self,proxy,lst):
        opener = self.opener_build()
        ProxyHandler = urllib.request.ProxyHandler(proxy)
        opener.add_handler(ProxyHandler)
        request = urllib.request.Request(self.verify_url)
        try:
            if opener.open(request,timeout=0.5).status == 200:
                lst.append(proxy)
        except:
            pass
        
    def verify(self,dic):
        threads,lst = [],[]
        for proxy in dic:
            thread = Thread(target=self.proxy_request,args=(proxy,lst))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        
        return lst
        
    def get(self,num=1,update=False):
        if update:
            urls = self.url_build(num)
            threads = []
            for url in urls:
                thread = Thread(target=self.request,args=(url,num))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            with open('proxy.pkl','wb') as f:
                pickle.dump(self.ls,f)
        else:
            self.ls = self.load_data()
        return self.ls
    
    def load_data(self):
        try:
            with open('proxy.pkl','rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(e)
            
    def request(self,url,num):
        opener = self.opener_build()
        webdata = opener.open(url).read().decode('utf-8')
        data = self.data_processing(webdata)

        return data