#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
@author: HJK
"""
import os, sys, getopt, datetime, re, threading, platform, requests

SITES = ['http://www.proxyserverlist24.top/', 'http://www.live-socks.net/']
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)'}
TIMEOUT = 5
SPIDER_PROXIES = None
IP138 = 'http://2000019.ip138.com/'

def echo(color, *args):
    colors = {'error': '\033[91m', 'success': '\033[94m', 'info': '\033[93m'}
    if not color in colors or platform.system() == 'Windows':
        print(' '.join(args))
    print(colors[color], ' '.join(args), '\033[0m')

def get_content(url, proxies=None) -> str:
    ''' 根据URL和代理获得内容 '''
    echo('info', url)
    try:
        r = requests.get(url, headers=HEADERS, proxies=proxies, timeout=TIMEOUT)
        if r.status_code == requests.codes.ok:
            return r.text
        echo('error', '请求失败', str(r.status_code), url)
    except Exception as e:
        echo('error', url, str(e))
    return ''

def get_proxies_thread(site, proxies):
    ''' 爬取一个站的代理的线程 '''
    content = get_content(site, SPIDER_PROXIES)
    pages = re.findall(r'<h3[\s\S]*?<a.*?(http.*?\.html).*?</a>', content)
    for page in pages:
        content = get_content(page, SPIDER_PROXIES)
        proxies += re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', content)

def get_proxies_set() -> list:
    ''' 获得所有站的代理并去重 '''
    spider_pool, proxies = [], []
    for site in SITES:
        t = threading.Thread(target=get_proxies_thread, args=(site, proxies))
        spider_pool.append(t)
        t.start()
    for t in spider_pool:
        t.join()
    return list(set(proxies))

def check_proxies_thread(check_url, proxies, callback):
    ''' 检查代理是否有效的线程 '''
    for proxy in proxies:
        proxy = proxy.strip()
        proxy = proxy if proxy.startswith('http://') else 'http://' + proxy
        content = get_content(check_url, proxies={'http': proxy})
        if content:
            if check_url == IP138:
                # 如果能获取到IP，则比对一下IP和代理所用IP一致则判断有效
                ip = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', content)
                if ip and ip[0] in proxy:
                    callback(proxy)
            else:
                callback(proxy)

def check_and_save_proxies(check_url, proxies, output_file):
    ''' 验证和保存所有代理 '''
    checker_pool = []
    open(output_file, 'w').write('')
    def save_proxy(proxy):
        echo('success', proxy, 'checked ok.')
        open(output_file, 'a').write(proxy + '\n')
    for i in range(0, len(proxies), 20):
        t = threading.Thread(target=check_proxies_thread, args=(check_url, proxies[i:i+20], save_proxy))
        checker_pool.append(t)
        t.start()
    for t in checker_pool:
        t.join()

if __name__ == '__main__':
    input_file, output_file, check_url = '', 'proxies.txt', IP138
    if len(sys.argv) > 1:
        try:
            opts, _ = getopt.getopt(sys.argv[1:], 'u:f:o:')
        except getopt.GetoptError as e:
            echo('error', str(e))
            sys.exit(2)
        for o, a in opts:
            if o in ('-f'): input_file = os.path.abspath(a)
            elif o in ('-u'): check_url = a
            elif o in ('-o'): output_file = os.path.abspath(a)
            else: assert False, 'unhandled option'
    start = datetime.datetime.now()
    proxies = open(input_file, 'r').readlines() if input_file else get_proxies_set()
    check_and_save_proxies(check_url, proxies, output_file)
    stop = datetime.datetime.now()
    note = '\n代理总数：%s\n有效代理数：%s\n结果文件：%s\n时间消耗：%s\n' % \
            (len(proxies), len(open(output_file, 'r').readlines()),
            output_file, stop - start)
    echo('success', note)
