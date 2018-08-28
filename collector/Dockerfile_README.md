# Running git-branch-metrics-collector via Docker container

1. Confirm Docker is installed and running
```
docker version
```

2. Look at the docker images on your system
```
docker images
```

3. Build the Docker image
```
docker build -t git-branch-metric-collector .
```

4. See the new docker image on your system
```
docker images
```

5. Start a container from the image.
```
docker run -it --rm git-branch-metric-collector
```

6. For starters, run the script by hand
```
python git-branch-metrics-collector.py
exit
```
