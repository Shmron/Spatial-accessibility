#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
========================================================================================
   Spatial Access to Health Facilities Workflow
========================================================================================
   Calculates spatial accessibility metrics using:
   - OSM routing network (OSRM)
   - H3 hexagonal grids
   - Population raster data
   - Facility locations

   Author: Rutendo Sibanda
   Date: 2025
========================================================================================
*/

// ============================================
// PARAMETERS
// ============================================

params.osm_pbf = "data/roads/togo-latest.osm.pbf"
params.districts_shp = "data/boundaries/geoBoundaries-TGO-ADM2_simplified.shp"
params.facilities_csv = "data/facilities/Togo_Health_Facilities_wgs84.csv"
params.population_tif = "data/population/tgo_pop_2025_CN_100m_R2025A_v1.tif"
params.facility_type = "health"
params.hex_resolution = 8
params.osrm_host = "localhost"
params.osrm_port = 5000
params.outdir = "results"
params.help = false

// Help message
if (params.help) {
    log.info"""
    ================================================================
    Spatial Access to Health Facilities Workflow
    ================================================================

    Usage:
      nextflow run spatial_access_workflow.nf

    Default Data Paths (can be overridden):
      --osm_pbf           data/roads/togo-latest.osm.pbf
      --districts_shp     data/boundaries/geoBoundaries-TGO-ADM2_simplified.shp
      --facilities_csv    data/facilities/Togo_Health_Facilities_wgs84.csv
      --population_tif    data/population/tgo_pop_2025_CN_100m_R2025A_v1.tif

    Optional Parameters:
      --facility_type     Type of facility (default: 'health')
      --hex_resolution    H3 hexagon resolution (default: 8)
      --outdir            Output directory (default: 'results')

    Output:
      results/
        ├── grids/          # Hexagonal grids with accessibility data
        ├── metrics/        # CSV files with facility metrics
        ├── maps/           # PNG visualization maps
        └── summary.csv     # Combined summary report

    ================================================================
    """.stripIndent()
    exit 0
}

// Validate required parameters
if (!params.osm_pbf || !params.districts_shp || !params.facilities_csv || !params.population_tif) {
    log.error "ERROR: Missing required parameters!"
    log.info "Run with --help to see usage information"
    exit 1
}

// ============================================
// PROCESS 1: Setup OSRM Routing Network
// ============================================

process setupOSRM {
    container 'osrm/osrm-backend:latest'

    input:
    path osm_pbf

    output:
    path "osrm_data/*", emit: osrm_files

    script:
    """
    set -e

    echo "Setting up OSRM routing network..."
    echo "Input PBF: ${osm_pbf}"

    mkdir -p osrm_data

    # Copy PBF to output directory and work there
    cp "${osm_pbf}" osrm_data/
    cd osrm_data

    FILENAME=\$(basename "${osm_pbf}")

    # Extract the network
    echo "Step 1/3: Extracting network..."
    osrm-extract -p /opt/car.lua "\$FILENAME"

    # Get base name for .osrm files
    OSRM_BASE="\${FILENAME%.osm.pbf}"
    OSRM_BASE="\${OSRM_BASE%.pbf}"

    # Partition the network
    echo "Step 2/3: Partitioning network..."
    osrm-partition "\${OSRM_BASE}.osrm"

    # Customize the network
    echo "Step 3/3: Customizing network..."
    osrm-customize "\${OSRM_BASE}.osrm"

    echo "OSRM setup complete!"
    ls -lh
    """
}

// ============================================
// PROCESS 2: Split Districts into Separate Files
// ============================================

process splitDistricts {
    container 'spatial-analysis:latest'

    input:
    path 'shapefile/*'
    path facilities_csv

    output:
    path "districts/*.geojson", emit: district_files

    script:
    """
    #!/usr/bin/env python3
    import geopandas as gpd
    import pandas as pd
    from pathlib import Path
    import glob

    # Find the .shp file
    shp_files = glob.glob("shapefile/*.shp")
    if not shp_files:
        raise FileNotFoundError("No .shp file found in shapefile directory")
    shp_file = shp_files[0]

    # Read districts
    districts = gpd.read_file(shp_file)
    facilities = pd.read_csv("${facilities_csv}")

    # Create output directory
    Path("districts").mkdir(exist_ok=True)

    print(f"Found {len(districts)} districts")

    # Save each district as separate file
    for idx, district in districts.iterrows():
        # Get district name (try common column names)
        district_name = None
        for col in ['name', 'NAME', 'district', 'DISTRICT', 'District']:
            if col in districts.columns:
                district_name = str(district[col]).replace(' ', '_').replace('/', '_')
                break

        if not district_name:
            district_name = f'district_{idx}'

        # Create GeoDataFrame with single district
        district_gdf = gpd.GeoDataFrame([district], geometry='geometry', crs=districts.crs)

        # Save as GeoJSON
        output_file = f"districts/{district_name}.geojson"
        district_gdf.to_file(output_file, driver='GeoJSON')

        print(f"Created {output_file}")
    """
}

// ============================================
// PROCESS 3: Generate H3 Hexagonal Grids
// ============================================

process generateGrids {
    container 'spatial-analysis:latest'
    tag "${district_file.baseName}"
    publishDir "${params.outdir}/grids", mode: 'copy', pattern: "*_grids.geojson"

    input:
    path district_file
    val hex_resolution

    output:
    tuple val("${district_file.baseName}"), path("${district_file.baseName}_grids.geojson"), emit: grids

    script:
    """
    python /scripts/02_generate_grids.py \\
        ${district_file} \\
        ${district_file.baseName}_grids.geojson \\
        ${hex_resolution}
    """
}

// ============================================
// PROCESS 4: Extract Population
// ============================================

process extractPopulation {
    container 'spatial-analysis:latest'
    tag "${district_name}"

    input:
    tuple val(district_name), path(grids_file)
    path population_tif

    output:
    tuple val(district_name), path("${district_name}_grids_pop.geojson"), emit: grids_with_pop

    script:
    """
    python /scripts/03_extract_population.py \\
        ${grids_file} \\
        ${population_tif} \\
        ${district_name}_grids_pop.geojson
    """
}

// ============================================
// PROCESS 5: Filter Facilities per District
// ============================================

process filterFacilities {
    container 'spatial-analysis:latest'
    tag "${district_name}"
    debug true

    input:
    tuple val(district_name), path(grids_file), path(district_file)
    path facilities_csv

    output:
    tuple val(district_name), path("${district_name}_facilities.csv"), emit: district_facilities

    script:
    """
    #!/usr/bin/env python3
    import geopandas as gpd
    import pandas as pd
    import os

    # Debug: Check what files exist
    print(f"Working directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    print(f"Facilities CSV path: ${facilities_csv}")
    print(f"Facilities CSV exists: {os.path.exists('${facilities_csv}')}")

    # Read district
    district = gpd.read_file("${district_file}")
    print(f"District loaded: {len(district)} features, CRS: {district.crs}")

    # Read facilities
    facilities = pd.read_csv("${facilities_csv}")
    print(f"Facilities loaded from CSV: {len(facilities)}")
    facilities_gdf = gpd.GeoDataFrame(
        facilities,
        geometry=gpd.points_from_xy(facilities.longitude, facilities.latitude),
        crs="EPSG:4326"
    )

    # Match CRS
    if district.crs != facilities_gdf.crs:
        facilities_gdf = facilities_gdf.to_crs(district.crs)

    # Get facilities within district
    district_geom = district.geometry.iloc[0]
    facilities_in_district = facilities_gdf[facilities_gdf.within(district_geom)]

    print(f"Found {len(facilities_in_district)} facilities in ${district_name}")

    # Save
    if len(facilities_in_district) > 0:
        facilities_in_district[['name', 'latitude', 'longitude']].to_csv(
            "${district_name}_facilities.csv",
            index=False
        )
    else:
        # Create empty file with header
        pd.DataFrame(columns=['name', 'latitude', 'longitude']).to_csv(
            "${district_name}_facilities.csv",
            index=False
        )
    """
}

// ============================================
// PROCESS 6: Calculate Accessibility
// ============================================

process calculateAccessibility {
    container 'spatial-analysis:latest'
    tag "${district_name}"
    publishDir "${params.outdir}/grids", mode: 'copy', pattern: "*_accessibility.geojson"

    input:
    tuple val(district_name), path(grids_file), path(facilities_file)
    val osrm_host
    val osrm_port

    output:
    tuple val(district_name), path("${district_name}_accessibility.geojson"), emit: results

    script:
    """
    python /scripts/04_calculate_accessibility.py \\
        ${grids_file} \\
        ${facilities_file} \\
        ${district_name}_accessibility.geojson \\
        ${osrm_host} \\
        ${osrm_port}
    """
}

// ============================================
// PROCESS 7: Compute Metrics
// ============================================

process computeMetrics {
    container 'spatial-analysis:latest'
    tag "${district_name}"
    publishDir "${params.outdir}/metrics", mode: 'copy'

    input:
    tuple val(district_name), path(accessibility_file)

    output:
    path "${district_name}_metrics.csv", emit: metrics

    script:
    """
    python /scripts/05_compute_metrics.py \\
        ${accessibility_file} \\
        ${district_name} \\
        ${district_name}_metrics.csv
    """
}

// ============================================
// PROCESS 8: Create Visualizations
// ============================================

process createVisualization {
    container 'spatial-analysis:latest'
    tag "${district_name}"
    publishDir "${params.outdir}/maps", mode: 'copy'

    input:
    tuple val(district_name), path(accessibility_file)
    val facility_type

    output:
    path "${district_name}_*.png"

    script:
    """
    python /scripts/06_create_visualization.py \\
        ${accessibility_file} \\
        "${district_name}" \\
        ${district_name} \\
        ${facility_type}
    """
}

// ============================================
// PROCESS 9: Aggregate Summary
// ============================================

process aggregateSummary {
    container 'spatial-analysis:latest'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path metrics_files

    output:
    path "summary.csv", emit: summary

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    import glob

    # Combine all metrics
    all_metrics = []
    for f in glob.glob("*_metrics.csv"):
        all_metrics.append(pd.read_csv(f))

    if all_metrics:
        combined = pd.concat(all_metrics, ignore_index=True)
        combined.to_csv("summary.csv", index=False)
        print(f"Combined {len(all_metrics)} administrative unit metric files")
        print("\\nSummary Statistics:")
        print(combined[combined['facility_name'] == 'DISTRICT_TOTAL'][
            ['district', 'population_served', 'pop_weighted_distance_km']
        ].to_string(index=False))
    else:
        pd.DataFrame().to_csv("summary.csv", index=False)
    """
}

// ============================================
// PROCESS 10: Create Summary Statistics Table
// ============================================

process createSummaryTable {
    container 'spatial-analysis:latest'
    publishDir "${params.outdir}", mode: 'copy'

    input:
    path summary_csv
    path 'boundaries/*'

    output:
    path "final_summary_table.png"
    path "final_summary_by_unit.csv"
    path "final_detailed_results.csv"

    script:
    """
    python /scripts/07_create_summary_table.py \
        ${summary_csv} \
        boundaries/${params.districts_shp.split('/').last()} \
        final
    """
}

// ============================================
// MAIN WORKFLOW
// ============================================

workflow {
    // Print workflow info
    log.info """
    ================================================================
    Spatial Access to ${params.facility_type.capitalize()} - Analysis
    ================================================================
    OSM PBF:          ${params.osm_pbf}
    Districts:        ${params.districts_shp}
    Facilities:       ${params.facilities_csv}
    Population:       ${params.population_tif}
    H3 Resolution:    ${params.hex_resolution}
    Output Directory: ${params.outdir}
    ================================================================
    """.stripIndent()

    // Create input channels
    osm_pbf_ch = Channel.fromPath(params.osm_pbf, checkIfExists: true)

    // For shapefiles, we need to collect all component files (.shp, .shx, .dbf, .prj, etc.)
    def shp_base = params.districts_shp.replaceAll(/\.shp$/, '')
    districts_ch = Channel.fromPath("${shp_base}.*", checkIfExists: true).collect()

    // Convert to value channels so they can be reused across all districts
    facilities_ch = Channel.fromPath(params.facilities_csv, checkIfExists: true).first()
    population_ch = Channel.fromPath(params.population_tif, checkIfExists: true).first()

    // Step 1: Setup OSRM (can run in parallel with district splitting)
    osrm_data = setupOSRM(osm_pbf_ch)

    // Step 2: Split districts into separate files
    district_files = splitDistricts(districts_ch, facilities_ch)

    // Step 3: For each district, generate grids
    grids = generateGrids(
        district_files.flatten(),
        params.hex_resolution
    )

    // Step 4: Extract population for each district's grids
    grids_with_pop = extractPopulation(
        grids,
        population_ch
    )

    // Step 5: Filter facilities per district
    // Match district files with grids by district name
    district_files_with_name = district_files.flatten()
        .map { file -> tuple(file.baseName, file) }

    // Combine grids with district files
    grids_and_districts = grids_with_pop.join(district_files_with_name)

    district_facilities = filterFacilities(
        grids_and_districts,
        facilities_ch
    )

    // Step 6: Combine grids with facilities for accessibility calculation
    accessibility_input = grids_with_pop
        .join(district_facilities)

    // Step 7: Calculate accessibility (requires OSRM to be ready)
    accessibility = calculateAccessibility(
        accessibility_input,
        params.osrm_host,
        params.osrm_port
    )

    // Step 8: Compute metrics
    metrics = computeMetrics(accessibility)

    // Step 9: Create visualizations
    maps = createVisualization(
        accessibility,
        params.facility_type
    )

    // Step 10: Aggregate all metrics
    summary = aggregateSummary(metrics.collect())

    // Step 11: Create summary statistics table with proper names
    summary_table = createSummaryTable(
        summary,
        districts_ch
    )

    // Print completion message
    summary.view {
        log.info """
        ================================================================
        Workflow Complete!
        ================================================================
        Results saved to: ${params.outdir}

        Summary files created:
        - summary.csv (combined metrics)
        - final_summary_table.png (visualization)
        - final_summary_by_unit.csv (summary by administrative unit)
        - final_detailed_results.csv (detailed results with proper names)
        ================================================================
        """
    }
}

// ============================================
// WORKFLOW COMPLETION
// ============================================

workflow.onComplete {
    log.info """
    ================================================================
    Pipeline completed at: ${workflow.complete}
    Duration:              ${workflow.duration}
    Success:               ${workflow.success}
    Exit status:           ${workflow.exitStatus}
    ================================================================
    """.stripIndent()
}