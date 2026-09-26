# Understanding the ambulance dispatch programs

Both files run the same ambulance simulation. You run one file at a time. The difference is how they search for a route:

| File | Route algorithm | Which location does it explore next? |
| --- | --- | --- |
| `FirstAlgorithm.py` | Dijkstra | The one with the lowest travel time found so far. |
| `SecondAlgorithm.py` | A* (say “A star”) | The one with the lowest time so far plus an estimate of the remaining time. |

Both choose the fastest route **including traffic delay**. Physical distance does not decide the winner. A* is not guaranteed to run faster with this dataset's simple estimate.

## Start with a preview

Open a terminal in this folder and run:

```powershell
python FirstAlgorithm.py --preview
python SecondAlgorithm.py --preview
```

These commands load the files and show the first 10 calls in priority order. They do not dispatch or write a log.

To run the complete simulations and keep their results separate:

```powershell
python FirstAlgorithm.py --log dijkstra_log.csv
python SecondAlgorithm.py --log astar_log.csv
```

Running without options also dispatches all calls, but both programs then append to `ambulance_call_log.csv`. Running again adds another set of records; it does not replace earlier records.

The default inputs are in the `data` folder, as specified in the application design. The copies beside the scripts currently match those files. To explicitly use the copies beside the scripts, add `--data-dir .` when running from this folder.

## Read the code in this order

The files now have the same five numbered sections. Start at section 1, `main()`. Python first reads the function definitions, then the last two lines call `main()` to begin the work. A function is a named group of steps; defining it does not run it.

1. **`main()` starts the program.** It reads optional settings, calls `load_simulation()`, and either shows a preview or starts dispatching.
2. **`dispatch_calls()` handles one call at a time.** For each call, it checks every ambulance, keeps the fastest reachable choice, records the result, and resets that ambulance.
3. **`find_fastest_route()` answers one question:** “What is the fastest route from this ambulance's staging location to this call?” It returns two results: a list of locations and the total travel time.
4. **`load_simulation()` prepares the data.** Read this after you understand the dispatch loop. It loads and validates the four input files and sorts the calls.
5. **The support functions handle details.** `read_rows()` reads CSV rows, `read_nonnegative_number()` checks road numbers, and `log_dispatch()` writes and prints an assignment.

The support code remains in each file so that either program can run independently.

## Follow one call

Imagine a call at location C, and two ambulances staged at A and B. These are teaching values, not rows from the supplied files.

- From A, the fastest route takes 8 time units including traffic.
- From B, the fastest route takes 5 time units including traffic.
- The program selects the ambulance at B, prints and logs the route, then resets it to B.

The program does not actually wait 5 time units. It changes the ambulance's stored location to represent arrival and then resets it immediately. If the two times are equal, the first ambulance in `ambulance.csv` wins. If one cannot reach the call, it is skipped. If none can reach it, the program stops with an error.

## Understand the route search

A **graph** represents the road network. Locations are its points, and roads connect them. Roads are directed: a row from A to B permits that direction only. A reverse trip needs its own road entry.

For each road, the loader adds `Travel Time + Traffic Delay` once. For example, a road with travel time 4 and delay 2 costs 6. The route search adds these road costs together.

Both algorithms use these variables:

| Variable | Meaning |
| --- | --- |
| `best_times` | Fastest time found so far to each location. |
| `previous_locations` | Where we came from on that best route. |
| `waiting` | Candidate locations still waiting to be explored. |
| `current_time` | Actual time along the route to the location being explored. |
| `new_time` | Current time plus the cost of the next road. |

`float('inf')` means infinity. Here it is a placeholder for “no route found yet.” A real route time will be smaller.

`heapq.heappush()` adds a candidate to the waiting queue. `heapq.heappop()` removes the candidate with the smallest value. An older, slower candidate is skipped when a better time has already been recorded.

Dijkstra orders that queue by actual time so far. A* uses `f = g + h`: actual time so far (`g`) plus estimated remaining time (`h`). With `g = 4` and `h = 3`, A* gives the candidate a queue score of 7. That estimate helps choose what to explore; it is not added to the final driving time.

The A* estimate is the cheapest outgoing road at each location, or zero at the destination and at dead ends. Any route to another location must take a first road, so this estimate cannot overstate the remaining travel time. The files have no coordinates for a straight-line estimate.

When the destination is reached, `build_route()` follows the saved previous locations backward. For example, C came from B, and B came from A. It collects C, B, A, then reverses them to return A, B, C.

## Connect the code to the application design

| Design document section | Where to look |
| --- | --- |
| Overall Operation | `main()` and the four numbered steps in `dispatch_calls()` |
| Simulation Files | `load_simulation()` and the input validation helpers |
| Call Priorities | `dispatch_order()` and `calls.sort(...)` |
| Dijkstra Algorithm | Section 3 of `FirstAlgorithm.py` |
| A Star Algorithm | Section 3 of `SecondAlgorithm.py`, including `estimate_remaining_times()` |
| Running and Logging | Command options in `main()` and `log_dispatch()` |
| Execution Timer | The `perf_counter()` calls around `find_fastest_route()` |

There are two separate kinds of priority. **Call priority** determines which emergency is handled first: 1, then 2, then 3. Equal-priority calls stay in their original CSV row order. The **route queue** determines which network location the route algorithm explores next.

There are also two separate kinds of time. **Travel time** is the simulated road cost. **Calculation time** is how many seconds the computer spends finding routes. The total calculation timer includes every ambulance's route search, not just the selected ambulance. It includes A* estimate building and excludes input loading, printing, and logging.

`Embedded Counters.docx` shows a JavaScript example of reading a clock before and after a function and subtracting the values. The Python programs apply that same timing idea using `perf_counter()`.

The reorganization preserves the application design's behavior, validation, command options, and log format. The design documents themselves have not been edited.
