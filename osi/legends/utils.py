def convert_to_legend_items(data):
    legend_items = []
    for key, value in data.items():
        legend_item = {
            "color": value["color"],
            "label": f"{key}: {value['name']}"
        }
        legend_items.append(legend_item)
    return legend_items