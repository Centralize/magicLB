
class BackendServer:
    def __init__(self, id, host, port, protocol="http", weight=1):
        self.id = id
        self.host = host
        self.port = port
        self.protocol = protocol # e.g., "http", "https", "tcp"
        self.weight = weight # Used for Weighted Round Robin

    def __str__(self):
        return f"Server(ID: {self.id}, Protocol: {self.protocol.upper()}, Host: {self.host}, Port: {self.port}, Weight: {self.weight})"

    def __eq__(self, other):
        if not isinstance(other, BackendServer):
            return NotImplemented
        return self.id == other.id and \
               self.host == other.host and \
               self.port == other.port and \
               self.protocol == other.protocol and \
               self.weight == other.weight
