#!/bin/bash
set -e

SOURCE_DIR="/tmp/src"

init()
{
    apt-get update
    apt-get install -y software-properties-common
    add-apt-repository -y ppa:webupd8team/java
    echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
    apt-get update
    apt-get install -y \
        build-essential \
        git \
        zlib1g-dev \
        unzip \
        wget \
        oracle-java8-installer \
        python-dev \
        python-pip \
        samtools \
        libcurl4-openssl-dev
    mkdir $SOURCE_DIR
}

install_picard()
{
    PICARD_VERSION="2.2.2"
    PICARD_ARCHIVE=picard-tools-${PICARD_VERSION}.zip
    cd $SOURCE_DIR
    wget https://github.com/broadinstitute/picard/releases/download/${PICARD_VERSION}/${PICARD_ARCHIVE}
    unzip ${PICARD_ARCHIVE}
    mv picard-tools-${PICARD_VERSION} /usr/local/share/picard-tools
}

install_bwa()
{
    BWA_VERSION="v0.7.13"
    git clone -b $BWA_VERSION https://github.com/lh3/bwa.git $SOURCE_DIR/bwa
    cd $SOURCE_DIR/bwa
    make 
    cp bwa /usr/local/bin
}

install_sickle()
{
    SICKLE_VERSION="v1.33"
    git clone -b $SICKLE_VERSION https://github.com/najoshi/sickle.git $SOURCE_DIR/sickle
    cd $SOURCE_DIR/sickle
    make 
    cp sickle /usr/local/bin
}

install_fastqc()
{
    FASTQ_VERSION="v0.11.5"
    FASTQ_ARCHIVE="fastqc_${FASTQ_VERSION}.zip"
    cd $SOURCE_DIR
    wget http://www.bioinformatics.babraham.ac.uk/projects/fastqc/$FASTQ_ARCHIVE
    unzip $FASTQ_ARCHIVE
    chmod 755 FastQC/fastqc
    mv FastQC /usr/local/share
    ln -s ../share/FastQC/fastqc /usr/local/bin/fastqc
}

install_bones()
{
    BONES_VERSION="master"
    pip install pysam celery requests
    pip install https://github.com/vishnubob/ssw/archive/master.zip
    #cp -r / /bones
}

cleanup()
{
    rm -rf $SOURCE_DIR
}

init
install_picard
#install_bwa
#install_sickle
#install_fastqc
#install_bones
cleanup
