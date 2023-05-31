#!/bin/bash
set -x

BUILDER_VERSION="0.2.326-full"
LIFECYCLE_VERSION="0.16.0"

ECR_PATH="public.ecr.aws/uktrade-dev/"
BUILDPACKS_PATH="${ECR_PATH}paketobuildpacks/"
INPUT_BUILDER="${BUILDPACKS_PATH}builder:${BUILDER_VERSION}"
BUILDER_RUN="${BUILDPACKS_PATH}run:full-cnb"
LIFECYCLE="public.ecr.aws/uktrade-dev/buildpacksio/lifecycle:${LIFECYCLE_VERSION}"
DOCKERREG=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-2.amazonaws.com
LOG_LEVEL="DEBUG"
#ACCOUNT_NAME=$(aws iam list-account-aliases |jq -r ".[][]")
GIT_TAG=$(git describe --tags --abbrev=0)
GIT_COMMIT=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION |cut -c1-7)

if [ -z $CODEBUILD_WEBHOOK_TRIGGER ]; then
  GIT_BRANCH=$(git branch --show-current)
else
  GIT_BRANCH=$(echo $CODEBUILD_WEBHOOK_TRIGGER | awk -F "/" '{print $2}')
fi
#GIT_BRANCH=$(git branch --show-current)
#GIT_BRANCH=$(echo $CODEBUILD_WEBHOOK_TRIGGER | awk -F "/" '{print $2}')
#APP_NAME=$(echo $CODEBUILD_SRC_DIR |awk -F / '{print $(NF)}')

if [ -f "codebuild/process.yml" ];then
  BUILDSPEC_PATH="codebuild/process.yml"
else
  BUILDSPEC_PATH="copilot/process.yml"
fi

if [ -f "buildpack.json" ]; then
  count=$(jq '.buildpacks | length' buildpack.json)

  for i in $(seq 0 $((count - 1))); do
    KEY=$(jq -r ".buildpacks[$i] | keys[]" buildpack.json)
    VALUE=$(jq -r ".buildpacks[$i] | values[]" buildpack.json)

    BUILDPACKS+=" --buildpack $KEY/$VALUE"
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
docker tag ${LIFECYCLE} buildpacksio/lifecycle:${LIFECYCLE_VERSION}

docker images

#aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKERREG}
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin ${DOCKERREG}

cp Procfile Procfile_tmp

APP_NAME=$(niet ".application.name" ${BUILDSPEC_PATH})

count=1

# If there are multiple Procfiles loop through them and create multiple OCI images for each instance
for PROC in $(niet ".application.process" ${BUILDSPEC_PATH})
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
    --tag ${DOCKERREG}/${APP_NAME}/${PROC}:${GIT_BRANCH} \
    --builder ${INPUT_BUILDER} \
    ${BUILDPACKS} \
    --env BP_LOG_LEVEL=${LOG_LEVEL} \
    ${PYTHON_VERSION} \
    --publish

  status=$?
  [ $status -ne 0 ] && exit 1

  let count++

done

#Report Image build to Slack
SLACK_DATA=$(jq -n \
--arg dt "\`Image=${APP_NAME}/${PROC}:${GIT_COMMIT}, ${GIT_TAG}, branch=${GIT_BRANCH}\`" \
'{"text":$dt}')
curl -X POST -H 'Content-type: application/json' --data "${SLACK_DATA}" https://hooks.slack.com/services/$SLACK_WORKSPACE_ID/$SLACK_CHANNEL_ID/$SLACK_TOKEN
