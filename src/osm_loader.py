# src/osm_loader.py
from pyrosm import OSM
import networkx as nx

class RiverNetwork:
    def __init__(self, graph):
        self.graph = graph  # nx.DiGraph

def build_river_network_from_osm(osm_file_path):
    """
    Build a river network from a PBF file using Pyrosm.
    Returns:
      RiverNetwork object
      dict of node coordinates {node_id: (lat, lon)}
    """
    print(f"Reading OSM PBF file: {osm_file_path}")
    
    osm = OSM(osm_file_path)

    waterways = osm.get_data_by_custom_criteria(
        custom_filter={"waterway": True},
        filter_type="keep"
    )

    if waterways.empty:
        raise ValueError("No waterways found in OSM data.")

    G = nx.DiGraph()
    node_coords = {}
    node_id_counter = 0
    coord_to_id = {}

    print(f"Processing {len(waterways)} waterways...")
    for idx, row in waterways.iterrows():
        geom = row["geometry"]
        lines = []
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = geom.geoms
        else:
            continue

        for line in lines:
            coords_list = list(line.coords)
            for i in range(len(coords_list)-1):
                start, end = coords_list[i], coords_list[i+1]

                if start not in coord_to_id:
                    coord_to_id[start] = node_id_counter
                    node_coords[node_id_counter] = start
                    node_id_counter += 1
                if end not in coord_to_id:
                    coord_to_id[end] = node_id_counter
                    node_coords[node_id_counter] = end
                    node_id_counter += 1

                u = coord_to_id[start]
                v = coord_to_id[end]
                G.add_edge(u, v)

        # --- Progress printing every 100 waterways ---
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(waterways)} waterways...")

    print("Building node coordinate map complete.")
    print(f"River network built: {len(G.nodes)} nodes, {len(G.edges)} edges.")
    return RiverNetwork(G), node_coords
