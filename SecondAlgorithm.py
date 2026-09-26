"""Ambulance dispatch using A*.

Start reading at main() below. Both files follow the same design:
    load the files -> sort calls -> compare ambulances -> log -> reset.
Only the route-search section differs between the two programs.

Run all calls:  python SecondAlgorithm.py
Preview only:  python SecondAlgorithm.py --preview
See BEGINNER_GUIDE.md for examples and a map to the application design.
"""

import argparse  # Optional command-line settings, such as --preview.
import csv       # Read input rows and write dispatch records.
import heapq     # A queue that gives us the smallest value first.
import math      # Check whether a number is finite.
from pathlib import Path  # File paths that work on Windows and Linux.
from time import perf_counter  # Measure computer calculation time.


# 1. START HERE: run the application

def main():
    """Read settings, load the data, and preview or dispatch calls."""
    # __file__ is this Python file. Its parent is the folder containing it.
    # This finds data even when you run the script from a different folder.
    data_folder = Path(__file__).parent / 'data'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=data_folder,
                        help='Folder containing the four simulation CSV files.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--preview', action='store_true',
                      help='Show the first 10 calls without dispatching.')
    # Keep --dispatch working for anyone using the earlier command.
    mode.add_argument('--dispatch', action='store_true',
                      help='Dispatch all calls (also the default behavior).')
    parser.add_argument('--log', type=Path,
                        default=Path(__file__).parent / 'ambulance_call_log.csv',
                        help='Log file path. Defaults to ambulance_call_log.csv beside this script.')
    args = parser.parse_args()

    # Report input or file errors in plain text instead of a long traceback.
    try:
        ambulances, network, calls = load_simulation(args.data_dir)
        print(f'Loaded {len(ambulances)} ambulances, {len(network)} locations, '
              f'and {len(calls)} calls.')

        if not args.preview:
            # Create the output folder if a custom log path needs one.
            args.log.parent.mkdir(parents=True, exist_ok=True)
            dispatch_calls(ambulances, network, calls, args.log)
            print(f'Completed {len(calls)} simulated dispatches.')
            print(f'Log saved to: {args.log.resolve()}')
        else:
            print('First 10 calls in dispatch order:')
            # [:10] takes up to the first 10 items in the list.
            for call in calls[:10]:
                print(f"Call {call['Call ID']}: {call['Call Type']}, "
                      f"priority {call['Priority']}")
            print('Preview only. Run without --preview to dispatch all calls.')
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')

# 2. DISPATCH: choose an ambulance for each call

def dispatch_calls(ambulances, network, calls, log_path):
    """Compare fastest routes and log each ambulance assignment."""
    total_execution_time = 0.0

    # 1. Take the next call from the already sorted list.
    for call in calls:
        # Reset the best choice for each new call.
        selected_ambulance = None  # None means no ambulance chosen yet.
        best_route = []
        best_travel_time = float('inf')

        # 2. Compare the route from every ambulance staging location.
        for ambulance in ambulances:
            # The design starts every route at the ambulance's staging location.
            start = ambulance['Staging Location']

            # Measure computer calculation time, not simulated driving time.
            start_time = perf_counter()
            route, travel_time = find_fastest_route(network, start, call['Location'])
            stop_time = perf_counter()
            total_execution_time += stop_time - start_time

            # Skip an ambulance if it cannot reach the call.
            if not route or not math.isfinite(travel_time):
                continue

            # A strictly smaller time wins. On a tie, keep the first ambulance.
            if travel_time < best_travel_time:
                selected_ambulance = ambulance
                best_route = route
                best_travel_time = travel_time

        if selected_ambulance is None:
            raise ValueError(f"No ambulance can reach call {call['Call ID']}.")

        # 3. Move the chosen ambulance to the call and record the result.
        selected_ambulance['Current Location'] = call['Location']
        log_dispatch(call, selected_ambulance, best_route, best_travel_time, log_path)

        # 4. Reset immediately so the ambulance is ready for the next call.
        selected_ambulance['Current Location'] = selected_ambulance['Staging Location']

    print(f'Total route calculation time: {total_execution_time:.6f} seconds')
    return total_execution_time

# 3. ROUTE SEARCH: A*

def find_fastest_route(network, start, destination):
    """Use A* to return the fastest route and its actual travel time."""
    # Both algorithms minimize travel time INCLUDING traffic delay.
    # The loader checks that all road times are nonnegative.
    if start not in network or destination not in network:
        raise ValueError('The start and destination must exist in the network.')
    if start == destination:
        return [start], 0.0  # The ambulance is already at the call.

    # Infinity means we have not found a route to this location yet.
    best_times = {}
    previous_locations = {}
    for location in network:
        best_times[location] = float('inf')
        previous_locations[location] = None
    best_times[start] = 0.0

    # A* ranks locations using f = g + h:
    # g = actual travel time from the start to the current location.
    # h = estimated travel time still needed to reach the destination.
    # f = estimated total travel time through this location.
    # Example: g = 4 and h = 3 give f = 7 for queue ordering.
    # The returned driving time uses g only; h is never added to the result.
    # This setup happens inside the routing function, so the timer includes it.
    estimates = estimate_remaining_times(network, destination)

    # A heap removes the entry with the smallest estimated total first.
    # Each entry stores (estimated total, actual time so far, location).
    waiting = []
    heapq.heappush(waiting, (estimates[start], 0.0, start))

    while waiting:
        estimated_total, current_time, current_location = heapq.heappop(waiting)

        # Another route may have improved this location since it was queued.
        if current_time > best_times[current_location]:
            continue

        # Our estimate never overstates the remaining time and is zero at
        # the goal. Thus the goal removed from the queue has an optimal route.
        if current_location == destination:
            route = build_route(previous_locations, destination)
            return route, current_time

        for road in network[current_location]:
            neighbor = road['end']
            # Example: 4 units to get here + 3 on this road = 7 to the neighbor.
            new_time = current_time + road['time']  # The new g value.

            if new_time < best_times[neighbor]:
                best_times[neighbor] = new_time
                previous_locations[neighbor] = current_location
                estimated_total = new_time + estimates[neighbor]  # g + h
                heapq.heappush(waiting, (estimated_total, new_time, neighbor))

    # Never return an estimated time as the driving time. If no route exists,
    # report an empty route and infinity so dispatch can skip this ambulance.
    return [], float('inf')


def estimate_remaining_times(network, destination):
    """Build a simple, safe travel-time estimate (called a heuristic)."""
    # The CSV has no coordinates, so we cannot use straight-line distances.
    # Instead, use the cheapest outgoing road time at each location.
    # Any route to a DIFFERENT location must use an outgoing road first.
    # Therefore this estimate cannot exceed the actual remaining route time.
    # Example: outgoing times of 3 and 8 give an estimate of 3.
    # Even a route with several roads must pay at least that first-road cost.
    # This property is called "admissibility" and keeps A*'s answer optimal.
    estimates = {}
    for location in network:
        estimates[location] = 0.0
        if location == destination:
            continue  # No travel remains once we reach the destination.

        cheapest_time = float('inf')
        for road in network[location]:
            if road['time'] < cheapest_time:
                cheapest_time = road['time']

        # Keep zero at dead ends; the search will find no outgoing roads there.
        if cheapest_time != float('inf'):
            estimates[location] = cheapest_time

    # This is a weak estimate, so A* is not guaranteed to beat Dijkstra.
    # If all estimates are zero, A* explores like Dijkstra.
    return estimates


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

# 4. INPUT: load the files and put calls in priority order

def load_simulation(folder):
    """Load and check the four simulation files described in the design."""
    ambulances = read_rows(folder, 'ambulance.csv',
                          ['Ambulance Number', 'Staging Location'])
    priority_rows = read_rows(folder, 'call_priority.csv',
                             ['Call Type', 'Priority'])
    calls = read_rows(folder, 'calls.csv',
                      ['Call ID', 'Location', 'Call Type'])
    roads = read_rows(folder, 'location_network.csv',
                      ['Start', 'End', 'Distance', 'Travel Time', 'Traffic Delay'])

    # Step 1: Make a lookup table: call type -> priority number.
    priorities = {}
    for row in priority_rows:
        call_type = row['Call Type']
        priority = int(row['Priority'])  # CSV values start as text.
        if priority not in (1, 2, 3):
            raise ValueError('Each priority must be 1, 2, or 3.')
        if call_type in priorities:
            raise ValueError(f'Duplicate call type: {call_type}')
        priorities[call_type] = priority

    # Step 2: Build a directed graph: location -> list of outgoing roads.
    # "Directed" means Start -> End does not automatically allow End -> Start.
    network = {}
    for row in roads:
        start = row['Start']
        end = row['End']
        distance = read_nonnegative_number(row, 'Distance')
        travel_time = read_nonnegative_number(row, 'Travel Time')
        traffic_delay = read_nonnegative_number(row, 'Traffic Delay')
        total_time = travel_time + traffic_delay
        if not math.isfinite(total_time):
            raise ValueError('Travel time plus traffic delay is too large.')

        if start not in network:
            network[start] = []
        if end not in network:
            network[end] = []

        road = {'end': end, 'distance': distance, 'time': total_time}
        network[start].append(road)
        # Keep distance to match the design; routing will minimize TIME.
        # The stored time already includes delay. Do not add delay again.

    # Step 3: Check ambulances and place each one at its staging location.
    ambulance_numbers = set()  # A set remembers unique values.
    for ambulance in ambulances:
        number = ambulance['Ambulance Number']
        staging_location = ambulance['Staging Location']
        if number in ambulance_numbers:
            raise ValueError(f'Duplicate ambulance number: {number}')
        if staging_location not in network:
            raise ValueError(f'Unknown staging location: {staging_location}')
        ambulance_numbers.add(number)
        ambulance['Current Location'] = staging_location

    # Step 4: Add each call's priority and original position in the file.
    call_ids = set()
    # enumerate() supplies both a row number (starting at 0) and the row.
    for position, call in enumerate(calls):
        call_id = int(call['Call ID'])
        if call_id in call_ids:
            raise ValueError(f'Duplicate call ID: {call_id}')
        if call['Call Type'] not in priorities:
            raise ValueError(f'Call {call_id} has an unknown call type.')
        if call['Location'] not in network:
            raise ValueError(f'Call {call_id} has an unknown location.')

        call_ids.add(call_id)
        call['Call ID'] = call_id
        call['Priority'] = priorities[call['Call Type']]
        call['Arrival Order'] = position

    # There are no arrival timestamps, so file order represents arrival order.
    # All priority 1 calls come first, then priority 2, then priority 3.
    # Example: priority 1 rows 4 and 9 are handled before priority 2 row 0.
    # This call ordering is separate from the heap used to choose roads.
    calls.sort(key=dispatch_order)
    return ambulances, network, calls


def dispatch_order(call):
    """Give sort() the two values used to put calls in order."""
    # Python compares priority first, then original row position for ties.
    return (call['Priority'], call['Arrival Order'])

# 5. SUPPORT: validate input and record output

def read_rows(folder, filename, required_fields):
    """Read a CSV into a list of dictionaries and check required values."""
    # A dictionary stores named values, such as row['Call Type'].
    # A list stores multiple rows in their original file order.
    file_path = folder / filename
    with file_path.open(newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        column_names = reader.fieldnames
        if column_names is None:
            raise ValueError(f'{filename} is empty.')

        for field in required_fields:
            if field not in column_names:
                raise ValueError(f'{filename} is missing the {field} column.')

        rows = []
        for row in reader:
            for field in required_fields:
                value = row.get(field)
                if value is None or value.strip() == '':
                    raise ValueError(f'{filename} has a missing {field}.')
                # strip() removes extra spaces before and after a value.
                row[field] = value.strip()
            rows.append(row)

    # The file closes automatically when the 'with' block ends.
    if len(rows) == 0:
        raise ValueError(f'{filename} has no data rows.')
    return rows


def read_nonnegative_number(row, field):
    """Convert road data from text to a number that is zero or greater."""
    number = float(row[field])
    if not math.isfinite(number) or number < 0:
        raise ValueError(f'{field} must be a finite number that is zero or greater.')
    return number


def log_dispatch(call, selected_ambulance, best_route, best_travel_time, log_path):
    """Append one dispatch record and display it on the screen."""
    record = {
        'Call ID': call['Call ID'],
        'Call Type': call['Call Type'],
        'Call Location': call['Location'],
        'Selected Ambulance': selected_ambulance['Ambulance Number'],
        'Route to Call Location': ' -> '.join(best_route),
        'Time to the Call Location': best_travel_time,
    }

    # Keep the existing log format: one row with named fields per call.
    # 'a' means append, so earlier log entries are kept.
    log_fields = []
    for name, value in record.items():
        log_fields.append(f'{name}={value}')
    with log_path.open('a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(log_fields)

    # Show the assignment so the simulation's progress is visible.
    print(f"Call {call['Call ID']} (priority {call['Priority']}): "
          f"{selected_ambulance['Ambulance Number']} -> {call['Location']}")
    print(f"  Route: {' -> '.join(best_route)}")
    print(f"  Travel time including traffic: {best_travel_time:.2f}")


# Python defines the functions above first, then starts main() here.
if __name__ == "__main__":
    main()
