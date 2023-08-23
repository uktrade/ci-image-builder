FROM public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:4.0

ENV PACK_VERSION=v0.28.0

RUN yum install -y jq

RUN curl -LO https://github.com/buildpacks/pack/releases/download/${PACK_VERSION}/pack-${PACK_VERSION}-linux.tgz && \
    tar xfz pack-${PACK_VERSION}-linux.tgz && \
    mv pack /usr/bin/

RUN pip install -U niet

RUN mkdir /work

RUN mkdir /docker_images

COPY build.sh /work/build.sh
RUN chmod +x /work/build.sh

COPY builder-post.sh /work/builder-post.sh
