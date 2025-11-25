#!/bin/bash
# Build Docker container for spatial accessibility workflow

set -e  # Exit on error

echo "=========================================="
echo "Building Spatial Analysis Container"
echo "=========================================="
echo ""

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker daemon is running
if ! docker info &> /dev/null; then
    echo "ERROR: Docker daemon not running. Please start Docker."
    exit 1
fi

echo "Building container image..."
echo "This may take 5-10 minutes on first build..."
echo ""

docker build -f Dockerfile.spatial -t spatial-analysis:latest .

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Container image: spatial-analysis:latest"
echo ""
echo "To verify installation:"
echo "  docker run --rm spatial-analysis:latest python -c 'import geopandas, h3, rasterio; print(\"All libraries installed!\")'"
echo ""
echo "Next steps:"
echo "  1. Validate your data: python scripts/00_validate_data.py"
echo "  2. Run workflow: nextflow run spatial_access_workflow.nf --help"
echo ""