
# How to Share This Workflow

## What to Share (Push to GitHub)

### ✅ MUST Include:

```
nf-tutorial/
├── spatial_access_workflow.nf    ← Main workflow
├── nextflow.config                ← Configuration
├── Dockerfile.spatial             ← Container definition
├── build_containers.sh            ← Build helper
├── .gitignore                     ← Excludes data/results
│
├── scripts/                       ← ALL scripts (essential!)
│   ├── 00_validate_data.py
│   ├── 00b_convert_coordinates.py
│   ├── 01_setup_osrm.sh
│   ├── 02_generate_grids.py
│   ├── 03_extract_population.py
│   ├── 04_calculate_accessibility.py
│   ├── 05_compute_metrics.py
│   └── 06_create_visualization.py
│
├── data/                          ← Structure only
│   ├── README.md                  ← Documents data sources
│   ├── boundaries/                ← Empty folder
│   ├── roads/                     ← Empty folder
│   ├── facilities/                ← Empty folder
│   └── population/                ← Empty folder
│
└── docs/
    ├── README.md                  ← User guide
    ├── WORKSHOP_GUIDE.md          ← Presentation
    └── HOW_IT_WORKS.md            ← Technical explanation
```

### ❌ DO NOT Include:

```
✗ data/*.pbf              # Large OSM files
✗ data/*.tif              # Large population rasters
✗ data/*.shp              # User-specific shapefiles
✗ data/*.csv              # User-specific facilities
✗ work/                   # Nextflow temp files
✗ results/                # Workflow outputs
✗ .nextflow/              # Nextflow cache
✗ Built Docker images     # Users build from Dockerfile
```

---

## How Users Get Started

### 1. Clone Your Repository

```bash
git clone https://github.com/yourusername/nf-tutorial.git
cd nf-tutorial
```

### 2. Install Requirements

```bash
# Install Nextflow
curl -s https://get.nextflow.io | bash
sudo mv nextflow /usr/local/bin/

# Ensure Docker is installed
docker --version
```

### 3. Build Container

```bash
./build_containers.sh
```

**This runs:**
```bash
docker build -f Dockerfile.spatial -t spatial-analysis:latest .
```

**Creates:** `spatial-analysis:latest` container with all Python libraries

### 4. Add Their Data

```bash
data/
├── boundaries/         # User adds their shapefiles
├── roads/             # User downloads OSM PBF
├── facilities/        # User provides facility CSV
└── population/        # User downloads WorldPop TIF
```

### 5. Validate & Run

```bash
# Validate
python scripts/00_validate_data.py

# Run workflow
nextflow run spatial_access_workflow.nf \
  --osm_pbf data/roads/region.osm.pbf \
  --districts_shp data/boundaries/districts.shp \
  --facilities_csv data/facilities/facilities.csv \
  --population_tif data/population/population.tif \
  --outdir results
```

---

## Sharing Options

### Option 1: GitHub Only (RECOMMENDED)

**What you push:**
- Dockerfile.spatial
- All workflow files
- All scripts
- Documentation
- Empty data folders

**Users build container themselves:**
```bash
git clone your-repo
./build_containers.sh
```

**Pros:**
- ✅ Simple - no Docker Hub needed
- ✅ Always up-to-date
- ✅ Users see what's in container

### Option 2: GitHub + Docker Hub

**If you want to share pre-built image:**

```bash
# Tag image with your Docker Hub username
docker tag spatial-analysis:latest yourusername/spatial-analysis:latest

# Push to Docker Hub
docker login
docker push yourusername/spatial-analysis:latest
```

**Update nextflow.config:**
```groovy
process {
    withName: 'generateGrids|extractPopulation|...' {
        container = 'yourusername/spatial-analysis:latest'
    }
}
```

**Users pull instead of building:**
```bash
docker pull yourusername/spatial-analysis:latest
nextflow run spatial_access_workflow.nf ...
```

**Pros:**
- ✅ Users don't need to build (faster start)
- ✅ Guaranteed same environment

**Cons:**
- ❌ Need Docker Hub account
- ❌ Need to push updates manually
- ❌ Image is ~1GB to download

---

## What Happens with Scripts?

### Scripts are MOUNTED, not BUILT INTO CONTAINER

**When Nextflow runs:**

```
1. Nextflow sees: process generateGrids
2. Config says: container = 'spatial-analysis:latest'
3. Docker starts container
4. Nextflow mounts: ${projectDir}/scripts/ → /workspace/scripts/
5. Container runs: python /workspace/scripts/02_generate_grids.py
6. Script uses libraries from container (h3, geopandas, etc.)
7. Output saved
8. Container destroyed
```

**Why this matters:**
- ✅ Scripts MUST be in repository
- ✅ Users can modify scripts without rebuilding container
- ✅ Container only has libraries, not your code

---

## For Your Workshop

### What to Demonstrate:

**1. Show what gets shared:**
```bash
# On GitHub
ls -R
# Users see: workflow, Dockerfile, scripts, docs
```

**2. Show what users build:**
```bash
./build_containers.sh
docker images | grep spatial-analysis
```

**3. Show scripts stay separate:**
```bash
# Scripts in repo
ls scripts/

# But used inside container
docker run --rm -v $(pwd):/workspace spatial-analysis:latest \
  ls /workspace/scripts/
```

---

## Quick Commands Reference

### Sharing (You):

```bash
# Initialize git (if not done)
git init
git add .
git commit -m "Spatial accessibility workflow"

# Push to GitHub
git remote add origin https://github.com/yourusername/nf-tutorial.git
git push -u origin main
```

### Using (Others):

```bash
# Clone
git clone https://github.com/yourusername/nf-tutorial.git
cd nf-tutorial

# Build container
./build_containers.sh

# Add data (following data/README.md instructions)
# ...

# Run
nextflow run spatial_access_workflow.nf --help
```

---

## Summary

**Share via Git:**
- ✅ Dockerfile (small text file)
- ✅ All scripts (your analysis code)
- ✅ Workflow files
- ✅ Documentation
- ❌ Not actual data (too large, user-specific)
- ❌ Not built images (users build from Dockerfile)

**Users do:**
1. Clone repo
2. Run `./build_containers.sh` (builds from Dockerfile)
3. Add their data
4. Run workflow

**Build script (`build_containers.sh`):**
- ✅ KEEP IT - it's helpful
- Just wraps: `docker build -f Dockerfile.spatial -t spatial-analysis:latest .`
- Makes it easier for users

**You DON'T need:**
- ❌ `docker run` (Nextflow does this)
- ❌ `docker-compose up` (not used here)
- ❌ Manual `docker push` (unless using Docker Hub)

---

Everything users need is in the repository! 🎯