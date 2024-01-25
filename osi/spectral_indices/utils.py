import ee

# normalization image, utils
# adapted from https://code.earthengine.google.com/a6013a970da3901f42b1db8ae7fc265a
def normalization_100(image, pca_scale=30, AOI=None):
    #image_scale = ee.Number(image.projection().nominalScale())
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
    return unit_scale.multiply(100)

def assigning_band(band_name_image,class_value,srcImg):

    # Create an image with the constant value for class
    constant_image_class = srcImg.multiply(0).add(class_value).rename(band_name_image)
    constant_image_pixel = srcImg.multiply(0).add(1).rename('pixel')

    # Add the new band to the existing image
    pixel_bandimg= srcImg.addBands(constant_image_pixel)
    pix_classImg = pixel_bandimg.addBands(constant_image_class)
    pix_classImg = pix_classImg.select([band_name_image,'pixel'])

    return pix_classImg