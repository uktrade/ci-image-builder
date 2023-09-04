# CI Image Builder

Docker image for building OCI images using Paketo buildpacks and uploading them to AWS ECR.

## Build

An environment variable for [`Pack CLI version`](https://github.com/buildpacks/pack/releases) has to be set in the environment settings within the AWS CodeBuild project console, for example:

    PACK_VERSION = v0.28.0

## Usage

The guidance below pertains to your application, which means within your application repository. This is designed to be used by AWS CodeBuild projects.

### Prerequisites

- Ensure the environment image is pointing to the location of the `ci-image-builder` ECR image.
  - _Note: The tag `latest` does not need to be supplied and is optional._
- Ensure the `buildspec` configuration is correctly configured to point to the source code `buildspec.yml` file.
  - _Note: This may point to a `buildspec.yml` file in a `codebuild` directory._  

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
    PAKETO_BUILDER_VERSION: 0.2.326-full
    LIFECYCLE_VERSION: 0.16.0

phases:
  pre_build:
    commands:
      - codebuild-breakpoint

  build:
    commands:
      - /work/build.sh
```

#### Environment variables

`SLACK_*` - Credentials/IDs needed to interact with Slack.
`ECR_VISIBILITY` - If set to `PUBLIC`, then the OCI image will be placed in a public repo in the AWS account, and if not set this will default to PRIVATE.
`PAKETO_BUILDER_VERSION` - Builder version supported within the [AWS ECR Gallery](https://eu-west-2.console.aws.amazon.com/ecr/repositories/public/763451185160/paketobuildpacks/builder?region=eu-west-2).
`LIFECYCLE_VERSION` - Lifecycle version supported by the above builder version. More details can be found on [GitHub](https://github.com/paketo-buildpacks/full-builder/releases).

#### Phases

It is possible to run multiple phases for your build, but in most cases, the example above will be sufficient.

If you need to install additional packages into the image, you can add that to the `install` section. Refer to the AWS reference for more details.

Under `pre-build`, we suggest including a breakpoint, this can be useful for troubleshooting the container. This can be enabled when you `Start build with overrides`, in the AWS console.

Finally, under `build`, the path to the `ci-image-builder`'s `build.sh` script is defined.  

## Instructions to deploy a public image

In order to deploy a public image rather than the default private image, do the following.

In your `buildspec.yml` file, add and set the variable `ECR_VISIBILITY: PUBLIC`.

In your repository, in the `process.yml` file, specify your public image name.

```yml
application:
  name: image_name
  process:
    - False
```

Setting the process to `False` will tell the builder to use the image name only. This will produce `public.ecr.aws/{aws alias}/image_name:latest`.

If you want to include a subdirectory for your image, you can specify this in the `process` section:

```yml
application:
  name: image_name
  process:
    - service_name
```

This will `public.ecr.aws/{aws alias}/image_name/service_name:latest`.

### Using `dbt-copilot-tools` to build images

Finally, to have CodeBuild watch your application repo and deploy an OCI image on GitHub changes, run the following commands:

```console
aws sso login --profile profile-name && export AWS_PROFILE=profile-name

copilot-helper codebuild codedeploy --project-profile <profile_name> --name <application_name> --desc <desciption> --git <git-url>  --branch <branch> --buildspec <location-buildspec.yml>
```
