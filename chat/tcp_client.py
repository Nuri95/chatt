import socket
import errno
import sys
import threading
import pickle


HEADER_LENGTH = 10
IP = socket.gethostname()
PORT = 5000

my_username = input("Login: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)


def read_sockets():
    # Отдельный процесс получения сообщений
    while True:
        try:
            # Независимо, ввели мы сообщение или нет, мы пытаемся получить сообщения от сервера
            username_header = client_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                print('Соединение закрыто сервером')
                sys.exit()

            username_length = int(bytes.decode(username_header).strip())
            username = client_socket.recv(username_length)

            in_message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(bytes.decode(in_message_header).strip())
            in_message = client_socket.recv(message_length)

            print(f'[{pickle.loads(username)}] > {pickle.loads(in_message)}')
        except IOError as error:
            if error.errno != errno.EAGAIN and error.errno != errno.EWOULDBLOCK:
                print('Ошибка чтения', str(error))
                sys.exit()
            continue
        except Exception as error:
            print('Ошибка приложения', str(error))
            sys.exit()


my_username = pickle.dumps({"login": my_username})
my_username_header = f'{len(my_username):<{HEADER_LENGTH}}'
client_socket.send(bytes(f'{my_username_header}', 'utf-8') + my_username)

potok = threading.Thread(target=read_sockets)
potok.start()

# Пишем сообщение
while True:
    out_message = input()
    if out_message:
        out_message = pickle.dumps({"message": out_message, 'to': ['kolyan', 'mary']})
        out_message_header = f'{len(out_message):<{HEADER_LENGTH}}'
        client_socket.send(bytes(out_message_header, 'utf-8') + out_message)
