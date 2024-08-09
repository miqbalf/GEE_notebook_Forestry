import ee
from ..spectral_indices.utils import normalization_100
from ..exporting_ee.main import exporting_to_ee
import pandas as pd
import numpy as np

class LandcoverML:
    def __init__(self, input_image, config, cluster_image = None, num_class=5):
        self.input_image = input_image
        self.pca_scale = config['pca_scale']
        self.cluster_image = cluster_image
        self.AOI = config['AOI']
        self.num_class=num_class
        self.project_name = config['project_name']


        ### normalized all the bands
        # Create an empty image to start with
        empty_image = ee.Image.constant(0).clip(AOI).select([])
        # list all bands necessary
        list_all_bands = self.input_image.bandNames().getInfo()

        # Recursively normalize each band and add it to the empty image
        normalized_image = empty_image
        for band in list_all_bands:
            normalized_band = normalization_100(input_image.select([band]), pca_scale, AOI)
            normalized_image = normalized_image.addBands(normalized_band)

        self.normalized_image = normalized_image

    # we will put land cover type classes based on what it's look like visually in the AOI
    # 5 classes will be as default, forest, shrub, grass, crop, water (example)
    def unsupervised_k_means(self): 
        # Perform k-means clustering - unsupervised class
        #scale is spatial resolution of Planet NICFI, numPixel (the bigger the better?) at least 100 per class for ha less than 500 or 10% of total pixel?, see: https://docs.google.com/spreadsheets/d/1J8MEi4IDn6faok6UUn9L64T61yWk0D4q/edit#gid=1919918133 to calculate manually (though its for stratified random sampling)
        training = self.cluster_image.sample(region=self.AOI, scale=self.pca_scale, numPixels=1000) 
        kmeans = ee.Clusterer.wekaKMeans(self.num_class).train(training)
        result_kmeans = self.cluster_image.cluster(kmeans)
        return result_kmeans

        
    # Calculate the area for each class
    def calculate_class_areas(self, k_means_image):
        # Create a pixel area image
        pixel_area = ee.Image.pixelArea()

        # Mask the image for each class and calculate the area
        class_areas = {}
        for i in range(self.num_class):  # in number_class above variable (previous cell)
            class_mask = k_means_image.eq(i)
            area = pixel_area.updateMask(class_mask).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=self.AOI,
                scale=self.pca_scale,
                maxPixels=1e10
            ).get('area')

            class_areas[i] = area

        return class_areas


    def stratified_random_creation(self):
        # try with K-means input
        result_kmeans = self.unsupervised_k_means().select('cluster')

        # Get the results
        area_dict = self.calculate_class_areas(result_kmeans)

        strata_area_based_kmeans = {}
        
        # Convert areas from square meters to hectares and print them
        for class_id, area in area_dict.items():
            area_ha = ee.Number(area).divide(1e4).getInfo()  # Convert area from square meters to hectares
            print(f'Class {class_id}: {area_ha:.2f} Ha')
            strata_area_based_kmeans[str(class_id)] = float(f'{area_ha:.2f}')
        
        # Convert the dictionary to a DataFrame
        df_sample_n = pd.DataFrame(list(strata_area_based_kmeans.items()), columns=['STRATA', 'MAPPED_AREA'])

        # Perform calculations
        total_area = df_sample_n['MAPPED_AREA'].sum()

        # A Prior parameter value
        S_O = 0.01  # A Priori total precision
        Ui = 0.7  # A priori user precision

        df_sample_n['Wi'] = df_sample_n['MAPPED_AREA'] / total_area
        df_sample_n['Ui'] = Ui
        df_sample_n['Si'] = np.sqrt(df_sample_n['Ui'] * (1 - df_sample_n['Ui']))
        df_sample_n['WiSi'] = df_sample_n['Wi'] * df_sample_n['Si']
        df_sample_n['WiSi^2'] = df_sample_n['Wi'] * (df_sample_n['Si'] ** 2)
        df_sample_n['NiSi'] = (df_sample_n['MAPPED_AREA'] * df_sample_n['Si'])
        
        total_sample_size = (df_sample_n['WiSi'].sum() ** 2) / ((S_O ** 2) + (1 / total_area) * df_sample_n['WiSi^2'].sum())

        df_sample_n['ni'] = ((total_sample_size * df_sample_n['WiSi']) / df_sample_n['WiSi'].sum()).astype(int)

        # Display the final DataFrame
        # display(df_sample_n)
        print('total sample size: ',total_sample_size)
        
        strata_ni = dict(zip(df_sample_n['STRATA'], df_sample_n['ni']))
        print(strata_ni)
            
        # Create stratified random samples
        stratified_training = result_kmeans.stratifiedSample(
            numPoints=0,  # Set numPoints to 0 to use class values from the dictionary
            classBand='cluster',
            region=self.AOI,
            scale=self.pca_scale,  # Adjust the scale as per your data resolution
            classValues=[int(k) for k in strata_ni.keys()],
            classPoints=list(strata_ni.values()),
            seed=0,  # For reproducibility, you can change the seed
            geometries=True
        )

        # Print the number of samples to verify
        print('Total samples:', stratified_training.size().getInfo())
        
        return {'df_sample_n':df_sample_n,
                'stratified_training':stratified_training}
    
    