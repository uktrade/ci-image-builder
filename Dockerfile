FROM public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0

ARG PACK_VERSION
ARG COPILOT_VERSION

RUN yum install -y jq

# Install Pack
RUN curl -LO https://github.com/buildpacks/pack/releases/download/${PACK_VERSION}/pack-${PACK_VERSION}-linux.tgz && \
    tar xfz pack-${PACK_VERSION}-linux.tgz && \
    mv pack /usr/bin/

# Install Copilot
RUN wget -q https://ecs-cli-v2-release.s3.amazonaws.com/copilot-linux-v${COPILOT_VERSION} -O copilot && \
    chmod +x ./copilot && \
    mv copilot /usr/bin/

# CAN REMOVE SECTION ONCE OVER TO PYTHON BASED BUILDER
RUN pip install -U niet

RUN mkdir /work
RUN mkdir /docker_images

COPY build.sh /work/build.sh
RUN chmod +x /work/build.sh

COPY builder-post.sh /work/builder-post.sh
# CAN REMOVE SECTION ONCE OVER TO PYTHON BASED BUILDER

COPY ./requirements.txt /work/
RUN cd /work && pip install -r requirements.txt

COPY ./image_builder /work/image_builder
COPY cli /work/
