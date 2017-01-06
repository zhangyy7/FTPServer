#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socketserver
import os
import json
import time
import hashlib
import platform

from conf import settings


class FtpServer(socketserver.BaseRequestHandler):
    """ftp服务器端请求处理类"""

    def handle(self):
        """处理客户端请求"""
        print("{} connect !".format(self.client_address))
        # self.sys_sep = os.sep
        while True:
            try:
                head = self.request.recv(1024)
                if not head:
                    print("客户端已断开")
                    break
                head_str = head.decode()
                head_dict = json.loads(head_str)
                print(head_dict)
                action = head_dict.get("action", 0)
                if not action:
                    print("请求异常")
                    self.request.send(b'6000')  # 请求有异常
                    continue
                else:
                    if hasattr(self, action):
                        func = getattr(self, action)
                        func(head_dict)
                    else:
                        self.request.send(b'1000')  # 指令错误
                        print("没有这个指令")
                        continue
            except Exception as e:
                print(e)
                break

    def put(self, cmd_dict):
        """处理客户端上传文件的请求"""
        filename = cmd_dict["filename"]
        size = int(cmd_dict["size"])
        self.request.send(b'ok')
        with open(os.path.join(self.client_home_dir, filename), 'wb') as f:
            recv_size = 0
            start = time.time()
            m = hashlib.md5()
            while recv_size < size:
                data = self.request.recv(min(1024, size - recv_size))
                m.update(data)
                f.write(data)
                recv_size += len(data)
            else:
                new_file_md5 = m.hexdigest()
                print(new_file_md5)
                print(time.time() - start)
                print('接收到的文件大小为：', recv_size)
                print("文件{}接收成功".format(filename))
        client_file_md5 = self.request.recv(1024).decode()
        stat_code = '0000'
        if new_file_md5 != client_file_md5:
            print("md5校验不通过")
            stat_code = '2000'  # md5校验失败
        self.request.send(stat_code.encode('utf-8'))

    def get(self, cmd_dict):
        """处理客户端下载文件的请求"""
        filepath = cmd_dict.get("filepath", 0)
        print(filepath)
        server_filepath = os.path.join(self.client_home_dir, filepath)
        if not os.path.isfile(server_filepath):
            return self.request.send(b'3000')  # 文件路径不存在

        filename = os.path.basename(server_filepath)
        filesize = os.path.getsize(server_filepath)
        head_dict = {"filename": filename, "size": filesize}
        head = json.dumps(head_dict, ensure_ascii=False)
        self.request.send(head.encode())  # 文件信息给客户端
        client_status_code = self.request.recv(1024).decode()
        if client_status_code == "0000":
            m = hashlib.md5()
            with open(server_filepath, 'rb') as f:
                for line in f:
                    m.update(line)
                    self.request.send(line)
                else:
                    file_md5 = m.hexdigest()
                    print("文件发送完毕！")
            if self.request.recv(1024).decode() == "0000":
                self.request.send(file_md5.encode())
        else:
            return

    def register(self, userinfo_dict):
        """处理用户的注册请求"""
        print("开始注册")
        print(userinfo_dict)
        client_username = userinfo_dict.get("username", 0)
        client_password = userinfo_dict.get("password", 0)
        if all((client_username, client_password)):
            user_account_path = os.path.join(
                settings.DATA_PATH, client_username)
            user_home_path = os.path.join(
                settings.HOME_PATH, client_username)
            if os.path.isfile(user_account_path):
                return self.request.send(b'5000')  # 用户已存在
            os.mkdir(user_home_path)  # 创建用户的家目录
            with open(user_account_path, 'w') as f:
                userinfo = {"username": client_username,
                            "password": client_password}
                json.dump(userinfo, f, ensure_ascii=False)
            print("注册成功")
            return self.request.send(b'0000')
        else:
            return self.request.send(b'6000')  # 请求有异常

    def login(self, userinfo_dict):
        """用户登录"""
        print("开始登录")
        # print(userinfo_dict)
        client_username = userinfo_dict.get("username", 0)
        client_password = userinfo_dict.get("password", 0)
        if any((not client_username, not client_password)):  # 有任意一个条件为假
            msg = json.dumps({"status_code": "6000"}).encode()
            self.request.send(str(len(msg)).encode())
            self.request.recv(1024)
            return self.request.send(msg)  # 请求有异常
        user_path = os.path.join(settings.DATA_PATH, client_username)
        if not os.path.isfile(user_path):
            msg = json.dumps({"status_code": "7000"}).encode()
            self.request.send(str(len(msg)).encode())
            self.request.recv(1024)
            return self.request.send(msg)  # 用户名不存在
            print("没返回？")
        with open(user_path, 'r') as f:
            userinfo = json.load(f)
        username = userinfo.get("username", 0)
        password = userinfo.get("password", 0)
        if all((client_username == username, client_password == password)):
            self.client_home_dir = os.path.join(
                settings.HOME_PATH, client_username)
            self.current_dir = self.client_home_dir
            status_code = '0000'
        else:
            msg = json.dumps({"status_code": "8000"})
            return self.request.send(msg.encode())
        msg_dict = {"status_code": status_code, "dir": self.client_home_dir}
        print(msg_dict)
        msg = json.dumps(msg_dict, ensure_ascii=False).encode()
        self.request.send(str(len(msg)).encode())
        self.request.recv(1024)
        return self.request.send(msg)

    def ls(self, cmd):
        ls_dir = cmd.get("dir")
        myplatform = platform.uname().system
        if myplatform == "Windows":
            cmd = ["dir", ls_dir]
        else:
            cmd = "ls {}".format(ls_dir)
        print(cmd)
        msg = platform.subprocess.getoutput(cmd).encode()
        self.request.send(str(len(msg)).encode())
        self.request.recv(1024)
        return self.request.send(msg)

    def cd(self, cmd):
        """处理客户端切换目录请求"""
        new_dir = cmd.get("new_dir", [])
        slice_start = len(self.client_home_dir)
        current_dir_list = self.current_dir.split(os.sep)
        if not new_dir:
            self.current_dir = self.client_home_dir
        if new_dir[0] == "..":
            new_current_dir_list = current_dir_list[slice_start:-1]
            self.current_dir = os.path.join(
                self.client_home_dir, os.sep.join(new_current_dir_list))
        else:
            current_dir_list.append(new_dir[0])
            self.current_dir = os.sep.join(current_dir_list)
        if os.path.isdir(self.current_dir):
            status_code = '0000'
        else:
            status_code = '3000'
        msg_dict = {"status_code": status_code, "new_dir": self.current_dir}
        msg = json.dumps(msg_dict, ensure_ascii=False).encode()
        self.request.send(str(len(msg)).encode())  # 发送结果长度
        self.request.recv(1024)
        return self.request.send(msg)


def main():
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 9999), FtpServer)
    print("服务启动成功！")
    server.serve_forever()


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 9999), FtpServer)
    server.serve_forever()
