import ee

class Slope:
    def __init__(self, config):
        self.config = config
        self.AOI = config['AOI']
        self.slope_threshold = config.get('slope_threshold', 25.0)

    def get_slope(self):
        """Returns {"slope_deg": ee.Image} — SRTM slope in degrees, clipped to AOI"""
        elevation = ee.Image("USGS/SRTMGL1_003")
        slope_image = ee.Terrain.slope(elevation).clip(self.AOI)
        return {"slope_deg": slope_image}

    def exclusion_mask(self, threshold_deg=None):
        """Returns {"steep_slope_mask": ee.Image} — binary mask where slope > threshold"""
        threshold = threshold_deg if threshold_deg is not None else self.slope_threshold
        slope = self.get_slope()["slope_deg"]
        mask = slope.gt(threshold).clip(self.AOI)
        return {"steep_slope_mask": mask}
