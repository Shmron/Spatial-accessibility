#!/usr/bin/env python3
"""
Extract population values from raster for each hexagonal grid
"""

import sys
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np

def extract_population(grids_geojson, population_tif):
    """
    Extract population from raster for each grid polygon

    Args:
        grids_geojson: Path to grids GeoJSON file
        population_tif: Path to population raster (TIF)

    Returns:
        GeoDataFrame with population column added
    """
    print(f"Reading grids from {grids_geojson}...")
    grids = gpd.read_file(grids_geojson)

    print(f"Reading population raster from {population_tif}...")
    with rasterio.open(population_tif) as src:
        print(f"Raster CRS: {src.crs}")
        print(f"Raster bounds: {src.bounds}")

        # Reproject grids to match raster CRS if needed
        if grids.crs != src.crs:
            print(f"Reprojecting grids from {grids.crs} to {src.crs}...")
            grids = grids.to_crs(src.crs)

        # Extract population for each grid
        populations = []

        print(f"Extracting population for {len(grids)} grids...")
        for idx, row in grids.iterrows():
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(grids)} grids...")

            try:
                # Mask raster with grid polygon
                out_image, out_transform = mask(src, [row.geometry], crop=True, nodata=src.nodata)

                # Sum population in grid (handle nodata values)
                valid_data = out_image[0]  # First band

                if src.nodata is not None:
                    valid_data = valid_data[valid_data != src.nodata]

                # Only sum positive values
                valid_data = valid_data[valid_data > 0]

                pop = np.sum(valid_data) if len(valid_data) > 0 else 0
                populations.append(float(pop))

            except Exception as e:
                print(f"  Warning: Could not extract population for grid {idx}: {e}")
                populations.append(0)

        grids['population'] = populations

        # Convert back to WGS84 for output
        if grids.crs != "EPSG:4326":
            grids = grids.to_crs("EPSG:4326")

    total_pop = grids['population'].sum()
    print(f"Total population extracted: {total_pop:,.0f}")
    print(f"Grids with population > 0: {(grids['population'] > 0).sum()}")

    return grids


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python 03_extract_population.py <grids_geojson> <population_tif> <output_geojson>")
        sys.exit(1)

    grids_file = sys.argv[1]
    pop_tif = sys.argv[2]
    output_file = sys.argv[3]

    # Extract population
    grids_with_pop = extract_population(grids_file, pop_tif)

    # Save
    grids_with_pop.to_file(output_file, driver='GeoJSON')
    print(f"Saved results to {output_file}")