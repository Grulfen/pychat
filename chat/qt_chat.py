""" Chat utilities for ELO322 """
import sys
import socket
import logging
from collections import namedtuple
from helper import GenericThread
from PyQt4 import QtGui, QtCore
from multiprocessing import Pipe

logging.basicConfig(level=logging.INFO)

Address = namedtuple('Address', ['name', 'port'])


class Chat(QtGui.QWidget):
    """ Simple chat with GUI """
    text_add = QtCore.pyqtSignal(str, name="new_message")

    def __init__(self, host, remote, friend, name, state,
                 close_pipe, get_pipe, show=True):
        super().__init__()

        self.state = state
        self.host = host
        self.remote = remote
        self.friend = friend
        self.close_pipe = close_pipe
        self.name = name
        self.get_pipe = get_pipe
        self.message_pipe_get, self.message_pipe_send = Pipe(False)

        send = GenericThread(self.wait_send)
        recv = GenericThread(self.wait_receive)
        send.start()
        recv.start()

        self.initUI(show)

    def initUI(self, show):
        """ Init the UI and signals """
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
        self.setWindowTitle(self.friend)
        if show:
            self.show()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def message_key_handler(self, e):
        """ What to do at keypress in message bar """
        if (e.key() == QtCore.Qt.Key_Return) or \
                (e.key() == QtCore.Qt.Key_Enter):
            text = self.message.toPlainText()
            if text:
                self.message_pipe_send.send(text)
                self.earlier_messages.append("yo: " + text)
                self.message.clear()
        else:
            QtGui.QTextEdit.keyPressEvent(self.message, e)

    def send_message(self, message):
        """ Send message 'message' to remote with sockets """
        # Internet socket and TCP
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        message = "<msg><{0}><{1}>{2}".format(self.name, self.friend, message)

        try:
            send_socket.connect(self.remote)
        except ConnectionRefusedError:
            logging.warning("Could not connect to {0}".format(self.remote))
            return

        logging.debug("Sending message {0} to  {1}".format(message, self.remote))
        send_socket.send(message.encode('latin1'))
        send_socket.close()

    def add_message(self, message):
        """ Add 'message' from friend to textbox in chat """
        self.earlier_messages.append(message)

    def close(self):
        self.close_pipe.send(self.friend)
        super().close()

    def wait_send(self):
        """ Thread that gets message from queue and sends them via chat"""
        while True:
            # Wait until message
            self.message_pipe_get.poll(None)
            message = self.message_pipe_get.recv()
            self.send_message(message)

    def wait_receive(self):
        """ Thread that waits for messages on 'get_pipe' and emits a signal to add
            message to GUI """
        while True:
            self.get_pipe.poll(None)
            message = self.get_pipe.recv()
            self.text_add.emit(message)


def start_chat(host, remote, friend, name, get_pipe, state, close_pipe):
    """ Start chat with 'friend' """
    app = QtGui.QApplication(sys.argv)
    chat = Chat(host=host, remote=remote, friend=friend, name=name,
                state=state, close_pipe=close_pipe, get_pipe=get_pipe)
    sys.exit(app.exec_())
