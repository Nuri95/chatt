import select
import socket


class Server:
    def __init__(self):
        ip, port = socket.gethostname(), 5000
        self.header_length = 10
        self.message_byte = self.header_length + 1024

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen()
        self.sockets_list = [self.sock]

    def add_connections(self, client_socket):
        return self.sockets_list.append(client_socket)

    def get_connections(self):
        return self.sockets_list

    def start(self):

        while True:
            read_sockets, _, exception_sockets = select.select(
                self.get_connections(),
                [],
                self.get_connections()
            )
            for i in read_sockets:
                message_full = b''
                if i == self.sock:
                    client_socket, client_address = self.sock.accept()
                    header = client_socket.recv(self.header_length)
                    if header:
                        while len(header) >= self.message_byte:
                            message_full += client_socket.recv(
                                self.message_byte)
                            header -= self.message_byte
                        message_full += client_socket.recv(header)
                        return message_full
                    return False


class Message:
    def __init__(self):
        pass

server = Server()
server.start()
