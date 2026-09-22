import csv
import importlib
from pathlib import Path
import sys
from unittest.mock import patch

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
tmp = root / '.draft_qa' / 'code_checks'
for name in ['FirstAlgorithm', 'SecondAlgorithm']:
    module = importlib.import_module(name)
    ambulances, network, calls = module.load_simulation(root / 'data')
    assert (len(ambulances), len(network), len(calls)) == (3, 7, 100)
    assert sum(map(len, network.values())) == 42
    for priority in (1, 2, 3):
        positions = [c['Arrival Order'] for c in calls if c['Priority'] == priority]
        assert positions == sorted(positions)
    assert [c['Priority'] for c in calls] == sorted(c['Priority'] for c in calls)
    assert next(e['time'] for e in network['Intersection B'] if e['end'] == 'Address 456 Oak St') == 3.16
    assert next(e['time'] for e in network['Address 456 Oak St'] if e['end'] == 'Intersection B') == 3.52
    try:
        module.find_fastest_route(network, 'Intersection A', 'Intersection B')
    except NotImplementedError:
        pass
    else:
        raise AssertionError('An undecided algorithm must not produce a route.')
    log = tmp / (name + '.csv')
    log.write_text('')
    # Controlled routes test the surrounding logic, not algorithm performance.
    def fake_route(graph, start, end):
        times = {'Intersection A': 8, 'Intersection C': 2, 'Address 123 Main St': 5}
        return [start, end], times[start]
    with patch.object(module, 'find_fastest_route', side_effect=fake_route) as route:
        with patch.object(module, 'perf_counter', side_effect=range(12)):
            assert module.dispatch_calls(ambulances, network, calls[:2], log) == 6
        assert route.call_count == 6
    with log.open(newline='') as file: rows = list(csv.reader(file))
    assert len(rows) == 2 and all(len(row) == 6 for row in rows)
    assert all('Selected Ambulance=Ambulance 2' in row for row in rows)
    assert all(a['Current Location'] == a['Staging Location'] for a in ambulances)
    with patch.object(module, 'find_fastest_route', return_value=([], float('inf'))):
        try:
            module.dispatch_calls(ambulances, network, calls[:1], log)
        except ValueError:
            pass
        else:
            raise AssertionError('Unreachable calls must fail clearly.')
    with log.open(newline='') as file: assert len(list(csv.reader(file))) == 2
    for source in (root / 'data').glob('*.csv'):
        (tmp / source.name).write_bytes(source.read_bytes())
    with (tmp / 'calls.csv').open('a') as file:
        file.write('101,Missing Location,Stroke\n')
    try:
        module.load_simulation(tmp)
    except ValueError:
        pass
    else:
        raise AssertionError('Unknown locations must be rejected.')
    print(name + ': data, priority order, direction, selection, timing, logging, reset, and validation passed.')
