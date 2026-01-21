# Folio User Import

Turns https://github.com/FOLIO-FSE/folio_data_import into a docker image to be run by Five Colleges.

```
git submodule init
cd folio_user_import
cp .env.example .env
# edit .env if you'd like to deeply test the image
./build.sh
```

You can run `./build.sh --relock` to get fresh dependency versions.

This repository locks based on the project's pyproject.toml.
Development shouldn't be done here, merge the changes upstream first.
