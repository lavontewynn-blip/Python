# Railroad Program
list_of_stations = ["New Haven", "West Haven", "Milford", "Stratford", "Bridgeport", "Stamford", "Norwalk", "Darien", "Greenwich"]

departure_station = "New Haven"
destination_station = "Greenwich"

# Visit each station in the order it appears in the list.
for current_station in list_of_stations:
    print(f"The train is currently at {current_station}.")

    if current_station == departure_station:
        answer = input("Is this your departure station? (yes/no): ").strip().lower()
        while answer not in ("yes", "y", "no", "n"):
            answer = input("Please enter yes or no: ").strip().lower()

        if answer in ("no", "n"):
            print("Journey cancelled. This trip departs from New Haven.")
            break

        print(f"Departing from {departure_station}! All aboard!")

    if current_station == destination_station:
        answer = input("Is this your destination station? (yes/no): ").strip().lower()
        while answer not in ("yes", "y", "no", "n"):
            answer = input("Please enter yes or no: ").strip().lower()

        if answer in ("yes", "y"):
            print(f"You have arrived at {destination_station}! Thank you for traveling.")
        else:
            print(f"{destination_station} is the final station on this route.")
    else:
        print("Continuing to the next station...")
