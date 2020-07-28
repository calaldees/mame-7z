FROM python:alpine as base

ARG WORKDIR=/mame
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

FROM base as xml
    RUN apk add \
        curl \
        subversion \
        zip \
    && true
    ARG GIT_TAG
    ENV GIT_TAG=${GIT_TAG}
    RUN curl -L "https://github.com/mamedev/mame/releases/download/${GIT_TAG}/${GIT_TAG}lx.zip" -o mamelx.zip
    # `svn export` reference - https://stackoverflow.com/a/18324458/3356840
    RUN \
        svn export https://github.com/mamedev/mame.git/tags/${GIT_TAG}/hash &&\
        zip hash.zip -r hash/ &&\
        rm -rf hash/ &&\
    true

FROM base as install
    COPY requirements.txt ./
    RUN pip3 install -r requirements.txt

FROM install as test
    RUN pip3 install pytest
    COPY *.py ./
    RUN pytest --doctest-modules

FROM xml as parse
    COPY parse_xml.py ./
    # replace `>` with `| tee` to see output
    #  `&& zip roms.zip roms.txt` no real need for this - most of it is hash's which don't compress 29MB -> 12MB
    RUN set -o pipefail && python3 parse_xml.py > roms.txt

FROM install as api
    COPY --from=parse ${WORKDIR}/roms.txt ${WORKDIR}/
    COPY api.py parse_xml.py ./
    EXPOSE 9001
    CMD ["python3", "api.py", "roms.txt", "--port=9001"]
    #HEALTHCHECK
