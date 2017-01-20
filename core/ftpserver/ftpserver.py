#! /usr/bin/env python
# -*-coding: utf-8 -*-
import socketserver

import logging.config
from . import requesthandler
from conf import settings


logging.config.dictConfig(settings.LOGGING_DIC)
logger = logging.getLogger(__name__)


def main():
    server = socketserver.ThreadingTCPServer(
        ('0.0.0.0', 9999), requesthandler.RequestHandler)
    print("服务启动成功！")
    server.serve_forever()


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('0.0.0.0', 9999), FtpServer)
    server.serve_forever()
