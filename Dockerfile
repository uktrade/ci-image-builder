#FROM paketobuildpacks/builder:0.2.263-full

FROM public.ecr.aws/codebuild/amazonlinux2-x86_64-standard:4.0

ENV PACK_VERSION=v0.28.0
#ENV BUILDER_VERSION=0.2.263

RUN yum install -y jq

RUN curl -LO https://github.com/buildpacks/pack/releases/download/${PACK_VERSION}/pack-${PACK_VERSION}-linux.tgz && \
    tar xfz pack-${PACK_VERSION}-linux.tgz && \
    mv pack /usr/bin/

RUN mkdir /work

COPY build.sh /work/build.sh
RUN chmod +x /work/build.sh

#COPY entrypoint.sh /work/entrypoint.sh

#RUN chmod +x /work/entrypoint.sh

#ENTRYPOINT [ "/work/entrypoint.sh" ]
