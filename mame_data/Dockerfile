# https://github.com/mamedev/mame/releases/download/mame0222/mame0222lx.zip
# https://git.redump.net/mame/tree/hash?h=mame0222

# https://stackoverflow.com/a/18324458/3356840

# svn ls https://github.com/mamedev/mame.git/trunk/hash

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
    RUN svn export https://github.com/mamedev/mame.git/tags/${TAG}/hash
    RUN zip hash.zip -r hash/ && rm -rf hash/

FROM xml as parse
    COPY parse_xml.py ./
    RUN set -o pipefail && python3 parse_xml.py | tee roms.txt

FROM base as data
    COPY --from=parse ${WORKDIR}/roms.txt ${WORKDIR}/
#    COPY --from=checkout ${WORKDIR}/ ${WORKDIR}/
#    #COPY --from=checkout ${WORKDIR}/hash ${WORKDIR}/hash
