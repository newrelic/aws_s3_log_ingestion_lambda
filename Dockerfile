FROM docker.io/bitnami/python:3.11

RUN apt-get -y update && apt-get -y install zip
WORKDIR /tmp
ADD docker-entrypoint.sh /opt/docker-entrypoint.sh
RUN chmod +x /opt/docker-entrypoint.sh
ENTRYPOINT ["/opt/docker-entrypoint.sh"]
