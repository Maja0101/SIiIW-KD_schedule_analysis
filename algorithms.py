import heapq
from graph import Graph, Node, Edge
from datetime import datetime, timedelta, date
from sys import maxsize
from geopy.distance import geodesic
from collections import deque
from timer import timer

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
    if ep: print(f"{current_datetime}: {edge.start_date} - {edge.end_date} ({current_route})")
    if current_datetime > edge.start_date and current_datetime < edge.end_date:
        # print("between dates")
        if ep: print(f"{edge.weekdays} - {edge.exceptions.get(current_datetime.date())}")

        if runs_on_this_day(current_datetime.date(), edge):
            curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)
            if ep: print(curr_td)

            if current_route is None and curr_td <= edge.departure_time:
                if ep: print("first")
                return edge.arrival_time - edge.departure_time, 0

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
            for v, e in graph.adj[u]:

                if u == 1413153:
                    expectedRoute = True
                else:
                    expectedRoute = False
                expectedRoute = False
                
                time_u_v, transfer_u_v = calc_cost(
                    previous_route_part[u]['arrival_time'], 
                    previous_route_part[u]['route'], 
                    e, expectedRoute)

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

def heuristics(first_stop, second_stop):
    return timedelta(seconds=int(geodesic(first_stop.coordinates, second_stop.coordinates).km / AVG_TRAVEL_TIME * 3600)) 

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

        for v, e in graph.adj[u]:
            if v in closed_v:
                continue

            time_u_v, transfer_u_v = calc_cost(
                previous_route_part[u]['arrival_time'], 
                previous_route_part[u]['route'], 
                e)

            is_not_infinite_cost = (optimize_by_time and time_u_v < timedelta.max) or (not optimize_by_time and transfer_u_v < maxsize)

            if is_not_infinite_cost:

                if u == starting_point:
                    temp_new_arrival_time = datetime(previous_route_part[u]['arrival_time'].year, previous_route_part[u]['arrival_time'].month, previous_route_part[u]['arrival_time'].day) + e.arrival_time
                else:
                    temp_new_arrival_time = previous_route_part[u]['arrival_time'] + time_u_v

                is_better_cost = (optimize_by_time and cost[v]['time'] > cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] > cost[u]['transfers'] + transfer_u_v)
                is_equal_cost = (optimize_by_time and cost[v]['time'] == cost[u]['time'] + time_u_v) or (not optimize_by_time and cost[v]['transfers'] == cost[u]['transfers'] + transfer_u_v)
                is_equal_and_earlier_than_best_known_part = is_equal_cost and (temp_new_arrival_time < previous_route_part[v]['arrival_time'])

                if (is_better_cost or is_equal_and_earlier_than_best_known_part):
                    
                    cost[v]['time'] = cost[u]['time'] + time_u_v
                    cost[v]['transfers'] = cost[u]['transfers'] + transfer_u_v
                    previous_route_part[v]['stop'] = u

                    if u == starting_point:
                        previous_route_part[v]['arrival_time'] = datetime(previous_route_part[u]['arrival_time'].year, previous_route_part[u]['arrival_time'].month, previous_route_part[u]['arrival_time'].day) + e.arrival_time
                    else:
                        previous_route_part[v]['arrival_time'] = previous_route_part[u]['arrival_time'] + time_u_v
                    previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - (e.arrival_time - e.departure_time)
                    previous_route_part[v]['route'] = e.route_name

                    f = cost[v]['time'] + heuristics(graph.nodes[v], graph.nodes[ending_point])
                    if not optimize_by_time:
                        f += cost[v]['transfers'] * TRANSFER_PENALTY
                    open_v.push(v, f)

    return cost, previous_route_part

def tsp_route_cost(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time=True):
    print("tsp_route_cost")
    curr_stop = starting_point
    curr_datetime = starting_datetime
    curr_route = None
    total_cost = {'time': timedelta(0), 'transfers': 0}

    for stop in stops_to_visit:
        print("stop: ", stop)
        print("total cost begin: ", total_cost)
        cost, previous_route_part = a_star_algorithm(graph, curr_stop, stop, curr_datetime, optimize_by_time, curr_route)

        if previous_route_part[stop]['stop'] == -1:
            print("max 1")
            return {'time': timedelta.max, 'transfers': maxsize}
        
        print("prev stop ", previous_route_part[stop]['stop'])
        
        total_cost['time'] += cost[stop]['time']
        total_cost['transfers'] += cost[stop]['transfers']
        print("total cost after iter: ", total_cost)

        curr_datetime = previous_route_part[stop]['arrival_time']
        curr_stop = stop
        curr_route = previous_route_part[stop]['route']

    cost, previous_route_part = a_star_algorithm(graph, curr_stop, starting_point, curr_datetime, optimize_by_time, curr_route)

    if previous_route_part[starting_point]['stop'] == -1:
        print("max 2")
        return {'time': timedelta.max, 'transfers': maxsize}
    
    print("prev stop ", previous_route_part[starting_point]['stop'])
    
    total_cost['time'] += cost[starting_point]['time']
    total_cost['transfers'] += cost[starting_point]['transfers']

    print("total cost at last: ", total_cost)
    return total_cost

def generate_neighbours(stops_to_visit):
    print("generate_neighbours")
    print("stops to visit ", stops_to_visit)
    neighbours = []

    n = len(stops_to_visit)

    for i in range(n - 1):
        for j in range(i + 1, n):
            new_stops_to_visit = stops_to_visit.copy()
            new_stops_to_visit[i:j+1] = reversed(new_stops_to_visit[i:j+1])
            neighbours.append((new_stops_to_visit, (i, j)))

    print("neighbours: ", neighbours)
    return neighbours

def path(a, b):
    return tuple(sorted((a, b)))

def generate_neighbours_paths(stops_to_visit):
    print("generate_neighbours 2")
    print("stops to visit ", stops_to_visit)
    neighbours = []

    n = len(stops_to_visit)

    for i in range(n - 1):
        for j in range(i + 1, n):
            new_stops_to_visit = stops_to_visit.copy()
            new_stops_to_visit[i:j+1] = reversed(new_stops_to_visit[i:j+1])

            a = stops_to_visit[i - 1] if i > 0 else None
            b = stops_to_visit[i]
            c = stops_to_visit[j]
            d = stops_to_visit[j + 1] if j < n - 1 else None

            removed = []
            added = []

            if a is not None:
                removed.append(path(a, b))
                added.append(path(a, c))

            if d is not None:
                removed.append(path(c, d))
                added.append(path(b, d))

            neighbours.append((new_stops_to_visit, added, removed))

    print("neighbours: ", neighbours)
    return neighbours

def initial_solution(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time=True):
    print("initial_solution")
    remaining_stops = set(stops_to_visit)
    initial_solution = []

    curr_stop = starting_point
    curr_datetime = starting_datetime
    curr_route = None

    while remaining_stops:
        print("remaining stops ", remaining_stops)
        best_stop = None
        best_cost = {'time': timedelta.max, 'transfers': maxsize}
        best_arrival = curr_datetime

        for stop in remaining_stops:
            print("stop: ", stop)
            
            cost, previous_route_part = a_star_algorithm(graph, curr_stop, stop, curr_datetime, optimize_by_time, curr_route)
            print("cost ", cost[stop])
            print("prev stop ", previous_route_part[stop]['stop'])

            if previous_route_part[stop]['stop'] != -1 and ((optimize_by_time and cost[stop]['time'] < best_cost['time']) or (not optimize_by_time and cost[stop]['transfers'] < best_cost['transfers'])):
                print("better")
                best_stop = stop
                best_cost['time'] = cost[stop]['time']
                best_cost['transfers'] = cost[stop]['transfers']
                best_arrival = previous_route_part[stop]['arrival_time']

        initial_solution.append(best_stop)
        remaining_stops.remove(best_stop)

        curr_stop = best_stop
        curr_datetime = best_arrival

    print("initial solution: ", initial_solution)
    return initial_solution

def tabu_search_tsp(graph, starting_point, stops_to_visit, starting_datetime, optimize_by_time=True, max_iter=500):
    print("tabu_search_tsp")
    n = len(stops_to_visit)

    TABU_SIZE = max(5, n // 2)
    NO_IMPROVEMENT_THRESHOLD = max(5, max_iter // 20) 

    tabu_queue = deque(maxlen=TABU_SIZE)
    tabu_set = set()

    curr_solution = initial_solution(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time)

    best_solution = curr_solution.copy() 

    best_cost = tsp_route_cost(graph, best_solution, starting_point, starting_datetime)

    iteration = 0
    no_improvement = 0

    while iteration < max_iter:
        iteration += 1
        print("\niteration: ", iteration, " max: ", max_iter)

        # neighbours = generate_neighbours(curr_solution)
        neighbours = generate_neighbours_paths(curr_solution)

        best_candidate = None
        best_candidate_cost = {'time': timedelta.max, 'transfers': maxsize}
        best_added_paths = None

        print("curr solution ", curr_solution)
        print("curr best ", best_solution, best_cost)

        for candidate, added, removed in neighbours:
            print("tabu: ", tabu_set)
            print("candidate: ", candidate)
            print("best candidate: ", best_candidate, best_candidate_cost)

            if any(e in tabu_set for e in added):
                continue

            cost = tsp_route_cost(graph, candidate, starting_point, starting_datetime)
            print("cost ", cost)

            if (optimize_by_time and cost['time'] < best_candidate_cost['time']) or (not optimize_by_time and cost['transfers'] < best_cost['transfers']):
                print("better")
                best_candidate = candidate
                best_candidate_cost = cost
                best_added_paths = added
                best_removed_paths = removed
                print("now best: ", best_candidate, best_candidate_cost, best_added_paths, best_removed_paths)
                # new best not set as best???

        if best_candidate is None:
            print("no best")
            break

        curr_solution = best_candidate

        print("new curr solution ", curr_solution)
        print("curr best ", best_solution, best_cost)

        for path in best_removed_paths:
            if len(tabu_queue) == tabu_queue.maxlen:
                oldest = tabu_queue.popleft()
                tabu_set.remove(oldest)

            tabu_queue.append(path)
            tabu_set.add(path)

        if (optimize_by_time and best_candidate_cost['time'] < best_cost['time']) or (not optimize_by_time and best_candidate_cost['transfers'] < best_cost['transfers']):
            print("new curr better than best")
            best_solution = best_candidate
            best_cost = best_candidate_cost
            print("new curr best ", best_solution, best_cost)
            no_improvement = 0
        else:
            no_improvement += 1

        print("best:")
        print(best_solution)
        print(best_cost)

        if no_improvement >= NO_IMPROVEMENT_THRESHOLD:
            print("no impro")
            break

    print("no iter")

    print("best solution: ", best_solution)
    print("best cost: ", best_cost)
    return best_solution, best_cost

def get_user_route_from_alg_res(starting_point, ending_point, algorithm_results):
    cost, route_part = algorithm_results

    route = []

    current_stop = ending_point

    if route_part[ending_point]['stop'] == -1:
        return None, None


    single_train_route = {"route_name": route_part[current_stop]['route'], "stops": [], "start_time": route_part[current_stop]['arrival_time'], "end_time":  route_part[current_stop]['arrival_time']}
    # print("first s t r ", single_train_route)
    while current_stop != starting_point:
        # print("while")
        # print("curr stop ", current_stop)
        # print("start stop ", starting_point)
        if single_train_route["route_name"] == route_part[current_stop]['route']:
            single_train_route["stops"].append(current_stop)
            single_train_route["start_time"] = route_part[current_stop]['departure_time']
            # print("s t r ", single_train_route)
        else:
           single_train_route['stops'].append(current_stop)
           single_train_route['stops'].reverse()
        #    print("final single route ", single_train_route)
           route.append(single_train_route)
           single_train_route = {"route_name": route_part[current_stop]['route'], "stops": [current_stop], "start_time": route_part[current_stop]['arrival_time'], "end_time":  route_part[current_stop]['arrival_time']} 

        current_stop = route_part[current_stop]['stop']
    
    single_train_route["stops"].append(current_stop)
    single_train_route['stops'].reverse()
    # print("final single route ", single_train_route)
    route.append(single_train_route) 
    route.reverse()

    # print("route: ")
    # for r in route:
    #     print(r)

    return cost[ending_point], route

def display_user_route(graph, user_route):
    cost, route = user_route

    if route is None:
        print("\nSorry! We couldn't find a train for you.\n")
        return False
    
    print("\n----------\n")
    for r in route:
        via = '\n\t\t'.join(graph.nodes[i].name for i in r['stops'][1:-1] if i in graph.nodes)
        print(f"Train: {r['route_name']}")
        print(f"\tDeparture from {graph.nodes.get(r['stops'][0]).name} at {r['start_time'].strftime('%Y-%m-%d %H:%M')}")
        if via:
            print(f"\tVia")
            print(f'\t\t{via}')
        print(f"\tArrival at {graph.nodes.get(r['stops'][-1]).name} at {r['end_time'].strftime('%Y-%m-%d %H:%M')}\n")

    print('-----------')
    print(f"Travel time: {cost['time']} Number of transfers: {cost['transfers']}")
    print('-----------\n')

    return True


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