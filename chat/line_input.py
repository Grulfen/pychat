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

Friend = namedtuple('Friend', ['name', 'ip', 'port'])


class StateControl:
    def __init__(self, name, host):
        self.name = name
        self.host = host
        self.friends = {}
        self.pipes = {}
        self.chats = []
        self.queue = Queue()
        self.friend_file = "{0}/.qt_chat".format(env['HOME'])
        self.load_friends()

        self.command_dict = {'add': self.add_friend,
                             'connect': self.connect_to,
                             'help': self.show_help,
                             'online': self.show_online,
                             'list': self.list_friends,
                             'show': self.show_friend,
                             'quit': self.shutdown,
                             'debug': self.debug,
                             'remove': self.remove_friend}

    def debug(self):
        print("name")
        print(self.name)
        print()
        print("pipes")
        print(self.pipes)
        print()
        print("friends")
        print(self.friends)

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
        print(">", end=" ")
        sys.stdout.flush()

    def show_friend(self, friend):
        """ show friend: show info about 'friend' """
        if friend not in self.friends:
            print("{0} not found".format(friend))
        else:
            print(self.friends[friend])

    def list_friends(self):
        """ list: List all friends """
        try:
            print("Friends: ", end="")
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

    def connect_to(self, friend_name):
        """ connect friend: start a chat with 'friend' """
        if friend_name in self.pipes:
            return
        get_pipe, send_pipe = Pipe(False)
        friend = self.friends.get(friend_name)
        if not friend:
            print("{0} is not a friend".format(friend_name))
        elif not friend_online(friend):
            print("{0} is not online".format(friend.name))
        else:
            friend_address = Address(friend.ip, int(friend.port))
            self.pipes[friend.name] = send_pipe
            chat = Process(target=start_chat,
                           kwargs={'host': self.host,
                                   'remote': friend_address,
                                   'friend': friend.name,
                                   'name': self.name,
                                   'state': self,
                                   'get_pipe': get_pipe,
                                   'queue': Queue()})
            self.chats.append(chat)
            chat.start()

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
        for chat in self.chats:
            chat.terminate()
        sys.exit(0)
