import contextlib
import csv
import importlib.util
import io
import math
from pathlib import Path

root = Path(__file__).resolve().parent.parent
modules = []
for filename in ('FirstAlgorithm.py', 'SecondAlgorithm.py'):
    spec = importlib.util.spec_from_file_location(filename[:-3], root / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    modules.append(module)

ambulances, network, calls = modules[0].load_simulation(root / 'data')
# Floyd-Warshall is an independent reference for all pairs of locations.
costs = {(a, b): (0 if a == b else math.inf) for a in network for b in network}
for a, roads in network.items():
    for road in roads:
        costs[a, road['end']] = min(costs[a, road['end']], road['time'])
for k in network:
    for a in network:
        for b in network:
            costs[a, b] = min(costs[a, b], costs[a, k] + costs[k, b])
for module in modules:
    for a in network:
        for b in network:
            route, time = module.find_fastest_route(network, a, b)
            assert math.isclose(time, costs[a, b])
            assert route[0] == a and route[-1] == b
            actual = sum(min(r['time'] for r in network[x] if r['end'] == y)
                         for x, y in zip(route, route[1:]))
            assert math.isclose(actual, time)
    edge_case = {'A': [{'end': 'B', 'time': 0}],
                 'B': [{'end': 'A', 'time': 0}], 'C': []}
    assert module.find_fastest_route(edge_case, 'A', 'B') == (['A', 'B'], 0)
    assert module.find_fastest_route(edge_case, 'A', 'C') == ([], math.inf)
    ambulances, graph, calls = module.load_simulation(root / 'data')
    assert calls == sorted(calls, key=lambda c: (c['Priority'], c['Arrival Order']))
    output = root / '.work' / (module.__name__ + '_test_log.csv')
    output.write_text('')
    with contextlib.redirect_stdout(io.StringIO()):
        module.dispatch_calls(ambulances, graph, calls, output)
    with output.open(newline='') as stream:
        assert len(list(csv.reader(stream))) == 100
    assert all(a['Current Location'] == a['Staging Location'] for a in ambulances)
    print(module.__name__, ': 49 shortest paths, edge cases, and 100 dispatches passed')
