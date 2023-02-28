# Consistent Hashing Routing
import hashlib as hl
from Node import Node


class Router:
    def __int__(self, nodes: int):
        self.total_nodes = nodes
        self.current_nodes_num = nodes
        self.current_nodes = []

    def route(self, key: str) -> int:
        hashed = hl.md5()
        hashed.update(bytes(key.encode('utf-8')))
        return int(hashed.hexdigest(), 16) % self.current_nodes_num

    def add_node(self, ip_address: str, name: str) -> None:
        self.current_nodes.append(Node.__int__(name, ip_address, status=True))

    def remove_node(self, ip_address: str, name: str) -> None:
        self.current_nodes.remove(Node.__int__(name, ip_address, status=True))
