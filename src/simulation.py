# src/simulation.py
import random
import networkx as nx

def pick_upstream_source(river_network):
    """
    Pick a random upstream node (source) in the river network.
    Assumes nodes with no incoming edges are upstream sources.
    """
    G = river_network.graph
    upstream_nodes = [n for n, deg in G.in_degree() if deg == 0]
    
    if not upstream_nodes:
        # fallback: pick any random node
        upstream_nodes = list(G.nodes)
    
    source_node = random.choice(upstream_nodes)
    print("Selected source node:", source_node)
    return source_node

def simulate_pollution(river_network, source_node, decay=0.9):
    """
    Simple pollution spread simulation along the river network.
    - decay: pollution decay factor per edge
    Returns a dict mapping nodes to pollution concentration.
    """
    G = river_network.graph
    concentrations = {node: 0 for node in G.nodes}
    concentrations[source_node] = 1.0  # start with full pollution at source

    # Use BFS to propagate pollution downstream
    queue = [(source_node, 1.0)]
    while queue:
        current_node, current_conc = queue.pop(0)
        for neighbor in G.successors(current_node):
            next_conc = current_conc * decay
            if next_conc > concentrations[neighbor]:
                concentrations[neighbor] = next_conc
                queue.append((neighbor, next_conc))

    return concentrations
