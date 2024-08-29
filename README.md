# CI Image Builder

Docker image and Python application for building [OCI](https://opencontainers.org/) images using [Paketo](https://paketo.io/) buildpacks and uploading
them to AWS ECR.

> [!NOTE]
> If you are using the old image builder (your `buildspec.yml` will have `/work/build.sh` in it),
> see the documentation for that [here](./OLD_README.md).

## Configuration

To configure your application repository for use with this image, run the following command:

```shell
platform-helper codebase prepare
```

Alternatively, you can create or use the following folder structure:

```console
.
└── .copilot
    ├── config.yml
    ├── image_build_run.sh
    └── phases
        ├── build.sh
        ├── install.sh
        ├── post_build.sh
        └── pre_build.sh
```

### `.copilot/config.yml`

This file configures the image builder telling it which [Paketo](https://paketo.io/) builder and
buildpacks to use when building your application image.

```yaml
repository: demodjango/application
builder:
  name: paketobuildpacks/builder-jammy-base
  version: 0.4.240
packages:
  - libpq-dev
```

| field             | type        | description                                                                                                                                                                                                          |
|-------------------|-------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `repository`      | string      | The ECR repository the image is pushed to.<br>To enable caching another repository at `{repository}-cache` must exist.                                                                                               |
| `builder.name`    | string      | The builder image used to create your image. See [paketo builders](https://github.com/paketo-buildpacks?q=builder&type=all) for a full list.                                                                         |
| `builder.version` | string      | The version of the builder to use, see the releases page of your builder image and the [list of builders](./image_builder/configuration/builder_configuration.yml) for details on supported and deprecated builders. |
| `packages`        | string list | A list of APT packages to install prior to building your application. For example, `libpg-dev` required to compile the Python package `psycopg2`.                                                                    |

### `.copilot/image_build_run.sh` (Optional)

This file is executed inside the built container after all other build actions have completed. Use this to run commands like `python manage.py collectstatic`.

An example of this could be:

```bash
#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

echo "Running post build script"
cd src
echo "Running collectstatic"
python manage.py collectstatic --settings=config.settings.build --noinput
```

### `.copilot/phases/*.sh` (Optional)

These files are executed outside the container by CodeBuild in each phase. They are entirely optional.

CodeBuild phases:

- `install`
- `pre_build`
- `build`
- `post_build`

An example use of these scripts could be to scan an image for image vulnerabilities in the `post_build` phase, as follows:

`.copilot/phases/post_build.sh`
```bash
#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

GIT_COMMIT=$(git rev-parse --short HEAD)
aws ecr start-image-scan --repository-name demodjano/application --image-id "imageTag=commit-$GIT_COMMIT" --region eu-west-2

aws ecr describe-image-scan-findings --repository-name demodjano/application --image-id "imageTag=commit-$GIT_COMMIT" --region eu-west-2
```

### How the Python version is specified

The version of Python used to run your code in the built image will come from the following in this order of preference:

- `pyproject.toml`
- `runtime.txt`
- The latest release

## Building an Image

Images are built by CodeBuild when a push to a branch or tag of your repository matches a given pattern.

> [!NOTE]
> Setup for this is not developed yet and will be part of the `dbt-copilot-tools` package.

<!-- TODO: build out configuration command in dbt-copilot-tools to configure a codebase to use the new builder -->

## Using `ci-image-builder` to build an image locally for testing

Assumptions:

- This repository and your codebase repository have the same parent directory
- You are using virtual Python environments
- Commands will be run from the application codebase directory
- You've [installed Pack](https://buildpacks.io/docs/for-platform-operators/how-to/integrate-ci/pack/#install)

Make sure your application's Python environment has the dependencies for `ci-image-builder`:

```shell
pip install -r ../ci-image-builder/requirements.txt
```

Temporarily edit your codebase's `.copilot/config.yml` so that `repository` has a public URL. e.g. change `this/application` to `public.ecr.aws/this/application`. If you don't do this, it just exits with no explanation after outputting "Docker is running, continuing with build...".

Build the image:

```shell
../ci-image-builder/cli build
```

## Publishing `ci-image-builder`

When you push a commit to GitHub, a CodeBuild job will attempt to build the image and publish it with the following tags intended to allow for testing etc.

- `branch-<branch_name>`
- `commit-<commit_hash>`
- `pack-<pack_version>`

When you tag a commit to release it, the following tags should be added

- `tag-<commit_tag>`
- `tag-latest` (if the image has a semantic versioning tag like `1.2.3`)
