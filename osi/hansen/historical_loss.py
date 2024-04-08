import ee
############################ Deforestation areas - TCL (Tree Cover Loss)
### adapted from https://developers.google.com/earth-engine/tutorials/community/forest-cover-loss-estimation
class HansenHistorical:
    def __init__(self, config):
        self.config = config
        self.pixel_number = config['pixel_number']
        self.year_start_loss = config['year_start_loss']
        self.tree_cover_forest = config['tree_cover_forest']
        self.AOI = config['AOI']
    def initiate_tcl(self):
        # hansen - updated version - global data
        # gfc = ee.Image("UMD/hansen/global_forest_change_2022_v1_10")
        gfc = ee.Image('UMD/hansen/global_forest_change_2023_v1_11') # updated to hansen 2023 version
        
        #Canopy cover percentage (e.g. 30%), for Indonesia
        cc = ee.Number(self.tree_cover_forest)
        
        #Minimum forest area in pixels (e.g. 3 pixels, ~ 0.27 ha in this example).
        pixels = ee.Number(self.pixel_number)
        
        #Minimum mapping area for tree loss (usually same as the minimum forest area).
        lossPixels = pixels
        
        canopyCover = gfc.select(['treecover2000'])
        canopyCoverThreshold = canopyCover.gte(cc).selfMask()
        
        #Use connectedPixelCount() to get contiguous area.
        contArea = canopyCoverThreshold.connectedPixelCount()
        #Apply the minimum area requirement.
        minArea = contArea.gte(pixels).selfMask()
        
        prj = gfc.projection()
        scale = prj.nominalScale()
        ForestArea2000Hansen = minArea.reproject(prj.atScale(scale))  
        #Map.addLayerControl()
        # Map.addLayer(ForestArea2000Hansen, {
        #     'palette': ['#96ED89']
        # }, 'tree cover: >= min canopy cover & area (light green)', False)
        #create visual boundary color only
        empty = ee.Image().byte()
        AOIm = empty.paint(self.AOI,0,10)

        ##### Visualized LANDSAT CLOUDLESS FROM HANSEN DATASET LAST YEAR # just to check the visual images from Hansen
        LastImageLandsat = gfc.select(['last_b30', 'last_b40', 'last_b50', 'last_b70']).rename(['red', 'nir', 'swir1', 'swir2']).clip(self.AOI)
        # Map.addLayer(LastImageLandsat, {'bands': ['swir2', 'nir', 'red'], 'min': 0, 'max': 600, 'gamma': 1.5 },
        #                 f'Landsat Hansen Last Year {end_date}', False)

        ### HISTORICAL DATA THRESHOLD - Get the TCL data LOSS PIXEL overall data from loss year in the input
        # adapted from https://developers.google.com/earth-engine/tutorials/community/forest-cover-loss-estimation
        
        treeLossYear = gfc.select(['lossyear'])
        treeLoss = treeLossYear.gte(self.year_start_loss).selfMask() # tree loss in e.g., year > 2012 ####SHOULD CHANGE TO RECENT YEAR for the '12' number
        #Select the tree loss within the derived tree cover
        #(>= canopy cover and area requirements). THIS ONE ALREADY MASK TCL IN FOREST AREA
        treecoverLoss = minArea.And(treeLoss).rename(f'lossfrom_{self.year_start_loss}').selfMask()
        
        #Create connectedPixelCount() to get contiguous area.
        contLoss = treecoverLoss.connectedPixelCount()
        #Apply the minimum area requirement, and get the TCL data ---> minLoss - ACTUAL TCL AREA from Hansen since the year_start_loss
        minLoss = contLoss.gte(lossPixels).selfMask()
        
        # Map.addLayer(treeLossYear.clip(AOI),{"opacity":1,"bands":["lossyear"],"min":1,"max":22,"palette":["3d358c","4457c9","4777f0","4196ff","2eb4f3","1ad1d5","1ae5b6","36f493","64fd6a","92ff47","b4f836","d3e935","ecd239","fbb938","fe992c","f9751d","ec520e","d93806","bf2102","9f1001","7a0403","#FF0000"]},"Tree Loss Year", False)
        # Map.addLayer(minLoss.clip(AOI),{
        #     'palette': ['#ff0000']
        # }, f'tree cover >30% loss since 20{year_start_loss}', False)

        return {
            'LastImageLandsat': LastImageLandsat,
            'treeLossYear': treeLossYear,
            'minLoss':minLoss,
            'ForestArea2000Hansen': ForestArea2000Hansen,
            'gfc': gfc,
        }
