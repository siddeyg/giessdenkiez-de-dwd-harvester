# building a buffer shape for filtering the weather data
import geopandas
import os
from shapely.ops import unary_union
from dotenv import load_dotenv

load_dotenv()

input_path = os.environ.get("SURROUNDING_SHAPE_FILE")
if input_path is None:
    raise ValueError("Environment variable SURROUNDING_SHAPE_FILE is not set.")

if not os.path.exists(input_path):
    raise FileNotFoundError(
        f"Input shapefile not found at path: {input_path}. "
        f"Please check the SURROUNDING_SHAPE_FILE environment variable."
    )

berlin = geopandas.read_file(input_path)

# Get the directory of the input file
input_dir = os.path.dirname(input_path)
# Define the output filename
output_filename = "buffer.shp"
# Construct the full output path
output_path = os.path.join(input_dir, output_filename)

berlin = berlin.to_crs("epsg:3857")

# Use convex hull of all geometries — works correctly for both city boundary
# polygons (Berlin) and point datasets (Bonn trees). Much faster than
# buffering a unary_union of thousands of individual points.
city_hull = unary_union(berlin["geometry"]).convex_hull
berlin_boundary = geopandas.GeoDataFrame(
    geopandas.GeoSeries([city_hull])
)
berlin_boundary = berlin_boundary.rename(columns={0: "geometry"}).set_geometry(
    "geometry"
)

berlin_buffer = berlin_boundary.buffer(2000)
berlin_buffer = berlin_buffer.simplify(1000)

berlin_buffer = geopandas.GeoDataFrame(berlin_buffer)
berlin_buffer = berlin_buffer.rename(columns={0: "geometry"}).set_geometry("geometry")
berlin_buffer.crs = "epsg:3857"
berlin_buffer.to_file(output_path)
