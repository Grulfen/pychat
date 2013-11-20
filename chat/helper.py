""" Helper functions for chat """
import socket
import re
import logging
from PyQt4 import QtCore


class GenericThread(QtCore.QThread):
    """ Class to make runt a function in a thread """
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        """ Run the thread """
        self.function(*self.args, **self.kwargs)
        return


def parse_message(message):
    match = re.search(
        r'<(?P<type>[a-z]+)><(?P<sender>\w+)><(?P<receiver>\w+)>(?P<body>.*)',
        message)
    if not match:
        logging.debug("Couldn't parse message: {0}".format(message))
        return {}
    else:
        message_dict = match.groupdict()
        return message_dict


def friend_online(friend):
    """ Check if a friend is online """
    addr = (friend.ip, int(friend.port))
    ping_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        ping_socket.connect(addr)
    except ConnectionRefusedError:
        logging.debug("In friend_online: {0}\
                ConnectionRefused".format(friend.name))
        return False
    except OSError:
        print("IP of friend '{0}' not valid".format(friend.name))
        return False
    try:
        ping_socket.send("<ping><null><null>".encode('latin1'))
        ping_socket.shutdown(socket.SHUT_WR)
        pong = ping_socket.recv(1024).decode('latin1')
    except socket.timeout:
        logging.debug("ping timeout")
        return False
    message = parse_message(pong)
    if message['type'] == 'pong':
        return True
    else:
        return False
