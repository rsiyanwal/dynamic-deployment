# Dynamic Deployment
Modern distributed systems, by their nature, consist of multiple interconnected components working together. Such systems integrate various technologies, for example, different parts of the system might be written in different programming languages, and these parts might be running on a mix of servers with different operating systems and CPUs. Different components might use different databases (SQL, NoSQL), message queues (Apache Kafka, RabbitMQ), and caching systems (Redis, Memcached), and ultimately, the system could be deployed across different environments (on-premise, cloud, edge). This **heterogeneity** makes integration, maintenance, and deployment more complex. Modern distributed systems' **scale** and complexity make manual management impractical. Hence, automation is essential for tasks such as - deploying and updating software across hundreds or thousands of servers, dynamically scaling resources in response to the changing workload, continuously monitoring the health and performance of the system, managing the configurations of a large number of components, and minimizing downtime. 

These problems of heterogeneity and scale can be addressed using **FogDEFT framework**[^1][^2], in which heterogeneity is taken care of by achieving platform independence using **Containers**. The framework employs **Docker Swarm** and **Kubernetes** platforms to automate containerized applications' deployment, scaling, and management. To describe such systems, FogDEFT extended and uses **OASIS TOSCA (Topology and Orchestration Specification for Cloud Applications)**, an open standard that provides a way to describe applications and their components in a platform-neutral way. By integrating containers, orchestration tools, and standardization, FogDEFT enables seamless on-the-fly deployment and undeployment of services. 

### Key features of FogDEFT
| Feature | Next heading |
| --------- | ------------ |
| Platform independence | Using Docker containers to run services on any node |
| Interoperability | Docker Swarm / Kubernetes |
| Standardization | Extends OASIS TOSCA to define applications in a vendor-neutral way |

## Learning FogDEFT in one week
### Day 1: Hands-on guide to Docker and Docker Swarm with Python Microservices

> [!TIP]
> Make a list of all the tasks we are doing manually.

# References:
[^1]: S. N. Srirama and S. Basak, "Fog Computing out of the Box with FogDEFT Framework: A Case Study," 2022 IEEE 15th International Conference on Cloud Computing (CLOUD), Barcelona, Spain, 2022, pp. 342-350, doi: 10.1109/CLOUD55607.2022.00057.
[^2]: Thalla R, Srirama SN. FogDEFTKube: Standards-compliant dynamic deployment of fog service containers. Softw: Pract Exper. 2024; 54(12): 2428-2453. doi: 10.1002/spe.3354

