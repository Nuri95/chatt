import socket
import select
import pickle


IP = socket.gethostname()  # IP сервера
PORT = 5000  # Порт
HEADER_LENGTH = 10  # Размер заголовка в символах
MESSAGE_BYTE = HEADER_LENGTH + 1024  # Сколько байт принимаем за раз
CLIENTS = {}  # Активные кленты <SOCKET>: {headers, login} / {headers, message, ...}


class Users:
    def user_from_a_socket(self, client_socket):
        """ По клиентскому сокету получаем логин"""
        for user in CLIENTS:
            if CLIENTS[user] == client_socket:
                return user


class MessagesProcessing(Users):

    def _message_decode_params(self, message, params):
        """ декодируем объект сообщения, достаем из него необходимый параметр """
        return pickle.loads(message['data'])[params]

    def send_messages(self, message, notified_socket):
        """
        Отправка сообщения.
        :param message: словарь, с сообщением
        :param notified_socket: сокет пользователя, с которым работаем в даннй момент
        :return: None
        """

        from_user_login = self.user_from_a_socket(notified_socket)
        from_user_header = bytes(
            f'{len(pickle.dumps({"login": from_user_login})):<{HEADER_LENGTH}}', 'utf-8'
        )
        from_user_data = pickle.dumps({"login": from_user_login})

        if self._message_decode_params(message, 'to'):
            for user in self._message_decode_params(message, 'to'):
                if user in CLIENTS:
                    return CLIENTS[user].send(
                    from_user_header + from_user_data + message['header'] + message['data'])

        for user in CLIENTS:
            if CLIENTS[user] != notified_socket:
                return CLIENTS[user].send(
                    from_user_header + from_user_data + message['header'] + message['data'])

    def receiving_messages(self, client_socket):
        """
        Читаем заголовок, получаем длинну сообщения
        :param client_socket: Текущая сессия
        :return: dict {header: bytes(Заголовок), data: bytes(Сообщение)}
        """
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(bytes.decode(message_header)):
            return False
        message_length = int(bytes.decode(message_header).strip())  # Получаем длинну сообщения
        return {'header': message_header, 'data': self.messages_processing(client_socket, message_length)}

    def messages_processing(self, client_socket, message_length: int):
        """
        Принимаем сообщение частями, если оно больше, чем MESSAGE_BYTE
        :param client_socket: Текущая сессия
        :param message_length: Длинна сообщения
        :return: bytes: Принятое сообщение
        """
        if message_length >= MESSAGE_BYTE:
            # Если принимаемое сообщение больше чем положено
            message_full = b''
            bytes_cale = message_length
            while bytes_cale >= MESSAGE_BYTE:
                # Принимаем до тех пор, пока остаток не будет меньше нашего сообщения
                message_full += client_socket.recv(MESSAGE_BYTE)
                bytes_cale -= MESSAGE_BYTE
            else:
                message_full += client_socket.recv(bytes_cale)
                return message_full
        return client_socket.recv(message_length)


class ChatsBasic(MessagesProcessing, Users):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((IP, PORT))
    server_socket.listen()
    sockets_list = [server_socket]  # Подключенные сокеты

    def connected_user(self):
        """
        Подключаем нового клиена. Возращаем скет
        :return: Сокет
        """
        client_socket, client_address = self.server_socket.accept()
        client = self.receiving_messages(client_socket)
        if not client:
            return False
        self.sockets_list.append(client_socket)
        CLIENTS[self._message_decode_params(client, 'login')] = client_socket

        print(f'Новое подключение. Клиент {client_address[0]}:{client_address[1]} '
              f"Логин: {pickle.loads(client['data'])}")
        return client_address, client_socket

    def disconnected_user(self, client_socket):
        self.sockets_list.remove(client_socket)
        del CLIENTS[self.user_from_a_socket(client_socket)]

    def processing(self):
        print('Сервер запущен')
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            # Опрашиваем активные сокеты, которым есть о чем с нами разговаривать
            for notified_socket in read_sockets:
                if notified_socket == self.server_socket:
                    # Принимаем новое подключение
                    if self.connected_user() is False:
                        continue
                else:
                    message = self.receiving_messages(notified_socket)
                    if message is False:
                        # Соединение закрыто
                        print(f"Соединение закрыто {self.user_from_a_socket(notified_socket)}")
                        self.disconnected_user(notified_socket)
                        continue
                    print(f"Принято новое сообщение от {self.user_from_a_socket(notified_socket)}: "
                          f"{pickle.loads(message['data'])}")
                    self.send_messages(message, notified_socket)
            for notified_socket in exception_sockets:
                self.disconnected_user(notified_socket)


ChatsBasic().processing()
