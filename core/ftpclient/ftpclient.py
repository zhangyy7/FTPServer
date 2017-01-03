#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socket
import hashlib
import os
import json


class FtpClient(object):
    """ftp客户端"""

    def __init__(self, ip, port):
        self.client = socket.socket()
        self.connect_to_server(ip, port)

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
                    "filename": os.path.basename(local_filepath),  # 获取文件名
                    "size": os.path.getsize(local_filepath),  # 获取文件大小
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

    def get(self, remote_filepath, local_file_path):
        """从服务端下载文件"""
        head = {
            "action": "get",
            "filepath": remote_filepath
        }
        self.client.send(json.dumps(head).encode('utf-8'))  # 发送下载请求
        server_response = self.client.recv(1024).decode('utf-8')
        if server_response == '9995':  # 服务端返回异常状态码
            return
        else:  # 服务端返回的不是异常状态
            head_dict = json.load(server_response)
            server_file_name = head_dict.get("filename", 0)
            try:
                server_file_size = int(head_dict.get("size", 0))
            except ValueError as e:
                print(e)
                return
            if all((server_file_name, server_file_size)):  # 判断服务端返回的2个数据是否正常
                self.client.send("0000".encode())  # 告诉服务端我已经准备好接收文件了
            else:
                return self.client.send('9999'.encode())  # 告诉服务端发给我的数据有异常
            m = hashlib.md5()
            with open(
                    os.path.join(
                        'local_file_path', 'server_file_name', 'wb')) as f:
                recv_size = 0
                while recv_size < server_file_size:  # 开始接收文件
                    data = self.client.recv(
                        min(1024, server_file_size - recv_size))
                    m.update(data)
                    f.write(data)
                else:
                    print("文件接收完毕")
            self.client.send("0000".encode())  # 告诉服务器我已经接收完毕了
            recv_file_md5 = m.hexdigest()
            server_file_md5 = self.client.recv(1024).decode()
            print(recv_file_md5, server_file_md5)
            if recv_file_md5 == server_file_md5:
                return "0000"
            else:
                pass


class FtpClientAccount(FtpClient):
    """ftp客户端账户类"""

    def register(self, username, password):
        """用户注册"""
        info_dict = {
            "action": "register",
            "username": username,
            "password": password
        }
        self.client.send(json.dumps(info_dict, ensure_ascii=False).encode())

    def login(self, username, password):
        pass


if __name__ == '__main__':
    client = FtpClient('192.168.1.111', 9999)
    # client.put(r'E:\python\pythonshouce.zip', '123')
    client.get(r'pythonshouce.zip', r'E:\python\hardway')
