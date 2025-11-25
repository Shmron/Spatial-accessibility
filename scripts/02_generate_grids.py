#!/usr/bin/env python3
"""
Generate H3 hexagonal grids for a district polygon
"""

import sys
import geopandas as gpd
import h3
from shapely.geometry import Polygon
import json

def generate_h3_grids(district_geojson, resolution=8):
    """
    Generate H3 hexagons covering a district polygon

    Args:
        district_geojson: Path to district GeoJSON file
        resolution: H3 resolution (default 8)

    Returns:
        GeoDataFrame with hexagonal grids
    """
    # Read district
    district = gpd.read_file(district_geojson)

    # Ensure WGS84 (required for H3)
    if district.crs != "EPSG:4326":
        district = district.to_crs("EPSG:4326")

    # Get the first geometry
    geom = district.geometry.iloc[0]

    # Convert to GeoJSON format for h3
    geojson_geom = json.loads(gpd.GeoSeries([geom]).to_json())['features'][0]['geometry']

    # Generate H3 hexagons
    print(f"Generating H3 hexagons at resolution {resolution}...")
    hexagons = list(h3.polyfill_geojson(geojson_geom, resolution))

    print(f"Generated {len(hexagons)} hexagons")

    # Create geometries from H3 IDs
    hex_geometries = []
    hex_ids = []

    for hex_id in hexagons:
        # Get boundary coordinates (lat, lon pairs)
        boundary = h3.h3_to_geo_boundary(hex_id, geo_json=True)
        # Create polygon (note: h3 returns lon, lat so we need to reverse)
        poly = Polygon(boundary)
        hex_geometries.append(poly)
        hex_ids.append(hex_id)

    # Create GeoDataFrame
    grids = gpd.GeoDataFrame({
        'hex_id': hex_ids,
        'geometry': hex_geometries
    }, crs="EPSG:4326")

    # Calculate centroid for each grid
    grids['centroid_lat'] = grids.geometry.centroid.y
    grids['centroid_lon'] = grids.geometry.centroid.x

    return grids


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 02_generate_grids.py <district_geojson> <output_geojson> [resolution]")
        sys.exit(1)

    district_file = sys.argv[1]
    output_file = sys.argv[2]
    resolution = int(sys.argv[3]) if len(sys.argv) > 3 else 8

    # Generate grids
    grids = generate_h3_grids(district_file, resolution)

    # Save
    grids.to_file(output_file, driver='GeoJSON')
    print(f"Saved {len(grids)} grids to {output_file}")