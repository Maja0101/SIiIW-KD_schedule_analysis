from sys import maxsize
from collections import deque
from datetime import timedelta
from random import randint, choice
from algorithms import a_star_algorithm, heuristics_distance
from loggers import log_time, log_inline, log_inline_end

def tsp_route_cost(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time=True):
    curr_stop = starting_point
    curr_datetime = starting_datetime
    curr_route = None
    total_cost = {'time': timedelta(0), 'transfers': 0}

    for stop in stops_to_visit:
        cost, previous_route_part = a_star_algorithm(graph, curr_stop, stop, curr_datetime, optimize_by_time, curr_route)

        if previous_route_part[stop]['stop'] == -1:
            return {'time': timedelta.max, 'transfers': maxsize}
        
        
        total_cost['time'] += cost[stop]['time']
        total_cost['transfers'] += cost[stop]['transfers']

        curr_datetime = previous_route_part[stop]['arrival_time']
        curr_stop = stop
        curr_route = previous_route_part[stop]['route']

    cost, previous_route_part = a_star_algorithm(graph, curr_stop, starting_point, curr_datetime, optimize_by_time, curr_route)

    if previous_route_part[starting_point]['stop'] == -1:
        return {'time': timedelta.max, 'transfers': maxsize}
    
    total_cost['time'] += cost[starting_point]['time']
    total_cost['transfers'] += cost[starting_point]['transfers']

    return total_cost

def path(a, b):
    return tuple(sorted((a, b)))

def generate_neighbours_paths(stops_to_visit, starting_point):
    neighbours = []

    full_stops_list = [starting_point] + stops_to_visit + [starting_point]
    n = len(full_stops_list)

    for i in range(1, n - 2):
        for j in range(i + 1, n - 1):

            new_stops_to_visit = stops_to_visit.copy()
            new_stops_to_visit[i-1:j] = reversed(new_stops_to_visit[i-1:j])

            a = full_stops_list[i - 1]
            b = full_stops_list[i]
            c = full_stops_list[j]
            d = full_stops_list[j + 1]

            removed = [(a, b), (c, d)]
            added = [(a, c), (b, d)]

            neighbours.append((new_stops_to_visit, added, removed))

    return neighbours

def build_candidate_list(graph, nodes, k, heuristics_func=heuristics_distance):
    promising_candidates = {}

    for u in nodes:

        scored = []

        for v in nodes:

            if v == u:
                continue

            score = heuristics_func(graph.nodes[u], graph.nodes[v])
            scored.append((score, v))

        scored.sort(key=lambda x: x[0])

        promising_candidates[u] = [v for _, v in scored[:k]]

    return promising_candidates

def generate_mixed_neighbours(stops_to_visit, starting_point, promising_candidates, sample_size, alpha=0.7):
    neighbours = []

    full_stops_list = [starting_point] + stops_to_visit + [starting_point]
    n = len(full_stops_list)

    num_close_candidates = int(sample_size * alpha)

    seen = set()
    added_count = 0

    while added_count <= num_close_candidates:

        i = randint(1, n - 3)
        u = full_stops_list[i]

        if u not in promising_candidates:
            continue

        v = choice(promising_candidates[u])

        if v not in stops_to_visit:
            continue

        j = stops_to_visit.index(v) + 1

        if j <= i or j >= n - 1:
            continue

        new_stops_to_visit = stops_to_visit.copy()
        new_stops_to_visit[i-1:j] = reversed(new_stops_to_visit[i-1:j])

        a = full_stops_list[i - 1]
        b = full_stops_list[i]
        c = full_stops_list[j]
        d = full_stops_list[j + 1]

        removed = [(a, b), (c, d)]
        added = [(a, c), (b, d)]

        key = tuple(new_stops_to_visit)
        if key not in seen:
            seen.add(key)
            neighbours.append((new_stops_to_visit, added, removed))
            added_count += 1

    while added_count < sample_size:

        i = randint(1, n - 3)
        j = randint(i + 1, n - 2)

        new_stops_to_visit = stops_to_visit.copy()
        new_stops_to_visit[i-1:j] = reversed(new_stops_to_visit[i-1:j])

        a = full_stops_list[i - 1]
        b = full_stops_list[i]
        c = full_stops_list[j]
        d = full_stops_list[j + 1]

        removed = [(a, b), (c, d)]
        added = [(a, c), (b, d)]

        key = tuple(new_stops_to_visit)
        if key not in seen:
            seen.add(key)
            neighbours.append((new_stops_to_visit, added, removed))
            added_count += 1

    return neighbours

def generate_neighbours_advanced(best_cost, stops_to_visit, starting_point, promising_candidates, sample_size, alpha):
    if best_cost['time'] == timedelta.max:
        neighbours = generate_neighbours_paths(stops_to_visit, starting_point)
    else:
        neighbours = generate_mixed_neighbours(stops_to_visit, starting_point, promising_candidates, sample_size, alpha)

    return neighbours

def initial_solution(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time=True):
    remaining_stops = set(stops_to_visit)
    initial_solution = []

    curr_stop = starting_point
    curr_datetime = starting_datetime
    curr_route = None

    while remaining_stops:
        best_stop = None
        best_cost = {'time': timedelta.max, 'transfers': maxsize}
        best_arrival = curr_datetime

        for stop in remaining_stops:
            
            cost, previous_route_part = a_star_algorithm(graph, curr_stop, stop, curr_datetime, optimize_by_time, curr_route)

            if previous_route_part[stop]['stop'] != -1 and ((optimize_by_time and cost[stop]['time'] < best_cost['time']) or (not optimize_by_time and cost[stop]['transfers'] < best_cost['transfers'])):
                best_stop = stop
                best_cost['time'] = cost[stop]['time']
                best_cost['transfers'] = cost[stop]['transfers']
                best_arrival = previous_route_part[stop]['arrival_time']

        if best_stop is None:
            for r in remaining_stops:
                initial_solution.append(r)
            break

        initial_solution.append(best_stop)
        remaining_stops.remove(best_stop)

        curr_stop = best_stop
        curr_datetime = best_arrival

    return initial_solution

@log_time()
def tabu_search_tsp(graph, starting_point, stops_to_visit, starting_datetime, optimize_by_time=True, max_iter=500, unlimited=False, **kwargs):
    log_is_allowed = kwargs.get("_log_if_allowed")
    if log_is_allowed:
        log_is_allowed("tabu_search_tsp was executed wtih param %s", 'time' if optimize_by_time else 'transfers')

    n = len(stops_to_visit)

    if unlimited:
        tabu_size = None
    else:
        tabu_size = max(5, n // 2)

    NO_IMPROVEMENT_THRESHOLD = max(5, max_iter // 20) 

    tabu_queue = deque(maxlen=tabu_size)
    tabu_set = set()

    # curr_solution = initial_solution(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time)
    curr_solution = stops_to_visit

    best_solution = curr_solution.copy() 

    best_cost = tsp_route_cost(graph, best_solution, starting_point, starting_datetime)

    if n <= 5:
        k = max(1, n-1)
        sample_size = ((n-1)*n)//2
    elif n <= 15:
        k = 10
        sample_size = ((n-1)*n)//4
    elif n <= 50:
        k = 20
        sample_size = 50
    else:
        k = 30
        sample_size = 50

    promising_candidates = build_candidate_list(
        graph,
        stops_to_visit + [starting_point],
        k
    )

    iteration = 0
    no_improvement = 0

    while iteration < max_iter:
        iteration += 1
        
        log_inline('|')

        neighbours = generate_neighbours_advanced(best_cost, curr_solution, starting_point, promising_candidates, sample_size, 0.7)

        best_candidate = None
        best_candidate_cost = {'time': timedelta.max, 'transfers': maxsize}
        best_added_paths = None

        for candidate, added, removed in neighbours:

            cost = tsp_route_cost(graph, candidate, starting_point, starting_datetime)

            has_tabu_edges = any(e in tabu_set for e in added)
            better_time_cost = optimize_by_time and cost['time'] < best_cost['time']
            better_transfer_cost = not optimize_by_time and cost['transfers'] < best_cost['transfers']

            if (not has_tabu_edges) or (better_time_cost or better_transfer_cost):
                is_tabu = False
            else:
                is_tabu = True

            if is_tabu:
                continue

            if (optimize_by_time and cost['time'] < best_candidate_cost['time']) or (not optimize_by_time and cost['transfers'] < best_candidate_cost['transfers']):
                best_candidate = candidate
                best_candidate_cost = cost
                best_added_paths = added
                best_removed_paths = removed

        if best_candidate is None:
            break

        curr_solution = best_candidate

        for path in best_removed_paths:
            if len(tabu_queue) == tabu_queue.maxlen:
                oldest = tabu_queue.popleft()
                tabu_set.remove(oldest)

            tabu_queue.append(path)
            tabu_set.add(path)

        real_cost = tsp_route_cost(graph, curr_solution, starting_point, starting_datetime)

        if (optimize_by_time and real_cost['time'] < best_cost['time']) or (not optimize_by_time and real_cost['transfers'] < best_cost['transfers']):
            best_solution = best_candidate
            best_cost = real_cost
            no_improvement = 0
        else:
            no_improvement += 1


        if no_improvement >= NO_IMPROVEMENT_THRESHOLD:
            break

    log_inline_end()
    
    return best_cost, best_solution