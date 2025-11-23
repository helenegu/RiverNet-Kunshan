from .osm_loader import build_river_network_from_osm
from .simulation import simulate_pollution, pick_upstream_source
from .visualization import plot_concentration_map


def main():
    place = "Kunshan, Jiangsu, China"
    rn, node_coords = build_river_network_from_osm(place_name=place,
                                                   flow_speed=0.8,
                                                   min_segment_length=50.0)
    print(f"Number of nodes: {len(rn.nodes)}")

    source_node = pick_upstream_source(rn)
    print(f"Source node: {source_node}")

    sources = [
        {"node": source_node, "concentration": 100.0, "start_time": 0.0}
    ]

    arrival_time, concentration = simulate_pollution(rn, sources)

    C_SAFE = 20.0
    unsafe_nodes = [v for v in rn.nodes if concentration[v] > C_SAFE]
    print(f"Unsafe nodes (C > {C_SAFE}): {len(unsafe_nodes)}")

    plot_concentration_map(node_coords, concentration,
                           title=f"Simulated Pollution in {place}")


if __name__ == "__main__":
    main()
