#!/usr/bin/env bash

set -x

LOG_LEVEL="DEBUG"

# Set env VAR to PUBLIC for public images
ECR_VISIBILITY="${ECR_VISIBILITY:=PRIVATE}"

ECR_PATH="public.ecr.aws/uktrade"
BUILDER_VERSION=${PAKETO_BUILDER_VERSION}
LIFECYCLE_VERSION=${LIFECYCLE_VERSION}
RUN_VERSION="full-cnb"

BUILDPACKS_PATH="$ECR_PATH/paketobuildpacks"
INPUT_BUILDER="$BUILDPACKS_PATH/builder:$BUILDER_VERSION"
BUILDER_RUN="$BUILDPACKS_PATH/run:$RUN_VERSION"
LIFECYCLE="$ECR_PATH/buildpacksio/lifecycle:$LIFECYCLE_VERSION"
BUILDPACK_JSON="buildpack.json"
BUILDPACK_POST="fagiani/run@0.1.1"
BUILDPACKS=""

GIT_TAG=$(git describe --tags --abbrev=0)
GIT_COMMIT=$(echo "$CODEBUILD_RESOLVED_SOURCE_VERSION" | cut -c1-7)

if [ -z "$CODEBUILD_WEBHOOK_TRIGGER" ]; then
  GIT_BRANCH=$(git branch --show-current)
else
  GIT_BRANCH=$(echo "$CODEBUILD_WEBHOOK_TRIGGER" | awk -F "/" '{print $2}')
fi

if [ -f "codebuild/process.yml" ];then
  BUILDSPEC_PATH="codebuild/process.yml"
else
  BUILDSPEC_PATH="copilot/process.yml"
fi

# Create a list of Buildpacks
if [ -f $BUILDPACK_JSON ]; then
  if [[ $(jq '.buildpacks' $BUILDPACK_JSON) != "null" ]]; then
    count=$(jq '.buildpacks | length' $BUILDPACK_JSON)

    for i in $(seq 0 $((count - 1))); do
      KEY=$(jq -r ".buildpacks[$i] | keys[]" $BUILDPACK_JSON)
      VALUE=$(jq -r ".buildpacks[$i] | values[]" $BUILDPACK_JSON)

      BUILDPACKS+=" --buildpack $KEY/$VALUE"
    done
  fi
fi

if [ -z "$BUILDPACKS" ]; then
  echo "Found no build packs in file \"$BUILDPACK_JSON\", you must add at least one."
  exit 1
fi

if [ -f "runtime.txt" ]; then
  PYTHON_VERSION="--env BP_CPYTHON_VERSION=$(awk -F - '{print $2}' < runtime.txt)"
else
  PYTHON_VERSION=""
fi

# Start Docker deamon
nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2 &
timeout 15 sh -c "until docker info; do echo .; sleep 1; done"

docker pull $BUILDER_RUN
docker tag $BUILDER_RUN paketobuildpacks/run:$RUN_VERSION

docker pull $LIFECYCLE
docker tag $LIFECYCLE buildpacksio/lifecycle:$LIFECYCLE_VERSION

docker images

cp Procfile Procfile_tmp

# Create buildpack-run.sh file which is used by the buildpack post to run commands in the container after build completes
cat /work/builder-post.sh >> buildpack-run.sh
chmod +x buildpack-run.sh

# Check if the application repo already contains user-post.sh with post app commands, if so append to buildpack-run.sh.
if [ -f "user-post.sh" ]; then
  cat user-post.sh >> buildpack-run.sh
fi

APP_NAME=$(niet ".application.name" $BUILDSPEC_PATH)
count=1

# If there are multiple processes, loop through them and create multiple OCI images for each instance
for PROC in $(niet ".application.process" $BUILDSPEC_PATH)
do
  sed -n "$count p" Procfile_tmp > Procfile

  if [ $PROC == "False" ]; then
    IMAGE_NAME="$APP_NAME"
  else
    IMAGE_NAME="$APP_NAME/$PROC"
  fi

  # Public/Private repos have different commands and targets.
  if [ $ECR_VISIBILITY == "PRIVATE" ]; then
    DOCKERREG=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.eu-west-2.amazonaws.com
    aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin "$DOCKERREG"

    aws ecr describe-repositories --repository-names "$IMAGE_NAME" --region eu-west-2 >/dev/null
    status=$?
    [ $status -ne 0 ] && aws ecr create-repository --repository-name "$IMAGE_NAME" --region eu-west-2 --image-scanning-configuration scanOnPush=true --image-tag-mutability IMMUTABLE

  else
    aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
    REG_ALIAS=$(aws ecr-public describe-registries --region us-east-1 |jq '.registries[]|.aliases[0]|.name' | xargs)
    DOCKERREG="public.ecr.aws/$REG_ALIAS"

    aws ecr-public describe-repositories --repository-names "$IMAGE_NAME" --region eu-west-2 >/dev/null
    status=$?
    [ $status -ne 0 ] && aws ecr-public create-repository --repository-name "$IMAGE_NAME" --region us-east-1

  fi
  
  # Build image and push to ECR
  IMAGE="$DOCKERREG"/"$IMAGE_NAME"
  pack build "$IMAGE" \
    --tag "$IMAGE":"$GIT_TAG" \
    --tag "$IMAGE":"$GIT_COMMIT" \
    --tag "$IMAGE":"$GIT_BRANCH" \
    --builder "$INPUT_BUILDER" \
    $BUILDPACKS \
    --buildpack "$BUILDPACK_POST" \
    --env BP_LOG_LEVEL="$LOG_LEVEL" \
    --env CODEBUILD_BUILD_IMAGE="$CODEBUILD_BUILD_IMAGE" \
    --env BUILDER_VERSION="$BUILDER_VERSION" \
    --env BUILDPACK_POST="$BUILDPACK_POST" \
    --env COPILOT_TOOLS_VERSION="$COPILOT_TOOLS_VERSION" \
    --env GIT_TAG="$GIT_TAG" \
    --env GIT_COMMIT="$GIT_COMMIT" \
    --env GIT_BRANCH="$GIT_BRANCH" \
    $PYTHON_VERSION \
    --publish

  status=$?
  [ $status -ne 0 ] && exit 1

  (( count++ ))

  # Report image build to Slack
  BUILD_RUN_URL="$(echo "$CODEBUILD_BUILD_ARN" | awk -F: -v APP_NAME="$APP_NAME" '{ printf "https://%s.console.aws.amazon.com/codesuite/codebuild/%s/projects/%s/%s%s%s", $4, $5, APP_NAME, $6, "%3A", $7; }')"
  NEW_LINE=$'\n'
  SLACK_DATA="$(jq -n --arg dt "*Image:* \`$IMAGE_NAME:$GIT_COMMIT\`$NEW_LINE*Tag:* ${GIT_TAG:-none}$NEW_LINE*Branch:* $GIT_BRANCH$NEW_LINE*Builder Version:* $BUILDER_VERSION$NEW_LINE*Lifecycle Version:* $LIFECYCLE_VERSION$NEW_LINE$NEW_LINE<$BUILD_RUN_URL|:rocket: View Build Run>" '{"text":$dt}')"
  SLACK_WEBHOOK="https://hooks.slack.com/services/$SLACK_WORKSPACE_ID/$SLACK_CHANNEL_ID/$SLACK_TOKEN"
  curl -X POST -H 'Content-type: application/json' --data "$SLACK_DATA" "$SLACK_WEBHOOK"
done
