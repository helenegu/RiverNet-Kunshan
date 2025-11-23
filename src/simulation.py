import math
from .river_network import topo_sort, RiverNetwork


def simulate_pollution(network: RiverNetwork, sources):
    arrival_time = {v: math.inf for v in network.nodes}
    concentration = {v: 0.0 for v in network.nodes}

    for src in sources:
        node = src["node"]
        C0 = src["concentration"]
        t0 = src["start_time"]
        arrival_time[node] = min(arrival_time[node], t0)
        concentration[node] = max(concentration[node], C0)

    order = topo_sort(network)

    for u in order:
        if arrival_time[u] is math.inf or concentration[u] == 0.0:
            continue
        for (v, travel_time, decay_factor) in network.graph[u]:
            cand_arrival = arrival_time[u] + travel_time
            cand_conc = concentration[u] * decay_factor

            if cand_conc > 0:
                if cand_arrival < arrival_time[v]:
                    arrival_time[v] = cand_arrival
                concentration[v] = max(concentration[v], cand_conc)

    return arrival_time, concentration


def pick_upstream_source(network: RiverNetwork):
    indegree = network.get_indegrees()
    upstream_nodes = [v for v, deg in indegree.items() if deg == 0]
    return upstream_nodes[0] if upstream_nodes else None
