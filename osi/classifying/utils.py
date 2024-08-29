import ee

# Create a function to add two images element-wise
def add_images(img1, img2):
    return ee.Image(img1).add(img2)

def add_classes(image, empty):
        # Cast the image to Int32 to handle NaN and null values
        image = image.unmask(0).toInt32()
        # Set a conditional statement to retain existing class values if non-zero, otherwise use the new class value
        merged_image = empty.where(empty.neq(0), empty).where(image.neq(0), image)
        return merged_image

# Function to check if a band exists in an image
def select_band_if_exists(image, band_name):
    # Check if the band exists in the image
    if band_name in image.bandNames().getInfo():
        # Select the band if it exists
        return image.select([band_name])
    else:
        # Return None if the band does not exist
        return None
    
def unmasked_helper(image, AOI_img, AOI):
    mask_image = image.mask()
    mask_image_inverted = mask_image.Not()
    unmasked_image = AOI_img.unmask().updateMask(mask_image_inverted).clip(AOI)
    return unmasked_image