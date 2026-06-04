import heapq

def dijkstra(graph, start, end):
    """Dijkstra yang juga mengembalikan langkah perhitungan.

    Returns:
        total_cost (float), path (list), steps (list of dict)
    steps: list of snapshots with keys: 'popped', 'cost', 'path', 'pushed' (list)
    """
    queue = [(0, start, [])]
    visited = set()
    steps = []

    while queue:
        (cost, node, path) = heapq.heappop(queue)

        if node in visited:
            continue

        # record popped node snapshot
        snapshot = {
            'popped': node,
            'cost': cost,
            'path': path + [node],
            'pushed': []
        }

        visited.add(node)
        path = path + [node]

        if node == end:
            steps.append(snapshot)
            return cost, path, steps

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                new_cost = cost + weight
                heapq.heappush(queue, (new_cost, neighbor, path))
                snapshot['pushed'].append((neighbor, new_cost))

        steps.append(snapshot)

    return float("inf"), [], steps