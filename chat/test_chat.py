""" Testing the chat """
from qt_chat import GenericThread, Address
from helper import parse_message
from state import State
from multiprocessing import Pipe
import time
import socket
import os

TESTFILE = "test.txt"


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
    def setup_class(self):
        from listen import listen_thread
        new_chat_pipe_out, new_chat_pipe_in = Pipe(False)
        host = Address(socket.gethostname(), 9898)
        self.state = State("test", host, TESTFILE)
        self.l_thread = GenericThread(listen_thread, host, self.state,
                new_chat_pipe_in)
        self.l_thread.start()
        time.sleep(0.2)

    def teardown_class(self):
        self.l_thread.terminate()
        os.remove(TESTFILE)

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

    def test_send_msg_hi(self):
        get_pipe, send_pipe = Pipe(False)
        self.state.pipes["test_sender"] = (send_pipe, None)

        remote = Address(socket.gethostname(), 9898)
        hi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        message_send = "<msg><test_sender><test>hi"

        hi_socket.connect(remote)
        hi_socket.send(message_send.encode('latin1'))
        hi_socket.close()

        while not get_pipe.poll():
            time.sleep(0.01)
        message_get = get_pipe.recv()
        assert message_get == "test_sender: hi"

        del self.state.pipes["test_sender"]
