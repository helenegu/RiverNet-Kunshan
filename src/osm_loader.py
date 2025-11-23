# src/osm_loader.py
from pyrosm import OSM
import networkx as nx

class RiverNetwork:
    def __init__(self, graph):
        self.graph = graph

def build_river_network_from_osm(osm_file_path):
    """
    Build a river network from a PBF file using Pyrosm.
    Returns a RiverNetwork object and a dict of node coordinates.
    """
    print(f"Reading OSM PBF file: {osm_file_path}")
    
    # Load OSM PBF
    osm = OSM(osm_file_path)

    # Extract waterways (rivers, streams, canals)
    waterways = osm.get_data_by_custom_criteria(
        custom_filter={"waterway": True},
        filter_type="keep"
    )

    if waterways.empty:
        raise ValueError("No waterways found in the OSM data.")

    # Build a directed graph using NetworkX
    G = nx.DiGraph()

    print(f"Processing {len(waterways)} waterway geometries...")
    for idx, row in waterways.iterrows():
        geom = row["geometry"]

        # Handle LineString and MultiLineString
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = geom.geoms
        else:
            continue  # skip other geometries

        for line in lines:
            coords = list(line.coords)
            for i in range(len(coords) - 1):
                start = coords[i]
                end = coords[i + 1]
                G.add_node(start, pos=start)
                G.add_node(end, pos=end)
                G.add_edge(start, end)

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(waterways)} waterways...")

    print("Building node coordinate map...")
    node_coords = {node: data["pos"] for node, data in G.nodes(data=True)}

    river_network = RiverNetwork(G)
    print(f"River network built: {len(G.nodes)} nodes, {len(G.edges)} edges.")
    return river_network, node_coords
