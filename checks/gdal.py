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
