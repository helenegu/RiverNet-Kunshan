# src/simulation.py
import random

def pick_upstream_source(rn):
    """
    Pick a node with indegree 0 as pollution source.
    """
    indegrees = rn.graph.in_degree()
    upstream_nodes = [n for n, deg in indegrees if deg == 0]
    if not upstream_nodes:
        upstream_nodes = list(rn.graph.nodes)
    return random.choice(upstream_nodes)

def simulate_pollution_single_pulse(rn, source_node, decay_factor=0.98, min_threshold=0.001):
    """
    Single-pulse pollution spread along all downstream edges.
    """
    pollution = {n: 0.0 for n in rn.graph.nodes}
    stack = [(source_node, 1.0)]  # (node_id, pollution level)

    while stack:
        node, value = stack.pop()
        if value < min_threshold:
            continue
        # update pollution at this node
        pollution[node] = value
        for neighbor in rn.graph.successors(node):
            stack.append((neighbor, value * decay_factor))

    return pollution
