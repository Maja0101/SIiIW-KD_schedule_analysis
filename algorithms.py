import heapq
from datetime import timedelta
from sys import maxsize
from geopy.distance import geodesic
from loggers import log_time, SUPRESS
from bisect import bisect_left

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

def calc_cost(current_datetime, current_route, edge):
    if current_datetime > edge.start_date and current_datetime < edge.end_date:

         if runs_on_this_day(current_datetime.date(), edge):
             
             curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)

             if (current_route is None or edge.route_name == current_route) and curr_td <= edge.departure_time:
                 return edge.arrival_time - curr_td, 0
             
             if curr_td + TRANSFER_TIME <= edge.departure_time:
                 return edge.arrival_time - curr_td, 1
             
    return timedelta.max, maxsize

def process_edge(graph, queue, u, v, e, arrival_to_u, previous_route_part, cost, optimize_by_time=True, ending_point=None, delta_u=timedelta(0)):
    time_u_v, transfer_u_v = calc_cost(arrival_to_u, previous_route_part[u]['route'], e)

    is_infinite_cost = time_u_v == timedelta.max

    if is_infinite_cost:
        return False
    
    temp_new_arrival_time = arrival_to_u + time_u_v

    time_u_v += delta_u

    new_time = cost[u]['time'] + time_u_v
    new_transfers = cost[u]['transfers'] + transfer_u_v

    is_better_cost = (optimize_by_time and cost[v]['time'] > new_time) or (not optimize_by_time and cost[v]['transfers'] > new_transfers)
    is_equal_cost_less_transfers = optimize_by_time and cost[v]['time'] == new_time and cost[v]['transfers'] > new_transfers
    is_equal_cost_less_time = not optimize_by_time and cost[v]['transfers'] == new_transfers and cost[v]['time'] > new_time

    if is_better_cost or is_equal_cost_less_transfers or is_equal_cost_less_time:
                        
        cost[v]['time'] = new_time
        cost[v]['transfers'] = new_transfers

        previous_route_part[v]['stop'] = u

        previous_route_part[v]['arrival_time'] = temp_new_arrival_time
        previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - e.travel_time

        previous_route_part[v]['route'] = e.route_name

        f = cost[v]['time']

        if ending_point is not None:
            f += heuristics(graph.nodes[v], graph.nodes[ending_point])

        if not optimize_by_time:
            f += cost[v]['transfers'] * TRANSFER_PENALTY
            
        queue.push(v, f)

    return True
    
@log_time(SUPRESS)
def dijkstra_algorithm(graph, starting_point, starting_datetime, optimize_by_time=True, **kwargs):
    log_is_allowed = kwargs.get("_log_if_allowed")
    if log_is_allowed:
        log_is_allowed("dijkstra_algorithm was executed wtih param %s", 'time' if optimize_by_time else 'transfers')

    pq = PriorityQueue()

    cost = {key: {'time': timedelta.max, 'transfers': maxsize} for key in graph.nodes.keys()}

    previous_route_part = {key: {'stop': -1, 'route': None, 'departure_time': None, 'arrival_time': None}  for key in graph.nodes.keys()} 

    cost[starting_point]['time'] = timedelta(0)
    cost[starting_point]['transfers'] = 0

    previous_route_part[starting_point]['arrival_time'] = starting_datetime

    pq.push(starting_point, timedelta(0))

    while not pq.is_empty():

        d, u = pq.pop()

        for v in graph.adj[u]:

            edges = graph.adj[u][v]
            deps = graph.departures[u][v]

            arrival_to_u = previous_route_part[u]['arrival_time']
            arrival_to_u_td = timedelta(hours=arrival_to_u.hour, minutes=arrival_to_u.minute, seconds=arrival_to_u.second)

            idx = bisect_left(deps, arrival_to_u_td)

            no_path_in_current_day = True
            
            for i in range(idx, len(edges)):
                e = edges[i]
                path_was_found = process_edge(graph, pq, u, v, e, arrival_to_u, previous_route_part, cost, optimize_by_time)
                if path_was_found:
                    no_path_in_current_day = False

            if no_path_in_current_day:
                next_day_midnight = (arrival_to_u + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                delta_u = next_day_midnight - arrival_to_u

                for i in range(len(edges)):
                    e = edges[i]
                    path_was_found = process_edge(graph, pq, u, v, e, arrival_to_u, previous_route_part, cost, optimize_by_time, delta_u=delta_u)
                    if path_was_found:
                        no_path_in_current_day = False

    return cost, previous_route_part

def heuristics_distance(first_stop, second_stop):
    return geodesic(first_stop.coordinates, second_stop.coordinates).km

def heuristics(first_stop, second_stop):
    return timedelta(seconds=int(heuristics_distance(first_stop, second_stop) / AVG_TRAVEL_TIME * 3600)) 

@log_time(SUPRESS)
def a_star_algorithm(graph, starting_point, ending_point, starting_datetime, optimize_by_time=True, starting_route=None, **kwargs):
    log_is_allowed = kwargs.get("_log_if_allowed")
    if log_is_allowed:
        log_is_allowed("a_star_algorithm was executed wtih param %s", 'time' if optimize_by_time else 'transfers')
    
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
            deps = graph.departures[u][v]

            arrival_to_u = previous_route_part[u]['arrival_time']
            arrival_to_u_td = timedelta(hours=arrival_to_u.hour, minutes=arrival_to_u.minute, seconds=arrival_to_u.second)

            idx = bisect_left(deps, arrival_to_u_td)

            no_path_in_current_day = True
           
            for i in range(idx, len(edges)):
                e = edges[i]
                path_was_found = process_edge(graph, open_v, u, v, e, arrival_to_u, previous_route_part, cost, optimize_by_time, ending_point)
                if path_was_found:
                    no_path_in_current_day = False

            if no_path_in_current_day:
                next_day_midnight = (arrival_to_u + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                delta_u = next_day_midnight - arrival_to_u

                for i in range(len(edges)):
                    e = edges[i]
                    path_was_found = process_edge(graph, open_v, u, v, e, arrival_to_u, previous_route_part, cost, optimize_by_time, ending_point, delta_u)
                    if path_was_found:
                        no_path_in_current_day = False

    return cost, previous_route_part