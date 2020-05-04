import socket
import struct
import sys
import threading


class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def emit(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)


class Message:
    TYPE = 1

    def __init__(self, text: str):
        self.text = text

    def serialize(self):
        return self.text.encode('utf-8')

    @staticmethod
    def deserialize(payload):
        return Message(payload.decode('utf-8'))


class Socket:
    sock = None
    def __init__(self):
        self.port = 5000
        self.header_length = 10
        self.ip = socket.gethostname()
        self.onMessage = EventHook()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.ip, self.port))
        client_socket.setblocking(False)
        self.sock = client_socket

    def start(self):
        self.listen_messages()

    def listen_messages(self):
        while True:
            header = self.sock.recv(self.header_length)
            if not len(header):
                sys.exit()
            t = 1
            payload = b'123123'
            if t == Message.TYPE:
                msg = Message.deserialize(payload)
                self.onMessage.emit(msg)

    def send(self, package):
        bytes = package.serialize()
        self.sock.send(struct.pack('LBs', len(bytes), package.TYPE, bytes))


class User:
    def __init__(self, s: Socket):
        s.onMessage += self.onMessage
        self.s = s

    def onMessage(self, message: Message):
        print('New msg: ' + message.text)

    def start(self):
        msg = input()
        s.send(Message(msg))
        pass


s = Socket()
socket_thread = threading.Thread(target=s.start)
user_thread = threading.Thread(target=User(s).start)
user_thread.start()
socket_thread.start()
user_thread.join()
socket_thread.join()

