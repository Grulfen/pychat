""" Chat utilities for ELO322 """
import sys
import socket
import logging
import time
from collections import namedtuple
from helper import GenericThread
from PyQt4 import QtGui, QtCore

logging.basicConfig(level=logging.INFO)

Address = namedtuple('Address', ['name', 'port'])


class Chat(QtGui.QWidget):
    """ Simple chat with GUI """
    text_add = QtCore.pyqtSignal(str, name="new_message")

    def __init__(self, host, remote, send_queue, friend, name, state,
                 close_pipe):
        super().__init__()

        self.state = state
        self.host = host
        self.remote = remote
        self.friend = friend
        self.send_queue = send_queue
        self.close_pipe = close_pipe
        self.name = name
        self.initUI()

    def initUI(self):
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
                self.send_queue.put(text)
                self.earlier_messages.append("yo: " + text)
                self.message.clear()
                # self.spawn_send_thread(text)
        else:
            QtGui.QTextEdit.keyPressEvent(self.message, e)

    def send_message(self, message):
        """ Send message 'message' to self.remote with sockets """
        # Internet socket and TCP
        remote = self.remote
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        message = "<msg><{0}><{1}>{2}".format(self.name, self.friend, message)

        try:
            send_socket.connect(remote)
        except ConnectionRefusedError:
            logging.warning("Could not connect to {0}".format(remote))
            return

        logging.debug("Sending message {0} to  {1}".format(message, remote))
        send_socket.send(message.encode('latin1'))
        send_socket.close()

    def add_message(self, message):
        """ Add 'message' from friend to textbox in chat """
        self.earlier_messages.append(message)

    def close(self):
        self.close_pipe.send(self.friend)
        super().close()


def wait_send(queue, chat):
    """ Thread that gets message from queue and sends them via chat"""
    while True:
        if not queue.empty():
            message = queue.get()
            chat.send_message(message)
            queue.task_done()
        time.sleep(0.01)


def wait_receive(get_pipe, signal):
    """ Thread that waits for messages on 'get_pipe' and emits a signal to add
        message to GUI """
    while True:
        if(get_pipe.poll()):
            message = get_pipe.recv()
            signal.emit(message)
        time.sleep(0.01)


def start_chat(host, remote, friend, name, get_pipe, queue, state, close_pipe):
    """ Start chat with 'friend' """
    app = QtGui.QApplication(sys.argv)
    chat = Chat(host=host, remote=remote, friend=friend, name=name,
                send_queue=queue, state=state, close_pipe=close_pipe)
    send = GenericThread(wait_send, queue, chat)
    recv = GenericThread(wait_receive, get_pipe, chat.text_add)
    # TODO se till att de här trådarna dör när chatten gör
    send.start()
    recv.start()
    sys.exit(app.exec_())
