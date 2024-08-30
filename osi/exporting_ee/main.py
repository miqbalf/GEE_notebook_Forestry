import ee

# here we want to have an export to gdrive
def exporting_from_ee(name_file_desc='some_desc', folder_name='somefolder', input_data = None, AOI=None,pca_scale=5,type_data_export='vector', output='shp'):
    if type_data_export == 'vector':
        if output=='shp':
            # Export the samples to a shp file in Google Drive
            export_task = ee.batch.Export.table.toDrive(
                collection=input_data,
                description=name_file_desc,
                folder=folder_name,
                fileFormat='SHP'
            )
            extension = '.shp'
        elif output=='kml':
            # Export the samples to a kml file in Google Drive
            export_task = ee.batch.Export.table.toDrive(
                collection=input_data,
                description=name_file_desc,
                folder=folder_name,
                fileFormat='KML'
            )
            extension = '.kml'

    elif type_data_export == 'raster':
        if output == 'GeoTIFF':
            export_task = ee.batch.Export.image.toDrive(
                image=input_data,  # Clip the image to the ROI
                description=name_file_desc,  # Description for the export task
                folder=folder_name,  # Optional: Folder in Google Drive to save the file
                fileNamePrefix=name_file_desc,  # File name prefix for the exported TIFF
                region=AOI.geometry().getInfo()['coordinates'],  # The region to export (in GeoJSON format)
                scale=pca_scale,  # Pixel resolution in meters (e.g., 10 for Sentinel-2)
                crs='EPSG:4326',  # Coordinate reference system (e.g., WGS84)
                maxPixels=1e13,  # Maximum number of pixels allowed for the export
                fileFormat='GeoTIFF'  # File format for the exported image
            )
            extension = '.tiff'

    # Start the export task
    export_task.start()

    # Monitor the task status
    import time
    while export_task.active():
        print('Export task status:', export_task.status())
        time.sleep(10)

    print(f'Export task completed: {name_file_desc}')

    path_gdrive = fr'\My Drive\{folder_name}\{name_file_desc}{extension}'

    print(f'location in gdrive (please add location drive letter) --> {path_gdrive}')
    return path_gdrive

