#! /usr/bin/env python
# -*-coding: utf-8 -*-

from core.ftpclient import ftpclient
from core.ftpserver import ftpserver
from core.ftpserver import selector_socket_server


def run():
    while True:
        choice = input("1.启动服务  2.运行客户端").strip()
        if choice == "1":
            while True:
                inp = input("请选择启用那种模式的服务器：【1.多线程  2.协程】").strip()
                if inp == "1":
                    ftpserver.main()
                elif inp == "2":
                    selector_socket_server.main()
                else:
                    continue
        elif choice == "2":
            ftpclient.main()
        else:
            continue
