import heapq
from graph import Graph, Node, Edge
from datetime import datetime, timedelta, date
from sys import maxsize
from geopy.distance import geodesic

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
    # print("cost by time")
    if current_datetime > edge.start_date and current_datetime < edge.end_date:
        # print("between dates")
        if runs_on_this_day(current_datetime.date(), edge):
            # print("runs on this day")
            curr_td = timedelta(hours=current_datetime.hour, minutes=current_datetime.minute, seconds=current_datetime.second)
            # print("curr td ", curr_td)
            # print("departure time ", edge.departure_time)
            # print("valid ", curr_td <= edge.departure_time)

            if current_route is None and curr_td <= edge.departure_time:
                # print("first")
                # print("ok")
                # print("cost: ", edge.arrival_time - edge.departure_time)
                return edge.arrival_time - edge.departure_time, 0

            if edge.route_name == current_route and curr_td <= edge.departure_time:
                # print("without transfer")
                # print("ok")
                # print("cost: ", edge.arrival_time - curr_td)
                return edge.arrival_time - curr_td, 0
            
            if curr_td + TRANSFER_TIME <= edge.departure_time:
                # print("with transfer")
                # print("ok")
                # print("cost: ", edge.arrival_time - curr_td)
                return edge.arrival_time - curr_td, 1
        
    # print("not ok")   
    return timedelta.max, maxsize
    

def dijkstra_algorithm(graph, starting_point, starting_datetime):
    pq = PriorityQueue()

    cost = {key: {'time': timedelta.max, 'transfers': maxsize} for key in graph.nodes.keys()}

    previous_route_part = {key: {'stop': -1, 'route': None, 'departure_time': None, 'arrival_time': None}  for key in graph.nodes.keys()} 

    cost[starting_point]['time'] = timedelta(0)
    cost[starting_point]['transfers'] = 0

    previous_route_part[starting_point]['arrival_time'] = starting_datetime

    pq.push(starting_point, timedelta(0))

    print("start")
    print("cost: ", cost)
    print("previous_route_part: ", previous_route_part)

    i = 0
    while not pq.is_empty():
        print("i = ", i)

        d, u = pq.pop()

        j = 0
        for v, e in graph.adj[u]:
            print("j = ", j)
            print("u: ", u, " v: ", v, " e: ", f"{e.departure_time}-{e.arrival_time} ({e.route_name})")
            
            time_u_v, transfer_u_v = calc_cost(
                previous_route_part[u]['arrival_time'], 
                previous_route_part[u]['route'], 
                e)
            
            print("time cost: ", time_u_v)
            print("transfer cost: ", time_u_v)

            if time_u_v < timedelta.max and (cost[v]['time'] > cost[u]['time'] + time_u_v or (cost[v]['time'] == cost[u]['time'] + time_u_v and previous_route_part[u]['arrival_time'] + time_u_v < previous_route_part[v]['arrival_time'])):
                cost[v]['time'] = cost[u]['time'] + time_u_v
                cost[v]['transfers'] = cost[u]['transfers'] + transfer_u_v
                previous_route_part[v]['stop'] = u

                if u == starting_point:
                    previous_route_part[v]['arrival_time'] = datetime(previous_route_part[u]['arrival_time'].year, previous_route_part[u]['arrival_time'].month, previous_route_part[u]['arrival_time'].day) + e.arrival_time
                else:
                    previous_route_part[v]['arrival_time'] = previous_route_part[u]['arrival_time'] + time_u_v
                previous_route_part[v]['departure_time'] = previous_route_part[v]['arrival_time'] - (e.arrival_time - e.departure_time)
                previous_route_part[v]['route'] = e.route_name
                pq.push(v, cost[v]['time'])

            print("cost: ", cost)
            print("previous_route_part: ", previous_route_part)

            j += 1

        i += 1

    return cost, previous_route_part

def heuristics(first_stop, second_stop):
    print("heuristics ", timedelta(seconds=int(geodesic(first_stop.coordinates, second_stop.coordinates).km / AVG_TRAVEL_TIME * 3600)) )
    return timedelta(seconds=int(geodesic(first_stop.coordinates, second_stop.coordinates).km / AVG_TRAVEL_TIME * 3600)) 

def a_star_algorithm(graph, starting_point, ending_point, starting_datetime, optimize_by_time=True):
    open_v = PriorityQueue()
    closed_v = set()

    cost = {key: {'time': timedelta.max, 'transfers': maxsize} for key in graph.nodes.keys()}

    previous_route_part = {key: {'stop': -1, 'route': None, 'departure_time': None, 'arrival_time': None}  for key in graph.nodes.keys()} 

    cost[starting_point]['time'] = timedelta(0)
    cost[starting_point]['transfers'] = 0

    previous_route_part[starting_point]['arrival_time'] = starting_datetime

    open_v.push(starting_point, timedelta(0))

    i = 0
    while not open_v.is_empty():
        print("i = ", i)

        d, u = open_v.pop()

        print("got with f ", d)

        if u == ending_point:
            return cost, previous_route_part

        closed_v.add(u)

        j = 0
        for v, e in graph.adj[u]:
            print("j = ", j)
            print("u: ", u, " v: ", v, " e: ", f"{e.departure_time}-{e.arrival_time} ({e.route_name})")

            print("cost: ", cost)
            print("previous_route_part: ", previous_route_part)

            if v in closed_v:
                continue

            time_u_v, transfer_u_v = calc_cost(
                previous_route_part[u]['arrival_time'], 
                previous_route_part[u]['route'], 
                e)
            
            print("time cost: ", time_u_v)
            print("transfer cost: ", transfer_u_v)

            if (optimize_by_time and (
                time_u_v < timedelta.max and (
                    cost[v]['time'] > cost[u]['time'] + time_u_v or (
                        cost[v]['time'] == cost[u]['time'] + time_u_v and previous_route_part[u]['arrival_time'] + time_u_v < previous_route_part[v]['arrival_time'])))) or (
                not optimize_by_time and (
                    transfer_u_v < maxsize and (
                        cost[v]['transfers'] > cost[u]['transfers'] + transfer_u_v or (
                            cost[v]['transfers'] == cost[u]['transfers'] + transfer_u_v and previous_route_part[u]['arrival_time'] + time_u_v < previous_route_part[v]['arrival_time'])))
                ):
                    
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

                print("adding with f ", f)

            j += 1

        i += 1

    return cost, previous_route_part


def user_route(starting_point, ending_point, algorithm_results):
    cost, route_part = algorithm_results

    route = []

    current_stop = ending_point


    single_train_route = {"route_name": route_part[current_stop]['route'], "stops": [], "start_time": route_part[current_stop]['arrival_time'], "end_time":  route_part[current_stop]['arrival_time']}
    while current_stop != starting_point:
        if single_train_route["route_name"] == route_part[current_stop]['route']:
            single_train_route["stops"].append(current_stop)
            single_train_route["start_time"] = route_part[current_stop]['departure_time']
            print("s t r ", single_train_route)
        else:
           single_train_route['stops'].append(current_stop)
           single_train_route['stops'].reverse()
           print("final single route ", single_train_route)
           route.append(single_train_route)
           single_train_route = {"route_name": route_part[current_stop]['route'], "stops": [current_stop], "start_time": route_part[current_stop]['arrival_time'], "end_time":  route_part[current_stop]['arrival_time']} 

        current_stop = route_part[current_stop]['stop']
    
    single_train_route["stops"].append(current_stop)
    single_train_route['stops'].reverse()
    print("final single route ", single_train_route)
    route.append(single_train_route) 
    route.reverse()

    print("route: ")
    for r in route:
        print(r)

    return cost[ending_point], route

def display_user_route(graph, user_route):
    cost, route = user_route
    
    for r in route:
        via = ', '.join(graph.nodes[i].name for i in  r['stops'][1:-1] if i in graph.nodes)
        print(f"Train: {r['route_name']} Departure from {graph.nodes.get(r['stops'][0]).name} at {r['start_time'].strftime('%Y-%m-%d %H:%M')} {f'via {via} ' if via else ''}arrival at {graph.nodes.get(r['stops'][-1]).name} at {r['end_time'].strftime('%Y-%m-%d %H:%M')}")

    print(f"Travel time: {cost['time']} Number of transfers: {cost['transfers']}")


if __name__ == '__main__':
    graph = Graph()

    graph.add_node(0, Node('A', 50, 15))
    graph.add_node(1, Node('B', 50, 16))
    graph.add_node(2, Node('C', 51, 16))
    graph.add_node(3, Node('D', 51, 17))
    graph.add_node(4, Node('E', 52, 15))
    graph.add_node(5, Node('F', 52, 16))
    graph.add_node(6, Node('G', 51, 18))

    # graph.add_edge(0, 1, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=13), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(0, 4, Edge(timedelta(0, hours=10, minutes=16), timedelta(0, hours=10, minutes=19), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, False, True], {date(2026, 3, 14): 1}))
    # graph.add_edge(1, 2, Edge(timedelta(0, hours=10, minutes=13), timedelta(0, hours=10, minutes=14), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 3, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=11), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=14), timedelta(0, hours=10, minutes=15), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(3, 1, Edge(timedelta(0, hours=10, minutes=35), timedelta(0, hours=10, minutes=36), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(4, 5, Edge(timedelta(0, hours=10, minutes=20), timedelta(0, hours=10, minutes=21), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 0, Edge(timedelta(0, hours=10, minutes=15), timedelta(0, hours=10, minutes=21), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=30), timedelta(0, hours=10, minutes=35), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    # graph.add_edge(3, 6, Edge(timedelta(0, hours=10, minutes=46), timedelta(0, hours=10, minutes=50), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))

    graph.add_edge(0, 1, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=13), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(0, 4, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=31), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, False, True], {date(2026, 3, 14): 1}))
    graph.add_edge(1, 2, Edge(timedelta(0, hours=10, minutes=18), timedelta(0, hours=10, minutes=20), 'e', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(2, 3, Edge(timedelta(0, hours=10, minutes=10), timedelta(0, hours=10, minutes=11), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(2, 5, Edge(timedelta(0, hours=10, minutes=26), timedelta(0, hours=10, minutes=36), 'f', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(3, 1, Edge(timedelta(0, hours=10, minutes=35), timedelta(0, hours=10, minutes=36), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(4, 5, Edge(timedelta(0, hours=10, minutes=32), timedelta(0, hours=10, minutes=36), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 0, Edge(timedelta(0, hours=10, minutes=15), timedelta(0, hours=10, minutes=21), 'a', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=41), timedelta(0, hours=10, minutes=45), 'c', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(3, 6, Edge(timedelta(0, hours=10, minutes=46), timedelta(0, hours=10, minutes=50), 'd', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))
    graph.add_edge(5, 3, Edge(timedelta(0, hours=10, minutes=36), timedelta(0, hours=10, minutes=55), 'b', datetime(2026, 3, 3), datetime(2026, 12, 12), [True, True, True, True, True, True, True], {}))

    # cost, previous_route_part = dijkstra_algorithm(graph, 0, datetime(2026, 3, 14, 10, 10, 00))
    cost, previous_route_part = a_star_algorithm(graph, 0, 3, datetime(2026, 3, 14, 10, 10, 00), False)

    print("end")
    print("cost: ", cost)
    print("previous_route_part: ", previous_route_part)

    user_route  = user_route(0, 3, (cost, previous_route_part))

    display_user_route(graph, user_route)