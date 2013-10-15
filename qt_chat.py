import sys
import socket
import logging
import select

logging.basicConfig(level=logging.INFO)

from PyQt4 import QtGui, QtCore


class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args,**self.kwargs)
        return


class Chat(QtGui.QWidget):
    text_add = QtCore.pyqtSignal(str, name="new_message")
    def __init__(self, host=socket.gethostname(), local_port=12347, remote_port=12345):
        super().__init__()

        self.host = host
        self.local_port = local_port
        self.remote_port = remote_port
        self.initUI()

        self.l_thread = GenericThread(self.listen_thread)
        self.l_thread.start()

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
        if (e.key() == QtCore.Qt.Key_Return) or (e.key() == QtCore.Qt.Key_Enter):
            text = self.message.toPlainText()
            self.spawn_send_thread(text)
            self.earlier_messages.append("l: " + text)
            self.message.clear()
        else:
            QtGui.QTextEdit.keyPressEvent(self.message, e)

    def send_message(self, message):
        # Internet socket and TCP
        host = self.host
        port = self.remote_port
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            send_socket.connect((host, port))
        except ConnectionRefusedError:
            logging.warning("Could not connect to {0}".format((host, port)))
            return

        logging.debug("Sending message {0} to  {1}".format(message, (host, port)))
        send_socket.send(message.encode('latin1'))
        send_socket.close()

    def add_message(self, message):
        self.earlier_messages.append("r: " + message)

    def listen_thread(self):
        host = self.host
        port = self.local_port

        logging.debug("Listen thread started")
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        listen_socket.bind((host, port))

        listen_socket.listen(5)
        listen_socket.setblocking(0)
        while True:
            inputready, _, _ = select.select([listen_socket], [], [], 0)

            if inputready:
                client_socket, _ = listen_socket.accept()
                cthread = GenericThread(self.get_message, client_socket)
                cthread.start()
        logging.debug("Listen thread shutting down")

    def get_message(self, c_socket):
        addr = c_socket.getpeername()
        logging.debug("Client thread started")
        message_part = c_socket.recv(1024)
        message = b""
        while message_part:
            message += message_part
            message_part = c_socket.recv(1024)
        message = message.decode('latin1')
        logging.debug("Got message {0} from {1}".format(message, addr))
        self.text_add.emit(message)


def main():
    if len(sys.argv) == 3:
        local_port, remote_port = int(sys.argv[1]), int(sys.argv[2])
    else:
        local_port, remote_port = 12347, 12345
    app = QtGui.QApplication(sys.argv)
    chat = Chat(local_port=local_port, remote_port=remote_port)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
