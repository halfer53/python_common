#encoding=utf-8
#-*- coding:utf-8-*-
import os
import sys
import logging
import requests
import Queue
import random
import time
from pymongo import MongoClient
from common_func import get_ip_list_from_locale
from requests_toolbelt.adapters.source import SourceAddressAdapter

TEST_URL = {'URL': 'http://www.baidu.com/img/baidu_jgylogo3.gif', 'SIZE': 705}

class AntiBan():

    """anti ban module by requests"""

    def __init__(self, use_proxy=False, need_auth=False):
        self.logger = logging.getLogger('anti_ban_requests')
        self.use_proxy = use_proxy
        if use_proxy == False:
            self.ip_list = []
            self.ip_queue = Queue.Queue()
            self.ip_list = get_ip_list_from_locale()
            if need_auth:
                self.ip_list = self.get_usefulness_ip(self.ip_list)
            random.shuffle(self.ip_list)
            for ip in self.ip_list:
                self.ip_queue.put(ip)
            self.logger.info('initialize usefulness ip size=%d ips=%s', len(self.ip_list), str(self.ip_list))
        else:
            self.init_mongo_db()
            self.proxy_list = []
            self.proxy_queue = Queue.Queue()

            for item in self.mongo_db.tj_proxy.find():
                ip = item['ip']
                proxy_host = ip[ip.find('://')+3 : ip.rfind(':')]
                proxy_port = ip[ip.rfind(':') + 1 :]
                proxy_username, proxy_password = item['user_pass'].split(':')
                source_ip = item['source_ip']
                self.proxy_list.append({'proxy_host': proxy_host,
                                        'proxy_port': proxy_port,
                                        'proxy_username': proxy_username,
                                        'proxy_password': proxy_password,
                                        'source_ip': source_ip})
            random.shuffle(self.proxy_list)
            for proxy_info in self.proxy_list:
                self.proxy_queue.put(proxy_info)

            self.logger.info('initialize tj proxy size=%d', self.proxy_queue.qsize())
            if self.proxy_queue.qsize() == 0:
                self.proxy_queue = None

    def get_requests(self):
        if self.use_proxy:
            return self.get_requests_with_new_proxy()
        else:
            return self.get_requests_with_new_ip()

    def get_requests_with_new_ip(self):
        ret = {'ip': '127.0.0.1',
               'requests': None,
               'error': ''}
        try:
            ip = self.ip_queue.get(block=False)
            s = requests.Session()
            s.mount('http://', SourceAddressAdapter((ip, 0)))
            s.mount('https://', SourceAddressAdapter((ip, 0)))
            ret['ip'] = ip
            ret['requests'] = s
            ret['error'] = 'ok'
            self.ip_queue.put(ip)
        except Exception, e:
            self.logger.error('get requests with new ip failed! (%s)', str(e))
            ret['error'] = str(e)
        return ret

    def get_requests_with_new_proxy(self):
        ret = {'ip': '127.0.0.1',
               'requests': None,
               'error': ''}
        try:
            proxy_info = self.proxy_queue.get(block=False)
            proxy_host = proxy_info['proxy_host']
            proxy_port = proxy_info['proxy_port']
            proxy_username = proxy_info.get('proxy_username', '')
            proxy_password = proxy_info.get('proxy_password', '')
            source_ip = proxy_info.get('source_ip', '')
            if proxy_username and proxy_password:
                proxies = {
                    "http": "http://%s:%s@%s:%s" % (proxy_username, proxy_password, proxy_host, proxy_port),
                    "https": "https://%s:%s@%s:%s" % (proxy_username, proxy_password, proxy_host, proxy_port)
                }
            else:
                proxies = {
                    "http": "http://%s:%s" % (proxy_host, proxy_port),
                    "https": "http://%s:%s" % (proxy_host, proxy_port)
                }
            s = requests.Session()
            s.proxies = proxies
            ret['requests'] = s
            ret['ip'] = source_ip
            self.proxy_queue.put(proxy_info)
        except Exception, e:
            self.logger.error('get proxies with new ip failed! (%s)', str(e))
            ret['error'] = str(e)
        return ret

    def init_mongo_db(self):
        while True:
            try:
                self.mongo_db = MongoClient('192.168.60.65', 10010).anti_ban
                break
            except Exception, e:
                self.logger.error('initialize mongo db error! (%s)', str(e))
                time.sleep(5)

    def get_usefulness_ip(self, ip_list):
        usefulness_ip_list = []
        for ip in ip_list:
            try:
                s = requests.Session()
                s.mount('http://', SourceAddressAdapter((ip, 0)))
                s.mount('https://', SourceAddressAdapter((ip, 0)))
                r = s.get(TEST_URL['URL'])
                if r.status_code == 200 and len(r.text) == TEST_URL['SIZE']:
                    usefulness_ip_list.append(ip)
            except Exception, e:
                logging.error(str(e))
                continue
        return usefulness_ip_list

