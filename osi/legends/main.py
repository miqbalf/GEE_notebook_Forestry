import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.legend_handler import HandlerBase
import matplotlib.font_manager as fm
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

class LegendsBuilder:
    THEME_COLORS = {
        'GREEN': '#008028',
        'GREEN_DARK': '#003329',
        'GREEN_FV': '#7CB513',
        'GREEN_LIGHT': '#88F89A',
        'ORANGE': '#DF4F1E',
        'GRAY': '#646567',
        'DODGERBLUE1': '#1E90FF',
        'DODGERBLUE2': '#1C86EE',
        'DODGERBLUE3': '#1874CD',
        'DODGERBLUE4': '#104E8B',
        'BLACK': '#000000',
        'LIGHTGRAY': '#DEDEDE',
        'GRAY1': '#A0A1A2',
        'GRAY2': '#808182',
        'GRAY3': '#646567',
        'ORANGE1': '#F9DFD6',
        'ORANGE2': '#DF4F1E'
    }

    def __init__(self, legend_items):
        self.legend_items = legend_items
        self.font_list = [font.name for font in fm.fontManager.ttflist]
        self.ensure_font_installed()
        plt.rcParams['font.family'] = "Barlow"
        plt.rcParams['font.size'] = 10

    def ensure_font_installed(self):
        if not "Barlow" in self.font_list:
            fontpaths = "/library/fonts/"
            if os.path.isfile(fontpaths + "Barlow-Regular.ttf"):
                fm.fontManager.addfont(fontpaths + "Barlow-Regular.ttf")
            if os.path.isfile(fontpaths + "Barlow-Bold.ttf"):
                fm.fontManager.addfont(fontpaths + "Barlow-Bold.ttf")
            if os.path.isfile(fontpaths + "Barlow-Italic.ttf"):
                fm.fontManager.addfont(fontpaths + "Barlow-Italic.ttf")
            if os.path.isfile(fontpaths + "Barlow-BoldItalic.ttf"):
                fm.fontManager.addfont(fontpaths + "Barlow-BoldItalic.ttf")
            self.download_font_from_github()

    def download_font_from_github(self):
        font_urls = {
            'Barlow-Regular': 'https://github.com/google/fonts/blob/main/ofl/barlow/Barlow-Regular.ttf?raw=true',
            'Barlow-Bold': 'https://github.com/google/fonts/blob/main/ofl/barlow/Barlow-Bold.ttf?raw=true',
            'Barlow-Italic': 'https://github.com/google/fonts/blob/main/ofl/barlow/Barlow-Italic.ttf?raw=true',
            'Barlow-BoldItalic': 'https://github.com/google/fonts/blob/main/ofl/barlow/Barlow-BoldItalic.ttf?raw=true'
        }

        for font_name, url in font_urls.items():
            response = urlopen(url)
            temp_file = NamedTemporaryFile(delete=False, suffix='.ttf')
            temp_file.write(response.read())
            temp_file.close()
            fm.fontManager.addfont(temp_file.name)

    class CustomHandlerRectangle(HandlerBase):
        def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
            w = 30  # fixed width
            h = 15  # fixed height
            patch = mpatches.Rectangle(
                (xdescent, ydescent + (height - h) / 2), w, h, 
                edgecolor=orig_handle.get_edgecolor(),
                facecolor=orig_handle.get_facecolor(), 
                lw=orig_handle.get_linewidth(), 
                transform=trans
            )
            return [patch]

    def create_legend(self, title_legend='None'):
        fig, ax = plt.subplots(figsize=(6, 6))

        patches = [mpatches.Patch(edgecolor='black', linewidth=0.5, facecolor=item["color"], label=item["label"]) for item in self.legend_items]

        legend = ax.legend(
            handles=patches, 
            loc='center left', 
            frameon=False, 
            fontsize='medium', 
            title=f'Legend {title_legend}',
            handler_map={mpatches.Patch: self.CustomHandlerRectangle()},
            borderpad=2, 
            labelspacing=1, 
            handletextpad=1.5
        )

        plt.setp(legend.get_title(), fontsize='13', fontweight='bold', ha='left')
        ax.axis('off')
        plt.show()

    def create_colorbar(self, title,info):
        cmap = LinearSegmentedColormap.from_list("custom_cmap", info['palette'])

        fig, ax = plt.subplots(figsize=(6, 2))

        norm = mcolors.Normalize(vmin=info['min'], vmax=info['max'])
        cb = ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')

        ax.set_aspect(10)  # Increase the value to make the colorbar narrower

        cb.set_label(title, fontsize=10, fontweight='normal', labelpad=10)

        cb.set_ticks([info['min'], (info['min'] + info['max']) / 2, info['max']])
        cb.set_ticklabels([str(info['min']), str(info['max'] / 2), str(info['max'])])

        ax.yaxis.set_label_position('left')
        ax.yaxis.set_ticks_position('right')
        cb.ax.yaxis.set_label_coords(-0.1, 0.5)  # Adjust this value to move the label closer or further from the colorbar

        plt.show()
