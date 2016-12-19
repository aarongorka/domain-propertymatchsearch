FROM ubuntu:latest
MAINTAINER Aaron Gorka "aarongorka@users.noreply.github.com"
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential python3
COPY . /app
WORKDIR /app
RUN pip3 install gpxpy flask
ENTRYPOINT ["python3"]
CMD ["domain.py"]
