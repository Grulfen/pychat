""" Main program for simple chat for elo322 """
from qt_chat import Address, GenericThread
from line_input import StateControl
from listen import listen_thread
from argparse import ArgumentParser
import socket


def main():
    """ Main function, gets arguments from sys.argv and starts chat and listen
        thread """
    parser = ArgumentParser(description='Chat program')
    parser.add_argument('-l', '--local-port', default=12345, type=int)
    parser.add_argument('-n', '--name', default='apa', help='Your name')
    args = parser.parse_args()
    host = Address(socket.gethostname(), args.local_port)

    state_control = StateControl(args.name, host)

    l_thread = GenericThread(listen_thread, host, state_control)
    l_thread.start()

    while True:
        try:
            state_control.handle_input(input("> "))
        except (EOFError, KeyboardInterrupt):
            state_control.shutdown()

if __name__ == '__main__':
    main()
