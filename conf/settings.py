#! /usr/bin/env python
# -*-coding: utf-8 -*-
import os


HOME_PATH = os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'home')

DATA_PATH = os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), 'data')

ERROR_CODE = {
    "0000": "成功",
    "1000": "指令错误",
    "2000": "MD5校验失败",
    "3000": "文件路径错误",
    "4000": "权限错误",
    "5000": "用户名已存在",
    "6000": "请求异常",
    "7000": "用户名不存在",
    "8000": "用户名或密码不正确"
}
