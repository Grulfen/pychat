import sys
import socket
import logging
import select

logging.basicConfig(level=logging.INFO)

from PyQt4 import QtGui, QtCore


class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args,**self.kwargs)
        return


class Chat(QtGui.QWidget):
    def __init__(self, host=socket.gethostname(), local_port=12347, remote_port=12345):
        super().__init__()

        self.host = host
        self.local_port = local_port
        self.remote_port = remote_port
        self.initUI()

        self.l_thread = GenericThread(listen_thread, host, local_port)
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

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Chat')
        self.show()

    def spawn_send_thread(self, message):
        send_thread = GenericThread(send_message, port=self.remote_port, message=message)
        send_thread.start()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def message_key_handler(self, e):
        if (e.key() == QtCore.Qt.Key_Return) or (e.key() == QtCore.Qt.Key_Enter):
            text= self.message.toPlainText()
            self.spawn_send_thread(text)
            self.earlier_messages.append(text)
            self.message.clear()
        else:
            QtGui.QTextEdit.keyPressEvent(self.message, e)


def send_message(host=socket.gethostname(), port=12345, message="Hej"):
    # Internet socket and TCP
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        send_socket.connect((host, port))
    except ConnectionRefusedError:
        logging.warning("Could not connect to {0}".format((host, port)))
        return

    logging.debug("Sending message {0} to  {1}".format(message, (host, port)))
    send_socket.send(message.encode('latin1'))
    send_socket.close()


def listen_thread(host, port):
    logging.debug("Listen thread started")
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    listen_socket.bind((host, port))

    listen_socket.listen(5)
    listen_socket.setblocking(0)
    while True:
        try:
            inputready, _, _ = select.select([listen_socket], [], [], 0)
        except KeyboardInterrupt:
            listen_socket.close()
            print("Shutting down")
            break

        for s in inputready:
            if s == listen_socket:
                # TODO fixa här
                client_socket, _ = listen_socket.accept()
                cthread = GenericThread(get_message, client_socket)
                cthread.start()
    logging.debug("Listen thread shutting down")


def get_message(c_socket):
    addr = c_socket.getpeername()
    logging.debug("Client thread started")
    message_part = c_socket.recv(1024)
    message = b""
    while message_part:
        message += message_part
        message_part = c_socket.recv(1024)
    message = message.decode('latin1')
    logging.debug("Got message {0} from {1}".format(message, addr))
    print(message)


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
