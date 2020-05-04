import socket
import select
import pickle


class CollectionClients:
    clients = {}

    def add_client(self, new_login):
        self.clients[new_login] = {'socket': None}

    def get_clients(self, login=None):
        if not login:
            return self.clients
        if login in self.clients:
            return self.clients[login]
        return False

    def get_login_from_sockets(self, sockets):
        for user in self.get_clients():
            if self.get_clients(user)['socket'] == sockets:
                return user
        return False

    def connected(self, login, client_socket):
        self.clients[login]['socket'] = client_socket

    def disconnected(self, login):
        self.clients[login]['socket'] = None


class ConnectionsActive:
    sockets_list = []

    def add_connections(self, client_socket):
        return self.sockets_list.append(client_socket)

    def get_connections(self):
        return self.sockets_list

    def delete_connections(self, client_socket):
        return self.sockets_list.remove(client_socket)


class StringParsing:
    def __init__(self, data):
        self.data = data

    def bytes_decode(self):
        return bytes.decode(self.data)

    def bytes_encode(self):
        return bytes(self.data, 'utf-8')

    def object_decode(self):
        return pickle.loads(self.data)

    def object_encode(self):
        return pickle.dumps(self.data)


class MessageProcessing:
    header_length = 10
    message_byte = header_length + 1024

    @staticmethod
    def _message_length(message):
        message = StringParsing(message)
        if not len(message.bytes_decode()):
            return False
        return int(message.bytes_decode().strip())

    def receiving_messages(self, client_socket):
        message_full = b''
        header = self._message_length(client_socket.recv(self.header_length))
        if header:
            while header >= self.message_byte:
                message_full += client_socket.recv(self.message_byte)
                header -= self.message_byte
            message_full += client_socket.recv(header)
            return message_full
        return False


class Server:
    ip = socket.gethostname()
    port = 5000
    sockets_list = ConnectionsActive()
    message = MessageProcessing()
    client = CollectionClients()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen()
    sockets_list.add_connections(server_socket)

    def connected(self, client_socket):
        if client_socket == self.server_socket:
            client_socket, client_address = self.server_socket.accept()

        data = self.message.receiving_messages(client_socket)
        if data is False:
            return False

        print(StringParsing(data).object_decode())

        if not self.client.get_login_from_sockets(client_socket):
            login = StringParsing(data).object_decode()['login']
            if not self.client.get_clients(login):
                self.client.add_client(login)
            self.client.connected(login, client_socket)
            self.sockets_list.add_connections(client_socket)
            print('Клиент подключен', login)
            return login


class ManagingConnection(Server):
    def __init__(self):
        self.connection_active = self.sockets_list
        self.exception_sockets = None

    def route(self):
        while True:
            print('route start')
            read_sockets, _, self.exception_sockets = select.select(
                self.connection_active.get_connections(),
                [],
                self.connection_active.get_connections()
            )
            for notified_socket in read_sockets:
                if self.connected(notified_socket) is False:
                    continue

            for notified_socket in self.exception_sockets:
                login = self.client.get_login_from_sockets(notified_socket)
                self.connection_active.delete_connections(notified_socket)
                self.client.disconnected(self.client.disconnected(login))


ManagingConnection().route()

