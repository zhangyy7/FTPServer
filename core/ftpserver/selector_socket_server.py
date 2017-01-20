import socket
import selectors
import threading
import logging.config
from conf import settings
from . import requesthandler


logging.config.dictConfig(settings.LOGGING_DIC)
logger = logging.getLogger(__name__)


class SelectorsSocketserver(object):
    """基于selectors实现的socketserver类"""
    request_queue_size = 5  # listen的参数，允许等待的最大连接数
    allow_reuse_address = False  # 这个标记是用来判断是否允许地址重用

    # 第一步
    def __init__(self, port, RequestHandlerClass, bind_and_activate=True):
        self.port = port  # 端口
        self.socket = socket.socket()  # 实例化一个socket
        # 定义selector的类型，DefaultSelector就是系统支持那种底层就用哪种底层(select|epoll)
        self.selector = selectors.DefaultSelector
        self.RequestHandlerClass = RequestHandlerClass  # 把RequestHandlerClass绑定到server实例
        self.__is_shut_down = threading.Event()  # 实例化一个事件，相当于一个红绿灯，红灯停绿灯行
        self.__shutdown_request = False  # 请求实例关闭标记
        if bind_and_activate:  # 尝试绑定和监听，有异常就关闭server实例，并抛出异常
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

    def server_bind(self):
        """由构造方法调用，用来bind socket"""
        if self.allow_reuse_address:
            self.socket.setsocketopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.server_address = self.socket.getsockname()

    def server_activate(self):
        """由构造方法调用，用来启监听"""
        self.socket.listen(self.request_queue_size)

    def server_close(self):
        """关闭服务连接"""
        self.socket.close()

    # 第二步
    def serve_forever(self, poll_interval=0.5):
        self.__is_shut_down.clear()  # 将红绿灯设置为绿灯，把请求放行
        try:
            with self.selector() as selector:
                # 把server实例自己交给selector监视
                selector
                selector.register(self.socket, selectors.EVENT_READ)

                while not self.__shutdown_request:  # 如果客户端连接没有关闭
                    # 如果系统支持异步模式(select,epoll等)，会返回一个列表，否则返回的是空列表
                    ready = selector.select(poll_interval)
                    if ready:
                        self._handle_request_noblock()  # 如果ready不是空值就把客户端连接设置为非阻塞
                    # self.service_actions()
        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()  # 将红绿灯设置为红灯，阻塞请求

    def _handle_request_noblock(self):
        """以非阻塞的方式处理一个请求"""
        try:
            request, client_address = self.get_request()  # 获取请求
        except OSError:
            return
        try:
            self.process_request(request, client_address)  # 处理请求
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    # def service_actions(self):
    #     """Called by the serve_forever() loop.

    #     May be overridden by a subclass / Mixin to implement any code that
    #     needs to be run during the loop.
    #     """
    #     pass

    def get_request(self):
        """获取请求"""
        return self.socket.accept()

    def process_request(self, request, client_address):
        """这个方法就是调用finish_request"""
        self.finish_request(request, client_address)
        self.shutdown_request(request)

    def finish_request(self, request, client_address):
        """调用真正处理请求的RequestHandlerClass"""
        self.RequestHandlerClass(request, client_address, self)

    def shutdown_request(self, request):
        try:
            request.shutdown(socket.SHUT_WR)
        except OSError:
            pass

        self.close_request(request)

    def close_request(self, request):
        request.close()

    def handle_error(self, request, client_address):
        """优雅的处理一个错误"""
        print('-' * 40)
        print('处理请求时发生了异常', end=' ')
        import traceback
        traceback.print_exc()
        print('-' * 40)


def main():
    server = SelectorsSocketserver(9999, requesthandler.RequestHandler)
    print("服务启动成功！")
    server.serve_forever()


if __name__ == '__main__':
    main()
