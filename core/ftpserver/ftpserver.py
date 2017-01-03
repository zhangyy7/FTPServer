#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socketserver
import os
import sys
import json
import time
import hashlib

base_dir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)


from conf import settings


class FtpServer(socketserver.BaseRequestHandler):
    """ftp服务器端请求处理类"""

    def handle(self):
        """处理客户端请求"""
        while True:
            try:
                print("{} connect !".format(self.client_address))
                head = self.request.recv(8192)
                if not head:
                    print("客户端已断开")
                    break
                head_str = head.decode()
                head_dict = json.loads(head_str)
                # print("size:", head_dict["size"], type(head_dict["size"]))
                action = head_dict.get("action", 0)
                if not action:
                    self.request.send(b'9999')
                    break
                else:
                    if hasattr(self, action):
                        func = getattr(self, action)
                        return func(head_dict)
                    else:
                        self.request.send(b'9998')
                        break
            except Exception as e:
                print(e)
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
            count = 0
            start = time.time()
            m = hashlib.md5()
            while recv_size < size:
                data = self.request.recv(min(1024, size - recv_size))
                m.update(data)
                f.write(data)
                recv_size += len(data)
                count += 1
            else:
                new_file_md5 = m.hexdigest()
                print(new_file_md5)
                print(time.time() - start)
                print("count:", count)
                print('接收到的文件大小为：', recv_size)
                print("文件{}接收成功".format(filename))
        client_file_md5 = self.request.recv(1024).decode()
        stat_code = '0000'
        if new_file_md5 != client_file_md5:
            print("md5校验通过")
            stat_code = '9997'
        self.request.send(stat_code.encode('utf-8'))

    def get(self, cmd_dict):
        """处理客户端下载文件的请求"""
        filepath = cmd_dict.get("filepath", 0)
        if not os.path.isfile(os.path.join(settings.HOME_PATH, filepath)):
            self.request.send(b'9995')
        else:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            head_dict = {"filename": filename, "size": filesize}
            head = json.dumps(head_dict, ensure_ascii=False)
            self.request.send(head.encode())  # 文件信息给客户端
        client_status_code = self.request.recv(1024).decode()
        if client_status_code == "0000":
            m = hashlib.md5()
            with open(filepath, 'rb') as f:
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

    def other_cmd(self, cmd):
        pass


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 9999), FtpServer)
    server.serve_forever()
