""" echo server program for elo322 - Redes de Computadores """
import socket
import threading
import logging

logging.basicConfig(filename="server.log", level=logging.INFO)


class client_thread(threading.Thread):
    """ Echos the message from a client connection """

    def __init__(self, client_socket):
        super().__init__()
        self.socket = client_socket
        self.addr = self.socket.getpeername()
        logging.info("Connection from {0}".format(self.addr))

    def run(self):
        message_part = self.socket.recv(1024)
        message = b""
        while message_part:
            message += message_part
            message_part = self.socket.recv(1024)
        logging.info("Got '{0}' from {1}".format(message.decode("latin1"),
                                                 self.addr))
        self.socket.send(message)
        self.socket.close()


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
            client_socket, _ = listen_socket.accept()
        except KeyboardInterrupt:
            return

        cthread = client_thread(client_socket)
        cthread.run()


if __name__ == '__main__':
    main()
