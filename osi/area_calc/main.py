from gee_lib.osi.spectral_indices.utils import assigning_band
import time
import ee

class CalcAreaClass:
    def __init__(self, config, calc_image=None):
        self.config = config
        self.AOI = config['AOI']
        scale = None
        if config['I_satellite'] == 'Sentinel':
            scale = 10
        elif config['I_satellite'] == 'Landsat':
            scale = 30
        elif config['I_satellite'] == 'Planet':
            scale = 5
        self.scale = scale
        self.AOI_client = self.AOI.getInfo()

        self.list_id = [i['properties']['id'] for i in self.AOI_client['features']]

        self.calc_image = calc_image
        self.calc_pix = ee.Image(assigning_band('pix',1,self.calc_image))
        # print(list_id)
        
        self.list_geom = [i['geometry'] for i in self.AOI_client['features']]
        # print(list_geom)
        
        self.class_list = ['1','2','3','4','5','6','7','8']
        # print(class_list)
    
    # Define calc_area
    def calc_area_zone(self, class_zone, feature):
        geometry = feature.geometry()
        feature_id = feature.get('id')  # hard-coded the field name here is still 'id'
        # geometry = feature
        class_mask = self.calc_image.select('Class').eq(ee.Number.parse(class_zone))
        
        masked_imaged = self.calc_pix.select('pix').mask(class_mask)
    
        zone_area_image = masked_imaged.multiply(ee.Image.pixelArea()).divide(10000)
        
        class_pixel_count = zone_area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=self.scale
        ).get('pix')
    
        result = ee.Feature(geometry, {class_zone: class_pixel_count, 'feature_id': feature_id})
        # result = {class_zone: class_pixel_count.getInfo()}
        # result = ee.Feature({class_zone: class_pixel_count})
        return result

    def calc_all_zone(self):

        s = time.perf_counter()
        # Convert your AOI to an Earth Engine FeatureCollection
        # aoi_fc = ee.FeatureCollection(AOI_client['features'])
        aoi_fc = self.AOI
        
        # geom_list_ee = ee.List(list_geom)
        
        # Iterate over each class in class_list
        results = []
        for class_zone in self.class_list:
            # Apply .map to the feature collection for each class
            class_results = aoi_fc.map(lambda feature: self.calc_area_zone(class_zone, feature))
            # class_results = geom_list_ee.map(lambda geometry: calc_area_zone(class_zone, geometry))
            
            # Append the results for the current class to the overall results list
            results.append(class_results)
        
        # Convert the results to a Python list
        final_results = [result.getInfo() for result in results]
        
        # Print or use final_results as needed
        # print(final_results)
        
        elapsed = time.perf_counter() - s
        print(f" executed in {elapsed:0.2f} seconds.")
        return final_results
    def run_calc_per_id(self):
        # this method to clean the result into a better human readable and api-json serializable
        list_dict_zone_id = []
        for i in self.calc_all_zone():
            for j in i['features']:
                # print(j['properties'])
                list_dict_zone_id.append(j['properties'])
        
        # list_id
        dict_id_zone = {}
        for i in self.list_id:
            init_dict = {}
            for j in list_dict_zone_id:
                
                if j['feature_id'] == i:
                    for k,v in j.items():
                        if k != 'feature_id':
                            init_dict[k] = v
                dict_id_zone[i] = init_dict
        
        # print(dict_id_zone)
        
        # adjusting dict_id
        adj_dict_id_zone = {}
        for k,v in dict_id_zone.items():
            init_dict = {}
            for j,l in v.items():
                init_dict[j] = round(l,2)
            adj_dict_id_zone[k] = init_dict
        print(adj_dict_id_zone)
        return adj_dict_id_zone