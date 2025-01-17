def convert_to_legend_items(data):
    legend_items = []
    for key, value in data.items():
        legend_item = {
            "color": value["color"],
            "label": f"{key}: {value['name']}"
        }
        legend_items.append(legend_item)
    return legend_items

def legends_obj_creation(pallette_class_segment, class_name_dict):
    # Define the order of class IDs only for FCD
    all_keys = [k for k,v in pallette_class_segment.items()] 
    all_keys_num_sorted = sorted([int(str) for str in all_keys])
    class_ids_order = [str(index) for index in all_keys_num_sorted] 
    #class_ids_order = set['1', '2', '3', '4', '5', '6', '7', '8', '9','10','11','12','13','14']
    
    # Create a list of colors in the correct order
    colors_in_order = [pallette_class_segment[class_id] for class_id in class_ids_order]

    vis_param = {'min': min(all_keys_num_sorted), 'max': len(class_ids_order), 'palette': colors_in_order}

    legend_class = {k:{'name':v, 'color':pallette_class_segment[k]} for k,v in class_name_dict.items()}
    return{'vis_param':vis_param,
           'legend_class':legend_class}