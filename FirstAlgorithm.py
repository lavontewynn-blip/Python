"""Ambulance dispatch prototype: first routing algorithm is not added yet.

Run this file to preview the first 10 calls in priority order:
    python FirstAlgorithm.py

After implementing find_fastest_route(), run the dispatch simulation:
    python FirstAlgorithm.py --dispatch

The design uses /var/log/ambulance_call_log.csv for the log. For Windows
practice, choose a local file instead:
    python FirstAlgorithm.py --dispatch --log ambulance_call_log.csv
"""

import argparse  # Reads optional settings typed after the script name.
import csv       # Reads and writes comma-separated value (CSV) files.
import math      # Checks for invalid numbers such as infinity.
from pathlib import Path  # Builds file paths on Windows or Linux.
from time import perf_counter  # Measures elapsed time in seconds.


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


def dispatch_order(call):
    """Give sort() the two values used to put calls in order."""
    # Python compares priority first, then original row position for ties.
    return (call['Priority'], call['Arrival Order'])


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
    calls.sort(key=dispatch_order)
    return ambulances, network, calls


def find_fastest_route(network, start, destination):
    """Placeholder for the first routing algorithm, as stated in the design."""
    # TODO: Choose and implement the first algorithm here.
    # network[start] gives the roads leaving the starting location.
    # Each road has an 'end', a 'distance', and a delay-adjusted 'time'.
    # Return two values: the route (a list of locations) and total travel time.
    # If start == destination, return ([start], 0).
    # If no route exists, return ([], float('inf')). Infinity means unreachable.
    raise NotImplementedError('The first routing algorithm has not been chosen yet.')


def dispatch_calls(ambulances, network, calls, log_path):
    """Compare routes and log each assignment once routing is implemented."""
    total_execution_time = 0.0

    for call in calls:
        # Reset the best choice for each new call.
        selected_ambulance = None  # None means no ambulance chosen yet.
        best_route = []
        best_travel_time = float('inf')

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

        # Simulate arrival, record the assignment, then reset for the next call.
        selected_ambulance['Current Location'] = call['Location']
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

        selected_ambulance['Current Location'] = selected_ambulance['Staging Location']

    print(f'Total route calculation time: {total_execution_time:.6f} seconds')
    return total_execution_time


def main():
    """Read settings, load the data, and preview or dispatch calls."""
    # __file__ is this Python file. Its parent is the folder containing it.
    # This finds data even when you run the script from a different folder.
    data_folder = Path(__file__).parent / 'data'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=data_folder,
                        help='Folder containing the four simulation CSV files.')
    parser.add_argument('--dispatch', action='store_true',
                        help='Run dispatch after implementing the routing algorithm.')
    parser.add_argument('--log', type=Path,
                        default=Path('/var/log/ambulance_call_log.csv'),
                        help='Log file path. Use a local path for Windows practice.')
    args = parser.parse_args()

    # Report input or file errors in plain text instead of a long traceback.
    try:
        ambulances, network, calls = load_simulation(args.data_dir)
        print(f'Loaded {len(ambulances)} ambulances, {len(network)} locations, '
              f'and {len(calls)} calls.')

        if args.dispatch:
            dispatch_calls(ambulances, network, calls, args.log)
        else:
            print('First 10 calls in dispatch order:')
            # [:10] takes up to the first 10 items in the list.
            for call in calls[:10]:
                print(f"Call {call['Call ID']}: {call['Call Type']}, "
                      f"priority {call['Priority']}")
            print('Preview only. Choose and add a routing algorithm before dispatching.')
    except (OSError, ValueError, NotImplementedError) as error:
        parser.exit(1, f'{error}\n')


# Start here when running this file directly. Importing it does not run main().
if __name__ == '__main__':
    main()
