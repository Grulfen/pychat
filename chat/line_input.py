""" Get input from user and handle it """
import sys
import re
from os import environ as env
import pickle
# from listen import pipes
from helper import friend_online
from collections import namedtuple
# from qt_chat import start_chat

Friend = namedtuple('Friend', ['name', 'ip', 'port'])
default_port = 12345


class StateControl:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.friends = {}
        self.pipes = {}
        self.friend_file = "{0}/.qt_chat".format(env['HOME'])
        self.load_friends()

        self.command_dict = {'add': self.add_friend,
                             'connect': self.connect_to,
                             'help': self.show_help,
                             'online': self.show_online,
                             'list': self.list_friends,
                             'show': self.show_friend,
                             'remove': self.remove_friend}

    def load_friends(self):
        try:
            friends_file = open(self.friend_file, "rb")
            self.friends = pickle.load(friends_file)
        except pickle.UnpicklingError:
            self.friends = {}
            friends_file.close()
        except FileNotFoundError:
            self.friends = {}

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

    def show_friend(self, friend):
        """ show friend: show info about 'friend' """
        if friend not in self.friends:
            print("{0} not found".format(friend))
        else:
            print(self.friends[friend])

    def list_friends(self):
        """ list: List all friends """
        try:
            print(', '.join(self.friends.keys()))
        except TypeError:
            print(self.list_friends.__doc__)

    def add_friend(self, friend, ip, port='12345'):
        """ add friend ip port: Add friend with ip 'ip' and port 'port' """
        friend_re = re.compile(r'\w+')
        ip_re = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
        port_re = re.compile(r'[0-9]{2,5}')

        if not friend_re.match(friend):
            print(self.add_friend.__doc__)
            return

        if not ip_re.match(ip):
            print(self.add_friend.__doc__)
            return

        if not port_re.match(port):
            print(self.add_friend.__doc__)
            return

        self.friends[friend] = Friend(friend, ip, port)
        self.write_friends()
        print("User {0} added".format(friend))

    def remove_friend(self, friend):
        """ remove friend: remove 'friend' """
        if not friend in self.friends:
            print("{0} is not a friend".format(friend))
        else:
            del self.friends[friend]
            self.write_friends()

        print("User {0} removed".format(friend))

    def write_friends(self):
        friends_file = open(self.friend_file, "wb")
        pickle.dump(self.friends, friends_file)
        friends_file.close()

    def connect_to(self, friend):
        """ connect friend: start a chat with 'friend' """
        print("Starting chat with {0}".format(friend))

    def show_online(self):
        """ online: show available friends """
        print("Online friends: ", end='')
        online_friends = [friend for friend in self.friends.keys() if
                          friend_online(self.friends[friend])]
        print(', '.join(online_friends))

    def show_help(self, command=None):
        """ help command: print help message for 'command' """
        if command in self.command_dict:
            print(self.command_dict[command].__doc__)
        else:
            print("Available commands: ")
            print(', '.join(self.command_dict.keys()))

    def shutdown(self):
        """ Close the chat """
        sys.exit(0)
