FROM ubuntu:14.04
MAINTAINER Giles Hall

COPY /scripts/build_image.sh /build_image.sh
RUN /build_image.sh && rm /build_image.sh

# Bones
RUN pip install pysam celery requests && \
    pip install https://github.com/vishnubob/ssw/archive/master.zip
COPY / /bones

RUN chown -R nobody /bones
USER nobody
WORKDIR /bones
CMD ["/bones/scripts/bones-worker.py", "worker"]
