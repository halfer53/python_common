#!/usr/bin/python
#coding:utf-8

import smtplib
import time
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

PHONE_MAIL = {
'mabosen@hc360.com': '18210607604@139.com',
'guona@hc360.com': '18201166786@139.com',
}

def send_mail(title, content, mail_list, file_path = ''):
    sender = 'searchmonitor@hc360.com'
    smtpserver='smtp.hc360.com'
    username='searchmonitor'
    password='5633d0346aaf'

    msg=MIMEMultipart()

    ## mail body
    body =MIMEText(content, _subtype='plain', _charset='utf-8')
    msg.attach(body)

    ## mail attachment
    if file_path:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(file_path, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' %(file_path if file_path.find('/') < 0 else file_path[file_path.rfind('/')+1:]))
        msg.attach(part)


    ## mail attribute
    msg['Subject']=title
    msg['From']='Spider_Monitor'
    msg['To']=';'.join(mail_list)
    msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')
    smtp=smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    for receiver_one in mail_list:
        smtp.sendmail(sender, receiver_one, msg.as_string())
    smtp.quit()

if __name__ == '__main__':
    # send_mail('test', 'test', ['mabosen@hc360.com',])
    #send_mail('test', 'test', ['mabosen@hc360.com',], 'result_2016-06-07.csv')
    import sys, os
    if len(sys.argv) >= 4:
        title = sys.argv[1]
        body = sys.argv[2]
        mail_list_str = sys.argv[3]
        mail_list = mail_list_str.split(',')

        if len(sys.argv) >= 5 and os.path.isfile(sys.argv[4]):
            file_name = sys.argv[4]
            send_mail(title, body, mail_list, file_name)
            
        else:
            send_mail(title, body, mail_list)

