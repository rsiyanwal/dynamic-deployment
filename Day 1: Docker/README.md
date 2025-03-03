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

I request you to examine both the files: [Producer.py](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/producer.py) and [Consumer.py](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/consumer.py) to understand them. The code is well-commented. Please run both services to see them in action, **but make sure you run the producer.py first**. In consumer.py, you must change the value of `PRODUCER_URL` with one of the URLs provided by the `producer.py,` which generally includes `127.0.0.1` and your local IP address. Therefore, one of the valid values is `http://127.0.0.1:5000/number`.
```
# Defining the Producer's URL
"""
Remember that /number URL invokes the get_number() function in the producer.py
When you run producer.py, replace the server_address with any of the ones in the output.
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
`0.0.0.0` is a special IP address that listens on all available network interfaces. It means that it will accept incoming connections from:
- The loopback interface (`127.0.0.1` or `localhost`).
- Any local network interface (e.g., `192.168.x.x`).
- Any external network interface if the server is exposed to the internet.

Therefore, you can access the `producer service` response using `http://127.0.0.1:5000/number`. Similarly, we can use `http://localhost:5000/number`, `http://192.168.x.x:5000/number`, etc., to get the number. Also, you can follow the guidelines below to make the right decision. 
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
Once you are done running the application, let's start containerizing it. We need to create **Dockerfiles** for each service. Please take a look at [Dockerfile-consumer](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/Dockerfile-consumer) and [Dockerfile-producer](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/Dockerfile-producer). The files are very well explained and help you to understand how we dockerized the consumer.py and producer.py files respectively. **Needs a Docker primer here**

Now, we have two services, and we need **Docker Compose** to manage them. [This](https://github.com/rsiyanwal/dynamic-deployment/blob/main/Day%201%3A%20Docker/docker-compose.yml) is a docker-compose file for this application. Again, please take a look at the file to understand it. This file defines and connects both services. To run the docker-compose file, use the following command: `docker compose up --build`.

#### How does the Consumer access the Producer?
The Consumer communicates with the Producer **internally within the Docker network**. Docker Compose automatically sets up a network for the services, allowing them to communicate using their service names. Right now, in the `consumer.py` file, the `PRODUCER_URL` is defined as `http://<server_address>:5000/number`, and we are replacing the `<server_address>` with the ones suitable to us. If we continue using those same addresses, we run into a problem: `localhost,` `127.0.0.1`, etc., they refer to the Consumer's container loopback addresses now, and if we continue using these addresses, we won't get any number because the Producer service is running in a different container. Therefore, the value of `PRODUCER_URL` should be changed to `http://producer:5000/number`. The `producer` in the URL is the name of the Producer service that we defined in the docker-compose file. 

#### If the services can communicate using the Docker network, why have we mapped port 5000 of the Producer service with port 5000 of the host machine?
We mapped the Producer's port with the host's port because **not for the communication between the Producer and Consumer services** but for the **external access** to the Producer service. It is useful if you want to access the Producer service outside the Docker network. Also, if other services or applications outside the Docker network depend on the Producer service, they need a way to access it. Port mapping makes it possible. If you don't map, the Producer service will still be accessible within the Docker network. You can remove the mapping if a service is **only meant to be accessed by another internal service**. 

The network created by Docker Compose is a **bridge network**. The network is named `<project_name>_default` where `<project_name>` is the directory's name containing the docker-compose file. Other networks are available in Docker, namely **Docker Ingress Network** and **Docker Overlay Network**. The Ingress network is used for load balancing and routing traffic to services, whereas the Overlay network enables communication between containers running on different Docker hosts (nodes). Both networks span multiple Docker hosts. 
##### Key Differences:
| Feature | Docker Compose default network | Docker Ingress network | Docker Overlay network |
| ------- | ------------------------------ | ---------------------- | ---------------------- |
| **Type** | Bridge network | Overlay network | Overlay network |
| **Scope** | Single Docker host | Swarm cluster | Swarm cluster |
| **Purpose** | Internal communication | Load balancing and routing | Cross-host communication |
| **Created by** | Docker Compose | Docker Swarm | Docker Swarm |

We will look at `Docker Swarm` next. If you have completed the tutorial this far, then **you have completed** the deployment of Dockerized application on a single host. There are many other things you can do with the application, such as:
- Check logs of the services: `docker compose logs -f consumer`
- Scaling the services
- Stop the application: `docker compose down`

### Questions
1. What does `depends_on` do in the `docker-compose.yml` file?
2. Can you access the producer service in a browser?











