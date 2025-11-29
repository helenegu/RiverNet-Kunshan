# src/visualization.py
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon
from matplotlib.animation import FuncAnimation, PillowWriter

def plot_rivers_map(rn, coords, pollution_map=None, arrow_every=100, boundaries=None, pois=None):
    print("[DEBUG] Entered plot_rivers_map()")

    lines = []
    colors = []
    arrow_edges = []

    print("[DEBUG] Building river lines...")
    for i, u in enumerate(rn.graph):
        for j, v in enumerate(rn.graph.successors(u)):
            if u not in coords or v not in coords:
                continue
            start = coords[u]
            end = coords[v]
            lines.append([start[::-1], end[::-1]])  # (lon, lat)

            if pollution_map:
                colors.append((pollution_map.get(u, 0) + pollution_map.get(v, 0)) / 2)

            if i % arrow_every == 0 and j % arrow_every == 0:
                arrow_edges.append((u, v))

    print(f"[DEBUG] Lines built: {len(lines)}")
    print(f"[DEBUG] Arrow edges: {len(arrow_edges)}")

    if not lines:
        print("[DEBUG] No river edges to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 12))

    # --- Draw river lines ---
    print("[DEBUG] Drawing river lines...")
    if pollution_map and colors:
        colors_array = np.array(colors)
        norm = mcolors.Normalize(vmin=colors_array.min(), vmax=colors_array.max())
        lc = LineCollection(lines, array=colors_array, cmap="plasma", linewidths=1.2, alpha=0.8, norm=norm)

        ax.add_collection(lc)
        sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label="Pollution level")
    else:
        lc = LineCollection(lines, colors="blue", linewidths=1)
        ax.add_collection(lc)

    # --- Draw arrows ---
    print("[DEBUG] Drawing direction arrows...")
    for u, v in arrow_edges:
        if u not in coords or v not in coords:
            continue
        x_start, y_start = coords[u][1], coords[u][0]
        x_end, y_end = coords[v][1], coords[v][0]
        ax.add_patch(FancyArrowPatch(
            (x_start, y_start), (x_end, y_end),
            arrowstyle="->", mutation_scale=5, color="black", alpha=0.4
        ))

    # --- Draw administrative boundaries ---
    print("[DEBUG] Drawing boundaries...")
    if boundaries:
        print(f"[DEBUG] Total boundaries: {len(boundaries)}")
        for poly in boundaries:
            ax.add_patch(Polygon(
                [(lon, lat) for lat, lon in poly],
                closed=True, edgecolor="green", facecolor="none", linewidth=0.8, alpha=0.5
            ))
    else:
        print("[DEBUG] No boundaries provided.")

    # --- Draw POIs ---
    print("[DEBUG] Drawing POIs...")
    if pois:
        valid_pois = [p for p in pois if "category" in p and not (np.isnan(p["lat"]) or np.isnan(p["lon"]))]
        if not valid_pois:
            print("[DEBUG] No valid POIs to draw.")
        else:
            pollution_x = [p["lon"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_y = [p["lat"] for p in valid_pois if p["category"] == "pollution_source"]
            at_risk_x = [p["lon"] for p in valid_pois if p["category"] != "pollution_source"]
            at_risk_y = [p["lat"] for p in valid_pois if p["category"] != "pollution_source"]

            scatter_handles = []
            if pollution_x:
                print(f"[DEBUG] Drawing {len(pollution_x)} pollution source POIs.")
                h1 = ax.scatter(pollution_x, pollution_y, c="red", marker="s", s=30, zorder=10)
                scatter_handles.append((h1, "Pollution source"))
            if at_risk_x:
                print(f"[DEBUG] Drawing {len(at_risk_x)} at-risk POIs.")
                h2 = ax.scatter(at_risk_x, at_risk_y, c="blue", marker="^", s=10, zorder=5)
                scatter_handles.append((h2, "At-risk zone"))
            if scatter_handles:
                handles, labels = zip(*scatter_handles)
                ax.legend(handles, labels, loc="upper right")
    else:
        print("[DEBUG] No POIs to draw.")

    # --- Set axis limits ---
    print("[DEBUG] Setting axis limits...")
    lats = [lat for lat, lon in coords.values()]
    lons = [lon for lat, lon in coords.values()]
    margin_lat = (max(lats) - min(lats)) * 0.02
    margin_lon = (max(lons) - min(lons)) * 0.02
    ax.set_xlim(min(lons) - margin_lon, max(lons) + margin_lon)
    ax.set_ylim(min(lats) - margin_lat, max(lats) + margin_lat)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Jiangsu River Network with Pollution")

    plt.tight_layout()
    print("[DEBUG] Finished plotting! Displaying figure...")
    plt.show(block=True)


def animate_pollution(rn, coords, pollution_snapshots, pois=None, log_scale=False, arrow_every=200, save_path=None):
    print("[DEBUG] Entered animate_pollution()")
    lines = []
    for u in rn.graph:
        for v in rn.graph.successors(u):
            if u not in coords or v not in coords:
                continue
            lines.append([coords[u][::-1], coords[v][::-1]])

    fig, ax = plt.subplots(figsize=(12, 12))
    lc = LineCollection(lines, cmap="plasma", linewidths=1.5, alpha=0.8)
    ax.add_collection(lc)

    # --- Draw persistent POIs ---
    print("[DEBUG] Drawing POIs on animation...")
    if pois:
        valid_pois = [p for p in pois if "category" in p and not (np.isnan(p["lat"]) or np.isnan(p["lon"]))]
        if valid_pois:
            pollution_x = [p["lon"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_y = [p["lat"] for p in valid_pois if p["category"] == "pollution_source"]
            at_risk_x = [p["lon"] for p in valid_pois if p["category"] != "pollution_source"]
            at_risk_y = [p["lat"] for p in valid_pois if p["category"] != "pollution_source"]

            handles = []
            if pollution_x:
                print(f"[DEBUG] Animation: {len(pollution_x)} pollution source POIs")
                h1 = ax.scatter(pollution_x, pollution_y, marker="s", color="red", s=30, zorder=5)
                handles.append((h1, "Pollution source"))
            if at_risk_x:
                print(f"[DEBUG] Animation: {len(at_risk_x)} at-risk POIs")
                h2 = ax.scatter(at_risk_x, at_risk_y, marker="^", color="blue", s=30, zorder=5)
                handles.append((h2, "At-risk zone"))
            if handles:
                hs, labels = zip(*handles)
                ax.legend(hs, labels, loc="upper right")
        else:
            print("[DEBUG] Animation: No valid POIs to draw.")
    else:
        print("[DEBUG] Animation: No POIs provided.")

    # --- Set axis limits ---
    lats = [lat for lat, lon in coords.values()]
    lons = [lon for lat, lon in coords.values()]
    margin_lat = (max(lats) - min(lats)) * 0.02
    margin_lon = (max(lons) - min(lons)) * 0.02
    ax.set_xlim(min(lons) - margin_lon, max(lons) + margin_lon)
    ax.set_ylim(min(lats) - margin_lat, max(lats) + margin_lat)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    def update(frame):
        pollution_map = pollution_snapshots[frame]
        colors = np.array([(pollution_map.get(u, 0) + pollution_map.get(v, 0)) / 2 for u, v in rn.graph.edges()])
        norm = mcolors.Normalize(vmin=colors.min(), vmax=colors.max())
        lc.set_array(colors)
        lc.set_norm(norm)

        ax.set_title(f"Step {frame + 1}/{len(pollution_snapshots)}")
        return lc,

    anim = FuncAnimation(fig, update, frames=len(pollution_snapshots), interval=200, blit=True)

    if save_path:
        print(f"[DEBUG] Saving animation to {save_path} ...")
        writer = PillowWriter(fps=5)
        anim.save(save_path, writer=writer)
        print("[DEBUG] Animation saved!")

    plt.show()

def animate_pollution_zoomed(rn, coords, pollution_snapshots, source_node, pois=None, log_scale=False, save_path=None):
    print("[DEBUG] Entered animate_pollution_zoomed()")
    
    # --- Get source coordinates ---
    source_lat, source_lon = coords[source_node]
    zoom_radius = 0.005  # degrees (~0.5 km)

    # --- Prepare lines ---
    lines = []
    for u in rn.graph:
        for v in rn.graph.successors(u):
            if u not in coords or v not in coords:
                continue
            lines.append([coords[u][::-1], coords[v][::-1]])  # (lon, lat)

    fig, ax = plt.subplots(figsize=(12, 12))
    lc = LineCollection(lines, cmap="plasma", linewidths=1.5, alpha=0.8)
    ax.add_collection(lc)

    # --- Draw persistent POIs ---
    if pois:
        valid_pois = [p for p in pois if "category" in p and not (np.isnan(p["lat"]) or np.isnan(p["lon"]))]
        if valid_pois:
            pollution_x = [p["lon"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_y = [p["lat"] for p in valid_pois if p["category"] == "pollution_source"]
            at_risk_x = [p["lon"] for p in valid_pois if p["category"] != "pollution_source"]
            at_risk_y = [p["lat"] for p in valid_pois if p["category"] != "pollution_source"]

            handles = []
            if pollution_x:
                h1 = ax.scatter(pollution_x, pollution_y, marker="s", color="red", s=30, zorder=5)
                handles.append((h1, "Pollution source"))
            if at_risk_x:
                h2 = ax.scatter(at_risk_x, at_risk_y, marker="^", color="blue", s=10, zorder=5)
                handles.append((h2, "At-risk zone"))
            if handles:
                hs, labels = zip(*handles)
                ax.legend(hs, labels, loc="upper right")

    # --- Set fixed zoomed axis around source ---
    ax.set_xlim(source_lon - zoom_radius, source_lon + zoom_radius)
    ax.set_ylim(source_lat - zoom_radius, source_lat + zoom_radius)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # --- Set global min/max for colors ---
    all_colors = [ (pollution_snapshots[f].get(u,0) + pollution_snapshots[f].get(v,0))/2
                   for f in range(len(pollution_snapshots)) 
                   for u,v in rn.graph.edges()]
    global_min, global_max = min(all_colors), max(all_colors)

    def update(frame):
        pollution_map = pollution_snapshots[frame]
        colors = np.array([(pollution_map.get(u, 0) + pollution_map.get(v, 0)) / 2 for u, v in rn.graph.edges()])
        if log_scale:
            colors = np.log10(0.01 + colors)
        lc.set_array(colors)
        lc.set_norm(mcolors.Normalize(vmin=global_min, vmax=global_max))
        ax.set_title(f"Step {frame + 1}/{len(pollution_snapshots)}")
        return lc,

    anim = FuncAnimation(fig, update, frames=len(pollution_snapshots), interval=200, blit=True)

    if save_path:
        print(f"[DEBUG] Saving animation to {save_path} ...")
        writer = PillowWriter(fps=5)
        anim.save(save_path, writer=writer)
        print("[DEBUG] Animation saved!")

    plt.show()
