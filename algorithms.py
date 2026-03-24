import heapq
from graph import Graph, Node, Edge
from datetime import datetime, timedelta, date
from sys import maxsize
from geopy.distance import geodesic
from loggers import log_time, SUPRESS, log_debug
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

def calc_cost(current_datetime, current_route, edge):
    if current_datetime > edge.start_date and current_datetime < edge.end_date:
        #  print(f"{current_datetime} ({current_route}): {edge.departure_time} - {edge.arrival_time} - {edge.weekdays} - {edge.exceptions.get(current_datetime.date())}")

         if runs_on_this_day(current_datetime.date(), edge):
             
             curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)

             if (current_route is None or edge.route_name == current_route) and curr_td <= edge.departure_time:
                 return edge.arrival_time - curr_td, 0
             
             if curr_td + TRANSFER_TIME <= edge.departure_time:
                 return edge.arrival_time - curr_td, 1
             
    return timedelta.max, maxsize

# def calc_cost(current_datetime, current_route, edge, ep=False):
#     cost_time, cost_transfers = calc_cost_for_datetime(current_datetime, current_route, edge, ep)
#     if ep: log_debug(f"{cost_time} {cost_transfers}")

#     if cost_time is None:
#         if ep: log_debug("None found")
#         next_day = (current_datetime + timedelta(days=1)).replace(hour=0, minute=0, second=0)
#         if ep: log_debug(f"next day {next_day}")
#         cost_time, cost_transfers = calc_cost_for_datetime(next_day, current_route, edge, ep)
#         if ep: log_debug(cost_time, cost_transfers)

#         if cost_time is None:
#             log_debug("still none")
#             return timedelta.max, maxsize
#         else:
#             log_debug(f"some {cost_time + (next_day - current_datetime)}, {cost_transfers} ")
#             return cost_time + (next_day - current_datetime), cost_transfers
        
#     if ep: log_debug(f"found {cost_time} {cost_transfers}")
#     return cost_time, cost_transfers


    # if current_datetime > edge.start_date and current_datetime < edge.end_date:
    #     # if ep: print("between dates")
    #     # if ep: print(f"{edge.weekdays} - {edge.exceptions.get(current_datetime.date())}")

    #     if runs_on_this_day(current_datetime.date(), edge):
    #         if ep: print(f"{current_datetime}: {edge.start_date} - {edge.end_date} ({current_route})")

    #         curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)
    #         if ep: print(curr_td)

    #         if current_route is None and curr_td <= edge.departure_time:
    #             if ep: print("first")
    #             # return edge.arrival_time - edge.departure_time, 0
    #             return edge.arrival_time - curr_td, 0

    #         if edge.route_name == current_route and curr_td <= edge.departure_time:
    #             if ep: print("no transfer")
    #             return edge.arrival_time - curr_td, 0
            
    #         if curr_td + TRANSFER_TIME <= edge.departure_time:
    #             if ep: print("transfer")
    #             return edge.arrival_time - curr_td, 1
        
    # return timedelta.max, maxsize
    
@log_time(SUPRESS)
def dijkstra_algorithm(graph, starting_point, starting_datetime, **kwargs):
    log_is_allowed = kwargs.get("_log_if_allowed")
    if log_is_allowed:
        log_is_allowed("dijkstra_algorithm was executed wtih param time")

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

def process_edge(graph, u, v, e, arrival_to_u, previous_route_part, cost, ending_point, open_v, optimize_by_time, delta_u=timedelta(0)):
    time_u_v, transfer_u_v = calc_cost(arrival_to_u, previous_route_part[u]['route'], e)

    is_infinite_cost = not ((optimize_by_time and time_u_v < timedelta.max) or (not optimize_by_time and transfer_u_v < maxsize))

    if is_infinite_cost:
        return False
    
    temp_new_arrival_time = arrival_to_u + time_u_v

    time_u_v += delta_u

    is_better_cost = (optimize_by_time and cost[v]['time'] > cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] > cost[u]['transfers'] + transfer_u_v)
    is_equal_cost_less_transfers = optimize_by_time and cost[v]['time'] == cost[u]['time'] + time_u_v and cost[v]['transfers'] > cost[u]['transfers'] + transfer_u_v
    is_equal_cost_less_time = not optimize_by_time and cost[v]['transfers'] == cost[u]['transfers'] + transfer_u_v and cost[v]['time'] > cost[u]['time'] + time_u_v

    if (is_better_cost or is_equal_cost_less_transfers or is_equal_cost_less_time):
                        
        cost[v]['time'] = cost[u]['time'] + time_u_v
        cost[v]['transfers'] = cost[u]['transfers'] + transfer_u_v

        previous_route_part[v]['stop'] = u

        previous_route_part[v]['arrival_time'] = temp_new_arrival_time
        previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - e.travel_time

        previous_route_part[v]['route'] = e.route_name

        f = cost[v]['time'] + heuristics(graph.nodes[v], graph.nodes[ending_point])
        if not optimize_by_time:
            f += cost[v]['transfers'] * TRANSFER_PENALTY
        
        open_v.push(v, f)

    return True

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

            # print(f"{graph.nodes[u].name} --> {graph.nodes[v].name}")

            if v in closed_v:
                continue
            
            edges = graph.adj[u][v]
            deps = graph.departures[u][v]

            arrival_to_u = previous_route_part[u]['arrival_time']
            arrival_to_u_td = timedelta(hours=arrival_to_u.hour, minutes=arrival_to_u.minute, seconds=arrival_to_u.second)

            idx = bisect_left(deps, arrival_to_u_td)

            no_path_in_current_day = True
           
            # print("for loop 1 ")
            for i in range(idx, len(edges)):
                e = edges[i]
                path_was_found = process_edge(graph, u, v, e, arrival_to_u, previous_route_part, cost, ending_point, open_v, optimize_by_time)
                if path_was_found:
                    # print("path was found")
                    # print(cost[v])
                    # print(previous_route_part[v])
                    no_path_in_current_day = False

            # print("no_path_in_current_day ", no_path_in_current_day)
            if no_path_in_current_day:
                next_day_midnight = (arrival_to_u + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                delta_u = next_day_midnight - arrival_to_u

                # print("next day ", next_day_midnight, " delta ", delta_u)

                # print("for loop 2 ")
                for i in range(len(edges)):
                    e = edges[i]
                    path_was_found = process_edge(graph, u, v, e, next_day_midnight, previous_route_part, cost, ending_point, open_v, optimize_by_time, delta_u)
                    if path_was_found:
                        # print("path was found")
                        # print(cost[v])
                        # print(previous_route_part[v])
                        no_path_in_current_day = False

                # print("no_path_in_current_day ", no_path_in_current_day)

    return cost, previous_route_part