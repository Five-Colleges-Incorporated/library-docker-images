#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

pushd ./Patron-Transform >/dev/null || exit
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
	git checkout requirements.lock
	uv pip compile --no-cache ./requirements.txt >requirements.lock
	git --no-pager diff requirements.lock
fi

build="$RANDOM"
echo "building $build"
docker build \
	--build-arg PYTHON_VERSION="$(cat .python-version)" \
	-t edu.fivecolleges.libraries.Patron-Tranform:latest \
	-t edu.fivecolleges.libraries.Patron-Transform:"$version" \
	-t edu.fivecolleges.libraries.Patron-Transform:"$build" \
	.

#pt="$(docker run -d --env-file .env edu.fivecolleges.libraries.Patron-Transform:"$build")"
#trap 'docker container rm --force "$pt" >/dev/null' exit
