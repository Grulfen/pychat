""" Main program for simple chat for elo322 """
from qt_chat import Address, GenericThread
from line_input import InputControl
from state import State
from listen import listen_thread
from argparse import ArgumentParser
from multiprocessing import Pipe
import sys
import select
import socket


def main():
    """ Main function, gets arguments from sys.argv and starts chat and listen
        thread """
    parser = ArgumentParser(description='Chat program')
    parser.add_argument('-l', '--local-port', default=12345, type=int)
    parser.add_argument('-n', '--name', default='apa', help='Your name')
    args = parser.parse_args()
    host = Address(socket.gethostname(), args.local_port)

    new_chat_pipe_out, new_chat_pipe_in = Pipe(False)
    state = State(args.name, host)
    input_control = InputControl(args.name, host, state)
    l_thread = GenericThread(listen_thread, host, state, new_chat_pipe_in)
    l_thread.start()

    print(">", end=" ")
    sys.stdout.flush()
    while True:
        try:
            input_ready, _, _ = select.select([sys.stdin,
                                              new_chat_pipe_out.fileno()],
                                              [], [], 0)
            if sys.stdin in input_ready:
                # Command from command line
                line = sys.stdin.readline()
                if line:
                    input_control.handle_input(line)
                else:
                    # Shutdown on EOF
                    input_control.shutdown()
            if new_chat_pipe_out.fileno() in input_ready:
                # Got message from friend, but chat is not open
                friend_name = new_chat_pipe_out.recv()
                state.connect_to(friend_name)
            # Check if any chat has been closed
            state.check_closed_chat()

        except (EOFError, KeyboardInterrupt):
            state.shutdown()
            l_thread.terminate()

if __name__ == '__main__':
    main()
