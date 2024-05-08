#!/usr/bin/env bash

echo "Running fake pack command"
echo "===> BUILDING"
echo "."
echo "."
echo "."
echo "."
echo "."
echo "."
>&2 echo "Not in notification"
>&2 awk 'BEGIN {s = sprintf("%*s", 3000, ""); gsub(".", "x", s); print s; }'
>&2 echo "Failed to build"
exit 127
