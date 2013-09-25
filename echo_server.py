""" echo server program for elo322 - Redes de Computadores """
import socket
import logging

logging.basicConfig(filename="server.log", level=logging.INFO)


def main():
    """ Main function of chat server """
    # Internet socket and TCP
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Local host
    host = socket.gethostname()
    port = 12345

    listen_socket.bind((host, port))

    listen_socket.listen(5)
    while True:
        try:
            client_socket, addr = listen_socket.accept()
        except KeyboardInterrupt:
            return
        logging.info("client_socketection from {0}".format(addr))
        message_part = client_socket.recv(1024)
        message = b""
        while message_part:
            message += message_part
            message_part = client_socket.recv(1024)
        logging.info("Got '{0}' from {1}".format(message.decode("utf-8"),
                                                 addr))
        client_socket.send(message)
        client_socket.close()

if __name__ == '__main__':
    main()
