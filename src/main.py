# src/main.py
import os
import random
import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # ensures plots pop up in scripts

from osm_loader import build_river_network_from_osm, load_osm_features
from simulation import simulate_pollution_downstream, simulate_pollution_animation
from visualization import plot_rivers_map, animate_pollution_zoomed
import matplotlib.pyplot as plt


def pick_random_poi_sources(poi_sources, n_sources=3):
    """Randomly pick n_sources from the list of POI-based source nodes."""
    if len(poi_sources) <= n_sources:
        return poi_sources
    return random.sample(poi_sources, n_sources)


def main():
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SRC_DIR)
    OSM_PATH = os.path.join(PROJECT_ROOT, "data", "jiangsu.osm.pbf")
    
    print("Loading river network from local OSM PBF file…")
    rn, node_coords = build_river_network_from_osm(OSM_PATH)
    print(f"River network loaded! {len(node_coords)} nodes")

    print("Graph nodes:", len(rn.graph.nodes))
    print("Graph edges:", len(rn.graph.edges))
    if rn.graph.edges:
        print("Example edges:", list(rn.graph.edges())[:5])
    if node_coords:
        print("Example node coords:", list(node_coords.items())[:5])
    
    # --- Load boundaries and POIs ---
    print("Loading boundaries and POIs…")
    boundaries, pois = load_osm_features(OSM_PATH)
    pois = [poi for poi in pois if "category" in poi and not (np.isnan(poi["lat"]) or np.isnan(poi["lon"]))]
    print(f"Filtered POIs for simulation: {len(pois)}")
    
    # --- Map POIs to nearest river nodes and assign random intensities ---
    print("[DEBUG] Mapping POIs to nearest river nodes...")
    source_nodes = []

    for i, poi in enumerate(pois, start=1):
        if poi.get("category") != "pollution_source":
            continue

        lat, lon = poi["lat"], poi["lon"]
        nearest_node = min(
            node_coords,
            key=lambda n: (node_coords[n][0] - lat)**2 + (node_coords[n][1] - lon)**2
        )
        intensity = random.uniform(0.5, 1.0)
        source_nodes.append((nearest_node, intensity))

        if i % 50 == 0 or i == len(pois):
            print(f"[DEBUG] Processed {i}/{len(pois)} POIs, current sources: {len(source_nodes)}")

    if not source_nodes:
        print("[DEBUG] No POIs mapped to river nodes. Picking 3 random nodes as sources...")
        fallback_nodes = random.sample(list(node_coords.keys()), min(3, len(node_coords)))
        for n in fallback_nodes:
            source_nodes.append((n, random.uniform(0.5, 1.0)))

    print(f"[DEBUG] Total source nodes based on POIs: {len(source_nodes)}")
    print(f"[DEBUG] Example source nodes: {source_nodes[:5]}")
    
    # --- Simulate full downstream pollution (for static map) ---
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
    
    # --- Plot static river network with pollution overlay and POIs ---
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
    
    # --- Generate multiple zoomed animations from random POI sources ---
    NUM_ANIMATIONS = 20  # change this for more/less animations
    for i in range(NUM_ANIMATIONS):
        random_sources = pick_random_poi_sources(source_nodes, n_sources=3)
        print(f"[DEBUG] Animation {i+1}: selected POI sources = {random_sources}")
        
        pollution_snapshots = simulate_pollution_animation(
            rn,
            source_nodes=random_sources,
            decay_factor=0.9,
            retention=0.2
        )
        
        if pollution_snapshots and pollution_snapshots[0]:
            zoom_node = max(pollution_snapshots[0], key=pollution_snapshots[0].get)
            save_path = os.path.join(PROJECT_ROOT, f"output/zoomed_pollution_random_{i+1}.gif")
            animate_pollution_zoomed(
                rn,
                coords=node_coords,
                pollution_snapshots=pollution_snapshots,
                source_node=zoom_node,
                pois=pois,
                log_scale=False,
                save_path=save_path
            )

    print("Simulation complete!")


if __name__ == "__main__":
    main()
