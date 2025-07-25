import json
import os
import subprocess
import sys
import threading
import time
import socket # Added for status check

from src.backend_server import BackendServer
from src.load_balancer import RoundRobinLoadBalancer, WeightedRoundRobinLoadBalancer
from src.proxy_server import ProxyServer

CONFIG_FILE = "config.json"
PID_FILE = "magiclb.pid" # Define PID file path

def save_config(servers, listening_port):
    config_data = {
        "listening_port": listening_port,
        "backend_servers": [
            {
                "id": server.id,
                "host": server.host,
                "port": server.port,
                "protocol": server.protocol,
                "weight": server.weight
            } for server in servers
        ]
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        print(f"Configuration saved to {CONFIG_FILE}")
    except IOError as e:
        print(f"Error saving configuration: {e}")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("No existing configuration found. Starting with empty settings.")
        return None, []
    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
        
        listening_port = config_data.get("listening_port")
        backend_servers_data = config_data.get("backend_servers", [])
        servers = []
        for s_data in backend_servers_data:
            servers.append(BackendServer(
                s_data["id"],
                s_data["host"],
                s_data["port"],
                s_data.get("protocol", "http"), # Default to http for backward compatibility
                s_data.get("weight", 1)
            ))
        print(f"Configuration loaded from {CONFIG_FILE}")
        return listening_port, servers
    except json.JSONDecodeError as e:
        print(f"Error decoding configuration file: {e}")
        return None, []
    except IOError as e:
        print(f"Error loading configuration: {e}")
        return None, []

def check_lb_status():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Check if the process with this PID is actually running
            # On Linux, /proc/PID will exist if the process is running
            if os.path.exists(f"/proc/{pid}"):
                return "Running", pid
            else:
                # PID file exists but process doesn't, clean up
                os.remove(PID_FILE)
                return "Stopped (PID file stale)", None
        except (ValueError, IOError):
            return "Stopped (PID file corrupt)", None
    return "Stopped", None

def check_backend_server_status(host, port, timeout=1):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return "Reachable"
    except (socket.timeout, ConnectionRefusedError, OSError):
        return "Unreachable"

def run_dialog_mode(listening_port, servers, load_balancer):
    while True:
        print("\n--- Main Menu ---")
        print("1. Add Backend Server")
        print("2. Select Load Balancing Algorithm")
        print("3. Send Request")
        print("4. List Servers")
        print("5. Edit Backend Server")
        print("6. Delete Backend Server")
        print("7. Set Local Listening Port")
        print("8. Restart Load Balancer")
        print("9. Save Configuration")
        print("10. Show Status")
        print("11. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            # Add Server logic
            try:
                server_id = len(servers) + 1
                host = input("Enter server host (e.g., 127.0.0.1): ")
                protocol = input("Enter server protocol (e.g., http, https, tcp, default http): ").lower() or "http"
                port = int(input("Enter server port (e.g., 8000): "))
                weight = int(input("Enter server weight (for Weighted Round Robin, default 1): "))
                new_server = BackendServer(server_id, host, port, protocol, weight)
                servers.append(new_server)
                if load_balancer: # If an algorithm is already selected, add server to it
                    load_balancer.add_server(new_server)
                print(f"Server {new_server} added.")
            except ValueError:
                print("Invalid input. Please enter valid numbers for port and weight.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == '2':
            # Select Algorithm logic
            print("\n--- Select Algorithm ---")
            print("1. Round Robin")
            print("2. Weighted Round Robin")
            algo_choice = input("Enter algorithm choice: ")

            if algo_choice == '1':
                load_balancer = RoundRobinLoadBalancer()
                for server in servers:
                    load_balancer.add_server(server)
                print("Round Robin algorithm selected.")
            elif algo_choice == '2':
                load_balancer = WeightedRoundRobinLoadBalancer()
                for server in servers:
                    load_balancer.add_server(server)
                print("Weighted Round Robin algorithm selected.")
            else:
                print("Invalid algorithm choice.")

        elif choice == '3':
            # Send Request logic
            if not load_balancer:
                print("Please select a load balancing algorithm first.")
            elif not load_balancer.servers:
                print("No backend servers added yet. Please add servers.")
            else:
                next_server = load_balancer.get_next_server()
                if next_server:
                    print(f"Request routed to: {next_server}")
                else:
                    print("No available servers to route the request.")

        elif choice == '4':
            # List Servers
            if not servers:
                print("No backend servers added yet.")
            else:
                print("\n--- Current Backend Servers ---")
                for server in servers:
                    print(server)

        elif choice == '5':
            # Edit Server logic
            if not servers:
                print("No backend servers added yet.")
                continue
            try:
                server_id_to_edit = int(input("Enter the ID of the server to edit: "))
                server_found = False
                for i, server in enumerate(servers):
                    if server.id == server_id_to_edit:
                        print(f"Editing Server: {server}")
                        new_host = input(f"Enter new host (current: {server.host}): ") or server.host
                        new_protocol = input(f"Enter new protocol (current: {server.protocol}, default http): ").lower() or server.protocol
                        new_port = input(f"Enter new port (current: {server.port}): ")
                        new_weight = input(f"Enter new weight (current: {server.weight}, default 1): ")

                        server.host = new_host
                        server.protocol = new_protocol
                        server.port = int(new_port) if new_port else server.port
                        server.weight = int(new_weight) if new_weight else server.weight

                        # If load balancer is active, update the server in it
                        if load_balancer:
                            # For simplicity, we'll re-add the server to update its properties
                            # A more robust solution might involve specific update methods in load_balancer
                            load_balancer.remove_server(server) # Remove old instance
                            load_balancer.add_server(server)    # Add updated instance

                        print(f"Server {server.id} updated to: {server}")
                        server_found = True
                        break
                if not server_found:
                    print(f"Server with ID {server_id_to_edit} not found.")
            except ValueError:
                print("Invalid input. Please enter valid numbers for ID, port, and weight.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == '6':
            # Delete Server logic
            if not servers:
                print("No backend servers added yet.")
                continue
            try:
                server_id_to_delete = int(input("Enter the ID of the server to delete: "))
                server_found = False
                for i, server in enumerate(servers):
                    if server.id == server_id_to_delete:
                        if load_balancer:
                            load_balancer.remove_server(server)
                        servers.pop(i)
                        print(f"Server {server.id} deleted.")
                        server_found = True
                        # Re-assign IDs to maintain sequential order after deletion
                        for j in range(i, len(servers)):
                            servers[j].id = j + 1
                        break
                if not server_found:
                    print(f"Server with ID {server_id_to_delete} not found.")
            except ValueError:
                print("Invalid input. Please enter a valid integer for ID.")
            except Exception as e:
                print(f"An error occurred: {e}")

        elif choice == '7':
            # Set Local Listening Port
            try:
                port_input = input("Enter the local listening port (e.g., 80): ")
                if port_input:
                    listening_port = int(port_input)
                    print(f"Local listening port set to: {listening_port}")
                else:
                    listening_port = None
                    print("Local listening port cleared.")
            except ValueError:
                print("Invalid port number. Please enter a valid integer.")

        elif choice == '8':
            # Restart Load Balancer
            print("Restarting magicLB...")
            save_config(servers, listening_port) # Save current state before restarting
            try:
                subprocess.run(["./runServer.sh", "restart"], check=True)
                print("magicLB restart command sent.")
            except subprocess.CalledProcessError as e:
                print(f"Error executing restart command: {e}")
            except FileNotFoundError:
                print("Error: runServer.sh script not found. Make sure it's in the same directory and executable.")

        elif choice == '9':
            save_config(servers, listening_port)

        elif choice == '10':
            # Show Status
            print("\n--- Load Balancer Status ---")
            lb_status, pid = check_lb_status()
            print(f"Load Balancer Service Status: {lb_status}")
            if pid: print(f"PID: {pid}")
            print(f"Listening IP: 0.0.0.0") # Proxy listens on all interfaces
            print(f"Listening Port: {listening_port if listening_port else 'Not Set'}")

            print("\n--- Backend Server Status ---")
            if not servers:
                print("No backend servers configured.")
            else:
                for server in servers:
                    status = check_backend_server_status(server.host, server.port)
                    print(f"  {server.host}:{server.port} ({server.protocol.upper()}): {status}")

        elif choice == '11':
            save_config(servers, listening_port) # Save before exiting
            print("Exiting magicLB. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def run_server_mode(listening_port, servers):
    if not listening_port:
        print("Error: Listening port not set. Cannot start proxy server.")
        return

    load_balancer = RoundRobinLoadBalancer() # Default algorithm for server mode
    for server in servers:
        load_balancer.add_server(server)

    proxy_server = ProxyServer("0.0.0.0", listening_port, load_balancer, servers)
    proxy_thread = threading.Thread(target=proxy_server.start)
    proxy_thread.daemon = True
    proxy_thread.start()

    # Keep the main thread alive while the proxy thread runs
    try:
        while True:
            time.sleep(1) # Keep main thread alive
    except KeyboardInterrupt:
        print("Server mode interrupted.")
    finally:
        proxy_server.stop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server_mode":
        listening_port, servers = load_config()
        run_server_mode(listening_port, servers)
    elif len(sys.argv) > 1 and sys.argv[1] == "dialog_mode":
        listening_port, servers = load_config()
        load_balancer = None
        if servers:
            load_balancer = RoundRobinLoadBalancer() 
            for server in servers:
                load_balancer.add_server(server)
            print("Load balancer initialized with loaded servers (Round Robin default).")
        run_dialog_mode(listening_port, servers, load_balancer)
    else:
        print("Usage: python3 -m src.main {server_mode|dialog_mode}")
        print("Please use runServer.sh to start the application.")


