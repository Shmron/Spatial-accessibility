#!/bin/bash
# Script to prepare OSRM routing network from OSM PBF file

set -e

PBF_FILE=$1
OUTPUT_DIR=${2:-osrm_data}

if [ -z "$PBF_FILE" ]; then
    echo "Usage: $0 <pbf_file> [output_dir]"
    exit 1
fi

echo "Setting up OSRM routing network..."
echo "Input PBF: $PBF_FILE"
echo "Output directory: $OUTPUT_DIR"

mkdir -p $OUTPUT_DIR

# Extract the network
echo "Step 1/3: Extracting network..."
osrm-extract -p /opt/car.lua "$PBF_FILE" -o "$OUTPUT_DIR/network.osrm"

# Partition the network
echo "Step 2/3: Partitioning network..."
osrm-partition "$OUTPUT_DIR/network.osrm"

# Customize the network
echo "Step 3/3: Customizing network..."
osrm-customize "$OUTPUT_DIR/network.osrm"

echo "OSRM setup complete! Files in $OUTPUT_DIR/"
ls -lh $OUTPUT_DIR/