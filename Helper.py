# @Time    : 2021/10/21 5:06 下午
# @Author  : lichanghong
# @File    : Helper.py

# !/usr/bin/python3
# coding=utf8
import os
import shutil

import requests
import json
import DBManager


# 异常消息发到企业微信
def exceptionForWecom(msg):
    print('------------excetptin msg ------------')
    msg = '1222 ' + msg
    print(msg)
    DBManager.insert_error_info_data(msg)
    print('------------end excetptin msg ------------')

    url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=企业微信key发送群消息通知'
    headers = {'Content-Type': 'application/json'}
    data = {
        'msgtype': "text",
        'text': {
            "content": msg
        }
    }
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    print(response)


def clearCache(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir, ignore_errors=True)
