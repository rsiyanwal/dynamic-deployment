# Day 02: Docker Swarm
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



