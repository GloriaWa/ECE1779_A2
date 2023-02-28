# Consistent Hashing Routing
import hashlib as hl
from Node import Node


class Router:
    def __int__(self, nodes: int):
        self.total_nodes = nodes
        self.current_nodes_num = nodes
        self.current_nodes = []
        self.hash_ring = []

    def route(self, key: str) -> int:
        hashed = hl.md5()
        hashed.update(bytes(key.encode('utf-8')))
        return int(hashed.hexdigest(), 16) % self.current_nodes_num

    def fill(self) -> None:
        for slot in self.hash_ring:
            for node in self.current_nodes:
                slot = node.name

    def diff(self, new_ring: list, old_ring: list) -> list:
        diff_partition = []
        for (a, b) in zip(new_ring, old_ring):
            if a != b: diff_partition.append(new_ring.index(a))
        return diff_partition

    def add_node(self, ip_address: str, name: str) -> None:
        old_partition = self.hash_ring.copy()
        self.current_nodes.append(Node.__int__(name, ip_address, status=True))
        self.current_nodes.sort(key=lambda x: x.name)
        self.fill()
        collision_partition = self.diff(self.hash_ring, old_partition)
        """
        ## TODO: found collision partitions, need to do data migration
        """

    def remove_node(self, ip_address: str, name: str) -> None:
        removal = Node.__int__(name=name, address=ip_address, status=True)
        removal.cw.clear()
        old_partition = self.hash_ring.copy()
        self.current_nodes.remove(removal)
        self.fill()
        collision_partition = self.diff(self.hash_ring, old_partition)
        """
        ## TODO: found 
        """
