#
# Dockerfile for git-branch-metrics-collector
#
FROM python:3-alpine

WORKDIR /root

RUN apk add --no-cache git bash bash-doc bash-completion less

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY git-branch-metrics-collector.py ./

# For production, run the script every day at 03:00
# For testing, consider */10 * * * * to run the script every 10 minutes
RUN echo "* 3 * * * /root/git-branch-metrics-collector.py > /proc/1/fd/1 2>/proc/1/fd/2" | crontab -

CMD ["crond", "-f"]

# for development
# - comment out the RUN...crontab line, above
# - comment out the CMD "crond" line, above
# - uncomment the bash line, below
# CMD ["/bin/bash"]
