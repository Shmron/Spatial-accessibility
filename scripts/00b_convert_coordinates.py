#!/usr/bin/env python3
"""
Convert projected coordinates to WGS84 lat/long
Handles facilities CSV with projected coordinates
"""

import pandas as pd
import sys

def convert_projected_to_latlon(csv_path, source_epsg=32631):
    """
    Convert projected coordinates to lat/lon

    Args:
        csv_path: Path to CSV with projected coordinates
        source_epsg: Source EPSG code (default 32631 = UTM Zone 31N for Togo)
    """
    try:
        from pyproj import Transformer
    except ImportError:
        print("[ERROR] pyproj not installed. Install with: pip install pyproj")
        sys.exit(1)

    # Read CSV
    df = pd.read_csv(csv_path)

    print(f"Original data:")
    print(f"  Longitude range: {df['longitude'].min():.2f} to {df['longitude'].max():.2f}")
    print(f"  Latitude range: {df['latitude'].min():.2f} to {df['latitude'].max():.2f}")

    # Create transformer (from projected to WGS84)
    transformer = Transformer.from_crs(f"EPSG:{source_epsg}", "EPSG:4326", always_xy=True)

    # Transform coordinates
    lon_latlong, lat_latlong = transformer.transform(
        df['longitude'].values,
        df['latitude'].values
    )

    # Create new dataframe with converted coordinates
    df_converted = df.copy()
    df_converted['longitude'] = lon_latlong
    df_converted['latitude'] = lat_latlong

    print(f"\nConverted data (WGS84):")
    print(f"  Longitude range: {df_converted['longitude'].min():.4f} to {df_converted['longitude'].max():.4f}")
    print(f"  Latitude range: {df_converted['latitude'].min():.4f} to {df_converted['latitude'].max():.4f}")

    # Sanity check for Togo (6-11N, 0-2E)
    if (5 < df_converted['latitude'].min() and df_converted['latitude'].max() < 12 and
        -1 < df_converted['longitude'].min() and df_converted['longitude'].max() < 3):
        print(f"  [OK] Coordinates within expected Togo bounds")
    else:
        print(f"  [WARN] Coordinates may be outside Togo - check EPSG code")

    # Save converted CSV
    output_path = csv_path.replace('.csv', '_wgs84.csv')
    df_converted.to_csv(output_path, index=False)
    print(f"\n[OK] Saved converted CSV: {output_path}")
    print(f"\nSample converted data:")
    print(df_converted[['name', 'longitude', 'latitude', 'type']].head())

    return output_path

if __name__ == "__main__":
    csv_file = "data/Togo_Health_Facilities.csv"

    # Try UTM Zone 31N (most of Togo)
    print("Converting coordinates from UTM Zone 31N (EPSG:32631) to WGS84...")
    print("=" * 60)

    output = convert_projected_to_latlon(csv_file, source_epsg=32631)

    print("\n" + "=" * 60)
    print("Use the converted file in your workflow:")
    print(f"  --facilities_csv {output}")
    print("=" * 60)