import ee

# exploring SNIC - SEGMENTATION
# adapted from #https://gis.stackexchange.com/questions/333413/is-google-earth-engine-snic-segmentation-algorithm-inconsistent
class OBIASegmentation:
    def __init__(self, config, image, pca_scale):
        self.image = image
        self.super_pixel_size = config['super_pixel_size']
        self.pca_scale = pca_scale

    # by default cluster aggregation per cluster are on the mean summary, if we want to create another aggregation (std, area, etc we can apply again later)
    def SNIC_cluster(self):
        # Apply SNIC segmentation on the FCD image
        snic = ee.Algorithms.Image.Segmentation.SNIC(
            image=self.image,
            # image= avi_norm,
            size=self.super_pixel_size,
            compactness=0, # let's make this default for the moment, we can change it later
            connectivity=8,
            neighborhoodSize=64,
            # seeds=seeds,
        ).reproject( # handling/apply the workaround of inconsistency https://gis.stackexchange.com/questions/333413/is-google-earth-engine-snic-segmentation-algorithm-inconsistent
        crs='EPSG:4326',
        scale=self.pca_scale)

        # only means number of these bands in clusters
        mean_cluster_values = snic.select([
        'red_mean',
        'green_mean',
        'blue_mean',
        'nir_mean',
        'ndwi_mean',
        'msavi2_mean',
        'MTVI2_mean',
        'NDVI_mean',
        'VARI_mean',
        'FCD1_1_mean',
        'FCD2_1_mean',
        ])

        # Map.addLayer(vectors, {}, 'snic-vector')

        # Pull out the clusters layer, each cluster has a uniform value
        clusters = snic.select('clusters')
        return { 'clusters':clusters,
                'mean_cluster_values':mean_cluster_values }
    
    def summarize_cluster(self, is_include_std = False):
        clusters = self.SNIC_cluster()['clusters']
        mean_cluster_values = self.SNIC_cluster()['mean_cluster_values']
        # Compute the area of each cluster.
        area_cluster = ee.Image.pixelArea().addBands(clusters).reduceConnectedComponents(
            reducer=ee.Reducer.sum(),
            labelBand='clusters',
            maxSize=256
        )

        # Compute the perimeter of each cluster.
        minMax = clusters.reduceNeighborhood(
        reducer= ee.Reducer.minMax(),
        kernel= ee.Kernel.square(1)
        )
        perimeterPixels = minMax.select(0).neq(minMax.select(1))
        perimeter = perimeterPixels.addBands(clusters).reduceConnectedComponents(
            reducer=ee.Reducer.sum(),
            labelBand='clusters',
            maxSize= 256
        )

        # Compute the width and height of each cluster.
        sizes = ee.Image.pixelLonLat().addBands(clusters).reduceConnectedComponents(
            reducer=ee.Reducer.minMax(),
            labelBand='clusters',
            maxSize=256,
        )
        width = sizes.select('longitude_max').subtract(sizes.select('longitude_min')).rename('width')
        height = sizes.select('latitude_max').subtract(sizes.select('latitude_min')).rename('height')

        ## putting all together the info of additional stat and object info (perimeter, size, width, height)
        object_properties_image = ee.Image.cat([
            mean_cluster_values,
            area_cluster,
            perimeter,
            width,
            height,
            ])
        
        if is_include_std:
            stdDev_image =  self.image.addBands(clusters).reduceConnectedComponents(
                reducer =ee.Reducer.stdDev(),
                labelBand= 'clusters',
                maxSize=256,
                )
            object_properties_image = ee.Image.cat([object_properties_image, 
                                                    stdDev_image])

        print(f'snic list bands: {object_properties_image.bandNames().getInfo()}')
        return object_properties_image
    

