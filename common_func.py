import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
import datetime

def logInit(loglevel, log_file, backup_count=0, consoleshow=False):
    if not os.path.exists(log_file):
        dir_path, file_name = os.path.split(log_file)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
    fileTimeHandler = TimedRotatingFileHandler(log_file, "D", 1, backup_count)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    fileTimeHandler.setFormatter(formatter)
    logging.getLogger('').addHandler(fileTimeHandler)
    logging.getLogger('').setLevel(loglevel)
    if consoleshow:
      console = logging.StreamHandler()
      console.setLevel(loglevel)
      console.setFormatter(formatter)
      logging.getLogger('').addHandler(console)

def logInit2(loglevel, log_file, max_bytes, backup_count=0, consoleshow=False):
    if not os.path.exists(log_file):
        dir_path, file_name = os.path.split(log_file)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
    fileHandler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    fileHandler.setFormatter(formatter)
    logging.getLogger('').addHandler(fileHandler)
    logging.getLogger('').setLevel(loglevel)
    if consoleshow:
      console = logging.StreamHandler()
      console.setLevel(loglevel)
      console.setFormatter(formatter)
      logging.getLogger('').addHandler(console)

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

def get_ip_list_from_locale():
    import subprocess, re
    call_handle = subprocess.Popen('ip addr',  shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ip_buf = call_handle.stdout.readlines()
    ip_list = re.findall(r'(?<=inet )\d+\.\d+\.\d+\.\d+(?=/)', str(ip_buf))
    ip_pub_list = []
    for ip in ip_list:
        if re.match(r'^1(((0|27)(.(([1-9]?|1[0-9])[0-9]|2([0-4][0-9]|5[0-5])))|(72.(1[6-9]|2[0-9]|3[01])|92.168))(.(([1-9]?|1[0-9])[0-9]|2([0-4][0-9]|5[0-5]))){2})$', ip):
            continue
        ip_pub_list.append(ip)
    return ip_pub_list

def init_redis(is_tj=True):
    import redis

    redis_hosts = [
            ('10.10.10.27', 6379),
            ('172.16.252.22', 6379),
            ('192.168.245.31', 7901),
            ('172.16.248.22', 6379)
            ]
    if not is_tj:
        redis_hosts = redis_hosts[1:]

    r = None
    for host, port in redis_hosts:
        redis_pool = redis.ConnectionPool(host=host, port=port, socket_timeout=2)
        r = redis.Redis(connection_pool = redis_pool)
        try:
            last_len = r.llen('ALI_COMPANY_KEYWORD_LIST')
            break
        except redis.exceptions.ConnectionError:
            continue

    return r
