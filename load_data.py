from graph import Graph, Node, Edge
import pandas as pd

def create_graph(
        stops_file='stops.txt', 
        stop_times='stop_times.txt', 
        trips_file='trips.txt', 
        routes_file='routes.txt', 
        calendar_file='calendar.txt', 
        calendar_dates_file='calendar_dates.txt'):
    # creating empty graph
    graph = Graph()

    # reading data from stops_file
    stops = pd.read_csv(stops_file)
    stops = stops.set_index('stop_id')

    # adding data about stops to nodes dict in graph
    for row in stops.itertuples():
        if not pd.isna(row.parent_station):
            stop_id = int(row.parent_station)
        else:
            stop_id = row.Index

        graph.add_node(stop_id, Node(stop_id, row.stop_name, row.stop_lat, row.stop_lon)) 

    # reading data from stop_times_file
    stop_times = pd.read_csv(stop_times)
    stop_times['arrival_time'] = pd.to_timedelta(stop_times['arrival_time'])
    stop_times['departure_time'] = pd.to_timedelta(stop_times['departure_time'])

    # reading data from trips_file
    trips = pd.read_csv(trips_file)
    trips = trips.set_index('trip_id')

    # reading data from routes_file
    routes = pd.read_csv(routes_file)
    routes = routes.set_index('route_id')

    # reading data from calendar_file
    calendar = pd.read_csv(calendar_file)
    calendar = calendar.set_index('service_id')
    calendar['start_date'] = pd.to_datetime(calendar['start_date'], format="%Y%m%d")
    calendar['end_date'] = pd.to_datetime(calendar['end_date'], format="%Y%m%d")

    # reading data from calendar_dates_file
    calendar_dates = pd.read_csv(calendar_dates_file)
    calendar_dates['date'] = pd.to_datetime(calendar_dates['date'], format="%Y%m%d").dt.date

    # data nessesary for one travel section
    previus_stop_id = None
    next_stop_id = None
    route_name = ""
    start_date = None
    end_date = None
    weekdays = []
    exceptions = {}
    arrival_time = None
    departure_time = None

    # iterating through stop_times, creating edges and appending them do adj list in graph
    for row in stop_times.itertuples(index=False):
        if row.stop_sequence == 0:
            previus_stop_id = stops.loc[row.stop_id]
            previus_stop_id = int(previus_stop_id['parent_station']) if pd.notna(previus_stop_id['parent_station']) else previus_stop_id.name

            departure_time = row.departure_time

            route = routes.loc[trips.loc[row.trip_id]['route_id']]
            route_name = route['route_short_name'] if not pd.isna(route['route_short_name']) else route['route_long_name']

            service_id = trips.loc[row.trip_id]['service_id']
            operating_time = calendar.loc[service_id]
            start_date = operating_time['start_date']
            end_date = operating_time['end_date']
            weekdays_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            weekdays = [True if operating_time[day] == 1 else False for day in weekdays_names]
            
            route_exceptions = calendar_dates.loc[calendar_dates['service_id'] == service_id]
            if not route_exceptions.empty:
                for row in route_exceptions.itertuples():
                    exceptions[row.date] = row.exception_type
        else:
            next_stop_id = stops.loc[row.stop_id]
            next_stop_id = int(next_stop_id['parent_station']) if pd.notna(next_stop_id['parent_station']) else next_stop_id.name

            arrival_time = row.arrival_time

            edge = Edge(departure_time, arrival_time, route_name, start_date, end_date, weekdays, exceptions)

            graph.add_edge(previus_stop_id, next_stop_id, edge)

            previus_stop_id = next_stop_id
            departure_time = row.departure_time

    return graph
