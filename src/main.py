# src/main.py
import os
import matplotlib
matplotlib.use("TkAgg")  # ensures plots pop up in scripts

from osm_loader import build_river_network_from_osm
from simulation import simulate_pollution_single_pulse, pick_upstream_source
from visualization import plot_rivers_map
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
    
    # --- Pick upstream source ---
    source_node = pick_upstream_source(rn)
    print("Source node selected:", source_node)
    
    # --- Simulate pollution ---
    concentration_map = simulate_pollution_single_pulse(rn, source_node, decay_factor=0.9, min_threshold=0.01)
    print("Pollution simulation complete!")
    print("Min pollution:", min(concentration_map.values()))
    print("Max pollution:", max(concentration_map.values()))
    
    # --- Plot ---
    try:
        plot_rivers_map(
            rn,
            node_coords,
            pollution_map=concentration_map,
            source_node=source_node,
            log_scale=True,
            arrow_every=200  # reduce number of arrows for large network
        )
        print("River network with pollution overlay plotted!")
    except Exception as e:
        print("Warning: Could not plot river network:", e)
    
    print("Simulation complete!")

if __name__ == "__main__":
    main()
