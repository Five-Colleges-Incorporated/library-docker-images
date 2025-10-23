# Setae API

Turns https://github.com/cul-it/setae-api into a docker image to be hosted by Five Colleges.

```
git submodule init
cp setae-api/.env.example .env
# edit .env if you'd like to deeply test the image
./build.sh
```

You can run `./build.sh --relock` to get fresh dependency versions.

This repository mirrors the dependencies in the setae repository itself.
But it doesn't use poetry or the upstream lock file because we want the latest versions of python/libraries for security reasons.
Development shouldn't be done here, merge the changes upstream first.
