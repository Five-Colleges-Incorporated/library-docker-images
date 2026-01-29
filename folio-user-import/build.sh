#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

pushd ./folio_data_import >/dev/null || exit
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

if [[ "${1:-}" == "--relock" ]] || [[ "${2:-}" == "--relock" ]]; then
	git checkout requirements.lock
	uv pip compile --no-cache ./folio_data_import/pyproject.toml > requirements.lock
	uv pip compile --no-cache ./requirements.txt >> requirements.lock
	git --no-pager diff requirements.lock
fi

build="$RANDOM"
echo "building $build"
docker build \
	--build-arg PYTHON_VERSION="$(cat .python-version)" \
	-t edu.fivecolleges.libraries.folio-user-import:latest \
	-t edu.fivecolleges.libraries.folio-user-import:"$version" \
	-t edu.fivecolleges.libraries.folio-user-import:"$build" \
	.

#fui="$(docker run -d --env-file .env edu.fivecolleges.libraries.folio-user-import:"$build")"
#trap 'docker container rm --force "$fui" >/dev/null' exit
