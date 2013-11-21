""" Main program for simple chat for elo322 """
from qt_chat import Address, GenericThread
from line_input import InputControl
from state import State
from listen import listen_thread
from argparse import ArgumentParser
import sys
import select
import socket
import queue


def main():
    """ Main function, gets arguments from sys.argv and starts chat and listen
        thread """
    parser = ArgumentParser(description='Chat program')
    parser.add_argument('-l', '--local-port', default=12345, type=int)
    parser.add_argument('-n', '--name', default='apa', help='Your name')
    args = parser.parse_args()
    host = Address(socket.gethostname(), args.local_port)

    state = State(args.name, host)
    input_control = InputControl(args.name, host, state)

    l_thread = GenericThread(listen_thread, host, state)
    l_thread.start()

    print(">", end=" ")
    sys.stdout.flush()
    while True:
        try:
            input_ready, _, _ = select.select([sys.stdin], [], [], 0)
            if sys.stdin in input_ready:
                line = sys.stdin.readline()
                if line:
                    input_control.handle_input(line)
                else:
                    input_control.shutdown()
            try:
                friend_name = state.queue.get(False)
                state.connect_to(friend_name)
                state.queue.task_done()
            except queue.Empty:
                pass
            state.check_closed_chat()

        except (EOFError, KeyboardInterrupt):
            state.shutdown()
            l_thread.terminate()

if __name__ == '__main__':
    main()
