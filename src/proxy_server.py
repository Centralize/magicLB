import socket
import threading
import select
import time

class ProxyServer:
    def __init__(self, host, port, load_balancer, servers):
        self.host = host
        self.port = port
        self.load_balancer = load_balancer
        self.servers = servers # Reference to the main servers list
        self.running = False
        self.server_socket = None
        print(f"ProxyServer initialized to listen on {self.host}:{self.port}")

    def start(self):
        if self.running:
            print("Proxy server is already running.")
            return

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0) # Timeout for accept to allow checking self.running
            self.running = True
            print(f"Proxy server listening on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"Accepted connection from {client_address}")
                    client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                    client_handler.daemon = True
                    client_handler.start()
                except socket.timeout:
                    continue # Continue loop if no connection within timeout
                except Exception as e:
                    if self.running: # Only print error if server is still expected to be running
                        print(f"Error accepting connection: {e}")
        except Exception as e:
            print(f"Failed to start proxy server on {self.host}:{self.port}: {e}")
            self.running = False
        finally:
            if self.server_socket:
                self.server_socket.close()
                print("Proxy server socket closed.")

    def stop(self):
        if self.running:
            print("Stopping proxy server...")
            self.running = False
            if self.server_socket:
                self.server_socket.close()
            print("Proxy server stopped.")
        else:
            print("Proxy server is not running.")

    def handle_client(self, client_socket):
        backend_server_info = None
        backend_socket = None
        try:
            if not self.load_balancer or not self.load_balancer.servers:
                print("No load balancing algorithm selected or no backend servers available.")
                client_socket.sendall(b"HTTP/1.1 503 Service Unavailable\r\n\r\nNo backend servers available.")
                return

            backend_server_info = self.load_balancer.get_next_server()
            if not backend_server_info:
                print("Load balancer returned no available server.")
                client_socket.sendall(b"HTTP/1.1 503 Service Unavailable\r\n\r\nNo available backend servers.")
                return

            print(f"Routing request to backend: {backend_server_info}")

            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.connect((backend_server_info.host, backend_server_info.port))

            # Proxy data between client and backend
            inputs = [client_socket, backend_socket]
            while self.running:
                try:
                    readable, _, _ = select.select(inputs, [], [], 1.0) # 1-second timeout
                    if not readable:
                        continue # No data to read, continue waiting

                    for sock in readable:
                        if sock is client_socket:
                            data = client_socket.recv(4096)
                            if not data:
                                # Client closed connection
                                return
                            backend_socket.sendall(data)
                        elif sock is backend_socket:
                            data = backend_socket.recv(4096)
                            if not data:
                                # Backend closed connection
                                return
                            client_socket.sendall(data)
                except (socket.error, ConnectionResetError) as e:
                    print(f"Socket error during data transfer: {e}")
                    break # Exit loop on socket error
                except Exception as e:
                    print(f"Unexpected error during data transfer: {e}")
                    break

        except ConnectionRefusedError:
            print(f"Connection to backend {backend_server_info} refused. It might be down.")
            if client_socket:
                client_socket.sendall(b"HTTP/1.1 503 Service Unavailable\r\n\r\nBackend server refused connection.\r\n")
        except socket.timeout:
            print("Socket timeout during initial connection or data transfer.")
            if client_socket:
                client_socket.sendall(b"HTTP/1.1 504 Gateway Timeout\r\n\r\nBackend server connection timed out.\r\n")
        except Exception as e:
            print(f"Error handling client connection: {e}")
            if client_socket:
                client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\nLoad balancer internal error.\r\n")
        finally:
            if client_socket:
                client_socket.close()
                # print("Client socket closed.") # Keep commented for less verbose output
            if backend_socket:
                backend_socket.close()
                # print("Backend socket closed.") # Keep commented for less verbose output
