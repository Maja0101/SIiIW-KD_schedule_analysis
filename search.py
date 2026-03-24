from datetime import datetime
from load_data import create_graph
from algorithms import dijkstra_algorithm, a_star_algorithm
from tabu import tabu_search_tsp
from user_route import display_user_route, get_user_route_from_alg_res, get_tsp_user_route_from_alg_res
from datetime import timedelta
from loggers import log_debug
import city_definition as city

MIN_DATE = datetime(2026, 3, 3, 0, 0)
MAX_DATE = datetime(2026, 12, 12, 23, 59)

def get_answer(msg, first_option, second_option):
    while True:
        answer = input(msg).lower()
        if answer == first_option:
            return True
        elif answer == second_option:
            return False
        print('Unknown value. Please try again...')

def get_new_route():
    msg = 'Do you want to search for new route? (y/n) '
    return get_answer(msg, 'y', 'n')

def get_single_or_tsp_default_single():
    msg = 'Do you want to search for single route (s) or tsp (t)? (s/t) '
    return get_answer(msg, 's', 't')

def get_station(is_destination):
    if is_destination:
        msg = 'What is your destination? '
    else:
        msg = 'What is your starting station? '

    while True:
        answer = input(msg).strip().lower()
        found_station = next((station for station in graph.nodes.values() if station.name.lower() == answer), None)
        if found_station is not None:
            return found_station
        print('Unknown station. Please try again...')

def get_destinations_list():
    msg = 'What stations do you want to visit? Write a list of stations separated by a semicolon, ex. Bierkowice;Wrocław Muchobór;Żarów;Legnica;Głuszyca;Świerki Dolne;Przybyłowice;Kłodzko Główne;Wałbrzych Miasto '
    print(msg)
    while True:

        answer = input().strip().lower()
        stations_list_names = answer.split(';')
        stations = []
        all_recognized = True

        for city in stations_list_names:
            # print("city name ", city)
            found_station = next((station for station in graph.nodes.values() if station.name.lower() == city.strip()), None)
            # print("found station ", found_station)
            if found_station is not None:
                stations.append(found_station.idx)
            else:
                all_recognized = False

        if all_recognized:
            return stations
            
        print('Some stations were not recognized. Please try again...')



def get_algorithm_default_dijkstra():
    msg = 'Do you want to use Dijkstra (d) ot A* (a) algorithm? (d/a) '
    return get_answer(msg, 'd', 'a')
    
def get_optimalization_parameter_default_time():
    msg = 'What do you want to optimize the route based on time (t) or the number of transfers (p)? (t/p) '
    return get_answer(msg, 't', 'p')

def get_travel_start_time():
    msg = 'What is your travel start time? (yyyy-mm-dd HH:MM) '
    date_format = '%Y-%m-%d %H:%M'
    while True:
        answer = input(msg)
        try:
            answer_as_date = datetime.strptime(answer, date_format)
            if answer_as_date < MIN_DATE or answer_as_date > MAX_DATE:
                answer_as_date = None
                print(f"Sorry! We don't have data for this date. Try searching for route between {MIN_DATE.strftime('%Y-%m-%d')} - {MAX_DATE.strftime('%Y-%m-%d')}")
        except ValueError:
            answer_as_date = None
            print('Invalid date. Please try again...')

        if answer_as_date is not None:
            return answer_as_date


def get_data_for_new_route():
    is_seatch_single_route = get_single_or_tsp_default_single()

    if is_seatch_single_route:
        return {
            'single_route_param': True,
            'starting_station': get_station(False),
            'destination': get_station(True),
            'dijkstra_alg_param': (d := get_algorithm_default_dijkstra()),
            'time_opt_param': True if d else get_optimalization_parameter_default_time(),
            'travel_start_time': get_travel_start_time()
        }
    else:
        return {
            'single_route_param': False,
            'starting_station': get_station(False),
            'destinations_ids': get_destinations_list(),
            'time_opt_param': get_optimalization_parameter_default_time(),
            'travel_start_time': get_travel_start_time()
        }

if __name__ == '__main__':
    graph = create_graph()

    # cost, previous_route_part = a_star_algorithm(graph, city.LADEK_ZDROJ, city.WROCLAW, datetime(2026, 3, 5, 22, 0), False)       
    # user_route  = get_user_route_from_alg_res(city.LADEK_ZDROJ, city.WROCLAW, (cost, previous_route_part))
    # display_user_route(graph, user_route)


    # Przekroczenie dnia pośrednio
    # best_cost, best_solution = tabu_search_tsp(graph, city.WROCLAW, [city.BIERKOWICE, city.WROCLAW_MUCHOBOR, city.ZAROW, city.LEGNICA, city.GLUSZYCA, city.SWIERKI_DOLNE, city.PRZYBYLOWICE, city.KLODZKO, city.WALBRZYCH_MIASTO], datetime(2026, 3, 1, 16, 0), True)
    # user_route = get_tsp_user_route_from_alg_res(graph, city.WROCLAW, datetime(2026, 3, 1, 16, 0), (best_cost, best_solution), True)
    # display_user_route(graph, user_route)

    # To samo dla przesiadek
    # best_cost, best_solution = tabu_search_tsp(graph, city.WROCLAW, [city.BIERKOWICE, city.WROCLAW_MUCHOBOR, city.ZAROW, city.LEGNICA, city.GLUSZYCA, city.SWIERKI_DOLNE, city.PRZYBYLOWICE, city.KLODZKO, city.WALBRZYCH_MIASTO], datetime(2026, 3, 1, 16, 0), False)
    # user_route = get_tsp_user_route_from_alg_res(graph, city.WROCLAW, datetime(2026, 3, 1, 16, 0), (best_cost, best_solution), False)
    # display_user_route(graph, user_route)

    # while get_new_route(): 
    #     print('Input your route info:')
    #     route_input_data = get_data_for_new_route()
    #     print()

    #     if route_input_data['single_route_param']:

    #         log_debug(f'Searching for: {route_input_data['starting_station']} -> {route_input_data['destination']}; {'d' if route_input_data['dijkstra_alg_param'] else 'a'}, {'t' if route_input_data['time_opt_param'] else 'p'}; {route_input_data['travel_start_time'].strftime('%Y-%m-%d %H:%M')}')
        
    #         if route_input_data['dijkstra_alg_param']:
    #             cost, previous_route_part = dijkstra_algorithm(graph, route_input_data['starting_station'].idx, route_input_data['travel_start_time'])
    #         else:
    #             cost, previous_route_part = a_star_algorithm(graph, route_input_data['starting_station'].idx, route_input_data['destination'].idx, route_input_data['travel_start_time'], route_input_data['time_opt_param'])        
            
    #         user_route  = get_user_route_from_alg_res(route_input_data['starting_station'].idx, route_input_data['destination'].idx, (cost, previous_route_part))
    #         display_user_route(graph, user_route)

    #     else:

    #         log_debug(f'Searching for tsp from: {route_input_data['starting_station']}; {'t' if route_input_data['time_opt_param'] else 'p'}; {route_input_data['travel_start_time'].strftime('%Y-%m-%d %H:%M')}')

    #         best_cost, best_solution = tabu_search_tsp(graph, route_input_data['starting_station'].idx, route_input_data['destinations_ids'], route_input_data['travel_start_time'], route_input_data['time_opt_param'])

    #         user_route = get_tsp_user_route_from_alg_res(graph, route_input_data['starting_station'].idx, route_input_data['travel_start_time'], (best_cost, best_solution), route_input_data['time_opt_param'])
    #         display_user_route(graph, user_route)

    # else:
    #     print('Bye')