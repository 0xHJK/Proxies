#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, requests, threading
from pyecho import echo

# 封装http请求
def reqs(**kwargs):
    # 传递url，正则表达式，timeout，proxies
    url = kwargs.get('url', '')
    rex = kwargs.get('rex', '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}')
    timeout = kwargs.get('timeout', 10)
    proxies = kwargs.get('proxies', {
        'http': 'socks5://127.0.0.1:1080',
        'https': 'socks5://127.0.0.1:1080'
    })
    headers = { 'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)' }
    try:
        r = requests.get(url, headers = headers, proxies = proxies, timeout = timeout)
        if r.status_code == 200:
            echo.success('请求 %s 成功' % url)
            # 根据传入的正则返回需要的数据
            return re.findall(rex, r.text)
        else:
            echo.error('%d %s' % (r.status_code, url))
    except Exception as e:
        echo.error('请求 %s 异常 %s' % (url, e))
    return []

# 从sites.txt文件中获取站点列表
def get_sites(fname):
    with open(fname, 'r') as f:
        sites = [x.strip() for x in f.readlines()]
    return sites

# 获取爬到的代理
def get_ip_ports(site):
    pages = reqs(url = site, rex = '<h3[\s\S]*?<a.*?(http.*?\.html).*?</a>')
    ip_ports = []
    for page in pages:
        ip_ports += reqs(url = page)
    return ip_ports

# 检查代理是否可用
def check_ip_ports(ip_ports, func):
    timeout = 5
    for ip_port in ip_ports:
        proxies = {
            'http': 'http://%s' % ip_port,
            'https': 'https://%s' % ip_port
        }
        ips = reqs(url = 'http://1212.ip138.com/ic.asp', 
            rex = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 
            proxies = proxies, timeout = timeout)
        if len(ips) > 0 and ips[0] in ip_port:
            echo.success('%s has checked' % ip_port)
            # 如果可用则调用回调函数
            func(ip_port)

# 将可用的代理保存到文件proxies.txt
def save_ip_ports(fname, ip_ports):
    with open(fname, 'w') as f:
        for i in ip_ports:
            f.write(i + '\n')

if __name__ == '__main__':
    ip_ports = []
    ip_ports_ok = []
    all_threads = []

    sites = get_sites('sites.txt')
    for site in sites:
        ip_ports += get_ip_ports(site)
    ip_ports = list(set(ip_ports))

    # 把爬到的代理存到临时文件
    save_ip_ports('temp.txt', ip_ports)

    def checked(ip_port):
        ip_ports_ok.append(ip_port)

    # 每20个代理开一个线程，一般代理数量在几千到一万
    for i in range(0, len(ip_ports), 20):
        t = threading.Thread(target = check_ip_ports, args = (ip_ports[i: i+20], checked))
        all_threads.append(t)
        t.start()

    for t in all_threads:
        t.join()

    # 保存可用的代理到proxies.txt
    save_ip_ports('proxies.txt', ip_ports_ok)

    echo.info('All done : )')
