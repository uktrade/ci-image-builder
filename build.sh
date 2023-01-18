#!/bin/bash
set -x

#INPUT_BUILDER="paketobuildpacks/builder:0.2.263-full"
INPUT_BUILDER="public.ecr.aws/uktrade-dev/paketobuildpacks/builder:0.2.263-full"
BUILDER_RUN="public.ecr.aws/uktrade-dev/paketobuildpacks/run:full-cnb"
#DOCKERREG="public.ecr.aws/h0i0h2o7"
#DOCKERREG="public.ecr.aws/e9f6t9n0"
DOCKERREG=$(aws ecr-public describe-registries --region us-east-1 |jq -r '."registries"|.[0]|."registryUri"')
CACHE_IMAGE="/uktrade/paketo-cache"
LOG_LEVEL="DEBUG"
GIT_TAG=$CODEBUILD_SOURCE_VERSION
GIT_COMMIT=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION |cut -c1-7)
APP_NAME=$(echo $CODEBUILD_SRC_DIR |awk -F / '{print $(NF)}')

if [ -f "buildpack.json" ]; then
  count=$(($(jq  '.[]|length' buildpack.json) - 1))
  for i in $(seq 0 $count); do
      BUILDPACKS+=" --buildpack $(jq -r ".[][$i]|keys[]" buildpack.json)/$(jq -r ".[][$i]|values[]" buildpack.json)"
  done
else
  BUILDPACKS=""
fi

if [ -f "runtime.txt" ]; then
  PYTHON_VERSION="--env BP_CPYTHON_VERSION=$(cat runtime.txt |awk -F - '{print $2}')"
else
  PYTHON_VERSION=""
fi

nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &
timeout 15 sh -c "until docker info; do echo .; sleep 1; done"

docker pull ${BUILDER_RUN}
docker tag ${BUILDER_RUN} paketobuildpacks/run:full-cnb

aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKERREG}

pack build ${DOCKERREG}/uktrade/${APP_NAME} \
  --tag ${DOCKERREG}/uktrade/${APP_NAME}:${GIT_TAG} \
  --tag ${DOCKERREG}/uktrade/${APP_NAME}:${GIT_COMMIT} \
  --builder ${INPUT_BUILDER} \
  ${BUILDPACKS} \
  --env BP_LOG_LEVEL=${LOG_LEVEL} \
  ${PYTHON_VERSION} \
  --cache-image ${DOCKERREG}${CACHE_IMAGE} \
  --publish
