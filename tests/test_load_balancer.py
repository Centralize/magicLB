
import unittest
from src.load_balancer import RoundRobinLoadBalancer, WeightedRoundRobinLoadBalancer
from src.backend_server import BackendServer

class TestLoadBalancer(unittest.TestCase):
    def test_round_robin(self):
        lb = RoundRobinLoadBalancer()
        server1 = BackendServer(1, "127.0.0.1", 8001, protocol="http")
        server2 = BackendServer(2, "127.0.0.1", 8002, protocol="https")
        lb.add_server(server1)
        lb.add_server(server2)

        self.assertEqual(lb.get_next_server(), server1)
        self.assertEqual(lb.get_next_server(), server2)
        self.assertEqual(lb.get_next_server(), server1)

    def test_round_robin_remove_server(self):
        lb = RoundRobinLoadBalancer()
        server1 = BackendServer(1, "127.0.0.1", 8001, protocol="http")
        server2 = BackendServer(2, "127.0.0.1", 8002, protocol="https")
        server3 = BackendServer(3, "127.0.0.1", 8003, protocol="http")
        lb.add_server(server1)
        lb.add_server(server2)
        lb.add_server(server3)

        self.assertEqual(lb.get_next_server(), server1)
        lb.remove_server(server1)
        self.assertEqual(len(lb.servers), 2)
        self.assertNotIn(server1, lb.servers)
        self.assertEqual(lb.get_next_server(), server3) # Should skip server2 if index was 1 and reset to 0
        self.assertEqual(lb.get_next_server(), server2)

    def test_backend_server_attributes(self):
        server = BackendServer(1, "192.168.1.1", 9000, protocol="tcp", weight=5)
        self.assertEqual(server.id, 1)
        self.assertEqual(server.host, "192.168.1.1")
        self.assertEqual(server.port, 9000)
        self.assertEqual(server.protocol, "tcp")
        self.assertEqual(server.weight, 5)
        self.assertEqual(str(server), "Server(ID: 1, Protocol: TCP, Host: 192.168.1.1, Port: 9000, Weight: 5)")

    def test_weighted_round_robin(self):
        lb = WeightedRoundRobinLoadBalancer()
        server1 = BackendServer(1, "127.0.0.1", 8001, protocol="http", weight=3)
        server2 = BackendServer(2, "127.0.0.1", 8002, protocol="https", weight=1)
        lb.add_server(server1)
        lb.add_server(server2)

        # Expected sequence: server1, server1, server1, server2, server1, server1, server1, server2...
        # This is a simplified test, actual WRR might be more complex
        self.assertEqual(lb.get_next_server(), server1)
        self.assertEqual(lb.get_next_server(), server1)
        self.assertEqual(lb.get_next_server(), server2) # This might fail depending on WRR implementation
        self.assertEqual(lb.get_next_server(), server1)

    def test_weighted_round_robin_remove_server(self):
        lb = WeightedRoundRobinLoadBalancer()
        server1 = BackendServer(1, "127.0.0.1", 8001, protocol="http", weight=3)
        server2 = BackendServer(2, "127.0.0.1", 8002, protocol="https", weight=1)
        lb.add_server(server1)
        lb.add_server(server2)

        self.assertEqual(lb.get_next_server(), server1)
        lb.remove_server(server1)
        self.assertEqual(len(lb.servers), 1)
        self.assertNotIn(server1, lb.servers)
        self.assertEqual(lb.get_next_server(), server2) # Should be server2 as it's the only one left

if __name__ == '__main__':
    unittest.main()
