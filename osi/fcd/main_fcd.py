# fcd: Forest Canopy Density Mapping defining forest vs no forest, and additional: shrubland, grassland (?)
# FCD adapted -> 
## http://www.ijesd.org/vol8/1012-F0032.pdf
## http://www.itto.int/files/itto_project_db_input/2056/Technical/pd13-97-3%20rev1(F)%20FCD-Mapper%20User's%20Guide_e.pdf

import ee
from gee_lib.osi.image_collection.main import ImageCollection
from gee_lib.osi.spectral_indices.spectral_analysis import SpectralAnalysis
from gee_lib.osi.pca.pca_gee import PCA
from gee_lib.osi.spectral_indices.utils import normalization_100, assigning_band

class FCDCalc:
    def __init__(self, config):
        self.config = config
        self.I_satellite = config['I_satellite']
        self.IsThermal = config['IsThermal']
        self.AOI = config['AOI']
        self.date_start_end = config['date_start_end']
        self.cloud_cover_threshold = config['cloud_cover_threshold']
        self.region = config['region']

        # initiate instance class for the image collection and later mosaicking
        self.InputCollection = ImageCollection(AOI=self.AOI, 
                                               date_start_end=self.date_start_end, 
                                               cloud_cover_threshold = self.cloud_cover_threshold, 
                                               I_satellite=self.I_satellite, 
                                               region=self.region, 
                                               config = self.config
                                               )
        
        self.image_mosaick = None
        self.image_collection_mask = None

        self.avi_image = None
        self.bsi_image = None
        self.si_image = None

        self.avi_norm = None
        self.bsi_norm = None
        self.si_norm = None
        self.ti_norm = None

        self.svi1 = None
        self.svi2 = None
        self.ssi1 = None
        self.ssi2 = None

        
        self.FCD1_1 = None
        self.FCD2_2 = None
        self.FCD1_2 = None
        self.FCD2_1 = None
        

    def fcd_calc(self):
        ti_norm, ssi2 = None, None
        FCD1_1, FCD2_1, FCD1_2, FCD2_2 = None, None, None, None
        image_collection_mask = self.InputCollection.image_collection_mask()
        image_mosaick = self.InputCollection.image_mosaick()
        
        # class image spectral
        classImageSpectral = SpectralAnalysis(image_mosaick, self.config)
        
        print('processing AVI')
        avi_image = classImageSpectral.AVI_func()

        print('processing BSI')
        bsi_image = classImageSpectral.BSI_func()

        print('processing SI')
        si_image = classImageSpectral.SI_func()

        print('Normalizing to 100 AVI')
        ##### Starting (normalized 100) Indices
        # acquire the existing configuration after conditional I_satellite
        pca_scale = classImageSpectral.pca_scale
        tileScale = classImageSpectral.tileScale
        print('Normalizing to 100 AVI')
        avi_norm = normalization_100(avi_image, pca_scale=pca_scale, AOI=self.AOI)
        print('Normalizing to 100 BSI')
        bsi_norm = normalization_100(bsi_image, pca_scale=pca_scale, AOI=self.AOI)
        print('Normalizing to 100 SI')
        si_norm = normalization_100(si_image, pca_scale=pca_scale, AOI=self.AOI)

        print('Combining AVI AND BSI')
        # Combine  AVI and BSI to one image with two bands
        AVI_BSI = avi_norm.addBands(bsi_norm)
        # Masked-out process or remove null data, to avoid errors
        avi_bsi_clean = AVI_BSI.gte(0).Or(AVI_BSI.lte(0))
        AVI_BSI = AVI_BSI.updateMask(avi_bsi_clean)

        print(f'no thermal band, choosing {self.I_satellite} images')
        si = si_norm

        sviPCAClass = PCA(AVI_BSI, self.config)
        print('Processing means center of AVI_BSI please wait')
        sviPCA = sviPCAClass.getPrincipalComponents()

        print('Now we proceed to the PCA of Vegetation density')

        VD = sviPCA.rename(['VD1', 'VD2'])
        SVI = normalization_100(VD,pca_scale=pca_scale, AOI=self.AOI)

        print('Success get the PCA normalized of VD => SVI')

        print('Now calculating the FCD from SVI and SSI - selecting band svi1 svi2 ssi1 and ssi2')
        svi1 = SVI.select(['VD1'])
        ssi1 = si.select(['SI'])
        svi2 = SVI.select(['VD2'])

        # Starting to include in the formula for Forest Cover Density
        FCD1_1 = (((svi1.multiply(ssi1)).add(1)).pow(0.5)).subtract(1).rename('FCD')
        FCD2_1 = (((svi2.multiply(ssi1)).add(1)).pow(0.5)).subtract(1).rename('FCD')

        print('finish processing PCA, the result: FCD1_1 and FCD2_1 please continue')

        # if the option to use thermal band
        if self.IsThermal == True:
            ti_norm = normalization_100(image_mosaick.select('TI'),pca_scale=pca_scale, AOI=self.AOI)
            SI_TI = si_norm.addBands(ti_norm)
            si_ti_clean = SI_TI.gte(0).Or(SI_TI.lte(0))
            SI_TI = SI_TI.updateMask(si_ti_clean)

            print('Now we get to the PCA of SI and TI')
            ssiPCAClass = PCA(SI_TI, self.config)
            SI_TI_PCA = sviPCAClass.getPrincipalComponents()
            SSI = normalization_100(SI_TI_PCA,pca_scale=pca_scale, AOI=self.AOI)

            print('Success get the PCA normalized of SI and TI => SSI')

            print('Now calculating the FCD from SVI and SSI - selecting band svi1 svi2 ssi1 and ssi2')
            svi1 = SVI.select(['VD1'])
            ssi1 = SSI.select(['SSI1'])
            svi2 = SVI.select(['VD2'])
            ssi2 = SSI.select(['SSI2'])

            # Starting to include in the formula for Forest Cover Density
            FCD1_1 = (((svi1.multiply(ssi1)).add(1)).pow(0.5)).subtract(1).rename('FCD')
            FCD2_2 = (((svi2.multiply(ssi2)).add(1)).pow(0.5)).subtract(1).rename('FCD')
            FCD1_2 = (((svi1.multiply(ssi2)).add(1)).pow(0.5)).subtract(1).rename('FCD')
            FCD2_1 = (((svi2.multiply(ssi1)).add(1)).pow(0.5)).subtract(1).rename('FCD')

        self.image_mosaick = image_mosaick
        self.image_collection_mask = image_collection_mask

        self.avi_image = avi_image
        self.bsi_image = bsi_image
        self.si_image = si_image

        self.avi_norm = avi_norm
        self.bsi_norm = bsi_norm
        self.si_norm = si_norm
        self.ti_norm = ti_norm

        self.svi1 = svi1
        self.svi2 = svi2
        self.ssi1 = ssi1
        self.ssi2 = ssi2

        self.FCD1_1 = FCD1_1
        self.FCD2_2 = FCD2_2
        self.FCD1_2 = FCD1_2
        self.FCD2_1 = FCD2_1

        # return FCD1_1, FCD2_1, FCD1_2, FCD2_2

        results = {

            'image_mosaick': self.image_mosaick,
            # 'image_collection_mask': self.image_collection_mask,

            'avi_image': self.avi_image,
            'bsi_image': self.bsi_image,
            'si_image': self.si_image,

            'avi_norm': self.avi_norm,
            'si_norm': self.si_norm,
            'ti_norm': self.ti_norm,
            
            'svi1' :self.svi1,
            'svi2' :self.svi2,
            'ssi1' :self.ssi1,
            'ssi2' :self.ssi2,

            'FCD1_1': self.FCD1_1,
            'FCD2_1': self.FCD2_1,
            'FCD1_2': self.FCD1_2,
            'FCD2_2': self.FCD2_2,

            'pca_scale': pca_scale,
            'tileScale': tileScale,

        }
        return results
            
