# This is a pretty simple hacked script that can download historical boat position information from
# PredictWind.  If you use the DataHub vessle tracking then you can get all the position data.
# This script can determined - based on your preference - when a trip starts and ends and pull
# all the data points which give you position, boat speed, wind angle, wind speed, wind direction
# and bearing.  It then generates a summary of the trip including total distance, average speed.
import requests
import json
from datetime import datetime
import math
import argparse

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers. Use 3956 for miles.
    r = 6371

    # Calculate the result
    return c * r

parser = argparse.ArgumentParser(description="Extracts track information for \
                                 boat trips from PredictWind")
parser.add_argument('-n', '--name', help='PredictWind vessel identifier')
parser.add_argument('-d', '--distance', type=int, help='The length (in feet) the \
                    denotes the start of a trip', default=100)
args = parser.parse_args()

# Define the URL of the JSON document
url = 'https://forecast.predictwind.com/tracking/data/' + args.name + '.json'

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    try:
        # Parse the JSON content
        data = response.json()


        # Do something with the parsed data
        trip = []
        last_item = None
        start_trip = False
        print("Start Date/Time,Trip Distance(nm),Average Speed(kts), Timestamp,\
               Interval Distance(nm),Elpsed Distance(nm),\
               Elapsed Time(hhh:mm),Latitude,Longitude,\
               Bearing, Boat Speed(kts),True Wind Angle,\
               True Wind Speed(kts),True Wind Direction")
        for item in data["route"]:
            if last_item is not None:
                lat1 = last_item["p"]["lat"]
                lon1 = last_item["p"]["lon"]
                lat2 = item["p"]["lat"]
                lon2 = item["p"]["lon"]

                mindist_km = args.distance * 0.0003048

                last_distance = haversine(lat1, lon1, lat2, lon2)
                item["distance"] = last_distance
                if len(trip) == 0 and last_distance > mindist_km:
                    start_trip = True

                if (len(trip) > 3 and last_distance <= mindist_km and 
                    trip[len(trip)-1]["distance"] <= mindist_km and 
                    trip[len(trip)-2]["distance"] <= mindist_km and 
                    trip[len(trip)-3]["distance"] <= mindist_km):
                    del trip[-1]
                    del trip[-1]
                    del trip[-1]

                    # Remove the last point if the boat speed is less than 1 knot.
                    if trip[-1]["bsp"] * 0.53995 < 1.0:
                        del trip[-1]

                    # Generate the trip summary data.  
                    trip_length = 0.0
                    total_speed = 0.0
                    for step in trip:
                        trip_length = trip_length + step["distance"] * 0.5399568
                        total_speed = total_speed + step["bsp"] * 0.53995
                    trip_length = trip_length - trip[0]["distance"]
                    average_speed = total_speed / len(trip)
                    if trip_length > 0.15:
                        if trip[1]["t"] - trip[0]["t"] > 1800:
                            trip[0]["t"] = trip[1]["t"] - 1800 
                        step_number = 0
                        start_time = trip[0]["t"]    
                        
                        print(datetime.fromtimestamp(start_time), ",", 
                              trip_length, ",", average_speed, ",", datetime.fromtimestamp(start_time),
                              ", 0.0, 0.0, 0,", trip[0]["p"]["lat"], ",",
                              trip[0]["p"]["lon"], ",", trip[0]["bearing"],
                              ",", trip[0]["bsp"], ",", trip[0]["twa"], ",",
                              trip[0]["tws"], ",", trip[0]["twd"])
                        
                        trip_length = 0.0
                        for step in trip:
                            if step_number > 0:
                                trip_length = trip_length + step["distance"] * 0.5399568
                                stamp = step["t"] 
                                duration = (datetime.fromtimestamp(stamp) -
                                            datetime.fromtimestamp(start_time))
                                total_seconds = int(duration.total_seconds())
                                hours, remainder = divmod(total_seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                formatted_time = f"{hours:03}:{minutes:02}"
                                wind_speed_in_knots = 1.94384 * step["tws"]
                                boat_speed_in_knots = 0.53995 * step["bsp"]
#                                print(datetime.fromtimestamp(start_time),",",datetime.fromtimestamp(stamp),",",formatted_time,",",step["bearing"],",", boat_speed_in_knots,",", step["twa"],",", wind_speed_in_knots,",", step["twd"])

                                print(",,,", datetime.fromtimestamp(stamp), ",",
                                      step["distance"] * 0.5399568, ",", trip_length, ",",
                                      formatted_time, ",", step["p"]["lat"],
                                      ",", step["p"]["lon"], ",",
                                      step["bearing"], ",", boat_speed_in_knots,
                                      ",", step["twa"], ",", wind_speed_in_knots,
                                      ",", step["twd"])
                                
                            step_number = step_number + 1
                    trip.clear() 
                elif len(trip) > 0 or start_trip:
                    trip.append(last_item)

            last_item = item
            start_trip = False

    except json.JSONDecodeError:
        print("Failed to decode JSON from response.")
else:
    print(f"Request failed with status code {response.status_code}")
