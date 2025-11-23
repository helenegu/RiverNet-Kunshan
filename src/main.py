# src/main.py
import os
from osm_loader import build_river_network_from_osm
from simulation import simulate_pollution, pick_upstream_source
from visualization import plot_concentration_map

def main():
    # --- Path setup ---
    SRC_DIR = os.path.dirname(os.path.abspath(__file__))       # .../src
    PROJECT_ROOT = os.path.dirname(SRC_DIR)                    # .../BK2
    OSM_PATH = os.path.join(PROJECT_ROOT, "data", "jiangsu.osm.pbf")
    
    print("Loading river network from local OSM PBF file…")
    print("Using OSM file at:", OSM_PATH)
    
    # --- Load river network ---
    rn, node_coords = build_river_network_from_osm(OSM_PATH)
    print("River network loaded!", len(node_coords), "nodes")
    
    # --- Example: simulate pollution ---
    source_node = pick_upstream_source(rn)  # pick an upstream source node
    concentration_map = simulate_pollution(rn, source_node)
    
    # --- Plot results ---
    plot_concentration_map(node_coords, concentration_map)
    print("Simulation complete!")

if __name__ == "__main__":
    main()
