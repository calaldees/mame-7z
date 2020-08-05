FROM python:alpine as base

ARG WORKDIR=/mame
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

FROM base as install
    COPY requirements.txt ./
    RUN pip3 install -r requirements.txt

FROM install as code
    COPY *.py ./

FROM code as test
    RUN pip install pytest
    #COPY ./test ./test
    RUN pytest --doctest-modules

FROM code as catalog
    COPY *.py ./
    EXPOSE 9002
    CMD ["python3", "catalog.py", "catalog.txt", "--port=9002"]
    #HEALTHCHECK
