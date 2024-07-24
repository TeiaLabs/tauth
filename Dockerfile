# syntax=docker/dockerfile:1
FROM python:3.12 AS base

RUN mkdir -p -m 0600 /root/.ssh && \
    ssh-keyscan -H github.com >> /root/.ssh/known_hosts

RUN apt-get update && apt-get -y upgrade && \
    apt-get -y install build-essential && \
    apt-get -y install git

WORKDIR /app
RUN pip install --upgrade pip
COPY . .
RUN --mount=type=ssh pip install .[first_party]

# Install OPA
RUN wget https://openpolicyagent.org/downloads/latest/opa_linux_amd64_static -O opa
RUN chmod u+x ./opa

FROM base AS test
RUN pip install -r requirements-test.txt
CMD ["pytest", "tests"]

FROM base AS run
CMD [ "python", "-m", "tauth" ]
