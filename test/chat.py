""" Simple chat program for elo322 - Redes de Computadores """
import socket
import threading
import sys
import logging
import select

logging.basicConfig(filename="chat.log", level=logging.DEBUG)


class client_thread(threading.Thread):
    """ Prints the message from a client connection """

    def __init__(self, client_socket):
        super().__init__()
        self.socket = client_socket
        self.addr = self.socket.getpeername()

    def run(self):
        logging.debug("Client thread started")
        message_part = self.socket.recv(1024)
        message = b""
        while message_part:
            message += message_part
            message_part = self.socket.recv(1024)
        message = message.decode('latin1')
        logging.debug("Got message {0} from {1}".format(message, self.addr))
        print(message)


class listen_thread(threading.Thread):
    """ Thread that listenes for connections and user input, spawns a
    client_thread on connection and send_thread on user input """
    def __init__(self, host_port, remote_port):
        super().__init__()
        self.host_port = host_port
        self.remote_port = remote_port

    def run(self):
        logging.debug("Listen thread started")
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        host = socket.gethostname()
        listen_socket.bind((host, self.host_port))

        listen_socket.listen(5)
        listen_socket.setblocking(0)
        while True:
            try:
                inputready, _, _ = select.select([listen_socket, sys.stdin],
                                                 [], [], 0)
            except KeyboardInterrupt:
                listen_socket.close()
                print("Shutting down")
                break

            for s in inputready:
                if s == listen_socket:
                    client_socket, _ = listen_socket.accept()
                    cthread = client_thread(client_socket)
                    cthread.start()
                elif s == sys.stdin:
                    s_thread = send_thread(host, self.remote_port)
                    s_thread.start()
        logging.debug("Listen thread shutting down")


class send_thread(threading.Thread):
    """ Send message from stdin to (host, port) assume local host if nothing
    else given """

    def __init__(self, host=socket.gethostname(), port=12345):
        super().__init__()
        self.port = port
        self.host = host
        self.message = sys.stdin.readline().rstrip()

    def run(self):
        # Internet socket and TCP
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            send_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            logging.warning("Could not connect to {0}".format((self.host,
                                                               self.port)))
            return

        logging.debug("Sending message {0}".format(self.message))
        send_socket.send(self.message.encode('latin1'))
        send_socket.close()


def main():
    """ Main program """

    try:
        host_port, remote_port = int(sys.argv[1]), int(sys.argv[2])
    except (ValueError, IndexError):
        print("Usage: python chat.py host_port remote_port")
        sys.exit(1)

    l_thread = listen_thread(host_port, remote_port)
    l_thread.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
