from datetime import datetime

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
        answer = input(msg)
        # serach for station
        return answer
    
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
    starting_station = get_station(False)
    destination = get_station(True)
    time_opt_param = get_optimalization_parameter_time()
    travel_start_time = get_travel_start_time()

    print(f'Searching for: {starting_station} -> {destination}; {'t' if time_opt_param else 'p'}; {travel_start_time.strftime('%Y-%m-%d %H:%M')}')

if __name__ == '__main__':
    if get_new_route(): 
        print('Input your route info:')
        get_data_for_new_route()
    else:
        print('bye')