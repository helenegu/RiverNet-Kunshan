from collections import defaultdict, deque
import math


class RiverNetwork:
    def __init__(self):
        self.graph = defaultdict(list)  # u -> [(v, travel_time, decay_factor), ...]
        self.nodes = set()

    def add_edge(self, u, v, travel_time, decay_factor=1.0):
        self.graph[u].append((v, travel_time, decay_factor))
        self.nodes.add(u)
        self.nodes.add(v)

    def get_indegrees(self):
        indegree = {v: 0 for v in self.nodes}
        for u in self.graph:
            for (v, _, _) in self.graph[u]:
                indegree[v] += 1
        return indegree


def topo_sort(network: RiverNetwork):
    indegree = network.get_indegrees()
    q = deque()
    for v in network.nodes:
        if indegree[v] == 0:
            q.append(v)

    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for (v, _, _) in network.graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                q.append(v)

    if len(order) != len(network.nodes):
        raise ValueError("Graph is not a DAG (cycle detected).")
    return order
