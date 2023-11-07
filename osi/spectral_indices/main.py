# class SpectralAnalysis:
#     def __init__(self, image *args, **kwargs):
#         self.image = image
#         self.arg = args


#     # Advanced Vegetation index - scaled from old formula (8bit) to relative number based on region
#     def AVI_func(image):
#         AVI = image.expression('((nir + 1 )* (maxRed-red) *(nir -red))**0.333',{
#             'nir':image.select(['nir']),
#             'red':image.select(['red']),
#             'maxRed': max_bands(image)[0],
#             }
#         ).rename('AVI') 

#         return AVI

#     # Bare Soil Index 
#     # https://www.researchgate.net/publication/319045433_Integration_of_GIS_and_Remote_Sensing_for_Evaluating_Forest_Canopy_Density_Index_in_Thai_Nguyen_Province_Vietnam/link/599293be0f7e9b433f415b40/download
#     def BSI_func(image):
#         if I_satellite == 'LANDSAT':
#             BSI = image.expression('(((SWIR1 + red) - (G + NIR)) / ((SWIR1 + red) + (G + NIR)))*100+100',{
#                 'SWIR1':image.select(['swir1']),
#                 'G':image.select(['green']),
#                 'red':image.select(['red']),
#                 'NIR':image.select(['nir']),
#                 }
#             ).rename('BSI')
            
#         elif I_satellite == 'PlanetNicfi' or I_satellite == 'Sentinel':
#             BSI = image.expression(
#                 '(NIR + GREEN + RED) / (NIR + GREEN - RED)',  {
#                     'NIR': image.select('nir'),
#                     'GREEN': image.select('green'),
#                     'RED': image.select('red')
#                         }
#                     ).rename('BSI')
    
#         return BSI

#     def SI_func(image):
#         SI = image.expression('((maxGreen-Green)*(maxBlue-Blue)*(maxRed-Red))**(1/3)',{  
#             'Red':image.select(['red']),
#             'Green':image.select(['green']), #//******
#             'Blue':image.select(['blue']),
#             'maxRed': max_bands(image)[0],
#             'maxGreen': max_bands(image)[1],
#             'maxBlue': max_bands(image)[2],
#         }
#         ).rename('SI')
#         return SI

def adding_all(x):
    return x+x