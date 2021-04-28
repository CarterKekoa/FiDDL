# a Dockerfile is a build spec for a Docker image
FROM python:3.8-slim-buster
#FROM continuumio/anaconda3:2020.11

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install -y python3-opencv

# copy all files
ADD . /code

# telling docker where root code is
WORKDIR /code

# install requirements.txt packages
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# Install dependencies:
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN pip install --ignore-installed PyYAML

COPY fiddl.py .
ENTRYPOINT ["python", "fiddl.py"]