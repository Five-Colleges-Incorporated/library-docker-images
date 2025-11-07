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

if [[ "${1:-}" == "--relock" ]] || [[ "${2:-}" == "--relock" ]]; then
	git checkout requirements.lock
	uv pip compile requirements.txt -o requirements.lock > /dev/null
	git --no-pager diff requirements.lock
fi

build="$RANDOM"
echo "building $build"
docker build \
	--build-arg PYTHON_VERSION="$(cat .python-version)" \
	-t edu.fivecolleges.libraries.setae-api:latest \
	-t edu.fivecolleges.libraries.setae-api:"$version" \
	-t edu.fivecolleges.libraries.setae-api:"$build" \
	.

setae="$(docker run -d -p "$build":80 --env-file .env edu.fivecolleges.libraries.setae-api:"$build")"
trap 'docker container rm --force "$setae" >/dev/null' exit

echo "waiting for startup"
sleep 10

echo "readyz"
curl -w "%{http_code}" "localhost:$build/readyz"
echo ""

echo "livez"
curl -w "%{http_code}" "localhost:$build/livez"
echo ""

echo "407 proxy required"
curl -w "%{http_code}" "localhost:$build"
echo ""

echo "401 unauthorized"
curl -H "do-connecting-ip: 1.1.1.1" -w "%{http_code}" "localhost:$build"
echo ""

echo "hello world"
curl -H "do-connecting-ip: 148.85.255.199" "localhost:$build"
echo ""

echo "fetching json"
curl -H "do-connecting-ip: 148.85.255.199" "localhost:$build/items/310212313168477?format=json"
echo ""

if [[ "${1:-}" == "--check-xml" ]] || [[ "${2:-}" == "--check-xml" ]]; then
	echo "fetching xml"
	curl -H "do-connecting-ip: 148.85.255.199" "localhost:$build/items/5159903*-UMA"
	echo ""
fi
