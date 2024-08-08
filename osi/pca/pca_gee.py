import ee
from ..spectral_indices.spectral_analysis import SpectralAnalysis

#############################
## Forest Canopy Density Mapping
#############################
#### PRINCIPAL COMPONENT ANALYSIS ########
# adapted from https://developers.google.com/earth-engine/guides/arrays_eigen_analysis
# Define the mean-centered function
# this image will be for the combination of two spectral indices or more

class PCA(SpectralAnalysis):
    def __init__(self, image, config):
        # arg that needed in this child class
        # self.image, self.pca_scale, self.tileScale, 
        
        # args that inherit from parent class, and now we will override if necessary
        # self.image, self.AOI, self.I_satellite, self.pca_scaling, self.pca_scale, self.tileScale, 
        super().__init__(image, config)

    # def means_centered(image, region, scale, tileScale):
    def means_centered(self):
        bandNames = self.image.bandNames()

        # Mean center the data
        meanDict = self.image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=self.AOI,
            scale=self.pca_scale,
            maxPixels=1e9,
            tileScale=self.tileScale,
            bestEffort=True,
        )
        means = ee.Image.constant(meanDict.values(bandNames))
        centered = self.image.subtract(means)

        self.centered = centered # it's not assign in the following method
        self.bandNames = bandNames

        return {'centered':centered, 'bandNames': bandNames}

    # Define the helper function to generate new band names
    def getNewBandNames(self, prefix):
        # seq = ee.List.sequence(1, self.bandNames.length())
        bandNames = self.means_centered()['bandNames']
        seq = ee.List.sequence(1, bandNames.length())
        return seq.map(lambda b: ee.String(prefix).cat(ee.Number(b).int().format()))

    # Define the function to get principal components
    def getPrincipalComponents(self):
        # Collapse the bands into a 1D array per pixel
        # arrays = self.centered.toArray()

        centered = self.means_centered()['centered']
        arrays = centered.toArray()

        # Compute the covariance within the region
        covar = arrays.reduceRegion(
            reducer=ee.Reducer.centeredCovariance(),
            geometry=self.AOI,
            scale=self.pca_scale,
            maxPixels=1e9,
            tileScale=self.tileScale,
            bestEffort=True,

        )

        # Get the covariance array result and cast to an array
        covarArray = ee.Array(covar.get('array'))

        # Perform eigen analysis and slice apart the values and vectors
        eigens = covarArray.eigen()

        # Extract eigenvalues and eigenvectors
        eigenValues = eigens.slice(1, 0, 1)
        eigenVectors = eigens.slice(1, 1)

        # Convert the array image to 2D arrays
        arrayImage = arrays.toArray(1)

        # Left multiply the image array by the matrix of eigenvectors
        principalComponents = ee.Image(eigenVectors).matrixMultiply(arrayImage)

        # Square root of eigenvalues as a P-band image
        sdImage = ee.Image(eigenValues.sqrt()) \
            .arrayProject([0]).arrayFlatten([self.getNewBandNames('sd')])

        # Normalize the principal components by their standard deviations
        return principalComponents \
            .arrayProject([0]) \
            .arrayFlatten([self.getNewBandNames('pc')]) \
            .divide(sdImage)

