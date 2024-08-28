FROM public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0

ARG PACK_VERSION="v0.32.0"
ARG REGCTL_VERSION="v0.5.3"
ARG COPILOT_VERSIONS="1.32.0 1.32.1 1.33.0 1.33.1 1.33.2 1.33.3 1.33.4 1.34.0"

#RUN yum install -y jq
#
## Install Pack
#RUN curl -LO https://github.com/buildpacks/pack/releases/download/${PACK_VERSION}/pack-${PACK_VERSION}-linux.tgz && \
#    tar xfz pack-${PACK_VERSION}-linux.tgz && \
#    mv pack /usr/bin/
#
## Install Copilot
#RUN mkdir /copilot && \
#    for version in ${COPILOT_VERSIONS}; do \
#        wget -q https://ecs-cli-v2-release.s3.amazonaws.com/copilot-linux-v${version} -O /copilot/copilot-${version}; \
#        chmod +x /copilot/copilot-${version}; \
#    done
#
## Install regclient
#RUN curl -L https://github.com/regclient/regclient/releases/download/${REGCTL_VERSION}/regctl-linux-amd64 > regctl && \
#    chmod +x ./regctl && \
#    mv regctl /usr/bin/
#
## CAN REMOVE SECTION ONCE OVER TO PYTHON BASED BUILDER
#RUN pip install -U niet
#
#RUN mkdir /work
#RUN mkdir /docker_images
#
#COPY build.sh /work/build.sh
#RUN chmod +x /work/build.sh
#
#COPY builder-post.sh /work/builder-post.sh
## CAN REMOVE SECTION ONCE OVER TO PYTHON BASED BUILDER

COPY ./requirements.txt /work/

# So we can easily see what versions of Python it has installed
RUN pyenv versions

# Install dependencies for all Python versions so that it
# doesn't matter which is used to send Slack notifications
COPY ./install-dependencies-for-all-pythons.sh /work/
RUN cd /work && ./install-dependencies-for-all-pythons.sh
RUN rm /work/install-dependencies-for-all-pythons.sh
RUN exit 1

COPY ./image_builder /work/image_builder
COPY cli /work/
