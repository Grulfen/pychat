""" Get input from user and handle it """
import sys
import re
from os import environ as env
import pickle
from helper import friend_online
from collections import namedtuple
from multiprocessing import Pipe, Process
from queue import Queue
from qt_chat import start_chat, Address


class InputControl:
    def __init__(self, name, host, state):
        self.name = name
        self.host = host
        self.state = state

        self.command_dict = {'add': self.state.add_friend,
                             'connect': self.state.connect_to,
                             'help': self.show_help,
                             'online': self.state.show_online,
                             'list': self.list_friends,
                             'show': self.show_friend,
                             'quit': self.shutdown,
                             'debug': self.state.debug,
                             'remove': self.state.remove_friend}

    def handle_input(self, line):
        """ Handle user input from terminal """
        commands = line.split()
        if len(commands) < 1:
            return
        function = self.command_dict.get(commands[0],
                                         lambda: print("Unkown command"))
        try:
            function(*commands[1:])
        except TypeError:
            self.show_help(commands[0])
        print(">", end=" ")
        sys.stdout.flush()

    def show_friend(self, friend):
        """ show friend: show info about 'friend' """
        if friend not in self.state.friends:
            print("{0} not found".format(friend))
        else:
            print(self.state.friends[friend])

    def list_friends(self):
        """ list: List all friends """
        try:
            print("Friends: ", end="")
            print(', '.join(self.state.friends.keys()))
        except TypeError:
            print(self.list_friends.__doc__)

    def show_help(self, command=None):
        """ help command: print help message for 'command' """
        if command in self.command_dict:
            print(self.command_dict[command].__doc__)
        else:
            print("Available commands: ")
            print(', '.join(self.command_dict.keys()))

    def shutdown(self):
        """ Close the chat """
        for chat in self.state.chats.values():
            chat.terminate()
        sys.exit(0)
