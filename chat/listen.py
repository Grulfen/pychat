""" The listening thread """
import logging
import socket
import select
import time
from helper import parse_message, GenericThread


def listen_thread(host, state, new_chat_pipe):
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
            cthread = GenericThread(get_message, client_socket, state,
                                    new_chat_pipe)
            cthread.start()
        time.sleep(0.01)
    logging.debug("Listen thread shutting down")


def get_message(c_socket, state, new_chat_pipe):
    """ Receive a message from connection and emit a signal to GUI thread
    """
    logging.debug("Client thread started")
    addr = c_socket.getpeername()

    message_part = c_socket.recv(1024)
    message = b""
    while message_part:
        message += message_part
        message_part = c_socket.recv(1024)
    message = message.decode('latin1')
    logging.debug("Got message {0} from {1}".format(message, addr))

    message_dict = parse_message(message)
    if(message_dict.get('type') == 'msg'):
        pipes = state.pipes
        handle_msg(message_dict, pipes, state, new_chat_pipe)
    elif(message_dict.get('type') == 'ping'):
        handle_ping(c_socket)
    c_socket.close()


def handle_msg(message_dict, pipes, state, new_chat_pipe):
    try:
        send_pipe, _ = pipes.get(message_dict['sender'])
        send_pipe.send("{0}: {1}".format(message_dict['sender'],
                       message_dict['body']))
    except TypeError:
        sender = message_dict['sender']
        if sender in state.friends:
            new_chat_pipe.send(sender)
            time.sleep(0.3)
            handle_msg(message_dict, pipes, state, new_chat_pipe)


def handle_ping(c_socket):
    logging.debug("Got ping, sending pong")
    c_socket.send("<pong><null><null>".encode('latin1'))
