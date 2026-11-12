# pdal-docker

[GDAL](https://gdal.org/) and [PDAL](https://pdal.io/) base images with Python, used for LINZ raster and point cloud processing containers.
Their packages come from [conda-forge](https://conda-forge.org/), on `ubuntu` LTS with Ubuntu's `main` fixes and time zone data.

| Image                         | Built from target | Contains                                                       |
| ----------------------------- | ----------------- | -------------------------------------------------------------- |
| `ghcr.io/linz/li-gdal-docker` | `gdal`            | GDAL programs, GDAL's Python bindings and scripts, Python 3.15 |
| `ghcr.io/linz/li-pdal-docker` | `pdal`            | `pdal`, GDAL programs, Python 3.15                             |

Both are built with [pixi](https://pixi.prefix.dev/) from one environment solve (`pixi.toml`, `pixi.lock`), so they share the same Python, PROJ and GDAL libraries.
This also means PDAL's GDAL requirement limits the GDAL version in both images.

Both have LINZ's PROJ grids (`nz_linz_*`, copied from conda-forge's `proj-data`), and `PROJ_ONLY_BEST_DEFAULT=YES` makes a transformation fail rather than fall back to a less accurate one when its grid is missing.
PDAL's `filters.reprojection` drops the points it can't transform unless `error_on_failure` is set.

Earlier images, with PDAL built from source on Ubuntu's GDAL, are at `ghcr.io/linz/pdal-docker` and are no longer updated.

## Usage

Pin by digest, so a moved tag cannot change what is built. For example, with uv:

```dockerfile
FROM ghcr.io/linz/li-gdal-docker:<version>@sha256:<digest> AS builder
COPY --from=ghcr.io/astral-sh/uv:<version>@sha256:<digest> /uv /bin/
ENV UV_PROJECT_ENVIRONMENT=/venv UV_PYTHON=$CONDA_PREFIX/bin/python UV_PYTHON_PREFERENCE=only-system
RUN uv sync --frozen --no-dev --no-editable

FROM ghcr.io/linz/li-gdal-docker:<version>@sha256:<digest>
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
```

Your `requires-python` must match the images' Python. The entrypoint is `tini`.

The images have no compiler, so Python packages with compiled code need wheels, or a compiler added in your builder stage.

## Building

```bash
docker build --target gdal --tag li-gdal-docker .
docker build --target pdal --tag li-pdal-docker .
docker run --rm --interactive --network none li-gdal-docker python - < checks/gdal.py
docker run --rm --interactive --network none li-pdal-docker python - < checks/pdal.py
```

## Publishing

Every push to `master` builds both images, reads the version of the GDAL or PDAL package installed in each image, and publishes two tags for each: `<version>` and `<version>-<short sha>`. Both images are published even when a change only affects one of them.
The second (`<version>-<short sha>`) distinguishes rebuilds that do not change the GDAL or PDAL version, such as a Python, PROJ or Ubuntu update.

Pull requests build and verify without publishing.

The digests to pin are printed in the workflow run summary.

## Updating

- `.github/workflows/pixi-update.yml` opens a weekly pull request updating `pixi.lock`. `exclude-newer` in `pixi.toml` sets the minimum package age.
- Dependabot updates the `pixi` and `ubuntu` images in the `Dockerfile`, the GitHub Actions and the formatter.
- To change a version, such as GDAL's, PDAL's or Python's, edit `pixi.toml` and run `pixi lock`.

## License

This repository is MIT licensed. The images redistribute conda-forge packages under their own licences, reproduced at `$CONDA_PREFIX/licenses/<package>-<version>-<build>/`, and LINZ's PROJ grids under CC BY 4.0 (`$CONDA_PREFIX/share/proj/nz_linz_README.txt`).
