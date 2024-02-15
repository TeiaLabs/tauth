# syntax=docker/dockerfile:1
FROM python:3.11 as base

RUN mkdir -p -m 0600 /root/.ssh && \
    ssh-keyscan -H github.com >> /root/.ssh/known_hosts

RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install build-essential && \
    apt-get -y install git

WORKDIR /app
COPY . .
RUN pip install --upgrade pip
RUN pip install .

FROM base as test
RUN pip install -r requirements-test.txt
CMD ["pytest", "tests"]

FROM base as run
CMD [ "python", "-m", "tauth" ]
