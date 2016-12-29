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
        try:
            if os.path.isfile(local_filepath):
                head = {
                    "action": "put",
                    "filename": os.path.basename(local_filepath),
                    "size": os.stat(local_filepath).st_size,
                    "target_path": remote_filepath
                }
                self.client.send(json.dumps(
                    head, ensure_ascii=False).encode(encoding='utf_8'))
                print("发送head完毕")
                server_response = self.client.recv(8192)
                print(server_response)
                m = hashlib.md5()
                with open(local_filepath, 'rb') as f:
                    for line in f:
                        m.update(line)
                        self.client.send(line)
                    else:
                        file_md5 = m.hexdigest()
                        print("文件{}发送完毕！".format(local_filepath))
                self.client.send(file_md5.encode('utf-8'))
                server_file_md5 = self.client.recv(1024).decode('utf-8')
                print(server_file_md5, file_md5)
                if server_file_md5 == file_md5:
                    return True
            else:
                raise OSError("文件不存在")
        except Exception as e:
            print(e)

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


if __name__ == '__main__':
    client = FtpClient()
    client.connect_to_server('localhost', 9999)
    client.put(r'D:\Temp\11111.JPG', '123')
