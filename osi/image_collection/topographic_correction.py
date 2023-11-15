# Topographic Correction Function ========================================================================================
# Define the function to convert degrees to radians
# adapted from https://doi.org/10.1016/j.rse.2019.111225 
# https://code.earthengine.google.com/193a79d71d96e2e5080939a74a345a43

import ee

def radians(img):
    return img.toFloat().multiply(3.14159265359).divide(180)

# Define the function to perform physical correction
def doPhysicalCorrection(image, type_DEM='srtm', I_satellite='LANDSAT'):

    # illumination parameters
    alos = ee.Image('JAXA/ALOS/AW3D30_V1_1')
    srtm = ee.Image('USGS/SRTMGL1_003')

    extent = image.geometry().bounds(1)

    # Select DEM, calculate aspect and slope
    
    if type_DEM == 'alos':
        DEM = alos
    else: 
        DEM = srtm
    
    DEM = DEM.clip(extent)
    boxcar = ee.Kernel.square(radius=3, units='pixels', normalize=True)
    DEMs = DEM.convolve(boxcar)
    SLP_deg = ee.Terrain.slope(DEMs)
    SLP = radians(SLP_deg)
    ASP_deg = ee.Terrain.aspect(DEMs)
    ASP = radians(ASP_deg)
    cos_SLP = SLP.cos()

    if I_satellite == 'LANDSAT':
        AZ = ee.Number(image.get('SUN_AZIMUTH'))
        ZE = ee.Number(image.get('SUN_ELEVATION'))
    elif I_satellite == 'Sentinel':
        AZ = ee.Number(image.get('MEAN_SOLAR_AZIMUTH_ANGLE'))
        ZE = ee.Number(image.get('MEAN_SOLAR_ZENITH_ANGLE'))

    AZ_R = radians(ee.Image(AZ)).clip(extent)
    ZE_R = radians(ee.Image(ZE)).clip(extent)
    cos_ZE = ZE_R.cos()
    cos_ZE_SLP = cos_ZE.multiply(SLP.cos())
    cos_VA = ee.Image(0).clip(extent).cos()

    # Calculate cos(Z)⋅cos(s) + sin(Z)⋅sin(s)⋅cos(a - a')
    IL1 = AZ_R.subtract(ASP).cos().multiply(SLP.sin()).multiply(ZE_R.sin()).add(cos_ZE.multiply(SLP.cos()))
    IL2 = IL1.where(IL1.lte(0), 0)
    IL3 = IL2.where(IL2.gt(0), 1)
    IL = IL1.mask(IL3).select([0], ['IL'])

    # Create and return a dictionary
    keyList = ee.List(['IL', 'cos_ZE', 'cos_VA', 'cos_SLP', 'SLP', 'ASP'])
    valueList = ee.List([IL, cos_ZE, cos_VA, cos_SLP, SLP, ASP])
    dictionary = ee.Dictionary.fromLists(keyList, valueList)

    # get illumination parameter result
    parameters = dictionary

    # starting to apply the parameter
    cos_ZE = ee.Image(parameters.get('cos_ZE'))
    cos_VA = ee.Image(parameters.get('cos_VA'))
    cos_SLP = ee.Image(parameters.get('cos_SLP'))

    IL = ee.Image(parameters.get('IL'))

    imgTC = image.select().addBands(image.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2'])  \
                                        .mask(image.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2'])  \
                                        .And(IL).And(image.select('cloudM')))    \
                                        .multiply((((cos_ZE).add(cos_VA))).divide((IL.add(cos_SLP)))))   \
                                        .addBands(image.select('cloudM'))   \
                                        .set('system:time_start', image.get('system:time_start'))

    return ee.Image(imgTC)