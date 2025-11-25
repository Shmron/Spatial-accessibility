#!/usr/bin/env python3
"""
Assign grids to nearest facilities and calculate routing distances using OSRM
"""

import sys
import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import requests
import time

def assign_grids_to_facilities(grids, facilities):
    """
    Assign each grid to its nearest facility using KDTree

    Args:
        grids: GeoDataFrame with grid polygons
        facilities: DataFrame with facility coordinates (lat, lon)

    Returns:
        grids with assigned facility information
    """
    print(f"Assigning {len(grids)} grids to {len(facilities)} facilities...")

    # Get grid centroids
    grid_coords = np.array([[row['centroid_lat'], row['centroid_lon']]
                            for _, row in grids.iterrows()])

    # Get facility coordinates
    facility_coords = facilities[['latitude', 'longitude']].values

    # Build KDTree for nearest neighbor search
    tree = cKDTree(facility_coords)

    # Find nearest facility for each grid
    distances, indices = tree.query(grid_coords)

    # Assign facilities to grids
    grids['assigned_facility'] = facilities.iloc[indices]['name'].values
    grids['assigned_facility_id'] = facilities.iloc[indices].index.values
    grids['assigned_facility_lat'] = facility_coords[indices, 0]
    grids['assigned_facility_lon'] = facility_coords[indices, 1]
    grids['straight_line_distance_km'] = distances * 111  # Rough conversion to km

    print(f"Assignment complete!")
    print(f"Facilities assigned: {grids['assigned_facility'].nunique()}")

    return grids


def calculate_osrm_distances(grids, osrm_host='localhost', osrm_port=5000, batch_size=100):
    """
    Calculate actual routing distances using OSRM

    Args:
        grids: GeoDataFrame with assigned facilities
        osrm_host: OSRM server host
        osrm_port: OSRM server port
        batch_size: Number of routes to calculate per request

    Returns:
        grids with route distances and travel times
    """
    print(f"Calculating OSRM routes...")
    print(f"OSRM endpoint: http://{osrm_host}:{osrm_port}")

    route_distances = []
    route_durations = []

    # Process in batches to avoid overwhelming OSRM
    total = len(grids)

    for idx, row in grids.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{total} routes...")

        origin_lon = row['centroid_lon']
        origin_lat = row['centroid_lat']
        dest_lon = row['assigned_facility_lon']
        dest_lat = row['assigned_facility_lat']

        # OSRM expects lon,lat format
        url = f"http://{osrm_host}:{osrm_port}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=false"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data['code'] == 'Ok' and len(data['routes']) > 0:
                    # Distance in meters, duration in seconds
                    distance_m = data['routes'][0]['distance']
                    duration_s = data['routes'][0]['duration']

                    route_distances.append(distance_m / 1000)  # Convert to km
                    route_durations.append(duration_s / 60)    # Convert to minutes
                else:
                    # No route found, use straight line distance
                    route_distances.append(row['straight_line_distance_km'])
                    route_durations.append(row['straight_line_distance_km'] / 0.5)  # Assume 30 km/h
            else:
                # OSRM error, use straight line
                route_distances.append(row['straight_line_distance_km'])
                route_durations.append(row['straight_line_distance_km'] / 0.5)

        except Exception as e:
            print(f"  Warning: OSRM request failed for grid {idx}: {e}")
            # Fallback to straight line distance
            route_distances.append(row['straight_line_distance_km'])
            route_durations.append(row['straight_line_distance_km'] / 0.5)

        # Small delay to avoid overwhelming OSRM
        time.sleep(0.01)

    grids['route_distance_km'] = route_distances
    grids['travel_time_min'] = route_durations

    print(f"Route calculation complete!")
    print(f"Average route distance: {np.mean(route_distances):.2f} km")
    print(f"Average travel time: {np.mean(route_durations):.2f} minutes")

    return grids


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python 04_calculate_accessibility.py <grids_geojson> <facilities_csv> <output_geojson> <osrm_host> [osrm_port]")
        print("Example: python 04_calculate_accessibility.py grids.geojson facilities.csv output.geojson localhost 5000")
        sys.exit(1)

    grids_file = sys.argv[1]
    facilities_file = sys.argv[2]
    output_file = sys.argv[3]
    osrm_host = sys.argv[4]
    osrm_port = int(sys.argv[5]) if len(sys.argv) > 5 else 5000

    # Load data
    print(f"Loading grids from {grids_file}...")
    grids = gpd.read_file(grids_file)

    print(f"Loading facilities from {facilities_file}...")
    facilities = pd.read_csv(facilities_file)

    # Validate facilities have required columns
    required_cols = ['name', 'latitude', 'longitude']
    if not all(col in facilities.columns for col in required_cols):
        print(f"Error: Facilities CSV must have columns: {required_cols}")
        sys.exit(1)

    print(f"Loaded {len(grids)} grids and {len(facilities)} facilities")

    if len(facilities) == 0:
        print("Warning: No facilities found. Creating output with no assignments.")
        grids['assigned_facility'] = None
        grids['route_distance_km'] = np.nan
        grids['travel_time_min'] = np.nan
    else:
        # Step 1: Assign grids to nearest facilities
        grids = assign_grids_to_facilities(grids, facilities)

        # Step 2: Calculate OSRM routes
        grids = calculate_osrm_distances(grids, osrm_host, osrm_port)

    # Save results
    grids.to_file(output_file, driver='GeoJSON')
    print(f"Saved results to {output_file}")