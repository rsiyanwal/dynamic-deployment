"""
Continuously polls a remote API at a fixed interval to fetch a random number.
requests: A library for making HTTP requests
time: A library for time-related tasks
"""
# Importing the dependencies
import requests
import time

# Defining the producer's URL
"""
Remember that /number URL invokes the get_number() function in the producer.py
When you run producer.py, replace the server_address with any of the ones in the output
"""
PRODUCER_URL = "http://<server_address>:5000/number"

# Polling
"""
- Forever loop.
- Get the data from the producer.py URL
- Parse the json response from server (producer.py) into a python dictionary
- Print the received number from the server
"""
while True:
    try:
        response = requests.get(PRODUCER_URL)
        data = response.json()
        print(f"Received number: {data['number']}")
    except Exception as e:
        print(f"Error fetching the number: {e}")
    time.sleep(3)
