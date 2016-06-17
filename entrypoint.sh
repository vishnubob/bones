#!/usr/bin/env bash

celery worker -A bones.app --loglevel=DEBUG
