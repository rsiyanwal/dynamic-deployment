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
> [!NOTE]
> As you can see, all the files are located in the same folder, meaning there is no hierarchy. This is done just because of laziness. It is not mandatory to have your folder set up in this fashion. You may also notice that the folder name is "myapp," but that's not the actual case either (_when you download the code for this day, just change "Day 1: Docker" to "myapp"_). 

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
![Image](https://github.com/user-attachments/assets/36c4f6c6-17a1-4ece-8371-854a8aacaec0)
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

We will look at `Docker Swarm` next. If you have completed the tutorial this far, then **you have completed** the deployment of the Dockerizethe d application on a single host. There are many other things you can do with the application, such as:
- Check logs of the services: `docker compose logs -f consumer`
- Scaling the services
- Stop the application: `docker compose down`

![Image](https://github.com/user-attachments/assets/f7dc8404-8a8c-405a-be19-08f499d8eaa6)

#### Questions
1. What does `depends_on` do in the `docker-compose.yml` file?
2. Can you access the producer service in a browser?

### Scenario 02: On Different Machines
Now, we will **scale the services across multiple Raspberry Pis**. Right now, we will use two Raspberry Pis running on Raspbian OS. 
#### Step 01: Initialize Docker Swarm on the Manager node
Choose any of the Pis as a manager node and run the command mentioned below on it:
```
docker swarm init
```
This command initializes a Docker Swarm on the Pi, making it the **manager node**. The manager node is responsible for managing the **Swarm cluster**, maintaining the **cluster state**, and handling **worker nodes**. 
- A **Swarm cluster** is a group of Docker hosts(nodes) that work together as a single virtual system. It consists of Manager Nodes that manage the cluster and tasks and Worker Nodes that run the tasks(containers) assigned by the Manager node. It allows us to _deploy and manage machines across multiple machines_.
- **Scheduling services** refers to assigning tasks (containers) to worker nodes. The manager node decides:
  - Appropriate worker node for a specific task
  - Distribution of the tasks across the cluster for optimum performance and resource utilization (For example, if you deploy a service with 5 replicas, the manager node will schedule 5 containers across the available worker nodes)
- The **cluster state** refers to the current status and configuration of the Swarm cluster. The cluster state is maintained by the manager node(s). It is a dynamic representation of what is actually happening in the cluster. 
- **Worker nodes** are the machines in the Swarm cluster that run the tasks (containers) assigned to them by the manager node. The manager node handles worker nodes by:
  - Monitoring the health and status of the worker nodes
  - Rescheduling tasks if a worker node fails
  - Distributing tasks evenly across worker nodes to ensure efficient resource utilization 
> [!NOTE]
> Imagine you have a Swarm cluster with:
> - 1 Manager node
> - 3 Worker nodes
> You deploy a service with 3 replicas. The manager node schedules the service by:
> - Assigning 1 replica to each worker node
> - Ensuring the desired state of 3 replicas is maintained
> If one of the worker nodes fails, the manager node detects the failure and reschedules the affected tasks on the **remaining health nodes**.
> If you want to scale the service to 6 replicas, the manager node will schedule 2 replicas on each worker node.

#### Step 02: Initialize the Worker nodes
When you complete Step 01, the manager node will give you an output similar to the following:
```
Swarm initialized: current node (7x4..) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-0h.. <IP_Address>:<Port>

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.
```
**As it says, we need to run the given command on all the nodes we want as Worker nodes**. Ignore the `docker swarm join-token manager` command for now. If you succeed, you will get a message, `This node joined a swarm as a worker` from all the Worker nodes.

You have successfully created a Swarm cluster. Let's verify it:
```
docker node ls
```

#### Step 03: Deploy the Swarm Stack (deploying the application on the Swarm cluster)
On the Manager node, navigate to the directory that has all the files we created so far. Make changes in the docker-compose.yml file by incrementing the consumer's replica by 1 (making it 2) and run the command:
```
docker stack deploy -c docker-compose.yml myapp
```
We are deploying the application that will have 1 producer service and 2 consumer services. Let's verify:
```
docker service ls
```
You should get an output like this:
```
ID             NAME             MODE         REPLICAS   IMAGE             PORTS
kich........   myapp_consumer   replicated   2/2        consumer:latest   
atew........   myapp_producer   replicated   1/1        producer:latest   *:5000->5000/tcp
```
It means that 1 producer service and 2 consumer services are running successfully. But where exactly are they running (which service at what node)? First let's check the Producer service:
```
docker service ps myapp_producer
```
Which should give you the following output (if you don't get it, keep on reading):
```
ID             NAME               IMAGE             NODE        DESIRED STATE   CURRENT STATE            ERROR     PORTS
9llr........   myapp_producer.1   producer:latest   localhost   Running         Running 21 minutes ago 
```
`localhost` is the name of my Master node (I know it is confusing), but it is not the actual 127.0.0.1 localhost but just the machine's name. The output states that the Producer service is running on the Master node named localhost. Now, let's see where Consumer services are running:
```
docker service ps myapp_consumer
```
Which should give you the following output:
```
ID             NAME                   IMAGE             NODE        DESIRED STATE   CURRENT STATE             ERROR                              PORTS
7l73........   myapp_consumer.1       consumer:latest   localhost   Running         Running 18 minutes ago                                       
2sfs........   myapp_consumer.2       consumer:latest   localhost   Running         Running 17 minutes ago                                       
88s9........    \_ myapp_consumer.2   consumer:latest   rasp11      Shutdown        Rejected 17 minutes ago   "No such image: consumer:latest"   
vro5........    \_ myapp_consumer.2   consumer:latest   rasp11      Shutdown        Rejected 17 minutes ago   "No such image: consumer:latest"   
n21c........    \_ myapp_consumer.2   consumer:latest   rasp11      Shutdown        Rejected 18 minutes ago   "No such image: consumer:latest"   
mfso........    \_ myapp_consumer.2   consumer:latest   rasp11      Shutdown        Rejected 18 minutes ago   "No such image: consumer:latest"   
```
Observe that we have an error. "No such image: consumer:latest" at `rasp11` (which, btw, is the name of my worker node). 
> [!IMPORTANT]
> We got this error because we don't have the images at the worker node. Yet, the Master node managed to give us two services. It did it by hosting both of the consumer services on its own. Let this be **the first example we have witnessed of the way Manager node handles failure**. In this scenario, one of the two machines is not useful/unavailable to us. 
> In Docker Swarm, when you deploy an application, all the Docker images must be available on all nodes where the service is scheduled to run. If the image is missing on a node, the task will fail with the error `"No such image: <service_name>"`.

#### Step 04: Pushing the Docker images to all the Worker nodes
You can use any of the following ways:
##### 01. The simple old way - 
You can copy-paste the entire directory on every Worker node and run `docker compose up --build` command. 
##### 02. Push images to Docker Registry - 
- Login to your docker account: `docker login`
- Tag the image with your Docker Hub username: `docker tag consumer:latest <your-dockerhub-username>/consumer:latest`
- Push the tagged image to Docker Hub: `docker push <your-dockerhub-username>/consumer:latest`
- Open your Docker Hub account on a browser and validate if the image is there. You will notice that the image name is not `consumer` anymore but `<your-dockerhub-username>/consumer`. Therefore, you have to make a change in your Docker compose file. Open it and change the Consumer service as:
```
consumer:
  image: <your-dockerhub-username>/consumer:latest
...
```
- Pull the image on Worker nodes: `docker pull <your-dockerhub-username>/consumer:latest`
- Redeploy the Stack: `docker stack deploy -c docker-compose.yml myapp`
> [!IMPORTANT]
> Do the same for the Producer image as well

Verify the changes. 

















