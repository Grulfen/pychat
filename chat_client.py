""" Client program for elo322 - Redes de Computadores """
import socket
import sys


def main():
    """ Main function of chat server """
    # Internet socket and TCP
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Local host
    host = socket.gethostname()
    port = 12345

    if len(sys.argv) >= 2:
        send_message = " ".join(sys.argv[1:]).encode('utf-8')
    else:
        send_message = b"THAT DATA"

    send_socket.connect((host, port))
    send_socket.send(send_message)
    send_socket.shutdown(socket.SHUT_WR)
    message = send_socket.recv(10)
    while message:
        print(message.decode('utf-8'), end='')
        message = send_socket.recv(1)
    print()
    send_socket.close()

if __name__ == '__main__':
    main()
