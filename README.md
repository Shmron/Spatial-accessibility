# Spatial Access to Care/Education Workflow

A containerized Nextflow workflow for analyzing spatial accessibility to facilities (schools, healthcare) using OSM routing, hexagonal grids, and population data.

## Overview

This workflow calculates spatial accessibility metrics by:
1. Processing OSM road network with OSRM for routing
2. Generating H3 hexagonal grids for each district
3. Extracting population data for each grid cell
4. Assigning grids to nearest facilities
5. Calculating actual route distances and travel times
6. Computing population-weighted accessibility metrics
7. Creating visualization maps

## Quick Start

### 1. Prepare Your Data

Organize your data in the `data/` directory:

```
data/
├── region.osm.pbf              # OSM road network
├── districts.shp               # District boundaries
├── facilities.csv              # Facility locations
└── population.tif              # Population raster
```

**Where to get data:**
- **OSM PBF**: https://download.geofabrik.de/
- **Boundaries**: Your own data or https://gadm.org/
- **Population**: https://www.worldpop.org/
- **Facilities**: Your survey data or government records

### 2. (Optional) Validate Your Data

**Optional but recommended**: Run validation to catch data issues early:

```bash
python3 scripts/00_validate_data.py
```

This checks:
- All required files exist
- Coordinate systems are correct
- CSV columns are properly named
- Data bounds are reasonable

**If validation detects projected coordinates** (large numbers like 682222):

```bash
python3 scripts/00b_convert_coordinates.py
```

**Note**: The workflow includes basic validation, so you can skip these scripts if your data is clean.

### 3. Build Docker Container

```bash
chmod +x build_containers.sh
./build_containers.sh
```

Wait ~5-10 minutes for container to build.

### 4. Run Workflow

```bash
nextflow run spatial_access_workflow.nf \
  --osm_pbf data/region.osm.pbf \
  --districts_shp data/districts.shp \
  --facilities_csv data/facilities.csv \
  --population_tif data/population.tif \
  --facility_type healthcare \
  --outdir results
```

## Input Requirements

### 1. Administrative Boundaries (REQUIRED)

**Formats**: Shapefile (.shp), GeoJSON (.geojson), GeoPackage (.gpkg), or ZIP

**Requirements**:
- Polygon or MultiPolygon geometry
- Name attribute: `name`, `NAME`, `district`, or `DISTRICT`
- Any CRS (auto-reprojected)

### 2. OSM Road Network (REQUIRED)

**Format**: OSM PBF file (.osm.pbf)

**Download**: https://download.geofabrik.de/ (select your region)

### 3. Population Raster (REQUIRED)

**Format**: GeoTIFF (.tif) or any GDAL-readable raster

**Source**: WorldPop (recommended) - population count per pixel

**Requirements**:
- Population counts (not density)
- Valid nodata values
- Any CRS (auto-reprojected)

### 4. Facilities CSV (REQUIRED)

**Format**: CSV file

**Required columns**:
- `name` (or `facility_name`): Facility identifier
- `latitude` (or `lat`): Decimal degrees (WGS84)
- `longitude` (or `lon`, `long`): Decimal degrees (WGS84)

**Example**:
```csv
name,latitude,longitude,type
Central Hospital,6.1234,1.2345,hospital
District Clinic,6.5678,1.6789,clinic
```

**IMPORTANT**: Coordinates MUST be in WGS84 (EPSG:4326) decimal degrees:
- Latitude: -90 to 90
- Longitude: -180 to 180

If your coordinates are projected (UTM, etc.), run the conversion script first.

## Parameters

### Required
```bash
--osm_pbf PATH           # Path to OSM PBF file
--districts_shp PATH     # Path to districts shapefile
--facilities_csv PATH    # Path to facilities CSV
--population_tif PATH    # Path to population raster
```

### Optional
```bash
--facility_type TEXT     # Type of facility (default: 'school')
--hex_resolution INT     # H3 resolution 1-15 (default: 8)
                         # Lower = larger hexagons, faster
                         # Higher = smaller hexagons, more detail
                         # Recommended: 7-9 for district analysis

--osrm_host TEXT         # OSRM server host (default: 'localhost')
--osrm_port INT          # OSRM server port (default: 5000)
--outdir PATH            # Output directory (default: 'results')
```

### Help
```bash
nextflow run spatial_access_workflow.nf --help
```

## Output

```
results/
├── grids/
│   ├── District_A_grids.geojson              # Hexagonal grids
│   └── District_A_accessibility.geojson      # Grids with accessibility data
│
├── metrics/
│   └── District_A_metrics.csv                # Facility-level statistics
│
├── maps/
│   ├── District_A_accessibility.png          # Catchment area map
│   └── District_A_population.png             # Population distribution
│
├── summary.csv                                # Combined metrics for all districts
├── report.html                                # Nextflow execution report
├── timeline.html                              # Timeline visualization
└── trace.txt                                  # Detailed execution trace
```

## Key Metrics

The workflow outputs facility-level metrics:

- **population_served**: Total population in assigned grids
- **pop_weighted_distance_km**: Population-weighted average distance
- **mean_distance_km**: Average distance across all grids
- **median_distance_km**: Median distance
- **pop_within_5km**: Population within 5km of facility
- **pop_within_10km**: Population within 10km
- **pop_within_20km**: Population within 20km
- **percent_within_5km**: % of served population within 5km

## Common Issues & Solutions

### Issue: "Coordinates outside expected bounds"

**Cause**: Coordinates are projected (UTM, etc.), not lat/long

**Solution**:
```bash
python3 scripts/00b_convert_coordinates.py
```

### Issue: "Column 'name' not found in facilities CSV"

**Cause**: Different column naming

**Solution**: Rename columns to: `name`, `latitude`, `longitude`

```python
import pandas as pd
df = pd.read_csv('facilities.csv')
df = df.rename(columns={
    'Facility_Name': 'name',
    'Lat': 'latitude',
    'Lon': 'longitude'
})
df.to_csv('facilities.csv', index=False)
```

### Issue: "Out of memory"

**Solution**: Reduce H3 resolution:
```bash
--hex_resolution 7    # or even 6 for large regions
```

### Issue: "OSRM connection failed"

**Solution**: Workflow uses straight-line distance × 1.4 as fallback. This provides reasonable estimates.

## Resume Failed Run

If the workflow fails partway through:

```bash
nextflow run spatial_access_workflow.nf -resume \
  --osm_pbf data/region.osm.pbf \
  --districts_shp data/districts.shp \
  --facilities_csv data/facilities.csv \
  --population_tif data/population.tif
```

The `-resume` flag skips already-completed steps.

## Example: Togo Healthcare Access

```bash
# 1. (Optional) Validate data
python3 scripts/00_validate_data.py

# 2. (Optional) Convert coordinates if needed
python3 scripts/00b_convert_coordinates.py

# 3. Run workflow
nextflow run spatial_access_workflow.nf \
  --osm_pbf data/roads/togo-latest.osm.pbf \
  --districts_shp data/boundaries/geoBoundaries-TGO-ADM2.shp \
  --facilities_csv data/facilities/Togo_Health_Facilities_wgs84.csv \
  --population_tif data/population/tgo_pop_2025_CN_100m_R2025A_v1.tif \
  --facility_type healthcare \
  --hex_resolution 8 \
  --outdir results/togo_healthcare
```

## Requirements

- **Nextflow** ≥ 23.0.0
- **Docker** (or Singularity)
- **RAM**: 16GB recommended (8GB minimum)
- **Disk**: 2-10GB depending on region size

## Installation

### Install Nextflow
```bash
curl -s https://get.nextflow.io | bash
sudo mv nextflow /usr/local/bin/
```

### Install Docker
Follow instructions at: https://docs.docker.com/get-docker/

## Generalizability & FAIR Principles

This workflow is designed to be:

**Generalizable**:
- ✓ Works for any country or region
- ✓ Handles multiple facility types (schools, healthcare, etc.)
- ✓ Accepts various data formats (Shapefile, GeoJSON, GeoPackage)
- ✓ Auto-detects and reprojects coordinate systems
- ✓ Flexible CSV column naming

**FAIR** (Findable, Accessible, Interoperable, Reusable):
- ✓ Clear directory structure
- ✓ Standard geospatial formats
- ✓ Open-source tools only
- ✓ Containerized for reproducibility
- ✓ Well-documented with examples

## Advanced Usage

### Run on HPC Cluster

Edit `nextflow.config` for your cluster:

```groovy
profiles {
    cluster {
        process.executor = 'slurm'
        process.queue = 'normal'
        process.clusterOptions = '--account=your-account'
    }
}
```

Then run:
```bash
nextflow run spatial_access_workflow.nf -profile cluster ...
```

### Different H3 Resolutions

- **Resolution 6**: ~36 km² hexagons (regional analysis)
- **Resolution 7**: ~5 km² hexagons (district analysis)
- **Resolution 8**: ~0.7 km² hexagons (default, local analysis)
- **Resolution 9**: ~0.1 km² hexagons (detailed analysis)

## Citation

If you use this workflow, please cite:

- **Nextflow**: Di Tommaso P, et al. (2017) Nextflow enables reproducible computational workflows. Nature Biotechnology 35, 316–319
- **H3**: Uber H3: https://h3geo.org/
- **OSRM**: Luxen D & Vetter C (2011) Real-time routing with OpenStreetMap data. ACM GIS

## License

MIT License

## Support

For questions or issues:
1. Check this README
2. Run `python3 scripts/00_validate_data.py`
3. Open a GitHub issue

## Author

Rutendo Sibanda, 2025