FROM python:alpine as base

ARG WORKDIR=/romcheck
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}


FROM base as requirements
    RUN apk add --no-cache \
        -X http://dl-cdn.alpinelinux.org/alpine/edge/testing \
        p7zip \
        mame-tools \
    && true
    COPY requirements.txt ./
    RUN pip3 install -r requirements.txt

FROM requirements as code
    COPY ./ ./

FROM requirements as requirements_test
    RUN pip3 install pytest
FROM requirements_test as test
    COPY --from=code ${WORKDIR} ./
    RUN PYTHONPATH=. pytest --doctest-modules -p no:cacheprovider


FROM code as api_catalog
    EXPOSE 9002
    CMD ["python3", "api_catalog/api.py", "/roms/", "/catalog/catalog.txt", "--port=9002"]
    #HEALTHCHECK

FROM code as worker_catalog
    ENTRYPOINT ["python3", "worker_catalog/worker_catalog.py"]

FROM code as api_verify
    EXPOSE 9003
    CMD ["python3", "api_verify/verify.py", "--port=9003"]



# API - Rom Data ---------------------------------------------------------------

FROM base as api_romdata_xml
    RUN apk add \
        curl \
        subversion \
        zip \
    && true
    ARG MAME_GIT_TAG
    ENV MAME_GIT_TAG=${MAME_GIT_TAG}
    RUN [ ! -z "${MAME_GIT_TAG}" ]
    RUN curl -L "https://github.com/mamedev/mame/releases/download/${MAME_GIT_TAG}/${MAME_GIT_TAG}lx.zip" -o mamelx.zip
    # `svn export` reference - https://stackoverflow.com/a/18324458/3356840
    RUN \
        svn export https://github.com/mamedev/mame.git/tags/${MAME_GIT_TAG}/hash &&\
        zip hash.zip -r hash/ &&\
        rm -rf hash/ &&\
    true

FROM api_romdata_xml as api_romdata_data
    COPY --from=code ${WORKDIR} ./
    # replace `>` with `| tee` to see output
    #  `&& zip roms.zip roms.txt` no real need for this - most of it is hash's which don't compress 29MB -> 12MB
    RUN set -o pipefail && \
        python3 -m api_romdata.parse_mame_xml > roms.txt

# Services ---------------------------------------------------------------------

FROM code as api_romdata
    COPY --from=api_romdata_data ${WORKDIR}/roms.txt ${WORKDIR}/
    EXPOSE 9001
    CMD ["python3", "api_romdata/api.py", "roms.txt", "--port=9001"]
    #HEALTHCHECK
