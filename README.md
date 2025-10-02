# 🌍 GEE Notebooks for Forestry Analysis

A comprehensive collection of Google Earth Engine (GEE) Python API notebooks and utilities for forestry and land eligibility analysis using satellite imagery.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Notebooks](#notebooks)
- [Utilities](#utilities)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🌟 Overview

This library provides a complete toolkit for forestry analysis using Google Earth Engine, including:

- **Sentinel-2 satellite data processing**
- **Cloud masking and atmospheric correction**
- **Vegetation indices calculation (NDVI, EVI, SAVI, etc.)**
- **Land eligibility analysis**
- **Forest gain/loss detection**
- **Export to various formats (GeoTIFF, Zarr, etc.)**

## ✨ Features

- 🛰️ **Multi-satellite support**: Sentinel-2, Landsat, MODIS
- ☁️ **Advanced cloud masking**: Multiple algorithms and thresholds
- 🌱 **Vegetation analysis**: Comprehensive vegetation indices
- 📊 **Interactive visualization**: Folium and Geemap integration
- 💾 **Flexible export**: GeoTIFF, Zarr, Google Drive, Cloud Storage
- 🔧 **Modular design**: Reusable functions and classes
- 📈 **Performance optimized**: Server-side processing for large datasets

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Google Earth Engine account
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

# Initialize Earth Engine
ee.Initialize()

# Create interactive map
Map = geemap.Map()
Map
```

### 2. Load and Process Sentinel-2 Data

```python
# Load Sentinel-2 collection
s2 = ee.ImageCollection('COPERNICUS/S2_SR')

# Define area of interest
aoi = ee.Geometry.Rectangle([lon1, lat1, lon2, lat2])

# Apply cloud masking
def maskS2clouds(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(
        qa.bitwiseAnd(cirrusBitMask).eq(0))
    return image.updateMask(mask).divide(10000)

# Process and visualize
masked = s2.map(maskS2clouds)
Map.addLayer(masked.median(), {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 0.3}, 'Sentinel-2')
```

### 3. Calculate Vegetation Indices

```python
# Calculate NDVI
def addNDVI(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

# Apply to collection
withNDVI = masked.map(addNDVI)
Map.addLayer(withNDVI.select('NDVI'), {'min': -1, 'max': 1, 'palette': ['red', 'yellow', 'green']}, 'NDVI')
```

## 📚 Notebooks

### Core Analysis Notebooks

- **`sentinel2_processing.ipynb`** - Complete Sentinel-2 data processing pipeline
- **`cloud_masking.ipynb`** - Advanced cloud masking techniques
- **`vegetation_analysis.ipynb`** - Vegetation indices and forest analysis
- **`land_eligibility.ipynb`** - ESA eligibility analysis workflow
- **`forest_gain_loss.ipynb`** - Forest change detection

### Utility Notebooks

- **`data_export.ipynb`** - Export data to various formats
- **`visualization.ipynb`** - Interactive mapping and visualization
- **`batch_processing.ipynb`** - Large-scale batch processing

## 🛠️ Utilities

### Core Functions

```python
from gee_utils import (
    maskS2clouds,           # Cloud masking
    addVegetationIndices,   # Calculate vegetation indices
    exportToDrive,          # Export to Google Drive
    exportToCloudStorage,   # Export to Cloud Storage
    createTimeSeries,       # Create time series analysis
    calculateForestMetrics  # Forest-specific metrics
)
```

### Configuration

Create a `config.json` file:

```json
{
    "gee_project": "your-gee-project-id",
    "export_bucket": "your-cloud-storage-bucket",
    "default_scale": 10,
    "default_crs": "EPSG:4326",
    "cloud_threshold": 20,
    "date_range": "2023-01-01/2023-12-31"
}
```

## 🔧 Configuration

### Environment Variables

```bash
# Set your GEE project
export GEE_PROJECT="your-project-id"

# Set export bucket
export EXPORT_BUCKET="your-bucket-name"

# Set authentication
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

### Jupyter Configuration

Add to your Jupyter config:

```python
# Enable widgets
c.NotebookApp.nbserver_extensions = {
    'jupyterlab_widgets': True,
}

# Increase memory limit
c.NotebookApp.max_buffer_size = 1000000000
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```bash
# Re-authenticate
earthengine authenticate

# Check authentication
earthengine authenticate --list
```

#### 2. Memory Issues
```python
# Reduce batch size
batch_size = 100  # Instead of 1000

# Use smaller AOI
aoi = aoi.buffer(-1000)  # Reduce area
```

#### 3. Export Failures
```python
# Check export status
task = ee.batch.Export.image.toDrive(...)
print(task.status())

# Retry failed exports
if task.status()['state'] == 'FAILED':
    task.start()
```

#### 4. Certificate Issues (ArcGIS Pro)
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r requirements.txt
```

### Performance Optimization

- **Use appropriate scale**: 10m for Sentinel-2, 30m for Landsat
- **Limit date ranges**: Process smaller time periods
- **Optimize AOI size**: Smaller areas process faster
- **Use server-side operations**: Minimize client-side processing

## 📊 Example Workflows

### Forest Change Detection

```python
# Load Landsat collections
landsat5 = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')

# Calculate NDVI for different time periods
ndvi_2000 = landsat5.filterDate('2000-01-01', '2000-12-31').map(addNDVI).median()
ndvi_2020 = landsat8.filterDate('2020-01-01', '2020-12-31').map(addNDVI).median()

# Calculate change
change = ndvi_2020.select('NDVI').subtract(ndvi_2000.select('NDVI'))
Map.addLayer(change, {'min': -0.5, 'max': 0.5, 'palette': ['red', 'white', 'green']}, 'Forest Change')
```

### ESA Eligibility Analysis

```python
# Define eligibility criteria
def calculateEligibility(image):
    ndvi = image.normalizedDifference(['B8', 'B4'])
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        {'NIR': image.select('B8'), 'RED': image.select('B4'), 'BLUE': image.select('B2')}
    )
    
    # Eligibility criteria
    vegetation = ndvi.gt(0.3)
    enhanced_vegetation = evi.gt(0.2)
    not_water = image.select('SCL').neq(6)
    
    eligibility = vegetation.And(enhanced_vegetation).And(not_water)
    return image.addBands(eligibility.rename('eligibility'))

# Apply to collection
eligible = s2.map(calculateEligibility)
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
- [Qiusheng Wu](https://github.com/giswqs) for Geemap development
- The open-source geospatial community

## 📞 Support

- 📧 Email: muh.firdausiqbal@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/GEE_notebook_Forestry/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/GEE_notebook_Forestry/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/GEE_notebook_Forestry/discussions)

---

**Made with ❤️ for the forestry and geospatial community**