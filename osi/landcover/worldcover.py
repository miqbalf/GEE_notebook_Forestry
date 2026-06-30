import ee

class WorldCover:
    def __init__(self, config):
        self.config = config
        self.AOI = config['AOI']

    def get_lulc(self):
        """Returns {"lc_image": ee.Image} — WorldCover reclassified to common 9-class scheme, clipped to AOI."""
        worldcover = ee.ImageCollection("ESA/WorldCover/v200").first()
        lc_image = worldcover.select('Map')

        # Reclassify native WorldCover classes to common 9-class scheme:
        #   10 (Tree cover)               → 1
        #   20 (Shrubland)                → 2
        #   30 (Grassland)                → 3
        #   40 (Cropland)                 → 4
        #   50 (Built-up)                 → 5
        #   60 (Bare / sparse)            → 6
        #   80 (Water)                    → 7
        #   90 (Herbaceous wetland)       → 8
        #   95 (Mangroves)                → 8
        #   70 (Snow/ice)                 → 9
        #  100 (Moss/lichen)              → 9
        reclassified = lc_image.remap(
            [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100],
            [1, 2, 3, 4, 5, 6, 9, 7, 8, 8, 9]
        ).rename('lc_image')

        return {"lc_image": reclassified.clip(self.AOI)}
