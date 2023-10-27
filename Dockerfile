FROM public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:5.0

ARG PACK_VERSION

RUN yum install -y jq

RUN curl -LO https://github.com/buildpacks/pack/releases/download/${PACK_VERSION}/pack-${PACK_VERSION}-linux.tgz && \
    tar xfz pack-${PACK_VERSION}-linux.tgz && \
    mv pack /usr/bin/

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
