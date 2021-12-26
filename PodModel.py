# @Time    : 2021/10/21 5:46 下午
# @Author  : lichanghong
# @File    : PodModel.py

# !/usr/bin/python3
# coding=utf8

'''
pod信息模型
'''
class PodModel(object):
    # 组件名
    name = ''
    # 版本号
    tag = ''
    # git地址
    git = ''
    # 分支名
    branch = ''

    def __init__(self, name='', tag='', git='', branch=''):
        self.name = name
        self.tag = tag
        self.git = git
        self.branch = branch

    def logInfo(self):
        print("name:", self.name)
        print("tag:", self.tag)
        print("git:", self.git)
        print("branch:", self.branch)
