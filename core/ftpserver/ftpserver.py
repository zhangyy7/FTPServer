#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socketserver


class FtpServer(socketserver.StreamRequestHandler):
    """ftp服务器端请求处理类"""

    def handle(self):
        pass
