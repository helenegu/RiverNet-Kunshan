import osmnx as ox
from shapely.geometry import LineString, MultiLineString, Point
from .river_network import RiverNetwork


def build_river_network_from_osm(place_name, flow_speed=0.8, min_segment_length=50.0):
    tags = {"waterway": ["river", "stream", "canal"]}
    gdf = ox.geometries_from_place(place_name, tags=tags)

    rivers = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]
    rivers_proj = ox.project_gdf(rivers)

    rn = RiverNetwork()
    node_index = {}
    node_coords = {}

    def get_node_id(x, y):
        key = (round(x, 2), round(y, 2))
        if key not in node_index:
            node_id = f"N{len(node_index)}"
            node_index[key] = node_id
            node_coords[node_id] = key
        return node_index[key]

    for geom in rivers_proj.geometry:
        if isinstance(geom, LineString):
            coords = list(geom.coords)
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                p1, p2 = Point(x1, y1), Point(x2, y2)
                length = p1.distance(p2)
                if length < min_segment_length:
                    continue
                u = get_node_id(x1, y1)
                v = get_node_id(x2, y2)
                travel_time = length / flow_speed
                decay_factor = 0.99
                rn.add_edge(u, v, travel_time, decay_factor)

        elif isinstance(geom, MultiLineString):
            for ls in geom.geoms:
                coords = list(ls.coords)
                for i in range(len(coords) - 1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i + 1]
                    p1, p2 = Point(x1, y1), Point(x2, y2)
                    length = p1.distance(p2)
                    if length < min_segment_length:
                        continue
                    u = get_node_id(x1, y1)
                    v = get_node_id(x2, y2)
                    travel_time = length / flow_speed
                    decay_factor = 0.99
                    rn.add_edge(u, v, travel_time, decay_factor)

    return rn, node_coords
