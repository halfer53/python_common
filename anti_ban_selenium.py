#encoding=utf-8
#-*- coding:utf-8-*-
import os
import sys
import logging
import Queue
import random
import time
from pymongo import MongoClient
import seleniumrequests
from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options

DEFAULT_UA = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
def create_proxyauth_extension(proxy_host, proxy_port,
                               proxy_username, proxy_password,
                               scheme='http', plugin_path=None):
    """Proxy Auth Extension

    args:
        proxy_host (str): domain or ip address, ie proxy.domain.com
        proxy_port (int): port
        proxy_username (str): auth username
        proxy_password (str): auth password
    kwargs:
        scheme (str): proxy scheme, default http
        plugin_path (str): absolute path of the extension

    return str -> plugin_path
    """
    import string
    import zipfile

    if plugin_path is None:
        plugin_path = 'c://chrome_proxyauth_plugin.zip'

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
    """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "${scheme}",
                host: "${host}",
                port: parseInt(${port})
              },
              bypassList: ["foobar.com"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "${username}",
                password: "${password}"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path

class AntiBan():

    """anti ban module by selenium"""

    def __init__(self, browser_type='chrome', use_proxy=False, use_requests=False, ua=''):
        self.logger = logging.getLogger('anti_ban_selenium')
        self.use_proxy = use_proxy
        self.use_requests = use_requests
        self.ua = ua if ua else DEFAULT_UA
        self.browser_type = browser_type.lower()
        self.browser = None

        if use_proxy == True:
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

    def __del__(self):
        self.browser_quit()

    def get_broswer(self, proxy_info = {}):
        self.browser_quit()

        if (self.use_proxy) and (not proxy_info):
            proxy_info = random.choice(self.proxy_list)

        if self.browser_type == 'chrome':
            opts = Options()
            opts.add_argument("--start-maximized")
            opts.add_argument("user-agent=%s" % (self.ua))
            if proxy_info:
                proxyauth_plugin_path = create_proxyauth_extension(
                    proxy_host = proxy_info['proxy_host'],
                    proxy_port = proxy_info['proxy_port'],
                    proxy_username = proxy_info['proxy_username'],
                    proxy_password = proxy_info['proxy_password']
                )
                opts.add_extension(proxyauth_plugin_path)
            if self.use_requests:
                self.browser = seleniumrequests.Chrome(chrome_options=opts)
            else:
                self.browser = webdriver.Chrome(chrome_options=opts)
        else:
            dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
            service_log_path = dirname + '/ghostdriver.log'
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = self.ua
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.resourceTimeout'] = '5000'
            service_args = [
                '--ignore-ssl-errors=true',
                '--load-images=true',
                '--disk-cache=true',
                '--disk-cache-path=%s' % (dirname + '/disk_cache')
            ]
            if proxy_info:
                service_args.extend([
                    '--proxy=%s:%s' % (proxy_info['proxy_host'], proxy_info['proxy_port']),
                    '--proxy-auth=%s:%s' % (proxy_info['proxy_username'], proxy_info['proxy_password']),
                    '--proxy-type=http'
                ])
            if self.use_requests:
                self.browser = seleniumrequests.PhantomJS(service_log_path=service_log_path, service_args=service_args)
            else:
                self.browser = webdriver.PhantomJS(service_log_path=service_log_path, service_args=service_args)
            self.browser.set_script_timeout(5)

        self.pid = self.browser.service.process.pid
        self.wait = ui.WebDriverWait(self.browser, 120)
        self.logger.info('get %s broswer\nUA:%s\nPROXY: %s:%s %s\nrequests:%ssupport',
                         self.browser_type if self.browser_type else 'phantomjs', self.ua,
                         proxy_info.get('proxy_host', ''), proxy_info.get('proxy_username', ''), proxy_info.get('source_ip', ''),
                         ' ' if self.use_requests else ' not ')
        return self.browser

    def browser_quit(self):
        try:
            if self.browser:
                self.browser.quit()
                os.kill(self.pid, 9)
        except Exception, e:
            self.logger.warning("browser quit error:%s" %(str(e)))
        finally:
            self.browser = None

    def init_mongo_db(self):
        while True:
            try:
                self.mongo_db = MongoClient('192.168.60.65', 10010).anti_ban
                break
            except Exception, e:
                self.logger.error('initialize mongo db error! (%s)', str(e))
                time.sleep(5)

def test():
    from time import sleep
    at = AntiBan('chrome')
    broswer = at.get_broswer()
    broswer.get('http://www.ip.cn')
    ele = broswer.find_element_by_xpath("//div[@id='result']/div[@class='well']/p[1]/code")
    ip = ele.text
    ele = broswer.find_element_by_xpath("//div[@id='result']/div[@class='well']/p[2]/code")
    local = ele.text
    print ip, local

def logInit(log_file, loglevel, consoleshow):
   logging.basicConfig(level=loglevel,
         format='[%(levelname)s] %(asctime)s %(message)s [%(filename)s:%(lineno)s]',
         datefmt='%Y-%m-%d %H:%M:%S',
         filename=log_file,
         filemode='a')
   if consoleshow:
      console = logging.StreamHandler()
      console.setLevel(loglevel)
      formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s [%(filename)s:%(lineno)s]')
      console.setFormatter(formatter)
      logging.getLogger('').addHandler(console)

if __name__ == '__main__':
    logInit('anti_ban.log', logging.INFO, True)
    test()
