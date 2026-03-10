class Node:
    def __init__(self, name, latitude, longitude):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"

class Edge:
    def __init__(self,departure_time, arrival_time, route_name, start_date, end_date, weekdays, exceptions):
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.travel_time = arrival_time - departure_time
        self.route_name = route_name
        self.start_date = start_date
        self.end_date = end_date
        self.weekdays = weekdays
        self.exceptions = exceptions

    def __str__(self):
        return f"{self.departure_time}-{self.arrival_time}, {self.route_name}, {self.start_date}-{self.end_date} ({self.weekdays})"

class Graph:
    def __init__(self):
        self.nodes = {}
        self.adj = {}

    def add_node(self, node_id, node):
        self.nodes[node_id] = node

    def add_edge(self, node_id, next_node_id, edge):
        if node_id not in self.adj:
            self.adj[node_id] = [(next_node_id, edge)]
        else:
            self.adj[node_id].append((next_node_id, edge))