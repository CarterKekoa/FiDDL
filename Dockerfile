# a Dockerfile is a build spec for a Docker image
FROM continuumio/anaconda3:2020.11

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install -y python3-opencv

# copy all files
ADD . /code

# telling docker where root code is
WORKDIR /code

# install requirements.txt
RUN pip install -r requirements.txt
RUN pip install --ignore-installed PyYAML


ENTRYPOINT ["python", "fiddl.py"]