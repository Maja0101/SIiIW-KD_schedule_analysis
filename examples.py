from datetime import datetime
from load_data import create_graph
from algorithms import dijkstra_algorithm, a_star_algorithm
from tabu import tabu_search_tsp
from user_route import display_user_route, get_user_route_from_alg_res, get_tsp_user_route_from_alg_res
import city_definition as city


if __name__ == "__main__":
    graph = create_graph()

    #Dijkstra time 
    cost, previous_route_part = dijkstra_algorithm(graph, city.TANVALD_ZASTAVKA, datetime(2026, 3, 6, 4, 40))
    user_route  = get_user_route_from_alg_res(city.TANVALD_ZASTAVKA, city.LOBAU_SACHS, (cost, previous_route_part))
    display_user_route(graph, user_route)

    # Dijkstra transfers 
    cost, previous_route_part = dijkstra_algorithm(graph, city.TANVALD_ZASTAVKA, datetime(2026, 3, 6, 4, 40), False)
    user_route  = get_user_route_from_alg_res(city.TANVALD_ZASTAVKA, city.LOBAU_SACHS, (cost, previous_route_part))
    display_user_route(graph, user_route)

    #A* time 
    cost, previous_route_part = a_star_algorithm(graph, city.TANVALD_ZASTAVKA, city.LOBAU_SACHS, datetime(2026, 3, 6, 4, 40))
    user_route  = get_user_route_from_alg_res(city.TANVALD_ZASTAVKA, city.LOBAU_SACHS, (cost, previous_route_part))
    display_user_route(graph, user_route)

    # A* transfers 
    cost, previous_route_part = a_star_algorithm(graph, city.TANVALD_ZASTAVKA, city.LOBAU_SACHS, datetime(2026, 3, 6, 4, 40), False)
    user_route  = get_user_route_from_alg_res(city.TANVALD_ZASTAVKA, city.LOBAU_SACHS, (cost, previous_route_part))
    display_user_route(graph, user_route)

	# Passing midnight directly
    cost, previous_route_part = a_star_algorithm(graph, city.BOJANOWO, city.RAWICZ, datetime(2026, 3, 6, 23, 40))
    user_route  = get_user_route_from_alg_res(city.BOJANOWO, city.RAWICZ, (cost, previous_route_part))
    display_user_route(graph, user_route)
	
	# Passing midnight indirectly / visible difference between time and transits
    best_cost, best_solution = tabu_search_tsp(graph, city.WROCLAW, [city.BIERKOWICE, city.WROCLAW_MUCHOBOR, city.ZAROW, city.LEGNICA, city.GLUSZYCA, city.SWIERKI_DOLNE, city.PRZYBYLOWICE, city.KLODZKO, city.WALBRZYCH_MIASTO], datetime(2026, 3, 1, 16, 0), True)
    user_route = get_tsp_user_route_from_alg_res(graph, city.WROCLAW, datetime(2026, 3, 1, 16, 0), (best_cost, best_solution), True)
    display_user_route(graph, user_route)

    # Passing midnight indirectly (for transits) / visible difference between time and transits
    best_cost, best_solution = tabu_search_tsp(graph, city.WROCLAW, [city.BIERKOWICE, city.WROCLAW_MUCHOBOR, city.ZAROW, city.LEGNICA, city.GLUSZYCA, city.SWIERKI_DOLNE, city.PRZYBYLOWICE, city.KLODZKO, city.WALBRZYCH_MIASTO], datetime(2026, 3, 1, 16, 0), False)
    user_route = get_tsp_user_route_from_alg_res(graph, city.WROCLAW, datetime(2026, 3, 1, 16, 0), (best_cost, best_solution), False)
    display_user_route(graph, user_route)