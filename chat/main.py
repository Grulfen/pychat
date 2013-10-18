""" Main program for simple chat for elo322 """
from qt_chat import start_chat, listen_thread, Address, GenericThread
from multiprocessing import Process, Pipe
from argparse import ArgumentParser
from queue import Queue
import socket


def main():
    """ Main function, gets arguments from sys.argv and starts chat and listen
        thread """
    parser = ArgumentParser(description='Chat program')
    parser.add_argument('-l', '--local-port', default=12345, type=int)
    parser.add_argument('-p', '--remote-port', default=12345, type=int)
    parser.add_argument('-r', '--remote', default=socket.gethostname())
    parser.add_argument('-f', '--friend', default='R', help='Friends name')
    parser.add_argument('-n', '--name', default='apa', help='Your name')
    args = parser.parse_args()
    host = Address(socket.gethostname(), args.local_port)
    remote = Address(args.remote, args.remote_port)
    get_pipe, send_pipe = Pipe(False)
    queue = Queue()
    pipes = {args.friend: send_pipe}

    l_thread = GenericThread(listen_thread, host, pipes)
    l_thread.start()

    chat1 = Process(target=start_chat, kwargs={'host': host, 'remote': remote,
                                               'friend': args.friend,
                                               'get_pipe': get_pipe,
                                               'queue': queue,
                                               'name': args.name})

    chat1.start()
    chat1.join()

if __name__ == '__main__':
    main()
