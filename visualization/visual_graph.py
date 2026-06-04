import networkx as nx
import matplotlib.pyplot as plt

def draw_graph(edges_df, best_path=None):
    G = nx.DiGraph()

    for _, row in edges_df.iterrows():
        G.add_edge(
            row['source'],
            row['target'],
            weight=row['weight']
        )

    pos = nx.spring_layout(G)

    edge_colors = []

    for edge in G.edges():
        if best_path:
            path_edges = list(zip(best_path, best_path[1:]))

            if edge in path_edges:
                edge_colors.append('blue')
            else:
                edge_colors.append('gray')
        else:
            edge_colors.append('gray')

    plt.figure(figsize=(8, 6))

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color='lightgreen',
        node_size=2000,
        font_size=10,
        edge_color=edge_colors,
        arrows=True
    )

    labels = nx.get_edge_attributes(G, 'weight')

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=labels
    )

    return plt