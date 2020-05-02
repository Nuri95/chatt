import socket
import select
import pickle


HEADER_LENGTH = 10
IP = socket.gethostname()
PORT = 5000
CLIENTS = {}

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Опции, что бы мы могли с любым из клиентов восстановить соединение
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()
socket_list = [server_socket]  # Список известных сокетов


def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)  # Получаем заголовок
        if not len(message_header.decode('utf-8')):
            return False

        message_length = int(message_header.decode('utf-8').strip())  # Получаем длинну сообщения
        # Возвращаем заголовок и получаем сообщение длинной, которая указана в заголовке.
        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except Exception as error:
        print(error)
        return False


while True:
    read_sockets, _, exception_sockets = select.select(socket_list, [], socket_list,)
    # мы пробегаемся по листу соединений, где есть информация
    for notified_socket in read_sockets:
        # ??? Если уведоменным сокетом является сервер, то значит это новое соединение и мы должны его принять ???
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()
            user = receive_message(client_socket)
            if user is False:
                # Если подключение у пользователя сорвалось
                continue
            socket_list.append(client_socket)
            CLIENTS[client_socket] = user
            print(f'Новое подключение. Клиент {client_address[0]}:{client_address[1]} '
                  f"Логин: {pickle.loads(user['data'])}")
        else:
            message = receive_message(notified_socket)
            if message is False:
                # Если сообщение не удалось получить
                print(f"Соединение закрыто. От {pickle.loads(CLIENTS[notified_socket]['data'])}")
                socket_list.remove(notified_socket)
                del CLIENTS[notified_socket]
                continue
            user = CLIENTS[notified_socket]
            print(f"Принято новое сообщение от {pickle.loads(user['data'])}: {pickle.loads(message['data'])}")

            # Делимся полученным сообщением
            for client_socket in CLIENTS:
                if client_socket != notified_socket:
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

    for notified_socket in exception_sockets:
        socket_list.remove(notified_socket)
        del CLIENTS[notified_socket]
