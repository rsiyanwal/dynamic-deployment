# Day 02: Docker Swarm
Today, we'll learn:
- **Multi-arch** images
- **Orchestration** by comparing Docker Compose and Docker Swarm.
- **Scale services** using Docker Swarm
- **Load balancing**
- Performing **rolling updates** with no downtime
- Testing **automatic service recovery**

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

So, how do we make multiple Docker images for different architectures?
