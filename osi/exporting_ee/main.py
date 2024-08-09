import ee

# here we want to have an export to gdrive
def exporting_to_ee(name_file_desc='some_desc', folder_name='somefolder', input_data = None, type_data_export='vector', output='shp'):
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

