#!/bin/bash

set -e

# Define a shared workspace and installation directory
WORKSPACE_DIR="$PWD"
INSTALL_DIR="$WORKSPACE_DIR/cyclonedds_install"
mkdir -p "$INSTALL_DIR"

echo "Creating miniconda directory..."
mkdir -p ~/miniconda3

echo "Downloading Miniconda..."
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh

echo "Installing Miniconda..."
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3

echo "Activating conda..."
# The recommended way to activate conda inside a bash script
source ~/miniconda3/etc/profile.d/conda.sh
conda activate base

# 1. Clone and build the core CycloneDDS (C library)
# Note: The C++ bindings require this to be installed first.
echo "Cloning and building CycloneDDS (Core C library)..."
cd "$WORKSPACE_DIR"
if [ ! -d "cyclonedds" ]; then
    git clone https://github.com/eclipse-cyclonedds/cyclonedds
fi
cd cyclonedds
mkdir -p build
cd build
cmake .. -DENABLE_TYPE_DISCOVERY=ON -DENABLE_TOPIC_DISCOVERY=ON -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR"
cmake --build . --parallel $(nproc)
cmake --install .

# 2. Clone and build the CycloneDDS C++ bindings
echo "Cloning and building CycloneDDS C++ bindings (cyclonedds-cxx)..."
cd "$WORKSPACE_DIR"
if [ ! -d "cyclonedds-cxx" ]; then
    git clone https://github.com/eclipse-cyclonedds/cyclonedds-cxx
fi
cd cyclonedds-cxx
mkdir -p build
cd build
# CMAKE_PREFIX_PATH tells the build where to find the core C library we just built
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" -DCMAKE_PREFIX_PATH="$INSTALL_DIR"
cmake --build . --parallel $(nproc)
cmake --install .

echo "Setting CYCLONEDDS_HOME environment variable..."
export CYCLONEDDS_HOME="$INSTALL_DIR"

# Add to bashrc if not already present
if ! grep -q "export CYCLONEDDS_HOME=" ~/.bashrc; then
    echo "export CYCLONEDDS_HOME=\"$INSTALL_DIR\"" >> ~/.bashrc
    echo "CYCLONEDDS_HOME added to ~/.bashrc"
fi

echo "Installing Python bindings..."
pip install git+https://github.com/eclipse-cyclonedds/cyclonedds-python

echo "Installing Python dependencies..."
pip install numpy pyyaml

echo "Setup complete!"
echo "Run 'source ~/.bashrc' or open a new terminal to load CYCLONEDDS_HOME."