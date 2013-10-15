""" Client program for elo322 - Redes de Computadores """
import socket
import sys


def send_and_recieve(message, host=socket.gethostname(), port=12345):
    # Internet socket and TCP
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    send_socket.connect((host, port))
    send_socket.send(message)
    send_socket.shutdown(socket.SHUT_WR)
    message = send_socket.recv(1024)
    while message:
        print(message.decode('latin1'), end='')
        message = send_socket.recv(1024)
    print()
    send_socket.close()


def main():
    """ Main function of chat server """

    if len(sys.argv) >= 2:
        send_message = " ".join(sys.argv[1:]).encode('latin1')
    else:
        while True:
            try:
                send_message = input("What to say?\n").encode('latin1')
            except (EOFError, KeyboardInterrupt):
                break
            print()

            if send_message:
                print('a:')
                send_and_recieve(send_message)
                print("---------------------\n")
            else:
                break


if __name__ == '__main__':
    main()
