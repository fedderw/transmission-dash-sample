#!/bin/bash

# Set up the directory structure for the Dash app

# Root directory name (change if you want a different name)
ROOT_DIR="transmission-dash-sample"

# Create the root directory
mkdir -p $ROOT_DIR

# Create subdirectories
mkdir -p $ROOT_DIR/assets
mkdir -p $ROOT_DIR/components
mkdir -p $ROOT_DIR/data
mkdir -p $ROOT_DIR/callbacks
mkdir -p $ROOT_DIR/utils

# Create main app files
touch $ROOT_DIR/app.py
touch $ROOT_DIR/index.py

# Create assets files
touch $ROOT_DIR/assets/style.css
touch $ROOT_DIR/assets/logo.png

# Create component files
touch $ROOT_DIR/components/custom_map.py
touch $ROOT_DIR/components/data_table.py
touch $ROOT_DIR/components/gantt_chart.py

# Create data file (example)
touch $ROOT_DIR/data/dataset.csv

# Create callback files
touch $ROOT_DIR/callbacks/map_callbacks.py
touch $ROOT_DIR/callbacks/table_callbacks.py
touch $ROOT_DIR/callbacks/gantt_callbacks.py

# Create utility files
touch $ROOT_DIR/utils/data_loader.py
touch $ROOT_DIR/utils/helper_functions.py

# Create requirements file
touch $ROOT_DIR/requirements.txt

echo "Dash app directory structure created in $ROOT_DIR"
