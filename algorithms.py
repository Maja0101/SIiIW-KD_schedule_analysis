import heapq
from graph import Graph, Node, Edge
from datetime import datetime, timedelta, date
from sys import maxsize
from geopy.distance import geodesic

TRANSFER_TIME = timedelta(minutes=5)
AVG_TRAVEL_TIME = 86.08

class PriorityQueue:
    def __init__(self):
        self.items = []

    def push(self, item, priority):
        heapq.heappush(self.items, (priority, item))

    def pop(self):
        return heapq.heappop(self.items)
    
    def is_empty(self):
        return not self.items

def runs_on_this_day(date, edge):
    exc = edge.exceptions.get(date)
    if exc is not None:
        if exc == 1:
            return True
        elif exc == 2:
            return False
    return edge.weekdays[date.weekday()]

def cost_by_time(current_datetime, current_route, edge):
    print("cost by time")
    if current_datetime > edge.start_date and current_datetime < edge.end_date:
        print("between dates")
        if runs_on_this_day(current_datetime.date(), edge):
            print("runs on this day")
            curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)
            print("curr td ", curr_td)
            print("departure time ", edge.departure_time)
            print("valid ", curr_td <= edge.departure_time)

            if current_route is None and curr_td <= edge.departure_time:
                print("first")
                print("ok")
                print("cost: ", edge.arrival_time - edge.departure_time)
                return edge.arrival_time - edge.departure_time, 0

            if edge.route_name == current_route and curr_td <= edge.departure_time:
                print("without transfer")
                print("ok")
                print("cost: ", edge.arrival_time - curr_td)
                return edge.arrival_time - curr_td, 0
            
            if curr_td + TRANSFER_TIME <= edge.departure_time:
                print("with transfer")
                print("ok")
                print("cost: ", edge.arrival_time - curr_td)
                return edge.arrival_time - curr_td, 1
        
    print("not ok")   
    return timedelta.max, maxsize
    

def dijkstra_algorithm(graph, starting_point, starting_datetime):
    pq = PriorityQueue()

    time_cost = {key: timedelta.max for key in graph.nodes.keys()}
    transfer_cost = {key: maxsize for key in graph.nodes.keys()}
    previous_stop = {key: -1 for key in graph.nodes.keys()}
    time_at_stop = {key: None for key in graph.nodes.keys()}
    route_at_stop = {key: None for key in graph.nodes.keys()}

    time_cost[starting_point] = timedelta(0)
    transfer_cost[starting_point] = 0

    time_at_stop[starting_point] = starting_datetime

    pq.push(starting_point, timedelta(0))

    print("start")
    print("time cost: ", time_cost)
    print("transfer cost: ", transfer_cost)
    print("previous_stop: ", previous_stop)
    print("time_at_stop: ", time_at_stop)
    print("route_at_stop: ", route_at_stop)

    i = 0
    while not pq.is_empty():
        print("i = ", i)

        d, u = pq.pop()

        if d > time_cost[u]:
            continue

        j = 0
        for v, e in graph.adj[u]:
            print("j = ", j)
            print("u: ", u, " v: ", v, " e: ", f"{e.departure_time}-{e.arrival_time} ({e.route_name})")

            cost_u_v, transfer = cost_by_time(time_at_stop[u], route_at_stop[u], e)
            if cost_u_v < timedelta.max and time_cost[v] > time_cost[u] + cost_u_v:
                time_cost[v] = time_cost[u] + cost_u_v
                transfer_cost[v] = transfer_cost[u] + transfer
                previous_stop[v] = u
                if route_at_stop[u] is None:
                    time_at_stop[u] = datetime(time_at_stop[u].year, time_at_stop[u].month, time_at_stop[u].day) + e.departure_time
                time_at_stop[v] = time_at_stop[u] + cost_u_v
                route_at_stop[v] = e.route_name if transfer == 1 or route_at_stop[u] is None else route_at_stop[u]
                pq.push(v, time_cost[v])

            print("time cost: ", time_cost)
            print("transfer cost: ", transfer_cost)
            print("previous_stop: ", previous_stop)
            print("time_at_stop: ", time_at_stop)
            print("route_at_stop: ", route_at_stop)

            j += 1

        i += 1

    return time_cost, transfer_cost, previous_stop, time_at_stop, route_at_stop

def heuristics(first_stop, second_stop):
    return timedelta(seconds=int(geodesic(first_stop.coordinates, second_stop.coordinates).km / AVG_TRAVEL_TIME * 3600)) 

if __name__ == '__main__':
    graph = Graph()

    graph.add_node(0, Node('A', None, None))
    graph.add_node(1, Node('B', None, None))
    graph.add_node(2, Node('C', None, None))
    graph.add_node(3, Node('D', None, None))
    graph.add_node(4, Node('E', None, None))
    graph.add_node(5, Node('F', None, None))

    graph.add_edge(0, 1, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=13), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(0, 4, Edge(timedelta(0, hours=10, minutes=16), timedelta(0, hours=10, minutes=19), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, False, True], {date(2026, 3, 14): 1}))
    graph.add_edge(1, 2, Edge(timedelta(0, hours=10, minutes=13), timedelta(0, hours=10, minutes=14), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(2, 3, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=11), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=14), timedelta(0, hours=10, minutes=15), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(3, 1, Edge(timedelta(0, hours=10, minutes=35), timedelta(0, hours=10, minutes=36), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(4, 5, Edge(timedelta(0, hours=10, minutes=20), timedelta(0, hours=10, minutes=21), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 1, Edge(timedelta(0, hours=10, minutes=15), timedelta(0, hours=10, minutes=21), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=30), timedelta(0, hours=10, minutes=35), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))

    c, tc, ps, tas, rat = dijkstra_algorithm(graph, 0, datetime(2026, 3, 14, 10, 10, 00))

    print("end")
    print("time cost: ", c)
    print("transfer cost: ", tc)
    print("previous_stop: ", ps)
    print("time_at_stop: ", tas)
    print("route_at_stop: ", rat)

