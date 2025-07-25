# magicLB

magicLB is a Load Balancer application featuring a dialog-based interface. It supports two primary load balancing algorithms:
- **Weighted Round Robin:** Distributes incoming requests based on predefined weights assigned to each backend server.
- **Round Robin:** Distributes incoming requests sequentially to each backend server in a cyclical manner.

Backend servers can be configured with a host, port, protocol (e.g., HTTP, HTTPS, TCP), and an optional weight.

The load balancer now actively listens on a local port (if set) and proxies incoming requests to the configured backend servers.

## Configuration Persistence

magicLB uses a `config.json` file to persist settings and backend server configurations across restarts. When the application starts, it attempts to load existing configurations from this file. You can also manually save the current configuration via the dialog interface.

## Setup

To set up the project, ensure you have Python 3 installed. Then, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The `runServer.sh` script provides commands to manage the magicLB application.

### Start the Load Balancer (Background Service)

To start the load balancer as a background service that listens for incoming connections on the configured port:

```bash
./runServer.sh start
```

### Stop the Load Balancer

To stop the running load balancer background service:

```bash
./runServer.sh stop
```

### Launch Dialog Interface

To launch the interactive dialog interface for managing backend servers and settings (this does NOT start the load balancer service itself):

```bash
./runServer.sh launch_dialog
```

### Restart the Load Balancer

To restart the load balancer background service (stops if running, then starts):

```bash
./runServer.sh restart
```

### Backend Server Management (via Dialog Interface)

Within the dialog interface (`./runServer.sh launch_dialog`):
- **Add Backend Server:** Option to add new servers with host, port, protocol, and weight.
- **Edit Backend Server:** Option to modify existing server details by ID.
- **Delete Backend Server:** Option to remove a server by ID.
- **Set Local Listening Port:** Configure the port on which the load balancer service will listen for incoming requests.
- **Restart Load Balancer:** Option to stop and then start the load balancer process (this will restart the background service if it was running).
- **Show Status:** Display the current status of the load balancer service, listening port, and reachability of backend servers.
