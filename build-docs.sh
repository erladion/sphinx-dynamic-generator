#!/bin/bash
# 
# Documentation Build Script for RPM Post-Install Hooks.
# Creates a temporary source structure, runs the generator, and builds the docs.
# 
# Usage: build_docs.sh <CLEAN_SOURCE_DIR> <DOCS_BUILD_DIR>
# 
# CLEAN_SOURCE_DIR: The path to the directory containing all source files (e.g., 'source')
# DOCS_BUILD_DIR:   Destination for the final output (e.g., 'docs-output')

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
TEMP_SOURCE_DIR="${CLEAN_SOURCE_DIR}_temp" 

# --- 1. Setup Temporary Source Structure ---

echo "--- Step 1/4 Setting up temporary source folder ---"

# 1. Clean up any previous temporary directory
rm -rf "$TEMP_SOURCE_DIR"

# 2. Create the temporary directory
mkdir -p "$TEMP_SOURCE_DIR"

# 3. Copy the CONTENTS of the clean source directory into the temporary directory.
# Step 3a: Copy all non-hidden files and directories (like chapters/ and _static/)
cp -r "${CLEAN_SOURCE_DIR}/"* "$TEMP_SOURCE_DIR"

if [ $? -ne 0 ]; then
    echo "❌ CRITICAL ERROR: Failed to copy non-hidden files from '$CLEAN_SOURCE_DIR'. Stopping build."
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

# Step 3b: Copy all dot-files/directories (like .chapterconf files) excluding '.' and '..'
# We pipe errors to /dev/null to hide 'No such file or directory' if no dot-files exist.
cp -r "${CLEAN_SOURCE_DIR}"/.[!.]* "$TEMP_SOURCE_DIR" 2>/dev/null

# IMPORTANT FIX: Ignore the exit status of the optional dot-file copy by resetting $? to 0.
# The previous logic incorrectly caught the benign error from this command.
true # Always sets the exit code to 0

# --- 2. Generate Dynamic Indices ---

echo "--- Step 2/4 Generating TOCTREE indices in temp folder ---"

# Navigate into the temporary source folder. 
cd "$TEMP_SOURCE_DIR" || { echo "ERROR: Cannot change to temp source directory '$TEMP_SOURCE_DIR'."; exit 1; }

# Execute the generator. 
python3 generator.py --root-dir .

if [ $? -ne 0 ]; then
    echo "ERROR: Dynamic chapter generation failed in temp structure."
    cd "$EXEC_ROOT"
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

echo "--- Step 3/4 Running Sphinx Builds ---"
# --- 3. Run Sphinx Builds (HTML and PDF) ---

# 3a. Run HTML Build
echo "--- 3a. Running Sphinx HTML Build ---"
HTML_OUTPUT_DIR="$EXEC_ROOT/$DOCS_BUILD_DIR/html"
mkdir -p "$HTML_OUTPUT_DIR"
sphinx-build -b html . "$HTML_OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo "ERROR: Sphinx HTML build failed."
    cd "$EXEC_ROOT"
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi


# 3b. Run PDF Build (LaTeX)
echo "--- 3b. Running Sphinx PDF Build ---"
LATEX_SOURCE_DIR="$EXEC_ROOT/$DOCS_BUILD_DIR/latex"
mkdir -p "$LATEX_SOURCE_DIR"

# Step 1: Generate LaTeX source files
echo "   -> Generating LaTeX source files..."
sphinx-build -b latex . "$LATEX_SOURCE_DIR"

if [ $? -eq 0 ]; then
    
    # --- DYNAMICALLY READ LOGO FILENAME FROM conf.py ---
    # 1. Extract the full path (e.g., '_static/logo.png') from conf.py
    # This works because the script is currently running inside $TEMP_SOURCE_DIR.
    LOGO_PATH=$(grep 'html_logo' conf.py | sed -n 's/.*html_logo = "\(.*\)".*/\1/p')

    if [ -z "$LOGO_PATH" ]; then
        echo "WARNING: Could not find 'html_logo' setting in conf.py. Skipping PDF logo copy."
    else
        # 2. Extract just the filename (e.g., 'logo.png') using basename
        LOGO_FILENAME=$(basename "$LOGO_PATH")
        
        # 3. Define the explicit source path (relative to CWD) and full destination path
        LOGO_SOURCE_PATH="./$LOGO_PATH" # E.g., ./_static/logo.png
        LOGO_DEST_PATH="$LATEX_SOURCE_DIR/$LOGO_FILENAME" # E.g., /path/to/docs-output/latex/logo.png

        echo "   -> Attempting to copy logo for PDF (Filename: $LOGO_FILENAME)..."
        echo "   -> Source path: $LOGO_SOURCE_PATH"
        
        if [ -f "$LOGO_SOURCE_PATH" ]; then
            echo "   -> CHECK: Logo file found in temp source."
            # Copy file to the LATEX_SOURCE_DIR where the makefile expects it to be
            cp "$LOGO_SOURCE_PATH" "$LATEX_SOURCE_DIR/"
            
            if [ -f "$LOGO_DEST_PATH" ]; then
                echo "   -> CHECK: Logo successfully copied to LaTeX output directory."
            else
                echo "❌ ERROR: Copy failed. Logo not found at destination after copy attempt."
            fi
        else
            echo "❌ FATAL ERROR: Logo file '$LOGO_SOURCE_PATH' not found in temporary source. Check conf.py path and file existence."
            cd "$EXEC_ROOT"
            rm -rf "$TEMP_SOURCE_DIR"
            exit 1
        fi
    fi
    # --- END OF DYNAMIC LOGO COPY ---
    
    # Step 2: Compile PDF from LaTeX source
    echo "   -> Compiling PDF (requires TeX Live/MiKTeX to be installed)..."
    cd "$LATEX_SOURCE_DIR" || { echo "ERROR: Cannot change to LaTeX source directory '$LATEX_SOURCE_DIR'."; exit 1; }
    
    # Use make all-pdf command provided by the Sphinx LaTeX Makefile
    make all-pdf
    
    # Navigate back to temp source root to ensure cleanup runs correctly
    cd "$EXEC_ROOT/$TEMP_SOURCE_DIR"
    
    if [ $? -ne 0 ]; then
        echo "WARNING: LaTeX to PDF compilation failed. PDF output will be unavailable."
    else
        echo "   -> PDF compiled successfully."
    fi
else
    echo "WARNING: Sphinx LaTeX source generation failed. PDF output will be unavailable."
fi


# --- 4. Cleanup ---
echo "--- Step 4/4 Cleaning up temporary source folder ---"

# Navigate back to the original root before removing the temp directory
cd "$EXEC_ROOT"

# Remove the entire temporary source directory
rm -rf "$TEMP_SOURCE_DIR"

echo "✅ Documentation build complete. HTML available in $DOCS_BUILD_DIR/html. Original source '$CLEAN_SOURCE_DIR' remains clean."