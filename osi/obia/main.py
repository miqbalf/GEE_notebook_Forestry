import ee

# exploring SNIC - SEGMENTATION
# adapted from #https://gis.stackexchange.com/questions/333413/is-google-earth-engine-snic-segmentation-algorithm-inconsistent
class OBIASegmentation:
    def __init__(self, config, image, pca_scale, bands_to_select=[ 'red',
                                    'green',
                                    'blue',
                                    'nir',
                                    'ndwi',
                                    'msavi2',
                                    'MTVI2',
                                    'NDVI',
                                    'VARI',
                                    'FCD1',
                                    'FCD2'],
                 segment_on_rgb=False,
                 segment_bands=None):
        self.image = image
        self.super_pixel_size = config['super_pixel_size']
        self.pca_scale = pca_scale
        ## default to OSI, but now we can change this to any bands we want to select
        self.bands_to_select = bands_to_select
        # If True: SNIC uses only RGB (or segment_bands) for boundaries; mean aggregation uses full-spectral image
        self.segment_on_rgb = segment_on_rgb
        self.segment_bands = segment_bands or ['red', 'green', 'blue']

    # by default cluster aggregation per cluster are on the mean summary, if we want to create another aggregation (std, area, etc we can apply again later)
    def SNIC_cluster(self):
        if self.segment_on_rgb:
            return self._SNIC_cluster_rgb_segment_full_aggregate()
        return self._SNIC_cluster_same_image()

    def _SNIC_cluster_same_image(self):
        """Original: segment and aggregate both use the same image (all bands)."""
        snic = ee.Algorithms.Image.Segmentation.SNIC(
            image=self.image,
            size=self.super_pixel_size,
            compactness=0,
            connectivity=8,
            neighborhoodSize=64,
        ).reproject(
            crs='EPSG:4326',
            scale=self.pca_scale)
        bands_to_select_mean = [band + '_mean' for band in self.bands_to_select]
        mean_cluster_values = snic.select(bands_to_select_mean)
        clusters = snic.select('clusters')
        return {'clusters': clusters, 'mean_cluster_values': mean_cluster_values}

    def _SNIC_cluster_rgb_segment_full_aggregate(self):
        """Segment on RGB (or segment_bands) for boundaries; aggregate mean from original full-spectral image."""
        # Image for segmentation: fewer bands (e.g. RGB) for cleaner, more stable boundaries
        image_for_segmentation = self.image.select(self.segment_bands)
        snic = ee.Algorithms.Image.Segmentation.SNIC(
            image=image_for_segmentation,
            size=self.super_pixel_size,
            compactness=0,
            connectivity=8,
            neighborhoodSize=64,
        ).reproject(
            crs='EPSG:4326',
            scale=self.pca_scale)
        clusters = snic.select('clusters')

        # Aggregate (mean) from original image: use full spectral resolution for cluster statistics
        image_for_aggregation = self.image.select(self.bands_to_select).addBands(clusters)
        mean_image = image_for_aggregation.reduceConnectedComponents(
            reducer=ee.Reducer.mean(),
            labelBand='clusters',
            maxSize=256,
        )
        # SNIC / summarize_cluster expect bands named band_mean
        bands_to_select_mean = [b + '_mean' for b in self.bands_to_select]
        mean_cluster_values = mean_image.select(self.bands_to_select).rename(bands_to_select_mean)

        return {'clusters': clusters, 'mean_cluster_values': mean_cluster_values}
    
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
    

