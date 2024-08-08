import ee

class SpectralAnalysis:
    # def __init__(self, image, AOI = None, I_satellite= 'Landsat', pca_scaling = 1, tileScale = 1):
    def __init__(self, image, config):
        self.image = image

        self.I_satellite = config['I_satellite']
        self.AOI = config['AOI']
        # scaling the pixel per satellite vendor type
        self.pca_scaling = config['pca_scaling']
        self.tileScale = config['tileScale']

        # self.I_satellite = I_satellite
        # self.AOI = AOI
        # # scaling the pixel per satellite vendor type
        # self.pca_scaling = pca_scaling
        # self.tileScale = tileScale # increase this if user memory limit occur, see: https://gis.stackexchange.com/questions/373250/understanding-tilescale-in-earth-engine


        self.pca_scale = 1*30
        if self.I_satellite == 'Landsat':
            self.pca_scale = self.pca_scaling *30 # 1 meaning that 1 x pixel size of spatial resolution e.g., Planet Labs 1 x 5, Sentinel 1 x 10, Landsat 1 x 30
        elif self.I_satellite == 'Sentinel':
            self.pca_scale = self.pca_scaling  *10
        elif self.I_satellite == 'Planet':
            self.pca_scale = self.pca_scaling *5

    def max_bands(self):
        maxRed = self.image.select('red').reduceRegion(reducer=ee.Reducer.max(),
                                                        geometry=self.AOI,
                                                        scale=self.pca_scale,
                                                        bestEffort=True,
                                                        tileScale=self.tileScale)
        #print("MAXRED",maxRed)
        maxRed = ee.Dictionary(maxRed).toImage()
        maxGreen =self.image.select('green').reduceRegion(reducer=ee.Reducer.max(),
                                                    geometry=self.AOI,
                                                    scale=self.pca_scale,
                                                    bestEffort=True,
                                                    tileScale=self.tileScale)
        maxGreen = ee.Dictionary(maxGreen).toImage()
        maxBlue = self.image.select('blue').reduceRegion(reducer=ee.Reducer.max(),
                                                    geometry=self.AOI,
                                                    scale=self.pca_scale,
                                                    bestEffort=True,
                                                    tileScale=self.tileScale)
        maxBlue = ee.Dictionary(maxBlue).toImage()
        return [maxRed,maxGreen,maxBlue]


    # Advanced Vegetation index - scaled from old formula (8bit) to relative number based on region
    def AVI_func(self):
        AVI = self.image.expression('((nir + 1 )* (maxRed-red) *(nir -red))**0.333',{
            'nir':self.image.select(['nir']),
            'red':self.image.select(['red']),
            'maxRed': self.max_bands()[0],
            }
        ).rename('AVI')

        return AVI

    # Bare Soil Index
    # https://www.researchgate.net/publication/319045433_Integration_of_GIS_and_Remote_Sensing_for_Evaluating_Forest_Canopy_Density_Index_in_Thai_Nguyen_Province_Vietnam/link/599293be0f7e9b433f415b40/download
    def BSI_func(self):
        BSI = ''
        if self.I_satellite == 'Landsat' or self.I_satellite == 'Sentinel':
            BSI = self.image.expression('(((SWIR1 + red) - (G + NIR)) / ((SWIR1 + red) + (G + NIR)))*100+100',{
                'SWIR1':self.image.select(['swir1']),
                'G':self.image.select(['green']),
                'red':self.image.select(['red']),
                'NIR':self.image.select(['nir']),
                }
            ).rename('BSI')

        elif self.I_satellite == 'Planet':
            BSI = self.image.expression(
                '(NIR + GREEN + RED) / (NIR + GREEN - RED)',  {
                    'NIR': self.image.select('nir'),
                    'GREEN': self.image.select('green'),
                    'RED': self.image.select('red')
                        }
                    ).rename('BSI')

        return BSI

    def SI_func(self):
        SI = self.image.expression('((maxGreen-Green)*(maxBlue-Blue)*(maxRed-Red))**(1/3)',{
            'Red':self.image.select(['red']),
            'Green':self.image.select(['green']), #//******
            'Blue':self.image.select(['blue']),
            'maxRed': self.max_bands()[0],
            'maxGreen': self.max_bands()[1],
            'maxBlue': self.max_bands()[2],
        }
        ).rename('SI')
        return SI
    
    
    # NDWI = (Green – NIR)/(Green + NIR)
    def NDWI_func(self):
        NDWI = self.image.expression(
            '(Green - NIR) / (Green + NIR)', {
                'Green': self.image.select('green'),
                'NIR': self.image.select('nir')
            }
        ).rename('ndwi')
        return NDWI
    
    # MSAVI2  https://developers.planet.com/docs/basemaps/tile-services/indices/
    def MSAVI2_func(self):
        MSAVI2 = self.image.expression(
            '((2*nir +1) - ((2* nir +1)**2-(8*(nir-red)))**0.5)/2', {
                'nir': self.image.select('nir'),
                'red': self.image.select('red')
            }
        ).rename('msavi2')
        return MSAVI2
    
    # Define the MTVI2 calculation function
    def MTVI2_func(self):
        mtvi2 = self.image.expression(
            '1.5 * ((1.2 * (NIR - Green) - 2.5 * (Red - Green)) / '
            'sqrt((2 * NIR + 1) ** 2 - (6 * NIR - 5 * sqrt(Red)) - 0.5))', {
                'NIR': self.image.select('nir'),
                'Red': self.image.select('red'),
                'Green': self.image.select('green')
            }
        ).rename('MTVI2')
        return mtvi2
    
    # Define the NDVI calculation function
    def NDVI_func(self):
        ndvi = self.image.expression(
            '(NIR - Red) / (NIR + Red)', {
                'NIR': self.image.select('nir'),
                'Red': self.image.select('red')
            }
        ).rename('NDVI')
        return ndvi


    # Visual Atmosphere Resistance Index (VARI)
    def VARI_func(self):
        vari = self.image.expression(
            '(Green - Red) / (Green + Red - Blue)', {
                'Green': self.image.select('green'),
                'Red': self.image.select('red'),
                'Blue': self.image.select('blue')
            }
        ).rename('VARI')
        return vari