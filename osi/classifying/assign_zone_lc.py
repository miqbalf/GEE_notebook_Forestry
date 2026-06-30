import ee
from ..spectral_indices.utils import assigning_band
from .utils import add_classes, add_images, unmasked_helper
from ..legends.utils import legends_obj_creation


class LCZoneAssigner:
    """
    Orchestrating class that combines landcover + Hansen deforestation + DW
    transitions + slope into the final 11-class go/no-go zoning map.

    Follows the existing AssignClassZone pattern: individual class images are
    created via ``assigning_band`` and merged via ``add_classes`` /
    ``add_images`` with ``ee.ImageCollection.iterate``.

    11-class scheme
    ---------------
      1  Shrubland go-zone
      2  Grassland go-zone
      3  Openland go-zone
      4  High-density forest (stable, gentle slope)
      5  Low-medium forest
      6  Regrowth high density (historical)
      7  Regrowth low density (historical)
      8  Historical deforestation (10-year rule)
      9  Water
     10  Steep-slope protected  (overrides ALL other classes)
     11  DW-flagged degradation
    """

    def __init__(self, config):
        self.config = config
        self.AOI = config["AOI"]
        self.AOI_img = config["AOI_img"]
        self.band_name_image = config["band_name_image"]  # typically "Class"

        self.class_name_map_color = {
            "1": "#ffe3b3",   # Shrubland go-zone
            "2": "#ffff33",   # Grassland go-zone
            "3": "#F89696",   # Openland go-zone
            "4": "#09ab0c",   # High-density forest
            "5": "#83ff5a",   # Low-medium forest
            "6": "#ff0004",   # Regrowth high density
            "7": "#ff0abe",   # Regrowth low density
            "8": "#ff8a1d",   # Historical deforestation
            "9": "#1900ff",   # Water
            "10": "#8B4513",  # Steep-slope protected
            "11": "#DAA520",  # DW-flagged degradation
        }

        self.class_name_map = {
            "1": "Shrubland_Go-Zone",
            "2": "Grassland_Go-Zone",
            "3": "Openland_Go-Zone",
            "4": "High_density_Forest",
            "5": "Low_Medium_density_Forest",
            "6": "Regrowth_High_Density_Forest_from_deforested_historical",
            "7": "Regrowth_Low_Density_Forest_from_deforested_historical",
            "8": "Historical_deforestation_10_years_rule",
            "9": "Water_Body",
            "10": "Steep_Slope_Protected",
            "11": "DW_flagged_Degradation",
        }

        legend = legends_obj_creation(
            self.class_name_map_color, self.class_name_map
        )
        self.vis_param_merged = legend["vis_param"]
        self.legend_class = legend["legend_class"]

    def assign(
        self,
        lc_image,
        hansen_tcl,
        minLoss,
        dw_transitions,
        slope_mask,
        dw_tree_prob=None,
    ):
        """Produce the final 11-class zone map.

        Parameters
        ----------
        lc_image : ee.Image
            WorldCover reclassified to common 9-class scheme (from
            ``WorldCover.get_lulc()["lc_image"]``).
        hansen_tcl : dict
            From ``HansenHistorical.initiate_tcl()``, containing keys
            ``"minLoss"``, ``"ForestArea2000Hansen"``, ``"gfc"``.
        minLoss : ee.Image
            Actual TCL loss pixels from Hansen
            (``hansen_tcl["minLoss"]``).
        dw_transitions : ee.Image
            DW tree->non-tree transition mask (from
            ``DynamicWorld.tree_transitions()["dw_transitions"]``).
        slope_mask : ee.Image
            Steep slope exclusion mask (from
            ``Slope.exclusion_mask()["steep_slope_mask"]``).
        dw_tree_prob : ee.Image, optional
            DW mean tree probability (from
            ``DynamicWorld.get_composite()["dw_tree_prob"]``).  When
            provided it is used to split stable forests into high-density
            (class 4) vs low-medium (class 5).  If ``None``, all stable
            trees in ``ForestArea2000Hansen`` are assigned to class 4 and
            class 5 is left empty.

        Returns
        -------
        dict
            ``{"all_zone": ee.Image, "vis_param_merged": dict,
            "legend_class": dict}``
        """
        gfc = hansen_tcl["gfc"]
        ForestArea2000Hansen = hansen_tcl["ForestArea2000Hansen"]

        # ------------------------------------------------------------------
        #  Water mask (class 9) — from Hansen gfc datamask AND/OR WorldCover
        # ------------------------------------------------------------------
        hansen_water = gfc.select(["datamask"]).eq(2)  # datamask == 2 = water
        lc_water = lc_image.eq(7)                      # WorldCover 7 = water
        water_mask = lc_water.Or(hansen_water)
        # Mask AOI_img where water exists (follows AssignClassZone pattern)
        water_in_AOI = self.AOI_img.mask().updateMask(water_mask)
        not_water = self.AOI_img.unmask().updateMask(
            water_in_AOI.mask().Not()
        ).clip(self.AOI)

        # ------------------------------------------------------------------
        #  Not-steep helper
        # ------------------------------------------------------------------
        not_steep = slope_mask.Not()

        # ------------------------------------------------------------------
        #  Areas outside the 10-year TCL (loss) window
        # ------------------------------------------------------------------
        unmasked_loss = unmasked_helper(minLoss, self.AOI_img, self.AOI)

        # ------------------------------------------------------------------
        #  Individual class images
        # ------------------------------------------------------------------

        # -- Class 1: Shrubland go-zone -----------------------------------
        # lc_image == 2 (shrubland) AND not in minLoss AND not water
        # AND not steep
        shrubland_go_mask = (
            lc_image.eq(2)
            .And(unmasked_loss)
            .And(not_water)
            .And(not_steep)
        )
        shrubland_go = ee.Image(
            assigning_band(self.band_name_image, 1, shrubland_go_mask)
        )

        # -- Class 2: Grassland go-zone -----------------------------------
        # lc_image == 3 (grassland) AND not in minLoss AND not water
        # AND not steep
        grassland_go_mask = (
            lc_image.eq(3)
            .And(unmasked_loss)
            .And(not_water)
            .And(not_steep)
        )
        grassland_go = ee.Image(
            assigning_band(self.band_name_image, 2, grassland_go_mask)
        )

        # -- Class 3: Openland go-zone ------------------------------------
        # lc_image in [5, 6] (built-up, bare) AND not in minLoss AND not
        # water AND not steep
        openland_go_mask = (
            lc_image.eq(5).Or(lc_image.eq(6))
            .And(unmasked_loss)
            .And(not_water)
            .And(not_steep)
        )
        openland_go = ee.Image(
            assigning_band(self.band_name_image, 3, openland_go_mask)
        )

        # -- Classes 4 & 5: Forest (stable, no recent loss) ---------------
        # Trees in ForestArea2000Hansen, NOT in minLoss (no recent loss),
        # not steep, not water.
        forest_base_mask = (
            lc_image.eq(1)                     # tree cover (WorldCover)
            .And(ForestArea2000Hansen)         # was forest in 2000
            .And(unmasked_loss)                # no recent TCL loss
            .And(not_steep)                    # gentle slope
            .And(not_water)                    # not water
        )

        if dw_tree_prob is not None:
            # Class 4: High-density forest — DW tree prob high (>= 50 %)
            high_density_mask = forest_base_mask.And(
                dw_tree_prob.gte(0.5)
            )
            # Class 5: Low-medium forest — DW tree prob low (< 50 %)
            low_medium_mask = forest_base_mask.And(
                dw_tree_prob.lt(0.5)
            )
        else:
            # Without DW tree probability, all stable forest-area trees are
            # treated as high-density (class 4).  Class 5 remains empty.
            high_density_mask = forest_base_mask
            low_medium_mask = ee.Image.constant(0)

        high_density_forest = ee.Image(
            assigning_band(self.band_name_image, 4, high_density_mask)
        )
        low_medium_forest = ee.Image(
            assigning_band(self.band_name_image, 5, low_medium_mask)
        )

        # -- Class 6: Regrowth high density (historical) ------------------
        # lc_image == 1 (tree) AND in minLoss (loss happened) AND
        # not steep
        regrowth_high_mask = (
            lc_image.eq(1)
            .And(minLoss)          # loss happened here per Hansen
            .And(not_steep)        # not on steep slope
            .And(not_water)
        )
        regrowth_high = ee.Image(
            assigning_band(self.band_name_image, 6, regrowth_high_mask)
        )

        # -- Class 7: Regrowth low density (historical) -------------------
        # lc_image == 1 (tree) AND in minLoss AND steep OK
        # (regrowth on slopes — not excluded by steep mask)
        regrowth_low_mask = (
            lc_image.eq(1)
            .And(minLoss)          # loss happened here per Hansen
            .And(not_water)
            # NOTE: no steep exclusion — regrowth IS allowed on slopes
        )
        regrowth_low = ee.Image(
            assigning_band(self.band_name_image, 7, regrowth_low_mask)
        )

        # -- Class 8: Historical deforestation (10-year rule) -------------
        # in minLoss area AND currently NOT tree => confirmed deforestation
        hist_deforest_mask = minLoss.And(lc_image.neq(1))
        hist_deforest = ee.Image(
            assigning_band(self.band_name_image, 8, hist_deforest_mask)
        )

        # -- Class 9: Water -----------------------------------------------
        water_zone = ee.Image(
            assigning_band(self.band_name_image, 9, water_in_AOI)
        )

        # -- Class 11: DW-flagged degradation -----------------------------
        # dw_transitions == 1 AND NOT in Hansen minLoss
        # (cross-check flag — degradation not captured by Hansen window)
        dw_degradation_mask = (
            dw_transitions.eq(1).And(minLoss.Not())
        )
        dw_degradation = ee.Image(
            assigning_band(self.band_name_image, 11, dw_degradation_mask)
        )

        # -- Class 10: Steep-slope protected (overrides EVERYTHING) -------
        steep_protected = ee.Image(
            assigning_band(self.band_name_image, 10, slope_mask)
        )

        # ------------------------------------------------------------------
        #  Merge all class images (except steep override) using the
        #  add_classes / add_images / iterate pattern from AssignClassZone.
        # ------------------------------------------------------------------
        empty_image = ee.Image.constant(0).rename(self.band_name_image)

        image_list = [
            shrubland_go.select([self.band_name_image]),
            grassland_go.select([self.band_name_image]),
            openland_go.select([self.band_name_image]),
            high_density_forest.select([self.band_name_image]),
            low_medium_forest.select([self.band_name_image]),
            regrowth_high.select([self.band_name_image]),
            regrowth_low.select([self.band_name_image]),
            hist_deforest.select([self.band_name_image]),
            water_zone.select([self.band_name_image]),
            dw_degradation.select([self.band_name_image]),
        ]

        image_collection = ee.ImageCollection(image_list)
        result_collection = image_collection.map(
            lambda img: add_classes(img, empty_image)
        )
        merged_image = ee.Image(
            result_collection.iterate(add_images, empty_image)
        )

        # --- Apply class 10 (steep-slope) override LAST ---
        steep_band = steep_protected.select([self.band_name_image])
        merged_image = merged_image.where(
            steep_band.neq(0), steep_band
        )

        merged_image = (
            merged_image.toInt32()
            .rename(self.band_name_image)
            .clip(self.AOI)
        )

        return {
            "all_zone": merged_image,
            "vis_param_merged": self.vis_param_merged,
            "legend_class": self.legend_class,
        }
