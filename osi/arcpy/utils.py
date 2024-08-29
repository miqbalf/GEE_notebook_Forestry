# Define a helper function to safely get the data source
def safe_get_data_source(layer):
    try:
        if layer.isFeatureLayer:
            return layer.dataSource
        else:
            return "Not a feature layer or no data source available"
    except Exception as e:
        return f"Error: {str(e)}"