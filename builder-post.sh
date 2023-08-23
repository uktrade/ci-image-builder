echo "Running builder post build script"
echo -n "CI image builder version: " > build_version.txt
echo $CODEBUILD_BUILD_IMAGE |awk -F ":" '{print $2}' >> build_version.txt
echo -n "Paketo builder version: " >> build_version.txt
echo $BUILDER_VERSION >> build_version.txt
echo -n "Post buildpack version: " >> build_version.txt
echo $BUILDPACK_POST |awk -F "@" '{print $2}' >> build_version.txt
echo -n "co-pilot tools version: " >> build_version.txt
echo $COPILOT_TOOLS_VERSION >> build_version.txt