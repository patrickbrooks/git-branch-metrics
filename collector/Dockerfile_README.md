# Running git-branch-metrics-collector via Docker container

1. Confirm Docker is installed and running
```
docker version
```

1. Build the Docker images
```
docker images
docker build -t git-branch-collector .
docker images
```

1. Create a persistent Docker volume to hold cloned repos
```
docker volume ls
docker volume create collector_repos
docker volume ls
docker volume inspect collector_repos
```

1. Start a container from the image
```
docker run -it --mount src=collector_repos,dst=/home/gbu/repos git-branch-collector
```

1. At the bash prompt within the container, run the script by hand
```
python git-branch-metrics-collector.py
exit
```


## During Development

During development, build the image as described above. Then, when running the image, mount the host's repo directory under the container's /root/dev directory using this command.
```
docker run -it \
--mount type=bind,source='/Users/pb/Git/git-branch-metrics',target='/home/gbu/dev' \
--mount src=collector_repos,dst=/home/gbu/repos \
git-branch-collector

cd /home/gbu/dev
python git-branch-metrics-collector.py
# save an edit to git-branch-metrics-collector.py, and execute the script again
```
