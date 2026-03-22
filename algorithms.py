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
        if exc == 1:
            return True
        elif exc == 2:
            return False
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

        if graph.adj.get(u) is not None:
            for v in graph.adj[u]:
                for e in graph.adj[u][v]:

                    time_u_v, transfer_u_v = calc_cost(
                        previous_route_part[u]['arrival_time'], 
                        previous_route_part[u]['route'], 
                        e)

                    if time_u_v < timedelta.max:

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

    return cost, previous_route_part

def heuristics_distance(first_stop, second_stop):
    return geodesic(first_stop.coordinates, second_stop.coordinates).km

def heuristics(first_stop, second_stop):
    return timedelta(seconds=int(heuristics_distance(first_stop, second_stop) / AVG_TRAVEL_TIME * 3600)) 

@timer
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

        if u == ending_point:
            return cost, previous_route_part

        closed_v.add(u)

        for v in graph.adj[u]:

            if v in closed_v:
                continue

            ep = False

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