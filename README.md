This Python script will use the back end web service that the PredictWind tracking page uses to download the data.  
You specify the tracking name of your vessel as well as the number of feet the boat must move to constitute the start
of a trip.  The script will download the data, calculate all the trips and emit (to stdout) a CSV that contains the
data.  You can redirect that to a file or other target.
