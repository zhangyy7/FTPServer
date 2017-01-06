#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socket
import hashlib
import os
import json
import getpass

from conf import settings


class FtpClient(object):
    """ftp客户端"""

    def __init__(self, ip, port):
        self.client = socket.socket()
        self.connect_to_server(ip, port)

    def connect_to_server(self, ip, port):
        self.client.connect((ip, port))

    def route(self, cmd):
        """判断cmd是否存在，存在则执行cmd指令"""
        if cmd:
            action, *_ = cmd.split(maxsplit=1)
            if hasattr(self, action):
                func = getattr(self, action)
                return func(cmd)
            else:
                return '1000'
        else:
            return '1000'

    def put(self, cmd):
        """上传文件到客户端"""
        cmd, local_filepath, *remote_filepath = cmd.strip().split()
        print(local_filepath)
        try:
            if os.path.isfile(local_filepath):
                head = {
                    "action": "put",
                    # 获取文件名
                    "filename": os.path.basename(local_filepath),
                    # 获取文件大小
                    "size": os.path.getsize(local_filepath),
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

    def get(self, cmd):
        """从服务端下载文件"""
        print("开始下载")
        try:
            cmd, remote_filepath, local_file_path = cmd.strip().split()
        except ValueError:
            return print("请告诉我要把文件下载到哪个目录")
        head = {
            "action": "get",
            "filepath": remote_filepath
        }
        self.client.send(json.dumps(head).encode('utf-8'))  # 发送下载请求
        # print("发送请求给服务端")
        server_response = self.client.recv(1024).decode('utf-8')
        # print("get:first response:", server_response)
        if server_response == '3000':  # 服务端返回异常状态码
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
            # print(recv_file_md5, server_file_md5)
            if recv_file_md5 == server_file_md5:
                return "0000"

    def register(self, username, password):
        """用户注册"""
        m = hashlib.md5()
        m.update(password.encode())
        password = m.hexdigest()
        info_dict = {
            "action": "register",
            "username": username,
            "password": password
        }
        # print(info_dict)
        self.client.send(json.dumps(info_dict, ensure_ascii=False).encode())
        return self.client.recv(1024).decode()

    def login(self, username, password):
        m = hashlib.md5()
        m.update(password.encode())
        password = m.hexdigest()
        info_dict = {
            "action": "login",
            "username": username,
            "password": password
        }
        self.client.send(json.dumps(info_dict).encode())
        server_recv_size = int(self.client.recv(1024))
        # print(server_recv_size)
        self.client.send(b'0000')
        recv_size = 0
        data_list = []
        while recv_size < server_recv_size:
            data = self.client.recv(min(1024, server_recv_size - recv_size))
            data_list.append(data)
            recv_size += len(data)
        recv_data = b''.join(data_list).decode()
        recv_dict = json.loads(recv_data)
        # print(recv_dict)
        recv_status = recv_dict.get("status_code", 0)
        if recv_status == '0000':
            recv_dir = recv_dict.get("dir")
            self.my_current_dir = recv_dir
        return recv_status

    def cd(self, command):
        """切换目录"""
        cmd, *new_dir = command.strip().split(maxsplit=1)
        # print(new_dir)
        cmd_dict = {"action": cmd, "dir": new_dir}
        self.client.send(json.dumps(cmd_dict, ensure_ascii=False).encode())
        server_response = self.client.recv(1024).decode()
        if server_response == '4000':
            return 'server_response'
        self.my_current_dir = server_response
        return server_response

    def ls(self, command):
        """查看目录下的子目录和文件"""
        cmd, *new_dir = command.strip().split()
        # print(new_dir)
        if not new_dir:
            new_dir.append(self.my_current_dir)
        cmd_dict = {"action": cmd, "dir": new_dir[0]}
        # print(cmd_dict)
        self.client.send(json.dumps(cmd_dict, ensure_ascii=False).encode())
        server_response_size = int(self.client.recv(1024).decode())
        # print(server_response_size)
        if server_response_size == 1000:
            return
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
        return


class InterActive(FtpClient):
    """与用户交互"""

    def interactive(self):
        command = input("{}#".format(self.my_current_dir)).strip()
        if command == 'exit':
            exit("GoodBye")
        self.route(command)

    def login(self):
        username = input("请输入用户名:\n>>").strip()
        password = getpass.getpass("请输入密码：\n>>").strip()
        return super(InterActive, self).login(username, password)

    def register(self):
        username = input("请输入用户名:\n>>").strip()
        password = getpass.getpass("请输入密码：\n>>").strip()
        return super(InterActive, self).register(username, password)


def main():
    while True:
        try:
            ip = input("请输入IP服务器IP地址：\n>>").strip()
            port = int(input("请输入端口号：\n>>").strip())
            conn = InterActive(ip, port)
            break
        except ValueError:
            print("端口号必须是数字！")
            continue
        except ConnectionRefusedError:
            exit("服务端未开启，请联系管理员！")
    while True:
        choice = input("1.注册  2.登录")
        if choice == "1":
            while True:
                result = conn.register()
                # print("result", result)
                if result == "0000":
                    print("注册成功，请登录！")
                    break
                else:
                    print(result, settings.ERROR_CODE.get(result))
        if choice == "2":
            print("开始登录")
            result = conn.login()
            # print("result", result)
            if result == "0000":
                print("登录成功！")
                break
            else:
                print(settings.ERROR_CODE.get(result))
        if choice == "exit":
            exit("Goodbye")
        else:
            continue
    while True:
        try:
            conn.interactive()
        except ConnectionAbortedError:
            continue


if __name__ == '__main__':
    # client = FtpClient('localhost', 9999)
    # # client.put(r'D:\Temp\11111.JPG', '123')
    # client.get(r'11111.JPG', r'D:\QMDownload')
    main()
