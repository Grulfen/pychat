""" Chat program for ELO322 """
import sys
import socket
import logging
import select
import time
from queue import Queue
from argparse import ArgumentParser
from collections import namedtuple
from PyQt4 import QtGui, QtCore
from multiprocessing import Process, Pipe

logging.basicConfig(level=logging.INFO)

Address = namedtuple('Address', ['name', 'port'])


class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args, **self.kwargs)
        return


class Chat(QtGui.QWidget):
    text_add = QtCore.pyqtSignal(str, name="new_message")

    def __init__(self, host, remote, friend, send_queue):
        super().__init__()

        self.host = host
        self.remote = remote
        self.initUI()
        self.friend = friend
        self.send_queue = send_queue

    def initUI(self):
        self.earlier_messages = QtGui.QTextEdit()
        self.earlier_messages.setReadOnly(True)

        self.message = QtGui.QTextEdit()
        self.message.setMaximumHeight(60)
        self.message.keyPressEvent = self.message_key_handler

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.earlier_messages)
        vbox.addWidget(self.message)

        self.setLayout(vbox)

        self.text_add.connect(self.add_message)
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Chat')
        self.show()

    def spawn_send_thread(self, message):
        send_thread = GenericThread(self.send_message, message=message)
        send_thread.start()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def message_key_handler(self, e):
        if (e.key() == QtCore.Qt.Key_Return) or \
                (e.key() == QtCore.Qt.Key_Enter):
            text = self.message.toPlainText()
            if text:
                self.send_queue.put(text)
                self.earlier_messages.append("yo: " + text)
                self.message.clear()
                # self.spawn_send_thread(text)
        else:
            QtGui.QTextEdit.keyPressEvent(self.message, e)

    def send_message(self, message):
        # Internet socket and TCP
        remote = self.remote
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            send_socket.connect(remote)
        except ConnectionRefusedError:
            logging.warning("Could not connect to {0}".format(remote))
            return

        logging.debug("Sending message {0} to  {1}".format(message, remote))
        send_socket.send(message.encode('latin1'))
        send_socket.close()

    def add_message(self, message):
        self.earlier_messages.append("{0}: ".format(self.friend) + message)


def wait_send(queue, chat):
    while True:
        if not queue.empty():
            message = queue.get()
            chat.send_message(message)


def wait_receive(get_pipe, signal):
    while True:
        if(get_pipe.poll()):
            message = get_pipe.recv()
            signal.emit(message)
        time.sleep(0.01)


def listen_thread(host, send_pipe):
    """ Thread that awaits incoming connection and starts a new thread to
        handle incoming connections"""
    logging.debug("Listen thread started")
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    listen_socket.bind(host)

    listen_socket.listen(5)
    listen_socket.setblocking(0)
    while True:
        inputready, _, _ = select.select([listen_socket], [], [], 0)

        if inputready:
            client_socket, _ = listen_socket.accept()
            cthread = GenericThread(get_message, client_socket, send_pipe)
            cthread.start()
        time.sleep(0.01)
    logging.debug("Listen thread shutting down")


def get_message(c_socket, send_pipe):
    """ Receive a message from connection and emit a signal to GUI thread
    """
    addr = c_socket.getpeername()
    logging.debug("Client thread started")
    message_part = c_socket.recv(1024)
    message = b""
    while message_part:
        message += message_part
        message_part = c_socket.recv(1024)
    message = message.decode('latin1')
    logging.debug("Got message {0} from {1}".format(message, addr))
    send_pipe.send(message)


def start_chat(host, remote, friend, get_pipe, queue):
    app = QtGui.QApplication(sys.argv)
    chat = Chat(host=host, remote=remote, friend=friend, send_queue=queue)
    send = GenericThread(wait_send, queue, chat)
    recv = GenericThread(wait_receive, get_pipe, chat.text_add)
    send.start()
    recv.start()
    sys.exit(app.exec_())


def main():
    parser = ArgumentParser(description='Chat program')
    parser.add_argument('-l', '--local-port', default=12345, type=int)
    parser.add_argument('-p', '--remote-port', default=12345, type=int)
    parser.add_argument('-r', '--remote', default=socket.gethostname())
    parser.add_argument('-f', '--friend', default='R', help='Friends name')
    args = parser.parse_args()
    host = Address(socket.gethostname(), args.local_port)
    remote = Address(args.remote, args.remote_port)
    get_pipe, send_pipe = Pipe(False)
    queue = Queue()

    l_thread = GenericThread(listen_thread, host, send_pipe)
    l_thread.start()

    p1 = Process(target=start_chat, kwargs={'host': host, 'remote': remote,
                                            'friend': args.friend,
                                            'get_pipe': get_pipe,
                                            'queue': queue})

    p1.start()
    p1.join()

if __name__ == '__main__':
    main()
