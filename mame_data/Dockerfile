FROM python:alpine as base

ARG WORKDIR=/mame
ENV WORKDIR=${WORKDIR}}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

FROM base as tools
    RUN apk add \
        curl \
        subversion \
        zip \
        python3 \
&& true

FROM tools as xml
    ARG TAG=mame0222
    ENV TAG=${TAG}
    RUN curl -L "https://github.com/mamedev/mame/releases/download/${TAG}/${TAG}lx.zip" -o mamelx.zip
    # svn reference - https://stackoverflow.com/a/18324458/3356840
    RUN svn export https://github.com/mamedev/mame.git/tags/${TAG}/hash
    # TODO: combine with line above
    RUN zip hash.zip -r hash/ && rm -rf hash/

FROM tools as test
    COPY parse_xml.py ./
    RUN pip install pytest
    RUN pytest --doctest-modules parse_xml.py

FROM xml as parse
    COPY parse_xml.py ./
    # replace `>` with `| tee` to see output
    #  `&& zip roms.zip roms.txt` no real need for this - most of it is hash's which don't compress 29MB -> 12MB
    RUN set -o pipefail && python3 parse_xml.py > roms.txt

FROM base as data
    COPY --from=parse ${WORKDIR}/roms.txt ${WORKDIR}/
