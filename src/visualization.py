# src/visualization.py
"""
Rewritten visualization module for timestep-based river pollution simulation.

Functions:
- plot_rivers_map(rn, coords, pollution_map=None, arrow_every=100, boundaries=None, pois=None, log_scale=False)
- animate_pollution(rn, coords, pollution_snapshots, pois=None, log_scale=False, arrow_every=200, interval=200, save_path=None)
- animate_pollution_zoomed(rn, coords, pollution_snapshots, source_node, pois=None, log_scale=False, zoom_radius=0.005, interval=200, save_path=None)

Assumptions:
- `coords` is a dict mapping node -> (lat, lon)
- `rn.graph` is a networkx-like directed graph; rn.graph.edges() yields (u, v) edges
- `pollution_snapshots` is a list of dicts [{node: value, ...}, ...] each representing a timestep
- POIs (if provided) are dicts with keys including "lat", "lon", "category", and optionally "intensity"
"""

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon
from matplotlib.animation import FuncAnimation, PillowWriter
import math


# ---------------------------
# Utility helpers
# ---------------------------

def _coords_to_segment(u, v, coords):
    """Return ((lon_u, lat_u), (lon_v, lat_v)) or None if missing coords."""
    if u not in coords or v not in coords:
        return None
    # coords are (lat, lon) in the dataset; LineCollection expects (x=lon, y=lat)
    start = coords[u]
    end = coords[v]
    return (start[1], start[0]), (end[1], end[0])


def _compute_global_range_from_snapshots(pollution_snapshots, log_scale=False):
    """Compute global vmin, vmax across all snapshots for consistent color scaling."""
    if not pollution_snapshots:
        return 0.0, 1.0
    values = []
    for snap in pollution_snapshots:
        if log_scale:
            values.extend([math.log10(0.01 + v) for v in snap.values()])
        else:
            values.extend(list(snap.values()))
    if not values:
        return 0.0, 1.0
    vmin, vmax = min(values), max(values)
    # protect against equal min/max
    if vmin == vmax:
        vmax = vmin + 1e-9
    return vmin, vmax


# ---------------------------
# Static river map
# ---------------------------

def plot_rivers_map(rn, coords, pollution_map=None, arrow_every=100, boundaries=None, pois=None, log_scale=False):
    """
    Static plot of rivers with optional node-based pollution overlay and POIs.
    - edges colored by downstream node pollution (if pollution_map supplied)
    - nodes plotted as small scatter dots colored by pollution
    """
    print("[DEBUG] Entered plot_rivers_map()")

    # Build edge segments and optional edge colors (downstream node)
    segments = []
    edge_down_values = []
    for i, (u, v) in enumerate(rn.graph.edges()):
        seg = _coords_to_segment(u, v, coords)
        if seg is None:
            continue
        segments.append(seg)
        if pollution_map is not None:
            edge_down_values.append(pollution_map.get(v, 0.0))

    if not segments:
        print("[DEBUG] No river edges to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 12))

    # Edge drawing
    if pollution_map is not None and edge_down_values:
        colors_array = np.array(edge_down_values)
        if log_scale:
            colors_array = np.log10(0.01 + colors_array)
        norm = mcolors.Normalize(vmin=colors_array.min(), vmax=colors_array.max())
        lc = LineCollection(segments, array=colors_array, cmap="plasma", linewidths=1.2, alpha=0.9, norm=norm)
        ax.add_collection(lc)
        sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
        sm.set_array([])  # required for colorbar
        cbar = plt.colorbar(sm, ax=ax, label="Pollution (downstream node)")
        cbar.ax.ticklabel_format(useOffset=False)
    else:
        lc = LineCollection(segments, colors="lightblue", linewidths=1.0, alpha=0.9)
        ax.add_collection(lc)

    # Draw small node dots colored by pollution_map (if provided)
    node_list = list(rn.graph.nodes())
    xs = []
    ys = []
    node_vals = []
    for n in node_list:
        if n not in coords:
            xs.append(np.nan); ys.append(np.nan); node_vals.append(0.0); continue
        lat, lon = coords[n]
        xs.append(lon); ys.append(lat)
        node_vals.append(pollution_map.get(n, 0.0) if pollution_map is not None else 0.0)

    if pollution_map is not None:
        plot_vals = np.log10(0.01 + np.array(node_vals)) if log_scale else np.array(node_vals)
        vmin = plot_vals.min(); vmax = plot_vals.max()
        if vmin == vmax:
            vmax = vmin + 1e-9
        sc = ax.scatter(xs, ys, c=plot_vals, cmap="plasma", s=8, edgecolors='none', vmin=vmin, vmax=vmax, zorder=5)
        # colorbar if not already from edges (we prefer single colorbar)
        if 'sm' not in locals():
            sm2 = plt.cm.ScalarMappable(cmap="plasma", norm=mcolors.Normalize(vmin=vmin, vmax=vmax))
            sm2.set_array([])
            plt.colorbar(sm2, ax=ax, label="Pollution (node)")
    else:
        # draw very small dots for nodes for context
        ax.scatter(xs, ys, c="black", s=4, zorder=4)

    # Direction arrows (sparser)
    arrow_edges = []
    for i, (u, v) in enumerate(rn.graph.edges()):
        if (i % arrow_every) == 0:
            arrow_edges.append((u, v))
    for u, v in arrow_edges:
        if u not in coords or v not in coords:
            continue
        # FancyArrowPatch expects (x, y) = (lon, lat)
        x_start, y_start = coords[u][1], coords[u][0]
        x_end, y_end = coords[v][1], coords[v][0]
        ax.add_patch(FancyArrowPatch((x_start, y_start), (x_end, y_end),
                                    arrowstyle="->", mutation_scale=6, color="black", alpha=0.4, linewidth=0.6))

    # Boundaries
    if boundaries:
        for poly in boundaries:
            ax.add_patch(Polygon([(lon, lat) for lat, lon in poly],
                                 closed=True, edgecolor="green", facecolor="none", linewidth=0.7, alpha=0.5))

    # POIs
    if pois:
        valid_pois = [p for p in pois if "category" in p and not (np.isnan(p["lat"]) or np.isnan(p["lon"]))]
        if valid_pois:
            pollution_x = [p["lon"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_y = [p["lat"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_sizes = [p.get("intensity", 0.5) * 100 for p in valid_pois if p["category"] == "pollution_source"]
            at_risk_x = [p["lon"] for p in valid_pois if p["category"] != "pollution_source"]
            at_risk_y = [p["lat"] for p in valid_pois if p["category"] != "pollution_source"]

            handles = []
            if pollution_x:
                h1 = ax.scatter(pollution_x, pollution_y, marker="s", color="red", s=pollution_sizes, zorder=12)
                handles.append((h1, "Pollution source"))
            if at_risk_x:
                h2 = ax.scatter(at_risk_x, at_risk_y, marker="^", color="blue", s=10, zorder=8)
                handles.append((h2, "At-risk zone"))
            if handles:
                hs, labels = zip(*handles)
                ax.legend(hs, labels, loc="upper right")

    # Axis limits
    lats = [lat for lat, lon in coords.values() if not np.isnan(lat)]
    lons = [lon for lat, lon in coords.values() if not np.isnan(lon)]
    if lats and lons:
        margin_lat = (max(lats) - min(lats)) * 0.02
        margin_lon = (max(lons) - min(lons)) * 0.02
        ax.set_xlim(min(lons) - margin_lon, max(lons) + margin_lon)
        ax.set_ylim(min(lats) - margin_lat, max(lats) + margin_lat)

    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("River Network")
    plt.tight_layout()
    plt.show()


# ---------------------------
# Animation (global)
# ---------------------------

def animate_pollution(rn, coords, pollution_snapshots, pois=None, log_scale=False,
                      arrow_every=200, interval=200, save_path=None):
    """
    Animate timestep-based pollution snapshots.
    Nodes are shown as very small colored dots; edges get colored by downstream node pollution.
    """
    print("[DEBUG] Entered animate_pollution()")
    if not pollution_snapshots:
        print("[DEBUG] No snapshots provided.")
        return None

    # Prepare segments and node positions
    segments = []
    edges = list(rn.graph.edges())
    for u, v in edges:
        seg = _coords_to_segment(u, v, coords)
        if seg is not None:
            segments.append(seg)

    node_list = list(rn.graph.nodes())
    xs = []
    ys = []
    for n in node_list:
        if n in coords:
            lat, lon = coords[n]
            xs.append(lon); ys.append(lat)
        else:
            xs.append(np.nan); ys.append(np.nan)

    # global color range
    vmin, vmax = _compute_global_range_from_snapshots(pollution_snapshots, log_scale=log_scale)

    fig, ax = plt.subplots(figsize=(12, 12))

    # initial LineCollection and scatter (with placeholder colors)
    # Edge colors initially zeros
    lc = LineCollection(segments, cmap="plasma", linewidths=1.5, alpha=0.85)
    ax.add_collection(lc)

    # Node scatter (very small dots)
    initial_vals = [pollution_snapshots[0].get(n, 0.0) for n in node_list]
    if log_scale:
        initial_vals = np.log10(0.01 + np.array(initial_vals))
    sc = ax.scatter(xs, ys, c=initial_vals, cmap="plasma", s=6, edgecolors='none', vmin=vmin, vmax=vmax, zorder=5)

    # persistent POIs
    if pois:
        valid_pois = [p for p in pois if "category" in p and not (np.isnan(p["lat"]) or np.isnan(p["lon"]))]
        if valid_pois:
            pollution_x = [p["lon"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_y = [p["lat"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_sizes = [p.get("intensity", 0.5) * 100 for p in valid_pois if p["category"] == "pollution_source"]
            at_risk_x = [p["lon"] for p in valid_pois if p["category"] != "pollution_source"]
            at_risk_y = [p["lat"] for p in valid_pois if p["category"] != "pollution_source"]

            handles = []
            if pollution_x:
                h1 = ax.scatter(pollution_x, pollution_y, marker="s", color="red", s=pollution_sizes, zorder=12)
                handles.append((h1, "Pollution source"))
            if at_risk_x:
                h2 = ax.scatter(at_risk_x, at_risk_y, marker="^", color="blue", s=10, zorder=8)
                handles.append((h2, "At-risk zone"))
            if handles:
                hs, labels = zip(*handles)
                ax.legend(hs, labels, loc="upper right")

    # axis limits
    lats = [lat for lat, lon in coords.values() if not np.isnan(lat)]
    lons = [lon for lat, lon in coords.values() if not np.isnan(lon)]
    if lats and lons:
        margin_lat = (max(lats) - min(lats)) * 0.02
        margin_lon = (max(lons) - min(lons)) * 0.02
        ax.set_xlim(min(lons) - margin_lon, max(lons) + margin_lon)
        ax.set_ylim(min(lats) - margin_lat, max(lats) + margin_lat)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # shared scalar mappable for colorbar
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, label="Pollution (log10)" if log_scale else "Pollution")

    def update(frame):
        pollution_map = pollution_snapshots[frame]
        # edge colors by downstream node v
        edge_vals = np.array([pollution_map.get(v, 0.0) for u, v in edges])
        if log_scale:
            edge_vals = np.log10(0.01 + edge_vals)
        lc.set_array(edge_vals)

        # node colors
        node_vals = np.array([pollution_map.get(n, 0.0) for n in node_list])
        if log_scale:
            node_vals = np.log10(0.01 + node_vals)
        sc.set_array(node_vals)

        ax.set_title(f"Step {frame + 1}/{len(pollution_snapshots)}")
        return lc, sc

    anim = FuncAnimation(fig, update, frames=len(pollution_snapshots), interval=interval, blit=False)

    if save_path:
        writer = PillowWriter(fps=1000 // interval if interval else 5)
        anim.save(save_path, writer=writer)
        print(f"[DEBUG] Animation saved to {save_path}")

    plt.show()
    return anim


# ---------------------------
# Zoomed animation (around a source node)
# ---------------------------

def animate_pollution_zoomed(rn, coords, pollution_snapshots, source_node, pois=None, log_scale=False,
                             zoom_radius=0.005, interval=200, save_path=None):
    """
    Animation zoomed into the neighborhood of `source_node`.
    zoom_radius is in degrees (lat/lon).
    """
    print("[DEBUG] Entered animate_pollution_zoomed()")

    if source_node not in coords:
        raise ValueError("source_node not in coords")

    source_lat, source_lon = coords[source_node]

    # Prepare edges within zoomed box (so edges outside are still drawn but clipped)
    edges = list(rn.graph.edges())
    node_list = list(rn.graph.nodes())
    xs = []
    ys = []
    for n in node_list:
        if n in coords:
            lat, lon = coords[n]
            xs.append(lon); ys.append(lat)
        else:
            xs.append(np.nan); ys.append(np.nan)

    vmin, vmax = _compute_global_range_from_snapshots(pollution_snapshots, log_scale=log_scale)

    fig, ax = plt.subplots(figsize=(10, 10))
    segments = []
    for u, v in edges:
        seg = _coords_to_segment(u, v, coords)
        if seg is not None:
            segments.append(seg)
    lc = LineCollection(segments, cmap="plasma", linewidths=1.5, alpha=0.85)
    ax.add_collection(lc)

    # node scatter
    initial_vals = [pollution_snapshots[0].get(n, 0.0) for n in node_list]
    if log_scale:
        initial_vals = np.log10(0.01 + np.array(initial_vals))
    sc = ax.scatter(xs, ys, c=initial_vals, cmap="plasma", s=6, edgecolors='none', vmin=vmin, vmax=vmax, zorder=5)

    # POIs as persistent markers
    if pois:
        valid_pois = [p for p in pois if "category" in p and not (np.isnan(p["lat"]) or np.isnan(p["lon"]))]
        if valid_pois:
            pollution_x = [p["lon"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_y = [p["lat"] for p in valid_pois if p["category"] == "pollution_source"]
            pollution_sizes = [p.get("intensity", 0.5) * 100 for p in valid_pois if p["category"] == "pollution_source"]
            at_risk_x = [p["lon"] for p in valid_pois if p["category"] != "pollution_source"]
            at_risk_y = [p["lat"] for p in valid_pois if p["category"] != "pollution_source"]

            handles = []
            if pollution_x:
                h1 = ax.scatter(pollution_x, pollution_y, marker="s", color="red", s=pollution_sizes, zorder=12)
                handles.append((h1, "Pollution source"))
            if at_risk_x:
                h2 = ax.scatter(at_risk_x, at_risk_y, marker="^", color="blue", s=10, zorder=8)
                handles.append((h2, "At-risk zone"))
            if handles:
                hs, labels = zip(*handles)
                ax.legend(hs, labels, loc="upper right")

    ax.set_xlim(source_lon - zoom_radius, source_lon + zoom_radius)
    ax.set_ylim(source_lat - zoom_radius, source_lat + zoom_radius)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="Pollution (log10)" if log_scale else "Pollution")

    def update(frame):
        pollution_map = pollution_snapshots[frame]
        edge_vals = np.array([pollution_map.get(v, 0.0) for u, v in edges])
        if log_scale:
            edge_vals = np.log10(0.01 + edge_vals)
        lc.set_array(edge_vals)

        node_vals = np.array([pollution_map.get(n, 0.0) for n in node_list])
        if log_scale:
            node_vals = np.log10(0.01 + node_vals)
        sc.set_array(node_vals)

        ax.set_title(f"Zoomed Step {frame + 1}/{len(pollution_snapshots)}")
        return lc, sc

    anim = FuncAnimation(fig, update, frames=len(pollution_snapshots), interval=interval, blit=False)

    if save_path:
        writer = PillowWriter(fps=1000 // interval if interval else 5)
        anim.save(save_path, writer=writer)
        print(f"[DEBUG] Zoomed animation saved to {save_path}")

    plt.show()
    return anim
