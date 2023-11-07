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