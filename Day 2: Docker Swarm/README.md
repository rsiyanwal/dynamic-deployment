# Day 02: Docker Swarm and more
Today, you will:
- Build **Multi-arch** images
	- Deploy them on heterogeneous Swarm cluster (different CPU architectures)
- **Scale services** using Docker Swarm
- **Load balancing**
- Perform **rolling updates** with no downtime
- Test **automatic service recovery**
- **Understand Orchestration** by comparing Docker Compose and Docker Swarm.

Let's start from where we left off on Day 01: **deploying an application via Docker Swarm on a cluster of multiple machines (nodes)**. Docker provides platform independence at the operating system level, but what if you work with different CPU architectures altogether? Such as, arm8, arm7, x86? Maybe on Day 1, you had the same architectures on both nodes and may not have encountered any errors that are caused by a mismatch of architectures. But today, the first task we will do is to learn how to adapt a Docker image to multiple architectures. 

Docker images are dependent on CPU architecture as they contain process-specific instructions. Take a look at it yourself:
- Push the images from your nodes separately to Docker Hub
- Run: `docker manifest inspect --verbose <image_name>` on each nodes.

You should get an output like this:
```
sudo docker manifest inspect --verbose <image_name>
{
	"Ref": "docker.io/<image_name>r:<tag>",
	"Descriptor": {
		"mediaType": "application/vnd.docker.distribution.manifest.v2+json",
		"digest": "sha256:6355f7...",
		"size": 2420,
		"platform": {
			"architecture": "arm64",
			"os": "linux",
			"variant": "v8"
		}
	},
	"SchemaV2Manifest": {
		"schemaVersion": 2,
		"mediaType": "application/vnd.docker.distribution.manifest.v2+json",
		"config": {
			"mediaType": "application/vnd.docker.container.image.v1+json",
			"size": 7666,
			"digest": "sha256:4223909..."
		},
		"layers": [
			{
				"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
				"size": 48308008,
				"digest": "sha256:52daf8b0f..."
			},
...
```
**Problem:**
- `localhost` (Swarm manager) is ARMv8 (Raspberry Pi 4)
- `rasp11` (Worker node) is ARMv7 (Raspberry Pi 3)
- Docker **builds images only for the local architecture**, so if `localhost` creates ARMv8-only images, then it will not work when deployed on ARMv7.

**So, how do we make multiple Docker images for different architectures?** We can use **Docker Buildx** to build multi-architecture images. Once we push such images to Docker Hub, we can use **platform-aware scheduling** to deploy services using Docker Swarm. 

## Let's get started:

### Step 01: Enable multi-arch builds
On your Swarm manager, enable `buildx`:
- Enable `binfmt_misc` for cross-architecture emulation: `docker run --privileged --rm tonistiigi/binfmt --install all`
- Create a `buildx` builder: `docker build create --name multiarch-builder --use`
- Ensure the builder is ready to use: `docker buildx inspect --bootstrap`

The [tonistiigi/binfmt](https://github.com/tonistiigi/binfmt) is an image that contains the [binfmt_misc](https://en.wikipedia.org/wiki/Binfmt_misc) utility, which allows the Linux kernel to recognize and execute binaries of different architectures. Using the `--install all` flag, the command installs support for all the supported architectures. We have to give this `container` full access to the host system. Therefore, we use the `--privileged` flag. The `--rm` flag removes the container after it exits. On running this command, you should get an output similar to:
```
installing: mips64 OK
installing: amd64 OK
installing: ppc64le OK
installing: riscv64 OK
installing: mips64le OK
installing: s390x OK
installing: 386 OK
installing: loong64 OK
{
  "supported": [
    "linux/arm64",
    "linux/amd64",
    "linux/amd64/v2",
    "linux/riscv64",
    "linux/ppc64le",
    "linux/s390x",
    "linux/386",
    "linux/mips64le",
    "linux/mips64",
    "linux/loong64",
    "linux/arm/v7",
    "linux/arm/v6"
  ],
  "emulators": [
    "qemu-i386",
    "qemu-loongarch64",
    "qemu-mips64",
    "qemu-mips64el",
    "qemu-ppc64le",
    "qemu-riscv64",
    "qemu-s390x",
    "qemu-x86_64"
  ]
}

``` 
Next, using the `docker buildx create --name multiarch-builder --use` we are creating a new `buildx` instance named `multiarch-builder` and setting it as the default builder using `--use` flag. `Docker buildx` is an extension of `Docker build` that supports multi-architecture builds. Once you run all the commands mentioned above, you should get the output:
```
[+] Building 42.3s (1/1) FINISHED                                                           
 => [internal] booting buildkit                                                       42.3s
 => => pulling image moby/buildkit:buildx-stable-1                                    24.6s
 => => creating container buildx_buildkit_multiarch-builder0                          17.8s
Name:   multiarch-builder
Driver: docker-container

Nodes:
Name:      multiarch-builder0
Endpoint:  unix:///var/run/docker.sock
Status:    running
Platforms: linux/arm64, linux/amd64, linux/amd64/v2, linux/riscv64, linux/ppc64le, linux/s390x, linux/386, linux/mips64le, linux/mips64, linux/loong64, linux/arm/v7, linux/arm/v6
```
Now, multiple architectures are supported on our master node. You can check the list of support platforms. 

### Step 02: Build and push multi-arch images
- Run: `docker buildx build --platform linux/arm/v7,linux/arm64 -t <your-dockerhub-username>/producer:multi-arch --push -f Dockerfile-producer`
- Run: `docker buildx build --platform linux/arm/v7,linux/arm64 -t <your-dockerhub-username>/consumer:multi-arch --push -f Dockerfile-consumer`
- Verify multi-arch support: `docker buildx imagetools inspect <your-dockerhub-username>/producer:multi-arch` &  `docker buildx imagetools inspect <your-dockerhub-username>/consumer:multi-arch`
The commands are easy to understand; give them a try. Let me help you by explaining what these flags mean:
- `-t` means `tag` (we used this flag before)
- `--push` means pushing the image to Docker Hub
- `-f` means the `Dockerfile` of the service

### Step 03: Make the necessary changes in the docker-compose file
Since we have created a new image with the same name but a different tag, we need to mention it in our docker-compose file, therefore, make the changes:
```
...
producer:
	image: <your-dockerhub-username>/producer:multi-arch
...
consumer:
	image: <your-dockerhub-username>/consumer:multi-arch
...
```
Finally, run the Docker Stack command: `docker stack deploy -c docker-compose.yml myapp`
Make sure to check if your Swarm cluster is working. You might remember the commands from Day 01 that will help you. 

P.S. Don't forget that you have exposed your host's port 5000 to the application: `curl http://127.0.0.1:5000/number`

## What else can Docker Swarm do?
### **Scale up** the services: 
Run: `docker service scale myapp_consumer=5`
![Image](https://github.com/user-attachments/assets/b170e279-ec8b-4918-a633-edd7dcf113e5)
***
### **Load balancing**:
Let's try to simulate some traffic.
- First, get the IP address of any of the Worker nodes. You should know it, but if you don't:
  - Run: `docker node inspect <your-worker-node> | grep Addr`
- Run: `for i in {1..20}; do curl http://<any-node-IP>:5000/number; done` (you can run it on any of the machines)
![Image](https://github.com/user-attachments/assets/2e02e8dd-033d-40a8-ada6-390bb4aaebbc)
- In the image above, notice how the requests are distributed among the nodes. We've only made 20 requests in a second. Let's increase the load even further.
- Install [wrk](https://github.com/wg/wrk): `sudo apt install wrk -y`
- Then, run: `wrk -t4 -c20 -d30s http://<any-node-IP>:5000/number`. This will simulate 4 threads, 20 concurrent users, sending requests for 30 seconds.
- **Observe** how requests are handled.
- Try simulating the traffic again, and this time, use `docker stats` to see how each node is performing. If a node is struggling somewhere, the load is not evenly balanced (remember, you have to run this command on both nodes as both of them have replicas of the Producer service).
- **Observe the performance again**
![Image](https://github.com/user-attachments/assets/2b64a378-f362-4523-9375-3f5ab9dff6a1)
Can we say if any of the Producer replicas are struggling?
- Let's increase the scale of our experiment: We will increase the Producer replicas and the traffic as well. 
**Master node (Localhost):**
```
NAME                                         CPU %     MEM USAGE / LIMIT   MEM %     NET I/O           BLOCK I/O     PIDS
myapp_producer.5.mr0l9hzo8ezmcqb05x2l58onr   60.47%    0B / 0B             0.00%     526kB / 673kB     1.88MB / 0B   3
myapp_producer.2.xh3tfi8ugd9d46yhzafibd7nw   59.00%    0B / 0B             0.00%     528kB / 673kB     1.97MB / 0B   5
myapp_producer.4.0v1hqdcvywvbxujnggs8t4rek   59.87%    0B / 0B             0.00%     530kB / 676kB     1.73MB / 0B   5
myapp_consumer.1.0wtbzo5gdmom8xvdcu1me82jx   0.26%     0B / 0B             0.00%     87.3kB / 86.6kB   17.9MB / 0B   1
```
**Worker node (Rasp11):**
```
NAME                                         CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O       PIDS
myapp_producer.3.ic1y50gznggr3ak4xco47702x   48.94%    13.1MiB / 3.749GiB    0.34%     2.85MB / 3.76MB   0B / 127kB      1
myapp_producer.1.lcs3fnzq701jwtrm1wmfcoxr0   47.59%    18.18MiB / 3.749GiB   0.47%     2.87MB / 3.78MB   5MB / 127kB     1
myapp_consumer.2.vwyfi9kxi2797gb1twt4qh719   0.00%     11.37MiB / 3.749GiB   0.30%     97.6kB / 99.4kB 
```
I simulated 200 concurrent users and 4 threads each, sending requests for 30 seconds. I sent the requests to the master node's IP. In total, they made 17,794 requests. So far, the master node handles more traffic than the worker node. **Is it because I made the requests to the master node?** Let's test this hypothesis.

**Master node (Localhost):**
```
NAME                                         CPU %     MEM USAGE / LIMIT   MEM %     NET I/O           BLOCK I/O     PIDS
myapp_producer.5.mr0l9hzo8ezmcqb05x2l58onr   71.49%    0B / 0B             0.00%     12.9MB / 15.5MB   1.88MB / 0B   4
myapp_producer.2.xh3tfi8ugd9d46yhzafibd7nw   71.06%    0B / 0B             0.00%     12.8MB / 15.5MB   1.97MB / 0B   5
myapp_producer.4.0v1hqdcvywvbxujnggs8t4rek   70.52%    0B / 0B             0.00%     12.8MB / 15.5MB   1.73MB / 0B   3
myapp_consumer.1.0wtbzo5gdmom8xvdcu1me82jx   0.50%     0B / 0B             0.00%     248kB / 265kB     17.9MB / 0B   1
```
**Worker node (Rasp11):**
```
NAME                                         CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O       PIDS
myapp_producer.3.ic1y50gznggr3ak4xco47702x   70.56%    13.28MiB / 3.749GiB   0.35%     12.4MB / 13.2MB   0B / 127kB      4
myapp_producer.1.lcs3fnzq701jwtrm1wmfcoxr0   72.18%    18.31MiB / 3.749GiB   0.48%     12.4MB / 13.3MB   5MB / 127kB     4
myapp_consumer.2.vwyfi9kxi2797gb1twt4qh719   0.00%     11.39MiB / 3.749GiB   0.30%     246kB / 260kB     13MB / 24.6kB   1
```
It seems like the case, but it can't be concluded as such yet because we haven't performed enough tests. If you want to test this hypothesis rigorously, go ahead. Increase the load and nodes as well if you want, and take it to the extremes. It's all up to you! 

> [!IMPORTANT]
> We know that Docker Swarm can balance the load well, but are we making any mistakes? Are we overlooking something? Think about it. We are running the `wrk` command from one of the nodes in Swarm. That node is doing two tasks: Making many requests (`wrk` command) and serving those requests (`Producer replica`). Do you think it gives us a proper look at the performance?

Let's separate the client and server. For forthcoming experiments, I used my machine (Windows 10 - Powershell) to run a command similar to `wrk`, which does not work on Windows. Here, I'd like to introduce a new command similar to `wrk` called `hey` which is built for Windows. 
- Download [hey](https://github.com/rakyll/hey?tab=readme-ov-file).
- In Powershell, navigate to the folder where `hey` is downloaded.
- You might have downloaded `hey_windows_amd64`.
- Run: `ren hey_windows_amd64 hey.exe`
- Move `hey.exe` to system-wide location: `Move-Item hey.exe C:\Windows\System32` (Now you can use `hey` from any location without specifying the full path)
- Test: `hey -n 1000 -c 50 http://<any-workernode-IP>:5000/number`

#### Real test:
**Command:** `hey -n 30000 -c 50 http://192.168.0.100:5000/number`
**Output:**
```
Summary:
  Total:        51.8463 secs
  Slowest:      0.4758 secs
  Fastest:      0.0209 secs
  Average:      0.0856 secs
  Requests/sec: 578.6337

  Total data:   432181 bytes
  Size/request: 14 bytes

Response time histogram:
  0.021 [1]     |
  0.066 [8246]  |■■■■■■■■■■■■■■■■■
  0.112 [19077] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.157 [1264]  |■■■
  0.203 [591]   |■
  0.248 [205]   |
  0.294 [225]   |
  0.339 [226]   |
  0.385 [138]   |
  0.430 [12]    |
  0.476 [15]    |


Latency distribution:
  10% in 0.0537 secs
  25% in 0.0646 secs
  50% in 0.0793 secs
  75% in 0.0924 secs
  90% in 0.1091 secs
  95% in 0.1430 secs
  99% in 0.3184 secs

Details (average, fastest, slowest):
  DNS+dialup:   0.0271 secs, 0.0209 secs, 0.4758 secs
  DNS-lookup:   0.0000 secs, 0.0000 secs, 0.0000 secs
  req write:    0.0006 secs, 0.0000 secs, 0.0197 secs
  resp wait:    0.0406 secs, 0.0057 secs, 0.3242 secs
  resp read:    0.0172 secs, 0.0001 secs, 0.1594 secs

Status code distribution:
  [200] 30000 responses
```
- Our system is handling ~578 requests per second.
- The system, in ~52 seconds, has processed 30,000 requests with no failure.
- 50% of the requests (median) are completed in 0.079s.
- 90% of the requests are completed in ~0.109s
- 1% of the requests took longer than 0.318s, which indicates an occasional slow response.
- Overall, we transferred ~126KB of response data per second.

The system is performing well. **Let's break it.**

Command: ` hey -n 600000 -c 2000 -z 30s http://192.168.0.106:5000/number`
Output:
```
Summary:
  Total:        47.4150 secs
  Slowest:      20.1692 secs
  Fastest:      0.6356 secs
  Average:      3.0731 secs
  Requests/sec: 394.1787

  Total data:   262820 bytes
  Size/request: 14 bytes

Response time histogram:
  0.636 [1]     |
  2.589 [11100] |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  4.542 [3525]  |■■■■■■■■■■■■■
  6.496 [1896]  |■■■■■■■
  8.449 [937]   |■■■
  10.402 [329]  |■
  12.356 [188]  |■
  14.309 [148]  |■
  16.262 [64]   |
  18.216 [24]   |
  20.169 [38]   |


Latency distribution:
  10% in 0.9993 secs
  25% in 1.3164 secs
  50% in 2.1034 secs
  75% in 3.6288 secs
  90% in 6.4166 secs
  95% in 7.8683 secs
  99% in 13.1125 secs

Details (average, fastest, slowest):
  DNS+dialup:   1.0871 secs, 0.6356 secs, 20.1692 secs
  DNS-lookup:   0.0000 secs, 0.0000 secs, 0.0000 secs
  req write:    0.0010 secs, 0.0000 secs, 0.0518 secs
  resp wait:    1.6888 secs, 0.0151 secs, 18.3150 secs
  resp read:    0.2863 secs, 0.0000 secs, 17.7615 secs

Status code distribution:
  [200] 18250 responses

Error distribution:
  [1]   Get "http://192.168.0.106:5000/number": context deadline exceeded
  [372] Get "http://192.168.0.106:5000/number": context deadline exceeded (Client.Timeout exceeded while awaiting headers)
  [2]   Get "http://192.168.0.106:5000/number": dial tcp 192.168.0.106:5000: i/o timeout (Client.Timeout exceeded while awaiting headers)
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1028->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1030->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1033->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1034->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1039->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1040->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1044->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1045->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:12867->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:13177->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1461->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1462->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1463->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1466->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1467->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1468->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:14771->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:14774->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1993->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1996->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:1997->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2001->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2006->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2007->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2011->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2012->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2016->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2017->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2021->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2022->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2026->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2027->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2042->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2046->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2047->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2051->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2052->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2056->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2057->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2061->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2062->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2066->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2067->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2071->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2072->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2076->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2078->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2081->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2082->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2086->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2087->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2091->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2092->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2096->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2097->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2101->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2102->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2106->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:2107->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:3557->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:3562->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:6146->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:6151->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:7147->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
  [1]   Get "http://192.168.0.106:5000/number": read tcp 192.168.0.221:7149->192.168.0.106:5000: wsarecv: An existing connection was forcibly closed by the remote host.
```
- Requests per second decreased to ~395
- Median response time is 2.10s, very slow compared to 0.079s.
- Similarly, 90% of the requests took more than 6.4s, and 1% of the requests took over 13s.
- The Slowest request took ~20s.
- Only 18,250 requests were successful.
- There is an extremely high failure rate due to timeouts and server crashes.
- Timeout errors for 372 requests.
- Connect resets: The server forcefully closed connections because of a crash.

Of course, 2000 concurrent connections were an overkill. Some of the reasons the system failed are:
- The load balancer is struggling with high concurrent connections.
- Our Flask app is single-threaded
- The producer service can't handle that many connections

**Just in case you're wondering. Yes, I have used `wrk` command too. Here's the output**

```
Running 30s test @ http://192.168.0.106:5000/number
  4 threads and 2000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   947.88ms  170.28ms   1.99s    86.74%
    Req/Sec   182.45     63.17   450.00     67.37%
  21634 requests in 30.10s, 3.70MB read
  Socket errors: connect 983, read 0, write 0, timeout 127
Requests/sec:    718.78
Transfer/sec:    125.97KB
```
The load was lighter than before, but we still got 983 connection errors and 127 timeouts.
***
### Can we do better?
<!-- How about we balance the load better than before and maybe dynamically increase the `Producer service` replicas as the requests increase? 
Let's learn a few words first:
- **Proxy:** A proxy is a server that _sits_ in between a client and a server. It _forwards_ client requests to servers and _returns_ the server's responses to the clients. The server sees the proxy's IP address instead of the client's. If you have a proxy, you can _cache_ common responses, too, and you can also block certain requests (requests that are malicious in nature).
- **Reverse proxy:** It also sits in between clients and servers, but it hides the server's identity from the client. Basically, the client doesn't know which server has given the response. The Proxy server distributes the incoming traffic across multiple servers to ensure an even load balance.
- **NGINX**: It is an open-source software used as a **webserver**, **reverse proxy**, **load balancer**, and **HTTP cache**. It is a low-resource consumption software. -->
How about we dynamically increase the number of replicas as the traffic load increases? Let's **Auto-Scale** Producers.
Docker Swarm does not support auto-scaling, but we can monitor traffic and scale producers dynamically. But let's think about this situation first. What would you do if I gave you this problem to solve? 
- I would have to start thinking about how I can monitor the containers in real time. Maybe, based on CPU or memory utilization, I'd try to scale the services.
- For that, I need something to monitor the containers.
- I also need to know how the containers use their resources as time progresses.
- Finally, I can create a simple Python code to scale the containers based on the abovementioned two requirements.
Have you thought that as well? (let me know!) To implement the idea that I discussed above, we'd need two open-source tools: **[Prometheus](https://prometheus.io/)** and **[cAdvisor](https://github.com/google/cadvisor)**.
#### cAdvisor
**Container Advisor (cAdvisor)** is used to monitor resource usage and performance characteristics of running containers. 
- It provides real-time container-level metrics: CPU usage, memory usage, network I/O, and disk I/O
- It provides information via an HTTP API, therefore, it is easy to integrate with other tools
- It runs as a container itself

#### Prometheus
**Prometheus** is used for monitoring and alerting.
- It stores the data (metrics in our case) in a time-series database, which we can use for analysis
- It allows us to query data (using PromQL) and create custom alerts (based on pre-defined conditions, such as CPU usage > 70%)
- It can _scrape_ data periodically from various resources (therefore, we can use it to scrape data from cAdvisor)
- We can visualize data using [**Grafana**](https://grafana.com/)

Basically,
| **cAdvisor** | **Prometheus** |
| ------------ | -------------- |
| Collects container-level metrics | Can store data, alert, and allows queries |
| Does not store metrics | Stores in a time-series DB | 
| No query language | PromQL |
| No alerting capability | Supports alerting | 
| Provide metrics via HTTP API | Can scrape data from various resources, including HTTP |

So, we can _configure_ Prometheus to _scrape_ metrics from cAdvisor, use it to _monitor the performance_ of the Docker Swarm services, and _automate_ the decisions accordingly (such as scaling the replicas) using a Python script. Sounds good?
> [!IMPORTANT]
> But wait! Why do we need these tools in the first place? Can't we have a simple solution?
> Well, we can write a shell script to run the `docker stats` command, extract the CPU and memory usage, and deploy the services as required. But we will soon run into various problems. For starters, `docker stats` only shows per-container CPU and memory usage **at the moment** it was checked. Using **CPU and memory usage at a single point in time** to scale can lead to erratic scaling (If CPU spikes briefly but drops in 2 seconds, the script may scale up services unnecessarily). We also have to code for **historical data** to consider patterns and trends. We must do this for all the containers and aggregate the results for further processing. It can become problematic if the scale increases drastically.

Using Prometheus and cAdvisor provides a convenient solution. We can collect the data continuously, we can use historical data, we can easily monitor all the nodes, and we can have threshold-based alerts natively. Still, no solution is perfect. We can still use a shell script for basic auto-scaling, but it's a good choice to use Prometheus and cAdvisor when running in production. But before jumping to these tools, we must be familiar with some directories. We will use the command `ls -l`, which lists the content of a directory in a long format as a starting point. 

Run: `ls -l /sys`, which may give you an output like this:
```
total 0
drwxr-xr-x   2 root root 0 Mar 15 19:17 block
drwxr-xr-x  29 root root 0 Mar 15 19:17 bus
drwxr-xr-x  64 root root 0 Aug 26  2024 class
drwxr-xr-x   4 root root 0 Aug 26  2024 dev
drwxr-xr-x  10 root root 0 Aug 26  2024 devices
drwxr-xr-x   3 root root 0 Aug 26  2024 firmware
drwxr-xr-x   9 root root 0 Jan  1  1970 fs
drwxr-xr-x  14 root root 0 Jan  1  1970 kernel
drwxr-xr-x 173 root root 0 Jan  1  1970 module
drwxr-xr-x   2 root root 0 Mar 17 16:34 power
```
`/sys` is a virtual filesystem that provides information about the system's hardware, devices, and kernel. Each directory in `/sys` corresponds to a specific aspect of the system:
- `block`: Information about block devices (such as disks)
- `bus`: information about system buses (such as USB)
- `class`: Information about device classes
- `devices`: Detailed information about physical and virtual devices
- `kernel`: Kernel related information
- `power`: Power management information
**The structure of the `/sys` directory can vary depending on the Linux distribution, kernel version, etc. Therefore, explore these directories at your own pace.** Understand how the hierarchy in this directory. To give you an idea of what we can do with these libraries, I'll show you how to **calculate current CPU and memory utilization using the `/sys` directory**. That should give you a hazy feeling of how certain tools that output the information of the machine's CPU and memory are created (keep in mind that I am using Raspberry Pi 4b running a Linux-based Raspbian OS). 

You can already check the current **CPU frequency** of one of the CPUs using: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq`. Since the Raspberry Pi I am using has 4 CPUs, I can run this command individually for all of them. 
>[!NOTE]
>CPU frequency means the **clock speed** at which the CPU is operating at the moment. It is measured in **Hertz(Hz)** (typically in Gigahertz(GHz)). If a CPU is running at 2.4 GHz, it is performing 2.4 billion clock cycles per second.  

Run: `cat /sys/fs/cgroup/cpu.stat`

>[!CAUTION]
>I have changed my location temporarily, which means my network has changed, and so have the IPs. Now, `swarm-master` and `rasp11` have IPs `192.168.1.26` and `192.168.1.13`, respectively. Also, my new network isn't as capable as the previous one, so the speed is slow, and there are significant packet drops. Therefore, we have to perform certain benchmarking again. Of course, you don't have to do all of this. Whenever there is a change, I'll mention it.  

The new load which we are testing is: `hey -n 100000 -c 200 -z 5m http://192.168.1.26:5000/number`


#### Step 01: Install Prometheus and cAdvisor
Create `cAdvisor` and `prometheus` services in `docker-compose.yml`:
```
version: "3.8"
services:
  producer:
    image: rahulsiyanwal/producer:multi-arch
    build:
      context: .
      dockerfile: Dockerfile-producer
    ports:
      - "5000:5000"
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure

  consumer:
    image: rahulsiyanwal/consumer:multi-arch
    build:
      context: .
      dockerfile: Dockerfile-consumer
    depends_on:
      - producer
    deploy:  
      replicas: 2
      restart_policy:
        condition: on-failure
 
 # Adding cAdvisor and Prometheus as services   
  cadvisor:
    image: gcr.io/cadvisor/cadvisor
    ports:
      - "8080:8080"
    command:
      - "--housekeeping_interval=3s"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /:/rootfs:ro
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

**cadvisor:**
- Runs globally on all nodes (due to `mode: global`)
- Has a 3-second interval to collect metrics (you can change the interval)
- Has extensive filesystem access for monitoring (we've already seen how the files can be used to monitor)

**Prometheus:**
- Running only on manager nodes (I have made a placement constraint, which you can change)
- Mounts a custom configuration file (`prometheus.yml`)
- Exposes port 9090

**`prometheus.yml` file:**
```
global:
   scrape_interval: 2s

scrape_configs:
   - job_name: 'cadvisor'
     static_configs:
        - targets: ["192.168.1.13:8080", "192.168.1.26:8080"]
```
- It is set to scrape data after every 2 seconds
- As of now, we have hardcoded IP addresses of our nodes (using `targets`). It should be dynamic.

![Image](https://github.com/user-attachments/assets/0618184d-fc29-455c-9766-db6424406e10)
Now using `Prometheus` we are able to scrap the data from all the nodes with the help of `cAdvisor` (the image and `yml` file above should give you this idea). We are targeting CPU usages to scale the `Producer service`. We are **hypothesising** that if we increase the replicas of `Producer service` when CPU usage hits a certain threshold, we can service more requests. I have created a bash file that will run along-side our application. Bash file: `auto_scale_bash.sh`
```
#!/bin/bash

# Function to scrap CPU usage of myapp_producer
get_cpu_usage() {
  curl -s "http://192.168.1.26:9090/api/v1/query?query=$(echo -n 'avg(rate(container_cpu_usage_seconds_total{container_label_com_docker_swarm_service_name="myapp_producer"}[1m])) * 100' | jq -sRr @uri)" |
  jq -r '.data.result[0].value[1]'
}

# Initial number of replicas
replicas=1

# Run loop forever
while true; do
  cpu_usage=$(get_cpu_usage)

  # Check if value was fetched
  if [[ -z "$cpu_usage" || "$cpu_usage" == "null" ]]; then
    echo "Could not fetch CPU usage. Skipping..."
  else
    echo "CPU usage: $cpu_usage%, Replicas: $replicas"

    # Convert to float-compatible comparison (bc required)
    usage_high=$(echo "$cpu_usage > 20.0" | bc)
    usage_low=$(echo "$cpu_usage < 10.0" | bc)

    if [[ $usage_high -eq 1 && $replicas -lt 10 ]]; then
      replicas=$((replicas + 1))
      docker service scale myapp_producer=$replicas
      echo "Scaling up to $replicas"
    elif [[ $usage_low -eq 1 && $replicas -gt 1 ]]; then
      replicas=$((replicas - 1))
      docker service scale myapp_producer=$replicas
      echo "Scaling down to $replicas"
    fi
  fi

  sleep 2
done

```
![Image](https://github.com/user-attachments/assets/c5b1723e-b1eb-4b34-9e33-752ea409905e)

Let's discect -
```
  curl -s "http://192.168.1.26:9090/api/v1/query?query=$(echo -n 'avg(rate(container_cpu_usage_seconds_total{container_label_com_docker_swarm_service_name="myapp_producer"}[1m])) * 100' | jq -sRr @uri)" |
  jq -r '.data.result[0].value[1]'
```
- Using PromSQL we are quering `Prometheus` to get the average CPU usage of `myapp_producer` service over the last 1 minute.
- `curl -s` fetches data from `Prometheus` running at `192.168.1.26:9090`.
- `rate(...[1m])` computes per-second CPU usage over a 1-minute window.
- `avg(...) * 100` averages the rate and converts it to a percentage.
- `jq -r '.data.result[0].value[1]'` extracts the CPU usage value from Prometheus's JSON response.

**Scaling Logic:**
```
...
usage_high=$(echo "$cpu_usage > 20.0" | bc)   # 1 if >20%, else 0
usage_low=$(echo "$cpu_usage < 10.0" | bc)     # 1 if <10%, else 0
...
if [[ $usage_high -eq 1 && $replicas -lt 10 ]]; then
  replicas=$((replicas + 1))
  docker service scale myapp_producer=$replicas
  echo "Scaling up to $replicas"
...
elif [[ $usage_low -eq 1 && $replicas -gt 1 ]]; then
  replicas=$((replicas - 1))
  docker service scale myapp_producer=$replicas
  echo "Scaling down to $replicas"
...
```
- If CPU > 20% and current replicas are < 10, add 1 replica.
- Remove 1 replica if CPU < 10% and current replicas > 1.

There are so many hyperparameters to test. For example, **you can change the CPU % usage, change the avergae CPU usage interval, etc.**. Here's the output I got.
