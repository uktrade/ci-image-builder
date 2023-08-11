# ci-image-builder

Docker image for building oci images using paketo buildpacks and uploading them to aws ecr.

## Usage

This is designed to be used by AWS Codebuild projects

1. Environment image, update this to the location of your uploaded Docker image of the ci-image-builder.

2. Buildspec, this will normally point to the location of your source codes buildspec.yml file.  


AWS Reference:  https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html

### buildspec.yml

```yml
version: 0.2

env:
  parameter-store:
    SLACK_WORKSPACE_ID: "/codebuild/slack_workspace_id"
    SLACK_CHANNEL_ID: "/codebuild/slack_channel_id"
    SLACK_TOKEN: "/codebuild/slack_api_token"
  variables:
    ECR_VISIBILITY: {PRIVATE/PUBLIC}

phases:
  # install:

  pre_build:
    commands:
      - codebuild-breakpoint

  build:
    commands:
      - /work/build.sh
```

#### ENV VARS

`SLACK_* - Credentials/ IDS needed to interact with SLACK`

`ECR_VISIBILITY - If set to PUBLIC then OCI image will be placed in a public repo in the AWS account, if not set this will default to PRIVATE`

#### PHASES

It is possible to run multiple phases for you build, in most cases the example above will be sufficient. 

If you need to install additional packages into the image you can add that to the Install section.

Under pre-build we suggest including a breakpoint, this can be useful for troubleshooting the container.  Which can be enabled when you `start build with overrides`, in the aws console.

Finally, under build, the path to the `ci-image-builders build.sh` script is defined.  

## Instructions to Deploy a public image

In order to deploy a public image rather than the default private image do the following.

In your `buildspec.yml` file add set the variable `ECR_VISIBILITY: PUBLIC`

In your codes repo `process.yml` specify your public image name.

```yml
application:
  name: image_name
  process:
    - False
```

Setting the process to `False` will tell the builder to use the image name only. This will produce the following:

`public.ecr.aws/{aws alias}/image_name:latest`

If you want to include a sub image name you can specify this in the process name.

```yml
application:
  name: image_name
  process:
    - app_name
```

This will produce:

`public.ecr.aws/{aws alias}/image_name/app_name:latest`

### Using copilot-tools to build images

Finally to have Codebuild watch you application repo and deploy an OCI image on changes run the following commands:

```
aws sso login --profile profile-name && export AWS_PROFILE=profile-name

copilot-helper codebuild codedeploy --project-profile <profile_name> --name <application_name> --desc <desciption> --git <git-url>  --branch <branch> --buildspec <location-buildspec.yml>
```