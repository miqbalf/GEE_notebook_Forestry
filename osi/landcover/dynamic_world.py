import ee


class DynamicWorld:
    """Dynamic World V1 composite and tree transition detection.

    Composites GOOGLE/DYNAMICWORLD/V1 over a date window and detects
    tree-to-non-tree transitions for deforestation cross-check.
    """

    # DW label band class values
    WATER = 0
    TREES = 1
    GRASS = 2
    FLOODED_VEGETATION = 3
    CROPS = 4
    SHRUB_AND_SCRUB = 5
    BUILT = 6
    BARE = 7
    SNOW_AND_ICE = 8

    def __init__(self, config):
        self.config = config
        self.AOI = config["AOI"]

    def get_composite(self, start_date, end_date):
        """Return mode (label) and mean tree probability over a date window.

        Parameters
        ----------
        start_date : str
            Start date in YYYY-MM-DD format.
        end_date : str
            End date in YYYY-MM-DD format.

        Returns
        -------
        dict
            {"dw_mode": ee.Image, "dw_tree_prob": ee.Image} clipped to AOI.
        """
        dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterDate(
            start_date, end_date
        )

        # Most frequent land-cover class over the window
        dw_mode = dw.select("label").mode().rename("dw_mode").clip(self.AOI)

        # Mean tree probability over the window
        dw_tree_prob = (
            dw.select("trees").mean().rename("dw_tree_prob").clip(self.AOI)
        )

        return {
            "dw_mode": dw_mode,
            "dw_tree_prob": dw_tree_prob,
        }

    def tree_transitions(self, year_start, year_end):
        """Detect pixels where trees (class 1) became non-trees at least once.

        Builds a yearly composite for each year in [year_start, year_end],
        then for each consecutive year pair marks pixels that went from
        class 1 (trees) to anything else.  All pair-wise masks are OR-ed
        together so the result shows *any* tree-to-non-tree transition.

        Parameters
        ----------
        year_start : int
            First year of the range (inclusive).
        year_end : int
            Last year of the range (inclusive).

        Returns
        -------
        dict
            {"dw_transitions": ee.Image} — binary mask clipped to AOI.
        """
        # Build yearly label-mode composites
        yearly = []
        for year in range(year_start, year_end + 1):
            comp = self.get_composite(f"{year}-01-01", f"{year}-12-31")
            yearly.append(comp["dw_mode"])

        if len(yearly) < 2:
            # Not enough years to detect a transition
            empty = ee.Image.constant(0).clip(self.AOI).rename("dw_transitions")
            return {"dw_transitions": empty}

        # Pair-wise tree-to-non-tree transitions
        masks = []
        for i in range(len(yearly) - 1):
            was_tree = yearly[i].eq(self.TREES)
            not_tree = yearly[i + 1].neq(self.TREES)
            transition = was_tree.And(not_tree)
            masks.append(transition)

        # OR all transition masks together
        transition_mask = ee.Image(masks[0])
        for m in masks[1:]:
            transition_mask = transition_mask.Or(m)

        transition_mask = transition_mask.rename("dw_transitions").clip(self.AOI)

        return {"dw_transitions": transition_mask}
