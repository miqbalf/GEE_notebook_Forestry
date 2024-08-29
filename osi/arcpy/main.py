import os
import arcpy
from .utils import safe_get_data_source

class ArcpyOps:
    def __init__(self, project_path_arcgis, map_name_arcgis):
        # fetch the arcgis project path object
        self.project_path_arcgis = project_path_arcgis
        self.project = arcpy.mp.ArcGISProject(self.project_path_arcgis)

        # selection map based on project to look at the existing layer
        # map_list_name = [f.name for f in self.project.listMaps()]
        # print(f'all_maps in project: {map_list_name}')
        self.map_name_arcgis = map_name_arcgis
        print(f'we will select the map for {self.map_name_arcgis}')
        self.map = [map for map in self.project.listMaps() if map.name == self.map_name_arcgis][0]
        self.list_layers = self.map.listLayers()
        self.list_source_layers_in_map = [safe_get_data_source(layer) for layer in self.list_layers]

    # option-1 select from existing layer
    def selecting_layer(self, name_layer):
        layer_selected = [shp for shp in self.map.listLayers() if shp.name == name_layer][0]
        return layer_selected
    
    # option-2 if we want to add the data as layer from path and adding the layer programmatically
    # prev. example, let's try for this training points (sample) to be added as layer in our current map
    def select_adding_layer(self,path_shp):
        if os.path.normpath(path_shp) not in self.list_source_layers_in_map:
            layer = self.map.addDataFromPath(path_shp)
            print(f'adding {layer.name}')
            AOIt_shp = layer.dataSource
            print(f'path of the AOI: {AOIt_shp}')
            return {'layer_path':AOIt_shp,
                    'layer': layer}
        else:
            print(f'layer of {path_shp} is already added, check it on the map, save it in the same path if you edited')
            
            filtered_layers = []
            path_shp_normalized = os.path.normpath(path_shp)  # Normalize the path for comparison

            for l in self.list_layers:
                # Skip if not a feature layer
                if not l.isFeatureLayer:
                    continue  # Skip to the next iteration if it's not a feature layer
                
                # Check if the data source matches the normalized path
                if l.dataSource == path_shp_normalized:
                    filtered_layers.append(l) 

            layer = filtered_layers[0]

            return {'layer': layer,
                    'layer_path':path_shp}
        
    def adding_ee_to_arcgisPro(self, ee_image, vis_params, layer_name):
        map_id_dict = ee_image.getMapId(vis_params)
        url_tiles  = map_id_dict['tile_fetcher'].url_format
        print(url_tiles)
        
        list_name_layers_in_map = [layer.name for layer in self.map.listLayers()]
        if layer_name not in list_name_layers_in_map:
            arcgis_layer = self.map.addDataFromPath(url_tiles)
            arcgis_layer.name = layer_name
        else:
            print(f'removing and re-adding the layer name: {layer_name}')
            arcgis_layer = self.map.removeLayer([layer for layer in self.map.listLayers() if layer.name == layer_name][0])
            arcgis_layer = self.map.addDataFromPath(url_tiles)
            arcgis_layer.name = layer_name
            print(f'layer re-added: {layer_name}')
            
        return arcgis_layer


        

    
    