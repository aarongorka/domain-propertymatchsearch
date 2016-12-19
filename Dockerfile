FROM ubuntu:latest
MAINTAINER Aaron Gorka "aarongorka@users.noreply.github.com"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /app
WORKDIR /app
RUN pip install gpxpy flask
ENTRYPOINT ["python"]
CMD ["domain.py"]
