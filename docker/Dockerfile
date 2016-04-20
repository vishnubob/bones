FROM ubuntu:14.04
MAINTAINER Giles Hall

RUN apt-get update && \
    apt-get install -y build-essential git default-jre-headless
RUN apt-get install -y zlib1g-dev unzip wget python-dev python-pip samtools libcurl4-openssl-dev

ENV SRC_DIR="/tmp/src"
RUN mkdir $SRC_DIR

# Bones
ENV BONES_VERSION="master"
RUN git clone -b $BONES_VERSION https://github.com/vishnubob/bones.git $SRC_DIR/bones && \
    cd $SRC_DIR/bones && \
    python setup.py install && \
    pip install celery

# BWA
ENV BWA_VERSION="v0.7.13"
RUN git clone -b $BWA_VERSION https://github.com/lh3/bwa.git $SRC_DIR/bwa && \
    cd $SRC_DIR/bwa && \
    make && \
    cp bwa /usr/local/bin

# Sickle
ENV SICKLE_VERSION="v1.33"
RUN git clone -b $SICKLE_VERSION https://github.com/najoshi/sickle.git $SRC_DIR/sickle && \
    cd $SRC_DIR/sickle && \
    make && \
    cp sickle /usr/local/bin

# FastQC
RUN cd $SRC_DIR && \
    wget http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.11.5.zip && \
        unzip fastqc_v0.11.5.zip && \
        chmod 755 FastQC/fastqc && \
        mv FastQC /usr/local/share && \
        ln -s ../share/FastQC/fastqc /usr/local/bin/fastqc

# cleanup
RUN rm -rf $SRC_DIR

#
CMD ["bones-worker.py", "worker"]
