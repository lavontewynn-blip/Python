from pathlib import Path
from docx import Document

root = Path(__file__).resolve().parent.parent
for filename in ('FirstAlgorithm.py', 'SecondAlgorithm.py'):
    path = root / filename
    text = path.read_text(encoding='utf-8')
    text = text.replace('The default log is', '''Beginner reading guide:
    1. main() chooses the data folder and starts the simulation.
    2. load_simulation() reads the files and sorts the calls.
    3. dispatch_calls() compares ambulances for each call.
    4. find_fastest_route() searches the roads for the lowest total time.
    5. build_route() turns saved previous locations into a route list.

Here, "shortest path" means the least travel time, including traffic delay.
It does not mean the fewest roads or the smallest physical distance.
Only Python's standard library is needed; no extra packages are required.

The default log is''')
    marker = '\ndef find_fastest_route(network, start, destination):'
    helper = '''
def build_route(previous_locations, destination):
    """Follow the saved previous locations to rebuild the route in order."""
    # Example: if C came from B and B came from A, we collect C, B, A.
    # Reversing that list gives the driving route A, B, C.
    route = []
    location = destination
    while location is not None:
        route.append(location)
        location = previous_locations[location]
    route.reverse()
    return route

'''
    text = text.replace(marker, helper + marker)
    old = '''            # Follow the saved links backward: destination -> ... -> start.
            route = []
            location = destination
            while location is not None:
                route.append(location)
                location = previous_locations[location]
            route.reverse()  # Show the route in driving order instead.
            return route, current_time'''
    text = text.replace(old, '''            route = build_route(previous_locations, destination)
            return route, current_time''')
    text = text.replace("    calls.sort(key=dispatch_order)", "    # Example: priority 1 rows 4 and 9 are handled before priority 2 row 0.\n    # This call ordering is separate from the heap used to choose roads.\n    calls.sort(key=dispatch_order)")
    text = text.replace("            new_time = current_time + road['time']", "            # Example: 4 units to get here + 3 on this road = 7 to the neighbor.\n            new_time = current_time + road['time']")
    text = text.replace("    # This property is called", "    # Example: outgoing times of 3 and 8 give an estimate of 3.\n    # Even a route with several roads must pay at least that first-road cost.\n    # This property is called")
    text = text.replace("    # f = estimated total travel time through this location.", "    # f = estimated total travel time through this location.\n    # Example: g = 4 and h = 3 give f = 7 for queue ordering.\n    # The returned driving time uses g only; h is never added to the result.")
    path.write_text(text, encoding='utf-8')

path = root / 'Ambulance Dispatch Application.docx'
doc = Document(path)
updates = {
13: "I built two Python programs that simulate dispatching ambulances to emergency calls. FirstAlgorithm.py uses Dijkstra's algorithm, and SecondAlgorithm.py uses A*. Both find the shortest path by total travel time, including traffic delay, rather than by physical distance. When I run either program, main() loads the simulation and dispatch_calls() processes the calls one at a time. For each call, the program compares routes from every ambulance's staging location and selects the ambulance with the lowest travel time. Ties keep the first ambulance listed in ambulance.csv. The program prints the assignment, appends the dispatch record to the log, and resets the selected ambulance to its staging location. The simulation does not wait for driving or treatment to finish.",
15: "Both programs use load_simulation() and Python's csv module to read four CSV files from the data folder beside the scripts, or from a folder selected with --data-dir. The ambulance.csv file supplies ambulance numbers and staging locations. The call_priority.csv file maps call types to priorities, and calls.csv supplies call IDs, locations, and types. The location_network.csv file becomes a directed graph stored as a dictionary of outgoing road lists. A Start-to-End road does not automatically allow travel in reverse. Each road stores its destination, distance, and the sum of Travel Time and Traffic Delay. Routing minimizes that sum; distance is stored but does not determine the route. The loader checks required values, nonnegative finite road numbers, duplicate identifiers, priority values, call types, and locations before dispatch begins.",
17: "Both programs assign each call the priority associated with its call type in call_priority.csv. Priority 1 calls are processed first, followed by priority 2 and then priority 3. Because calls.csv has no arrival timestamps, the program records each call's original row position as its arrival order. dispatch_order() supplies the priority and arrival order to sort(), keeping calls with the same priority in the order received. All calls are loaded and sorted before dispatch starts. This call ordering is separate from the routing priority queue, which chooses the next road-network location to explore.",
19: "In FirstAlgorithm.py, find_fastest_route() uses Dijkstra's algorithm. The start location has a best known travel time of zero, and other locations begin at infinity, meaning no route has been found. A heap-based priority queue selects the location with the lowest known travel time. The algorithm checks each outgoing road and updates a neighbor's time and previous location when it finds a faster route. Older queue entries are skipped if a faster route has already been recorded. With nonnegative road times, the destination's time is optimal when it is removed from the queue. build_route() follows the saved previous locations backward and reverses the list to return the route in driving order. dispatch_calls() uses this route calculation for every ambulance and call.",
21: "In SecondAlgorithm.py, find_fastest_route() uses A* to order the queue by f = g + h. Here, g is the actual travel time so far and h estimates the remaining time. Since the CSV has no coordinates, estimate_remaining_times() uses the cheapest outgoing road time at each location, with zero at the destination and at dead ends. Any route to a different location must first take an outgoing road, so this estimate cannot exceed the true remaining time. A* updates improved times and previous locations, then uses build_route() to reconstruct the path. Its returned travel time is g, without adding the estimate. This simple heuristic may not make A* faster than Dijkstra. Both programs return zero time when the ambulance is already at the call, skip ambulances without a reachable route, and stop with an error if none can reach the call.",
}
for index, text in updates.items():
    paragraph = doc.paragraphs[index]
    paragraph.runs[0].text = text
    for run in paragraph.runs[1:]:
        run.text = ''
doc.save(path)
print('Updated both scripts and the document.')
