# src/osm_loader.py

from pyrosm import OSM
import networkx as nx

# ---------------------------------------------------------
# CONSTANTS: POI Classification
# ---------------------------------------------------------

POLLUTION_AMENITIES = {
    "industrial", "wastewater_plant", "waste_disposal",
    "recycling", "chemical", "factory", "landfill"
}

AT_RISK_AMENITIES = {
    "school", "kindergarten", "college", "university",
    "hospital", "clinic", "social_facility",
    "nursing_home", "childcare"
}

# ---------------------------------------------------------
# DATA STRUCTURES
# ---------------------------------------------------------

class RiverNetwork:
    def __init__(self, graph):
        self.graph = graph  # nx.DiGraph

# ---------------------------------------------------------
# POIS
# ---------------------------------------------------------
def load_osm_features(osm_path):
    print("[1/6] Initializing OSM loader…")
    osm = OSM(osm_path)
    
    # ----------------------------------------
    # Administrative boundaries
    # ----------------------------------------
    print("[2/6] Loading administrative boundaries…")
    boundaries_gdf = osm.get_boundaries()
    print("[3/6] Filtering boundaries by admin_level=4…")
    boundaries_gdf = boundaries_gdf[boundaries_gdf['admin_level'] == '4']
    
    boundaries = []
    print(f"    Found {len(boundaries_gdf)} boundaries. Processing geometry…")
    for geom in boundaries_gdf.geometry:
        if geom.geom_type == "Polygon":
            boundaries.append([(y, x) for x, y in geom.exterior.coords])
        elif geom.geom_type == "MultiPolygon":
            for part in geom.geoms:
                boundaries.append([(y, x) for x, y in part.exterior.coords])

    # ----------------------------------------
    # POIs
    # ----------------------------------------
    print("[4/6] Loading POIs (pollution and at-risk)…")
    try:
        pois_gdf = osm.get_pois()  # load all POIs for robustness
    except Exception as e:
        print(f"Warning: Could not load POIs from OSM: {e}")
        pois_gdf = []

    pois = []
    if len(pois_gdf) > 0:
        print(f"[5/6] Processing {len(pois_gdf)} POIs…")
        for i, row in enumerate(pois_gdf.itertuples(), start=1):
            if i % 500 == 0:
                print(f"    Processed {i}/{len(pois_gdf)} POIs…")
            geom = row.geometry
            if geom.geom_type == "Point":
                lat, lon = geom.y, geom.x
            else:
                c = geom.centroid
                lat, lon = c.y, c.x

            poi_type = getattr(row, "amenity", "poi")
            if poi_type in POLLUTION_AMENITIES:
                category = "pollution_source"
            elif poi_type in AT_RISK_AMENITIES:
                category = "at_risk"
            else:
                continue

            pois.append({"lat": lat, "lon": lon, "type": poi_type, "category": category})

    # Fallback: create some test POIs if none loaded
    if not pois:
        print("[DEBUG] No POIs loaded from OSM. Creating test POIs...")
        pois = [
            {"lat": 32.0, "lon": 119.0, "type": "factory", "category": "pollution_source"},
            {"lat": 32.2, "lon": 119.5, "type": "school", "category": "at_risk"},
            {"lat": 32.1, "lon": 119.2, "type": "wastewater_plant", "category": "pollution_source"},
        ]

    print(f"[6/6] POIs loaded: {len(pois)}")
    print(f"    Pollution sources: {len([p for p in pois if p['category']=='pollution_source'])}")
    print(f"    At-risk zones: {len([p for p in pois if p['category']=='at_risk'])}")

    return boundaries, pois


# ---------------------------------------------------------
# BUILD RIVER NETWORK
# ---------------------------------------------------------

def build_river_network_from_osm(osm_file_path):
    """
    Build a river network from a PBF file using Pyrosm.

    Returns:
      RiverNetwork object
      node_coords: dict {node_id: (lat, lon)}
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
    coord_to_id = {}
    node_id_counter = 0

    print(f"Processing {len(waterways)} waterways...")

    for idx, row in waterways.iterrows():
        geom = row["geometry"]

        # Normalize geometry types
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = geom.geoms
        else:
            continue

        # Build graph edges
        for line in lines:
            coords_list = list(line.coords)
            for i in range(len(coords_list)-1):

                start = coords_list[i]
                end = coords_list[i+1]

                # Add unique coordinate nodes
                if start not in coord_to_id:
                    coord_to_id[start] = node_id_counter
                    node_coords[node_id_counter] = (start[1], start[0])  # lat, lon
                    node_id_counter += 1

                if end not in coord_to_id:
                    coord_to_id[end] = node_id_counter
                    node_coords[node_id_counter] = (end[1], end[0])  # lat, lon
                    node_id_counter += 1

                u = coord_to_id[start]
                v = coord_to_id[end]
                G.add_edge(u, v)

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx + 1}/{len(waterways)} waterways...")

    print("River network built.")
    print(f"Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")

    return RiverNetwork(G), node_coords
