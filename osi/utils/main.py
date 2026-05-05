import ee

# Function to validate each feature's 'id' property
def validate_feature(feature_info, field_name):
    try:
        # Check if 'id' property exists in the feature properties
        if field_name not in feature_info['properties']:
            raise ValueError(f"Feature {feature_info[field_name]} does not have an '{field_name}' property.")
        
        # Check if 'id' property is an integer
        id_value = feature_info['properties'][field_name]
        if not isinstance(id_value, int):
            raise TypeError(f"Feature {feature_info[field_name]} has an '{field_name}' value '{id_value}' which is not an integer.")
        
        # If all checks pass
        return True

    except ValueError as ve:
        print(f'Validation Error: {ve}')
        return False
    except TypeError as te:
        print(f'Validation Error: {te}')
        return False

# Convert FeatureCollection to a list and retrieve data to the client side for validation
def validate_aoi(AOI, ee, field_name):

    try:
        print('trying to list the featurecollection')
        AOI_list = AOI.toList(AOI.size())
        all_valid = True  # Flag to check if all features are valid

        print('now for loop to feature size range')
        for i in range(AOI.size().getInfo()):
            feature = ee.Feature(AOI_list.get(i))
            feature_info = feature.getInfo()  # Retrieve feature info to client-side

            # Validate the feature
            if not validate_feature(feature_info, field_name):
                all_valid = False  # Set flag to False if any feature is invalid

        if all_valid:
            print(f'All features have a valid "{field_name}" column with integer values.')
        else:
            print('There are invalid features in the collection. See error messages above.')

    except Exception as e:
        print(f'An unexpected error occurred: {e}')


def get_geometry_center(geometry, max_error=1):
    """
    Get the center point of a geometry with robust error handling.
    
    Args:
        geometry: Earth Engine Geometry object
        max_error (float): Maximum error margin for centroid calculation
    
    Returns:
        list: [longitude, latitude] coordinates of the center point
    """
    try:
        # Method 1: Try centroid with error margin
        center = geometry.centroid(maxError=max_error).coordinates().getInfo()
        print(f"✅ Centroid calculated successfully with error margin {max_error}")
        return center
        
    except Exception as e:
        print(f"⚠️  Centroid calculation failed: {e}")
        
        try:
            # Method 2: Use bounds center as fallback
            bounds = geometry.bounds().getInfo()
            if bounds and 'coordinates' in bounds:
                coords = bounds['coordinates'][0]
                if len(coords) >= 4:  # Should have at least 4 corners
                    center = [
                        (coords[0][0] + coords[2][0]) / 2,  # Average longitude
                        (coords[0][1] + coords[2][1]) / 2   # Average latitude
                    ]
                    print("✅ Using bounds center as fallback")
                    return center
                    
        except Exception as e2:
            print(f"⚠️  Bounds calculation failed: {e2}")
            
        try:
            # Method 3: Use first coordinate as last resort
            coords = geometry.coordinates().getInfo()
            if coords and len(coords) > 0:
                center = coords[0] if isinstance(coords[0], list) else [0, 0]
                print("⚠️  Using first coordinate as last resort")
                return center
                
        except Exception as e3:
            print(f"❌ All methods failed: {e3}")
            
        # Final fallback
        print("❌ Using default center [0, 0]")
        return [0, 0]


def get_geometry_info(geometry):
    """
    Get comprehensive information about a geometry including center, bounds, and area.
    
    Args:
        geometry: Earth Engine Geometry object
    
    Returns:
        dict: Dictionary containing geometry information
    """
    try:
        # Get coordinates
        coords = geometry.coordinates().getInfo()
        
        # Get center
        center = get_geometry_center(geometry)
        
        # Get bounds
        try:
            bounds = geometry.bounds().getInfo()
            # Use bounds directly for bbox if available
            if bounds and len(bounds) >= 2:
                bbox = {
                    'minx': float(bounds[0][0]),  # min longitude
                    'miny': float(bounds[0][1]),  # min latitude  
                    'maxx': float(bounds[1][0]),  # max longitude
                    'maxy': float(bounds[1][1])   # max latitude
                }
            else:
                bbox = None
        except Exception as e:
            print(f"Warning: Could not get bounds from geometry: {e}")
            bounds = None
            bbox = None
            
        # Get area
        try:
            area_m2 = geometry.area().getInfo()
            area_km2 = area_m2 / 1e6
        except:
            area_m2 = None
            area_km2 = None
        
        # If bounds method failed, calculate bounding box from coordinates as fallback
        if not bbox and coords:
            # Handle nested coordinate structures (Polygon, MultiPolygon, etc.)
            def flatten_coords(coord_list):
                """Recursively flatten coordinate arrays"""
                flattened = []
                for item in coord_list:
                    if isinstance(item, list) and len(item) > 0:
                        if isinstance(item[0], list):
                            # Nested array - recurse
                            flattened.extend(flatten_coords(item))
                        else:
                            # Coordinate pair
                            flattened.append(item)
                return flattened
            
            # Flatten coordinates to handle nested structures
            flat_coords = flatten_coords(coords)
            
            if flat_coords:
                lons = [float(coord[0]) for coord in flat_coords]
                lats = [float(coord[1]) for coord in flat_coords]
                bbox = {
                    'minx': min(lons),
                    'miny': min(lats),
                    'maxx': max(lons),
                    'maxy': max(lats)
                }
                print(f"Calculated bbox from coordinates: {bbox}")
        
        return {
            'center': center,
            'coordinates': coords,
            'bounds': bounds,
            'bbox': bbox,
            'area_m2': area_m2,
            'area_km2': area_km2
        }
        
    except Exception as e:
        print(f"❌ Error getting geometry info: {e}")
        return {
            'center': [0, 0],
            'coordinates': None,
            'bounds': None,
            'bbox': None,
            'area_m2': None,
            'area_km2': None
        }


def process_aoi_geometry(AOI_geom):
    """
    Process AOI geometry and return comprehensive information.
    
    Args:
        AOI_geom: Earth Engine Geometry object
    
    Returns:
        dict: Dictionary containing AOI information
    """
    try:
        # Get comprehensive geometry info
        geometry_info = get_geometry_info(AOI_geom)
        
        # Create aoi_info dictionary
        aoi_info = {
            'bbox': geometry_info['bbox'],
            'center': geometry_info['center'],
            'coordinates': geometry_info['coordinates'],
            'area_km2': geometry_info['area_km2']
        }
        
        print(f"✅ AOI processed successfully:")
        print(f"   - Center: {aoi_info['center']}")
        print(f"   - Area: {aoi_info['area_km2']:.2f} km²" if aoi_info['area_km2'] else "   - Area: Unknown")
        print(f"   - BBox: {aoi_info['bbox']}")
        
        return aoi_info
        
    except Exception as e:
        print(f"❌ Error processing AOI geometry: {e}")
        # Return fallback values
        return {
            'bbox': None,
            'center': [0, 0],
            'coordinates': None,
            'area_km2': None
        }


def create_aoi_info_from_geometry(AOI_geom):
    """
    Create AOI info dictionary from Earth Engine geometry.
    This is a convenience function for notebooks and other applications.
    
    Args:
        AOI_geom: Earth Engine Geometry object
    
    Returns:
        dict: AOI information dictionary
    """
    return process_aoi_geometry(AOI_geom)

def generate_map_id(layername_visparam: dict, layername_image: dict):
    """
    Generate Google Earth Engine Map IDs for visualization layers.
    
    This function creates tile URLs and metadata for GEE images that can be used
    in web mapping applications like MapStore, Leaflet, or other GIS platforms.
    
    Args:
        layername_visparam (dict): Dictionary mapping layer names to their visualization parameters.
                                 Format: {'layer_name': {'bands': [...], 'min': 0, 'max': 1, 'gamma': 1.5}}
        layername_image (dict): Dictionary mapping layer names to their corresponding GEE Image objects.
                               Format: {'layer_name': ee.Image_object}
    
    Returns:
        dict: Dictionary containing:
            - 'all_mapid': Raw GEE Map ID objects for each layer
            - 'map_layers': Processed layer metadata with tile URLs and descriptions
    
    Example:
        >>> vis_params = {'my_layer': {'bands': ['red', 'green', 'blue'], 'min': 0, 'max': 0.6}}
        >>> images = {'my_layer': ee.Image('LANDSAT/LC08/C01/T1_SR/LC08_044034_20140318')}
        >>> result = generate_map_id(vis_params, images)
        >>> print(result['map_layers']['my_layer']['tile_url'])
    """
    print("Generating GEE Map IDs...")

    # Generate Map IDs for each layer using GEE's getMapId() method
    # This creates tile URLs that can be consumed by web mapping clients
    all_mapid = {
        layer_name: ee.Image(image).getMapId(layername_visparam[layer_name]) 
        for layer_name, image in layername_image.items() 
        if layer_name in layername_visparam
    }
    
    # Process the Map IDs into a more user-friendly format
    map_layers = {}
    
    # Convert each Map ID into a structured layer object with metadata
    for layer_name, map_id_dict in all_mapid.items():
        map_layers[layer_name] = {
            # Tile URL format for web mapping (WMTS/TMS compatible)
            'tile_url': map_id_dict['tile_fetcher'].url_format,
            
            # Human-readable layer name (converts underscores to spaces, title case)
            'name': layer_name.replace('_', ' ').title(),
            
            # Descriptive text for the layer
            'description': f'{layer_name.upper()} visualization from GEE analysis',
            
            # Original visualization parameters used for this layer
            'vis_params': layername_visparam[layer_name]
        }

    return {'all_mapid': all_mapid, 'map_layers': map_layers}


def generate_map_id_list(layers_data: list):
    """
    Enhanced Map ID generation with flexible layer definitions.
    
    Args:
        layers_data: List of layer dictionaries, each containing:
            - 'name': Layer name (str)
            - 'image': GEE Image object (ee.Image)
            - 'vis_params': Visualization parameters (dict)
            - 'description': Optional description (str, optional)
    
    Returns:
        Dictionary containing:
            - 'all_mapid': Raw GEE Map ID objects for each layer
            - 'map_layers': Processed layer metadata with tile URLs and descriptions
    
    Example:
        >>> layers = [
        ...     {
        ...         'name': 'true_color',
        ...         'image': landsat_image,
        ...         'vis_params': {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000},
        ...         'description': 'True Color RGB visualization'
        ...     },
        ...     {
        ...         'name': 'ndvi',
        ...         'image': ndvi_image,
        ...         'vis_params': {'min': -0.2, 'max': 0.8, 'palette': ['red', 'yellow', 'green']}
        ...     }
        ... ]
        >>> result = generate_map_id_enhanced(layers)
    """
    print("Generating GEE Map IDs...")
    
    # Validate input
    if not layers_data:
        raise ValueError("layers_data cannot be empty")
    
    # Generate Map IDs for each layer
    all_mapid = {}
    map_layers = {}
    
    for layer_info in layers_data:
        layer_name = layer_info['name']
        image = layer_info['image']
        vis_params = layer_info['vis_params']
        description = layer_info.get('description', f'{layer_name.upper()} visualization from GEE analysis')
        
        # Validate inputs
        if not isinstance(image, ee.Image):
            raise ValueError(f"Layer '{layer_name}': image must be an ee.Image object")
        
        if not isinstance(vis_params, dict):
            raise ValueError(f"Layer '{layer_name}': vis_params must be a dictionary")
        
        try:
            # Generate Map ID
            map_id_dict = ee.Image(image).getMapId(vis_params)
            all_mapid[layer_name] = map_id_dict
            
            # Process into user-friendly format
            map_layers[layer_name] = {
                'tile_url': map_id_dict['tile_fetcher'].url_format,
                'name': layer_name.replace('_', ' ').title(),
                'description': description,
                'vis_params': vis_params
            }
            
            print(f"✅ Generated Map ID for layer: {layer_name}")
            
        except Exception as e:
            print(f"❌ Failed to generate Map ID for layer '{layer_name}': {e}")
            raise ValueError(f"Failed to generate Map ID for layer '{layer_name}': {e}")
    
    print(f"✅ Generated Map IDs for {len(map_layers)} layers")
    return {'all_mapid': all_mapid, 'map_layers': map_layers}


def generate_map_id_one(layers: dict):
    """
    Simple Map ID generation from a single dictionary.
    
    Args:
        layers: Dictionary where keys are layer names and values contain:
            - 'image': GEE Image object
            - 'vis_params': Visualization parameters
            - 'description': Optional description
    
    Returns:
        Dictionary containing Map ID results
    
    Example:
        >>> layers = {
        ...     'true_color': {
        ...         'image': landsat_image,
        ...         'vis_params': {'bands': ['B4', 'B3', 'B2']},
        ...         'description': 'True Color RGB'
        ...     },
        ...     'ndvi': {
        ...         'image': ndvi_image,
        ...         'vis_params': {'min': -0.2, 'max': 0.8, 'palette': ['red', 'yellow', 'green']}
        ...     }
        ... }
        >>> result = generate_map_id_simple(layers)
    """
    # Convert to list format
    layers_data = []
    for name, layer_info in layers.items():
        layers_data.append({
            'name': name,
            'image': layer_info['image'],
            'vis_params': layer_info['vis_params'],
            'description': layer_info.get('description', f'{name.upper()} visualization from GEE analysis')
        })
    
    return generate_map_id_list(layers_data)


def create_layer_info(name: str, image: ee.Image, vis_params: dict, description: str = None):
    """
    Create a layer info dictionary for use with generate_map_id_enhanced.
    
    Args:
        name: Layer name
        image: GEE Image object
        vis_params: Visualization parameters
        description: Optional description
    
    Returns:
        Layer info dictionary
    """
    return {
        'name': name,
        'image': image,
        'vis_params': vis_params,
        'description': description or f'{name.upper()} visualization from GEE analysis'
    }


def quick_map_id(name: str, image: ee.Image, vis_params: dict, description: str = None):
    """
    Quick Map ID generation for a single layer.
    
    Args:
        name: Layer name
        image: GEE Image object
        vis_params: Visualization parameters
        description: Optional description
    
    Returns:
        Map ID result for the single layer
    """
    layer_info = create_layer_info(name, image, vis_params, description)
    return generate_map_id_list([layer_info])