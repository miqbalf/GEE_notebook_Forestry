# 🌳 GEE Notebooks for Forestry Analysis

A comprehensive collection of Google Earth Engine (GEE) Python API notebooks and utilities for forestry analysis, land cover classification, and satellite verification for tree planting projects and carbon project development (ARR - Afforestation, Reforestation, and Revegetation).

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Notebooks](#notebooks)
- [Configuration](#configuration)
- [ArcGIS Pro Integration](#arcgis-pro-integration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

This library provides a complete toolkit for forestry analysis and satellite verification using Google Earth Engine, designed for **project developers** in carbon projects including:

- **Multi-satellite data processing** (Planet, Sentinel-2, Landsat)
- **Land cover classification** using machine learning
- **Forest Canopy Density (FCD)** analysis
- **Historical tree loss** assessment using Hansen data
- **Object-Based Image Analysis (OBIA)** segmentation
- **Interactive web mapping** with Geemap
- **Training data validation** and processing
- **Satellite verification** for tree planting projects
- **Carbon project development** support (ARR projects)

## ✨ Features

- 🛰️ **Multi-satellite support**: Planet, Sentinel-2, Landsat with cloud masking
- 🗺️ **Interactive mapping**: Geemap integration for web-based visualization
- 🌱 **Advanced vegetation analysis**: Forest Canopy Density (FCD), AVI, BSI, SI, PCA calculations
- 🤖 **Machine learning classification**: GBM, Random Forest, SVM algorithms
- 📊 **Object-based segmentation**: Super-pixel analysis and OBIA
- 📈 **Historical analysis**: Hansen Global Forest Change integration
- 🔧 **Training data management**: Validation and processing workflows
- 💾 **Flexible export**: Multiple output formats and cloud storage

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Google Earth Engine account
- ArcGIS Pro (for full functionality)
- Jupyter Notebook/Lab

### Method 1: Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/GEE_notebook_Forestry.git
cd GEE_notebook_Forestry

# Create virtual environment
python -m venv gee_forestry_env

# Activate environment
# On Windows:
gee_forestry_env\Scripts\activate
# On macOS/Linux:
source gee_forestry_env/bin/activate

# Install requirements
pip install -r requirements.txt

# Authenticate with Google Earth Engine
earthengine authenticate
```

### Method 2: Conda Installation

```bash
# Create conda environment
conda create -n gee_forestry python=3.9
conda activate gee_forestry

# Install conda packages
conda install -c conda-forge geopandas folium jupyter

# Install remaining packages
pip install -r requirements.txt

# Authenticate with Google Earth Engine
earthengine authenticate
```

### Method 3: ArcGIS Pro Integration

For users with ArcGIS Pro, follow the detailed instructions in [`step_conda_arcgis_pro.txt`](step_conda_arcgis_pro.txt):

```bash
# Add ArcGIS Pro conda to PATH (Windows)
$env:PATH += ";C:\Program Files\ArcGIS\Pro\bin\Python\Scripts;C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3"

# Clone ArcGIS Pro environment
conda create --name gee_forestry --clone arcgispro-py3

# Activate and install
conda activate gee_forestry
pip install -r requirements.txt
```

## 🎯 Quick Start

### 1. Initialize Google Earth Engine

```python
import ee
import geemap

# Initialize Earth Engine with your project
ee.Initialize(project='your-gee-project-id')

# Create interactive map
Map = geemap.Map()
Map
```

### 2. Load Configuration

```python
import json
import os

# Load configuration
config_path = '00_input/balaban_conf.json'
with open(config_path, 'r') as file:
    config = json.load(file)

print('Configuration loaded:', config)
```

### 3. Initialize ArcGIS Pro Integration

```python
from osi.arcpy.main import ArcpyOps

# Initialize ArcGIS Pro operations
arc_ops = ArcpyOps(project_path_arcgis="CURRENT", 
                   map_name_arcgis="eligibility_check_prospective_tpps")

# Add AOI layer
AOI_path = config['AOI_path']
AOI_layer = arc_ops.select_adding_layer(AOI_path)
```

### 4. Process Satellite Data

```python
from osi.image_collection.main import ImageCollection

# Initialize image collection
classInputCollection = ImageCollection(
    I_satellite=config['I_satellite'],
    AOI=AOI,
    date_start_end=config['date_start_end'],
    cloud_cover_threshold=config['cloud_cover_threshold'],
    region=config['region']
)

# Create image mosaic
image_mosaick = classInputCollection.image_mosaick()
```

## 🌐 Non-ArcGIS Workflow (Web-based)

### 1. Initialize Interactive Map

```python
import ee
import geemap
import osi
import pandas as pd
import geopandas as gpd
import os
import json

# Initialize Earth Engine
ee.Initialize(project='your-gee-project-id')

# Create interactive map
Map = geemap.Map(center=(-3, 115), zoom=4)
Map.centerObject(AOI, 10)
```

### 2. Configuration Setup

```python
# Define project configuration
dict_config = {
    "project_name": "oluba_westnile",
    "date_analyzed": '20250117',
    "I_satellite": "Sentinel",
    "AOI_path": "path/to/aoi.shp",
    "OID_field_name": "Id",
    "algo_ml_selected": "gbm",
    "date_start_end": ["2024-6-1", "2024-6-30"],
    "super_pixel_size": 3,
    "region": "africa",
    "cloud_cover_threshold": 40,
    "crs_input": "EPSG:4326",
    "tree_cover_forest": 10,
    "high_forest": 65,
    "yrf_forest": 55,
    "shrub_grass": 35,
    "open_land": 30,
    "create_training_gee": True,
    "num_training_to_create": 8
}

# Save configuration
config_json_loc = f"{dict_config['date_analyzed']}_{dict_config['project_name']}_conf.json"
with open(config_json_loc, 'w') as json_file:
    json.dump(dict_config, json_file, indent=4)
```

### 3. Data Validation

```python
from osi.utils.main import validate_aoi

# Load and validate AOI
AOI = geemap.shp_to_ee(config['AOI_path'])
validate_aoi(AOI, ee, config['OID_field_name'])

# Load AOI data
df_AOI = gpd.read_file(config['AOI_path'])
print(f"Field '{config['OID_field_name']}' found. Proceeding with operations...")

# Create AOI image for masking
AOI_img = AOI.filter(ee.Filter.notNull([config['OID_field_name']])).reduceToImage(
    properties=[config['OID_field_name']],
    reducer=ee.Reducer.first()
)
```

### 4. Interactive Visualization

```python
# Add satellite mosaic to map
if config['I_satellite'] == 'Planet':
    Map.addLayer(image_mosaick, 
                {"bands": ["red", "green", "blue"], "min": 0, "max": 0.6, "gamma": 1.5}, 
                f'{config["I_satellite"]} mosaicked - {start_date}-{end_date}')
else:
    Map.addLayer(image_mosaick, 
                {'bands': ['swir2', 'nir', 'red'], 'min': 0, 'max': 0.6, 'gamma': 1.5}, 
                f'{config["I_satellite"]} mosaicked - {start_date}-{end_date}')

# Display interactive map
Map
```

### 5. Forest Canopy Density Analysis

```python
from osi.fcd.main_fcd import FCDCalc

# Calculate Forest Canopy Density
class_FCD_run = FCDCalc(config).fcd_calc()
FCD1_1 = class_FCD_run['FCD1_1']
FCD2_1 = class_FCD_run['FCD2_1']

# Add FCD layers to map
Map.addLayer(FCD1_1, 
            {'min': 0, 'max': 80, 'palette': ['ff4c16', 'ffd96c', '39a71d']}, 
            f'FCD1_1_{project_name}')

Map.addLayer(FCD2_1, 
            {'min': 0, 'max': 80, 'palette': ['ff4c16', 'ffd96c', '39a71d']}, 
            f'FCD2_1_{project_name}')
```

### 6. Training Data Creation (Optional)

```python
if config['create_training_gee']:
    # Create training samples interactively
    # This allows users to create training points directly on the map
    training_points = Map.user_rois
    
    # Convert to GeoDataFrame and save
    training_gdf = geemap.ee_to_gdf(training_points)
    training_gdf.to_file(config['location_sample_created'])
```

## 📚 Notebooks

### Core Analysis Notebooks

- **`arcgispro_sa_gee_balaban.ipynb`** - Complete ArcGIS Pro + GEE integration workflow
- **`example_usage.ipynb`** - Non-ArcGIS web-based workflow with interactive mapping
- **`sentinel2_processing.ipynb`** - Sentinel-2 data processing pipeline
- **`planet_analysis.ipynb`** - Planet satellite data analysis
- **`landcover_classification.ipynb`** - Machine learning land cover classification
- **`forest_canopy_density.ipynb`** - FCD and historical analysis

### Utility Notebooks

- **`training_data_validation.ipynb`** - Training point validation and processing
- **`arcgis_integration.ipynb`** - ArcGIS Pro layer management
- **`export_workflows.ipynb`** - Data export and visualization

## 🛠️ Core Modules

### OSI (Open Source Intelligence) Framework

```python
# Image Collection Management
from osi.image_collection.main import ImageCollection

# Spectral Analysis
from osi.spectral_indices.spectral_analysis import SpectralAnalysis

# Forest Canopy Density
from osi.fcd.main_fcd import FCDCalc

# Machine Learning Classification
from osi.ml.main import LandcoverML

# ArcGIS Pro Integration
from osi.arcpy.main import ArcpyOps

# Object-Based Analysis
from osi.obia.main import OBIASegmentation

# Historical Analysis
from osi.hansen.historical_loss import HansenHistorical
```

## ⚙️ Configuration

### Configuration File Structure

Create a project configuration file (e.g., `oluba_westnile_conf.json`):

```json
{
    "project_name": "oluba_westnile",
    "date_analyzed": "20250117",
    "I_satellite": "Sentinel",
    "AOI_path": "path/to/your/aoi.shp",
    "OID_field_name": "Id",
    "input_training": "path/to/training_points.shp",
    "algo_ml_selected": "gbm",
    "date_start_end": ["2024-6-1", "2024-6-30"],
    "super_pixel_size": 3,
    "region": "africa",
    "cloud_cover_threshold": 40,
    "crs_input": "EPSG:4326",
    "tree_cover_forest": 10,
    "high_forest": 65,
    "yrf_forest": 55,
    "shrub_grass": 35,
    "open_land": 30,
    "create_training_gee": true,
    "num_training_to_create": 8
}
```

### Land Cover Classification Schema

```python
palette_class_segment = {
    '1': '#83ff5a',   # forest_trees
    '2': '#ffe3b3',   # shrubland
    '3': '#ffff33',   # grassland
    '4': '#f89696',   # openland
    '5': '#1900ff',   # waterbody_wet_area
    '6': '#e6e6fa',   # plantation
    '7': '#FFFFFF',   # infrastructure
    '8': '#4B0082',   # oil_palm
    '9': '#8B4513',   # cropland
    '10': '#87CEEB',  # waterbody
    '11': '#2F4F4F',  # wetlands
    '12': '#ADFF2F',  # forest_trees_regrowth
    '13': '#8B0000',  # historical_treeloss_10years
    '14': '#DAA520'   # paddy_irrigated
}
```

## 🗺️ ArcGIS Pro Integration

### Layer Management

```python
# Add layers to ArcGIS Pro map
arc_ops = ArcpyOps(project_path_arcgis="CURRENT")

# Add satellite imagery
image_layer = arc_ops.adding_ee_to_arcgisPro(
    image_mosaick, 
    vis_params, 
    layer_name
)

# Add classification results
classification_layer = arc_ops.adding_ee_to_arcgisPro(
    classified_image,
    {'min': 1, 'max': 14, 'palette': list(palette_class_segment.values())},
    'Land_Cover_Classification'
)
```

### Training Data Validation

```python
# Validate training points
from osi.utils.main import validate_aoi

# Check AOI
validate_aoi(AOI, ee, config['OID_field_name'])

# Process training data
input_training = arc_ops.select_adding_layer(config['input_training'])
training_ee = geemap.shp_to_ee(config['input_training'])
```

## 🔧 Advanced Features

### Forest Canopy Density (FCD)

```python
# Calculate Forest Canopy Density using PCA
class_FCD_run = FCDCalc(config).fcd_calc()
FCD1_1 = class_FCD_run['FCD1_1']
FCD2_1 = class_FCD_run['FCD2_1']

# Add to ArcGIS Pro
arc_ops.adding_ee_to_arcgisPro(
    FCD1_1, 
    {'min': 0, 'max': 80, 'palette': ['ff4c16', 'ffd96c', '39a71d']},
    f'FCD1_1_{project_name}'
)
```

### Historical Tree Loss Analysis

```python
# Hansen Global Forest Change
hansen_class = HansenHistorical(config)
run_hansen = hansen_class.initiate_tcl()

treeLossYear = run_hansen['treeLossYear']
ForestArea2000Hansen = run_hansen['ForestArea2000Hansen']

# Add historical analysis
arc_ops.adding_ee_to_arcgisPro(
    treeLossYear.randomVisualizer(), 
    {},
    'treeLossYear'
)
```

### Machine Learning Classification

```python
# Initialize ML classification
ml_class = LandcoverML(
    image=image_mosaick,
    training_data=training_ee,
    algorithm=config['algo_ml_selected']
)

# Train and classify
classified_image = ml_class.train_and_classify()

# Add to map
arc_ops.adding_ee_to_arcgisPro(
    classified_image,
    classification_vis_params,
    'ML_Classification'
)
```

## 🐛 Troubleshooting

### Common Issues

#### 1. ArcGIS Pro Integration
```python
# Check if layer exists in map
if os.path.normpath(config['AOI_path']) not in arc_ops.list_source_layers_in_map:
    print("Layer not found, adding to map...")
    arc_ops.select_adding_layer(config['AOI_path'])
```

#### 2. Training Data Validation
```python
# Validate field names
fields = [field.name for field in arcpy.ListFields(input_training)]
if config['OID_field_name'] not in fields:
    raise ValueError(f"Field '{config['OID_field_name']}' not found")
```

#### 3. GEE Authentication
```bash
# Re-authenticate
earthengine authenticate

# Check project access
earthengine authenticate --list
```

#### 4. Certificate Issues (ArcGIS Pro)
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r requirements.txt
```

## 📊 Example Workflows

### Complete Tree Planting Project Analysis Workflow

```python
# 1. Initialize (ArcGIS Pro workflow)
arc_ops = ArcpyOps(project_path_arcgis="CURRENT")
config = load_config('project_conf.json')

# 2. Load and validate data
AOI = geemap.shp_to_ee(config['AOI_path'])
validate_aoi(AOI, ee, config['OID_field_name'])

# 3. Process satellite data
classInputCollection = ImageCollection(config)
image_mosaick = classInputCollection.image_mosaick()

# 4. Calculate vegetation indices
classImageSpectral = SpectralAnalysis(image_mosaick, config)

# 5. Forest canopy density analysis
class_FCD_run = FCDCalc(config).fcd_calc()

# 6. Historical analysis
hansen_class = HansenHistorical(config)
historical_data = hansen_class.initiate_tcl()

# 7. Machine learning classification
ml_class = LandcoverML(image_mosaick, training_data, config['algo_ml_selected'])
classified = ml_class.train_and_classify()

# 8. Add all layers to ArcGIS Pro
arc_ops.adding_ee_to_arcgisPro(image_mosaick, vis_params, 'Satellite_Mosaic')
arc_ops.adding_ee_to_arcgisPro(classified, class_vis_params, 'Land_Cover')
```

### Web-based Interactive Workflow

```python
# 1. Initialize interactive map
Map = geemap.Map(center=(-3, 115), zoom=4)
ee.Initialize(project='your-gee-project-id')

# 2. Load configuration
config = load_config('project_conf.json')
AOI = geemap.shp_to_ee(config['AOI_path'])

# 3. Process satellite data
classInputCollection = ImageCollection(config)
image_mosaick = classInputCollection.image_mosaick()

# 4. Add to interactive map
Map.addLayer(image_mosaick, vis_params, 'Satellite_Mosaic')

# 5. Forest canopy density analysis
class_FCD_run = FCDCalc(config).fcd_calc()
Map.addLayer(class_FCD_run['FCD1_1'], fcd_vis_params, 'Forest_Canopy_Density')

# 6. Display interactive map
Map
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black .
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Earth Engine](https://earthengine.google.com/) for providing the platform
- [Geemap](https://geemap.org/) for excellent GEE Python integration
- [ArcGIS Pro](https://www.esri.com/en-us/arcgis/products/arcgis-pro/) for GIS integration
- The open-source geospatial community
- Project developers in carbon and forestry sectors

## 📞 Support

- 📧 Email: muh.firdausiqbal@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/GEE_notebook_Forestry/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/GEE_notebook_Forestry/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/GEE_notebook_Forestry/discussions)

---

**Made with ❤️ for project developers in carbon and forestry analysis**