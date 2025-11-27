#!/bin/bash
#
# Spatial Access to Health Facilities Workflow Runner
#
# This script runs the spatial accessibility analysis for Togo health facilities
# using data from /data directory
#

echo "========================================"
echo "Starting Spatial Access Analysis"
echo "========================================"

# Run the workflow with default /data paths
~/.local/bin/nextflow run spatial_access_workflow.nf

echo ""
echo "========================================"
echo "Workflow execution completed"
echo "Check the results/ directory for output"
echo "========================================"
