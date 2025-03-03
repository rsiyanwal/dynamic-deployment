# Day 01
Welcome to the Day 1 of learning FogDEFT. In this tutorial, you will learn Docker and Docker Swarm concepts with the help of Python microservices. In this hands-on tutorial, you will:
- **Containerize Python applications** using Docker.
- **Establish communication** between multiple containers.
- Use **Docker Compose** to manage multi-container applications on a single machine.
- Deploy the **same setup on multiple Raspberry Pis** using **Docker Swarm**.
- **Understand orchestration** by comparing Docker Compose and Docker Swarm. 

This is how the files are managed for our application:
```
myapp/
├── docker-compose.yml
├── Dockerfile-consumer
├── Dockerfile-producer
├── consumer.py
└── producer.py
```
As you can see, all the files are located in the same folder, meaning there is no hierarchy. This is done just because of laziness. It is not mandatory to have your folder set up in this fashion. You may also notice that the folder name is "myapp," but that's not the actual case either (anyway, it doesn't matter). 

## 1. Understanding the problem statement
You have two Python services that need to communicate:
1. `Producer service` - Generates random numbers
2. `Consumer service` - Receives numbers from the Producer and prints them

I request you to examine both the files: [producer.py](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/producer.py) and [consumer.py](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/consumer.py) to understand them. The code is well-commented. Please run both services to see them in action, **but make sure you run the producer.py first**. In consumer.py, you must change the value of `PRODUCER_URL` with one of the URLs provided by the `producer.py,` which generally includes `127.0.0.1` and your local IP address. Therefore, one of the valid values is `http://127.0.0.1:5000/number`.
```
# Defining the producer's URL
"""
Remember that /number URL invokes the get_number() function in the producer.py
When you run producer.py, replace the server_address with any of the ones in the output
"""
PRODUCER_URL = "http://<server_address>:5000/number"
```
If you just run the producer.py service, then on your web browser, if you visit the URL, you should get the following output:
```
{
  "number": 73
}
```
Of course, the number will be different. **How does it work?** When you run the script, the Flask server starts and listens to `http://0.0.0.0:5000`. If you visit `http://<server-address>:5000/number` in your browser or send a request to this URL, the server will:
- Generate a random number between 1 and 180.
- Return the number as a JSON response.

When you run the consumer.py service, it sends an **HTTP GET** request to `http://<server-address>:5000/number`. If the request is successful, it will parse the JSON response and print the number. If it fails, it prints an error message. After each request, it waits for 3 seconds before repeating the process. 

### What does `0.0.0.0` mean?
`0.0.0.0` is a special IP address which listens on all available network interfaces. It means that it will accept incoming connections from:
- The loopback interface (`127.0.0.1` or `localhost`).
- Any local network interface (e.g., `192.168.x.x`).
- Any external network interface if the server is exposed to the internet.

Therefore, you can access the `producer service` response using `http://127.0.0.1:5000/number`. Similarly, we can use `http://localhost:5000/number`, `http://192.168.x.x:5000/number`, etc., to get the number. Moreover, you can follow the guideline below to make appropriate decision. 
```
# Use 127.0.0.1 if running on the same machine
PRODUCER_URL = "http://127.0.0.1:5000/number"

# Use the local IP if running on the same network
PRODUCER_URL = "http://192.168.x.x:5000/number"

# Use a public IP or domain name if the server is exposed to the internet
PRODUCER_URL = "http://example.com:5000/number"
```

## 2. There are two deployment scenarios
| Scenario | Solution |
| -------- | -------- |
| Both services **run on the same machine** | Use Docker Compose |
| Services **run on different machines** (Raspberry Pis in this case) | Use Docker Swarm |

### Scenario 01: On the same machine
Once you are done running the application, let's start containerizing it. We need to create **Dockerfiles** for each service. 
















