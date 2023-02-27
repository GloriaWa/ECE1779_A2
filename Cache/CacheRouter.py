# Consistent Hashing Routing
import hashlib as hl
from collections import OrderedDict

class Router:
    def __int__(self, nodes: int):
        self.total_nodes = nodes
        self.current_nodes = nodes
        self.address_book = []    # add IP addresses here
        self.node_status = {}  # show whether each node is active

    def route(self, key: str) -> int:
        hashed = hl.md5().update(bytes(key))
        return int(hashed.hexdigest(), 16) % self.current_nodes

    def add_node(self, ip_address: str) -> None:
        self.address_book.append(ip_address)
        self.node_status.update({ip_address: True})

    def remove_node(self, ip_address: str) -> None:
        self.node_status.update({ip_address: False})