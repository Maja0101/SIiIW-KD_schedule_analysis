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