import pandas as pd

def build_graph(edge_file, jenis_bencana, avoid_danger=False):
    edges = pd.read_csv(edge_file)
    graph = {}

    risk_penalty = {
        "Banjir": 20,
        "Gempa": 10,
        "Tsunami": 30
    }

    for _, row in edges.iterrows():
        source = row['source']
        target = row['target']
        weight = row['weight']

        if row['status'] == "Bahaya":
            weight += risk_penalty.get(jenis_bencana, 0)
            weight += 15
            if avoid_danger:
                weight += 1000

        if source not in graph:
            graph[source] = []

        graph[source].append((target, weight))

    return graph