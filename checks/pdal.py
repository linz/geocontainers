"""Check PDAL writes, translates and reads a LAZ file in the pdal image."""

import json
import subprocess


def pdal(*args, stdin=None):
    return subprocess.run(
        ["pdal", *args], input=stdin, stdout=subprocess.PIPE, text=True, check=True
    ).stdout


subprocess.run(["pdal", "--version"], check=True)

# 100 generated points in a LAZ file
pdal(
    "pipeline",
    "--stdin",
    stdin=json.dumps(
        [
            {
                "type": "readers.faux",
                "count": 100,
                "mode": "ramp",
                "bounds": "([0, 100], [0, 100], [0, 10])",
            },
            "/tmp/points.laz",
        ]
    ),
)

pdal(
    "translate",
    "/tmp/points.laz",
    "/tmp/translated.laz",
    "--readers.las.spatialreference=EPSG:2193+7839",
    "--writers.las.filesource_id=0",
    "--writers.las.forward=all",
)

metadata = json.loads(pdal("info", "--metadata", "/tmp/translated.laz"))["metadata"]
result = {
    "count": metadata["count"],
    "compressed": metadata["compressed"],
    "srs": [
        component["id"]["code"] for component in metadata["srs"]["json"]["components"]
    ],
}
assert result == {"count": 100, "compressed": True, "srs": [2193, 7839]}, result

# NZVD2016 to ellipsoidal heights use LINZ's geoid grid
pdal(
    "pipeline",
    "--stdin",
    stdin=json.dumps(
        [
            {
                "type": "readers.faux",
                "count": 1,
                "mode": "constant",
                "bounds": "([1748978, 1748978], [5427288, 5427288], [100, 100])",
                "override_srs": "EPSG:2193+7839",
            },
            {
                "type": "filters.reprojection",
                "out_srs": "EPSG:4959",
                "error_on_failure": True,
            },
            {
                "type": "writers.text",
                "filename": "/tmp/ellipsoidal.txt",
                "order": "Z:3",
                "keep_unspecified": False,
            },
        ]
    ),
)
with open("/tmp/ellipsoidal.txt") as heights:
    assert heights.read().split()[1:] == ["113.029"]
