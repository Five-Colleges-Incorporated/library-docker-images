#!/usr/bin/env bash
set -euo pipefail

pyversion="$(cat .python-version)"

old_version="$(
	(grep 'folio-data-import==' requirements.lock || echo 'folio-data-import==NA') |
		awk -F'==' '{ print $2 }'
)"
echo "$old_version"

if [[ $old_version == "NA" || ${1:-} == "--relock" ]]; then
	git checkout requirements.lock
	uv pip compile --python-version "$pyversion" --no-cache ./requirements.txt >requirements.lock
	git --no-pager diff requirements.lock
fi
version="$(grep 'folio-data-import==' requirements.lock | awk -F'==' '{ print $2 }')"

if [[ $old_version != "$version" ]]; then
	echo "have $version (was $old_version)"
else
	echo "have $version (no changes)"
fi

build="$RANDOM"
echo "building $build"
#--build-arg PYTHON_VERSION="$pyversion" \
docker build \
	-t edu.fivecolleges.libraries.folio-user-import:latest \
	-t edu.fivecolleges.libraries.folio-user-import:"$version" \
	-t edu.fivecolleges.libraries.folio-user-import:"$build" \
	.

#fui="$(docker run -d --env-file .env edu.fivecolleges.libraries.folio-user-import:"$build")"
#trap 'docker container rm --force "$fui" >/dev/null' exit
