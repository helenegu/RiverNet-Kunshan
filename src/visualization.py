import matplotlib.pyplot as plt


def plot_concentration_map(node_coords, concentration, title="Pollution in Kunshan"):
    xs, ys, cs = [], [], []
    for node, (x, y) in node_coords.items():
        xs.append(x)
        ys.append(y)
        cs.append(concentration[node])

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(xs, ys, c=cs, s=10)
    plt.colorbar(sc, label="Concentration")
    plt.title(title)
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")
    plt.tight_layout()
    plt.show()
