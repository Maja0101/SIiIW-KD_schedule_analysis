from sys import maxsize
from collections import deque, defaultdict
from datetime import timedelta, datetime
from algorithms import a_star_algorithm, dijkstra_algorithm
from load_data import create_graph
from user_route import get_user_route_from_alg_res, display_user_route
import city_definition as city

def tsp_route_cost(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time=True):
    # print("tsp_route_cost")
    curr_stop = starting_point
    curr_datetime = starting_datetime
    curr_route = None
    total_cost = {'time': timedelta(0), 'transfers': 0}

    for stop in stops_to_visit:
        # print("stop: ", stop)
        # print("total cost before iter: ", total_cost)
        cost, previous_route_part = a_star_algorithm(graph, curr_stop, stop, curr_datetime, optimize_by_time, curr_route)

        # user_route  = get_user_route_from_alg_res(curr_stop, stop, (cost, previous_route_part))
        # display_user_route(graph, user_route)

        if previous_route_part[stop]['stop'] == -1:
            # print("max 1")
            return {'time': timedelta.max, 'transfers': maxsize}
        
        # print("prev stop ", previous_route_part[stop]['stop'])
        
        total_cost['time'] += cost[stop]['time']
        total_cost['transfers'] += cost[stop]['transfers']
        # print("total cost after iter: ", total_cost)

        curr_datetime = previous_route_part[stop]['arrival_time']
        curr_stop = stop
        curr_route = previous_route_part[stop]['route']

        # print("curr datetime ", curr_datetime)
        # print("curr stop ", curr_stop)
        # print("curr route ", curr_route)

    cost, previous_route_part = a_star_algorithm(graph, curr_stop, starting_point, curr_datetime, optimize_by_time, curr_route)

    # user_route  = get_user_route_from_alg_res(curr_stop, starting_point, (cost, previous_route_part))
    # display_user_route(graph, user_route)

    if previous_route_part[starting_point]['stop'] == -1:
        # print("max 2")
        return {'time': timedelta.max, 'transfers': maxsize}
    
    # print("prev stop ", previous_route_part[starting_point]['stop'])
    
    total_cost['time'] += cost[starting_point]['time']
    total_cost['transfers'] += cost[starting_point]['transfers']

    # print("total cost at last: ", total_cost)
    return total_cost

def generate_neighbours(stops_to_visit):
    # print("generate_neighbours")
    # print("stops to visit ", stops_to_visit)
    neighbours = []

    n = len(stops_to_visit)

    for i in range(n - 1):
        for j in range(i + 1, n):
            new_stops_to_visit = stops_to_visit.copy()
            new_stops_to_visit[i:j+1] = reversed(new_stops_to_visit[i:j+1])
            neighbours.append((new_stops_to_visit, (i, j)))

    # print("neighbours: ", neighbours)
    return neighbours

def path(a, b):
    return tuple(sorted((a, b)))

def generate_neighbours_paths(stops_to_visit, starting_point):
    # print("generate_neighbours 2")
    # print("stops to visit ", stops_to_visit)
    neighbours = []

    full_stops_list = [starting_point] + stops_to_visit + [starting_point]
    n = len(full_stops_list)

    # print("full stops list ", full_stops_list)

    for i in range(1, n - 2):
        # print("i: ", i)
        for j in range(i + 1, n - 1):
            # print("j: ", j)
            new_stops_to_visit = stops_to_visit.copy()
            new_stops_to_visit[i-1:j] = reversed(new_stops_to_visit[i-1:j])

            a = full_stops_list[i - 1]
            b = full_stops_list[i]
            c = full_stops_list[j]
            d = full_stops_list[j + 1]

            removed = [(a, b), (c, d)]
            added = [(a, c), (b, d)]

            # print("new stops to visit ", new_stops_to_visit)
            # print("added ", added, "removed ", removed)

            neighbours.append((new_stops_to_visit, added, removed))

    # print("neighbours: ", neighbours)
    return neighbours

def initial_solution(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time=True):
    return stops_to_visit
    # print("initial_solution")
    remaining_stops = set(stops_to_visit)
    initial_solution = []

    curr_stop = starting_point
    curr_datetime = starting_datetime
    curr_route = None

    while remaining_stops:
        # print("remaining stops ", remaining_stops)
        best_stop = None
        best_cost = {'time': timedelta.max, 'transfers': maxsize}
        best_arrival = curr_datetime

        for stop in remaining_stops:
            # print("stop: ", stop)
            
            cost, previous_route_part = a_star_algorithm(graph, curr_stop, stop, curr_datetime, optimize_by_time, curr_route)

            # print("cost ", cost[stop])
            # print("prev stop ", previous_route_part[stop]['stop'])

            if previous_route_part[stop]['stop'] != -1 and ((optimize_by_time and cost[stop]['time'] < best_cost['time']) or (not optimize_by_time and cost[stop]['transfers'] < best_cost['transfers'])):
                # print("better")
                best_stop = stop
                best_cost['time'] = cost[stop]['time']
                best_cost['transfers'] = cost[stop]['transfers']
                best_arrival = previous_route_part[stop]['arrival_time']

        # print(best_stop)

        if best_stop is None:
            for r in remaining_stops:
                initial_solution.append(r)
            break

        initial_solution.append(best_stop)
        remaining_stops.remove(best_stop)

        curr_stop = best_stop
        curr_datetime = best_arrival

    print("initial solution: ", initial_solution)
    return initial_solution

def tabu_search_tsp(graph, starting_point, stops_to_visit, starting_datetime, optimize_by_time=True, max_iter=500):
    # print("tabu_search_tsp")
    n = len(stops_to_visit)

    TABU_SIZE = max(5, n // 2)
    # TABU_SIZE = 2
    # print("tabu size ", TABU_SIZE)
    NO_IMPROVEMENT_THRESHOLD = max(5, max_iter // 20) 
    k = 10
    HISTORY_SIZE = k
    epsilon = 0.01

    tabu_queue = deque(maxlen=TABU_SIZE)
    tabu_set = set()

    history = defaultdict(int)
    history_queue = deque(maxlen=HISTORY_SIZE)

    curr_solution = initial_solution(graph, stops_to_visit, starting_point, starting_datetime, optimize_by_time)

    best_solution = curr_solution.copy() 

    best_cost = tsp_route_cost(graph, best_solution, starting_point, starting_datetime)

    iteration = 0
    no_improvement = 0

    while iteration < max_iter:
        iteration += 1
        print("\niteration: ", iteration)

        # neighbours = generate_neighbours(curr_solution)
        neighbours = generate_neighbours_paths(curr_solution, starting_point)

        best_candidate = None
        best_candidate_cost = {'time': timedelta.max, 'transfers': maxsize}
        best_added_paths = None

        # print("curr solution ", curr_solution)
        # print("curr best ", best_solution, best_cost)

        for candidate, added, removed in neighbours:
            # print("tabu: ", tabu_set)
            # print("candidate: ", candidate)
            # print("best candidate: ", best_candidate, best_candidate_cost)

            # if any(e in tabu_set for e in added):
            #     continue

            cost = tsp_route_cost(graph, candidate, starting_point, starting_datetime)
            # print("cost ", cost)

            bonus = 0
            for e in added:
                bonus += (k - history[e])

            # if cost['time'] < timedelta.max:
            aspiration_cost = cost['time'] - timedelta(seconds=(epsilon*bonus))
            # else:
                # aspiration_cost = cost['time']

            tabu_edges = any(e in tabu_set for e in added)
            if not tabu_edges or cost['time'] < aspiration_cost:
                is_move_allowed = True
            else:
                is_move_allowed = False

            if not is_move_allowed:
                continue

            # if (optimize_by_time and cost['time'] < best_candidate_cost['time']) or (not optimize_by_time and cost['transfers'] < best_cost['transfers']):
            if aspiration_cost < best_candidate_cost['time']:
                # print("better")
                best_candidate = candidate
                best_candidate_cost = cost
                best_candidate_cost['time'] = aspiration_cost
                best_added_paths = added
                best_removed_paths = removed
                # print("now best: ", best_candidate, best_candidate_cost, best_added_paths, best_removed_paths)

        if best_candidate is None:
            # print("no best")
            break

        curr_solution = best_candidate

        # print("new curr solution ", curr_solution)
        # print("curr best ", best_solution, best_cost)

        for path in best_removed_paths:
            if len(tabu_queue) == tabu_queue.maxlen:
                oldest = tabu_queue.popleft()
                tabu_set.remove(oldest)

            tabu_queue.append(path)
            tabu_set.add(path)

        for path in best_added_paths:
            history[path] += 1
            history_queue.append(path)

            if len(history_queue) > history_queue.maxlen:
                old = history_queue.popleft()
                history[old] -= 1

        # print("tabu queue len ", len(tabu_queue))
        # print("tabu set ", tabu_set)

        real_cost = tsp_route_cost(graph, curr_solution, starting_point, starting_datetime)

        # if (optimize_by_time and best_candidate_cost['time'] < best_cost['time']) or (not optimize_by_time and best_candidate_cost['transfers'] < best_cost['transfers']):
        if (optimize_by_time and real_cost['time'] < best_cost['time']) or (not optimize_by_time and real_cost['transfers'] < best_cost['transfers']):
            print("new curr better than best")
            best_solution = best_candidate
            best_cost = real_cost
            # best_cost = best_candidate_cost
            # print("new curr best ", best_solution, best_cost)
            no_improvement = 0
        else:
            no_improvement += 1

        print("history ", history_queue)
        print("history dict ", history)

        # print("best:")
        # print(best_solution)
        # print(best_cost)

        if no_improvement >= NO_IMPROVEMENT_THRESHOLD:
            # print("no impro")
            break

    # print("no iter")

    print("best solution: ", best_solution)
    print("best cost: ", best_cost)
    return best_solution, best_cost

if __name__ == "__main__":
    graph = create_graph()
    best_solution, best_cost = tabu_search_tsp(graph, city.WROCLAW, [city.BIERKOWICE, city.WROCLAW_MUCHOBOR, city.ZAROW, city.LEGNICA, city.GLUSZYCA, city.SWIERKI_DOLNE, city.PRZYBYLOWICE, city.KLODZKO, city.WALBRZYCH_MIASTO], datetime(2026, 3, 6, 4, 55), True, 500)


    # solution = [1413380, 1413365, 1413255, 1413185, 1413210, 1413380]
    # solution = [city.WROCLAW, 1413423, 1413366, 1413139, 1413347, 1413078, 1413185, 1413284, 1413210, 1413386, city.WROCLAW]
    # curr_datetime = datetime(2026, 3, 6, 4, 55)
    # curr_route = None
    # for i in range(1, len(solution)):
    #     print("starting_time ", curr_datetime, curr_route)
    #     cost, previous_route_part = a_star_algorithm(graph, solution[i-1], solution[i], curr_datetime, starting_route=curr_route)
    #     user_route  = get_user_route_from_alg_res(solution[i-1], solution[i], (cost, previous_route_part))
    #     display_user_route(graph, user_route)
    #     curr_datetime = previous_route_part[solution[i]]['arrival_time']
    #     curr_route = previous_route_part[solution[i]]['route']

    # cost, previous_route_part = a_star_algorithm(graph, 1413185, 1413210, datetime(2026, 3, 6, 7, 35), True, None)
    # user_route  = get_user_route_from_alg_res(1413185, 1413210, (cost, previous_route_part))
    # display_user_route(graph, user_route)

    # cost, previous_route_part = a_star_algorithm(graph, 1413185, 1413210, datetime(2026, 3, 6, 7, 35), True, 'D6/D96')
    # user_route  = get_user_route_from_alg_res(1413185, 1413210, (cost, previous_route_part))
    # display_user_route(graph, user_route)

    # cost, previous_route_part = a_star_algorithm(graph, 1413185, 1413210, datetime(2026, 3, 6, 7, 35), True, 'D9')
    # user_route  = get_user_route_from_alg_res(1413185, 1413210, (cost, previous_route_part))
    # display_user_route(graph, user_route)

    # cost, previous_route_part = dijkstra_algorithm(graph, city.KLODZKO, datetime(2026, 3, 6, 7, 35))
    # user_route  = get_user_route_from_alg_res(city.KLODZKO, city.LEGNICA, (cost, previous_route_part))
    # display_user_route(graph, user_route)