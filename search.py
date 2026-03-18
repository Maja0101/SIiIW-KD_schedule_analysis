from datetime import datetime
from load_data import create_graph
from algorithms import dijkstra_algorithm, a_star_algorithm, user_route, display_user_route

graph = create_graph()

MIN_DATE = datetime(2026, 3, 3, 0, 0)
MAX_DATE = datetime(2026, 12, 12, 23, 59)

def get_new_route():
    msg = 'Do you want to search for new route? (y/n) '
    while True:
        answer = input(msg).lower()
        if answer == 'y':
            return True
        elif answer == 'n':
            return False
        print('Unknown value. Please try again...')

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
        print("Unknown station. Please try again...")

    
def get_optimalization_parameter_time():
    msg = 'What do you want to optimize the route based on time (t) or the number of transfers (p)? (t/p) '
    while True:
        answer = input(msg).lower()
        if answer == 't':
            return True
        elif answer == 'p':
            return False
        print('Unknown value. Please try again...')

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
    return {
        'starting_station': get_station(False),
        'destination': get_station(True),
        'time_opt_param': get_optimalization_parameter_time(),
        'travel_start_time': get_travel_start_time()
    }

if __name__ == '__main__':
    # if get_new_route(): 
        # print('Input your route info:')
        # route_input_data = get_data_for_new_route()
        # print(f'Searching for: {route_input_data['starting_station']} -> {route_input_data['destination']}; {'t' if route_input_data['time_opt_param'] else 'p'}; {route_input_data['travel_start_time'].strftime('%Y-%m-%d %H:%M')}')
        # cost, previous_route_part = dijkstra_algorithm(graph, route_input_data['starting_station'].idx, route_input_data['travel_start_time'])
        # cost, previous_route_part = dijkstra_algorithm(graph, 1413209, datetime(2026, 3, 21, 13, 25)) # ladek
        # cost, previous_route_part = dijkstra_algorithm(graph, 1413209, datetime(2026, 3, 6, 13, 25))
        cost, previous_route_part = a_star_algorithm(graph, 1413209, 1413356, datetime(2026, 3, 6, 13, 25))
        # print(cost[1413380])
        # print(cost[1413386])
        # print(previous_route_part[1413380])
        # print(previous_route_part[1413386])
        
        # user_route  = user_route(1413209, 1413355, (cost, previous_route_part)) # ladek -> trzeb ieszowice - nie znajduje
        user_route  = user_route(1413209, 1413356, (cost, previous_route_part))
        display_user_route(graph, user_route)
    # else:
    #     print('Bye')