import ee
from .image_collection_composite import ImageCollectionComposite
from .topographic_correction import doPhysicalCorrection

class ImageCollection(ImageCollectionComposite):
    def __init__(self, I_satellite, *args,**kwargs):
        self.I_satellite = I_satellite
        super().__init__(*args, **kwargs)

    def image_collection_mask(self):
        image_collection_mask = None
        if self.I_satellite == 'Landsat':
            image_collection_mask = self.merging_collection_landsat()
        elif self.I_satellite == 'Planet':
            image_collection_mask = self.merging_collection_planet(self.AOI) # if there is no image in here, maybe you choose a WRONG REGION
        elif self.I_satellite == 'Sentinel':
            image_collection_mask = self.merging_collection_sentinel()
        return image_collection_mask
    
    def image_mosaick(self):
        image_mosaick = None
        # we will use landsat that already corrected its topography
        if self.I_satellite == 'Landsat':
            image_mosaick = self.image_collection_mask().map(lambda image: doPhysicalCorrection(image, type_DEM='srtm',
                                                                                        I_satellite='Landsat')) \
                                                                                        .median().clip(self.AOI)
        elif self.IsThermal == True:
            # Define the weighted median function
            def weighted_median(collection):
                # Sort the collection by the timestamp in descending order
                sorted_collection = collection.sort('system:time_start', False)

                # Compute the weighted median
                weighted_median = sorted_collection.median()

                return weighted_median
            
            image_mosaick = weighted_median(self.image_collection_mask()).clip(self.AOI)
        
        else:
            image_mosaick = self.image_collection_mask().median().clip(self.AOI)

        return image_mosaick