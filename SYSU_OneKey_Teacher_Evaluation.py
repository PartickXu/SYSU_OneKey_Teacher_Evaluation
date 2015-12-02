#!/usr/bin/env python
# -*- coding: utf-8 -*-
# python verson: 2.7
# @Author: JinJin Lin
# @Email: jinjin.lin@outlook.com
# @License: MIT
# @Date:   2015-12-02 16:16:31
# @Last Modified time: 2015-12-03 01:20:22
# All copyright reserved
#

from PIL import Image
from PIL import ImageChops
import os
import demjson
# import pytesseract
import pytesser
import requests
import hashlib
import json
from bs4 import BeautifulSoup
from StringIO import StringIO

class PingJiao:
    def __init__(self, username, password, year, term):
        self._session = requests.Session()
        self.passwordMd5 = hashlib.md5(password.encode("utf-8")).hexdigest().upper()
        self.username = username
        self.year = year
        self.term = term

    def login(self):
        print 'Login...'
        req = self._session.get(
            "http://uems.sysu.edu.cn/jwxt",
            headers={'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}
        )
        soup = BeautifulSoup(req.content.decode("utf-8"))
        rno = soup.find(id='rno')['value']

        req = self._session.get("http://uems.sysu.edu.cn/jwxt/jcaptcha", stream=True)
        im = Image.open(StringIO(req.content))
        code = self.getCode(im)
        loginData = {
            "j_username": self.username,
            "j_password": self.passwordMd5,
            "jcaptcha_response": code,
            "rno": rno
        }
        req = self._session.post("http://uems.sysu.edu.cn/jwxt/j_unieap_security_check.do", data=loginData)
        soup = BeautifulSoup(req.content.decode('utf-8'))
        if req.status_code == 200:
            text = soup.find('title')
            if text is not None and text.get_text() == u'首页':
                print u'登陆失败，有可能是验证码识别出错或账号密码错误,可重新尝试运行程序'
                return False
            print u'登陆成功!'
            return True
        else:
            print u'服务器出错'
            return False

    def getCode(self, im):
        im = im.convert('L')
        im = im.point(lambda x:255 if x > 128 else x)
        im = im.point(lambda x:0 if x < 255 else 255)
        box = (2, 2, im.size[0] - 2, im.size[1] - 2)
        im = im.crop(box)
        code = pytesser.image_to_string(im).replace(' ', '').strip()
        return code

    def run(self):
        print u'获取课程中...'
        courseList = self.getCourse()
        if len(courseList) == 0:
            print u'没有需要评教的课程'
            return
        print u'共获取到', len(courseList), u'门未评教的课程,开始评教...'
        self.evaluaCourses(courseList)

    def evaluaCourses(self, courseList):
        for course in courseList:
            print u'系统正在评', course['kcmc'], '课程,请等待....'
            self.evaluaCourse(course)
            print '---------------------------------------'
        print u'所有课程评教完成 !'

    def evaluaCourse(self, course):
        questionList = self.getQuesList(course['khtxbh'])
        ansList = self.ansQue(questionList)
        bjid = self.getBJID(course)
        postdata = {
            'header':{
                "code": -100,
                "message": {"title": "", "detail": ""}
            },
            'body':{
                'dataStores':{
                    'itemStore':{
                        'rowSet':{
                            "primary": ansList,
                            "filter":[],
                            "delete":[]
                        },
                        'name':"itemStore",
                        'pageNumber':1,
                        'pageSize':2147483647,
                        'recordCount':14,
                        'rowSetName':"pojo_com.neusoft.education.sysu.pj.xspj.entity.DtjglyEntity"
                    }
                },
                'parameters':{
                    "args": ["ds_itemStore_all", bjid],
                    "responseParam": "bj"
                }
            }
        }
        headers = {
            'Accept': '*/*',
            'ajaxRequest': 'true',
            'render': 'unieap',
            '__clientType': 'unieap',
            'workitemid': 'null',
            'resourceid': 'null',
            'Content-Type': 'multipart/form-data',
            'Referer': 'http://uems.sysu.edu.cn/jwxt/forward.action?path=/sysu/wspj/xspj/jxb_pj',
            'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729)',
            'Host': 'uems.sysu.edu.cn',
            'Content-Length': 1410,
            'Connection': 'Keep-Alive',
            'Pragma': 'no-cache'
        }
        req = self._session.post("http://uems.sysu.edu.cn/jwxt/xspjaction/xspjaction.action?method=saveWjxxbyly", headers=headers, json=postdata)
        if req.status_code == 200:
            data = demjson.decode(req.content.decode('utf-8'))
            if data['body']['parameters']['bj'] == 'OK':
                print u'评教', course['kcmc'], u'课程, 成功!'
        else:
            print 'Fail'

    def ansQue(self, questionList):
        ansList = []
        jg = 5799273910
        for que in questionList:
            wtid = que['resourceId']
            ansList.append({'wtid':wtid, 'jg':str(jg), 'gxbh':'', 'resource_id':'', '_t':"1"})
            jg += 4
        return ansList

    def getQuesList(self, courseID):
        postdata = {
            "header":{
                "code": -100,
                "message": {"title": "", "detail": ""}
            },
            "body":{
                "dataStores":{
                    "wjStroe":{
                        "rowSet":{"primary":[],"filter":[],"delete":[]},
                        "name":"wjStroe",
                        "pageNumber":1,
                        "pageSize":2147483647,
                        "recordCount":0,
                        "rowSetName":"pojo_com.neusoft.education.sysu.pj.xspj.model.WjlyModel",
                        "order":" XSSX ASC "
                    }
                },
                "parameters":{"args": [courseID]}
            }
        }
        headers = {
            'Accept': '*/*',
            'ajaxRequest': 'true',
            'render': 'unieap',
            '__clientType': 'unieap',
            'workitemid': 'null',
            'resourceid': 'null',
            'Content-Type': 'multipart/form-data',
            'Referer': 'http://uems.sysu.edu.cn/jwxt/forward.action?path=/sysu/wspj/xspj/jxb_pj',
            'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729)',
            'Host': 'uems.sysu.edu.cn',
            'Content-Length': 325,
            'Connection': 'Keep-Alive',
            'Pragma': 'no-cache' 
        }
        req = self._session.post("http://uems.sysu.edu.cn/jwxt/xspjaction/xspjaction.action?method=getWjxx", headers=headers, json=postdata)
        return self._parseToQueList(req.content.decode("utf-8"))

    def getCourse(self):
        postdata = {
            "header": {
                "code": -100,
                "message": {"title": "", "detail": ""}
            },
            "body": {
                "dataStores":{
                    "pj1Stroe":{
                        "rowSet":{
                            "primary":[],
                            "filter":[],
                            "delete":[]
                        },
                        "name":"pj1Stroe",
                        "pageNumber":1,
                        "pageSize":50,
                        "recordCount":0,
                        "rowSetName":"pojo_com.neusoft.education.sysu.pj.xspj.model.PjsyfwModel"}
                },
                "parameters":{"args": []}
            }
        }
        headers = {
            "Accept": "*/*",
            "ajaxRequest": "true",
            "render": "unieap",
            "__clientType": "unieap",
            "workitemid": "null",
            "resourceid": "null",
            "Content-Type": "multipart/form-data",
            "Referer": "http://uems.sysu.edu.cn/jwxt/forward.action?path=/sysu/wspj/xspj/xspj_list&xnd="+self.year+"&xq="+self.term,
            "Accept-Language": "en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729)",
            "Host": "uems.sysu.edu.cn",
            "Content-Length": 290,
            "Connection": "Keep-Alive",
            "Pragma": "no-cache",
        }
        req = self._session.post("http://uems.sysu.edu.cn/jwxt/xspjaction/xspjaction.action?method=getXspjlist", headers=headers, json=postdata)
        return self._parseToCourseList(req.content.decode("utf-8"))

    def getBJID(self, course):
        postdata = {
            'header':{
                "code": -100, 
                "message": {"title": "", "detail": ""}
            },
            'body':{
                'dataStores':{},
                'parameters':{
                    "args": [course['jsbh'], course['kch'], course['khlx'], course['jxbh'], course['khtxbh'], course['pjlx']], 
                    "responseParam": "bjid"
                }
            }
        }
        headers = { 
            'Accept': '*/*',
            'ajaxRequest': 'true',
            'render': 'unieap',
            '__clientType': 'unieap',
            'workitemid': 'null',
            'resourceid': 'null',
            'Content-Type': 'multipart/form-data',
            'Referer': 'http://uems.sysu.edu.cn/jwxt/forward.action?path=/sysu/wspj/xspj/jxb_pj',
            'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.3; WOW64; Trident/7.0; .NET4.0E; .NET4.0C; .NET CLR 3.5.30729; .NET CLR 2.0.50727; .NET CLR 3.0.30729)',
            'Host': 'uems.sysu.edu.cn',
            'Content-Length': 196,
            'Connection': 'Keep-Alive',
            'Pragma': 'no-cache'
        }
        req = self._session.post("http://uems.sysu.edu.cn/jwxt/xspjaction/xspjaction.action?method=getPjsyfwbzj", headers=headers, json=postdata)
        data = demjson.decode(req.content.decode('utf-8'))
        return data['body']['parameters']['bjid']

    def _parseToCourseList(self, reqJson):
        reqJson = demjson.decode(reqJson)
        courseList = reqJson['body']['dataStores']['pj1Stroe']['rowSet']['primary']
        return courseList

    def _parseToQueList(self, reqJson):
        reqJson = demjson.decode(reqJson)
        questionList = reqJson['body']['dataStores']['wjStroe']['rowSet']['primary']
        return questionList

if __name__ == "__main__":
    debug = False
    os.system("cls")
    print '============================================================================'
    print '                                                                            '
    print '                Welcome, SYSU OneKey Teacher Evaluation  V1.0               '
    print '                      '+u'中山大学一键评教，默认评最高分'
    print '                                                                            '
    print '                                                 Design By: JinJin Lin      '
    print '                                                 jinjin.lin@outlook.com     '
    print '                                                Github.com/linjinjin123     '
    print '                                                                            '
    print '                                                               2015.12.2    '
    print '                                                                            '
    print '============================================================================'
    if debug == True:
        year = '2015-2016'
        term = '2'
        username = '13331149'
        password = ''
    else:
        year = raw_input('Please input year(The format is 2015-2016)\n')
        term = raw_input('Please input the number of semester: \n1.first \n2.second \n3.third\n')
        username = raw_input('Username:')
        password = raw_input('Password:')    
    pingjiao = PingJiao(username, password, year, term)
    pingjiao.login()
    pingjiao.run()
    print u'程序运行结束，是否成功请登陆教务系统查看'
    raw_input(u'Enter any key to quit')
