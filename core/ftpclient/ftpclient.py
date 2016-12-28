#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socket
import hashlib
import os
import json


class FtpClient(object):
    """ftp客户端"""

    def __init__(self):
        self.client = socket.socket()

    def connect_to_server(self, ip, port):
        self.client.connect((ip, port))

    def route(self, cmd):
        """判断cmd是否存在，存在则执行cmd指令"""
        action, filepath = cmd.split()
        if hasattr(self, action):
            func = getattr(self, action)
            return func(self, filepath)
        else:
            raise AttributeError("指令不正确")

    def put(self, local_filepath, remote_filepath=None):
        """上传文件到客户端"""
        if os.path.isfile(local_filepath):
            head = {
                "filename": os.path.basename(local_filepath),
                "size": os.path.getsize(local_filepath),
                "target_path": remote_filepath
            }
            self.client.send(json.dumps(head).encode(encoding='utf_8'))
            server_response = self.client.recv(4096)
            print(server_response)
            with open(local_filepath, 'rb') as f:
                for line in f:
                    self.client.send(line)
                else:
                    print("文件{}发送完毕！".format(filepath))
            self.client.close()
        else:
            raise OSError("文件不存在")

    def get(self, filename):
        pass


class FtpClientAccount(FtpClient):
    """ftp客户端账户类"""

    def __init__(self):
        pass

    def register(self, username, password):
        """用户注册"""

    def login(self, username, password):
        pass
