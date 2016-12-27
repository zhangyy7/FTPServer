#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socket


class FtpClient(object):
    """ftp客户端"""

    def __init__(self, user_obj):
        self.client = socket.socket()
        self.user = user_obj

    def connect_to_server(self, user_obj, ip, port):
        pass

    def put(self, filename):
        """上传文件到客户端"""
        pass

    def get(self, filename):
        pass


class FtpClientAccount(object):
    """ftp客户端账户类"""

    def __init__(self):
        pass

    def register(self, username, password):
        pass

    def login(self, username, password):
        pass
