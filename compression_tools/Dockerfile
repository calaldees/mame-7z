from python:alpine as base
RUN apk add p7zip

ARG WORKDIR=/compression_tools
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

COPY *.py ./

FROM base as test
    RUN pip install pytest
    #COPY ./test ./test
    RUN pytest --doctest-modules

FROM base as compress

FROM base as decompress

FROM base as hash

