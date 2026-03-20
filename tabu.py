from sys import maxsize
from collections import deque
from datetime import timedelta
from algorithms import a_star_algorithm

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