#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socketserver
import os
import json


class FtpServer(socketserver.StreamRequestHandler):
    """ftp服务器端请求处理类"""

    def handle(self):
        """处理客户端请求"""
        while True:
            head = self.connection.recv(8192)
            print(len(head))
            head_str = head.decode()
            print(type(head_str), head_str)
            head_dict = json.loads(head_str)
            print(type(head_dict), head_dict)
            action = head_dict.get("action", 0)
            if not action:
                self.request.send(b'9999')
                break
            else:
                if hasattr(self, action):
                    func = getattr(self, action)
                    func(head_dict)
                else:
                    self.request.send(b'9998')
                    break

    def put(self, cmd_dict):
        """处理客户端上传文件的请求"""
        filename = cmd_dict["filename"]
        size = int(cmd_dict["size"])
        self.request.send(b'ok')
        with open(
            os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.abspath(__file__)))),
                'home', filename), 'wb') as f:
            recv_size = 0
            while recv_size < size:
                data = self.request.recv(min(size - recv_size, 8192))
                f.write(data)
                # print(min(size - recv_size, 8192))
                recv_size += min(size - recv_size, 8192)
            else:
                print(recv_size)
                print("文件{}接收成功".format(filename))


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 9999), FtpServer)
    server.serve_forever()
