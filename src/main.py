# src/main.py
import os
import random
import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # ensures plots pop up in scripts

from osm_loader import build_river_network_from_osm, load_osm_features
from simulation import simulate_pollution_downstream, simulate_pollution_animation
from visualization import plot_rivers_map, animate_pollution, animate_pollution_zoomed
import matplotlib.pyplot as plt


def main():
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SRC_DIR)
    OSM_PATH = os.path.join(PROJECT_ROOT, "data", "jiangsu.osm.pbf")
    
    print("Loading river network from local OSM PBF file…")
    rn, node_coords = build_river_network_from_osm(OSM_PATH)
    print("River network loaded!", len(node_coords), "nodes")
    
    # --- Debug info ---
    print("Graph nodes:", len(rn.graph.nodes))
    print("Graph edges:", len(rn.graph.edges))
    if rn.graph.edges:
        print("Example edges:", list(rn.graph.edges())[:5])
    if node_coords:
        print("Example node coords:", list(node_coords.items())[:5])
    
    # --- Load boundaries and POIs ---
    print("Loading boundaries and POIs…")
    boundaries, pois = load_osm_features(OSM_PATH)

    # Filter out POIs without a category or with NaN coordinates
    pois = [poi for poi in pois if "category" in poi and not (np.isnan(poi["lat"]) or np.isnan(poi["lon"]))]
    print(f"Filtered POIs for simulation: {len(pois)}")
    
    # --- Map POIs to nearest river nodes and assign random intensities ---
    print("[DEBUG] Mapping POIs to nearest river nodes...")
    source_nodes = []

    for i, poi in enumerate(pois, start=1):
        # Only consider pollution sources
        if poi.get("category") != "pollution_source":
            continue

        lat, lon = poi.get("lat"), poi.get("lon")
        if lat is None or lon is None or np.isnan(lat) or np.isnan(lon):
            continue

        # Find nearest river node
        nearest_node = min(
            node_coords,
            key=lambda n: (node_coords[n][0] - lat)**2 + (node_coords[n][1] - lon)**2
        )

        # Assign random initial intensity
        intensity = random.uniform(0.5, 1.0)
        source_nodes.append((nearest_node, intensity))

        # Debug progress every 50 POIs
        if i % 50 == 0 or i == len(pois):
            print(f"[DEBUG] Processed {i}/{len(pois)} POIs, current sources: {len(source_nodes)}")

    if not source_nodes:
        # Fallback: pick some random nodes if none mapped
        print("[DEBUG] No POIs mapped to river nodes. Picking 3 random nodes as sources...")
        fallback_nodes = random.sample(list(node_coords.keys()), min(3, len(node_coords)))
        for n in fallback_nodes:
            source_nodes.append((n, random.uniform(0.5, 1.0)))

    print(f"[DEBUG] Total source nodes based on POIs: {len(source_nodes)}")
    print(f"[DEBUG] Example source nodes: {source_nodes[:5]}")
    
    # --- Simulate pollution ---
    print("Simulating pollution downstream from POI sources…")
    concentration_map = simulate_pollution_downstream(
        rn,
        source_nodes,
        decay_factor=0.9,
        min_threshold=0.01
    )
    print("Pollution simulation complete!")
    print("Min pollution:", min(concentration_map.values()))
    print("Max pollution:", max(concentration_map.values()))
    
    # --- Plot river network with pollution overlay and POIs ---
    try:
        plot_rivers_map(
            rn,
            node_coords,
            pollution_map=concentration_map,
            arrow_every=200,
            boundaries=boundaries,
            pois=pois
        )
        print("River network with pollution overlay plotted!")
    except Exception as e:
        print("Warning: Could not plot river network:", e)
    
    '''
    # --- Simulate pollution animation ---
    print("Generating pollution animation…")
    pollution_snapshots = simulate_pollution_animation(
        rn,
        source_nodes=source_nodes,  # pass POI-based sources here!
        decay_factor=0.9,
        retention=0.2
    )
    
    save_gif_path = os.path.join(PROJECT_ROOT, "output", "jiangsu_pollution.gif")
    animate_pollution(
        rn,
        node_coords,
        pollution_snapshots,
        pois=pois,  # keeps POIs symbols in animation
        log_scale=False,
        save_path=save_gif_path
    )
    '''

    # -----------------------------
    # Animation: Zoomed on first-step most polluted node
    # -----------------------------
    # Ensure we have pollution snapshots
    pollution_snapshots = simulate_pollution_animation(
        rn,
        source_nodes=source_nodes,  # pass POI-based sources here!
        decay_factor=0.9,
        retention=0.2
    )

    if pollution_snapshots:
        first_step_pollution = pollution_snapshots[0]
        if first_step_pollution:
            # Pick the most polluted node in the first step
            zoom_node = max(first_step_pollution, key=first_step_pollution.get)
            print(f"[DEBUG] Zooming on first-step most polluted node: {zoom_node}, pollution: {first_step_pollution[zoom_node]:.3f}")

            animate_pollution_zoomed(
            rn,
            coords=node_coords,
            pollution_snapshots=pollution_snapshots,
            source_node=zoom_node,  # match the function signature
            pois=pois,
            log_scale=False,
            save_path="zoomed_pollution.gif"
            )
        else:
            print("[DEBUG] No pollution data in first step to animate.")
    else:
        print("[DEBUG] No pollution snapshots generated.")


    print("Simulation complete!")


if __name__ == "__main__":
    main()
