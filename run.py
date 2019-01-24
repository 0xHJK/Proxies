#!/usr/bin/env python  
#-*- coding:utf-8 -*-  
"""
@author: HJK 
@file: run.py
@time: 2019-01-24

100行代码快速获得一个代理池

"""
import time, datetime, re, threading, platform, requests

SITES = ['http://www.proxyserverlist24.top/', 'http://www.live-socks.net/']
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)'}
TIMEOUT = 5
PROXIES = {'http': 'socks5://127.0.0.1:1086', 'https': 'socks5://127.0.0.1:1086'}

def colorize(color, *args):
    colors = {'error': '\033[91m', 'success': '\033[94m', 'info': '\033[93m'}
    if not color in colors or platform.system() == 'Windows':
        return ' '.join(args)
    return colors[color] + ' '.join(args) + '\033[0m'

def get_list_by_rex(url, rex, proxies=None) -> list:
    ''' 根据URL和正则提取需要的列表 '''
    s = requests.Session()
    s.headers.update(HEADERS)
    if proxies:
        s.proxies.update(proxies)
    print(colorize('info', url))
    try:
        r = s.get(url, timeout=TIMEOUT)
        if r.status_code == requests.codes.ok:
            return re.findall(rex, r.text)
        else:
            print(colorize('error', '请求失败', str(r.status_code), url))
    except Exception as e:
        print(colorize('error', url, str(e)))
    return []

def get_proxies_thread(site, proxies):
    ''' 爬取一个站的代理 '''
    pages = get_list_by_rex(site, r'<h3[\s\S]*?<a.*?(http.*?\.html).*?</a>', PROXIES)
    for page in pages:
        proxies += get_list_by_rex(page, r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', PROXIES)

def get_proxies_set() -> list:
    ''' 获得所有站的代理并去重 '''
    spider_pool = []
    proxies = []
    for site in SITES:
        t = threading.Thread(target=get_proxies_thread, args=(site, proxies))
        spider_pool.append(t)
        t.start()
    for t in spider_pool:
        t.join()
    return list(set(proxies))

def check_proxies_thread(proxies, callback):
    ''' 检查代理是否有效，包括http代理和socks代理 '''
    for proxy in proxies:
        for proto in ['http://', 'socks5://']:
            proxy = proto + proxy
            ip = get_list_by_rex(
                url='http://2019.ip138.com/ic.asp',
                rex=r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
                proxies={'http': proxy}
            )
            # 如果返回的IP和代理所用IP一致则判断有效
            if ip and ip[0] in proxy:
                print(colorize('success', proxy, 'checked ok.'))
                callback(proxy)

def check_and_save_proxies(filename, proxies):
    ''' 获得所有检查过的代理 '''
    checker_pool = []

    def save_proxy(proxy):
        with open(filename, 'a') as f:
            f.write(proxy + '\n')

    for i in range(0, len(proxies), 20):
        t = threading.Thread(target=check_proxies_thread, args=(proxies[i:i+20], save_proxy))
        checker_pool.append(t)
        t.start()
    for t in checker_pool:
        t.join()

if __name__ == '__main__':
    start = time.time()
    # proxies = get_proxies_set()
    # check_and_save_proxies('proxies.txt', proxies)
    stop = time.time()
    print(colorize('success', 'Proxies Count: %s' % len(open('proxies.txt', 'r').readlines())))
    print(colorize('success', 'Time Spent: %s' % datetime.timedelta(stop - start)))
    print(colorize('success', 'Done. :)'))
