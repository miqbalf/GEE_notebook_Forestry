import ee
from gee_lib.osi.spectral_indices.utils import assigning_band

class AssignClassZone:
    def __init__(self, config, *args, **kwargs):
        self.config = config
        self.FCD = None
        self.args = args
        self.kwargs = kwargs
        fcd_selected = config['fcd_selected']
        if fcd_selected == 11:
            self.FCD = kwargs['FCD1_1']
        elif fcd_selected == 21:
            self.FCD = kwargs['FCD2_1']
        elif fcd_selected == 12:
            self.FCD = kwargs['FCD1_2']
        elif fcd_selected == 22:
            self.FCD = kwargs['FCD1_2']

        self.shrub_grass = config['shrub_grass']
        self.yrf_forest = config['yrf_forest']
        self.high_forest = config['high_forest']
        self.AOI_img = config['AOI_img']
        self.AOI = config['AOI']
        self.band_name_image = config['band_name_image']
    
    def assigning_fcd_class(self, gfc, minLoss):
        # Starting to create threshold for labeling
        WaterMask = gfc.select(['datamask']).rename('datamask').eq(2)
        WaterinAOI = self.AOI_img.mask().updateMask(WaterMask)
        # unmasked the water (hansen)
        unmaskedWaterAOI = self.AOI_img.unmask().updateMask(WaterinAOI.mask().Not()).clip(self.AOI)
        print(f'Adding the map of Forest, FCD >= {self.yrf_forest}% and mask only if not water in area (hansen) and NDWI')
        #Forest
        AllForest = self.FCD.mask(self.FCD.gte(self.yrf_forest)).And(unmaskedWaterAOI)
        HighForestDense = self.FCD.mask(self.FCD.gte(self.high_forest)).And(unmaskedWaterAOI)
        YRFForestDense = self.FCD.mask(self.FCD.gte(self.yrf_forest).And(self.FCD.lt(self.high_forest))).And(unmaskedWaterAOI)
        #Map.addLayer(AllForest,{'min':0 ,'max':100}, 'AllForest')
        # Map.addLayer(HighForestDense, {'min':0 ,'max':100}, f'Forest (FCD >= {high_forest}%)', False)
        
        # Map.addLayer(YRFForestDense, {'min':0 ,'max':100}, f'Forest (FCD >= {yrf_forest}%) and < {high_forest}%', False)
        
        print(f'Adding the map of Shrubland, FCD <  {self.yrf_forest}% and FCD >= {self.shrub_grass}%')
        #Shrubland
        Shrubland = self.FCD.mask(self.FCD.lt(self.yrf_forest).And(self.FCD.gte(self.shrub_grass)))#                                                            .And(unmaskedWaterAOI)
        # Map.addLayer(Shrubland, {'min':0 ,'max':100}, f'Shrubland ({self.shrub_grass}% <= FCD < {yrf_forest}%)', False)
        
        print(f'Adding the map of Grassland or Openland, FCD  < {self.shrub_grass}%')
        #Grassland / openland
        Grassland = self.FCD.mask(self.FCD.lt(self.shrub_grass)).And(unmaskedWaterAOI)
        # Map.addLayer(Grassland, {'min':0 ,'max':100}, f'Grassland (FCD < {shrub_grass})', False)
        
        hiforest_masked = AllForest

        print('Processing - the zoning classification')
        highForestOnly = ee.Image(assigning_band(self.band_name_image,1,hiforest_masked.clip(self.AOI)))

        ######### Zone 6-7 - High Baseline Forest: That does not have (overlaid with) TCL
        # Unmasked the forest loss 10 years rule
        unmaskedLoss = self.AOI_img.unmask().updateMask(minLoss.mask().Not()).clip(self.AOI)
        highBaselineF = hiforest_masked.And(unmaskedLoss)
        #Map.addLayer(highBaselineF,{'palette':hi_forest},'High baseline (Forest)')
        # assigning class band 6
        highf_edited = ee.Image(assigning_band(self.band_name_image,6,highBaselineF)) #high baseline forest - 2
        ##################################################
    
        ######### Zone 4-5: High Forest and Loss (e.g., Young Regenerating Forest)
        ####### Get the overlay information of HighBaseline (Sentinel) and Tree Cover Loss (Hansen), e.g., Young Regenerating Forest
        HiForestAndLoss = self.AOI_img.And(hiforest_masked.And(minLoss)) #minLoss is the actual TCL without overlaying with Sentinel
        #Map.addLayer(HiForestAndLoss,{'palette': '#FF0000'},"High Baseline and not pass 10 years rule")
        # Final Result for High Forest and TCL -> Class number: 3
        tenyrfl_edited = ee.Image(assigning_band(self.band_name_image,3,HiForestAndLoss)) #tenyears rule not pass and high baseline - 3
        ##############################################
    
        ######### Zone 3: Tree Cover Loss on the current low baseline (Sentinel)
        ###### Get the 10 years data only that is not overlay with Sentinel High baseline (Forest) #############
        # Create a helper mask indicating where the smaller areas maskhiFL, distinguish only the highbaseline and TCL (mask) and assign mask as 1
        maskHiFL = HiForestAndLoss.mask()
        #Map.addLayer(maskHiFL)
        # Helper - Invert the mask to get the areas where the smaller raster is absent - get only area outside high forest and loss, and mask from 1 to 0
        # invert mask just to get the number from 0 to 1 or vice versa -> .Not()
        maskHiFL_inverted = maskHiFL.Not()
        #Map.addLayer(maskHiFL_inverted)
        # Unmask the bigger raster in the areas to get the pixel value for area 'outside' HiFL (High Baseline and Forest Loss)
        unmaskedHiFL = self.AOI_img.unmask().updateMask(maskHiFL_inverted).clip(self.AOI)
        #Map.addLayer(unmaskedHiFL)
        #outcome result for 10 years data only that is not overlay with Sentinel High baseline (Forest) unmaskedHiFL is Area that is not Forest Sentinel############
        tenYearsRule = unmaskedHiFL.And(minLoss)
        #Map.addLayer(tenYearsRule,{'palette': '#FFA500'},"10 Years Rule - not OK")
        # assign the Class into no. 3 - Final Result
        tenyrule_edited = ee.Image(assigning_band(self.band_name_image,3,tenYearsRule)) #tenyears rule not pass - 3
        ###############################################
    
        ######### Zone 8: Water Body - NDWI Sentinel
        # from a function, output is already assigned in a band name: Class : 5
        #water_list = applying_sentinel_water(s2_sr_median, ndwi_hi)
        #waterinAOI = water_list[0]
        #water_edited = water_list[1]
        # Use hansen data instead - better result, no need to adjust threshold and water body not change for long time
        WaterMask = gfc.select(['datamask']).rename('datamask').eq(2)
        waterinAOI = self.AOI_img.mask().updateMask(WaterMask)
        water_edited = ee.Image(assigning_band(self.band_name_image,8,waterinAOI)).clip(self.AOI)
        # unmasked the water (hansen)
        unmaskedWaterAOI = self.AOI_img.unmask().updateMask(waterinAOI.mask().Not()).clip(self.AOI)
    
        ###############################################
        ######### Zone 1-2: Go Zone - outside (forest, forest - TCL, no-forest TCL, WaterBody)
        # Utils - Similar with above (but easier), unmasked the high forest means that in the end only include area that is not in forest (hiforest_masked)
        maskHiF = hiforest_masked.mask()
        maskHiF_inverted = maskHiF.Not()
        # Unmasked High Forest - the result is all the area outside of hiforest_masked (Total all forest), and now in no forest
        unmaskedHiF = self.AOI_img.unmask().updateMask(maskHiF_inverted).clip(self.AOI)
        # unmasked the water
        #unmaskedWaterAOI = AOI_img.unmask().updateMask(waterinAOI.mask().Not()).clip(AOI)
        goZone = unmaskedLoss.And(unmaskedHiF).And(unmaskedWaterAOI)
        #Map.addLayer(goZone,{'palette':'#FFFF00'},'Go Zone')
        # assigning band - Go Zone
        goZone_edited = ee.Image(assigning_band(self.band_name_image,1,goZone)) #go Zone - 1
        ##############################################
    
        # Map.addLayer(goZone_edited,{'bands': ['Class'],'palette':'#FFFF00'},'Go Zone', False)
        # Map.addLayer(highf_edited,{'bands': ['Class'],'palette':hi_forest},'High baseline (Forest)', False)
        # Map.addLayer(tenyrfl_edited,{'bands': ['Class'],'palette': '#FF0000'},"High Baseline and not pass 10 years rule", False)
        # Map.addLayer(tenyrule_edited,{'bands': ['Class'],'palette': '#FFA500'},"10 Years Rule - not OK", False)
        # Map.addLayer(water_edited,{'bands': ['Class'],'palette': water},"Water in AOI", False)

        # HighForestDense = FCD.mask(FCD.gte(high_forest).And(unmaskedWaterAOI))
        HighForestDense_no10yrs = HighForestDense.And(highf_edited).select(['pixel'])
        HighForestDense_no10yrs = ee.Image(assigning_band(self.band_name_image,7,HighForestDense_no10yrs))

        HighForestDense_10yrs = HighForestDense.And(tenyrfl_edited).select(['pixel'])
        HighForestDense_10yrs = ee.Image(assigning_band(self.band_name_image,5,HighForestDense_10yrs))
        
        #YRFForestDense = FCD.mask(FCD.gte(yrf_forest).And(unmaskedWaterAOI).And(FCD.lt(high_forest)))
        YRFForestDense_no10yrs = YRFForestDense.And(highf_edited).select(['pixel'])
        YRFForestDense_no10yrs = ee.Image(assigning_band(self.band_name_image,6,YRFForestDense_no10yrs))
        
        YRFForestDense_10yrs = YRFForestDense.And(tenyrfl_edited).select(['pixel'])
        YRFForestDense_10yrs = ee.Image(assigning_band(self.band_name_image,4,YRFForestDense_10yrs))
        
        Shrubland_gozone = Shrubland.And(goZone_edited).select(['pixel'])
        Shrubland_gozone = ee.Image(assigning_band(self.band_name_image,2,Shrubland_gozone))
        
        Grassland_gozone = Grassland.And(goZone_edited).select(['pixel'])
        Grassland_gozone = ee.Image(assigning_band(self.band_name_image,1,Grassland_gozone))

        # Filter the images based on the 'Class' band
        grassland_gozone = Grassland_gozone.select([self.band_name_image])
        # Map.addLayer(grassland_gozone,{'palette': ['#ffff33']},'Grass land - Go Zone')
        
        shrubland_gozone = Shrubland_gozone.select([self.band_name_image])
        # Map.addLayer(shrubland_gozone,{'palette': ['#ffe3b3']},'Shrub land - Go Zone')
        
        yrf_forest_dense_no10yrs = YRFForestDense_no10yrs.select([self.band_name_image])
        # Map.addLayer(yrf_forest_dense_no10yrs,{'palette': ['#83ff5a']},'Low-Med Forest')
        
        high_forest_dense_no10yrs = HighForestDense_no10yrs.select(self.band_name_image)
        # Map.addLayer(high_forest_dense_no10yrs,{'palette': ['#09ab0c']},'High- Density Forest')
        
        yrf_forest_dense_10yrs = YRFForestDense_10yrs.select([self.band_name_image])
        # Map.addLayer(yrf_forest_dense_10yrs,{'palette': ['#ff0abe']},'Re-growth Low-Med Density Forest')
        
        high_forest_dense_10yrs = HighForestDense_10yrs.select([self.band_name_image])
        # Map.addLayer(high_forest_dense_10yrs,{'palette': ['#ff0004']},'Re-growth High Density Forest')
        
        No_pass_historical_years_rule = tenyrule_edited.select([self.band_name_image])
        # Map.addLayer(No_pass_historical_years_rule,{'palette': ['#ff8a1d']},'Historical deforestation no regrowth (3 or 10 years)')
        
        Water_Un_plantable = water_edited.select([self.band_name_image])
        # Map.addLayer(Water_Un_plantable,{'palette': ['#1900ff'

        empty_image = ee.Image.constant(0).rename(self.band_name_image)

        def add_classes(image, empty):
            # Cast the image to Int32 to handle NaN and null values
            image = image.unmask(0).toInt32()
            # Set a conditional statement to retain existing class values if non-zero, otherwise use the new class value
            merged_image = empty.where(empty.neq(0), empty).where(image.neq(0), image)
            return merged_image

        # Create a list of images excluding the 'empty_image'
        image_list = [
            grassland_gozone, #1
            shrubland_gozone, #2
            No_pass_historical_years_rule, #3
            yrf_forest_dense_10yrs, #4
            high_forest_dense_10yrs, #5
            yrf_forest_dense_no10yrs, #6
            high_forest_dense_no10yrs, #7
            Water_Un_plantable #8
        ]

        # Create an ImageCollection from the list of images
        image_collection = ee.ImageCollection(image_list)

        # Apply the add_classes function to each image in the collection while merging them into the 'empty_image'
        result_collection = image_collection.map(lambda image: add_classes(image, empty_image))

        # Create a function to add two images element-wise
        def add_images(img1, img2):
            return ee.Image(img1).add(img2)

        # Merge all the images in the result_collection using ee.ImageCollection.iterate()
        merged_image = ee.Image(result_collection.iterate(add_images, empty_image))
        
        # Cast the merged image to Int32 and set the original Class band name
        merged_image = merged_image.toInt32().rename(self.band_name_image)
        merged_image = merged_image.clip(self.AOI)
        print('finish processing, merging all the zone into one image')

        class_name_map_color = {
            '1': '#ffff33',
            '2': '#ffe3b3',
            '3': '#ff8a1d',
            '4': '#ff0abe',
            '5': '#ff0004',
            '6': '#83ff5a',
            '7': '#09ab0c',
            '8': '#1900ff'
        }
        
        # Define the order of class IDs
        class_ids_order = ['1', '2', '3', '4', '5', '6', '7', '8']
        
        # Create a list of colors in the correct order
        colors_in_order = [class_name_map_color[class_id] for class_id in class_ids_order]
        
        # Set the min and max values based on your class IDs
        vis_params = {
            'min': 1,
            'max': 8,
            'palette': colors_in_order
        }

        class_name_map = {
            '2': 'Shrubland_Go-Zone',
            '1': 'Grassland_Go-Zone',
            '7': 'High density Forest',
            '6': 'Low - Medium density Forest',
            '5': 'Regrowth High Density Forest from deforested (historical)',
            '4': 'Regrowth Low Density Forest from deforested (historical)',
            '3': 'Historical deforestation (3 or 10 years rule)',
            '8': 'Water Body'
        }

        legend_class = {k:{'name':v, 'color':class_name_map_color[k]} for k,v in class_name_map.items()}
        

        return {'all_zone': merged_image,
                'vis_param_merged': vis_params,
                'class_name_map': class_name_map,
                'legend_class': legend_class,
               'grassland_gozone': grassland_gozone,
           'shrubland_gozone': shrubland_gozone,
           'yrf_forest_dense_no10yrs': yrf_forest_dense_no10yrs,
           'high_forest_dense_no10yrs': high_forest_dense_no10yrs,
           'yrf_forest_dense_10yrs': yrf_forest_dense_10yrs,
         'high_forest_dense_10yrs':   high_forest_dense_10yrs,
          'No_pass_historical_years_rule':  No_pass_historical_years_rule,
          'Water_Un_plantable':  Water_Un_plantable}