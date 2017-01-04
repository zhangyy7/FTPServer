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
        action, *_ = cmd.split()
        if hasattr(self, action):
            func = getattr(self, action)
            return func(self, cmd)
        else:
            raise AttributeError("指令不正确")

    def put(self, cmd):
        """上传文件到客户端"""
        cmd, local_filepath, *remote_filepath = cmd.strip().split()
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

    def get(self, cmd, remote_filepath, local_file_path):
        """从服务端下载文件"""
        cmd, remote_filepath, *local_file_path = cmd.strip().split()
        head = {
            "action": "get",
            "filepath": remote_filepath
        }
        self.client.send(json.dumps(head).encode('utf-8'))  # 发送下载请求
        server_response = self.client.recv(1024).decode('utf-8')
        if server_response == '9995':  # 服务端返回异常状态码
            return
        else:  # 服务端返回的不是异常状态
            head_dict = json.loads(server_response)
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
            with open(os.path.join(local_file_path, server_file_name), 'wb') as f:
                recv_size = 0
                while recv_size < server_file_size:  # 开始接收文件
                    data = self.client.recv(
                        min(1024, server_file_size - recv_size))
                    if not data:
                        break
                    m.update(data)
                    f.write(data)
                    recv_size += len(data)
                else:
                    print("文件接收完毕！")
            self.client.send("0000".encode())  # 告诉服务器我已经接收完毕了
            recv_file_md5 = m.hexdigest()
            server_file_md5 = self.client.recv(1024).decode()
            print(recv_file_md5, server_file_md5)
            if recv_file_md5 == server_file_md5:
                return "0000"

    def register(self, username, password):
        """用户注册"""
        info_dict = {
            "action": "register",
            "username": username,
            "password": password
        }
        self.client.send(json.dumps(info_dict, ensure_ascii=False).encode())
        return self.client.recv(1024).decode()

    def login(self, username, password):
        info_dict = {
            "action": "login",
            "username": username,
            "password": password
        }
        self.client.send(json.dumps(info_dict).encode())
        server_recv_size = int(self.client.recv(1024))
        self.client.send(b'0000')
        recv_size = 0
        data_list = []
        while recv_size < server_recv_size:
            data = self.client.recv(min(1024, server_recv_size - recv_size))
            data_list.append(data)
            recv_size += len(data)
        recv_data = b''.join(data_list).decode()
        recv_dict = json.loads(recv_data)
        recv_status = recv_dict.get("status", 0)
        if recv_status == '0000':
            recv_dir = recv_dict.get("dir")
            self.dir = recv_dir
        return recv_status

    def cd(self, command):
        """切换目录"""
        cmd, new_dir = command.strip().split(maxsplit=1)
        cmd_dict = {"action": cmd, "dir": new_dir}
        self.client.send(json.dumps(cmd_dict, ensure_ascii=False).encode())
        server_response = self.client.recv(1024).decode()
        if server_response == '4000':
            return False
        self.dir = server_response

    def ls(self, command):
        """查看目录下的子目录和文件"""
        cmd, *new_dir = command.strip().split()
        if not new_dir:
            new_dir = self.dir
        cmd_dict = {"action": cmd, "dir": new_dir}
        self.client.send(json.dumps(cmd_dict, ensure_ascii=False).encode())
        server_response_size = int(self.client.recv(1024).decode())
        self.client.send(b'0000')
        recv_size = 0
        recv_data_list = []
        while recv_size < server_response_size:
            data = self.client.recv(
                min(1024, server_response_size - recv_size))
            recv_size += len(data)
            recv_data_list.append(data)
        cmd_result = b''.join(recv_data_list)
        print(cmd_result.decode())


class InterActive(FtpClient):
    """与用户交互"""

    def interactive(self):
        command = input("请输入指令：\n{}#".format(self.dir)).strip()
        if command == 'exit':
            exit("GoodBye")
        self.route(command)

    def login(self):
        username = input("请输入用户名:\n>>").strip()
        password = input("请输入密码：\n>>").strip()
        return super(InterActive, self).login(username, password)

    def register(self):
        username = input("请输入用户名:\n>>").strip()
        password = input("请输入密码：\n>>").strip()
        return super(InterActive, self).register(username, password)


def main():
    choice = input()


if __name__ == '__main__':
    client = FtpClient('localhost', 9999)
    # client.put(r'D:\Temp\11111.JPG', '123')
    client.get(r'11111.JPG', r'D:\QMDownload')
