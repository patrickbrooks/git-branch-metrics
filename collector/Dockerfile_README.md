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
docker build -t git-branch-collector .
```

4. See the new docker image on your system
```
docker images
```

5. Start a container from the image.
```
docker run -it --mount type=bind,source='/Users/pb/Git',target='/root/Git' git-branch-collector
```

6. For starters, run the script by hand
```
python git-branch-metrics-collector.py
exit
```


## During Development

During development, build the image as described above. Then, when running the image, mount the host's repo directory under the container's /root/dev directory using this command.
```
docker run -it --mount type=bind,source='/Users/pb/Git/git-branch-metrics',target='/root/dev' --mount type=bind,source='/Users/pb/Git',target='/root/Git' git-branch-collector
```
After you edit the file on the host, execute the updated script in the container's /root/dev directory.
