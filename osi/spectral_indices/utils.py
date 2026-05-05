import ee

# normalization image, utils
# adapted from https://code.earthengine.google.com/a6013a970da3901f42b1db8ae7fc265a
def normalization_100(image, pca_scale=30, AOI=None, scale_factor=100):
    """
    Normalize image using min-max with ±3σ clipping.
    
    Parameters:
    -----------
    image : ee.Image
        Input image to normalize
    pca_scale : float, default=30
        Scale for reduceRegion
    AOI : ee.Geometry, optional
        Region for computing statistics
    scale_factor : float, default=100
        Final scaling factor (100 for 0-100 range, 10000 for 0-10000 range)
    
    Returns:
    --------
    ee.Image : Normalized image scaled to [0, scale_factor]
    """
    image_scale = pca_scale
    region = AOI
    def normalize_band(name):
        name = ee.String(name)
        band = image.select(name)

        mean_std = image.reduceRegion(
            reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), None, True),
            geometry=region,
            scale=image_scale,
            maxPixels=10e9
        )

        mean = ee.Number(mean_std.get(name.cat('_mean')))
        std = ee.Number(mean_std.get(name.cat('_stdDev')))

        max_value = mean.add(std.multiply(3))
        min_value = mean.subtract(std.multiply(3))

        band1 = ee.Image(min_value).multiply(band.lt(min_value)).add(ee.Image(max_value).multiply(band.gt(max_value))) \
            .add(band.multiply(ee.Image(1).subtract(band.lt(min_value)).subtract(band.gt(max_value))))

        result_band = band1.subtract(min_value).divide(max_value.subtract(min_value))

        return result_band

    band_names = image.bandNames()
    unit_scale = ee.ImageCollection.fromImages(band_names.map(normalize_band)).toBands().rename(band_names)
    return unit_scale.multiply(scale_factor)  # Changed from 100 to scale_factor

def normalization_10000(image, pca_scale=30, AOI=None):
    """
    Normalize image to 0-10000 range (same as normalization_100 but scaled to 10000).
    Useful for mosaicking to preserve precision.
    """
    return normalization_100(image, pca_scale=pca_scale, AOI=AOI, scale_factor=10000)

def assigning_band(band_name_image,class_value,srcImg):

    # Create an image with the constant value for class
    constant_image_class = srcImg.multiply(0).add(class_value).rename(band_name_image)
    constant_image_pixel = srcImg.multiply(0).add(1).rename('pixel')

    # Add the new band to the existing image
    pixel_bandimg= srcImg.addBands(constant_image_pixel)
    pix_classImg = pixel_bandimg.addBands(constant_image_class)
    pix_classImg = pix_classImg.select([band_name_image,'pixel'])

    return pix_classImg