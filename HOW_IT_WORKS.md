# How Containers & Workflows Connect - Complete Flow

## For Your Workshop Demonstration

This document shows EXACTLY how containers, Nextflow, and your data connect.

---

## The Complete Flow (Step-by-Step)

### Step 1: Build the Container

```bash
./build_containers.sh
```

**What happens:**
```
Dockerfile.spatial
    ↓
    Reads instructions (FROM python:3.11, RUN pip install...)
    ↓
    Downloads Python 3.11 base image
    ↓
    Installs: geopandas, h3, rasterio, matplotlib, scipy, pandas
    ↓
    Creates: spatial-analysis:latest container image
    ↓
    Stored locally in Docker
```

**Result:** A container with ALL Python geospatial tools installed.

---

### Step 2: Nextflow Reads Your Command

```bash
nextflow run spatial_access_workflow.nf \
  --osm_pbf data/roads/togo-latest.osm.pbf \
  --districts_shp data/boundaries/geoBoundaries-TGO-ADM2.shp \
  --facilities_csv data/facilities/Togo_Health_Facilities_wgs84.csv \
  --population_tif data/population/tgo_pop_2025_CN_100m_R2025A_v1.tif \
  --facility_type healthcare \
  --outdir results
```

**What Nextflow does:**
1. Reads `spatial_access_workflow.nf`
2. Reads `nextflow.config`
3. Creates execution plan (DAG - Directed Acyclic Graph)
4. Identifies which processes can run in parallel

---

### Step 3: Nextflow Launches Processes in Containers

Each process runs inside a container. Here's the flow:

```
┌─────────────────────────────────────────────────────────────┐
│  PROCESS 1: setupOSRM                                       │
│  Container: osrm/osrm-backend:latest                        │
├─────────────────────────────────────────────────────────────┤
│  Input:  data/roads/togo-latest.osm.pbf                     │
│  Script: scripts/01_setup_osrm.sh                          │
│  Action: Docker runs container, mounts data, executes script│
│  Output: work/xx/osrm_data/* (routing network files)       │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  PROCESS 2: splitDistricts                                  │
│  Container: spatial-analysis:latest  ← YOUR CONTAINER!      │
├─────────────────────────────────────────────────────────────┤
│  Input:  data/boundaries/geoBoundaries-TGO-ADM2.shp        │
│  Input:  data/facilities/Togo_Health_Facilities_wgs84.csv │
│  Script: Python code inside workflow (uses geopandas)      │
│  Action: Docker runs YOUR container with Python code       │
│  Output: work/yy/districts/*.geojson (1 file per district) │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  PROCESS 3: generateGrids (RUNS IN PARALLEL FOR EACH)      │
│  Container: spatial-analysis:latest  ← YOUR CONTAINER!      │
├─────────────────────────────────────────────────────────────┤
│  Input:  work/yy/districts/District_A.geojson              │
│  Script: scripts/02_generate_grids.py                      │
│  Action: Docker runs container, executes Python script      │
│  Output: work/zz/District_A_grids.geojson                  │
└─────────────────────────────────────────────────────────────┘
         ↓
     ... (more processes, all in containers)
         ↓
┌─────────────────────────────────────────────────────────────┐
│  FINAL: All results copied to results/                      │
│  - results/grids/                                           │
│  - results/metrics/                                         │
│  - results/maps/                                            │
│  - results/summary.csv                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## How Containers Connect (The Key!)

### In nextflow.config:

```groovy
process {
    // This tells Nextflow: use spatial-analysis container for these processes
    withName: 'splitDistricts|generateGrids|extractPopulation|...' {
        container = 'spatial-analysis:latest'
    }

    withName: 'setupOSRM' {
        container = 'osrm/osrm-backend:latest'
    }
}

docker {
    enabled = true  // Enable Docker execution
}
```

### In spatial_access_workflow.nf:

```groovy
process generateGrids {
    container 'spatial-analysis:latest'  // ← Specifies which container

    input:
    path district_file

    script:
    """
    python ${projectDir}/scripts/02_generate_grids.py \
        ${district_file} \
        output.geojson \
        8
    """
}
```

**What happens when this process runs:**

1. Nextflow sees: "Need to run generateGrids process"
2. Checks: "Container = spatial-analysis:latest"
3. Docker: "Pull/use spatial-analysis:latest image"
4. Docker: "Create container from image"
5. Docker: "Mount input files into container"
6. Docker: "Mount scripts/ directory into container"
7. Container: "Run Python script with geopandas, h3, etc."
8. Container: "Write output.geojson"
9. Docker: "Copy output from container to work directory"
10. Docker: "Destroy container"
11. Nextflow: "Process complete! Move to next process"

---

## Data Flow Through Containers

```
Your Computer:
data/
├── boundaries/
├── roads/
├── facilities/
└── population/
        ↓ (mounted as read-only)

┌──────────────────────────────────────┐
│  INSIDE CONTAINER                    │
│  (spatial-analysis:latest)           │
│                                      │
│  /workspace/  ← Working directory    │
│  - Input files mounted here          │
│  - Python environment available:     │
│    • geopandas                       │
│    • h3                              │
│    • rasterio                        │
│    • matplotlib                      │
│                                      │
│  Script executes:                    │
│  python script.py input.shp output   │
│                                      │
│  Writes: output.geojson              │
└──────────────────────────────────────┘
        ↓ (output copied out)

Your Computer:
work/abc123/output.geojson
        ↓ (published to results)
results/grids/District_A_grids.geojson
```

---

## Why Containers Matter (For Your Demo)

### WITHOUT Containers:
```
User's Computer:
- Python 3.9? 3.11? 3.12?
- geopandas installed? Which version?
- Missing GDAL? Different version?
- Conda? pip? virtualenv?
- ❌ "Works on my machine!"
```

### WITH Containers:
```
Any Computer:
- Docker pulls: spatial-analysis:latest
- ✅ Exact Python 3.11
- ✅ Exact geopandas 0.14.1
- ✅ Exact GDAL version
- ✅ Same environment everywhere!
```

---

## Live Demo Flow for Workshop

### 1. Show the Dockerfile

```bash
cat Dockerfile.spatial
```

**Explain:**
- "This defines our computational environment"
- "FROM python:3.11 = base image"
- "RUN pip install = our dependencies"
- "Everyone gets identical environment"

### 2. Build the Container

```bash
./build_containers.sh
```

**Show:**
```bash
docker images | grep spatial-analysis
```

**Output:**
```
spatial-analysis  latest  abc123def456  5 minutes ago  1.2GB
```

**Explain:** "This is our packaged environment, ready to use"

### 3. Show How Nextflow Uses It

```bash
# Show nextflow.config
grep -A 5 "withName.*generateGrids" nextflow.config
```

**Explain:**
- "Nextflow sees this process needs spatial-analysis container"
- "Automatically launches Docker container"
- "Runs script inside isolated environment"
- "Saves output and destroys container"

### 4. Run the Workflow

```bash
nextflow run spatial_access_workflow.nf \
  --osm_pbf data/roads/togo-latest.osm.pbf \
  --districts_shp data/boundaries/geoBoundaries-TGO-ADM2.shp \
  --facilities_csv data/facilities/Togo_Health_Facilities_wgs84.csv \
  --population_tif data/population/tgo_pop_2025_CN_100m_R2025A_v1.tif \
  --outdir results
```

**While running, show:**
```bash
# In another terminal
docker ps  # Show running containers
```

**Output:**
```
CONTAINER ID   IMAGE                    COMMAND
abc123         spatial-analysis:latest  "/bin/bash -c 'python...'"
```

**Explain:** "See! Nextflow launched our container to run the process"

### 5. Show Results

```bash
ls -lh results/
ls -lh results/metrics/
cat results/summary.csv
```

---

## The Complete Picture

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR FILES                                                 │
│  ├── Dockerfile.spatial (defines environment)               │
│  ├── spatial_access_workflow.nf (defines processes)         │
│  ├── nextflow.config (links processes to containers)        │
│  └── scripts/*.py (analysis code)                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  DOCKER BUILD                                               │
│  Dockerfile.spatial → spatial-analysis:latest container     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  NEXTFLOW EXECUTION                                         │
│  1. Reads workflow definition                               │
│  2. Reads config (sees container = spatial-analysis:latest) │
│  3. For each process:                                       │
│     a. Launch Docker container                              │
│     b. Mount input data                                     │
│     c. Execute script inside container                      │
│     d. Save output                                          │
│     e. Destroy container                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  RESULTS                                                    │
│  ├── Grids with accessibility data (GeoJSON)               │
│  ├── Metrics per facility (CSV)                            │
│  ├── Maps (PNG)                                            │
│  └── Summary report (CSV)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Points for Workshop

1. **Container = Packaged Environment**
   - Dockerfile defines it
   - Docker builds it
   - Everyone uses identical environment

2. **Nextflow = Workflow Orchestrator**
   - Defines analysis steps (processes)
   - Decides execution order
   - Launches containers automatically
   - Handles data flow between steps

3. **Connection = nextflow.config**
   - Links each process to its container
   - `container = 'spatial-analysis:latest'`
   - Nextflow reads this, launches container

4. **Reproducibility**
   - Same Dockerfile → Same container
   - Same container → Same results
   - Any computer with Docker → Works!

---

## Troubleshooting for Demo

**If container not found:**
```bash
docker images | grep spatial-analysis
# If missing: ./build_containers.sh
```

**If Nextflow can't find Docker:**
```bash
docker ps  # Test Docker works
# Edit nextflow.config: docker.enabled = true
```

**Show work directory:**
```bash
ls work/  # Show Nextflow's execution directory
ls work/*/  # Show intermediate files
```

---

## Summary: The Connection

1. **Dockerfile** → Builds → **Container Image**
2. **Container Image** ← Referenced by ← **nextflow.config**
3. **Nextflow.config** + **Workflow.nf** → Executed by → **Nextflow**
4. **Nextflow** → Launches → **Docker Containers**
5. **Docker Containers** → Run → **Your Scripts**
6. **Your Scripts** → Process → **Your Data**
7. **Results** → Saved to → **results/**

**That's how it all connects!**

The workflow file defines WHAT to do.
The config file defines WHERE to do it (which container).
Docker provides the HOW (isolated, reproducible environment).
Nextflow orchestrates EVERYTHING.

---

Your data is now organized intuitively, and you understand the complete flow! 🎯