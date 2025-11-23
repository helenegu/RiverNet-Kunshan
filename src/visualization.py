# src/visualization.py
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.patches import FancyArrowPatch

def plot_rivers_map(rn, coords, pollution_map=None, source_node=None,
                    log_scale=True, arrow_every=100):
    """
    Plot river network with optional pollution overlay and source node highlight.
    Arrows are shown every `arrow_every` edges to avoid clutter.
    """
    lines, colors = [], []
    arrow_edges = []

    for i, u in enumerate(rn.graph):
        for j, v in enumerate(rn.graph.successors(u)):
            if u not in coords or v not in coords:
                continue
            start = coords[u]
            end = coords[v]
            lines.append([start[::-1], end[::-1]])  # lon, lat

            if pollution_map:
                colors.append((pollution_map.get(u, 0) + pollution_map.get(v, 0)) / 2)
            
            if i % arrow_every == 0 and j % arrow_every == 0:
                arrow_edges.append((u, v))

    if not lines:
        print("No edges to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 12))

    # Draw river lines
    if pollution_map and colors:
        colors_array = np.array(colors)
        if log_scale:
            colors_array = np.log10(0.01 + colors_array)
        norm = mcolors.Normalize(vmin=colors_array.min(), vmax=colors_array.max())
        lc = LineCollection(lines, array=colors_array, cmap="plasma", linewidths=1.5, alpha=0.8, norm=norm)
        ax.add_collection(lc)
        sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
        plt.colorbar(sm, ax=ax, label="Pollution level")
    else:
        lc = LineCollection(lines, colors='blue', linewidths=1)
        ax.add_collection(lc)

    # Draw arrows on selected edges only
    for u, v in arrow_edges:
        x_start, y_start = coords[u][1], coords[u][0]
        x_end, y_end = coords[v][1], coords[v][0]
        ax.add_patch(FancyArrowPatch(
            (x_start, y_start), (x_end, y_end),
            arrowstyle='->', mutation_scale=5, color='black', alpha=0.5
        ))

    # Highlight source node
    if source_node is not None and source_node in coords:
        lat, lon = coords[source_node]
        ax.scatter(lon, lat, color='red', s=60, zorder=5, label='Source')
        ax.legend()

    # Set axis limits
    lats = [lat for lat, lon in coords.values()]
    lons = [lon for lat, lon in coords.values()]
    margin_lat = (max(lats) - min(lats)) * 0.02
    margin_lon = (max(lons) - min(lons)) * 0.02
    ax.set_xlim(min(lons) - margin_lon, max(lons) + margin_lon)
    ax.set_ylim(min(lats) - margin_lat, max(lats) + margin_lat)
    ax.set_aspect('equal')
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Jiangsu River Network with Pollution" if pollution_map else "Jiangsu River Network")

    plt.tight_layout()
    plt.show(block=True)
