#%% Importing the dependencies
from flask import Flask, jsonify
import random

# Creating the flask app
app = Flask(__name__)
"""
@app.route('/number') decorator binds /number url path to get_number() function.
function. When a user accesses this route (e.g., by visiting http://<server-address>:5000/number), the get_number function is executed.
"""
@app.route('/number')
def get_number():
    number = random.randint(1, 180)
    return jsonify({'number': number})

# Main
if __name__ == '__main__':
    """
    host='0.0.0.0': Makes the server accessible from any device on the network (not just localhost).
    """
    app.run(host = '0.0.0.0', port = 5000)
