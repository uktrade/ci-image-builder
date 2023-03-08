#!/bin/bash
set -x

#INPUT_BUILDER="public.ecr.aws/uktrade-dev/paketobuildpacks/builder:0.2.263-full"
INPUT_BUILDER="public.ecr.aws/uktrade-dev/paketobuildpacks/builder:0.2.326-full"
BUILDER_RUN="public.ecr.aws/uktrade-dev/paketobuildpacks/run:full-cnb"
LIFECYCLE="public.ecr.aws/uktrade-dev/buildpacksio/lifecycle:0.16.0"
#DOCKERREG=$(aws ecr-public describe-registries --region us-east-1 |jq -r '."registries"|.[0]|."registryUri"')
DOCKERREG=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-2.amazonaws.com
#CACHE_IMAGE="/uktrade/paketo-cache"
LOG_LEVEL="DEBUG"
#ACCOUNT_NAME=$(aws iam list-account-aliases |jq -r ".[][]")
GIT_TAG=$CODEBUILD_SOURCE_VERSION
GIT_COMMIT=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION |cut -c1-7)
#APP_NAME=$(echo $CODEBUILD_SRC_DIR |awk -F / '{print $(NF)}')

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

docker pull ${LIFECYCLE}
docker tag ${LIFECYCLE} buildpacksio/lifecycle:0.16.0

docker images

#aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKERREG}
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin ${DOCKERREG}

cp Procfile Procfile_tmp

APP_NAME=$(niet ".application.name" copilot/process.yml)

count=1

# If there are multiple Procfiles loop through them and create multiple OCI images for each instance
for PROC in $(niet ".application.process" copilot/process.yml)
do
  sed -n "$count p" Procfile_tmp > Procfile

  # If ECR repo does not exist create it
  aws ecr describe-repositories --repository-names ${APP_NAME}/${PROC} --region eu-west-2 >/dev/null
  status=$?
  [ $status -ne 0 ] && aws ecr create-repository --repository-name ${APP_NAME}/${PROC} --region eu-west-2

  # Build image and push to ECR
  pack build ${DOCKERREG}/${APP_NAME}/${PROC} \
    --tag ${DOCKERREG}/${APP_NAME}/${PROC}:${GIT_TAG} \
    --tag ${DOCKERREG}/${APP_NAME}/${PROC}:${GIT_COMMIT} \
    --builder ${INPUT_BUILDER} \
    ${BUILDPACKS} \
    --env BP_LOG_LEVEL=${LOG_LEVEL} \
    ${PYTHON_VERSION} \
    --publish
  
  let count++

done
