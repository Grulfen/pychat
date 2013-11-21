""" Testing the chat """
from qt_chat import GenericThread, Address
from helper import parse_message
import socket


class TestParse:
    def test_parse_type(self):
        """ Test type parse part """
        message = "<ping><null><null>"
        message_dict = parse_message(message)
        assert message_dict['type'] == 'ping'

    def test_parse_sender(self):
        """ Test sender parse part """
        message = "<null><test_sender><null>"
        message_dict = parse_message(message)
        assert message_dict['sender'] == 'test_sender'

    def test_parse_reciever(self):
        """ Test reciever parse part """
        message = "<null><null><test_recv>null"
        message_dict = parse_message(message)
        assert message_dict['receiver'] == 'test_recv'

    def test_parse_body(self):
        """ Test body parse part """
        message = "<null><null><null>hejsan"
        message_dict = parse_message(message)
        assert message_dict['body'] == 'hejsan'

    def test_parse_mismatch(self):
        """ Test parse mismatch """
        message = "<null><null>"
        message_dict = parse_message(message)
        assert message_dict == {}


class TestServer:
    def setup_class(cls):
        from listen import listen_thread
        host = Address(socket.gethostname(), 9898)
        cls.l_thread = GenericThread(listen_thread, host, None)
        cls.l_thread.start()

    def teardown_class(cls):
        cls.l_thread.terminate()

    def test_ping_pong(self):
        remote = Address(socket.gethostname(), 9898)
        ping_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        message = "<ping><null><null>"

        ping_socket.connect(remote)
        ping_socket.send(message.encode('latin1'))
        ping_socket.shutdown(socket.SHUT_WR)
        pong = ping_socket.recv(1024).decode('latin1')
        ping_socket.close()
        assert pong == "<pong><null><null>"
