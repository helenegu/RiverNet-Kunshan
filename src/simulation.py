# src/simulation.py
from collections import defaultdict
import random

def pick_upstream_sources(rn, num_sources=1):
    """
    Pick multiple nodes with indegree 0 as pollution sources.
    Returns a list of node IDs.
    """
    indegrees = rn.graph.in_degree()
    upstream_nodes = [n for n, deg in indegrees if deg == 0]
    if not upstream_nodes:
        upstream_nodes = list(rn.graph.nodes)
    return random.sample(upstream_nodes, min(num_sources, len(upstream_nodes)))


def simulate_pollution_downstream(rn, source_nodes, retention=0.2, min_threshold=0.001):

    pollution = {n: 0.0 for n in rn.graph.nodes} # Total pollution accumulated in the system
    arrival = defaultdict(float)  # arrival[node] = inflow of pollution to node for current timestep

    # Initialize with source nodes
    for node, intensity in source_nodes:
        arrival[node] += intensity

    # Continue while some pollution is still flowing
    while arrival:
        next_arrival = defaultdict(float)

        for node, inflow in arrival.items():
            if inflow < min_threshold:
                continue

            # 1. Retain portion of inflow
            retained = inflow * retention
            pollution[node] += retained

            # 2. Remaining pollution to send downstream
            to_send = inflow * (1 - retention)
            if to_send < min_threshold:
                continue

            neighbors = list(rn.graph.successors(node))

            if neighbors:
                share = to_send / len(neighbors)
                for nbr in neighbors:
                    next_arrival[nbr] += share
            else:
                # leaf node keeps all pollution
                pollution[node] += to_send

        arrival = next_arrival

    return pollution


def simulate_pollution_animation(
    rn, 
    source_nodes, 
    retention=0.2, 
    min_threshold=0.001
):
    """
    Timestep-based simulation with snapshots for animation.
    """

    pollution = {n: 0.0 for n in rn.graph.nodes}
    arrival = defaultdict(float)
    snapshots = []

    for node, intensity in source_nodes:
        arrival[node] += intensity

    while arrival:
        next_arrival = defaultdict(float)

        for node, inflow in arrival.items():
            if inflow < min_threshold:
                continue

            retained = inflow * retention
            pollution[node] += retained

            to_send = inflow * (1 - retention)
            if to_send < min_threshold:
                continue

            neighbors = list(rn.graph.successors(node))
            if neighbors:
                share = to_send / len(neighbors)
                for nbr in neighbors:
                    next_arrival[nbr] += share
            else:
                pollution[node] += to_send

        snapshots.append(pollution.copy())
        arrival = next_arrival

    return snapshots
