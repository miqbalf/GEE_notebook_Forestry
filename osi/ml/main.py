import ee
import geemap
from ..spectral_indices.utils import normalization_100
from ..exporting_ee.main import exporting_to_ee
import pandas as pd
import numpy as np
import os

class LandcoverML:
    def __init__(self, input_image, config, cluster_properties = None, num_class=5, pca_scale=5):
        self.input_image = input_image
        self.pca_scale = pca_scale
        self.cluster_properties = cluster_properties
        self.AOI = config['AOI']
        self.num_class=num_class
        self.project_name = config['project_name']
        self.input_training = config['input_training']
        self.config = config
        


        ### normalized all the bands
        # Create an empty image to start with
        empty_image = ee.Image.constant(0).clip(self.AOI).select([])
        # list all bands necessary
        list_all_bands = self.input_image.bandNames().getInfo()

        # Recursively normalize each band and add it to the empty image
        normalized_image = empty_image
        for band in list_all_bands:
            normalized_band = normalization_100(input_image.select([band]), pca_scale, self.AOI)
            normalized_image = normalized_image.addBands(normalized_band)

        self.normalized_image = normalized_image

    # we will put land cover type classes based on what it's look like visually in the AOI
    # 5 classes will be as default, forest, shrub, grass, crop, water (example)
    def unsupervised_k_means(self): 
        # Perform k-means clustering - unsupervised class
        #scale is spatial resolution of Planet NICFI, numPixel (the bigger the better?) at least 100 per class for ha less than 500 or 10% of total pixel?, see: https://docs.google.com/spreadsheets/d/1J8MEi4IDn6faok6UUn9L64T61yWk0D4q/edit#gid=1919918133 to calculate manually (though its for stratified random sampling)
        training = self.cluster_properties.sample(region=self.AOI, scale=self.pca_scale, numPixels=1000) 
        kmeans = ee.Clusterer.wekaKMeans(self.num_class).train(training)
        result_kmeans = self.cluster_properties.cluster(kmeans)
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
    
    def run_classifier(self):
        path_shp_input_training = self.input_training
        input_training_feature = geemap.shp_to_ee(path_shp_input_training)
        points = input_training_feature.randomColumn()
        training_fraction = 0.7
        training_points = points.filter(ee.Filter.lt('random', training_fraction))
        validation_points = points.filter(ee.Filter.gte('random', training_fraction))

        ###### trying random forest- pixel based (without segmentation): classic supervised classification
        training_pixel = self.input_image.sampleRegions(
            collection=training_points,
            properties=['code_lu'],
            scale=self.pca_scale
        )

        # Train a random forest classifier using the segmented statistics
        classifier_pixel = ee.Classifier.smileRandomForest(10).train(
            features=training_pixel,
            classProperty='code_lu',
            inputProperties=self.input_image.bandNames()
            # inputProperties=stats_image_spectralindices_fcd.bandNames()
        )

        # Classify the segments using the trained classifier
        classified_image_basedpixel = self.input_image.classify(classifier_pixel)

        # Sample the points from the shapefile for training in segmented (cluster) image
        training_stats_segmented = self.cluster_properties.sampleRegions(
            collection=training_points,
            properties=['code_lu'],
            scale=self.pca_scale
        )

        ############ RANDOM FOREST
        # Train a random forest classifier using the segmented statistics
        classifier_rf = ee.Classifier.smileRandomForest(10).train(
                            features=training_stats_segmented,
                            classProperty='code_lu',
                            inputProperties=self.cluster_properties.bandNames()
                            )

        # Classify the segments using the trained classifier
        classified_segments_rf_stat = self.cluster_properties.classify(classifier_rf)

        ############# SVM
        # Train a Support Vector Machine (SVM) classifier
        classifier_svm = ee.Classifier.libsvm().train(
            features=training_stats_segmented,
            classProperty='code_lu',
            inputProperties=self.cluster_properties.bandNames()
        )

        # Classify the image using the trained classifier
        classified_image_svm = self.cluster_properties.classify(classifier_svm)

        ############# GBM
        # Train a Gradient Boosting Classifier
        classifier_gbm = ee.Classifier.smileGradientTreeBoost (#numberOfTrees, shrinkage, samplingRate, maxNodes, loss, seed
            numberOfTrees=100,
        ).train(
            features=training_stats_segmented,
            classProperty='code_lu',
            inputProperties=self.cluster_properties.bandNames()
        )

        # Classify the image using the trained classifier
        classified_image_gbm = self.cluster_properties.classify(classifier_gbm)

        ############# CART
        # Train a CART classifier
        classifier_cart = ee.Classifier.smileCart().train(
            features=training_stats_segmented,
            classProperty='code_lu',
            inputProperties=self.cluster_properties.bandNames()
        )

        # Classify the image using the trained classifier
        classified_image_cart = self.cluster_properties.classify(classifier_cart)

        return {'training_points':training_points,
                'validation_points': validation_points,
                'classified_image_basedpixel':classified_image_basedpixel,
                'classified_segments_rf_stat': classified_segments_rf_stat,
                'classified_image_svm':classified_image_svm,
                'classified_image_gbm':classified_image_gbm,
                'classified_image_cart':classified_image_cart
                }
    
    def matrix_confusion(self, image_class, validation_points, ml_algorithm):
        sample_validation_image = image_class.sampleRegions(
            collection=validation_points,
            properties=['code_lu'],
            scale=self.pca_scale
        )

        # Get the confusion matrix for both classifiers
        result_matrix = sample_validation_image.errorMatrix('code_lu', 'classification')
        
        # Prepare output text
        output_lines = []
        output_lines.append('-------------------------------------------------------------------------------------')
        output_lines.append(f'Algorithm of ML used: {ml_algorithm}')
        # Print and prepare the accuracy metrics
        output_lines.append('Confusion Matrix:')
        output_lines.append(str(result_matrix.getInfo()))
        output_lines.append(f'Overall Accuracy: {result_matrix.accuracy().getInfo()}')
        output_lines.append(f'Producer\'s Accuracy: {result_matrix.producersAccuracy().getInfo()}')
        output_lines.append(f'User\'s Accuracy: {result_matrix.consumersAccuracy().getInfo()}')
        output_lines.append(f'Kappa: {result_matrix.kappa().getInfo()}')
        output_lines.append('-------------------------------------------------------------------------------------')

        # Print to console
        for line in output_lines:
            print(line)

        output_dir = os.path.join(self.config['module_path'],"osi","01_output")

        # Write to a text file in 01_output and with the file name confusion_matrix_output_{self.config["project_name"]}.txt'
        with open(os.path.join(output_dir,f'conf_acc_{self.config["project_name"]}.txt'), 'a') as f:
            for line in output_lines:
                f.write(line + '\n')
    
    
    def lc_legend_param(self):
        pallette_class_segment = {
            '1': '#83ff5a',  # forest_trees (1)
            '2': '#ffe3b3',  # shrubland (2)
            '3': '#ffff33',  # grassland (3)
            '4': '#f89696',  # openland (4)
            '5': '#1900ff',  # waterbody_wet_area (5)
            '6': '#e6e6fa',  # plantation (6)
            '7': '#FFFFFF',   # gray_infrastructure (7)
            '8': '#4B0082',  # oil_palm (8) - Dark Purple
            '9': '#8B4513',  # cropland (9) - Brown
            '10': '#87CEEB',  # waterbody (10) - Light Blue
            '11': '#2F4F4F',  # wetlands (11) - Dark Teal
            '12': '#ADFF2F',  # forest_trees_regrowth (12) - Light Green
            '13': '#8B0000',  # historical_treeloss_10years (13) - Dark Red
            '14': '#DAA520'   # paddy_irrigated (14) - Golden Yellow

            }
        
        # Define the order of class IDs only for FCD
        class_ids_order = ['1', '2', '3', '4', '5', '6', '7', '8', '9','10','11','12','13','14']
        
        # Create a list of colors in the correct order
        colors_in_order = [pallette_class_segment[class_id] for class_id in class_ids_order]

        vis_param_lc = {'min': 1, 'max': 14, 'palette': colors_in_order}
        class_name_lc = {
            '1': 'forest_trees',
            '2': 'shrubland',
            '3': 'grassland',
            '4': 'openland',
            '5': 'waterbody_wet_area',
            '6': 'plantation',
            '7': 'gray_infrastructure',
            '8': 'oil_palm',
            '9': 'cropland',
            '10':'waterbody',
            '11': 'wetlands',
            '12': 'forest_trees_regrowth',
            '13': 'historical_treeloss_10years',
            '14': 'paddy_irrigated',
        }

        legend_class = {k:{'name':v, 'color':pallette_class_segment[k]} for k,v in class_name_lc.items()}

        return {'legend_class':legend_class,
                'vis_param_lc':vis_param_lc}



    