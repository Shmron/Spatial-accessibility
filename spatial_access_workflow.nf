#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
========================================================================================
   Spatial Access to Care/Education Workflow
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

params.osm_pbf = null
params.districts_shp = null
params.facilities_csv = null
params.population_tif = null
params.facility_type = "school"
params.hex_resolution = 8
params.osrm_host = "localhost"
params.osrm_port = 5000
params.outdir = "results"
params.help = false

// Help message
if (params.help) {
    log.info"""
    ================================================================
    Spatial Access to Care/Education Workflow
    ================================================================

    Usage:
      nextflow run spatial_access_workflow.nf \\
        --osm_pbf data/region.osm.pbf \\
        --districts_shp data/districts.shp \\
        --facilities_csv data/facilities.csv \\
        --population_tif data/population.tif \\
        --facility_type school \\
        --outdir results

    Required Parameters:
      --osm_pbf           Path to OSM PBF file
      --districts_shp     Path to districts shapefile
      --facilities_csv    Path to facilities CSV (columns: name, latitude, longitude)
      --population_tif    Path to population raster (TIF)

    Optional Parameters:
      --facility_type     Type of facility (default: 'school')
      --hex_resolution    H3 hexagon resolution (default: 8)
      --osrm_host         OSRM server host (default: 'localhost')
      --osrm_port         OSRM server port (default: 5000)
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
    bash ${projectDir}/scripts/01_setup_osrm.sh ${osm_pbf} osrm_data
    """
}

// ============================================
// PROCESS 2: Split Districts into Separate Files
// ============================================

process splitDistricts {
    container 'spatial-analysis:latest'

    input:
    path districts_shp
    path facilities_csv

    output:
    path "districts/*.geojson", emit: district_files

    script:
    """
    #!/usr/bin/env python3
    import geopandas as gpd
    import pandas as pd
    from pathlib import Path

    # Read districts
    districts = gpd.read_file("${districts_shp}")
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
    python ${projectDir}/scripts/02_generate_grids.py \\
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
    python ${projectDir}/scripts/03_extract_population.py \\
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

    input:
    tuple val(district_name), path(grids_file)
    path district_file
    path facilities_csv

    output:
    tuple val(district_name), path("${district_name}_facilities.csv"), emit: district_facilities

    script:
    """
    #!/usr/bin/env python3
    import geopandas as gpd
    import pandas as pd

    # Read district
    district = gpd.read_file("${district_file}")

    # Read facilities
    facilities = pd.read_csv("${facilities_csv}")
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
    python ${projectDir}/scripts/04_calculate_accessibility.py \\
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
    python ${projectDir}/scripts/05_compute_metrics.py \\
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
    python ${projectDir}/scripts/06_create_visualization.py \\
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
    path "summary.csv"

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
        print(f"Combined {len(all_metrics)} district metric files")
        print("\\nSummary Statistics:")
        print(combined[combined['facility_name'] == 'DISTRICT_TOTAL'][
            ['district', 'population_served', 'pop_weighted_distance_km']
        ].to_string(index=False))
    else:
        pd.DataFrame().to_csv("summary.csv", index=False)
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
    districts_ch = Channel.fromPath(params.districts_shp, checkIfExists: true)
    facilities_ch = Channel.fromPath(params.facilities_csv, checkIfExists: true)
    population_ch = Channel.fromPath(params.population_tif, checkIfExists: true)

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
    // Need to match district files with grids
    district_files_ch = district_files.flatten()
        .map { file -> tuple(file.baseName, file) }

    district_facilities = filterFacilities(
        grids_with_pop,
        district_files_ch.map { it[1] },
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

    // Print completion message
    summary.view {
        log.info """
        ================================================================
        Workflow Complete!
        ================================================================
        Results saved to: ${params.outdir}
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