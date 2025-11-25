#!/usr/bin/env python3
"""
Create visualization maps for spatial accessibility analysis
"""

import sys
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import numpy as np

def create_accessibility_map(grids_geojson, output_png, district_name, facility_type='facility'):
    """
    Create a map showing grids colored by assigned facility and shaded by distance

    Args:
        grids_geojson: Path to grids with accessibility data
        output_png: Output PNG file path
        district_name: Name of the district
        facility_type: Type of facility (for title)
    """
    print(f"Creating visualization for {district_name}...")

    # Load grids
    grids = gpd.read_file(grids_geojson)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

    # MAP 1: Colored by facility assignment
    # Get unique facilities and assign colors
    if 'assigned_facility' in grids.columns and not grids['assigned_facility'].isna().all():
        facilities = grids['assigned_facility'].dropna().unique()
        n_facilities = len(facilities)

        # Create color map
        colors = plt.cm.tab20(np.linspace(0, 1, n_facilities))
        facility_colors = {facility: colors[i] for i, facility in enumerate(facilities)}

        # Plot grids colored by facility
        for facility in facilities:
            facility_grids = grids[grids['assigned_facility'] == facility]
            facility_grids.plot(
                ax=ax1,
                color=facility_colors[facility],
                edgecolor='black',
                linewidth=0.3,
                alpha=0.7
            )

        # Plot facility locations
        if 'assigned_facility_lat' in grids.columns:
            facility_points = grids[['assigned_facility', 'assigned_facility_lat', 'assigned_facility_lon']].drop_duplicates()

            for _, point in facility_points.iterrows():
                ax1.scatter(
                    point['assigned_facility_lon'],
                    point['assigned_facility_lat'],
                    c='red',
                    s=200,
                    marker='*',
                    edgecolors='black',
                    linewidths=2,
                    zorder=5
                )

        # Create legend
        legend_elements = [
            mpatches.Patch(facecolor=facility_colors[f], edgecolor='black', label=f)
            for f in facilities
        ]
        legend_elements.append(
            plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='red',
                      markersize=15, markeredgecolor='black', label='Facility Location')
        )

        ax1.legend(handles=legend_elements, loc='upper left', fontsize=8)
    else:
        grids.plot(ax=ax1, color='lightgray', edgecolor='black', linewidth=0.3)

    ax1.set_title(f'Facility Catchment Areas - {district_name}', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Longitude')
    ax1.set_ylabel('Latitude')
    ax1.grid(True, alpha=0.3)

    # MAP 2: Shaded by distance
    if 'route_distance_km' in grids.columns:
        grids.plot(
            column='route_distance_km',
            ax=ax2,
            legend=True,
            cmap='RdYlGn_r',  # Red (far) to Green (near)
            edgecolor='black',
            linewidth=0.3,
            legend_kwds={
                'label': 'Distance to nearest facility (km)',
                'orientation': 'horizontal',
                'pad': 0.05
            }
        )

        # Plot facility locations
        if 'assigned_facility_lat' in grids.columns:
            facility_points = grids[['assigned_facility_lat', 'assigned_facility_lon']].drop_duplicates()
            ax2.scatter(
                facility_points['assigned_facility_lon'],
                facility_points['assigned_facility_lat'],
                c='red',
                s=200,
                marker='*',
                edgecolors='black',
                linewidths=2,
                zorder=5,
                label='Facilities'
            )

        ax2.legend(loc='upper left')
    else:
        grids.plot(ax=ax2, color='lightgray', edgecolor='black', linewidth=0.3)

    ax2.set_title(f'Travel Distance to Nearest {facility_type.capitalize()} - {district_name}',
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.grid(True, alpha=0.3)

    # Add overall title
    fig.suptitle(f'Spatial Access to {facility_type.capitalize()} - {district_name}',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout()

    # Save
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"Saved map to {output_png}")

    plt.close()


def create_population_map(grids_geojson, output_png, district_name):
    """
    Create a map showing population distribution

    Args:
        grids_geojson: Path to grids with population data
        output_png: Output PNG file path
        district_name: Name of the district
    """
    print(f"Creating population map for {district_name}...")

    # Load grids
    grids = gpd.read_file(grids_geojson)

    if 'population' not in grids.columns:
        print("Warning: No population data found")
        return

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot population
    grids.plot(
        column='population',
        ax=ax,
        legend=True,
        cmap='YlOrRd',
        edgecolor='black',
        linewidth=0.3,
        legend_kwds={
            'label': 'Population per grid',
            'orientation': 'horizontal',
            'pad': 0.05
        }
    )

    ax.set_title(f'Population Distribution - {district_name}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"Saved population map to {output_png}")

    plt.close()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python 06_create_visualization.py <grids_geojson> <district_name> <output_prefix> [facility_type]")
        print("Example: python 06_create_visualization.py grids.geojson 'District A' output school")
        sys.exit(1)

    grids_file = sys.argv[1]
    district_name = sys.argv[2]
    output_prefix = sys.argv[3]
    facility_type = sys.argv[4] if len(sys.argv) > 4 else 'facility'

    # Create accessibility map
    create_accessibility_map(
        grids_file,
        f"{output_prefix}_accessibility.png",
        district_name,
        facility_type
    )

    # Create population map
    create_population_map(
        grids_file,
        f"{output_prefix}_population.png",
        district_name
    )

    print("Visualization complete!")