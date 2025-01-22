import ee
from ..spectral_indices.utils import assigning_band
from .utils import add_classes, add_images, select_band_if_exists, unmasked_helper
from ..legends.utils import legends_obj_creation

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

        self.open_land = config['open_land']
        self.shrub_grass = config['shrub_grass']
        self.yrf_forest = config['yrf_forest']
        self.high_forest = config['high_forest']
        self.AOI_img = config['AOI_img']
        self.AOI = config['AOI']
        self.band_name_image = config['band_name_image']

        self.class_name_map_color = {
            '1': '#ffe3b3',
            '2': '#ffff33',
            '3': '#F89696',
            '4': '#09ab0c',
            '5': '#83ff5a',
            '6': '#ff0004',
            '7': '#ff0abe',
            '8': '#ff8a1d',
            '9': '#1900ff',
            '10': '#e6e6fa',
            '11': '#FFFFFF',
            '12': '#4B0082',
            '13': '#8B4513',
            '14': '#DAA520'
        }

        # list_all_id_int = [int(k) for k,v in self.class_name_map_color.items()]
        
        # # Define the order of class IDs only for FCD
        # class_ids_order_FCD_num = sorted(list_all_id_int)
        # class_ids_order_FCD = [str(num_id) for num_id in class_ids_order_FCD_num]
        
        # # Create a list of colors in the correct order
        # colors_in_order_FCD = [self.class_name_map_color[class_id] for class_id in class_ids_order_FCD]
        
        # # Set the min and max values based on your class IDs
        # self.vis_param_merged = {
        #     'min': min(class_ids_order_FCD_num),
        #     'max': len(class_ids_order_FCD_num),
        #     'palette': colors_in_order_FCD
        # }

        self.class_name_map = {
            '1': 'Shrubland_Go-Zone',
            '2': 'Grassland_Go-Zone',
            '3': 'Openland_Go-Zone',
            '4': 'High density Forest',
            '5': 'Low - Medium density Forest',
            '6': 'Regrowth High Density Forest from deforested (historical)',
            '7': 'Regrowth Low Density Forest from deforested (historical)',
            '8': 'Historical deforestation (10 years rule)',
            '9': 'Water Body',
            '10':'Plantation_No_Go-Zone',
            '11': 'Infrastructure_No_Go-Zone',
            '12': 'Oil_palm_No_Go-Zone',
            '13': 'Cropland_Go-Zone',
            '14': 'Paddy_irrigated_Go-Zone',
        }

        legend = legends_obj_creation(self.class_name_map_color, self.class_name_map)
        legend_class = legend['legend_class']
        vis_param_lc = legend['vis_param']
        self.vis_param_merged = vis_param_lc
        self.legend_class = legend_class

        # self.legend_class = {k:{'name':v, 'color':self.class_name_map_color[k]} for k,v in self.class_name_map.items()}

    def restrict_zone_from_lc(self, list_class_lc = []):
        print('you are restricting the zone information legend and visualization list in this {list_class_lc}')
        #check restricted zone for new item legend from land cover (filter only on existing class in AOI)
        pairing_lc_zone = {'1': ['4','5','6','7'], # possibility outcome from lc (ML) to hansen data
                   '2': ['1', '8'],
                   '3': ['2','8'],
                   '4': ['3','8'],
                   '5': ['9'],
                   '6': ['10'],
                   '7': ['11'],
                   '8': ['12'],
                   '9': ['13'],
                   '10': ['9'],
                   '11': ['9'],
                   '12': ['4','5','6','7'],
                   '13': ['8'], # this actually needs to recheck/ revisit
                   '14': ['14'] }
        
        if list_class_lc != []:
            # example [1, 2, 3, 4]
            # will give us:
            '''
            {'1': ['4', '5', '6', '7'],
                '2': ['1', '8'],
                '3': ['2', '8'],
                '4': ['3', '8']}
            '''
            filtered_pair_lc_zone = {k: v for k, v in pairing_lc_zone.items() if k in [str(num) for num in list_class_lc]}
            init_v = []
            for k,v in filtered_pair_lc_zone.items():
                # print(v)
                init_v  = init_v + v 
            list_set_zone = list(set(init_v))

            #ensuring they are str num
            str_list_class_restrict = [str(id_class) for id_class in list_set_zone]
            # filtered based on id class
            self.class_name_map_color = {k:v for k,v in self.class_name_map_color.items() if str(k) in str_list_class_restrict}
            self.class_name_map = {k:v for k,v in self.class_name_map.items() if str(k) in str_list_class_restrict}
            legend = legends_obj_creation(self.class_name_map_color, self.class_name_map)
            legend_class = legend['legend_class']
            vis_param_lc = legend['vis_param']
            self.vis_param_merged = vis_param_lc
            self.legend_class = legend_class
        else:
            print('no list specified for the restriction from land cover to zone')

       
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
        
        print(f'Adding the map of Shrubland, FCD <  {self.yrf_forest}% and FCD >= {self.shrub_grass}%')
        #Shrubland
        Shrubland = self.FCD.mask(self.FCD.lt(self.yrf_forest).And(self.FCD.gte(self.shrub_grass)))#                                                            .And(unmaskedWaterAOI)
        
        print(f'Adding the map of Grassland or Openland, FCD  < {self.shrub_grass}%')
        #Grassland will be differentiated with openland
        Grassland = self.FCD.mask(self.FCD.lt(self.shrub_grass).And(self.FCD.gte(self.open_land))).And(unmaskedWaterAOI)
        Openland = self.FCD.mask(self.FCD.lt(self.open_land)).And(unmaskedWaterAOI)
        
        hiforest_masked = AllForest

        print('Processing - the zoning classification')
        highForestOnly = ee.Image(assigning_band(self.band_name_image,1,hiforest_masked.clip(self.AOI)))

        # Unmasked the forest loss 10 years rule
        unmaskedLoss = self.AOI_img.unmask().updateMask(minLoss.mask().Not()).clip(self.AOI)
        highBaselineF = hiforest_masked.And(unmaskedLoss)
        #Map.addLayer(highBaselineF,{'palette':hi_forest},'High baseline (Forest)')
        # assigning class band 6
        highf_edited = ee.Image(assigning_band(self.band_name_image,6,highBaselineF)) #high baseline forest - 2
        ##################################################
    
        ####### Get the overlay information of HighBaseline and Tree Cover Loss (Hansen), e.g., Young Regenerating Forest
        HiForestAndLoss = self.AOI_img.And(hiforest_masked.And(minLoss)) #minLoss is the actual TCL without overlaying with Sentinel
        tenyrfl_edited = ee.Image(assigning_band(self.band_name_image,3,HiForestAndLoss)) #tenyears rule not pass and high baseline - 3
        ##############################################
    
        ###### Get the 10 years data only that is not overlay with Sentinel High baseline (Forest) #############
        # Create a helper mask indicating where the smaller areas maskhiFL, distinguish only the highbaseline and TCL (mask) and assign mask as 1
        maskHiFL = HiForestAndLoss.mask()
        
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
        # assign the Class into no. 8 - Final Result
        tenyrule_edited = ee.Image(assigning_band(self.band_name_image,8,tenYearsRule)) #tenyears rule not pass
        ###############################################
    
        # Use hansen data instead - better result, no need to adjust threshold and water body not change for long time
        # hansen water will be override in the machine learning version
        WaterMask = gfc.select(['datamask']).rename('datamask').eq(2)
        waterinAOI = self.AOI_img.mask().updateMask(WaterMask)
        water_edited = ee.Image(assigning_band(self.band_name_image,9,waterinAOI)).clip(self.AOI)
        # unmasked the water (hansen)
        unmaskedWaterAOI = self.AOI_img.unmask().updateMask(waterinAOI.mask().Not()).clip(self.AOI)
    
        ###############################################
        ######### Go Zone - outside (forest, forest - TCL, no-forest TCL, WaterBody)
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

        
        ## GO ZONE
        Shrubland_gozone = Shrubland.And(goZone_edited).select(['pixel'])
        Shrubland_gozone = ee.Image(assigning_band(self.band_name_image,1,Shrubland_gozone))

        Grassland_gozone = Grassland.And(goZone_edited).select(['pixel'])
        Grassland_gozone = ee.Image(assigning_band(self.band_name_image,2,Grassland_gozone))

        Openland_gozone = Openland.And(goZone_edited).select(['pixel'])
        Openland_gozone = ee.Image(assigning_band(self.band_name_image,3,Openland_gozone))
        ############################

        ### High Baseline
        # HighForestDense = FCD.mask(FCD.gte(high_forest).And(unmaskedWaterAOI))
        HighForestDense_no10yrs = HighForestDense.And(highf_edited).select(['pixel'])
        HighForestDense_no10yrs = ee.Image(assigning_band(self.band_name_image,4,HighForestDense_no10yrs))

        #YRFForestDense = FCD.mask(FCD.gte(yrf_forest).And(unmaskedWaterAOI).And(FCD.lt(high_forest)))
        YRFForestDense_no10yrs = YRFForestDense.And(highf_edited).select(['pixel'])
        YRFForestDense_no10yrs = ee.Image(assigning_band(self.band_name_image,5,YRFForestDense_no10yrs))
        
        HighForestDense_10yrs = HighForestDense.And(tenyrfl_edited).select(['pixel'])
        HighForestDense_10yrs = ee.Image(assigning_band(self.band_name_image,6,HighForestDense_10yrs))
        
        YRFForestDense_10yrs = YRFForestDense.And(tenyrfl_edited).select(['pixel'])
        YRFForestDense_10yrs = ee.Image(assigning_band(self.band_name_image,7,YRFForestDense_10yrs))
                
        # Filter the images based on the 'Class' band
        openland_gozone = Openland_gozone.select([self.band_name_image])
        grassland_gozone = Grassland_gozone.select([self.band_name_image])
        shrubland_gozone = Shrubland_gozone.select([self.band_name_image])
        yrf_forest_dense_no10yrs = YRFForestDense_no10yrs.select([self.band_name_image])
        high_forest_dense_no10yrs = HighForestDense_no10yrs.select(self.band_name_image)       
        yrf_forest_dense_10yrs = YRFForestDense_10yrs.select([self.band_name_image])
        high_forest_dense_10yrs = HighForestDense_10yrs.select([self.band_name_image])
        No_pass_historical_years_rule = tenyrule_edited.select([self.band_name_image]) #check above, tenyrule_edited should have class 8
        Water_Un_plantable = water_edited.select([self.band_name_image]) #check above water_edited should have class 9
        
        empty_image = ee.Image.constant(0).rename(self.band_name_image)

        # Create a list of images excluding the 'empty_image'
        image_list = [
            shrubland_gozone, #1
            grassland_gozone, #2
            openland_gozone, #3
            high_forest_dense_no10yrs, #4
            yrf_forest_dense_no10yrs, #5
            high_forest_dense_10yrs, #6
            yrf_forest_dense_10yrs, #7
            No_pass_historical_years_rule, #8
            Water_Un_plantable #9
        ]

        # Create an ImageCollection from the list of images
        image_collection = ee.ImageCollection(image_list)

        # Apply the add_classes function to each image in the collection while merging them into the 'empty_image'
        result_collection = image_collection.map(lambda image: add_classes(image, empty_image))

        # Merge all the images in the result_collection using ee.ImageCollection.iterate()
        merged_image = ee.Image(result_collection.iterate(add_images, empty_image))
        
        # Cast the merged image to Int32 and set the original Class band name
        merged_image = merged_image.toInt32().rename(self.band_name_image)
        merged_image = merged_image.clip(self.AOI)
        print('finish processing, merging all the zone into one image')

        # NOW THIS IS FOR LC, JUST DISPLAYING ONLY AND COMPARING THE RESULT LATER
        #FCD LC for confusing matrix
        forest_lc_fcd = AllForest.multiply(0).add(1).rename('classification').select(['classification'])
        shrub_lc_fcd = Shrubland.multiply(0).add(2).rename('classification').select(['classification'])
        grass_lc_fcd = Grassland.multiply(0).add(3).rename('classification').select(['classification'])
        openland_lc_fcd = Openland.multiply(0).add(4).rename('classification').select(['classification'])
        water_lc_fcd = Water_Un_plantable.multiply(0).add(5).rename('classification').select(['classification'])

        # Create a list of images excluding the 'empty_image'
        image_list_lc_fcd = [
            forest_lc_fcd,
            shrub_lc_fcd,
            grass_lc_fcd,
            openland_lc_fcd,
            water_lc_fcd,
        ]

        # Create an ImageCollection from the list of images
        image_collection_fcd_lc = ee.ImageCollection(image_list_lc_fcd)

        empty_image_lc = ee.Image.constant(0).rename('Class')

        # Apply the add_classes function to each image in the collection while merging them into the 'empty_image'
        result_collection_fcd_lc = image_collection_fcd_lc.map(lambda image: add_classes(image, empty_image_lc))

        # Merge all the images in the result_collection using ee.ImageCollection.iterate()
        fcd_class_lc_image = ee.Image(result_collection_fcd_lc.iterate(add_images, empty_image))

        # Cast the merged image to Int32 and set the original Class band name
        fcd_class_lc_image = fcd_class_lc_image.toInt32().rename('classification')
        fcd_class_lc_image = fcd_class_lc_image.clip(self.AOI)

        pallette_class_segment_lc = ['#83ff5a',
                                    '#ffe3b3',
                                    '#ffff33',
                                    '#f89696',
                                    '#1900ff',
                                    ]
        vis_param_segment_lc = {'min': 1, 'max': 5, 'palette': pallette_class_segment_lc}
               
        return {'all_zone': merged_image,
                # 'vis_param_merged': vis_params_FCD,
                # 'class_name_map': class_name_map,
                # 'legend_class': legend_class,
                'openland_gozone': openland_gozone,
                'grassland_gozone': grassland_gozone,
                'shrubland_gozone': shrubland_gozone,
                'yrf_forest_dense_no10yrs': yrf_forest_dense_no10yrs,
                'high_forest_dense_no10yrs': high_forest_dense_no10yrs,
                'yrf_forest_dense_10yrs': yrf_forest_dense_10yrs,
                'high_forest_dense_10yrs':   high_forest_dense_10yrs,
                'No_pass_historical_years_rule':  No_pass_historical_years_rule,
                'Water_Un_plantable':  Water_Un_plantable,
                
                # this one are for landcover, not zone, we need this because its not overlap with 10 years rule, and for landcover accuracy assessment
                'AllForest':AllForest,
                'Shrubland':Shrubland,
                'Grassland':Grassland,
                'Openland':Openland,
                'fcd_class_lc_image':fcd_class_lc_image,
                'vis_param_segment_lc':vis_param_segment_lc,

                # for the overlay of historical hansen and ML
                'HighForestDense':HighForestDense, # to breakdown high density forest and med. density forest
                }
    
    def assign_zone_ml(self, lc_image_ml, minLoss, AOI_img, HighForestDense):
        
        forest_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(1))
        shrub_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(2))
        grass_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(3))
        openland_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(4))
        water_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(5))
        plantation_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(6))
        infrastructure_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(7))
        oil_palm_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(8))
        cropland_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(9))
        paddy_irigated_masked = lc_image_ml.updateMask(lc_image_ml.select(['classification']).eq(14))

        #sub-forest considering the fcd threshold of high density forest, regardless the ML method
        # HighForestDense = FCD.mask(FCD.gte(high_forest).And(unmaskedWaterAOI))
        unmaskedHighForest = AOI_img.unmask().updateMask(HighForestDense.mask().Not()).clip(self.AOI)
        yrf_forest = forest_masked.And(unmaskedHighForest)
        high_forest_fix = HighForestDense.And(forest_masked)


        ######### general go-zone
        ## Starting to retrieve from 10 TCL unmask
        unmaskedLoss = unmasked_helper(minLoss, AOI_img, self.AOI)
        # Unmasked Forest - the result is all the area outside of forest_masked (Total all forest), and now in no forest
        # maskHiF = forest_masked.mask()
        # maskHiF_inverted = maskHiF.Not()
        # unmaskedHiF = AOI_img.unmask().updateMask(maskHiF_inverted).clip(AOI)
        unmaskedHiF = unmasked_helper(forest_masked, AOI_img, self.AOI)
        # unmasked water
        waterinAOI = water_masked
        unmaskedWaterAOI = unmasked_helper(water_masked, AOI_img, self.AOI)
        # unmasked grey infrastructure
        unmasked_infrastructure = unmasked_helper(infrastructure_masked, AOI_img, self.AOI)
        # unmasked oil palm
        unmasked_oilpalm = unmasked_helper(oil_palm_masked, AOI_img, self.AOI)

        goZone = unmaskedLoss.And(unmaskedHiF).And(unmaskedWaterAOI).And(unmasked_infrastructure).And(unmasked_oilpalm)
        goZone_edited = ee.Image(assigning_band(self.config['band_name_image'],999,goZone))

        # forest category and no 10 years rule
        highBaselineF = forest_masked.And(unmaskedLoss)
        highf_edited = ee.Image(assigning_band(self.config['band_name_image'],111,highBaselineF))

        ####### Get the overlay information of HighBaseline and Tree Cover Loss (Hansen), e.g., Young Regenerating Forest
        HiForestAndLoss = AOI_img.And(forest_masked.And(minLoss)) #minLoss is the actual TCL without overlaying with Sentinel
        tenyrfl_edited = ee.Image(assigning_band(self.band_name_image,888,HiForestAndLoss))
        # arc_ops.adding_ee_to_arcgisPro(tenyrfl_edited.randomVisualizer(),{},'tenyrlfl_edited')

        # Create a helper mask indicating where the smaller areas maskhiFL, distinguish only the highbaseline and TCL (mask) and assign mask as 1
        # Unmask the bigger raster in the areas to get the pixel value for area 'outside' HiFL (High Baseline and Forest Loss)
        unmaskedHiFL = unmasked_helper(HiForestAndLoss, AOI_img, self.AOI)
        #outcome result for 10 years data only that is not overlay with high baseline (Forest) unmaskedHiFL is Area that is not Forest Sentinel############
        tenYearsRule = unmaskedHiFL.And(minLoss)
        tenyrule_edited = ee.Image(assigning_band(self.band_name_image,8,tenYearsRule))
        # arc_ops.adding_ee_to_arcgisPro(tenyrule_edited.randomVisualizer(),{},'tenyrule_edited')

        #re-acquired the same method for 10 years rule data (GFW or Hansen data (pixel 30m))
        #assigning to zones:
        ## GO ZONE
        Shrubland_gozone = shrub_masked.And(goZone_edited).select(['pixel'])
        Shrubland_gozone = ee.Image(assigning_band(self.config['band_name_image'],1,Shrubland_gozone))

        Grassland_gozone = grass_masked.And(goZone_edited).select(['pixel'])
        Grassland_gozone = ee.Image(assigning_band(self.config['band_name_image'],2,Grassland_gozone))

        Openland_gozone = openland_masked.And(goZone_edited).select(['pixel'])
        Openland_gozone = ee.Image(assigning_band(self.config['band_name_image'],3,Openland_gozone))

        Openland_gozone = openland_masked.And(goZone_edited).select(['pixel'])
        Openland_gozone = ee.Image(assigning_band(self.config['band_name_image'],3,Openland_gozone))

        Cropland_Gozone = cropland_masked.And(goZone_edited).select(['pixel'])
        Cropland_Gozone = ee.Image(assigning_band(self.config['band_name_image'],13,Cropland_Gozone))

        Paddy_Gozone = paddy_irigated_masked.And(goZone_edited).select(['pixel'])
        Paddy_Gozone = ee.Image(assigning_band(self.config['band_name_image'],14,Paddy_Gozone))

        ## NO GO additional
        Plantation_noGozone = plantation_masked.And(goZone_edited).select(['pixel'])
        Plantation_noGozone = ee.Image(assigning_band(self.config['band_name_image'],10,Plantation_noGozone))

        Infrastructure_noGozone = infrastructure_masked.And(goZone_edited).select(['pixel'])
        Infrastructure_noGozone = ee.Image(assigning_band(self.config['band_name_image'],11,Infrastructure_noGozone))

        Oilpalm_noGozone = oil_palm_masked.And(goZone_edited).select(['pixel'])
        Oilpalm_noGozone = ee.Image(assigning_band(self.config['band_name_image'],12,Oilpalm_noGozone))

        # highbaseline
        # HighForestDense = FCD.mask(FCD.gte(high_forest).And(unmaskedWaterAOI))
        HighForestDense_no10yrs = HighForestDense.And(highf_edited).select(['pixel'])
        HighForestDense_no10yrs = ee.Image(assigning_band(self.config['band_name_image'],4,HighForestDense_no10yrs))

        #YRFForestDense = FCD.mask(FCD.gte(yrf_forest).And(unmaskedWaterAOI).And(FCD.lt(high_forest)))
        YRFForestDense_no10yrs = yrf_forest.And(highf_edited).select(['pixel'])
        YRFForestDense_no10yrs = ee.Image(assigning_band(self.config['band_name_image'],5,YRFForestDense_no10yrs))
        ##########################

        # high baseline regrowth
        HighForestDense_10yrs = HighForestDense.And(tenyrfl_edited).select(['pixel'])
        HighForestDense_10yrs = ee.Image(assigning_band(self.config['band_name_image'],6,HighForestDense_10yrs))

        YRFForestDense_10yrs = yrf_forest.And(tenyrfl_edited).select(['pixel'])
        YRFForestDense_10yrs = ee.Image(assigning_band(self.config['band_name_image'],7,YRFForestDense_10yrs))
        ############################

        # 10 years rule, straight forward
        # tenyrule_edited = ee.Image(assigning_band(band_name_image,8,tenYearsRule)) #tenyears rule not pass - 8  # already hard-coded set in the previous function
        No_pass_historical_years_rule = tenyrule_edited.select([self.config['band_name_image']])

        # Filter the images based on the 'Class' band, and add them one by one on map canvas!!!!!!!!!!!!!!!!!!!! # just comment this Map.addLayer if you want not to display one by one
        openland_gozone = Openland_gozone.select([self.config['band_name_image']])
        # Map.addLayer(openland_gozone,{'palette': ['#F89696']},'Open land - Go Zone')

        grassland_gozone = Grassland_gozone.select([self.config['band_name_image']])
        # Map.addLayer(grassland_gozone,{'palette': ['#ffff33']},'Grass land - Go Zone')

        shrubland_gozone = Shrubland_gozone.select([self.config['band_name_image']])
        # Map.addLayer(shrubland_gozone,{'palette': ['#ffe3b3']},'Shrub land - Go Zone')

        yrf_forest_dense_no10yrs = YRFForestDense_no10yrs.select([self.config['band_name_image']])
        # Map.addLayer(yrf_forest_dense_no10yrs,{'palette': ['#83ff5a']},'Low-Med Forest')

        high_forest_dense_no10yrs = HighForestDense_no10yrs.select(self.config['band_name_image'])
        # Map.addLayer(high_forest_dense_no10yrs,{'palette': ['#09ab0c']},'High- Density Forest')

        yrf_forest_dense_10yrs = YRFForestDense_10yrs.select([self.config['band_name_image']])
        # Map.addLayer(yrf_forest_dense_10yrs,{'palette': ['#ff0abe']},'Re-growth Low-Med Density Forest')

        high_forest_dense_10yrs = HighForestDense_10yrs.select([self.config['band_name_image']])
        # Map.addLayer(high_forest_dense_10yrs,{'palette': ['#ff0004']},'Re-growth High Density Forest')

        No_pass_historical_years_rule = tenyrule_edited.select([self.config['band_name_image']])
        # Map.addLayer(No_pass_historical_years_rule,{'palette': ['#ff8a1d']},'Historical deforestation no regrowth (3 or 10 years)')

        # since there are case water from mining (overlap 10 years rule with water), we should unmasked first
        unmasked10years = AOI_img.unmask().updateMask(No_pass_historical_years_rule.mask().Not()).clip(self.AOI)
        water_no_10yr = waterinAOI.And(unmasked10years).And(unmasked10years)
        Water_Un_plantable = ee.Image(assigning_band(self.config['band_name_image'],9,water_no_10yr)).select([self.config['band_name_image']])
        # such a headache to forgetting things that to merge, need to be in Class and also need to be selected

        # Map.addLayer(Water_Un_plantable,{'palette': ['#1900ff']},'Water body (unplantable)')

        # Example band name to check
        band_name = self.config['band_name_image']
        
        # Select images if the band exists
        plantation_noGozone = select_band_if_exists(Plantation_noGozone, band_name)
        infrastructure_noGozone = select_band_if_exists(Infrastructure_noGozone, band_name)
        oilpalm_noGozone = select_band_if_exists(Oilpalm_noGozone, band_name)
        cropland_Gozone = select_band_if_exists(Cropland_Gozone, band_name)
        paddy_Gozone = select_band_if_exists(Paddy_Gozone, band_name)

        empty_image = ee.Image.constant(0).rename(self.config['band_name_image'])

        image_list_result = [
            openland_gozone,
            grassland_gozone,
            shrubland_gozone,
            high_forest_dense_no10yrs,
            yrf_forest_dense_no10yrs,
            high_forest_dense_10yrs,
            yrf_forest_dense_10yrs,
            No_pass_historical_years_rule,
            Water_Un_plantable,
            plantation_noGozone,
            infrastructure_noGozone,
            oilpalm_noGozone,
            cropland_Gozone,
            paddy_Gozone

        ]

        # Remove None entries from the list
        image_list_result = [img for img in image_list_result if img is not None]

        # Create an ImageCollection from the list of images
        image_collection_result = ee.ImageCollection(image_list_result)

        # Apply the add_classes function to each image in the collection while merging them into the 'empty_image'
        result_collection_with_class = image_collection_result.map(lambda image: add_classes(image, empty_image))

        # Merge all the images in the result_collection using ee.ImageCollection.iterate()
        merged_image_result = ee.Image(result_collection_with_class.iterate(add_images, empty_image))

        # Cast the merged image to Int32 and set the original Class band name
        merged_image_result = merged_image_result.toInt32().rename(self.config['band_name_image'])
        merged_image_result = merged_image_result.clip(self.AOI)
        final_zone_map = merged_image_result

        return final_zone_map
