# ci-image-builder

Docker image for building OCI images using Paketo buildpacks and uploading them to AWS ECR.

## Usage

This is designed to be used by AWS CodeBuild projects.

1. Environment image - update this to the location of your uploaded Docker image of the `ci-image-builder`.
2. Buildspec - this will normally point to the location of your source codes `buildspec.yml` file.
3. Include 3 environment variables in the CodeBuild projects environment section, which indicate the versions of binaries and buildpacks to use.

For example...

```
PACK_VERSION = v0.28.0
PAKETO_BUILDER_VERSION = 0.2.395-full
LIFECYCLE_VERSION = 0.16.0
```

AWS Reference: https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html

### `buildspec.yml`

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
  pre_build:
    commands:
      - codebuild-breakpoint

  build:
    commands:
      - /work/build.sh
```

#### Environment Variables

`SLACK_*` - Credentials/IDs needed to interact with Slack.

`ECR_VISIBILITY` - If set to `PUBLIC`, then the OCI image will be placed in a public repo in the AWS account, and if not set this will default to PRIVATE.

#### Phases

It is possible to run multiple phases for your build, but in most cases, the example above will be sufficient.

If you need to install additional packages into the image, you can add that to the `install` section. Refer to the AWS reference for more details.

Under `pre-build`, we suggest including a breakpoint, this can be useful for troubleshooting the container. This can be enabled when you `Start build with overrides`, in the AWS console.

Finally, under `build`, the path to the `ci-image-builder`'s `build.sh` script is defined.  

## Instructions to deploy a public image

In order to deploy a public image rather than the default private image do the following.

In your `buildspec.yml` file, add and set the variable `ECR_VISIBILITY: PUBLIC`

In your repository, in the `process.yml` file, specify your public image name.

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

### Using `copilot-tools` to build images

Finally, to have CodeBuild watch your application repo and deploy an OCI image on GitHub changes, run the following commands:

```
aws sso login --profile profile-name && export AWS_PROFILE=profile-name

copilot-helper codebuild codedeploy --project-profile <profile_name> --name <application_name> --desc <desciption> --git <git-url>  --branch <branch> --buildspec <location-buildspec.yml>
```
