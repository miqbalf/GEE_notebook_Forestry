import ee
from datetime import datetime

from .cloud_mask import cloud_mask_oli, cloud_mask_tm

# need to have this threshold for a map function of thermal index, to ensure the data available,
#  if error 400 in TI or SSI data creation, please reduce the cloud cover
#cloud_cover_threshold = 40

class ImageCollectionComposite:
    def __init__(self, AOI=None, date_start_end=['2022-1-1',"2022-12-31"], cloud_cover_threshold = 40):
        self.AOI = AOI

        # get the date based on the input list
        self.date_start_end = date_start_end
        self.start_date = self.date_start_end[0]
        self.end_date = self.date_start_end[1]

        self.date_object = datetime.strptime(self.end_date, "%Y-%m-%d")
        self.year = self.date_object.year
        
        self.cloud_cover_threshold = cloud_cover_threshold
    
    # utils for filter collection
    def filter_collection(self, col):
        return col.filterDate(self.start_date, self.end_date).filterBounds(self.AOI). \
                                                              filter(ee.Filter.lte('CLOUD_COVER', self.cloud_cover_threshold))

    def merging_collection_landsat(self):
        # col -> or collection
        l4 = ee.ImageCollection("LANDSAT/LT04/C02/T1_L2")
        l7 = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        l5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")

        l4_raw = ee.ImageCollection("LANDSAT/LT04/C02/T1")
        l7_raw = ee.ImageCollection("LANDSAT/LE07/C02/T1")
        l9_raw = ee.ImageCollection("LANDSAT/LC09/C02/T1")
        l8_raw = ee.ImageCollection("LANDSAT/LC08/C02/T1")
        l5_raw = ee.ImageCollection("LANDSAT/LT05/C02/T1")

        # Composite function
        def landsat457():
            collection = self.filter_collection(l4).merge(self.filter_collection(l5)).merge(self.filter_collection(l7))
            image_collection = collection.map(cloud_mask_tm)#.median().clip(roi)
            return image_collection

        def landsat89():
            collection = self.filter_collection(l8).merge(self.filter_collection(l9))
            image_collection = collection.map(cloud_mask_oli)#.median().clip(roi)
            return image_collection

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
            landsat = landsat457
            landsat_raw = landsat_raw457
        else:
            landsat = landsat89
            landsat_raw = landsat_raw89

        image_col = landsat() # this one without median aggregation, still need to do it after,
        return image_col
    
    def merging_collection_planet(self, region='asia'):
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
        
        filtered_scaled = filteredNicfi.map(scaling_planet).median().clip(self.AOI) # this one already in median, single image
        return filtered_scaled


    

    
        