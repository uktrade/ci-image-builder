#!/usr/bin/env bash

echo "Running builder post build script"
echo "Builder version info ------------------------------------------" > build_version.txt
echo -n "CI image builder version: " >> build_version.txt
echo $CODEBUILD_BUILD_IMAGE |awk -F ":" '{print $2}' >> build_version.txt
echo -n "Paketo builder version: " >> build_version.txt
echo $BUILDER_VERSION >> build_version.txt
echo -n "Post buildpack version: " >> build_version.txt
echo $BUILDPACK_POST |awk -F "@" '{print $2}' >> build_version.txt
echo -n "Co-pilot tools version: " >> build_version.txt
echo $COPILOT_TOOLS_VERSION >> build_version.txt
echo "Application version info --------------------------------------" >> build_version.txt
echo -n "GIT tag: " >> build_version.txt
echo $GIT_TAG >> build_version.txt
echo -n "GIT commit: " >> build_version.txt
echo $BPE_GIT_COMMIT >> build_version.txt
echo -n "GIT branch: " >> build_version.txt
echo $BPE_GIT_BRANCH >> build_version.txt
