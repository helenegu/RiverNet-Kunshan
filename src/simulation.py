# src/simulation.py
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

def simulate_pollution_downstream(rn, source_nodes, decay_factor=0.98, retention=0.2, min_threshold=0.001):

    pollution = {n: 0.0 for n in rn.graph.nodes}
    stack = [(node, intensity) for node, intensity in source_nodes]

    while stack:
        node, value = stack.pop()
        if value < min_threshold:
            continue

        # Retain a fraction at this node
        retained = value * retention
        pollution[node] += retained

        # Remaining pollution to send downstream
        to_send = value * (1 - retention) * decay_factor
        if to_send < min_threshold:
            continue

        downstream_neighbors = list(rn.graph.successors(node))
        if downstream_neighbors:
            spread_value = to_send / len(downstream_neighbors)
            for neighbor in downstream_neighbors:
                stack.append((neighbor, spread_value))
        else:
            # Leaf node keeps all remaining pollution
            pollution[node] += to_send

    return pollution


def simulate_pollution_animation(rn, source_nodes, decay_factor=0.98, retention=0.2, min_threshold=0.001):
    """
    Return list of pollution maps over time for animation.
    """
    pollution = {n: 0.0 for n in rn.graph.nodes}
    stack = [(node, intensity) for node, intensity in source_nodes]
    snapshots = []

    while stack:
        next_stack = []
        for node, value in stack:
            if value < min_threshold:
                continue

            retained = value * retention
            pollution[node] += retained

            to_send = value * (1 - retention) * decay_factor
            if to_send < min_threshold:
                continue

            downstream_neighbors = list(rn.graph.successors(node))
            if downstream_neighbors:
                spread_value = to_send / len(downstream_neighbors)
                for neighbor in downstream_neighbors:
                    next_stack.append((neighbor, spread_value))
            else:
                pollution[node] += to_send

        snapshots.append(pollution.copy())
        stack = next_stack

    return snapshots


