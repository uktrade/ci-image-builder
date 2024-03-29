# CI Image Builder

> [!NOTE]
> If you are using the new image builder (your `buildspec.yml` will have `/work/cli build` in it),
> see the documentation for that [here](./README.md).

Docker image for building OCI images using Paketo buildpacks and uploading them to AWS ECR.

## Build

An environment variable for the [`Pack CLI version`](https://github.com/buildpacks/pack/releases) has to be set in the [`buildspec.yml`](buildspec.yml) file.

The CodeBuild project for the `ci-image-builder` is managed via Terraform in the `terraform-tools` GitLab repository.

## Usage

This guidance pertains to your application, which means within your application repository. This is designed to be used by AWS CodeBuild projects.

### Prerequisites

- The CodeBuild environment image is pointing to the location of the `ci-image-builder` ECR image.
  - The tag `latest` does not need to be supplied and is optional.
- The `buildspec` configuration is correctly configured to point to the source code `buildspec.yml` file.
  - This may point to a `buildspec.yml` file in a `codebuild` directory.

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

- `SLACK_*` - Credentials/IDs needed to interact with Slack.
- `ECR_VISIBILITY` - If set to `PUBLIC`, then the OCI image will be placed in a public repo in the AWS account, and if not set this will default to `PRIVATE`.
- `PAKETO_BUILDER_VERSION` - Builder version supported within the [AWS ECR Gallery](https://gallery.ecr.aws/uktrade/paketobuildpacks/builder).
- `LIFECYCLE_VERSION` - Lifecycle version supported by the specified Paketo builder version. More details can be found on [Paketo’s GitHub Releases](https://github.com/paketo-buildpacks/full-builder/releases) page.

#### Phases

It is possible to run multiple phases for your build, but in most cases, the example above will be sufficient.

If you need to install additional packages into the image, you can add that to the `install` section. Refer to the AWS reference for more details.

Under `pre-build`, we suggest including a breakpoint, this can be useful for troubleshooting the container. This can be enabled when you `Start build with overrides`, in the AWS console.

Finally, under `build`, the path to the `ci-image-builder`'s `build.sh` script is defined.  

## Instructions to deploy a public image

Follow these steps to deploy a public image rather than the default private image:

1. In your `buildspec.yml` file, add and set the variable `ECR_VISIBILITY: PUBLIC`.
2. In your repository, in the `process.yml` file, specify your public image name.

    ```yml
    application:
      name: image_name
      process:
        - False
    ```

    Setting the process to `False` will tell the builder to use the image name only. This will produce `public.ecr.aws/{aws alias}/image_name:latest`.

3. If you want to include a subdirectory for your image, you can specify this in the `process` section:

    ```yml
    application:
      name: image_name
      process:
        - service_name
    ```

    This will produce `public.ecr.aws/{aws alias}/image_name/service_name:latest`.

### Using `dbt-copilot-tools` to build images

To have CodeBuild watch your application repository and deploy an OCI image on GitHub changes, refer to the guide on how to [Add the AWS CodeBuild configuration files to build the application image](https://github.com/uktrade/platform-documentation/blob/main/adding-a-new-application.md#add-the-aws-codebuild-configuration-files-to-build-the-application-image) in the DBT PaaS documentation.
