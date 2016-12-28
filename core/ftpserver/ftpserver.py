#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socketserver
import os


class FtpServer(socketserver.StreamRequestHandler):
    """ftp服务器端请求处理类"""

    def handle(self):
        """处理客户端请求"""
        while True:
            pass

    def put(self, cmd_dict):
        """处理客户端上传文件的请求"""
        filename = cmd_dict["filename"]
        size = int(cmd_dict["size"].decode("utf-8"))
        target_path = cmd_dict["target_path"]
        with open(os.path.join(target_path, filename), 'wb') as f:
            recv_size = 0
            while recv_size < size:
                for line in self.rfile:
                    f.write(line)
