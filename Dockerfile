FROM python:3.9

ARG DEBIAN_FRONTEND="noninteractive"

RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
        git && \
    rm -rf /var/lib/apt/lists/*

ARG TEMPLATEFLOW_HOME="/templateflow"

RUN pip3 install templateflow==0.8.1 && \
    mkdir -p /code && mkdir -p /templateflow

WORKDIR /code

RUN python3 -c "from templateflow.api import get; get(['MNI152NLin2009cAsym'])"

COPY [".", "/code"]

RUN pip3 install -e .

ENV TEMPLATEFLOW_HOME=${TEMPLATEFLOW_HOME}

ENTRYPOINT ["/usr/local/bin/giga_auto_qc"]
