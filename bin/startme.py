#! /usr/bin/env python
# -*-coding: utf-8 -*-

from core.ftpclient import ftpclient
from core.ftpserver import ftpserver


def run():
    choice = input("1.启动服务  2.运行客户端").strip()
    if choice == "1":
        ftpserver.main()
    if choice == "2":
        ftpclient.main()
