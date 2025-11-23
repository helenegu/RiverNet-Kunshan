# src/visualization.py
import matplotlib.pyplot as plt

def plot_concentration_map(node_coords, concentration_map, figsize=(10, 10), cmap="Reds"):
    """
    Plot pollution concentration along the river network.
    
    node_coords: dict mapping node -> (x, y) coordinates
    concentration_map: dict mapping node -> pollution level (0-1)
    """
    # Prepare coordinates
    xs = []
    ys = []
    colors = []

    for node, (x, y) in node_coords.items():
        xs.append(x)
        ys.append(y)
        colors.append(concentration_map.get(node, 0))

    plt.figure(figsize=figsize)
    sc = plt.scatter(xs, ys, c=colors, cmap=cmap, s=10, alpha=0.8)
    plt.colorbar(sc, label="Pollution concentration")
    plt.title("River Pollution Simulation")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.axis("equal")
    plt.show()
