import arcpy

class ArcpyOps:
    def __init__(self, project_path_arcgis, map_name_arcgis):
        # fetch the arcgis project path object
        self.project_path_arcgis = project_path_arcgis
        self.project = arcpy.mp.ArcGISProject(self.project_path_arcgis)

        # selection map based on project to look at the existing layer
        map_list_name = [f.name for f in self.project.listMaps()]
        print(f'all_maps in project: {map_list_name}')
        self.map_name_arcgis = map_name_arcgis
        print(f'we will select the map for {self.map_name_arcgis}')
        self.map = [f for f in self.project.listMaps() if f.name == self.map_name_arcgis][0]
        self.list_layers = self.map.listLayers()

    def selecting_layer(self, name_layer):
        layer_selected = [shp for shp in self.map.listLayers() if shp.name == name_layer][0]
        return layer_selected
        

    
    