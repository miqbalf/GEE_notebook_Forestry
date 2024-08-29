# run the module first to ensure its included in the sys.path
import sys
import os
import json


# Connect to the path of the module
module_path = r'C:\Users\q_bal\Documents\Github\GEE_notebook_Forestry'

# Add the module path to sys.path
if module_path not in sys.path:
    sys.path.append(module_path)

print(sys.path)

# Get the directory of the current script
#current_dir = os.path.dirname(__file__)
#current_dir = os.getcwd()
#seem we need to use explicit path for this, for qgis to work
current_dir = os.path.join(module_path,"osi/qgis")
print('current_dir: ',current_dir)

# Move to the parent directory of the current script
parent_dir = os.path.dirname(current_dir)

# Construct the absolute path to the JSON file in the 'input' folder
json_path= os.path.join(parent_dir, '00_input', 'balaban_conf.json')
# json_path = r'input\balaban_conf.json'

# Read and load the JSON data from the file
with open(json_path, 'r') as file:
    config = json.load(file)

print('config---> ',config)



# import main library
import ee
import geemap
import osi

from osi.utils.main import validate_aoi
# convert the modules for image collection (cloudless masking, compositing, reducer etc)
from osi.image_collection.main import ImageCollection
from osi.spectral_indices.spectral_analysis import SpectralAnalysis
from osi.spectral_indices.utils import normalization_100
from osi.hansen.historical_loss import HansenHistorical
from osi.classifying.assign_zone import AssignClassZone
from osi.legends.utils import convert_to_legend_items
from osi.legends.main import LegendsBuilder
from osi.obia.main import OBIASegmentation
from osi.ml.main import LandcoverML

AOIt_shp_plot = geemap.shp_to_ee(config['AOI_path'])
crs_input = config['crs_input']
I_satellite = config['I_satellite']

AOI = AOIt_shp_plot
config['AOI'] = AOI

ndwi_hi = 0.1
if config['I_satellite'] == 'Landsat':
    ndwi_hi = config['ndwi_hi_landsat']
elif I_satellite == 'Sentinel':
    ndwi_hi = config['ndwi_hi_sentinel']
elif I_satellite == 'Planet':
    ndwi_hi = config['ndwi_hi_planet']

### Masking and overlay and area helper Make an image out of the AOI area attribute -> convert featurecollection into raster (image) for overlaying tools
OID = config['OID_field_name']
AOI_img = AOI.filter(ee.Filter.notNull([OID])).reduceToImage(
    properties= [OID],
    reducer= ee.Reducer.first()
)

print('validate the AOI input: ')
validate_aoi(AOI, ee, config['OID_field_name'])

input_training_ee = geemap.shp_to_ee(config['input_training'])
print('validate input training points')
validate_aoi(input_training_ee, ee, 'code_lu')

# now starting to do analysis
# initiate instance class for the image collection and later mosaicking
classInputCollection = ImageCollection(I_satellite=I_satellite,
                                       AOI=AOI, 
                                       date_start_end=config['date_start_end'], 
                                       cloud_cover_threshold = config['cloud_cover_threshold'],
                                       region=config['region'])

# run the method from image collection loaded, cloudless compositing until to image_mosaick
image_mosaick = classInputCollection.image_mosaick()

# special case for QGIS PLUGIN ONLY
from ee_plugin import Map
from qgis.core import QgsVectorLayer, QgsProject
from qgis.utils import iface

# Load the shapefile as a vector layer
layer_aoi = QgsVectorLayer(config['AOI_path'], 'AOI_input', 'ogr')

# Check if the layer is valid
if not layer_aoi.isValid():
    print("Layer failed to load!")
else:
    # Add the layer to the current QGIS project
    QgsProject.instance().addMapLayer(layer_aoi)
    
    # Get the extent of the layer
    extent = layer_aoi.extent()
    
    # Print the extent to check (optional)
    print(f"Layer extent: {extent.toString()}")
    
    # Set the map canvas to zoom to the extent of the layer
    iface.mapCanvas().setExtent(extent)
    iface.mapCanvas().refresh()

    print("Zoomed to the extent of the AOI layer.")

vis_params_image_mosaick = {"bands":["red","green","blue"],"min":0,"max":0.1,"gamma":1}
project_name = config['project_name']

start_date = config['date_start_end'][0]
end_date = config['date_start_end'][1]

layer_name_image_mosaick = f'image_mosaick_result_ee_{project_name}'

# add to canvas Map for this mosaic layer
if I_satellite == 'Planet':
    # true color {"bands":["red","green","blue"],"min":0,"max":0.6,"gamma":1.5}
    # nir veg color {"bands":["red","nir","blue"],"min":0,"max":0.6,"gamma":1.5 }
    Map.addLayer(image_mosaick,{"bands":["red","green","blue"],"min":0,"max":0.6,"gamma":1.5}, f'{I_satellite} mosaicked - {start_date}-{end_date} VegColor')
else:
    Map.addLayer(image_mosaick,{'bands': ['swir2', 'nir', 'red'], 'min': 0, 'max': 0.6, 'gamma': 1.5 }, f'{I_satellite} mosaicked - {start_date}-{end_date}')

# in case you want to add input training programmatically
input_training = QgsVectorLayer(config['input_training'], 'input_training', 'ogr')
# Check if the layer is valid
if not input_training.isValid():
    print("Layer failed to load!")
else:
    # Add the layer to the current QGIS project
    QgsProject.instance().addMapLayer(input_training)

classImageSpectral = SpectralAnalysis(image_mosaick,config)

from osi.fcd.main_fcd import FCDCalc

from osi.pca.pca_gee import PCA

class_FCD_run = FCDCalc(config).fcd_calc()
FCD1_1 = class_FCD_run['FCD1_1']
FCD2_1 = class_FCD_run['FCD2_1']

Map.addLayer(FCD1_1, {'min':0 ,'max':80, 'palette':['ff4c16', 'ffd96c', '39a71d']},
                                                   f'FCD1_1_{project_name}')

Map.addLayer(FCD2_1, {'min':0 ,'max':80, 'palette':['ff4c16', 'ffd96c', '39a71d']},
                                                   f'FCD2_1_{project_name}')

print('finish processing PCA please continue')

# Now this is historical data to overlay later with current baseline (landcover)
hansen_class = HansenHistorical(config)
run_hansen = hansen_class.initiate_tcl()
LastImageLandsat, treeLossYear, minLoss, ForestArea2000Hansen, gfc =  \
                                 run_hansen['LastImageLandsat'], \
                                 run_hansen['treeLossYear'], \
                                 run_hansen['minLoss'], \
                                 run_hansen['ForestArea2000Hansen'], \
                                 run_hansen['gfc']

config['AOI_img'] = AOI_img

class_assigning_fcd =  AssignClassZone(config, FCD1_1=FCD1_1, FCD2_1=FCD2_1)
list_images_classified = class_assigning_fcd.assigning_fcd_class(gfc, minLoss)

fcd_classified_zone = list_images_classified['all_zone']

vis_params_fcd_classified = class_assigning_fcd.vis_param_merged
# Convert the dictionary to the LEGEND_ITEMS format
legend_items = convert_to_legend_items(class_assigning_fcd.legend_class)

Map.addLayer(fcd_classified_zone, vis_params_fcd_classified,
                                                   f'FCD_classified_zone_{project_name}')


# Print the result
# print(legend_items)

# skip legend at the moment, let's go with the analysis first

# image_mosaick_all_bands  = image_mosaick.addBands([FCD2_1.select('FCD').rename('FCD2_1'), FCD1_1.select('FCD').rename('FCD1_1')])
## ADDING DIRECTLY SPECTRAL INDICES
# classImageSpectral
pca_scale = classImageSpectral.pca_scale #pca_scale is spatial resolution. eg planet: 5
ndwi_image = classImageSpectral.NDWI_func()
msavi2_image = classImageSpectral.MSAVI2_func()
mtvi2_image = classImageSpectral.MTVI2_func()
ndvi_image = classImageSpectral.NDVI_func()
vari_image = classImageSpectral.VARI_func()

image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari = (
    image_mosaick
    .addBands(ndwi_image)
    .addBands(msavi2_image)
    .addBands(mtvi2_image)
    .addBands(ndvi_image)
    .addBands(vari_image)
)

red_norm = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select(['red']), pca_scale=pca_scale, AOI=AOI)
green_norm = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select(['green']), pca_scale=pca_scale, AOI=AOI)
blue_norm = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select(['blue']), pca_scale=pca_scale, AOI=AOI)
nir_norm = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select(['nir']), pca_scale=pca_scale, AOI=AOI)

image_norm = red_norm.addBands(green_norm).addBands(blue_norm).addBands(nir_norm)

image_norm_ndvi = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select('NDVI'), pca_scale=pca_scale, AOI=AOI)
image_norm_ndwi = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select('ndwi'), pca_scale=pca_scale, AOI=AOI)
image_norm_msavi2 = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select('msavi2'), pca_scale=pca_scale, AOI=AOI)
image_norm_mtvi2 = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select('MTVI2'), pca_scale=pca_scale, AOI=AOI)
image_norm_vari = normalization_100(image_mosaick_ndvi_ndwi_msavi2_mtvi2_vari.select('VARI'), pca_scale=pca_scale, AOI=AOI)

# red_norm.bandNames().getInfo()
image_norm_with_spectral_indices = image_norm.addBands(image_norm_ndvi).addBands(image_norm_ndwi).addBands(image_norm_msavi2).addBands(image_norm_mtvi2).addBands(image_norm_vari)
image_norm_with_spectral_indices_FCD = image_norm_with_spectral_indices.addBands(FCD2_1.select('FCD').rename('FCD2_1')).addBands(FCD1_1.select('FCD').rename('FCD1_1'))

obia = OBIASegmentation(config=config, image=image_norm_with_spectral_indices_FCD, pca_scale=pca_scale) #pca_scale basically is spatial resolution e.g planet: 5
clusters = obia.SNIC_cluster()['clusters']
object_properties_image = obia.summarize_cluster(is_include_std = False)

lc = LandcoverML(config=config,
                 input_image = image_norm_with_spectral_indices_FCD,
                cluster_properties=object_properties_image,
                pca_scale = pca_scale)

classifier = lc.run_classifier()

legend_lc = lc.lc_legend_param()
vis_param_lc = legend_lc['vis_param_lc']

legend_lc = legend_lc['legend_class']
# Convert the dictionary to the LEGEND_ITEMS format
legend_items_lc = convert_to_legend_items(legend_lc)

legend_class_lc = LegendsBuilder(legend_items=legend_items_lc)
legend_class_lc.create_legend('landcover')

legend_class_zone = LegendsBuilder(legend_items=legend_items)
legend_class_zone.create_legend('final-zone')

training_points = classifier['training_points']
validation_points = classifier['validation_points']

rf = classifier['classified_image_rf']
svm = classifier['classified_image_svm']
gbm = classifier['classified_image_gbm']
cart = classifier['classified_image_cart']

# fcd lc, 5 classes only, just nice to know
fcd_lc = list_images_classified['fcd_class_lc_image']
fcd_lc_vs = list_images_classified['vis_param_segment_lc']

Map.addLayer(fcd_lc,fcd_lc_vs, 'fcd-method_lc_result')
Map.addLayer(rf,vis_param_lc,'Random_forest_lc_result')
Map.addLayer(svm,vis_param_lc,'SVM_lc_result')
Map.addLayer(gbm,vis_param_lc,'GBM_lc_result')
Map.addLayer(cart,vis_param_lc,'CART_lc_result')

lc.matrix_confusion(fcd_lc,validation_points,'fcd')
lc.matrix_confusion(rf, validation_points, 'rf')
lc.matrix_confusion(svm, validation_points, 'svm')
lc.matrix_confusion(gbm, validation_points, 'gbm')
lc.matrix_confusion(cart, validation_points, 'cart')

algo_ml_selected = 'rf'
selected_image_lc = rf
if config['algo_ml_selected'] == 'rf':
    algo_ml_selected = 'rf'
    selected_image_lc = rf
elif config['algo_ml_selected'] == 'svm':
    algo_ml_selected = 'svm'
    selected_image_lc = svm
elif config['algo_ml_selected'] == 'gbm':
    algo_ml_selected = 'gbm'
    selected_image_lc = gbm
elif config['algo_ml_selected'] == 'cart':
    algo_ml_selected = 'cart'
    selected_image_lc = cart

# re-overlay the data for zoning from the selected method if they give the best metric, and when we check visually the land cover map make sense, also FCD approach is already there
image_for_zone = selected_image_lc

# comment this first, just check the LC above, then run the overlay zoning classification after
HighForestDense = list_images_classified['HighForestDense']

final_zone = class_assigning_fcd.assign_zone_ml(image_for_zone, minLoss,AOI_img, HighForestDense)
Map.addLayer(final_zone, vis_params_fcd_classified, f'Final_zone_ML_{algo_ml_selected}_Hansen')  # the naming probably will need to change, for some concistencies only so that you understand again later to read the codes

#additional data
# Load DEM data (replace 'dataset' with your actual DEM dataset)
DEM = ee.Image('USGS/SRTMGL1_003').clip(AOI)

# Calculate slope in degrees
slope = ee.Terrain.slope(DEM)

# Convert slope to percentage
slopePercentage = slope.expression('tan(b*0.01745) * 100', {'b': slope})

# Define slope classification thresholds
thresholds = [8, 15, 25, 40]  # Adjust these thresholds as needed

# Classify slope into categories using conditional statements
slopeClasses = slopePercentage \
    .lte(thresholds[0]).multiply(1) \
    .add(slopePercentage.gt(thresholds[0]).And(slopePercentage.lte(thresholds[1])).multiply(2)) \
    .add(slopePercentage.gt(thresholds[1]).And(slopePercentage.lte(thresholds[2])).multiply(3)) \
    .add(slopePercentage.gt(thresholds[2]).And(slopePercentage.lte(thresholds[3])).multiply(4)) \
    .add(slopePercentage.gt(thresholds[3]).multiply(5))

# Display the classified slope image
palette = ['lightgreen', 'yellow', 'orange', 'pink', 'red']  # Change green to lightgreen
vis_params = {'min': 1, 'max': 5, 'palette': palette}
Map.addLayer(slopeClasses, vis_params, 'Slope Classes')
print('finished adding slope')

import pandas as pd

## SOIL Overlay FAO
FAO_soil = ee.Image("users/muhammadiqbaltreeo/HWSD2_FAO").clip(AOI)
# Get the unique values from the image
unique_values = FAO_soil.reduceRegion(
    reducer=ee.Reducer.frequencyHistogram(),
    geometry=AOI.geometry(),
    scale=30
).getInfo()

unique_values = list(unique_values['b1'].keys())
unique_values = [int(f) for f in unique_values]
print('Unique values:', unique_values)

import random

# Generate random colors for each unique value
def get_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


value_color_map = {value: get_random_color() for value in unique_values}
print('Value-Color Map:', value_color_map)

# Create a color palette based on the unique values and their corresponding colors
palette = [value_color_map[value] for value in unique_values]

# Create a visualization dictionary
visualization = {
    'min': min(unique_values),
    'max': max(unique_values),
    'palette': palette
}

smu_table = ee.FeatureCollection("users/muhammadiqbaltreeo/HWSD2_SMU")

# Get the data as a Python dictionary
filtered_smu_table = smu_table.filter(ee.Filter.inList('HWSD2_SMU_ID', unique_values))

# Get the filtered data as a Python dictionary
filtered_smu_data = filtered_smu_table.getInfo()

# Extract the features from the dictionary
features = filtered_smu_data['features']

# Extract properties from each feature
properties_list = [feature['properties'] for feature in features]

# Convert the list of properties to a pandas DataFrame
df_snum = pd.DataFrame(properties_list)

# Display the DataFrame
# display(df_snum)

# Extract the 'name' and 'snum' columns and convert them to a dictionary
name_snum_dict = df_snum.set_index('HWSD2_SMU_ID')['name'].to_dict()
print(name_snum_dict)

# Update the legend dictionary to use the format "snum: name_soil"
legend_dict = {f"{snum}: {name_snum_dict[snum]}": value_color_map[snum] for snum in unique_values}

# Map.add_legend(title="Soil Type (FAO) Legend", legend_dict=legend_dict)

Map.addLayer(FAO_soil.clip(AOI),visualization,'FAO_soil')

# Map.addLayer(AOIsmaller.style(**style), {}, 'AOI Smaller')
Map.addLayer(training_points, {'color': 'yellow'},
    'Training data location')
Map.addLayer(validation_points, {'color': 'red'},
    'Validation data location')


######### EXPORTING
# Define the export task.
task4 = ee.batch.Export.table.toDrive(
    collection=training_points,
    description=f'training_points_{project_name}',
    driveFolder =f'result_lu_class_zone_{project_name}',
    fileFormat='GeoJSON'
)

# Define the export task.
task5 = ee.batch.Export.table.toDrive(
    collection=validation_points,
    description=f'validation_points_{project_name}',
    driveFolder =f'result_lu_class_zone_{project_name}',
    fileFormat='GeoJSON'
)


# Start the export task.
task4.start()
task5.start()

selected_class_zone = image_for_zone.select('Class').reduceToVectors(
    geometryType='polygon',
    reducer=ee.Reducer.countEvery(),
    scale=pca_scale,
    maxPixels=1e10,
    geometry=AOI  # Add geometry parameter
)

task_zone_result_export = ee.batch.Export.table(final_zone, f'zone_result_{project_name}_{algo_ml_selected}_{config["super_pixel_size"]}_cluster', {
  'driveFolder': f'result_lu_class_zone_{project_name}',
  'fileFormat': 'KML'
})

task_zone_result_export.start()