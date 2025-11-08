#!/bin/bash
# 
# Documentation Build Script for RPM Post-Install Hooks.
# Creates a temporary source structure, runs the generator, and builds the docs.
# 
# Usage: build_docs.sh <CLEAN_SOURCE_DIR> <DOCS_BUILD_DIR>
# 
# CLEAN_SOURCE_DIR: The path to the directory containing all source files (e.g., 'source' or '/path/to/source')
# DOCS_BUILD_DIR:   Destination for the final HTML output (e.g., 'docs-output' or '/var/www/html/docs')

CLEAN_SOURCE_DIR=$1
DOCS_BUILD_DIR=$2

if [ -z "$CLEAN_SOURCE_DIR" ] || [ -z "$DOCS_BUILD_DIR" ]; then
    echo "ERROR: Missing clean source directory or build output directory."
    echo "Usage: build_docs.sh <CLEAN_SOURCE_DIR> <DOCS_BUILD_DIR>"
    exit 1
fi

# Store the path where the script was executed from for reliable cleanup
EXEC_ROOT=$(pwd)

# Define the location for the temporary source structure, adjacent to the clean source.
# Example: If CLEAN_SOURCE_DIR is 'source', TEMP_SOURCE_DIR will be 'source_temp'.
TEMP_SOURCE_DIR="${CLEAN_SOURCE_DIR}_temp"

# --- 1. Setup Temporary Source Structure ---

echo "--- 1. Setting up temporary source folder ---"

# 1. Clean up any previous temporary directory
rm -rf "$TEMP_SOURCE_DIR"

# 2. Create the temporary directory
mkdir -p "$TEMP_SOURCE_DIR"

# 3. Copy the CONTENTS of the clean source directory into the temporary directory.
# This copies everything (chapters, generator.py, conf.py, etc.) into 'source_temp/'.
cp -r "${CLEAN_SOURCE_DIR}/." "$TEMP_SOURCE_DIR"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to copy clean source files from '$CLEAN_SOURCE_DIR' to temp directory."
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

# --- 2. Generate Dynamic Indices ---

echo "--- 2. Generating TOCTREE indices in temp folder ---"

# Navigate into the temporary source folder. 
# All subsequent paths are relative to this folder.
cd "$TEMP_SOURCE_DIR" || { echo "ERROR: Cannot change to temp source directory '$TEMP_SOURCE_DIR'."; exit 1; }

# Execute the generator. Since we are inside the new source folder, we pass '--root-dir .'
python3 generator.py --root-dir .

if [ $? -ne 0 ]; then
    echo "ERROR: Dynamic chapter generation failed in temp structure."
    # Important: Cleanup on failure
    cd "$EXEC_ROOT"
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

# --- 3. Run Sphinx Build ---

echo "--- 3. Running Sphinx Build from temporary source ---"

# We use the explicit sphinx-build command.
# The source directory is '.' (since we cd'd into the temp folder)
# The output directory is the second argument, resolved relative to EXEC_ROOT.
sphinx-build -b html . "$EXEC_ROOT/$DOCS_BUILD_DIR"

if [ $? -ne 0 ]; then
    echo "ERROR: Sphinx build failed. Check logs."
    # Important: Cleanup on failure
    cd "$EXEC_ROOT"
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

# --- 4. Cleanup ---

echo "--- 4. Cleaning up temporary source folder ---"

# Navigate back to the original root before removing the temp directory
cd "$EXEC_ROOT"

# Remove the entire temporary source directory
rm -rf "$TEMP_SOURCE_DIR"

echo "✅ Documentation successfully built and available in $DOCS_BUILD_DIR. Original source '$CLEAN_SOURCE_DIR' remains clean."