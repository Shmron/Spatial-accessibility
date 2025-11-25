#!/usr/bin/env python3
"""
Compute facility-level accessibility metrics including population-weighted distances
"""

import sys
import geopandas as gpd
import pandas as pd
import numpy as np

def compute_facility_metrics(grids_geojson, district_name):
    """
    Compute metrics per facility

    Args:
        grids_geojson: Path to grids with accessibility data
        district_name: Name of the district

    Returns:
        DataFrame with facility-level metrics
    """
    print(f"Computing metrics for {district_name}...")

    # Load grids
    grids = gpd.read_file(grids_geojson)

    # Check if we have assignments
    if 'assigned_facility' not in grids.columns or grids['assigned_facility'].isna().all():
        print("Warning: No facility assignments found")
        return pd.DataFrame({
            'district': [district_name],
            'facility_name': ['No facilities'],
            'total_grids_served': [0],
            'population_served': [0],
            'mean_distance_km': [np.nan],
            'median_distance_km': [np.nan],
            'min_distance_km': [np.nan],
            'max_distance_km': [np.nan],
            'pop_weighted_distance_km': [np.nan],
            'pop_within_5km': [0],
            'pop_within_10km': [0],
            'pop_within_20km': [0]
        })

    # Group by facility
    metrics_list = []

    for facility_name in grids['assigned_facility'].unique():
        if pd.isna(facility_name):
            continue

        # Get grids for this facility
        facility_grids = grids[grids['assigned_facility'] == facility_name].copy()

        # Calculate metrics
        total_grids = len(facility_grids)
        total_pop = facility_grids['population'].sum() if 'population' in facility_grids.columns else 0

        # Distance statistics
        distances = facility_grids['route_distance_km'].values
        mean_dist = np.mean(distances)
        median_dist = np.median(distances)
        min_dist = np.min(distances)
        max_dist = np.max(distances)

        # Population-weighted distance
        if 'population' in facility_grids.columns and total_pop > 0:
            pop_weighted_dist = np.average(
                distances,
                weights=facility_grids['population']
            )
        else:
            pop_weighted_dist = mean_dist

        # Population within distance bands
        pop_within_5km = facility_grids[facility_grids['route_distance_km'] <= 5]['population'].sum() if 'population' in facility_grids.columns else 0
        pop_within_10km = facility_grids[facility_grids['route_distance_km'] <= 10]['population'].sum() if 'population' in facility_grids.columns else 0
        pop_within_20km = facility_grids[facility_grids['route_distance_km'] <= 20]['population'].sum() if 'population' in facility_grids.columns else 0

        metrics = {
            'district': district_name,
            'facility_name': facility_name,
            'total_grids_served': total_grids,
            'population_served': total_pop,
            'mean_distance_km': mean_dist,
            'median_distance_km': median_dist,
            'min_distance_km': min_dist,
            'max_distance_km': max_dist,
            'pop_weighted_distance_km': pop_weighted_dist,
            'pop_within_5km': pop_within_5km,
            'pop_within_10km': pop_within_10km,
            'pop_within_20km': pop_within_20km,
            'percent_within_5km': (pop_within_5km / total_pop * 100) if total_pop > 0 else 0,
            'percent_within_10km': (pop_within_10km / total_pop * 100) if total_pop > 0 else 0,
        }

        metrics_list.append(metrics)

        print(f"  {facility_name}:")
        print(f"    Population served: {total_pop:,.0f}")
        print(f"    Pop-weighted distance: {pop_weighted_dist:.2f} km")

    # Create DataFrame
    metrics_df = pd.DataFrame(metrics_list)

    # Add district-level summary
    district_summary = {
        'district': district_name,
        'facility_name': 'DISTRICT_TOTAL',
        'total_grids_served': len(grids),
        'population_served': grids['population'].sum() if 'population' in grids.columns else 0,
        'mean_distance_km': grids['route_distance_km'].mean(),
        'median_distance_km': grids['route_distance_km'].median(),
        'min_distance_km': grids['route_distance_km'].min(),
        'max_distance_km': grids['route_distance_km'].max(),
        'pop_weighted_distance_km': np.average(
            grids['route_distance_km'],
            weights=grids['population']
        ) if 'population' in grids.columns and grids['population'].sum() > 0 else grids['route_distance_km'].mean(),
        'pop_within_5km': grids[grids['route_distance_km'] <= 5]['population'].sum() if 'population' in grids.columns else 0,
        'pop_within_10km': grids[grids['route_distance_km'] <= 10]['population'].sum() if 'population' in grids.columns else 0,
        'pop_within_20km': grids[grids['route_distance_km'] <= 20]['population'].sum() if 'population' in grids.columns else 0,
        'percent_within_5km': (grids[grids['route_distance_km'] <= 5]['population'].sum() / grids['population'].sum() * 100) if 'population' in grids.columns and grids['population'].sum() > 0 else 0,
        'percent_within_10km': (grids[grids['route_distance_km'] <= 10]['population'].sum() / grids['population'].sum() * 100) if 'population' in grids.columns and grids['population'].sum() > 0 else 0,
    }

    metrics_df = pd.concat([metrics_df, pd.DataFrame([district_summary])], ignore_index=True)

    return metrics_df


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python 05_compute_metrics.py <grids_geojson> <district_name> <output_csv>")
        sys.exit(1)

    grids_file = sys.argv[1]
    district_name = sys.argv[2]
    output_file = sys.argv[3]

    # Compute metrics
    metrics = compute_facility_metrics(grids_file, district_name)

    # Save
    metrics.to_csv(output_file, index=False)
    print(f"\nSaved metrics to {output_file}")
    print(f"\nSummary:")
    print(metrics.to_string(index=False))