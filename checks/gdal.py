"""Check GDAL's Python bindings and scripts in the gdal image."""

import subprocess
from osgeo import gdal, osr

subprocess.run(["gdalinfo", "--version"], check=True)

gdal.UseExceptions()

# A 3x3 raster with a nodata hole in the middle
dataset = gdal.GetDriverByName("GTiff").Create("/tmp/hole.tif", 3, 3, 1, gdal.GDT_Byte)
dataset.GetRasterBand(1).SetNoDataValue(0)
dataset.GetRasterBand(1).WriteRaster(0, 0, 3, 3, bytes([1, 1, 1, 1, 0, 1, 1, 1, 1]))
dataset = None

subprocess.run(["gdal_edit", "-a_srs", "EPSG:2193", "/tmp/hole.tif"], check=True)
subprocess.run(
    ["gdal_fillnodata", "-q", "/tmp/hole.tif", "/tmp/filled.tif"], check=True
)

filled = gdal.Open("/tmp/filled.tif")
assert filled.GetRasterBand(1).ReadRaster() == bytes([1] * 9), list(
    filled.GetRasterBand(1).ReadRaster()
)
assert osr.SpatialReference(filled.GetProjection()).GetAuthorityCode(None) == "2193", (
    filled.GetProjection()
)


def transform(source: str, target: str, *point: float) -> tuple[float, ...]:
    """Transform an x, y(, z) point."""
    crs = []
    for code in (source, target):
        crs.append(osr.SpatialReference())
        crs[-1].SetFromUserInput(code)
        crs[-1].SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return osr.CoordinateTransformation(*crs).TransformPoint(*point)


# NZGD49 and NZVD2016 use LINZ's grids
nzmg = transform("EPSG:2193", "EPSG:27200", 1748978, 5427288)
assert [round(value, 2) for value in nzmg[:2]] == [2658999.93, 5989000.13], nzmg
ellipsoidal = transform("EPSG:2193+7839", "EPSG:4959", 1748978, 5427288, 100)
assert round(ellipsoidal[2], 2) == 113.03, ellipsoidal

# A transformation whose grid is missing fails
try:
    transform("EPSG:4267", "EPSG:4269", -100, 40)
except RuntimeError:
    pass
else:
    raise AssertionError("NAD27 to NAD83 without its grid did not fail")
