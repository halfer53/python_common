#!/usr/bin/python
#coding:utf-8

import glob
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

def send_mail(title, content, mail_list, **kw):
    sender = 'nagios_sj@hc360.com'
    smtpserver='smtp.hc360.com'
    username='nagios_sj'
    password='abcd@1704!@#'

    msg=MIMEMultipart()

    ## mail body
    mail_html = \
    '''
    <p>%s</p>
    ''' % (content)

    ## attachment pic list
    if 'pic_list' in kw:
        for i, pic in enumerate(kw['pic_list']):
            mail_html += \
                    '''
                <img src="cid:%d">
                ''' % (i)
            fp = open(pic, 'rb')
            msg_image = MIMEImage(fp.read())
            fp.close()
            msg_image.add_header('Content-ID', str(i))
            msg.attach(msg_image)

    body =MIMEText(mail_html, _subtype='html', _charset='utf-8')
    msg.attach(body)

    ## attachment file list
    if 'file_list' in kw:
        for i, file_path in enumerate(kw['file_list']):
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(file_path, 'rb').read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' %(file_path if file_path.find('/') < 0 else file_path[file_path.rfind('/')+1:]))
            msg.attach(part)


    ## mail attribute
    msg['Subject']=title
    msg['From']='HC360_BI'
    msg['To']=';'.join(mail_list)
    msg['date']=time.strftime('%a, %d %b %Y %H:%M:%S %z')
    smtp=smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    for receiver_one in mail_list:
        smtp.sendmail(sender, receiver_one, msg.as_string())
    smtp.quit()

if __name__ == '__main__':
    pic_list = glob.glob('*.png')
    file_list = glob.glob('*.xlsx')
    print pic_list
    print file_list
    send_mail('test', 'test', ['mabosen@hc360.com',], pic_list=pic_list, file_list=file_list)
