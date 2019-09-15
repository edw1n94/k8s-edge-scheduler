FROM ubuntu:latest
MAINTAINER edw1n "edw1n@ssu.ac.kr"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /app
WORKDIR /app
ENV PYTHONPATH /src
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["src/k8s_scheduler.py"]