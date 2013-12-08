""" Handle state of the chat server """
import sys
import re
from os import environ as env
import pickle
from helper import friend_online
from collections import namedtuple
from multiprocessing import Pipe, Process
from qt_chat import start_chat, Address

Friend = namedtuple('Friend', ['name', 'ip', 'port'])


class State:
    def __init__(self, name, host, datafile=None):
        self.friends = {}
        self.pipes = {}  # Dict with message- and close-pipes
        self.chats = {}
        if datafile:
            open(datafile, 'a').close()
            self.friend_file = datafile
        else:
            self.friend_file = "{0}/.pychat.conf".format(env['HOME'])
        self.load_friends()
        self.name = name
        self.host = host

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
        except (FileNotFoundError, EOFError):
            self.friends = {}

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
        if friend_name in self.chats:
            return
        friend = self.friends.get(friend_name)
        if not friend:
            print("{0} is not a friend".format(friend_name))
        elif not friend_online(friend):
            print("{0} is not online".format(friend.name))
        else:
            message_get_pipe, message_send_pipe = Pipe(False)
            close_get_pipe, close_send_pipe = Pipe(False)

            friend_address = Address(friend.ip, int(friend.port))
            self.pipes[friend.name] = (message_send_pipe, close_get_pipe)
            chat = Process(target=start_chat,
                           kwargs={'host': self.host,
                                   'remote': friend_address,
                                   'friend': friend.name,
                                   'name': self.name,
                                   'state': self,
                                   'get_pipe': message_get_pipe,
                                   'close_pipe': close_send_pipe})
            self.chats[friend.name] = chat
            chat.start()

    def disconnect_from(self, friend_name):
        """ Disconnect from a friend, removing the chat from pipes and chats
        """
        in_pipe = friend_name in self.pipes
        in_chat = friend_name in self.chats
        if in_pipe:
            del self.pipes[friend_name]
        if in_chat:
            del self.chats[friend_name]

    def show_online(self):
        """ online: show available friends """
        online_friends = [friend for friend in self.friends.keys() if
                          friend_online(self.friends[friend])]
        print("Online friends: ", end='')
        print(', '.join(online_friends))

    def show_help(self, command=None):
        """ help command: print help message for 'command' """
        if command in self.command_dict:
            print(self.command_dict[command].__doc__)
        else:
            print("Available commands: ")
            print(', '.join(self.command_dict.keys()))

    def check_closed_chat(self):
        """ Check close_pipe for every open chat if chat is closed, in that
        case, disconnect from chat """
        for friend_name, pipes in list(self.pipes.items()):
            _, close_pipe = pipes
            if close_pipe.poll():
                self.disconnect_from(friend_name)

    def shutdown(self):
        """ Close the chat """
        for chat in self.chats.values():
            chat.terminate()
        sys.exit(0)
