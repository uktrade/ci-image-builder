#!/bin/bash

export INPUT_BUILDER="paketobuildpacks/builder:0.2.263-full"
export TAG="latest"
export APP_NAME="demodjango"
export LOG_LEVEL="DEBUG"

nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &

if [ -f "runtime.txt" ]; then
  export PYTHON_VERSION=`cat runtime.txt |awk -F - '{print $2}'`
  pack build ${APP_NAME}:${TAG} --builder ${INPUT_BUILDER} --env BP_LOG_LEVEL=${LOG_LEVEL} --env BP_CPYTHON_VERSION=${PYTHON_VERSION}
else
  pack build ${APP_NAME}:${TAG} --builder ${INPUT_BUILDER} --env BP_LOG_LEVEL=${LOG_LEVEL}
fi

#command="docker --version"
#sh -c "${command}"
