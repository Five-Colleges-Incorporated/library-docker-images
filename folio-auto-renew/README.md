# Folio Auto Renew

Turns https://github.com/Five-Colleges-Incorporated/folio-auto-renew into a docker image to be run by Five Colleges.

```
git submodule init
cd folio-auto-renew
cp .env.example .env
# edit .env if you'd like to deeply test the image
./build.sh
```

You can run `./build.sh --relock` to get fresh dependency versions.

This repository locks based on the project's pyproject.toml.
Development shouldn't be done here, merge the changes upstream first.
