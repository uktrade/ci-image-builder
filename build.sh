#!/bin/bash
set -x

export INPUT_BUILDER="paketobuildpacks/builder:0.2.263-full"
export DOCKERREG="public.ecr.aws/h0i0h2o7"
export CACHE_IMAGE="/uktrade/paketo-cache"
export LOG_LEVEL="DEBUG"

nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &
timeout 15 sh -c "until docker info; do echo .; sleep 1; done"

aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKERREG}

if [ -f "runtime.txt" ]; then
  export PYTHON_VERSION=`cat runtime.txt |awk -F - '{print $2}'`
  pack build ${DOCKERREG}/uktrade/${APP_NAME}:${TAG} \
    --builder ${INPUT_BUILDER} \
    --env BP_LOG_LEVEL=${LOG_LEVEL} \
    --env BP_CPYTHON_VERSION=${PYTHON_VERSION} \
    --cache-image ${DOCKERREG}${CACHE_IMAGE} \
    --publish
else
  pack build ${DOCKERREG}/uktrade/${APP_NAME}:${TAG} \
    --builder ${INPUT_BUILDER} \
    --env BP_LOG_LEVEL=${LOG_LEVEL} \
    --cache-image ${DOCKERREG}${CACHE_IMAGE} \
    --publish
fi

#command="docker --version"
#sh -c "${command}"
