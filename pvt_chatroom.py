import socket
import threading
import sys

# Global variables
clients = {}
lock = threading.Lock()

# Function to handle client connections
def handle_client(client_socket, client_address):
    print(f"Connection established with {client_address}")
    try:
        # Receive the username from the client
        username = client_socket.recv(1024).decode("utf-8")
        with lock:
            clients[username] = client_socket

        # Notify other clients about the new user
        broadcast(f"{username} has joined the chat.")

        # Receive and broadcast messages
        while True:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                break
            broadcast(message)
    except:
        pass
    finally:
        # Remove the client from the dictionary when they disconnect
        with lock:
            if username in clients:
                del clients[username]
                broadcast(f"{username} has left the chat.")  # Print message when a client leaves
        client_socket.close()

# Function to broadcast messages to all clients
def broadcast(message):
    with lock:
        for client in clients.values():
            client.send(message.encode("utf-8"))

# Function to receive messages from the server
def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode("utf-8")
            print(message)
        except:
            break

# Function to send messages to the server
def send_messages(sock, username):
    while True:
        message = input()
        if message.lower() == 'exit':
            sock.send(f"{username} has left the chat.".encode("utf-8"))
            break
        else:
            sock.send(f"{username}: {message}".encode("utf-8"))

# Function to set username
def set_username():
    username = input("Enter your username: ")
    return username

# Function to get IP address
def get_ip_address():
    # Use getaddrinfo to get a list of possible address families
    result = socket.getaddrinfo(socket.gethostname(), None, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)

    # Iterate over the results to find an IPv4 or IPv6 address
    for res in result:
        af, socktype, proto, canonname, sa = res
        if af == socket.AF_INET:
            return sa[0]  # IPv4 address
        elif af == socket.AF_INET6:
            return sa[0]  # IPv6 address

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Server mode
        # Create a socket for the server
        server_socket = socket.socket(socket.AF_INET6 if ":" in get_ip_address() else socket.AF_INET, socket.SOCK_STREAM)
        host = get_ip_address()
        port = 12345
        server_socket.bind((host, port))
        server_socket.listen(5)
        print("Server started. Waiting for connections...")
        print("Server IP address:", host)

        # Accept incoming connections and spawn threads to handle them
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_thread.start()
        except KeyboardInterrupt:
            print("Server shutting down.")
            server_socket.close()
    else:
        # Client mode
        # Get username from the user
        username = set_username()

        # Automatically print the IP address of the current machine
        server_host = get_ip_address()
        print("Server IP address:", server_host)

        # Connect to the central server
        server_port = 12345
        client_socket = socket.socket(socket.AF_INET6 if ":" in server_host else socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, server_port))

        # Send the username to the server
        client_socket.send(username.encode("utf-8"))

        # Start threads for sending and receiving messages
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        send_thread = threading.Thread(target=send_messages, args=(client_socket, username))
        receive_thread.start()
        send_thread.start()

        # Keep the program running
        receive_thread.join()
        send_thread.join()

if __name__ == "__main__":
    main()
