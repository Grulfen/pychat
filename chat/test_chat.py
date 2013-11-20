""" Testing the chat """
from helper import parse_message

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
