"""Ambulance dispatch starter. Run normally to preview calls, or use --dispatch later."""

import argparse
import csv
import math
from pathlib import Path
from time import perf_counter


def read_rows(folder, filename, required_fields):
    """Read a CSV file and check its column names and values."""
    with (folder / filename).open(newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        if not set(required_fields).issubset(reader.fieldnames or []):
            raise ValueError(f'{filename} is missing required columns.')
        rows = list(reader)
    if not rows:
        raise ValueError(f'{filename} has no data.')
    for row in rows:
        for field in required_fields:
            if not row.get(field) or not row[field].strip():
                raise ValueError(f'{filename} has a missing {field}.')
            row[field] = row[field].strip()
    return rows


def load_simulation(folder):
    """Load the ambulances, road network, and calls in priority order."""
    ambulances = read_rows(folder, 'ambulance.csv', ['Ambulance Number', 'Staging Location'])
    priority_rows = read_rows(folder, 'call_priority.csv', ['Call Type', 'Priority'])
    calls = read_rows(folder, 'calls.csv', ['Call ID', 'Location', 'Call Type'])
    roads = read_rows(folder, 'location_network.csv',
                     ['Start', 'End', 'Distance', 'Travel Time', 'Traffic Delay'])

    priorities = {}
    for row in priority_rows:
        priority = int(row['Priority'])
        if priority not in (1, 2, 3) or row['Call Type'] in priorities:
            raise ValueError('Each call type needs one priority from 1 to 3.')
        priorities[row['Call Type']] = priority

    # Each connection keeps its own direction and delay-adjusted travel time.
    network = {}
    for row in roads:
        distance, travel, delay = (float(row[name]) for name in
                                   ['Distance', 'Travel Time', 'Traffic Delay'])
        if any(not math.isfinite(value) or value < 0 for value in (distance, travel, delay)):
            raise ValueError('Road distances, times, and delays must be finite and nonnegative.')
        network.setdefault(row['Start'], [])
        network.setdefault(row['End'], [])
        network[row['Start']].append({'end': row['End'], 'distance': distance,
                                     'time': travel + delay})

    ambulance_numbers = set()
    for ambulance in ambulances:
        number = ambulance['Ambulance Number']
        if number in ambulance_numbers or ambulance['Staging Location'] not in network:
            raise ValueError('Check ambulance numbers and staging locations.')
        ambulance_numbers.add(number)
        ambulance['Current Location'] = ambulance['Staging Location']

    call_ids = set()
    for position, call in enumerate(calls):
        call['Call ID'] = int(call['Call ID'])
        if call['Call ID'] in call_ids:
            raise ValueError('Call IDs must be unique.')
        if call['Call Type'] not in priorities or call['Location'] not in network:
            raise ValueError(f"Call {call['Call ID']} has an unknown type or location.")
        call_ids.add(call['Call ID'])
        call['Priority'] = priorities[call['Call Type']]
        call['Arrival Order'] = position
    calls.sort(key=lambda call: (call['Priority'], call['Arrival Order']))
    return ambulances, network, calls


def find_fastest_route(network, start, destination):
    """Later, return (route as a list of locations, total travel time)."""
    # TODO: Add the second routing algorithm after choosing it.
    # Use each connection's 'time', which already includes its traffic delay.
    # A start equal to the destination should return ([start], 0).
    # If no route exists, return ([], float('inf')).
    raise NotImplementedError('The second routing algorithm has not been chosen yet.')


def dispatch_calls(ambulances, network, calls, log_path):
    """Ready for the routing function; not a finished dispatch prototype yet."""
    total_execution_time = 0.0
    for call in calls:
        best = None
        for ambulance in ambulances:
            start = ambulance['Staging Location']
            # Follow the start / stop / difference pattern in Embedded Counters.
            started = perf_counter()
            route, travel_time = find_fastest_route(network, start, call['Location'])
            total_execution_time += perf_counter() - started
            if not route or not math.isfinite(travel_time):
                continue
            # If times tie, keep the first ambulance listed in the input file.
            if best is None or travel_time < best[0]:
                best = (travel_time, route, ambulance)
        if best is None:
            raise ValueError(f"No ambulance can reach call {call['Call ID']}.")

        travel_time, route, ambulance = best
        ambulance['Current Location'] = call['Location']
        record = {
            'Call ID': call['Call ID'], 'Call Type': call['Call Type'],
            'Call Location': call['Location'],
            'Selected Ambulance': ambulance['Ambulance Number'],
            'Route to Call Location': ' -> '.join(route),
            'Time to the Call Location': travel_time,
        }
        with log_path.open('a', newline='', encoding='utf-8') as file:
            csv.writer(file).writerow(f'{name}={value}' for name, value in record.items())
        ambulance['Current Location'] = ambulance['Staging Location']
    print(f'Total route calculation time: {total_execution_time:.6f} seconds')
    return total_execution_time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).parent / 'data')
    parser.add_argument('--dispatch', action='store_true', help='Use after adding the routing algorithm.')
    parser.add_argument('--log', type=Path, default=Path('/var/log/ambulance_call_log.csv'),
                        help='The assessment log path; override for local testing.')
    args = parser.parse_args()
    try:
        ambulances, network, calls = load_simulation(args.data_dir)
        print(f'Loaded {len(ambulances)} ambulances, {len(network)} locations, and {len(calls)} calls.')
        if args.dispatch:
            dispatch_calls(ambulances, network, calls, args.log)
        else:
            print('First 10 calls in dispatch order:')
            for call in calls[:10]:
                print(f"Call {call['Call ID']}: {call['Call Type']}, priority {call['Priority']}")
            print('Preview only. Choose and add a routing algorithm before dispatching.')
    except (OSError, ValueError, NotImplementedError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()

