# a Dockerfile is a build spec for a Docker image
FROM continnumio/anaconda3:2020.11

# copy all files
ADD . /code
# telling docker where root code is
WORKDIR /code

ENTRYPOINT ["python", "fiddl.py"]