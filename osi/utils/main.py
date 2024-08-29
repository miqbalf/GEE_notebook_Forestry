
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