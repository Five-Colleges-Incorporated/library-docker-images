#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

pushd ./setae-api >/dev/null || exit
old_version="$(git rev-parse --short=8 HEAD)"
git fetch
git pull
version="$(git rev-parse --short=8 HEAD)"
popd >/dev/null || exit
if [[ $old_version != "$version" ]]; then
	echo "have $version (was $old_version)"
else
	echo "have $version (no changes)"
fi

if [[ ${1:-} == "--relock" ]]; then
	uv pip compile requirements.txt -o requirements.lock
	git diff requirements.txt
fi

build="$RANDOM"
echo "building $build"
docker build \
	-t edu.fivecolleges.libraries.setae-api:latest \
	-t edu.fivecolleges.libraries.setae-api:"$version" \
	-t edu.fivecolleges.libraries.setae-api:"$build" \
	.

setae="$(docker run -d -p "$build":80 edu.fivecolleges.libraries.setae-api:"$build")"
trap 'docker container rm --force "$setae" >/dev/null' exit

echo "waiting for startup"
sleep 10
curl localhost:"$build"
