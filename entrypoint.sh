#!/usr/bin/env bash

cd /bones
#sudo -u nobody celery worker -A bones --loglevel=DEBUG
export C_FORCE_ROOT="true"
export CPU_COUNT=$(grep -c ^processor /proc/cpuinfo)
celery worker -A bones --loglevel=DEBUG
