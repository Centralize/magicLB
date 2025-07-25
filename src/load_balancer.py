
class LoadBalancer:
    def __init__(self):
        self.servers = []

    def add_server(self, server):
        self.servers.append(server)

    def remove_server(self, server_to_remove):
        self.servers = [server for server in self.servers if server != server_to_remove]

    def get_next_server(self):
        raise NotImplementedError("Subclasses must implement this method")

class RoundRobinLoadBalancer(LoadBalancer):
    def __init__(self):
        super().__init__()
        self.current_server_index = 0

    def remove_server(self, server_to_remove):
        super().remove_server(server_to_remove)
        if self.servers and self.current_server_index >= len(self.servers):
            self.current_server_index = 0 # Reset index if it's out of bounds

    def get_next_server(self):
        if not self.servers:
            return None
        server = self.servers[self.current_server_index]
        self.current_server_index = (self.current_server_index + 1) % len(self.servers)
        return server

class WeightedRoundRobinLoadBalancer(LoadBalancer):
    def __init__(self):
        super().__init__()
        self.current_weight_index = -1
        self.current_server_index = -1
        self.max_weight = 0
        self.gcd_weight = 0

    def add_server(self, server):
        super().add_server(server)
        self._recalculate_weights()
        if self.servers:
            self.current_weight_index = self.max_weight

    def remove_server(self, server_to_remove):
        super().remove_server(server_to_remove)
        self._recalculate_weights()
        if self.servers:
            self.current_weight_index = self.max_weight
            self.current_server_index = -1 # Reset index for WRR
        else:
            self.current_weight_index = -1
            self.current_server_index = -1

    def _recalculate_weights(self):
        if not self.servers:
            self.max_weight = 0
            self.gcd_weight = 0
            return

        weights = [s.weight for s in self.servers]
        self.max_weight = max(weights)
        self.gcd_weight = self._gcd_list(weights)

    def _gcd(self, a, b):
        while b:
            a, b = b, a % b
        return a

    def _gcd_list(self, numbers):
        if not numbers:
            return 0
        result = numbers[0]
        for i in range(1, len(numbers)):
            result = self._gcd(result, numbers[i])
        return result

    def get_next_server(self):
        if not self.servers:
            return None

        while True:
            self.current_server_index = (self.current_server_index + 1) % len(self.servers)
            if self.current_server_index == 0:
                self.current_weight_index -= self.gcd_weight
                if self.current_weight_index <= 0:
                    self.current_weight_index = self.max_weight

            if self.servers[self.current_server_index].weight >= self.current_weight_index:
                return self.servers[self.current_server_index]

