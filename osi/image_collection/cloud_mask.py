import ee

# class cloudmasking for landsat
def cloud_mask_tm(image, sr=True):
    qa = image.select('QA_PIXEL')
    dilated = 1 << 1
    cloud = 1 << 3
    shadow = 1 << 4
    mask = qa.bitwiseAnd(dilated).eq(0) \
        .And(qa.bitwiseAnd(cloud).eq(0)) \
        .And(qa.bitwiseAnd(shadow).eq(0))

    if sr:
        optical_bands = image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'], ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']) \
                                            .updateMask(mask) \
                                            .multiply(0.0000275).add(-0.2)


        thermal_band = image.select(['ST_B6'], ['thermal']).updateMask(mask) \
                                            .multiply(0.00341802).add(149.0)


    else:
        optical_bands = image.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B7'], ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']) \
                                            .updateMask(mask) \
                                            .multiply(0.0001)

        thermal_band = image.select(['B6'], ['thermal']).updateMask(mask) \
                                            .multiply(0.0001)

    cloudM = mask.rename('cloudM')

    imageCloudMasked = image.addBands(optical_bands, None, True) \
                            .addBands(thermal_band, None, True)

    imageCloudMasked = imageCloudMasked.addBands(cloudM)

    return imageCloudMasked

def cloud_mask_oli(image, sr=True):
    qa = image.select('QA_PIXEL')
    dilated = 1 << 1
    cirrus = 1 << 2
    cloud = 1 << 3
    shadow = 1 << 4
    mask = qa.bitwiseAnd(dilated).eq(0) \
        .And(qa.bitwiseAnd(cirrus).eq(0)) \
        .And(qa.bitwiseAnd(cloud).eq(0)) \
        .And(qa.bitwiseAnd(shadow).eq(0))

    if sr:
        #print('sr=True')
        optical_bands = image.select(['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7'], ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']) \
                        .updateMask(mask) \
                        .multiply(0.0000275).add(-0.2)

        thermal_band = image.select(['ST_B10'], ['thermal']).updateMask(mask) \
                        .multiply(0.00341802).add(149.0)

    else:
        optical_bands = image.select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7'], ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']) \
                        .updateMask(mask) #\
                        #.multiply(0.0001)

        # image = detect_cloud_shadow(image)

        thermal_band = image.select(['B10'], ['thermal']) \
                        .updateMask(mask) #\
                        #.multiply(0.0001)

        #best_image_year = detect_cloud_shadow(best_image_year)

        # thermal index adapted from:

        AlB10 = ee.Number(image.get('RADIANCE_ADD_BAND_10'))
        M1B10 = ee.Number(image.get('RADIANCE_MULT_BAND_10'))

        radiance = thermal_band.multiply(M1B10).add(AlB10)

        K_1 = ee.Number(image.get('K1_CONSTANT_BAND_10'))
        K_2 = ee.Number(image.get('K2_CONSTANT_BAND_10'))
        A = ee.Number(image.get('RADIANCE_ADD_BAND_10'))
        M = ee.Number(image.get('RADIANCE_MULT_BAND_10'))

        # Getting the Thermal Index - source??
        TI = radiance.expression('(K_2) / log((K_1 / TEMP)+1)',{
              'K_2': K_2,
              'K_1': K_1,
              'TEMP':radiance
            }
          ).rename('TI')


    cloudM = mask.rename('cloudM')

    imageCloudMasked = image.addBands(optical_bands, None, True) \
                            .addBands(thermal_band, None, True)
    if sr==False:
        #print('sr=False')
        imageCloudMasked = imageCloudMasked.addBands(TI, None, True)

    imageCloudMasked = imageCloudMasked.addBands(cloudM)

    return imageCloudMasked
'''
# cloud masked func. Sentinel
##### START SENTINEL CLOUDLESS COMPOSITE AND MOSAICKING
THIS ONE IS FOR SENTINEL STILL BASED ON TUTORIAL
# adapted from: https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless

'''

#CLOUD_FILTER = 80
CLOUD_FILTER = 60
CLD_PRB_THRESH = 50
NIR_DRK_THRESH = 0.15
CLD_PRJ_DIST = 1
BUFFER = 50

def get_s2_sr_cld_col(aoi, start_date, end_date):
    # Import and filter S2 SR.
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', CLOUD_FILTER)))

    # Import and filter s2cloudless.
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, end_date))

    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': s2_sr_col,
        'secondary': s2_cloudless_col,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    }))

def add_cloud_bands(img):
    # Get s2cloudless image, subset the probability band.
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # Condition s2cloudless by the probability threshold value.
    is_cloud = cld_prb.gt(CLD_PRB_THRESH).rename('clouds')

    # Add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))

def add_shadow_bands(img):
    # Identify water pixels from the SCL band.
    not_water = img.select('SCL').neq(6)

    # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(NIR_DRK_THRESH*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

    # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

    # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, CLD_PRJ_DIST*10)
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
        .select('distance')
        .mask()
        .rename('cloud_transform'))

    # Identify the intersection of dark pixels with cloud shadow projection.
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')

    # Add dark pixels, cloud projection, and identified shadows as image bands.
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))

def apply_cld_shdw_mask(img):
    # Add cloud component bands.
    img_cloud = add_cloud_bands(img)

    # Add cloud shadow component bands.
    img_cloud_shadow = add_shadow_bands(img_cloud)

    # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)

    # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
    # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
    not_cld_shdw = (is_cld_shdw.focalMin(2).focalMax(BUFFER*2/20)
        .reproject(**{'crs': img.select([0]).projection(), 'scale': 30})
        .Not().rename('cloudM'))

    # Add the final cloud-shadow mask to the image.
    #img_all = img_cloud_shadow.addBands(not_cld_shdw)

    # Preserve specific properties by copying from the original image
    preserved_properties = img.propertyNames()
    img_masked = img_cloud_shadow.select(['B.*']).updateMask(not_cld_shdw).multiply(0.0001)

    # Copy the preserved properties back to the masked image
    img_masked = img_masked.copyProperties(img, preserved_properties)

    return {'masked_image': img_masked, 'cloudM': not_cld_shdw}