import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Configuration
API_KEY = "your api-key here"   # Fingrid API key here
datasetId = 265
URL = f"https://data.fingrid.fi/api/datasets/{datasetId}/data"
HEADERS = {"x-api-key": API_KEY}

# Time selection
TIME_OPTIONS = {
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(days=7),
    "month": timedelta(days=30)
}

print("Select time range: \n - hour\n - day\n - week\n - month")

choice = input("Enter choice: ").lower()
if choice not in TIME_OPTIONS:
    print("Invalid option.")
    exit()

# Time range
end_time = datetime.now() - timedelta(hours=2)
start_time = end_time - TIME_OPTIONS[choice]

START_TIME = start_time.isoformat() + "Z"
END_TIME = end_time.isoformat() + "Z"

# Fetch data
PARAMS = {"startTime": START_TIME, "endTime": END_TIME, "pageSize": 15000}

try:
    response = requests.get(URL, headers=HEADERS, params=PARAMS)
    response.raise_for_status()
    
except requests.exceptions.HTTPError as http_err:
    if response.status_code == 401:
        print("Error: API key is invalid.")
    elif response.status_code == 403:
        print("Error: API key may be missing or incorrect.")
    else:
        print(f"HTTP error: {http_err}")
    sys.exit(1)

except requests.exceptions.ConnectionError:
    print("Error: Network error.")
    sys.exit(1)

response_data = response.json()

# Extract the data array from the response
if isinstance(response_data, dict) and "data" in response_data:
    data = response_data["data"]
elif isinstance(response_data, list):
    data = response_data
else:
    data = response_data

if not data:
    print("No data available for the selected time range.")
    exit()

# Averaging intervals
if choice == "hour":
    averaging_minutes = None      # all data points
elif choice == "day":
    averaging_minutes = 15       # 15 min intervals
elif choice == "week":
    averaging_minutes = 60        # 60 min intervals
else:  # month
    averaging_minutes = 60*6      # 6 hour intervals

times = []
values = []

if averaging_minutes is None:
    for entry in data:
        time = datetime.fromisoformat(entry["startTime"].replace("Z", "+00:00"))
        value = entry["value"]
        times.append(time)
        values.append(value)
else:
    data_point_set = defaultdict(list)
    delta = timedelta(minutes=averaging_minutes)

    for entry in data:
        time = datetime.fromisoformat(entry["startTime"].replace("Z", "+00:00"))
        value = entry["value"]

        # Use integer division to get the bucket start time
        epoch = datetime(1970,1,1, tzinfo=time.tzinfo)
        set_number = int((time - epoch) // delta)
        set_time = epoch + set_number * delta

        data_point_set[set_time].append(value)

    for set_time in sorted(data_point_set):
        avg_value = sum(data_point_set[set_time]) / len(data_point_set[set_time])
        times.append(set_time)
        values.append(avg_value)


# Plot
plt.figure(figsize=(10,5))
plt.plot(times, values, marker='.', linestyle='-', color='green')
plt.xlabel("Time")
plt.ylabel("Emission factor (gCO₂/kWh)")
plt.title(f"Emission factor for electricity consumed in Finland (past {choice})")
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()
