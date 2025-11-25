#!/usr/bin/env python3
"""
Validate and prepare data for spatial accessibility workflow
Handles flexible input formats and provides clear feedback
"""

import os
import sys
import zipfile
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if file exists and report"""
    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"  [OK] {description}: {filepath} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  [FAIL] {description}: NOT FOUND - {filepath}")
        return False

def extract_boundaries_zip(zip_path, output_dir):
    """Extract boundaries ZIP file"""
    print(f"\n2. Extracting boundaries ZIP...")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    # Find the shapefile
    shp_files = list(output_dir.glob("**/*.shp"))
    if shp_files:
        print(f"  [OK] Extracted to: {output_dir}")
        print(f"  [OK] Found shapefile: {shp_files[0].name}")
        return str(shp_files[0])
    else:
        print(f"  [FAIL] No .shp file found after extraction")
        return None

def validate_facilities_csv(csv_path):
    """Validate facilities CSV and check columns"""
    try:
        import pandas as pd
    except ImportError:
        print("  [WARN] pandas not available - skipping CSV validation")
        return True

    print(f"\n3. Validating facilities CSV...")

    df = pd.read_csv(csv_path)
    print(f"  [OK] Loaded {len(df)} facilities")
    print(f"  Columns: {list(df.columns)}")

    # Check for required columns (flexible naming)
    name_cols = ['name', 'facility_name', 'Name', 'Facility_Name', 'FACILITY_NAME']
    lat_cols = ['latitude', 'lat', 'Latitude', 'Lat', 'LAT']
    lon_cols = ['longitude', 'lon', 'long', 'Longitude', 'Lon', 'Long', 'LON']

    has_name = any(col in df.columns for col in name_cols)
    has_lat = any(col in df.columns for col in lat_cols)
    has_lon = any(col in df.columns for col in lon_cols)

    if has_name and has_lat and has_lon:
        print(f"  [OK] Has required columns (name, latitude, longitude)")

        # Get actual column names
        name_col = next((col for col in name_cols if col in df.columns), None)
        lat_col = next((col for col in lat_cols if col in df.columns), None)
        lon_col = next((col for col in lon_cols if col in df.columns), None)

        # Check coordinate ranges
        lat_min, lat_max = df[lat_col].min(), df[lat_col].max()
        lon_min, lon_max = df[lon_col].min(), df[lon_col].max()

        print(f"  Latitude range: {lat_min:.4f} to {lat_max:.4f}")
        print(f"  Longitude range: {lon_min:.4f} to {lon_max:.4f}")

        # Check if coordinates are reasonable for Togo
        # Togo is roughly 6-11N, 0-2E
        if 5 < lat_min and lat_max < 12 and -1 < lon_min and lon_max < 3:
            print(f"  [OK] Coordinates within Togo bounds")
        else:
            print(f"  [WARN] Warning: Coordinates may be outside Togo")

        # Standardize column names if needed
        if name_col != 'name' or lat_col != 'latitude' or lon_col != 'longitude':
            print(f"\n  Standardizing column names...")
            df_standard = df.rename(columns={
                name_col: 'name',
                lat_col: 'latitude',
                lon_col: 'longitude'
            })
            output_path = csv_path.replace('.csv', '_standardized.csv')
            df_standard.to_csv(output_path, index=False)
            print(f"  [OK] Saved standardized CSV: {output_path}")
            print(f"  --> Use this file in your workflow: --facilities_csv {output_path}")

        return True
    else:
        print(f"  [FAIL] Missing required columns!")
        print(f"    Need: name column = {has_name}")
        print(f"    Need: latitude column = {has_lat}")
        print(f"    Need: longitude column = {has_lon}")
        return False

def validate_population_raster(tif_path):
    """Validate population raster"""
    try:
        import rasterio
    except ImportError:
        print("  [WARN] rasterio not available - skipping raster validation")
        return True

    print(f"\n4. Validating population raster...")

    with rasterio.open(tif_path) as src:
        print(f"  [OK] Dimensions: {src.width} x {src.height}")
        print(f"  [OK] CRS: {src.crs}")
        print(f"  [OK] Bounds: {src.bounds}")
        print(f"  [OK] Data type: {src.dtypes[0]}")

        # Read a small sample
        sample = src.read(1, window=((0, 100), (0, 100)))
        valid_data = sample[sample > 0]

        if len(valid_data) > 0:
            print(f"  [OK] Sample values: min={valid_data.min():.1f}, max={valid_data.max():.1f}")
        else:
            print(f"  [WARN] Warning: No positive values in sample area")

    return True

def main():
    print("=" * 60)
    print("Spatial Accessibility Workflow - Data Validation")
    print("=" * 60)

    # Define expected file paths (organized structure)
    data_dir = Path("data")

    boundaries_zip = data_dir / "geoBoundaries-TGO-ADM2-all.zip"
    boundaries_shp = data_dir / "boundaries" / "geoBoundaries-TGO-ADM2.shp"
    osm_pbf = data_dir / "roads" / "togo-latest.osm.pbf"
    population_tif = data_dir / "population" / "tgo_pop_2025_CN_100m_R2025A_v1.tif"
    facilities_csv = data_dir / "facilities" / "Togo_Health_Facilities_wgs84.csv"

    print("\n1. Checking for input files...")

    all_present = True
    all_present &= check_file_exists(boundaries_zip, "Boundaries ZIP")
    all_present &= check_file_exists(osm_pbf, "OSM PBF")
    all_present &= check_file_exists(population_tif, "Population raster")
    all_present &= check_file_exists(facilities_csv, "Facilities CSV")

    if not all_present:
        print("\n[FAIL] Some required files are missing!")
        print("  Please ensure all files are in the data/ directory")
        sys.exit(1)

    # Extract boundaries
    boundaries_shp = extract_boundaries_zip(boundaries_zip, data_dir / "boundaries")

    # Validate facilities CSV
    facilities_ok = validate_facilities_csv(facilities_csv)

    # Validate population raster
    pop_ok = validate_population_raster(population_tif)

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    if boundaries_shp and facilities_ok and pop_ok:
        print("[OK] All data validated successfully!")
        print("\nReady to run workflow:")
        print("\nCommand:")
        print("nextflow run spatial_access_workflow.nf \\")
        print(f"  --osm_pbf {osm_pbf} \\")
        print(f"  --districts_shp {boundaries_shp} \\")

        # Check if standardized CSV exists
        facilities_std = str(facilities_csv).replace('.csv', '_standardized.csv')
        if os.path.exists(facilities_std):
            print(f"  --facilities_csv {facilities_std} \\")
        else:
            print(f"  --facilities_csv {facilities_csv} \\")

        print(f"  --population_tif {population_tif} \\")
        print(f"  --facility_type healthcare \\")
        print(f"  --outdir results/togo_healthcare")
        print("")
    else:
        print("[FAIL] Some validation checks failed")
        print("  Please fix the issues above before running the workflow")
        sys.exit(1)

if __name__ == "__main__":
    main()