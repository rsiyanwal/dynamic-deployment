# Manual tasks we performed day-wise:
## Day 01:
| TASK | Manual Action |
| ---- | ------------- |
| Directory | Manually setting-up folder structure |
| Services | Writing `consumer.py` & `producer.py` files | 
| Writing Dockerfiles | Manually created `Dockerfile-producer` & `Dockerfile-consumer`|
| Writing `docker-compose.yml` | Manually wrote service definitions and dependencies |
| Building & Running Containers | Ran `docker compose up --build` |
| Checking logs | Used `docker compose logs` |
| Initializing Docker Swarm | Ran `docker swarm init` & `docker swarm join` |
| Deploying the Stack | Ran `docker stack deploy -c docker-compose.yml myapp` |
| Debugging Errors | Manually checked logs & container status |
| Docker Hub | Manually tagging, pushing, and pulling images to/from Docker Hub|
***
## Day 02:
| **TASK** | **Manual Action** |
| -------- | ----------------- |
| Docker Swarm setup | `docker swarm init` |
| Docker Swarm node join | `docker swarm join` |
| Service deployment: Producer & Consumer | Created dockerfiles manually for each architecture; Tagged and pushed images; Defined and deployed services via `docker-compose.yml`; Deployed with `docker stack deploy` |
| Multi-arch Docker build & push | Used `buildx` to create multi-arch images; Had to manually specify platforms, tags, and push |
| Prometheus + cAdvisor | Wrote `docker-compose` configurations for `prometheus` and `cAdvisor`; Created `prometheus.yml` manually with hardcoded target IPs; Exposed Prometheus UI and checked metrics manually |
| Auto-scaling mechanism | Create a bash script to: Query Prometheus API using `curl`; Parse CPU usage using `jq`; Scaled the service with `docker service scale` |
| Manually inspected logs (not shown in the tutorials) | `docker service ps` |

### List of all commands, scripts, and files used:
#### Docker Swarm:
```
docker swarm init
docker swarm join --token <token> <manager_ip>:<port>
docker node ls
```
#### Dockerfile for producer & consumer:
```
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install flask
CMD ["python", "producer.py"]  # or consumer.py
```
#### Multi-arch image build:
```
docker buildx create --use
docker buildx build --platform linux/arm/v7,linux/arm64 -t username/producer:multiarch --push .
docker buildx build --platform linux/arm/v7,linux/arm64 -t username/consumer:multiarch --push .
```
#### Docker compose stack for Prometheus and cAdvisor:
```
# docker-compose.monitor.yml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /sys:/sys:ro
      - /dev/disk:/dev/disk:ro
    deploy:
      mode: global

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    deploy:
      placement:
        constraints:
          - node.role == manager
```
Deploying: `docker stack deploy -c docker-compose.yml <app_name>`
#### Prometheus config:
```
global:
  scrape_interval: 2s

scrape_configs:
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['192.168.1.13:8080', '192.168.1.26:8080']
```
#### Auto-scaling script:
```
#!/bin/bash
get_cpu_usage() {
  curl -s "http://192.168.1.26:9090/api/v1/query?query=$(echo -n 'avg(rate(container_cpu_usage_seconds_total{container_label_com_docker_swarm_service_name="myapp_producer"}[1m])) * 100' | jq -sRr @uri)" |
  jq -r '.data.result[0].value[1]'
}

replicas=1

while true; do
  cpu_usage=$(get_cpu_usage)
  if [[ -z "$cpu_usage" || "$cpu_usage" == "null" ]]; then
    echo "Could not fetch CPU usage. Skipping..."
  else
    echo "CPU usage: $cpu_usage%, Replicas: $replicas"
    usage_high=$(echo "$cpu_usage > 20.0" | bc)
    usage_low=$(echo "$cpu_usage < 5.0" | bc)

    if [[ $usage_high -eq 1 && $replicas -lt 10 ]]; then
      replicas=$((replicas + 1))
      docker service scale myapp_producer=$replicas
    elif [[ $usage_low -eq 1 && $replicas -gt 1 ]]; then
      replicas=$((replicas - 1))
      docker service scale myapp_producer=$replicas
    fi
  fi
  sleep 2
done
```
***
