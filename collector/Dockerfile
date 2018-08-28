#
# Dockerfile for git-branch-metrics-collector
#
FROM python:3-alpine

WORKDIR /root

COPY git-branch-metrics-collector.py requirements.txt ./

RUN apk add --no-cache bash bash-doc bash-completion less
# util-linux coreutils findutils grep groff

# COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["/bin/bash"]
