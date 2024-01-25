import ee
import math
from datetime import datetime

from .cloud_mask import (cloud_mask_oli, cloud_mask_tm, 
                         get_s2_sr_cld_col, add_cloud_bands, add_shadow_bands, apply_cld_shdw_mask  )

# need to have this threshold for a map function of thermal index, to ensure the data available,
#  if error 400 in TI or SSI data creation, please reduce the cloud cover
#cloud_cover_threshold = 40

# class imagecollection composite
class ImageCollectionComposite:
    def __init__(self, AOI=None, date_start_end=['2022-1-1',"2022-12-31"], cloud_cover_threshold = 40, config= {'IsThermal' : False}):
        self.config = config
        self.AOI = AOI

        # get the date based on the input list
        self.date_start_end = date_start_end

        import datetime 

        self.start_date = self.date_start_end[0]
        if isinstance(self.start_date, datetime.date):
            self.start_date = self.start_date.strftime("%Y-%m-%d")           

        self.end_date = self.date_start_end[1]
        if isinstance(self.end_date, datetime.date):
            self.end_date = self.end_date.strftime("%Y-%m-%d")      

        self.date_object = datetime.datetime.strptime(self.end_date, "%Y-%m-%d")
        self.year = self.date_object.year

        self.cloud_cover_threshold = cloud_cover_threshold\
        
        self.IsThermal = config['IsThermal']

    # utils for filter collection
    def filter_collection(self, col):
        return col.filterDate(self.start_date, self.end_date).filterBounds(self.AOI). \
                                                              filter(ee.Filter.lte('CLOUD_COVER', self.cloud_cover_threshold))

    def merging_collection_landsat(self):
        image_col = None
        if self.IsThermal == False:
            # col -> or collection
            l4 = ee.ImageCollection("LANDSAT/LT04/C02/T1_L2")
            l7 = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
            l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
            l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")

            # Composite function and only use cloud_masked image
            def landsat457():
                collection = self.filter_collection(l4).merge(self.filter_collection(l5)).merge(self.filter_collection(l7))
                image_collection = collection.map(cloud_mask_tm)#.median().clip(roi)
                return image_collection

            def landsat89():
                collection = self.filter_collection(l8).merge(self.filter_collection(l9))
                image_collection = collection.map(cloud_mask_oli)#.median().clip(roi)
                return image_collection

            
            print('selecting LANDSAT images')
            # select based on year, landsat 8 and 9 will be merged in the year 2014 or more
            if self.year < 2014:
                landsat = landsat457
            else:
                landsat = landsat89

            image_col = landsat() # this one without median aggregation, still need to do it after,
            return image_col
        
        elif self.IsThermal == True:
            l4_raw = ee.ImageCollection("LANDSAT/LT04/C02/T1")
            l7_raw = ee.ImageCollection("LANDSAT/LE07/C02/T1")
            l9_raw = ee.ImageCollection("LANDSAT/LC09/C02/T1")
            l8_raw = ee.ImageCollection("LANDSAT/LC08/C02/T1")
            l5_raw = ee.ImageCollection("LANDSAT/LT05/C02/T1")

            def landsat_raw457():
                collection = self.filter_collection(l4_raw).merge(self.filter_collection(l5_raw)).merge(self.filter_collection(l7_raw))
                image_collection = collection.map(lambda image: cloud_mask_tm(image, sr=False))#.median().clip(roi)
                return image_collection

            def landsat_raw89():
                collection = self.filter_collection(l8_raw).merge(self.filter_collection(l9_raw))
                image_collection = collection.map(lambda image: cloud_mask_oli(image, sr=False))#.median().clip(roi)
                return image_collection
            
            print('selecting LANDSAT images')
            # select based on year, landsat 8 and 9 will be merged in the year 2014 or more

            if self.year < 2014:
                landsat_raw = landsat_raw457
            else:
                landsat_raw = landsat_raw89

            image_col = landsat_raw() # this one without median aggregation, still need to do it after,
            return image_col


    # planet labs use the existing basemap, without masking, later will be treated in median
    def merging_collection_planet(self, region='asia'):
        print('selecting Planet images')
        nicfi_col = ee.ImageCollection("projects/planet-nicfi/assets/basemaps/asia")
        if region == 'asia':
            nifci_col = nicfi_col
        elif region == 'africa':
            nicfi_col = ee.ImageCollection("projects/planet-nicfi/assets/basemaps/africa")

        filteredNicfi = nicfi_col.filterDate(self.start_date, self.end_date) \
                     .filterBounds(self.AOI)

        def scaling_planet(image):
            sr_image = image.select(['R','G','B','N'], ['red','green', 'blue','nir']).multiply(0.0001)
            return sr_image

        filtered_scaled = filteredNicfi.map(scaling_planet) # this one already in median, single image
        return filtered_scaled

    def merging_collection_sentinel(self):
        print('selecting Sentinel images')

        s2_sr_cld_col = get_s2_sr_cld_col(self.AOI,self.start_date, self.end_date)

        SEN_BANDS = ['B2',   'B3', 'B4',  'B5', 'B6', 'B7', 'B8', 'B8A', 'B11', 'B12', 'cloudM' ]
        bandNamesSentinel2 = ['blue', 'green', 'red', 'redE1', 'redE2', 'redE3', 'nir', 'redE4', 'swir1', 'swir2','cloudM']

        # Apply the cloud and shadow mask to the entire image collection
        s2_sr_cld_col_masked = s2_sr_cld_col.map(lambda image: apply_cld_shdw_mask(image)['masked_image'])
        cloudM = s2_sr_cld_col.map(lambda image: apply_cld_shdw_mask(image)['cloudM'])

        # Convert the image collections to lists
        s2_sr_cld_list = s2_sr_cld_col_masked.toList(s2_sr_cld_col_masked.size())
        cloudM_list = cloudM.toList(cloudM.size())

        # Create an empty list to store the merged images
        merged_images = []

        # Iterate through the images in the collections and merge them
        for i in range(s2_sr_cld_col_masked.size().getInfo()):
            masked_image = ee.Image(s2_sr_cld_list.get(i))
            cloud_mask = ee.Image(cloudM_list.get(i))
            merged_image = masked_image.addBands(cloud_mask.rename('cloudM'))
            merged_images.append(merged_image)

        # Create a new ImageCollection from the merged images list
        s2_sr_cld_col_merged = ee.ImageCollection(merged_images)

        # Select the desired bands from the first image
        s2_sr_col = s2_sr_cld_col_merged.select(SEN_BANDS, bandNamesSentinel2)

        return s2_sr_col


    

    
        