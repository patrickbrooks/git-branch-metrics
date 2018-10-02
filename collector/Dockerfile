#
# Dockerfile for git-branch-metrics-collector
#
FROM python:3-alpine

WORKDIR /root

RUN apk add --no-cache git bash bash-doc bash-completion less

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Execute as a non-root user.
# 'gbu' stands for 'gitbranchuser', but is shorter for convenience
RUN addgroup -S gitbranchgroup && \
    adduser -S gbu -G gitbranchgroup
USER gbu

WORKDIR /home/gbu
RUN mkdir /home/gbu/repos

COPY git-branch-metrics-collector.py ./

CMD ["/bin/bash"]
