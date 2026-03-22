import heapq
from graph import Graph, Node, Edge
from datetime import datetime, timedelta, date
from sys import maxsize
from geopy.distance import geodesic
from timer import timer
from bisect import bisect_left
import city_definition as city

TRANSFER_TIME = timedelta(minutes=5)
AVG_TRAVEL_TIME = 86.08
TRANSFER_PENALTY = timedelta(hours=12)

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
        # print("not none")
        # print(exc)
        if exc == 1:
            # print("exc 1")
            return True
        elif exc == 2:
            # print("exc 2")
            return False
    # print("none")
    # print(edge.weekdays, date.weekday())
    # print(edge.weekdays[date.weekday()])
    # print("end runs on this day")
    return edge.weekdays[date.weekday()]

def calc_cost(current_datetime, current_route, edge, ep=False):
    if current_datetime > edge.start_date and current_datetime < edge.end_date:
        # if ep: print("between dates")
        # if ep: print(f"{edge.weekdays} - {edge.exceptions.get(current_datetime.date())}")

        if runs_on_this_day(current_datetime.date(), edge):
            if ep: print(f"{current_datetime}: {edge.start_date} - {edge.end_date} ({current_route})")

            curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)
            if ep: print(curr_td)

            if current_route is None and curr_td <= edge.departure_time:
                if ep: print("first")
                # return edge.arrival_time - edge.departure_time, 0
                return edge.arrival_time - curr_td, 0

            if edge.route_name == current_route and curr_td <= edge.departure_time:
                if ep: print("no transfer")
                return edge.arrival_time - curr_td, 0
            
            if curr_td + TRANSFER_TIME <= edge.departure_time:
                if ep: print("transfer")
                return edge.arrival_time - curr_td, 1
        
    return timedelta.max, maxsize
    
@timer
def dijkstra_algorithm(graph, starting_point, starting_datetime):
    pq = PriorityQueue()

    cost = {key: {'time': timedelta.max, 'transfers': maxsize} for key in graph.nodes.keys()}

    previous_route_part = {key: {'stop': -1, 'route': None, 'departure_time': None, 'arrival_time': None}  for key in graph.nodes.keys()} 

    cost[starting_point]['time'] = timedelta(0)
    cost[starting_point]['transfers'] = 0

    previous_route_part[starting_point]['arrival_time'] = starting_datetime

    pq.push(starting_point, timedelta(0))

    while not pq.is_empty():

        d, u = pq.pop()
        # print("---> u: ", graph.nodes[u].name)

        if graph.adj.get(u) is not None:
            for v in graph.adj[u]:
                for e in graph.adj[u][v]:

                    time_u_v, transfer_u_v = calc_cost(
                        previous_route_part[u]['arrival_time'], 
                        previous_route_part[u]['route'], 
                        e)

                    if time_u_v < timedelta.max:
                        # print("v: ", graph.nodes[v].name, "t_u_v: ", time_u_v, "e: ", e.departure_time, e.arrival_time)

                        if u == starting_point:
                            temp_new_arrival_time = datetime(previous_route_part[u]['arrival_time'].year, previous_route_part[u]['arrival_time'].month, previous_route_part[u]['arrival_time'].day) + e.arrival_time
                        else:
                            temp_new_arrival_time = previous_route_part[u]['arrival_time'] + time_u_v

                        is_equal_and_earlier_than_best_known_part = (cost[v]['time'] == cost[u]['time'] + time_u_v) and (temp_new_arrival_time < previous_route_part[v]['arrival_time'])

                        if (cost[v]['time'] > cost[u]['time'] + time_u_v or is_equal_and_earlier_than_best_known_part):
                            
                            cost[v]['time'] = cost[u]['time'] + time_u_v
                            cost[v]['transfers'] = cost[u]['transfers'] + transfer_u_v
                            previous_route_part[v]['stop'] = u

                            previous_route_part[v]['arrival_time'] = temp_new_arrival_time
                            previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - (e.arrival_time - e.departure_time)

                            previous_route_part[v]['route'] = e.route_name
                            
                            pq.push(v, cost[v]['time'])
                            # print("+v: ", graph.nodes[v].name, "v: ", v, "c: ", time_u_v)

    return cost, previous_route_part

def heuristics_distance(first_stop, second_stop):
    return geodesic(first_stop.coordinates, second_stop.coordinates).km

def heuristics(first_stop, second_stop):
    return timedelta(seconds=int(heuristics_distance(first_stop, second_stop) / AVG_TRAVEL_TIME * 3600)) 
    # return timedelta(seconds=int(geodesic(first_stop.coordinates, second_stop.coordinates).km / AVG_TRAVEL_TIME * 3600)) 

@timer
def a_star_algorithm_old(graph, starting_point, ending_point, starting_datetime, optimize_by_time=True, starting_route=None):
    open_v = PriorityQueue()
    closed_v = set()

    cost = {key: {'time': timedelta.max, 'transfers': maxsize} for key in graph.nodes.keys()}

    previous_route_part = {key: {'stop': -1, 'route': None, 'departure_time': None, 'arrival_time': None}  for key in graph.nodes.keys()} 

    cost[starting_point]['time'] = timedelta(0)
    cost[starting_point]['transfers'] = 0

    previous_route_part[starting_point]['arrival_time'] = starting_datetime
    previous_route_part[starting_point]['route'] = starting_route

    open_v.push(starting_point, timedelta(0))

    while not open_v.is_empty():

        d, u = open_v.pop()

        if u == ending_point:
            return cost, previous_route_part

        closed_v.add(u)

        for v in graph.adj[u]:
            if v in closed_v:
                continue

            edges = graph.adj[u][v]

            arrival_to_u = previous_route_part[u]['arrival_time']

            for e in edges:
                time_u_v, transfer_u_v = calc_cost(
                    arrival_to_u, 
                    previous_route_part[u]['route'], 
                    e)
            
                is_not_infinite_cost = (optimize_by_time and time_u_v < timedelta.max) or (not optimize_by_time and transfer_u_v < maxsize)

                if is_not_infinite_cost:

                    if u == starting_point:
                        temp_new_arrival_time = datetime(arrival_to_u.year, arrival_to_u.month, arrival_to_u.day) + e.arrival_time
                    else:
                        temp_new_arrival_time = arrival_to_u + time_u_v

                    is_better_cost = (optimize_by_time and cost[v]['time'] > cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] > cost[u]['transfers'] + transfer_u_v)
                    is_equal_cost = (optimize_by_time and cost[v]['time'] == cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] == cost[u]['transfers'] + transfer_u_v)
                    is_equal_and_earlier_than_best_known_part = is_equal_cost and (temp_new_arrival_time < previous_route_part[v]['arrival_time'])

                    if (is_better_cost or is_equal_and_earlier_than_best_known_part):
                        
                        cost[v]['time'] = cost[u]['time'] + time_u_v
                        cost[v]['transfers'] = cost[u]['transfers'] + transfer_u_v
                        previous_route_part[v]['stop'] = u

                        previous_route_part[v]['arrival_time'] = temp_new_arrival_time
                        previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - (e.arrival_time - e.departure_time)

                        previous_route_part[v]['route'] = e.route_name

                        f = cost[v]['time'] + heuristics(graph.nodes[v], graph.nodes[ending_point])
                        if not optimize_by_time:
                            f += cost[v]['transfers'] * TRANSFER_PENALTY
                        
                        open_v.push(v, f)

    return cost, previous_route_part

# @timer
def a_star_algorithm(graph, starting_point, ending_point, starting_datetime, optimize_by_time=True, starting_route=None):
    open_v = PriorityQueue()
    closed_v = set()

    cost = {key: {'time': timedelta.max, 'transfers': maxsize} for key in graph.nodes.keys()}

    previous_route_part = {key: {'stop': -1, 'route': None, 'departure_time': None, 'arrival_time': None}  for key in graph.nodes.keys()} 

    cost[starting_point]['time'] = timedelta(0)
    cost[starting_point]['transfers'] = 0

    previous_route_part[starting_point]['arrival_time'] = starting_datetime
    previous_route_part[starting_point]['route'] = starting_route

    open_v.push(starting_point, timedelta(0))

    while not open_v.is_empty():

        d, u = open_v.pop()

        # print("---> nowe u ", graph.nodes[u].name)

        if u == ending_point:
            return cost, previous_route_part

        closed_v.add(u)

        for v in graph.adj[u]:
            # print("       v ", graph.nodes[v].name)

            if v in closed_v:
                # print("       closed ")
                continue

            # if (v == city.LEGNICA and u == city.KLODZKO) or (v == city.LEGNICA and u == city.WROCLAW) or (v == city.WROCLAW and u == city.KLODZKO): 
            #     ep = True
            #     # print("---> edge dla ", graph.nodes[u].name, " -> ", graph.nodes[v].name)
            # else:
            #     ep = False

            ep = False

            # print(graph.nodes[u].name, " -> ", graph.nodes[v].name, ep)

            edges = graph.adj[u][v]
            deps = graph.departures[u][v]

            arrival_to_u = previous_route_part[u]['arrival_time']
            arrival_to_u_td = timedelta(hours=arrival_to_u.hour, minutes=arrival_to_u.minute, seconds=arrival_to_u.second)

            idx = bisect_left(deps, arrival_to_u_td)

            for i in range(idx, len(edges)):
                e = edges[i]

                time_u_v, transfer_u_v = calc_cost(
                    arrival_to_u, 
                    previous_route_part[u]['route'], 
                    e, ep)

                is_not_infinite_cost = (optimize_by_time and time_u_v < timedelta.max) or (not optimize_by_time and transfer_u_v < maxsize)

                if is_not_infinite_cost:
                    if ep: print("calculated cost ", time_u_v, transfer_u_v)

                    if u == starting_point:
                        temp_new_arrival_time = datetime(arrival_to_u.year, arrival_to_u.month, arrival_to_u.day) + e.arrival_time
                    else:
                        temp_new_arrival_time = arrival_to_u + time_u_v

                    is_better_cost = (optimize_by_time and cost[v]['time'] > cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] > cost[u]['transfers'] + transfer_u_v)
                    is_equal_cost = (optimize_by_time and cost[v]['time'] == cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] == cost[u]['transfers'] + transfer_u_v)
                    is_equal_and_earlier_than_best_known_part = is_equal_cost and (temp_new_arrival_time < previous_route_part[v]['arrival_time'])

                    if ep: print("is_better_cost ", is_better_cost)
                    if ep: print("is_equal_and_earlier_than_best_known_part ", is_equal_and_earlier_than_best_known_part)

                    if (is_better_cost or is_equal_and_earlier_than_best_known_part):
                        
                        cost[v]['time'] = cost[u]['time'] + time_u_v
                        cost[v]['transfers'] = cost[u]['transfers'] + transfer_u_v
                        previous_route_part[v]['stop'] = u

                        previous_route_part[v]['arrival_time'] = temp_new_arrival_time
                        previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - (e.arrival_time - e.departure_time)

                        previous_route_part[v]['route'] = e.route_name

                        f = cost[v]['time'] + heuristics(graph.nodes[v], graph.nodes[ending_point])
                        if not optimize_by_time:
                            f += cost[v]['transfers'] * TRANSFER_PENALTY
                        
                        open_v.push(v, f)

    return cost, previous_route_part


if __name__ == '__main__':
    graph = Graph()

    graph.add_node(0, Node(0, 'A', 50, 15))
    graph.add_node(1, Node(1, 'B', 51, 16))
    graph.add_node(2, Node(2, 'C', 50, 16))
    graph.add_node(3, Node(3, 'D', 49, 16))
    graph.add_node(4, Node(4, 'E', 51, 17))
    graph.add_node(5, Node(5, 'F', 50, 17))
    graph.add_node(6, Node(6, 'G', 49, 17))
    graph.add_node(7, Node(7, 'H', 50, 18))

    graph.add_edge(0, 1, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=13), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(0, 4, Edge(timedelta(0, hours=10, minutes=16), timedelta(0, hours=10, minutes=19), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, False, True], {date(2026, 3, 14): 1}))
    graph.add_edge(1, 2, Edge(timedelta(0, hours=10, minutes=13), timedelta(0, hours=10, minutes=14), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(2, 3, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=11), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=14), timedelta(0, hours=10, minutes=15), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(3, 1, Edge(timedelta(0, hours=10, minutes=35), timedelta(0, hours=10, minutes=36), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(4, 5, Edge(timedelta(0, hours=10, minutes=20), timedelta(0, hours=10, minutes=21), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 0, Edge(timedelta(0, hours=10, minutes=15), timedelta(0, hours=10, minutes=21), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=30), timedelta(0, hours=10, minutes=35), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(3, 6, Edge(timedelta(0, hours=10, minutes=46), timedelta(0, hours=10, minutes=50), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))

    # graph.add_edge(0, 1, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=13), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(0, 4, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=31), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, False, True], {date(2026, 3, 14): 1}))
    # graph.add_edge(1, 2, Edge(timedelta(0, hours=10, minutes=18), timedelta(0, hours=10, minutes=20), 'e', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 3, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=11), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=26), timedelta(0, hours=10, minutes=36), 'f', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(3, 1, Edge(timedelta(0, hours=10, minutes=55), timedelta(0, hours=11, minutes=00), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(4, 5, Edge(timedelta(0, hours=10, minutes=32), timedelta(0, hours=10, minutes=36), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 0, Edge(timedelta(0, hours=10, minutes=45), timedelta(0, hours=10, minutes=50), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=41), timedelta(0, hours=10, minutes=45), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(3, 6, Edge(timedelta(0, hours=10, minutes=46), timedelta(0, hours=10, minutes=50), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=36), timedelta(0, hours=10, minutes=55), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(1, 0, Edge(timedelta(0, hours=11, minutes=10), timedelta(0, hours=11, minutes=20), 'g', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    
    
    # graph.add_edge(0, 1, Edge(timedelta(0, hours=10, minutes=00), timedelta(0, hours=10, minutes=10), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(0, 2, Edge(timedelta(0, hours=10, minutes=00), timedelta(0, hours=10, minutes=20), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(0, 3, Edge(timedelta(0, hours=10, minutes=00), timedelta(0, hours=10, minutes=30), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(1, 2, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=12, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 1, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=30), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 3, Edge(timedelta(0, hours=10, minutes=20), timedelta(0, hours=10, minutes=30), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(3, 2, Edge(timedelta(0, hours=10, minutes=30), timedelta(0, hours=10, minutes=40), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(1, 4, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=11, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=20), timedelta(0, hours=10, minutes=40), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=40), timedelta(0, hours=10, minutes=50), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(3, 6, Edge(timedelta(0, hours=10, minutes=30), timedelta(0, hours=10, minutes=35), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(4, 5, Edge(timedelta(0, hours=11, minutes=00), timedelta(0, hours=12, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 4, Edge(timedelta(0, hours=10, minutes=40), timedelta(0, hours=10, minutes=50), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 6, Edge(timedelta(0, hours=10, minutes=40), timedelta(0, hours=10, minutes=45), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(6, 5, Edge(timedelta(0, hours=10, minutes=35), timedelta(0, hours=10, minutes=40), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 7, Edge(timedelta(0, hours=10, minutes=50), timedelta(0, hours=11, minutes=10), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 7, Edge(timedelta(0, hours=10, minutes=40), timedelta(0, hours=11, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 7, Edge(timedelta(0, hours=12, minutes=00), timedelta(0, hours=13, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(7, 0, Edge(timedelta(0, hours=11, minutes=00), timedelta(0, hours=11, minutes=30), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(7, 0, Edge(timedelta(0, hours=11, minutes=10), timedelta(0, hours=12, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(7, 0, Edge(timedelta(0, hours=13, minutes=00), timedelta(0, hours=14, minutes=00), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))

    print(graph.adj)

    # cost, previous_route_part = dijkstra_algorithm(graph, 0, datetime(2026, 3, 14, 10, 10, 00))
    # cost, previous_route_part = a_star_algorithm(graph, 0, 5, datetime(2026, 3, 14, 10, 0, 00), True, None)

    # print("end")
    # print("cost: ", cost)
    # print("previous_route_part: ", previous_route_part)

    # user_route  = user_route(0, 5, (cost, previous_route_part))

    # display_user_route(graph, user_route)

    # solution, cost = tabu_search_tsp(graph, 0, [3, 2, 5, 7], datetime(2026, 3, 14, 10, 0, 00), True, 100)

    # print("end")
    # print(solution)
    # print(cost)